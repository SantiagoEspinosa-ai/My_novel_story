"""`SPEC-33` `RF-13` y cuestion 1, `PLAN-33` E9: el techo de las generaciones desde la web.

Decision literal del autor: *«Techo propio para las generaciones desde la web: 50 USD.
Separado del de la evaluacion»*. Es una decision de presupuesto, no una medida: su marca
vive con el numero, como la del techo de la evaluacion.
"""

import json
import pathlib

import pytest
from pydantic import ValidationError

from app.commons import config
from app.commons.configuracion import carga
from app.commons.configuracion.esquemas import ConfiguracionDelSistema

MODELOS = {"escritor": "m", "juez": "m", "resumidor": "m"}


def test_el_techo_de_la_web_esta_separado_del_de_la_evaluacion():
    s = ConfiguracionDelSistema.model_validate({
        "modelos": MODELOS, "evaluacion": {"techo_de_gasto_usd": 150},
        "generacion_web": {"techo_de_gasto_usd": 50}})
    assert s.generacion_web.techo_de_gasto_usd == 50
    assert s.evaluacion.techo_de_gasto_usd == 150


@pytest.mark.parametrize("techo", [0, -1])
def test_un_techo_no_positivo_no_valida(techo):
    """El error tiene que ser **el del techo**. Antes de existir `generacion_web`, esta prueba
    pasaba por otra razon -una clave desconocida tambien es un error- y no probaba nada."""
    with pytest.raises(ValidationError) as e:
        ConfiguracionDelSistema.model_validate({
            "modelos": MODELOS, "generacion_web": {"techo_de_gasto_usd": techo}})
    assert [err["loc"] for err in e.value.errors()] == [("generacion_web", "techo_de_gasto_usd")]
    assert e.value.errors()[0]["type"] == "greater_than"


def test_el_techo_de_sistema_json_es_50_y_es_una_decision_de_presupuesto():
    assert config.TECHO_DE_GASTO_GENERACION_WEB_USD == 50
    assert carga.cargar_sistema().generacion_web.techo_de_gasto_usd == 50
    fuente = pathlib.Path(config.__file__).read_text(encoding="utf-8")
    bloque = fuente[:fuente.index("TECHO_DE_GASTO_GENERACION_WEB_USD")].rsplit("\n\n", 1)[-1]
    assert "presupuesto" in bloque and "no medida" in bloque
    sistema = json.loads((pathlib.Path(carga.__file__).resolve().parents[3] / "config"
                          / "sistema.json").read_text(encoding="utf-8"))
    assert sistema["generacion_web"]["techo_de_gasto_usd"] == 50
