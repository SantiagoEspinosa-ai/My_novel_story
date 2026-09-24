"""El adaptador del SDK de Langfuse, **el unico modulo que habla con la red** (`PLAN-29` E10).

Traduce los tipos de `envio.py` a la API de `langfuse` v4, que va sobre OpenTelemetry: cada
span es una observacion que se abre y se cierra en el acto, colgada de su traza y de su
padre por identificador; cada score, un `create_score`; cada version de prompt, un
`create_prompt`. La API de ingestion antigua se retira el 2026-11-16, y por eso no se usa.

TRES COSAS QUE NO SE HACEN, A PROPOSITO
---------------------------------------
- **Nunca `input` ni `output`, y nunca `@observe`**, que captura los argumentos de la
  funcion que decora: el prompt rellenado y la respuesta son justo lo que no sube.
- **Nunca el campo `model`**: con el modelo y sin coste, Langfuse puede calcular un coste
  propio por su tabla de precios, y seria una estimacion presentada como dato. Los modelos
  van en `metadata`.
- **Nunca un cero por un dato ausente**: sin tokens no hay `usage_details`, y sin coste no
  hay `cost_details`.

LO QUE NO ESTA COMPROBADO CONTRA EL SERVICIO REAL
-------------------------------------------------
Las firmas son las de `langfuse` 4.15.4, leidas del paquete publicado. Que la interfaz
cuelgue bien un span cuyo padre llega despues —los grupos se emiten al cerrarse, con su
agregado—, que la sesion se fije con `propagate_attributes`, que no se infiera coste sin
`model` y que no se exporten spans ajenos lo comprueba `PLAN-29` E13, no estas pruebas.
"""

import logging
import threading

from app.commons.observabilidad import credenciales
from app.commons.observabilidad.exportador import ExportadorNulo


def _hex16(id_):
    """Nuestros ids son 32 hex (`uuid4().hex`); un span de OpenTelemetry lleva 16."""
    return id_[:16]


class _IdsFijados:
    """Un `IdGenerator` de OpenTelemetry que da al siguiente span el id que ya tiene en
    nuestro lado. Sin esto, el hijo de un grupo apuntaria a un padre que no existe: el
    grupo se emite al cerrarse, y su id lo decidio `Observacion` al abrirlo."""

    def __init__(self):
        from opentelemetry.sdk.trace.id_generator import RandomIdGenerator
        self._azar = RandomIdGenerator()
        self._local = threading.local()

    def fijar(self, hex16):
        self._local.siguiente = int(hex16, 16)

    def generate_span_id(self):
        siguiente = getattr(self._local, "siguiente", None)
        self._local.siguiente = None
        return siguiente if siguiente is not None else self._azar.generate_span_id()

    def generate_trace_id(self):
        return self._azar.generate_trace_id()


class ErrorDelSDK(Exception):
    """`F-75`: el SDK escribio un error en su log. No se guarda el mensaje: puede citar lo
    que se intentaba enviar."""


class _ErroresDelLog(logging.Handler):
    """Cuenta los registros de nivel ERROR de los loggers del SDK. El SDK real no lanza
    cuando un envio falla: lo escribe en su log y `flush()` vuelve normal."""

    def __init__(self):
        super().__init__(level=logging.ERROR)
        self.cuenta = 0

    def emit(self, registro):
        self.cuenta += 1


LOGGERS_DEL_SDK = ("langfuse", "opentelemetry")


class ExportadorLangfuse:
    motivo = None
    error_de_vaciado = None

    def __init__(self, claves, sdk=None, propagar=None):
        self._ids = None
        if sdk is None:
            import langfuse
            self._ids = _IdsFijados()
            sdk = langfuse.Langfuse(public_key=claves["LANGFUSE_PUBLIC_KEY"],
                                    secret_key=claves["LANGFUSE_SECRET_KEY"],
                                    base_url=claves.get("LANGFUSE_BASE_URL"),
                                    id_generator=self._ids)
            propagar = propagar or langfuse.propagate_attributes
        self._sdk, self._propagar = sdk, propagar
        self._trazas = {}  # nuestro id -> (id de Langfuse, sesion, nombre)
        self._errores = _ErroresDelLog()
        for nombre in LOGGERS_DEL_SDK:
            logging.getLogger(nombre).addHandler(self._errores)
        self._errores_vistos = 0

    def enviar(self, tipo, objeto):
        getattr(self, "_" + tipo)(objeto)

    def _traza(self, t):
        self._trazas[t.id] = (self._sdk.create_trace_id(seed=t.id), t.sesion, t.nombre)

    def _span(self, s):
        id_traza, sesion, nombre = self._trazas[s.traza]
        contexto = {"trace_id": id_traza}
        if s.padre:
            contexto["parent_span_id"] = _hex16(s.padre)
        uso = {k: v for k, v in (("input", s.tokens_entrada), ("output", s.tokens_salida),
                                 ("cache_creation_input_tokens", s.tokens_cache_creados),
                                 ("cache_read_input_tokens", s.tokens_cache_leidos))
               if v is not None}
        kw = {"trace_context": contexto, "name": s.nombre,
              "as_type": {"rol": "generation", "tool": "tool"}.get(s.tipo, "span"),
              "metadata": s.model_dump(mode="json", exclude_none=True, include={
                  "tipo", "capitulo", "latencia_ms", "modelos", "coste_es_suelo",
                  "resultado", "clase_de_fallo", "validacion", "tokens_estimados"})}
        if s.version_de_prompt:
            kw["version"] = s.version_de_prompt
        if uso:
            kw["usage_details"] = uso
        if s.coste_usd is not None:
            kw["cost_details"] = {"total": s.coste_usd}
        if s.resultado == "fallo":
            kw["level"] = "ERROR"
        if self._ids is not None:
            self._ids.fijar(_hex16(s.id))
        with self._propagar(session_id=sesion, trace_name=nombre):
            self._sdk.start_observation(**kw).end()

    def _score(self, s):
        id_traza = self._trazas[s.traza][0]
        kw = {"name": s.nombre, "trace_id": id_traza,
              "value": s.valor if s.valor is not None else s.categoria.value,
              "data_type": "NUMERIC" if s.valor is not None else "CATEGORICAL",
              "metadata": s.model_dump(mode="json", exclude_none=True, include={
                  "capitulo", "nivel", "referencia", "termino", "motivo"})}
        if s.span:
            kw["observation_id"] = _hex16(s.span)
        self._sdk.create_score(**kw)

    def _prompt(self, v):
        self._sdk.create_prompt(name=v.rol, prompt=v.plantilla, commit_message=v.version,
                                labels=[], type="text")

    def vaciar(self, timeout=10):
        """`RF-09` no puede depender de que el SDK tenga timeout: `flush` va en un hilo,
        y uno que no vuelve a tiempo es una perdida."""
        resultado = {}

        def vaciar():
            try:
                self._sdk.flush()
                resultado["ok"] = True
            except Exception:  # noqa: BLE001
                resultado["ok"] = False

        hilo = threading.Thread(target=vaciar, daemon=True)
        hilo.start()
        hilo.join(timeout)
        if hilo.is_alive() or not resultado.get("ok", False):
            self.error_de_vaciado = TimeoutError()
            return False
        # `F-75`: un vaciado que termino pero dejo errores en el log del SDK tampoco llego.
        nuevos = self._errores.cuenta - self._errores_vistos
        self._errores_vistos = self._errores.cuenta
        if nuevos:
            self.error_de_vaciado = ErrorDelSDK()
            return False
        self.error_de_vaciado = None
        return True


def crear_exportador(ruta=None, sdk=None, propagar=None):
    """El real si hay claves en `backend/.env` y el paquete esta; si no, el nulo, con el
    motivo: un apagado callado se leeria como un envio que salio bien."""
    claves = credenciales.leer(ruta)
    faltan = credenciales.faltan(claves)
    if faltan:
        return ExportadorNulo("sin claves en backend/.env: faltan {0}".format(
            ", ".join(faltan)))
    try:
        return ExportadorLangfuse(claves, sdk=sdk, propagar=propagar)
    except ImportError:
        return ExportadorNulo("el paquete langfuse no esta instalado "
                              "(pip install -r requirements.txt)")
