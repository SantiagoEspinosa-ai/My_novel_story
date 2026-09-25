"""`SPEC-33` `RF-11`, `RF-18`, `RF-21`, `PLAN-33` E5: los agentes de la novela regalo, en un
solo sitio y anotando su gasto.

`agentes()` vivia en `novela_regalo.py`. Si el lanzamiento desde la web lo copiara habria
dos pipelines; por eso se mueve aqui y los dos lo llaman. Las sesiones son
`SesionDelegada` de verdad: lo unico doble es el proceso, que devuelve **la misma envoltura
que `claude`** con el texto de los dobles de `test_novela` y un coste conocido por agente.
"""

import importlib.util
import json
import pathlib
import sqlite3

import pytest

from app.commons.configuracion.esquemas import ConfiguracionDelSistema
from app.commons.db import migraciones
from app.commons.modelo import gasto
from app.features.orquestacion import novela, regalo
from app.features.orquestacion.tests.test_novela import (
    _agentes_para_la_novela_entera, _LeanFijo)
from app.features.planificacion.tests.conftest import ficha

# Costes distintos por agente, a proposito: si dos agentes costaran lo mismo, una suma
# que confundiera cual se anoto pasaria igual.
COSTE = {"planificador": 0.5, "revisor_plan": 0.25, "escritor": 0.125, "editor": 0.0625,
         "resumidor": 0.03125}
MODELOS = {n: "modelo-de-prueba" for n in
           ("planificador", "revisor_plan", "editor", "escritor", "resumidor", "juez")}
_NOMBRE_DEL_DOBLE = {"revisor_plan": "revisor"}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _proceso(dobles, sin_coste=()):
    """Un `_ejecutar` que responde con el doble del agente, dentro de su envoltura."""

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None, **kw):
        respuesta = dobles[_NOMBRE_DEL_DOBLE.get(agente, agente)].llamar(prompt)
        sobre = {"type": "result", "result": json.dumps(respuesta),
                 "usage": {"input_tokens": 1, "output_tokens": 1}}
        if agente not in sin_coste:
            sobre["total_cost_usd"] = COSTE[agente]
        return json.dumps(sobre)

    return ejecutar


def _sistema():
    return ConfiguracionDelSistema.model_validate({"modelos": MODELOS})


def _escribir(con, tmp_path, sin_coste=()):
    anotar = gasto.anotador(con, obra="obra-x", generacion="gen-1")
    ag = regalo.agentes(_sistema(), {}, anotar=anotar,
                        ejecutar=_proceso(_agentes_para_la_novela_entera(), sin_coste))
    r = novela.escribir(con, "obra-x", ficha(), ag, carpeta_de_reglas=str(tmp_path),
                        lean=_LeanFijo(), sistema=_sistema())
    return r, ag


def test_todos_los_agentes_de_la_generacion_anotan(con, tmp_path):
    """Los cinco de `agentes()` y el juez de la puerta, que es el Editor en un `Contador`."""
    _escribir(con, tmp_path)
    anotados = {f[0] for f in con.execute("SELECT DISTINCT agente FROM gasto_de_delegacion")}
    assert anotados == set(COSTE), anotados


def test_el_total_anotado_cuadra_con_el_informe_de_la_cli(con, tmp_path):
    """`RF-21`: si no cuadran, uno de los dos cuenta mal."""
    r, ag = _escribir(con, tmp_path)
    total = regalo.coste_total(r, ag)
    usd, n = con.execute("SELECT SUM(coste_usd), COUNT(*) FROM gasto_de_delegacion").fetchone()
    assert n == total["delegaciones"]
    assert usd == pytest.approx(total["usd"])
    assert total["sin_coste"] == 0


def test_una_delegacion_sin_coste_no_suma_y_se_cuenta(con, tmp_path):
    r, ag = _escribir(con, tmp_path, sin_coste=("resumidor",))
    total = regalo.coste_total(r, ag)
    nulos = con.execute("SELECT COUNT(*) FROM gasto_de_delegacion "
                        "WHERE coste_usd IS NULL").fetchone()[0]
    assert nulos == total["sin_coste"] > 0


def test_novela_regalo_usa_los_agentes_de_app():
    """No queda una segunda copia de `agentes()` en el guion."""
    ruta = pathlib.Path(__file__).resolve().parents[4] / "novela_regalo.py"
    spec = importlib.util.spec_from_file_location("novela_regalo", ruta)
    guion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guion)
    assert guion.agentes is regalo.agentes
    assert guion.coste_total is regalo.coste_total


# --- `PLAN-41` R2: el techo entre capitulos (`SPEC-41` `RF-03`) ---------------------------

def test_la_generacion_web_se_para_entre_capitulos_al_llegar_al_techo(con, tmp_path):
    """Con un techo por debajo de lo que cuesta un capitulo, la generacion se para al terminar
    el primero, con el motivo `techo_de_gasto`, y no llega a escribir el segundo."""
    from app.commons.configuracion.esquemas import ConfiguracionDelSistema
    from app.features.orquestacion.tests.test_lanzar import _entrevista  # noqa: F401
    from app.features.planificacion.tests.conftest import ficha as ficha_de_prueba
    sistema = ConfiguracionDelSistema.model_validate(
        {"modelos": MODELOS, "generacion_web": {"techo_de_gasto_usd": 0.9}})

    def fabrica(s, entorno, anotar):
        return regalo.agentes(s, entorno, anotar=anotar,
                              ejecutar=_proceso(_agentes_para_la_novela_entera()))
    r = regalo.generar(con, ":memory:", "obra-x", ficha_de_prueba(), "gen-1", sistema,
                       fabrica=fabrica, lean=_LeanFijo())
    assert r["parada"]["motivo"] == "techo_de_gasto", r["parada"]
    assert r["parada"]["tras_capitulo"] == 1
