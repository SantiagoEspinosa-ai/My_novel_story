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


def test_un_capitulo_terminado_trae_el_estado_de_su_escena_y_no_es_el_actual(cliente, con):
    """`F-200`: el pipeline no cierra capitulos (`capitulo.estado` sigue `abierto`) y no hay
    fase de «terminado», asi que un capitulo acabado seguia diciendo «resumiendo». Lo que dice
    que termino es el estado de su escena; y la fase solo es de ahora en el capitulo actual."""
    fijar_fase(con, OBRA, "escribiendo", 1)
    fijar_fase(con, OBRA, "resumiendo", 1)
    aceptar(con, id_escena(OBRA, 1), 1, estado="consolidada")
    fijar_fase(con, OBRA, "escribiendo", 2)
    uno, dos, tres = _leer(cliente)["capitulos"][:3]
    assert uno["es_el_actual"] is False
    assert uno["escenas"] == [{"id": id_escena(OBRA, 1), "estado": "consolidada"}]
    assert (dos["es_el_actual"], dos["escenas"][0]["estado"]) == (True, "planificada")
    assert tres["es_el_actual"] is False


def test_publicada_ningun_capitulo_es_el_actual(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 10)
    fijar_fase(con, OBRA, "en_la_puerta")
    fijar_fase(con, OBRA, "publicada")
    assert not any(c["es_el_actual"] for c in _leer(cliente)["capitulos"])


# --- `PLAN-35` F2: mientras se planifica, y si el lanzamiento falla (`SPEC-35` `RF-13`) ---

def _entrevista_sin_montar(con, obra):
    """La obra nace con su entrevista y no entra en `obra` hasta que se monta."""
    with con:
        con.execute("CREATE TABLE IF NOT EXISTS entrevista (id TEXT PRIMARY KEY, obra TEXT "
                    "NOT NULL, ficha TEXT NOT NULL, cerrada INTEGER NOT NULL DEFAULT 0, "
                    "juicios TEXT NOT NULL DEFAULT '[]', avisos_confirmados TEXT NOT NULL "
                    "DEFAULT '[]', vistas TEXT NOT NULL DEFAULT '{}')")
        con.execute("INSERT INTO entrevista (id, obra, ficha, cerrada) VALUES (?, ?, '{}', 1)",
                    ("ent-1", obra))


def test_una_obra_que_se_esta_planificando_no_es_404(cliente, con):
    """`F-206`: durante los minutos del Planificador la obra no esta en `obra`."""
    _entrevista_sin_montar(con, "obra-nueva")
    fijar_fase(con, "obra-nueva", "planificando", total=None)
    g = _leer(cliente, "obra-nueva")
    assert g["capitulos"] == [] and g["total_de_capitulos"] == 0
    assert g["fase_de_la_obra"] == "planificando"
    assert g["motivo_del_fallo"] is None


def test_un_lanzamiento_fallido_trae_su_motivo(cliente, con):
    """Sin `claude` el trabajo falla antes de la primera fila de progreso: sin esto la pagina
    diria «no empezado» para siempre."""
    from app.commons.trabajos import cola
    _entrevista_sin_montar(con, "obra-nueva")
    id_t = cola.encolar(con, "generacion_regalo", {"obra": "obra-nueva", "generacion": "g1"})
    cola.tomar(con, id_t)
    cola.registrar_fallo(con, id_t, "FaltaEntorno: no se encuentra el ejecutable de Claude Code")
    g = _leer(cliente, "obra-nueva")
    assert g["motivo_del_fallo"].startswith("FaltaEntorno")
    assert g["fase_de_la_obra"] is None


def test_un_lanzamiento_que_salio_bien_no_trae_motivo(cliente, con):
    from app.commons.trabajos import cola
    id_t = cola.encolar(con, "generacion_regalo", {"obra": OBRA, "generacion": "g1"})
    cola.tomar(con, id_t)
    cola.registrar_resultado(con, id_t, {"publicada": True})
    assert _leer(cliente)["motivo_del_fallo"] is None


def test_la_generacion_trae_la_fase_de_la_obra(cliente, con):
    fijar_fase(con, OBRA, "escribiendo", 10)
    fijar_fase(con, OBRA, "esperando_revision")
    assert _leer(cliente)["fase_de_la_obra"] == "esperando_revision"
