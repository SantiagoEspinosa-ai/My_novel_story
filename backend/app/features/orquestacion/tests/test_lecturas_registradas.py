"""El bucle registra lo que leyó cada llamada, o el registro no existe.

Una función que nadie llama es un dato que nadie escribe. La medida de cuánto
arrastra un cambio (`SPEC-23`, pregunta 5) solo es gratis si el registro viaja
**en la generación ordinaria**: si hubiera que lanzar una pasada aparte para
obtenerlo, habría que pagar una generación entera para medir.
"""

import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo
from app.features.contexto import repository as lecturas_repo
from app.features.escaleta import repository as repo
from app.features.orquestacion import bucle as agente


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    repo.guardar_escaleta(c, "obra-1", [
        {"id": "e1", "orden": 1, "pov": "per-marta", "lugar": "lug-salon",
         "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
         "beats": ["b1"], "longitud_objetivo": [1200, 2200]},
    ])
    return c


def _ctx(tam=100):
    from app.features.contexto.bloques import BLOQUES
    return {b.nombre: tam for b in BLOQUES}


# **Una sola forma.** `hechos` son fichas del canon en todo el camino, desde
# `reunir_material` hasta aqui. Los identificadores sueltos existen en un unico
# sitio -lo que se imprime en el prompt- y la conversion es explicita.
HECHOS = [{"id": "hec-llave", "enunciado": "La llave no aparece",
           "establecido_en": None}]
MUNDO = {"conocimiento": {("per-marta", "hec-llave"): {"desde": "e1"}}}


def test_generar_deja_registrado_que_hechos_tuvo_delante_la_escena(con):
    agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000,
                   hechos=HECHOS, mundo=MUNDO)

    filas = lecturas_repo.lecturas_de(con, "e1")

    assert {(f["tipo"], f["hecho"]) for f in filas} == {
        ("hecho", "hec-llave"), ("conocimiento", "hec-llave")}


def test_la_lectura_se_ata_a_la_llamada_por_su_prompt_hash(con):
    """Lo que une la lectura con el `Borrador` que salió de ella (`RF-11`)."""
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000,
                       hechos=HECHOS, mundo=MUNDO)

    filas = lecturas_repo.lecturas_de(con, "e1")

    assert filas, "sin filas no hay nada que atar"
    assert all(f["prompt_hash"] == r.traza.prompt_hash for f in filas)


def test_una_escena_sin_hechos_no_escribe_filas_y_no_falla(con):
    agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000)

    assert lecturas_repo.lecturas_de(con, "e1") == []


def test_se_registra_antes_de_llamar_al_modelo(con):
    """Una llamada que falla también leyó algo, y es la que hay que diagnosticar.

    Si el registro ocurriera después de la respuesta, el caso interesante -el
    contexto con el que se generó algo que no sirvió- sería justo el que no
    queda escrito.
    """
    from app.commons.modelo.doble import Guion

    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["sin_delta"])),
                       techo=10_000, hechos=HECHOS, mundo=MUNDO)

    assert r.fallo == "contrato"
    assert lecturas_repo.lecturas_de(con, "e1"), "la lectura ocurrió igual"


def test_el_bucle_recibe_fichas_y_solo_el_prompt_ve_identificadores(con):
    """El contrato unificado, fijado por su nombre.

    `hechos` viajaba con dos formas -fichas hacia `montar`, identificadores
    hacia `generar`- y el mismo nombre con dos formas es la Regla 5 en pequeño:
    ya hizo tropezar a quien escribio el registro de lecturas. Ahora la ficha es
    la unica forma que viaja y la proyeccion a identificadores ocurre una sola
    vez, al construir el prompt.

    Si alguien vuelve a aceptar las dos "por comodidad", esta prueba se lo dice.
    """
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000,
                       hechos=HECHOS, mundo=MUNDO)

    assert r.fallo is None
    # Lo que se registro es el identificador, no la ficha entera.
    assert [f["hecho"] for f in lecturas_repo.lecturas_de(con, "e1")
            if f["tipo"] == "hecho"] == ["hec-llave"]
