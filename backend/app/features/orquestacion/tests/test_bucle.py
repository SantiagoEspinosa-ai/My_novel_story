"""E2 — El bucle entero contra el doble, antes de que nada gaste.

Esta es la prueba que el plan pone antes del cliente real, y el motivo esta
escrito en la Fase E: si el bucle esta mal, se ve gratis.

El doble tiene la misma forma que lo real y **sabe portarse mal**: devolver un
delta fuera de esquema, quedarse mudo, quedarse corto. Un doble que solo sabe
portarse bien pasa contra si mismo y falla contra el proveedor.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.modelo.doble import DobleDelModelo, Guion
from app.features.escaleta import repository as repo
from app.features.orquestacion import bucle as agente


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    repo.guardar_escaleta(c, "obra-1", [
        {"id": "e1", "orden": 1,
         "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
         "beats": ["b1"], "longitud_objetivo": [1200, 2200]},
    ])
    return c


def _ctx(tam=100):
    from app.features.contexto.bloques import BLOQUES
    return {b.nombre: tam for b in BLOQUES}


def test_una_generacion_limpia_deja_borrador_traza_y_ningun_hallazgo(con):
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000)
    assert r.fallo is None
    assert r.version == 1
    assert r.hallazgos == []
    assert repo.escena(con, "e1")["estado"] == EE.GENERADA.value
    assert r.traza.tokens_declarados == 2100


def test_son_dos_numeros_desde_spec_14(con):
    """`SPEC-14` C-3 retiro `tokens_reservados`: decia "reservado" sin reservar."""
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000)
    assert r.traza.tokens_para_recortar == 700
    assert r.traza.tokens_reservados is None, "ya no se reserva nada"


def test_una_respuesta_sin_delta_es_fallo_de_contrato_y_no_hallazgo(con):
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["sin_delta"])), techo=10_000)
    assert r.fallo == "contrato"
    assert r.hallazgos == []
    assert repo.intentos_de(con, "e1") == 0, "no llego a guardarse borrador"
    assert r.traza.salida_fallida, "un fallo de contrato guarda la salida entera"


def test_un_delta_fuera_de_esquema_tambien(con):
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["delta_roto"])), techo=10_000)
    assert r.fallo == "contrato"


def test_una_respuesta_muda_es_fallo_y_no_un_texto_vacio(con):
    """Un vacio que pasa entra en el manuscrito sin que nada lo marque."""
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["mudo"])), techo=10_000)
    assert r.fallo == "contrato"


def test_un_timeout_deja_traza_y_no_guarda_salida(con):
    """`T-2`: una llamada que falla tambien deja traza. Y la salida entera solo
    en el fallo de contrato: en un timeout no hay salida que guardar."""
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["timeout"])), techo=10_000)
    assert r.fallo == "transporte"
    assert r.traza.resultado == "fallo"
    assert r.traza.salida_fallida is None


def test_ya_no_hay_techo_que_liberar(con):
    """Lo que `SPEC-14` C-1 se llevo, y con ello `MF-25`.

    Antes esta prueba comprobaba que un timeout liberase el presupuesto
    reservado, porque si no lo liberaba el techo se quedaba retenido hasta que
    expirase el margen de abandono: eso era `MF-25`. Sin reserva **no hay nada
    que retener**, asi que el interbloqueo desaparece con su causa.
    """
    techo = {}
    agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["timeout"])),
                   techo=10_000, estado_del_techo=techo)
    assert techo == {}, "nadie reserva, asi que no hay nada que liberar"


def test_una_escena_corta_produce_inv17_y_no_la_caza_ningun_juez(con):
    """El caso de la otra rama: 944 palabras con minimo de 1200.

    Alli lo aprobo el validador de genero porque juzga ritmo. Aqui lo caza una
    regla, y produce un hallazgo de severidad `mayor` que impide cerrar el
    capitulo.
    """
    r = agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["corto"])), techo=10_000)
    assert r.fallo is None, "un capitulo corto es utilizable, no un fallo de contrato"
    inv17 = [h for h in r.hallazgos if h.invariante == "INV-17"]
    assert inv17 and str(inv17[0].severidad) == "mayor"
    assert repo.hallazgos_abiertos(con, "e1")[0]["invariante"] == "INV-17"


def test_si_no_cabe_se_falla_en_vez_de_generar(con):
    """`RF-26`. No se genera con un contexto mutilado."""
    modelo = DobleDelModelo()
    r = agente.generar(con, "e1", _ctx(tam=10_000), modelo, techo=10)
    assert r.fallo == "no_cabe"
    assert modelo.llamadas == [], "no se llego a llamar al modelo"
    assert r.traza.recortes, "los recortes intentados quedan en la traza"


def test_los_recortes_quedan_en_la_traza_con_su_clase(con):
    r = agente.generar(con, "e1", _ctx(tam=500), DobleDelModelo(), techo=1500)
    clases = {x.clase for x in r.traza.recortes}
    assert clases <= {"reduccion", "eliminacion"}
    assert r.traza.recortes, "hubo recorte y quedo registrado"


def test_dos_intentos_seguidos_dan_versiones_1_y_2(con):
    agente.generar(con, "e1", _ctx(), DobleDelModelo(Guion(["corto"])), techo=10_000)
    r2 = agente.generar(con, "e1", _ctx(), DobleDelModelo(), techo=10_000)
    assert r2.version == 2
    assert repo.intentos_de(con, "e1") == 2
