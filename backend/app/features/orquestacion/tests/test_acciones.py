"""`PLAN-39` P1..P3 (`SPEC-39`): publicar y reanudar desde la web. Los agentes y Lean son
dobles: ninguna prueba llama al modelo. Una novela se escribe entera con la API, como en
`test_lanzar`, y despues se deja sin publicar o parada a medias."""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.trabajos import cola
from app.features.auditoria.publicacion import ResultadoLean
from app.features.orquestacion import regalo
from app.features.orquestacion.tests.test_lanzar import _entrevista
from app.features.orquestacion.tests.test_novela import _agentes_para_la_novela_entera
from app.features.orquestacion.tests.test_regalo import _proceso
from app.main import app, preparar_base


class Lean:
    def __init__(self, codigo=0, detalle=""):
        self.codigo, self.detalle, self.llamadas = codigo, detalle, 0

    def verificar(self, con, obra, version=None):
        self.llamadas += 1
        return ResultadoLean(self.codigo, detalle=self.detalle)


class Juez:
    """El Editor de la puerta: juzga la obra entera y dice que el arco se cierra."""

    def __init__(self):
        self.llamadas = 0

    def llamar(self, prompt):
        self.llamadas += 1
        return {"arco_cerrado": True, "final_abrupto": False, "justificacion": "bien"}


@pytest.fixture
def base(tmp_path):
    r = str(tmp_path / "web.db")
    preparar_base(r).close()
    app.state.ruta_db = r
    app.state.agentes_regalo = lambda sistema, entorno, anotar: regalo.agentes(
        sistema, entorno, anotar=anotar, ejecutar=_proceso(_agentes_para_la_novela_entera()))
    # Lean sin veredicto la primera vez: la novela queda escrita y sin publicar.
    app.state.lean_regalo = Lean(2, "sin veredicto: no habia dato bastante")
    app.state.juez_de_publicacion = Juez
    yield r
    for n in ("agentes_regalo", "lean_regalo", "juez_de_publicacion"):
        if hasattr(app.state, n):
            delattr(app.state, n)


@pytest.fixture
def cliente(base):
    return TestClient(app)


def _escrita(cliente, base):
    e = _entrevista(base)
    r = cliente.post("/obras/{0}/generaciones".format(e.obra))
    assert r.status_code == 202, r.text
    assert cliente.get("/trabajos/" + r.json()["id_trabajo"]).json()["estado"] == "terminado"
    return e.obra


def _acciones(cliente, obra):
    r = cliente.get("/obras/{0}/acciones".format(obra))
    assert r.status_code == 200, r.text
    return r.json()


def _parada_en_el_4(base, obra):
    """Deja la obra como si se hubiera parado en el capitulo 4."""
    con = sqlite3.connect(base)
    with con:
        caps = [f[0] for f in con.execute("SELECT id FROM capitulo WHERE obra = ? ORDER BY orden",
                                          (obra,))]
        for cap in caps[3:]:
            con.execute("UPDATE escena SET estado = 'planificada', borrador_aceptado = NULL "
                        "WHERE capitulo = ?", (cap,))
        con.execute("INSERT INTO progreso_de_generacion (obra, fase, capitulo, total_de_capitulos, "
                    "motivo) VALUES (?, 'parada', 4, 10, 'bloqueante')", (obra,))
    con.close()


# --- P1: que se puede hacer -------------------------------------------------------------

def test_una_novela_escrita_sin_publicar_se_puede_publicar(cliente, base):
    obra = _escrita(cliente, base)
    a = _acciones(cliente, obra)
    assert a["publicar"]["posible"] is True, a["publicar"]
    assert a["publicar"]["lean_disponible"] is True
    assert a["reanudar"]["posible"] is False


def test_sin_lake_publicar_no_es_posible_y_dice_por_que(cliente, base, monkeypatch):
    obra = _escrita(cliente, base)
    del app.state.lean_regalo
    from app.features.auditoria import lean as modulo_lean

    def sin_lake(*a, **k):
        raise modulo_lean.LeanNoDisponible("no se encuentra `lake`")
    monkeypatch.setattr(modulo_lean, "localizar_lake", sin_lake)
    p = _acciones(cliente, obra)["publicar"]
    assert p["posible"] is False and p["lean_disponible"] is False
    assert "Lean" in p["motivo"] and "elan" in p["motivo"]


def test_una_parada_se_puede_reanudar_desde_su_capitulo(cliente, base):
    obra = _escrita(cliente, base)
    _parada_en_el_4(base, obra)
    r = _acciones(cliente, obra)["reanudar"]
    assert r["posible"] is True, r
    assert (r["desde_capitulo"], r["faltan"]) == (4, 7)
    assert _acciones(cliente, obra)["publicar"]["posible"] is False


def test_la_estimacion_usa_lo_medido_o_la_referencia(cliente, base):
    obra = _escrita(cliente, base)
    _parada_en_el_4(base, obra)
    r = _acciones(cliente, obra)["reanudar"]
    assert r["coste_por_capitulo"] is not None and r["fuente"]
    assert r["estimacion_usd"] == pytest.approx(r["coste_por_capitulo"] * 7)


def test_con_algo_en_curso_no_se_puede_nada(cliente, base):
    obra = _escrita(cliente, base)
    _parada_en_el_4(base, obra)
    con = sqlite3.connect(base)
    cola.tomar(con, cola.encolar(con, regalo.TIPO_DE_TRABAJO, {"obra": obra}))
    con.close()
    a = _acciones(cliente, obra)
    assert a["reanudar"]["posible"] is False and "curso" in a["reanudar"]["motivo"]
    assert a["publicar"]["posible"] is False


# --- P2: publicar -----------------------------------------------------------------------

def _publicar(cliente, obra):
    r = cliente.post("/obras/{0}/publicaciones".format(obra))
    assert r.status_code == 202, r.text
    t = cliente.get("/trabajos/" + r.json()["id_trabajo"]).json()
    assert t["estado"] == "terminado", t["motivo"]
    return t["resultado"]


def test_publicar_pasa_la_puerta_y_publica(cliente, base):
    obra = _escrita(cliente, base)
    app.state.lean_regalo = Lean(0)
    r = _publicar(cliente, obra)
    assert r["publicada"] is True and r["lean"]["codigo"] == 0
    assert cliente.get("/obras/{0}/generacion".format(obra)).json()["fase_de_la_obra"] == "publicada"
    assert _acciones(cliente, obra)["publicar"]["posible"] is False


def test_si_no_pasa_dice_que_condicion_fallo(cliente, base):
    obra = _escrita(cliente, base)
    r = _publicar(cliente, obra)
    assert r["publicada"] is False
    assert [c["invariante"] for c in r["condiciones"]] == ["INV-28"]
    assert r["lean"]["codigo"] == 2 and "sin veredicto" in r["lean"]["detalle"]


def test_sin_lake_es_409_y_no_llama_al_editor(cliente, base, monkeypatch):
    obra = _escrita(cliente, base)
    del app.state.lean_regalo
    from app.features.auditoria import lean as modulo_lean

    def sin_lake(*a, **k):
        raise modulo_lean.LeanNoDisponible("no se encuentra `lake`")
    monkeypatch.setattr(modulo_lean, "localizar_lake", sin_lake)
    juez = Juez()
    app.state.juez_de_publicacion = lambda: juez
    r = cliente.post("/obras/{0}/publicaciones".format(obra))
    assert r.status_code == 409 and "Lean" in r.json()["detail"]
    assert juez.llamadas == 0


# --- P3: las huerfanas ------------------------------------------------------------------

def test_al_arrancar_una_generacion_en_curso_queda_abandonada_y_la_obra_parada(cliente, base):
    obra = _escrita(cliente, base)
    con = sqlite3.connect(base)
    id_t = cola.encolar(con, regalo.TIPO_DE_TRABAJO, {"obra": obra})
    cola.tomar(con, id_t)
    assert regalo.abandonar_huerfanas(con) == 1
    assert cola.leer(con, id_t).estado.value == "abandonado"
    fase = con.execute("SELECT fase, motivo FROM progreso_de_generacion WHERE obra = ? "
                       "ORDER BY id DESC LIMIT 1", (obra,)).fetchone()
    assert fase[0] == "parada" and "reinici" in fase[1]
    con.close()


# --- PLAN-44 G1 (SPEC-44): generar ------------------------------------------------------

def test_una_novela_solo_con_entrevista_tiene_acciones_y_se_puede_generar(cliente, base):
    """`RF-02`: sin plan no hay fila en `obra`, y eso no la hace inexistente."""
    e = _entrevista(base)
    g = _acciones(cliente, e.obra)["generar"]
    assert g["posible"] is True, g
    assert g["estimacion_usd"] is not None and g["fuente"]


def test_una_entrevista_abierta_no_se_puede_generar_y_dice_por_que(cliente, base):
    e = _entrevista(base, cerrada=False)
    g = _acciones(cliente, e.obra)["generar"]
    assert g["posible"] is False and "entrevista" in g["motivo"]


def test_una_lanzada_ya_no_se_genera_sino_que_se_reanuda(cliente, base):
    obra = _escrita(cliente, base)
    _parada_en_el_4(base, obra)
    a = _acciones(cliente, obra)
    assert a["generar"]["posible"] is False and "reanud" in a["generar"]["motivo"].lower()
    assert a["reanudar"]["posible"] is True


def test_la_estimacion_de_generar_es_la_media_de_las_publicadas(cliente, base):
    con = sqlite3.connect(base)
    with con:
        for obra, usd in (("obra-p1", 4.0), ("obra-p2", 8.0)):
            con.execute("INSERT INTO progreso_de_generacion (obra, fase) VALUES (?, 'publicada')",
                        (obra,))
            con.execute("INSERT INTO gasto_de_delegacion (obra, agente, coste_usd) VALUES (?, "
                        "'escritor', ?)", (obra, usd))
    con.close()
    e = _entrevista(base)
    g = _acciones(cliente, e.obra)["generar"]
    assert g["estimacion_usd"] == pytest.approx(6.0)
    assert "2 novelas publicadas" in g["fuente"]


def test_sin_obra_ni_entrevista_es_404(cliente):
    assert cliente.get("/obras/no-existe/acciones").status_code == 404
