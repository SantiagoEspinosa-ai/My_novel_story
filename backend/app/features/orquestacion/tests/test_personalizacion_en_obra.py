"""`INV-22` e `INV-23` en el bucle de la obra (`SPEC-26` `RF-13`, `RF-14`).

`INV-22` comparte contador y tope con `INV-21` (`O-2`): las dos son reglas del
codigo que le dicen al Escritor exactamente que escribio mal.
"""

import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo, Guion
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.cronologia import repository as usos
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra
from app.features.politica import repository as politica

IMPRESCINDIBLES = {"e1": [{"id": "imp-01", "elemento": "colecciona mapas",
                           "palabras_clave": ["mapa"]}]}


class Devuelve:
    nombre = "doble"

    def __init__(self, r):
        self.r = r

    def llamar(self, prompt):
        return dict(self.r)


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    politica.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": []})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e{0}".format(i), "orden": i, "capitulo": "cap-1",
         "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": ["b"], "longitud_objetivo": [10, 5000]} for i in (1, 2)])
    return c


def _generar(con, pasos, **kw):
    escritor = DobleDelModelo(Guion(pasos))
    kw.setdefault("nombres", ["Irene Valdés"])
    g = obra.generar_obra(con, "cap-1", escritor,
                          Devuelve({"veredicto": "PASA", "problemas": []}),
                          Devuelve({"texto": "Resumen. " * 10, "hechos_clave": []}),
                          techo=1_000_000, **kw)
    return g, escritor


def test_un_nombre_mal_escrito_se_reescribe_y_luego_se_acepta(con):
    g, escritor = _generar(con, ["nombre_mal", "nombre_mal", "bien"])
    assert g.llego_al_final and len(escritor.llamadas) == 4
    assert "INV-22" in escritor.llamadas[1] and "Irena" in escritor.llamadas[1]


def test_tres_nombres_mal_escritos_paran_sin_rendicion(con):
    g, _ = _generar(con, ["nombre_mal"])
    assert g.parada["motivo"] == "nombre_mal_escrito" and g.rendidas == []


def test_nombres_y_vetadas_comparten_el_mismo_contador(con):
    """Una vetada y un nombre mal escrito ya son dos reescrituras: la tercera
    falta, de cualquiera de las dos, para."""
    g, _ = _generar(con, ["vetada", "nombre_mal", "nombre_mal"], vetadas=["zoquete"])
    assert g.parada["motivo"] == "nombre_mal_escrito"
    g2, _ = _generar(con, ["vetada", "nombre_mal", "bien"], vetadas=["zoquete"])
    assert g2.llego_al_final


def test_una_clave_ausente_da_inv23_y_otro_intento(con):
    g, escritor = _generar(con, ["bien", "con_clave", "bien"],
                           imprescindibles=IMPRESCINDIBLES)
    assert g.llego_al_final and g.rendidas == []
    assert "INV-23" in escritor.llamadas[1] and "mapa" in escritor.llamadas[1]
    guardados = [h[0] for h in con.execute(
        "SELECT invariante FROM hallazgo WHERE escena='e1'").fetchall()]
    assert guardados == ["INV-23"]


def test_la_clave_presente_deja_su_uso_en_la_tabla(con):
    _generar(con, ["con_clave", "bien"], imprescindibles=IMPRESCINDIBLES)
    [u] = usos.usos_de_hecho(con, "imp-01")
    assert (u["escena"], str(u["tipo"]), str(u["origen"])) == ("e1", "menciona", "regla")


def test_el_prompt_lleva_los_nombres_y_las_claves(con):
    _, escritor = _generar(con, ["con_clave", "bien"], imprescindibles=IMPRESCINDIBLES)
    assert "Irene Valdés" in escritor.llamadas[0] and "mapa" in escritor.llamadas[0]
    # «mapa» si puede llegar al segundo prompt dentro de la escena anterior
    # (desde `F-58` el contexto llega como texto); el bloque de claves no.
    assert "ESTE CAPITULO TIENE QUE CONTAR" not in escritor.llamadas[1],         "las claves son de su capitulo"


def _audit(con):
    return con.execute("SELECT tipo, detalle FROM decision_de_politica ORDER BY id").fetchall()


def test_cada_reescritura_por_nombre_queda_en_el_audit_log_sin_los_nombres(con):
    """`F-73`: la rama de `INV-22` sumaba al contador y no dejaba rastro. Y lo que queda
    no lleva nombres: el audit log sobrevive a la entrega (`SPEC-25` `RF-21`)."""
    _generar(con, ["nombre_mal", "nombre_mal", "bien"])
    filas = _audit(con)
    tipos = [f[0] for f in filas]
    assert tipos.count("nombre_mal_escrito") == 2 and tipos.count("reescritura_pedida") == 2
    assert "Iren" not in repr(filas) and "Vald" not in repr(filas)


def test_la_parada_por_nombre_queda_en_el_audit_log(con):
    _generar(con, ["nombre_mal"])
    assert [f[0] for f in _audit(con)].count("parada_por_nombre") == 1
