"""`SPEC-33` `RF-18`, `RF-19`, `PLAN-33` E4: cada delegacion anota su coste.

Todas las delegaciones pasan por `SesionDelegada.llamar` -el Escritor, el Editor, el
Resumidor, el Planificador, el Revisor y el Entrevistador-, asi que se anota ahi, una vez,
y no en cada llamador. Los dobles devuelven **la misma envoltura que `claude`**
(`--output-format json`), no un diccionario con la forma que le convenga a la prueba.
"""

import json
import subprocess

import pytest

from app.commons.modelo import proveedor

RESPUESTA = '{"texto": "La puerta estaba abierta."}'


def _sobre(result=RESPUESTA, **extra):
    return json.dumps(dict({"type": "result", "result": result,
                            "usage": {"input_tokens": 5, "output_tokens": 7}}, **extra))


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv(proveedor.VARIABLES["modelo_escritor"], "modelo-de-prueba")
    monkeypatch.setenv(proveedor.VARIABLES["ejecutable"], "claude-de-mentira")


def _sesion(salida, anotadas):
    s = proveedor.SesionDelegada(agente="escritor", ejecutar=salida)
    s.anotador = lambda agente, coste_usd: anotadas.append((agente, coste_usd))
    return s


def test_cada_delegacion_anota_su_coste(entorno):
    anotadas = []
    s = _sesion(lambda *a, **k: _sobre(total_cost_usd=0.0421), anotadas)
    s.llamar("x")
    s.llamar("y")
    assert anotadas == [("escritor", 0.0421), ("escritor", 0.0421)]


def test_una_delegacion_sin_coste_anota_ausente_y_no_cero(entorno):
    anotadas = []
    _sesion(lambda *a, **k: _sobre(), anotadas).llamar("x")
    assert anotadas == [("escritor", None)]


def test_una_respuesta_sin_envoltura_anota_ausente(entorno):
    """Un formato viejo o un doble sin sobre: la delegacion ocurrio y no trae coste."""
    anotadas = []
    _sesion(lambda *a, **k: RESPUESTA, anotadas).llamar("x")
    assert anotadas == [("escritor", None)]


def test_una_respuesta_ilegible_anota_lo_que_costo(entorno):
    """Se pago igual (`PLAN-29` E1): su coste viaja en la excepcion y se anota."""
    anotadas = []
    s = _sesion(lambda *a, **k: _sobre(result="no es json", total_cost_usd=0.07), anotadas)
    with pytest.raises(proveedor.RespuestaIlegible):
        s.llamar("x")
    assert anotadas == [("escritor", 0.07)]


def test_un_fallo_de_transporte_anota_sin_coste(entorno):
    anotadas = []

    def revienta(*a, **k):
        raise subprocess.TimeoutExpired("claude", 1)

    with pytest.raises(proveedor.FalloDeTransporte):
        _sesion(revienta, anotadas).llamar("x")
    assert anotadas == [("escritor", None)]


def test_sin_anotador_la_sesion_no_cambia(entorno):
    s = proveedor.SesionDelegada(ejecutar=lambda *a, **k: _sobre(total_cost_usd=0.01))
    r = s.llamar("x")
    assert r["texto"] == "La puerta estaba abierta."
    assert r["medidas"]["coste_usd"] == 0.01


def test_un_anotador_que_falla_no_se_calla(entorno):
    """Entre perder el coste en silencio y fallar a la vista, a la vista."""
    s = proveedor.SesionDelegada(ejecutar=lambda *a, **k: _sobre(total_cost_usd=0.01))

    def roto(agente, coste_usd):
        raise RuntimeError("la base no acepto el gasto")

    s.anotador = roto
    with pytest.raises(RuntimeError, match="no acepto el gasto"):
        s.llamar("x")
