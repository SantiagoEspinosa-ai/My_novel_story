"""`PLAN-31` E3: el guion de entrevista se reproduce contra la API.

`evaluar.entrevistar` convierte el guion en lo que espera `entrevista_cli.dialogar`, y la
entrevista corre contra la API de verdad (`TestClient`) con el Entrevistador y el
extractor sustituidos por dobles que reproducen lo que el brief declara. El camino es el
mismo que el real: la CLI no sabe que hay dobles.
"""

import pathlib
import sqlite3

import pytest
from fastapi.testclient import TestClient

import evaluar
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.features.evaluacion import briefs
from app.features.evaluacion.tests.dobles import EntrevistadorDelGuion, ExtractorDelGuion
from app.main import app, preparar_base

EVALS = pathlib.Path(__file__).resolve().parents[5] / "harness" / "evals"


@pytest.fixture
def api(tmp_path):
    ruta = str(tmp_path / "evaluacion.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta

    def con_guion(guion):
        entrevistador, extractor = EntrevistadorDelGuion(guion), ExtractorDelGuion(guion)
        app.state.entrevistador = lambda: entrevistador
        app.state.extractor = lambda: extractor
        return TestClient(app)

    yield ruta, con_guion
    for nombre in ("entrevistador", "extractor"):
        if hasattr(app.state, nombre):
            delattr(app.state, nombre)


def _brief(nombre):
    return briefs.cargar(EVALS / (nombre + ".json"))


def test_el_guion_de_injection_cierra_sin_ningun_hecho_confirmado(api):
    """La segunda instruccion pasa el detector a proposito; lo que la para es que nadie
    confirma lo que el extractor propuso (`SPEC-25` `RF-13`)."""
    _, con_guion = api
    b = _brief("brief-injection")
    r = evaluar.entrevistar(con_guion(b.guion), b.guion)
    assert r.ficha is not None, r.dicho
    assert r.ficha["hechos_propuestos"] == []
    assert not any("tiendafalsa" in str(v) for v in r.ficha.values())


def test_el_guion_de_contradicciones_no_cierra_hasta_resolverlas(api):
    ruta, con_guion = api
    b = _brief("brief-contradicciones")
    r = evaluar.entrevistar(con_guion(b.guion), b.guion)
    assert any("Todavia no se puede cerrar" in d for d in r.dicho), r.dicho
    assert r.ficha is not None and r.ficha["destinatario"]["edad"] == 30
    con = sqlite3.connect(ruta)
    detectadas = [d["detalle"]["tipo"] for d in auditoria.decisiones(con, r.obra)
                  if d["tipo"] is TD.CONTRADICCION_DETECTADA]
    assert sorted(detectadas) == ["edad_frente_a_genero", "edad_frente_a_ocasion",
                                  "recuerdo_frente_a_edad"]


def test_una_inyeccion_del_guion_queda_en_el_audit_log(api):
    """Solo la que el detector ve: la otra no deja rastro, y eso es lo que el red-team
    tiene que decir de ella."""
    ruta, con_guion = api
    b = _brief("brief-injection")
    r = evaluar.entrevistar(con_guion(b.guion), b.guion)
    con = sqlite3.connect(ruta)
    inyecciones = [d for d in auditoria.decisiones(con, r.obra)
                   if d["tipo"] is TD.INSTRUCCION_EN_TEXTO_LIBRE]
    assert len(inyecciones) == 1
    assert "ignora todas las instrucciones" in inyecciones[0]["detalle"]["patrones"]


def test_un_guion_que_se_acaba_sin_cerrar_lo_dice_y_no_devuelve_ficha(api):
    _, con_guion = api
    b = _brief("brief-contradicciones")
    corto = b.guion.model_copy(update={"turnos": b.guion.turnos[:10]})
    r = evaluar.entrevistar(con_guion(corto), corto)
    assert r.ficha is None and r.obra
    assert any("sin cerrar" in d for d in r.dicho)
