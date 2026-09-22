"""A4 — La cola, el worker y los dos numeros sin medir.

La prueba que abre este paso no es la del encolado: es la del worker que
vuelve y se encuentra `abandonado`. Es la que sostiene que el margen de
abandono sea un parametro de **latencia** y no de **correccion**. Sin ella,
quince minutos mal elegidos corrompen el estado; con ella, solo cuestan
repetir trabajo.

    "Ningun numero sin medir deberia poder corromper el estado."
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.trabajos import cola
from app.commons.trabajos.estados import EstadoDeTrabajo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    return c


def test_un_worker_que_vuelve_abandonado_no_escribe_su_resultado(con):
    """LA prueba del paso. `SPEC-07` C-3 y `Docs/architecture.md`."""
    id_t = cola.encolar(con, "generar_escena", {"escena": "esc-1"})
    cola.tomar(con, id_t)
    cola.marcar_abandonado(con, id_t)

    escrito = cola.registrar_resultado(con, id_t, {"texto": "una escena entera"})

    assert escrito is False
    t = cola.leer(con, id_t)
    assert t.estado is EstadoDeTrabajo.ABANDONADO
    assert t.resultado is None
    assert t.volvio_tras_abandono is True, "tiene que quedar constancia de que volvio"


def test_abandonado_no_es_fallido(con):
    """No son el mismo hecho: uno se sabe que paso, el otro no se sabe si paso."""
    assert EstadoDeTrabajo.ABANDONADO is not EstadoDeTrabajo.FALLIDO
    assert cola.cuenta_contra_el_tope(EstadoDeTrabajo.FALLIDO) is True
    assert cola.cuenta_contra_el_tope(EstadoDeTrabajo.ABANDONADO) is False


def test_un_abandonado_no_se_relanza_solo(con):
    id_t = cola.encolar(con, "generar_escena", {"escena": "esc-1"})
    cola.tomar(con, id_t)
    cola.marcar_abandonado(con, id_t)
    assert cola.barrer(con) == 0, "nada automatico devuelve un abandonado a la cola"


def test_solo_una_persona_relanza_un_abandonado(con):
    id_t = cola.encolar(con, "generar_escena", {"escena": "esc-1"})
    cola.tomar(con, id_t)
    cola.marcar_abandonado(con, id_t)
    cola.relanzar(con, id_t)
    assert cola.leer(con, id_t).estado is EstadoDeTrabajo.EN_COLA


def test_los_siete_estados_y_sus_literales():
    assert [e.value for e in EstadoDeTrabajo] == [
        "en_cola",
        "esperando_presupuesto",
        "en_curso",
        "terminado",
        "fallido",
        "abandonado",
        "detenido_por_presupuesto",
    ]


def test_los_dos_numeros_estan_marcados_como_provisionales():
    """`SPEC-05`: un numero sin medir que no se declara es un numero inventado
    con aspecto de medido. `VER-56` recorre estas marcas tambien en codigo."""
    from app.commons import config

    fuente = (config.__file__).replace(".py", ".py")
    with open(fuente, encoding="utf-8") as f:
        texto = f.read()
    assert texto.count("Caduca con:") >= 2
    assert config.TOPE_REINTENTOS_TRANSPORTE == 3
    assert config.MARGEN_ABANDONO_SEGUNDOS == 15 * 60
