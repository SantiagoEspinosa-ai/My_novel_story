"""`PLAN-29` E3: la interfaz, su doble y la sesion observada.

Nada sale de la maquina: el exportador es `ExportadorEnMemoria`, que puede portarse mal a
peticion para probar `RF-09`.
"""

import sqlite3

import pytest

from app.commons.observabilidad import perdidas
from app.commons.observabilidad.exportador import ExportadorEnMemoria, ExportadorNulo
from app.commons.observabilidad.observacion import Observacion, SesionObservada

PROMPT = "PROMPT-SECRETO-4417 con la ficha rellenada"
RESPUESTA = {"texto": "RESPUESTA-SECRETA-9923", "delta": {},
             "medidas": {"tokens_entrada": 100, "tokens_salida": 50, "coste_usd": 0.02,
                         "modelos": ["m-1"], "duracion_ms": 1234}}


class Sesion:
    def __init__(self, respuesta=None, error=None):
        self.nombre, self.agente = "m-1", "escritor"
        self.reglas, self.entorno, self.herramientas = None, {}, None
        self._r, self._e = respuesta, error

    def llamar(self, prompt):
        if self._e:
            raise self._e
        return dict(self._r)


@pytest.fixture
def con():
    return sqlite3.connect(":memory:")


def _obs(con, **kw):
    return Observacion(ExportadorEnMemoria(**kw), con=con, obra="obra-a", nombre="generacion")


def test_la_sesion_observada_devuelve_lo_mismo_que_la_sesion(con):
    s = SesionObservada(Sesion(RESPUESTA), _obs(con), rol="escritor")
    assert s.llamar(PROMPT) == RESPUESTA


def test_la_sesion_observada_emite_un_span_con_las_medidas_del_sobre(con):
    obs = _obs(con)
    SesionObservada(Sesion(RESPUESTA), obs, rol="escritor").llamar(PROMPT)
    span = [e for t, e in obs.exportador.enviados if t == "span"][0]
    assert span["nombre"] == "escritor" and span["tipo"] == "rol"
    assert span["coste_usd"] == 0.02 and span["tokens_entrada"] == 100
    assert span["latencia_ms"] == 1234 and span["modelos"] == ["m-1"]


def test_la_sesion_observada_no_guarda_el_prompt_ni_la_respuesta(con):
    obs = _obs(con)
    s = SesionObservada(Sesion(RESPUESTA), obs, rol="escritor")
    s.llamar(PROMPT)
    todo = repr(vars(s)) + repr(vars(obs)) + repr(obs.exportador.enviados)
    assert "PROMPT-SECRETO-4417" not in todo
    assert "RESPUESTA-SECRETA-9923" not in todo


def test_la_sesion_observada_deja_pasar_reglas_entorno_y_nombre(con):
    interna = Sesion(RESPUESTA)
    s = SesionObservada(interna, _obs(con), rol="escritor")
    s.reglas = "reglas.json"
    s.entorno = {"HARNESS_DB": "x.db"}
    s.herramientas = {"db": "x.db", "obra": "obra-a"}
    assert interna.reglas == "reglas.json" and interna.entorno == {"HARNESS_DB": "x.db"}
    assert interna.herramientas == {"db": "x.db", "obra": "obra-a"}
    assert s.nombre == "m-1" and s.agente == "escritor"


def test_una_excepcion_del_modelo_sale_igual_y_deja_span_con_su_clase(con):
    from app.commons.modelo.proveedor import RespuestaIlegible
    obs = _obs(con)
    error = RespuestaIlegible("texto ilegible con DATO-7781", medidas={"coste_usd": 0.03})
    s = SesionObservada(Sesion(error=error), obs, rol="editor")
    with pytest.raises(RespuestaIlegible) as e:
        s.llamar(PROMPT)
    assert e.value is error
    span = [e for t, e in obs.exportador.enviados if t == "span"][0]
    assert span["resultado"] == "fallo" and span["clase_de_fallo"] == "RespuestaIlegible"
    assert span["coste_usd"] == 0.03
    assert "DATO-7781" not in repr(obs.exportador.enviados)


def test_si_el_exportador_revienta_la_llamada_devuelve_igual_y_queda_una_perdida(con):
    obs = _obs(con, falla=True)
    s = SesionObservada(Sesion(RESPUESTA), obs, rol="escritor")
    assert s.llamar(PROMPT) == RESPUESTA
    assert [p["tipo"] for p in perdidas.de(con)] == ["traza", "span"]


def test_la_perdida_guarda_la_clase_del_error_y_no_su_mensaje(con):
    obs = _obs(con, falla=True, mensaje="conexion rechazada para MENSAJE-SECRETO-551")
    SesionObservada(Sesion(RESPUESTA), obs, rol="escritor").llamar(PROMPT)
    filas = perdidas.de(con)
    assert filas and all(p["clase"] == "ConnectionError" for p in filas)
    assert "MENSAJE-SECRETO-551" not in repr(filas)


def test_un_score_se_asocia_a_la_traza_abierta(con):
    obs = _obs(con)
    obs.score(nombre="INV-21", categoria="pasa", capitulo=1)
    traza = [e for t, e in obs.exportador.enviados if t == "traza"][0]
    score = [e for t, e in obs.exportador.enviados if t == "score"][0]
    assert score["traza"] == traza["id"]


def test_los_spans_dentro_de_un_grupo_cuelgan_de_el(con):
    obs = _obs(con)
    with obs.grupo("capitulo", capitulo=3) as padre:
        SesionObservada(Sesion(RESPUESTA), obs, rol="escritor").llamar(PROMPT)
    spans = [e for t, e in obs.exportador.enviados if t == "span"]
    rol = [s for s in spans if s["tipo"] == "rol"][0]
    assert rol["padre"] == padre and rol["capitulo"] == 3


def test_el_exportador_nulo_no_envia_nada_y_dice_por_que(con):
    obs = Observacion(ExportadorNulo("sin claves en backend/.env"), con=con, obra="obra-a",
                      nombre="generacion")
    assert SesionObservada(Sesion(RESPUESTA), obs, rol="escritor").llamar(PROMPT) == RESPUESTA
    assert obs.exportador.motivo == "sin claves en backend/.env"
    assert perdidas.de(con) == []


# --- `PLAN-29` E5: los agregados de un grupo --------------------------------------

def _con_coste(coste):
    return dict(RESPUESTA, medidas=dict(RESPUESTA["medidas"], coste_usd=coste))


def _grupo(obs, nombre):
    return [e for t, e in obs.exportador.enviados if t == "span" and e["nombre"] == nombre][0]


def test_el_agregado_del_capitulo_con_una_llamada_sin_coste_es_suelo_y_lo_dice(con):
    obs = _obs(con)
    with obs.grupo("capitulo", capitulo=1):
        SesionObservada(Sesion(_con_coste(0.02)), obs, rol="escritor").llamar(PROMPT)
        SesionObservada(Sesion(_con_coste(None)), obs, rol="editor").llamar(PROMPT)
    g = _grupo(obs, "capitulo")
    assert g["coste_usd"] == 0.02 and g["coste_es_suelo"] is True


def test_un_grupo_sin_ningun_coste_lo_envia_ausente_y_no_en_cero(con):
    obs = _obs(con)
    with obs.grupo("capitulo", capitulo=1):
        SesionObservada(Sesion(_con_coste(None)), obs, rol="escritor").llamar(PROMPT)
    g = _grupo(obs, "capitulo")
    assert "coste_usd" not in g and "coste_es_suelo" not in g


def test_el_agregado_de_la_novela_suma_sus_capitulos(con):
    obs = _obs(con)
    with obs.grupo("novela"):
        for n in (1, 2):
            with obs.grupo("capitulo", capitulo=n):
                SesionObservada(Sesion(_con_coste(0.25)), obs, rol="escritor").llamar(PROMPT)
    g = _grupo(obs, "novela")
    assert g["coste_usd"] == 0.5 and g["coste_es_suelo"] is False
    assert g["tokens_entrada"] == 200


def test_un_vaciado_que_no_termina_deja_una_perdida(con):
    class Colgado(ExportadorEnMemoria):
        def vaciar(self, timeout=None):
            return False

    obs = Observacion(Colgado(), con=con, obra="obra-a")
    assert obs.vaciar(0.01) is False
    assert [p["tipo"] for p in perdidas.de(con)] == ["vaciado"]
