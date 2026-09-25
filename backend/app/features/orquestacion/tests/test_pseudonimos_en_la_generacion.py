"""`PLAN-34` E4: la generacion, con los nombres fuera del modelo (`SPEC-34` `RF-03`, `RF-05`,
`RF-07`).

Los dobles se montan con **la ficha pseudonimizada**: escriben con los nombres que verian,
como haria el modelo, y el pipeline tiene que restituirlos antes de guardar y de validar.
Datos inventados.
"""

import json
import re
import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.politica import pseudonimos
from app.features.entrevista.tests.conftest import ficha_completa
from app.features.evaluacion.tests import dobles
from app.features.orquestacion import novela

OBRA = "obra-p"
REALES = ("Irene", "Valdés", "Brisa", "Ramón", "Marcos", "Ledesma")


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _ficha():
    return ficha_completa(regalado_por="Ramón", nombres_vetados=["Marcos Ledesma"])


def _como_la_ve_el_modelo(con, ficha):
    tabla = pseudonimos.asegurar(con, OBRA, ficha)
    return tabla, FichaDeEntrevista.model_validate_json(
        tabla.pseudonimizar(ficha.model_dump_json()).replace(
            json.dumps(pseudonimos.MARCA_DE_VETADO), '"X"'))


def _escribir(con, tmp_path, ficha, agentes, **kw):
    return novela.escribir(con, OBRA, ficha, agentes, carpeta_de_reglas=str(tmp_path),
                           lean=dobles.LeanFijo(), **kw)


def test_ningun_prompt_de_la_generacion_lleva_un_nombre_real(con, tmp_path):
    ficha = _ficha()
    _, vista = _como_la_ve_el_modelo(con, ficha)
    prompts = []
    r = _escribir(con, tmp_path, ficha, dobles.agentes_para(vista, prompts))
    assert r["generacion"].parada is None, r["generacion"].parada
    assert prompts
    for p in prompts:
        for real in REALES:
            assert not re.search(r"(?<!\w){0}(?!\w)".format(real), p), (real, p[:300])


def test_el_texto_guardado_lleva_los_nombres_reales(con, tmp_path):
    ficha = _ficha()
    tabla, vista = _como_la_ve_el_modelo(con, ficha)
    _escribir(con, tmp_path, ficha, dobles.agentes_para(vista), hasta_capitulo=1)
    textos = [f[0] for f in con.execute("SELECT texto FROM borrador")]
    assert textos and all("Irene" in t for t in textos)
    assert not any(tabla.pares["Irene"] in t for t in textos)
    personajes = {f[0] for f in con.execute("SELECT plan FROM plan_de_obra")}
    assert any("Irene Valdés" in (p or "") for p in personajes)


def test_inv22_y_las_vetadas_miran_el_texto_restituido(con, tmp_path):
    """`RF-05`: con el texto sin restituir, `INV-22` veria un nombre que no es el de la story
    bible y pararia la escena. Que la novela llegue entera a la puerta es la prueba."""
    ficha = _ficha()
    _, vista = _como_la_ve_el_modelo(con, ficha)
    r = _escribir(con, tmp_path, ficha, dobles.agentes_para(vista))
    assert r["generacion"].parada is None
    assert r["publicacion"] is not None


def test_un_resto_en_el_texto_es_un_hallazgo_inv31(con, tmp_path):
    ficha = _ficha()
    tabla, vista = _como_la_ve_el_modelo(con, ficha)
    p = tabla.pares["Irene"]
    derivada = (p[:-1] if p[-1] in "aeiou" else p) + "ita"
    agentes = dobles.agentes_para(vista)
    escribir = agentes["escritor"].r
    agentes["escritor"].r = lambda prompt: dict(
        escribir(prompt), texto=escribir(prompt)["texto"] + " " + derivada)
    _escribir(con, tmp_path, ficha, agentes, hasta_capitulo=1)
    hallazgos = [dict(f) for f in con.execute(
        "SELECT invariante, descripcion FROM hallazgo WHERE invariante = 'INV-31'")]
    assert hallazgos and derivada in hallazgos[0]["descripcion"]


def test_las_reglas_del_hook_van_pseudonimizadas(con, tmp_path):
    """El hook compara las reglas con el texto del Escritor, que va pseudonimizado."""
    ficha = _ficha()
    tabla, vista = _como_la_ve_el_modelo(con, ficha)
    _escribir(con, tmp_path, ficha, dobles.agentes_para(vista), hasta_capitulo=1)
    reglas = json.loads((tmp_path / "reglas-{0}.json".format(OBRA)).read_text(encoding="utf-8"))
    volcado = json.dumps(reglas, ensure_ascii=False)
    for real in REALES:
        assert real not in volcado, real
    assert any(tabla.pares["Irene"] in n for n in reglas["nombres"])


def test_el_planificador_no_recibe_los_nombres_vetados(con, tmp_path):
    ficha = _ficha()
    _, vista = _como_la_ve_el_modelo(con, ficha)
    agentes = dobles.agentes_para(vista)
    _escribir(con, tmp_path, ficha, agentes, hasta_capitulo=1)
    # Los dobles comparten la lista: los prompts con la ficha son los del Planificador y el
    # Revisor. Desde `SPEC-40` la vista de los agentes ni siquiera lleva la clave.
    con_ficha = [p for p in agentes["planificador"].prompts if '"protagonista"' in p]
    assert con_ficha
    for p in con_ficha:
        assert "nombres_vetados" not in p and "Marcos" not in p
