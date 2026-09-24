"""El Editor (`SPEC-26` `RF-09`..`RF-11`, `PLAN-26` E8).

Critica y no reescribe: nota 1-5 por criterio, con justificacion. Por debajo del
umbral, `INV-26` y otro intento con su instruccion dentro; tras 1 intento + 3
reescrituras, rendicion con los hallazgos visibles.
"""

import pathlib
import sqlite3

import pytest

from app.commons import config
from app.commons.modelo.doble import DobleDelModelo
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, obra

CRITERIOS = ["continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion"]


def _valoraciones(nota_ritmo=4, justificacion="bien resuelto"):
    return {"valoraciones": [
        {"criterio": c, "nota": nota_ritmo if c == "ritmo" else 4,
         "justificacion": justificacion,
         "instruccion": "acorta la escena del puerto" if c == "ritmo" else ""}
        for c in CRITERIOS]}


class Editor:
    nombre = "doble-editor"

    def __init__(self, respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.respuestas[min(len(self.llamadas) - 1, len(self.respuestas) - 1)]


class Resumidor:
    nombre = "doble"

    def llamar(self, prompt):
        return {"texto": "Resumen. " * 10, "hechos_clave": []}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": []})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e1", "orden": 1, "capitulo": "cap-1",
         "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": ["b"], "longitud_objetivo": [10, 5000]}])
    return c


def _generar(con, editor):
    escritor = DobleDelModelo()
    g = obra.generar_obra(con, "cap-1", escritor, editor, Resumidor(),
                          techo=1_000_000, editor=True,
                          tope_intentos=1 + config.TOPE_REESCRITURAS_DEL_EDITOR)
    return g, escritor


def test_seis_notas_de_cuatro_se_acepta_sin_reescribir(con):
    g, escritor = _generar(con, Editor([_valoraciones()]))
    assert g.escenas_hechas == ["e1"] and len(escritor.llamadas) == 1


def test_una_nota_de_dos_da_inv26_y_la_instruccion_entra_en_el_siguiente(con):
    g, escritor = _generar(con, Editor([_valoraciones(nota_ritmo=2), _valoraciones()]))
    assert g.escenas_hechas == ["e1"] and g.rendidas == []
    assert "INV-26" in escritor.llamadas[1]
    assert "acorta la escena del puerto" in escritor.llamadas[1]


def test_cuatro_rondas_por_debajo_se_rinde_con_los_hallazgos_visibles(con):
    g, escritor = _generar(con, Editor([_valoraciones(nota_ritmo=1)]))
    assert len(escritor.llamadas) == 4
    assert [r[0] for r in g.rendidas] == ["e1"]
    # `SPEC-30` v4 `RF-11`: se queda rendida tambien despues de consolidar.
    assert repo.escena(con, "e1")["estado"] == "aceptada_por_rendicion"
    assert repo.escena(con, "e1")["borrador_aceptado"] is not None
    assert any(h["invariante"] == "INV-26" for h in repo.hallazgos_abiertos(con, "e1"))


def test_una_valoracion_sin_justificacion_es_ilegible_y_no_bloquea(con):
    g, escritor = _generar(con, Editor([_valoraciones(justificacion="")]))
    assert g.escenas_hechas == ["e1"] and len(escritor.llamadas) == 1
    estados = {h[0] for h in con.execute(
        "SELECT estado FROM hallazgo WHERE invariante='INV-26'").fetchall()}
    assert estados == {"sin_veredicto"}


def test_el_editor_recibe_el_texto_y_la_rubrica(con):
    editor = Editor([_valoraciones()])
    _generar(con, editor)
    assert "personalizacion" in editor.llamadas[0] and "palabra" in editor.llamadas[0]
    assert "terror" not in editor.llamadas[0].lower()


def test_el_editor_se_lanza_aislado_sin_claude_md(tmp_path):
    definicion = pathlib.Path(__file__).resolve().parents[5] / ".claude" / "agents" / "editor.md"
    sesion = ciclo.editor_aislado(modelo="modelo-de-prueba", definicion=definicion)
    cwd = pathlib.Path(sesion.cwd)
    assert (cwd / ".claude" / "agents" / "editor.md").exists()
    assert not (cwd / "CLAUDE.md").exists() and sesion.agente == "editor"
