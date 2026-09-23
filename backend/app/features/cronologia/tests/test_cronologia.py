"""`SPEC-21` C-3 — La cronologia de la fabula, y las tres cosas que sostiene.

Orden temporal, edad coherente con la fecha de nacimiento y que nadie este en
dos lugares a la vez. Las tres eran **inexpresables** antes de estas tablas: no
es que salieran mal, es que no habia contra que preguntarlas.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import TipoDePresencia as P
from app.features.cronologia import consultas, extraccion, repository as repo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    return c


def _evento(con, id_evento, t, lugar, presentes=(), mencionados=(), dur=None,
            capitulo="cap-1"):
    repo.registrar_evento(
        con,
        {"id": id_evento, "obra": "obra-1", "t_fabula": t, "lugar": lugar,
         "capitulo": capitulo, "duracion_min": dur},
        [(p, P.PRESENTE) for p in presentes]
        + [(m, P.MENCIONADO) for m in mencionados])


# --- La tabla ---------------------------------------------------------------


def test_un_evento_guarda_cuando_donde_y_quien_estaba(con):
    _evento(con, "evt-1", "1897-11-03", "lug-salon",
            presentes=["per-marta", "per-ubaldo"], mencionados=["per-pilar"])
    assert repo.participantes_de(con, "evt-1") == ["per-marta", "per-ubaldo"]


def test_mencionado_no_cuenta_como_presente(con):
    """`SPEC-21` C-3. Que hablen de alguien no lo pone en la habitacion.

    Sin esta separacion, dos personajes acordandose del mismo ausente lo
    situarian en dos sitios a la vez y la comprobacion de ubicuidad se llenaria
    de falsos positivos.
    """
    _evento(con, "evt-1", "1897-11-03", "lug-salon",
            presentes=["per-marta"], mencionados=["per-pilar"])
    assert "per-pilar" not in repo.participantes_de(con, "evt-1")
    assert repo.participantes_de(con, "evt-1", P.MENCIONADO) == ["per-pilar"]


def test_registrar_el_mismo_evento_dos_veces_no_lo_duplica(con):
    _evento(con, "evt-1", "1897-11-03", "lug-salon", presentes=["per-marta"])
    _evento(con, "evt-1", "1897-11-03", "lug-salon", presentes=["per-marta"])
    assert len(repo.eventos_de(con, "obra-1")) == 1


def test_los_eventos_vuelven_en_orden_de_fabula_no_de_lectura(con):
    """La analepsis es exactamente esto: el capitulo 2 puede contar algo
    anterior a lo del capitulo 1. Ordenar por capitulo mentiria."""
    _evento(con, "evt-b", "1897-11-03", "lug-salon", capitulo="cap-1")
    _evento(con, "evt-a", "1880-01-01", "lug-pozo", capitulo="cap-2")
    assert [e["id"] for e in repo.eventos_de(con, "obra-1")] == ["evt-a", "evt-b"]


def test_una_escena_sin_t_fabula_no_produce_evento_inventado():
    """Una cronologia completa y falsa es peor que una incompleta: la
    incompleta se nota."""
    assert extraccion.evento_de_la_escena(
        {"id": "e1", "lugar": "lug-salon"}, "obra-1") is None


# --- Las tres de Lean -------------------------------------------------------


def test_orden_temporal_detecta_la_inversion_frente_al_discurso(con):
    """Lo que `INV-08` llama monotonia de `t_fabula`: un capitulo posterior que
    cuenta algo anterior sin que nadie lo haya declarado analepsis."""
    _evento(con, "evt-1", "1897-11-03", "lug-salon", capitulo="cap-1")
    _evento(con, "evt-2", "1880-01-01", "lug-pozo", capitulo="cap-2")
    r = consultas.orden_temporal(con, "obra-1")
    assert r["inversiones"] == [("evt-1", "evt-2")]


def test_orden_temporal_no_marca_nada_si_la_fabula_sigue_al_discurso(con):
    _evento(con, "evt-1", "1897-11-03", "lug-salon", capitulo="cap-1")
    _evento(con, "evt-2", "1897-11-04", "lug-pozo", capitulo="cap-2")
    assert consultas.orden_temporal(con, "obra-1")["inversiones"] == []


def test_estar_presente_antes_de_nacer_es_incoherente(con):
    _evento(con, "evt-1", "1880-01-01", "lug-salon", presentes=["per-marta"])
    r = consultas.edades(con, "obra-1", {"per-marta": "1897-11-03"})
    assert r["incoherentes"] == [
        {"personaje": "per-marta", "evento": "evt-1",
         "t_fabula": "1880-01-01", "fecha_de_nacimiento": "1897-11-03"}]


def test_un_personaje_sin_fecha_de_nacimiento_se_dice_no_se_aprueba(con):
    """Un dato ausente no es un verde.

    La fecha es opcional (`SPEC-21` C-3), asi que quien no la tenga **no pasa**
    la comprobacion: la salta. Y la salta **en voz alta**, en una lista propia,
    para que nadie lea un `incoherentes` vacio como "todas las edades cuadran".
    """
    _evento(con, "evt-1", "1880-01-01", "lug-salon", presentes=["per-marta"])
    r = consultas.edades(con, "obra-1", {})
    assert r["incoherentes"] == []
    assert r["sin_fecha_de_nacimiento"] == ["per-marta"]


def test_dos_lugares_a_la_vez_es_un_conflicto(con):
    _evento(con, "evt-1", "1897-11-03T21:00", "lug-salon",
            presentes=["per-marta"], dur=120)
    _evento(con, "evt-2", "1897-11-03T22:00", "lug-pozo",
            presentes=["per-marta"], dur=30)
    conflictos = consultas.ubicuidades(con, "obra-1")
    assert len(conflictos) == 1
    assert conflictos[0]["personaje"] == "per-marta"
    assert set(conflictos[0]["lugares"]) == {"lug-salon", "lug-pozo"}


def test_el_mismo_personaje_en_dos_momentos_que_no_solapan_no_es_conflicto(con):
    _evento(con, "evt-1", "1897-11-03T21:00", "lug-salon",
            presentes=["per-marta"], dur=30)
    _evento(con, "evt-2", "1897-11-03T22:00", "lug-pozo",
            presentes=["per-marta"], dur=30)
    assert consultas.ubicuidades(con, "obra-1") == []


def test_dos_personajes_distintos_a_la_vez_en_sitios_distintos_no_es_conflicto(con):
    """El caso negativo que separa "solapan" de "solapan para el mismo"."""
    _evento(con, "evt-1", "1897-11-03T21:00", "lug-salon",
            presentes=["per-marta"], dur=120)
    _evento(con, "evt-2", "1897-11-03T21:30", "lug-pozo",
            presentes=["per-ubaldo"], dur=30)
    assert consultas.ubicuidades(con, "obra-1") == []


def test_una_fecha_ilegible_se_reporta_y_no_se_salta_en_silencio(con):
    """Saltarse una fila que no se entiende deja una comprobacion en verde que
    nunca llego a mirar nada."""
    _evento(con, "evt-1", "el dia de san juan", "lug-salon",
            presentes=["per-marta"])
    r = consultas.ubicuidades(con, "obra-1", con_incidencias=True)
    assert r["sin_fecha_legible"] == ["evt-1"]
