"""`PLAN-25` E10: la CLI fina.

Se prueba contra la API de verdad (`TestClient` es un cliente `httpx`) con el
doble del Entrevistador, asi que el camino es el mismo que el real: la CLI no
sabe que hay un doble, solo habla HTTP.
"""

import ast
import pathlib

import pytest
from fastapi.testclient import TestClient

import entrevista_cli
from app.features.entrevista.tests.conftest import ficha_completa
from app.main import app, preparar_base


class Guion:
    nombre = "doble"

    def __init__(self, fichas):
        self.fichas, self.i = fichas, 0

    def llamar(self, prompt):
        f = self.fichas[min(self.i, len(self.fichas) - 1)]
        self.i += 1
        return {"ficha": f, "pregunta": "pregunta {0}".format(self.i)}


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    completa = ficha_completa().model_dump(mode="json")
    solo_nombre = {"destinatario": {"nombre": "Irene Valdés"}}
    con_edad = {"destinatario": {"nombre": "Irene Valdés", "edad": 34}}
    agente = Guion([solo_nombre, con_edad, completa])
    app.state.entrevistador = lambda: agente
    yield TestClient(app)
    del app.state.entrevistador


def test_un_dialogo_de_tres_turnos_llega_al_brief(cliente):
    respuestas = iter(["Irene Valdés", "34", "le encantan los mapas", ":cerrar"])
    dicho = []
    brief = entrevista_cli.dialogar(cliente, entrada=lambda _: next(respuestas),
                                    salida=dicho.append, espera=0)
    assert brief["destinatario"]["nombre"] == "Irene Valdés"
    texto = "\n".join(dicho)
    assert "10 capitulos" in texto and "pregunta 3" in texto


def test_cerrar_antes_de_tiempo_dice_lo_que_falta_y_sigue(cliente):
    respuestas = iter([":cerrar", ":salir"])
    dicho = []
    assert entrevista_cli.dialogar(cliente, entrada=lambda _: next(respuestas),
                                   salida=dicho.append, espera=0) is None
    assert any("nombre" in d for d in dicho)


def test_la_cli_no_importa_ninguna_feature():
    """Si importara `app.features`, podria tener logica propia sin que se viera."""
    fuente = pathlib.Path(entrevista_cli.__file__).read_text(encoding="utf-8")
    modulos = [n.module or "" for n in ast.walk(ast.parse(fuente))
               if isinstance(n, ast.ImportFrom)]
    modulos += [a.name for n in ast.walk(ast.parse(fuente))
                if isinstance(n, ast.Import) for a in n.names]
    assert not [m for m in modulos if m.startswith("app")]
