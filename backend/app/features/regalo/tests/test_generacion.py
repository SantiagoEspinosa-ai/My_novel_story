"""`SPEC-33` `RF-14`..`RF-17`, `RF-19`, `RF-20`, `PLAN-33` E6: el estado de una generacion,
capitulo a capitulo, con las notas del Editor y el coste.

Todo lo calcula el backend: la fase de cada capitulo es la ultima fila de
`progreso_de_generacion` con ese capitulo, las notas son las del borrador aceptado, y si
una baja del umbral de `INV-26` viene marcado. La interfaz lo pinta.
"""

from app.commons.modelo import gasto
from app.features.regalo.tests.conftest import (
    CRITERIOS, OBRA, OTRA, aceptar, fijar_fase, id_escena, valorar)


def _leer(cliente, obra=OBRA):
    r = cliente.get("/obras/{0}/generacion".format(obra))
    assert r.status_code == 200, r.text
    return r.json()


def test_cada_capitulo_trae_su_ultima_fase(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 1)
    fijar_fase(con, OBRA, "editando", 1)
    fijar_fase(con, OBRA, "escribiendo", 2)
    fijar_fase(con, OTRA, "resumiendo", 3)
    g = _leer(cliente)
    assert g["total_de_capitulos"] == 10
    assert [c["numero"] for c in g["capitulos"]] == list(range(1, 11))
    assert g["capitulos"][0]["fase"] == "editando"
    assert g["capitulos"][1]["fase"] == "escribiendo"


def test_un_capitulo_no_empezado_viene_sin_fase_y_no_con_una_inventada(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 1)
    g = _leer(cliente)
    assert g["capitulos"][2]["fase"] is None
    assert g["capitulos"][2]["desde"] is None


def test_parada_trae_su_motivo(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 4)
    fijar_fase(con, OBRA, "parada", 4, motivo="FalloDeTransporte")
    c = _leer(cliente)["capitulos"][3]
    assert (c["fase"], c["motivo"]) == ("parada", "FalloDeTransporte")


def test_las_notas_son_las_del_borrador_aceptado(cliente, con):
    e = id_escena(OBRA, 1)
    valorar(con, e, 1, (2, 2, 2, 2, 2, 2))
    valorar(con, e, 2, (4, 5, 4, 4, 3, 5))
    aceptar(con, e, 2)
    notas = _leer(cliente)["capitulos"][0]["notas"]
    assert [n["nota"] for n in notas] == [4, 5, 4, 4, 3, 5]
    assert {n["criterio"] for n in notas} == set(CRITERIOS)


def test_un_capitulo_sin_borrador_aceptado_no_trae_notas(cliente, con):
    """Las notas aparecen al cerrarse el capitulo (`RF-16`), no a mitad."""
    valorar(con, id_escena(OBRA, 1), 1, (4, 4, 4, 4, 4, 4))
    assert _leer(cliente)["capitulos"][0]["notas"] == []


def test_una_nota_bajo_el_umbral_viene_marcada(cliente, con):
    """`INV-26`: `nota < umbral` con el umbral de la configuracion (3 por defecto)."""
    e = id_escena(OBRA, 1)
    valorar(con, e, 1, (2, 3, 4, 4, 4, 4))
    aceptar(con, e, 1)
    marcas = {n["criterio"]: n["bajo_el_umbral"] for n in _leer(cliente)["capitulos"][0]["notas"]}
    assert marcas["continuidad"] is True
    assert marcas["tono"] is False, "3 no esta bajo un umbral de 3"


def test_el_coste_es_el_de_la_ultima_generacion_de_la_obra(cliente, con):
    gasto.anotador(con, OBRA, "gen-vieja")("escritor", 9.0)
    nueva = gasto.anotador(con, OBRA, "gen-nueva")
    nueva("planificador", 0.5)
    nueva("escritor", 0.25)
    gasto.anotador(con, OTRA, "gen-otra")("escritor", 7.0)
    c = _leer(cliente)["coste"]
    assert (c["generacion"], c["usd"], c["delegaciones"], c["sin_coste"], c["es_suelo"]) == \
        ("gen-nueva", 0.75, 2, 0, False)


def test_con_una_delegacion_sin_coste_el_total_es_suelo(cliente, con):
    a = gasto.anotador(con, OBRA, "gen-1")
    a("escritor", 0.25)
    a("editor", None)
    c = _leer(cliente)["coste"]
    assert (c["usd"], c["sin_coste"], c["es_suelo"]) == (0.25, 1, True)


def test_sin_ninguna_con_coste_el_total_es_sin_medir(cliente, con):
    gasto.anotador(con, OBRA, "gen-1")("escritor", None)
    c = _leer(cliente)["coste"]
    assert c["usd"] is None and c["delegaciones"] == 1


def test_sin_generacion_el_coste_viene_ausente(cliente):
    assert _leer(cliente)["coste"] is None


def test_obra_que_no_existe_es_404(cliente):
    assert cliente.get("/obras/obra-que-no-existe/generacion").status_code == 404
