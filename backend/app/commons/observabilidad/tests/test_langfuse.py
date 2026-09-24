"""`PLAN-29` E10: el adaptador del SDK, las claves y `.env.example`.

Nada sale de la maquina: el SDK es un doble con las firmas de `langfuse` 4.15.4, leidas
del paquete publicado. **Lo que estas pruebas no prueban** —que el SDK real se comporte
asi— lo comprueba E13 contra la instancia. Las claves son dummy.
"""

import pathlib
import subprocess
import threading

from app.commons.observabilidad import credenciales
from app.commons.observabilidad.envio import (ScoreEnviado, SpanEnviado, TrazaEnviada,
                                              VersionDePrompt)
from app.commons.observabilidad.exportador import ExportadorNulo
from app.commons.observabilidad.langfuse import ExportadorLangfuse, crear_exportador

BACKEND = pathlib.Path(__file__).resolve().parents[4]
CLAVES = {"LANGFUSE_PUBLIC_KEY": "pk-lf-dummy-test", "LANGFUSE_SECRET_KEY": "sk-lf-dummy-test",
          "LANGFUSE_BASE_URL": "https://ejemplo.invalid"}


class Observacion_:
    def __init__(self, sdk):
        self.sdk = sdk

    def end(self):
        self.sdk.llamadas.append(("end",))


class SdkDoble:
    def __init__(self, flush_colgado=False):
        self.llamadas = []
        self._colgado = flush_colgado

    @staticmethod
    def create_trace_id(*, seed=None):
        import hashlib
        return hashlib.sha256(seed.encode()).hexdigest()[:32]

    def start_observation(self, **kw):
        self.llamadas.append(("start_observation", kw))
        return Observacion_(self)

    def create_score(self, **kw):
        self.llamadas.append(("create_score", kw))

    def create_prompt(self, **kw):
        self.llamadas.append(("create_prompt", kw))

    def flush(self):
        if self._colgado:
            threading.Event().wait(5)
        self.llamadas.append(("flush",))


def _propagar(visto):
    import contextlib

    @contextlib.contextmanager
    def propagar(**kw):
        visto.append(kw)
        yield
    return propagar


def _adaptador(**kw):
    visto = []
    sdk = SdkDoble(**kw)
    return ExportadorLangfuse(CLAVES, sdk=sdk, propagar=_propagar(visto)), sdk, visto


def _span(**kw):
    return SpanEnviado(**dict({"id": "a" * 32, "traza": "t1", "nombre": "escritor",
                               "tipo": "rol"}, **kw))


def test_sin_claves_no_hay_exportador_real_y_lo_dice(tmp_path):
    e = crear_exportador(tmp_path / ".env")
    assert isinstance(e, ExportadorNulo)
    assert "LANGFUSE_PUBLIC_KEY" in e.motivo and "LANGFUSE_SECRET_KEY" in e.motivo


def test_las_claves_se_leen_de_backend_env_y_no_entran_en_os_environ(tmp_path, monkeypatch):
    import os
    for k in CLAVES:
        monkeypatch.delenv(k, raising=False)
    env = tmp_path / ".env"
    env.write_text("# comentario\nLANGFUSE_PUBLIC_KEY=pk-lf-dummy-test\n"
                   "LANGFUSE_SECRET_KEY = \"sk-lf-dummy-test\"\nOTRA=1\n", encoding="utf-8")
    leidas = credenciales.leer(env)
    assert leidas["LANGFUSE_PUBLIC_KEY"] == "pk-lf-dummy-test"
    assert leidas["LANGFUSE_SECRET_KEY"] == "sk-lf-dummy-test"
    assert "OTRA" not in leidas
    assert "LANGFUSE_PUBLIC_KEY" not in os.environ


def test_con_claves_y_sdk_inyectado_hay_exportador_real(tmp_path):
    env = tmp_path / ".env"
    env.write_text("\n".join("{0}={1}".format(k, v) for k, v in CLAVES.items()),
                   encoding="utf-8")
    e = crear_exportador(env, sdk=SdkDoble(), propagar=_propagar([]))
    assert isinstance(e, ExportadorLangfuse)


def test_el_adaptador_traduce_un_span_sin_input_ni_output():
    a, sdk, visto = _adaptador()
    a.enviar("traza", TrazaEnviada(id="t1", nombre="generacion", sesion="ses-0123456789abcdef"))
    a.enviar("span", _span(padre="b" * 32, tokens_entrada=10, tokens_salida=5,
                           coste_usd=0.25, capitulo=3, version_de_prompt="abc123abc123"))
    nombre, kw = sdk.llamadas[0]
    assert nombre == "start_observation"
    assert "input" not in kw and "output" not in kw
    assert kw["name"] == "escritor" and kw["as_type"] == "generation"
    assert kw["usage_details"] == {"input": 10, "output": 5}
    assert kw["cost_details"] == {"total": 0.25}
    assert kw["version"] == "abc123abc123"
    assert kw["trace_context"]["parent_span_id"] == "b" * 16
    assert kw["metadata"]["capitulo"] == 3
    assert visto == [{"session_id": "ses-0123456789abcdef", "trace_name": "generacion"}]
    assert sdk.llamadas[1] == ("end",)


def test_un_coste_ausente_no_se_envia_como_cero():
    a, sdk, _ = _adaptador()
    a.enviar("traza", TrazaEnviada(id="t1", nombre="generacion", sesion="ses-x"))
    a.enviar("span", _span())
    kw = sdk.llamadas[0][1]
    assert "cost_details" not in kw and "usage_details" not in kw


def test_el_adaptador_no_manda_el_campo_modelo():
    """Con el modelo y sin coste, Langfuse podria calcular uno por su tabla de precios:
    seria una estimacion presentada como dato. Los modelos van en metadata."""
    a, sdk, _ = _adaptador()
    a.enviar("traza", TrazaEnviada(id="t1", nombre="generacion", sesion="ses-x"))
    a.enviar("span", _span(modelos=["claude-sonnet-5"]))
    kw = sdk.llamadas[0][1]
    assert "model" not in kw
    assert kw["metadata"]["modelos"] == ["claude-sonnet-5"]


def test_un_score_categorico_y_uno_numerico():
    a, sdk, _ = _adaptador()
    a.enviar("traza", TrazaEnviada(id="t1", nombre="generacion", sesion="ses-x"))
    a.enviar("score", ScoreEnviado(traza="t1", nombre="INV-28", categoria="sin_veredicto"))
    a.enviar("score", ScoreEnviado(traza="t1", nombre="INV-26.tono", valor=4, capitulo=2))
    (_, cat), (_, num) = sdk.llamadas
    assert cat["value"] == "sin_veredicto" and cat["data_type"] == "CATEGORICAL"
    assert num["value"] == 4 and num["data_type"] == "NUMERIC"
    assert num["metadata"] == {"capitulo": 2}
    assert cat["trace_id"] == num["trace_id"] == SdkDoble.create_trace_id(seed="t1")


def test_una_version_de_prompt_se_crea_con_su_huella():
    a, sdk, _ = _adaptador()
    a.enviar("prompt", VersionDePrompt(rol="escritor", version="abc123abc123",
                                       plantilla="Eres el escritor."))
    _, kw = sdk.llamadas[0]
    assert kw["name"] == "escritor" and kw["prompt"] == "Eres el escritor."
    assert kw["commit_message"] == "abc123abc123"


def test_un_flush_que_no_vuelve_es_una_perdida():
    a, _, _ = _adaptador(flush_colgado=True)
    assert a.vaciar(timeout=0.05) is False
    b, _, _ = _adaptador()
    assert b.vaciar(timeout=1) is True


def test_env_example_lista_las_variables_y_ningun_valor():
    lineas = [l.strip() for l in (BACKEND / ".env.example").read_text(encoding="utf-8")
              .splitlines() if l.strip() and not l.lstrip().startswith("#")]
    variables = dict(l.split("=", 1) for l in lineas)
    assert set(variables) >= set(CLAVES)
    assert all(v.strip() == "" for v in variables.values()), "ningun valor, ni de ejemplo"


def test_backend_env_esta_en_gitignore():
    r = subprocess.run(["git", "check-ignore", "-q", str(BACKEND / ".env")], cwd=BACKEND)
    assert r.returncode == 0
    r = subprocess.run(["git", "check-ignore", "-q", str(BACKEND / ".env.example")],
                       cwd=BACKEND)
    assert r.returncode == 1, ".env.example se versiona"
