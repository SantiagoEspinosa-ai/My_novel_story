"""La delegación en una sesión de Claude Code. **No hay API ni clave.**

QUE CAMBIA RESPECTO A LA PRIMERA VERSION
-----------------------------------------
La primera version de este modulo hablaba HTTP con cabeceras y un `Bearer`.
`SPEC-14` la retiro entera: el harness delega en sesiones y **ningun codigo
suyo toca la red**. Lo que queda es un adaptador a un proceso, con la misma
firma que el doble -`llamar(prompt) -> dict`- para que el bucle probado en
`PLAN-01` E2 sea el mismo que corra de verdad.

DOS COSAS DE ENTORNO QUE NO SE DISCUTEN, PORQUE YA SE PAGARON
--------------------------------------------------------------
Son hallazgos 13 y 14 de `DECISIONES.md` de la rama `main`, y son conocimiento
de entorno y no decisiones de diseno:

1. **En Windows `claude` no es un ejecutable, es un `.CMD`.**
   `subprocess.run(["claude", ...])` da `FileNotFoundError` mientras
   `claude --version` funciona perfectamente en la terminal. Hay que resolver
   la ruta y arrancarlo con `shell=True` o con su ruta absoluta.

2. **El prompt va por stdin, nunca como argumento.** Al pasar por `cmd.exe`, su
   analizador de linea de comandos **termina el comando en el primer salto de
   linea**, y el prompt llega truncado sin que nada avise. Costo un `502` que
   parecia un problema de prompt: *"no era el prompt: era el transporte"*.

EL AISLAMIENTO SE CONSIGUE POR DIRECTORIO, NO POR `omitClaudeMd`
-----------------------------------------------------------------
`SPEC-11` C-4 dice que el Juez no ve las reglas del proyecto, y su mecanismo
declarado era `omitClaudeMd: true` en la definicion del subagente. **Se
comprobo en la version 2.1.274 y no funciona.** La comprobacion fue controlada:

    omitClaudeMd: false  -> enumero los seis niveles del presupuesto, exactos
    omitClaudeMd: true   -> enumero los seis niveles del presupuesto, exactos
    cuerpo del agente    -> SI se aplica (un marcador arbitrario aparecio)
    cwd sin CLAUDE.md    -> "NO LO SE"

Es decir: la definicion del agente **si** se carga y la opcion **se ignora en
silencio**, que es justo lo que el hallazgo 3 de `DECISIONES.md` advertia que
pasa con lo que el frontmatter no reconoce.

Lo que si aisla es **el directorio de trabajo**: `claude` carga `CLAUDE.md`
desde el arbol del `cwd`, asi que una delegacion lanzada desde un directorio
vacio no lo ve. Por eso `_ejecutar_proceso` acepta `cwd` y el Juez se lanzara
desde uno aislado.

**Y no basta con el directorio.** Un agente con herramientas de lectura puede
ir a buscar el fichero: el propio agente aislado ofrecio hacerlo. El
aislamiento es **directorio sin `CLAUDE.md` mas ninguna herramienta que lea el
proyecto**.

EL PARSEO ES DESCONFIADO A PROPOSITO
-------------------------------------
Aunque el prompt prohiba las vallas de bloque de codigo, **las anade la sesion
intermedia al imprimir la respuesta**, no el modelo (hallazgo 7). Asi que se
intenta rescatar el JSON de tres formas antes de rendirse: directo, quitando
vallas, y extrayendo el primer objeto equilibrado. Perder una escena entera por
tres acentos graves seria absurdo.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import uuid

from app.commons.politica.herramientas import PERMITIDAS, SERVIDOR

VARIABLES = {
    "ejecutable": "HARNESS_CLAUDE_BIN",
    "modelo_escritor": "HARNESS_MODELO_ESCRITOR",
    "modelo_juez": "HARNESS_MODELO_JUEZ",
}


# `backend/app/commons/modelo/proveedor.py` -> la raiz, donde viven `.claude/`.
RAIZ_DEL_REPOSITORIO = pathlib.Path(__file__).resolve().parents[4]


class FaltaEntorno(RuntimeError):
    pass


class FalloDeTransporte(Exception):
    """El proceso no arranco, no respondio o murio. Por `O-3` **si** se reintenta."""


class RespuestaIlegible(Exception):
    """Ni siquiera el parseo desconfiado pudo sacar un objeto. Es fallo de
    **contrato**: por `O-3` no se reintenta sin cambiar nada."""


def _resolver_ejecutable():
    """Hallazgo 13: `claude` es un `.CMD` y `shutil.which` sí lo encuentra."""
    ruta = os.environ.get(VARIABLES["ejecutable"]) or shutil.which("claude")
    if not ruta:
        raise FaltaEntorno(
            "no se encuentra el ejecutable de Claude Code. Ponlo en {0} o "
            "asegurate de que `claude` esta en el PATH".format(VARIABLES["ejecutable"])
        )
    return ruta


def quitar_vallas(texto: str) -> str:
    """Quita ```json ... ``` si los anadio alguien por el camino."""
    t = (texto or "").strip()
    if t.startswith("```"):
        t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
        t = re.sub(r"\s*```$", "", t)
    return t.strip()


def primer_objeto_equilibrado(texto: str):
    """Extrae el primer `{...}` con las llaves balanceadas.

    No usa una expresion regular: las llaves anidadas no son un lenguaje
    regular, y una que lo intente corta en el primer `}` interior.
    """
    inicio = texto.find("{")
    if inicio == -1:
        return None
    profundidad = 0
    for i in range(inicio, len(texto)):
        if texto[i] == "{":
            profundidad += 1
        elif texto[i] == "}":
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio:i + 1]
    return None


def interpretar(bruto: str) -> dict:
    """Tres intentos antes de rendirse, en orden de menos a mas invasivo."""
    for candidato in (bruto, quitar_vallas(bruto), primer_objeto_equilibrado(bruto or "")):
        if not candidato:
            continue
        try:
            datos = json.loads(candidato)
        except (ValueError, TypeError):
            continue
        if isinstance(datos, dict):
            return datos
    raise RespuestaIlegible(
        "no se pudo interpretar la respuesta como objeto JSON tras quitar "
        "vallas y extraer el primer objeto equilibrado"
    )


class SesionDelegada:
    """Misma firma que `DobleDelModelo`. El bucle no distingue."""

    def __init__(self, modelo=None, agente=None, ejecutar=None, cwd=None):
        self.nombre = modelo or os.environ.get(VARIABLES["modelo_escritor"])
        if not self.nombre:
            raise FaltaEntorno(
                "falta {0}: el modelo se fija al construir, porque `SPEC-11` C-3 "
                "lo quiere fijo dentro de una obra".format(VARIABLES["modelo_escritor"])
            )
        self.agente = agente
        # `cwd` aisla: `claude` carga CLAUDE.md desde el arbol del directorio
        # de trabajo. Sin `cwd` se arranca en la **raiz del repositorio**, que
        # es lo que quiere el Escritor; el Juez y el Editor se lanzan desde uno
        # aislado. `F-61`: antes `None` heredaba el directorio del proceso
        # -`backend/` en los guiones- y Claude Code, que solo lee
        # `.claude/settings.json` de la carpeta donde arranca, no cargaba los
        # hooks. Se midio con dos sesiones minimas identicas.
        self.cwd = cwd if cwd is not None else str(RAIZ_DEL_REPOSITORIO)
        self._ejecutar = ejecutar or _ejecutar_proceso
        # `SPEC-26`: lo que leen los hooks. Se fija desde fuera, por obra: la
        # ruta de las reglas del capitulo y donde apuntar lo que nieguen.
        self.reglas = None
        self.entorno = {}
        # `SPEC-28`: si se fija (`{"db", "obra"}`), la delegacion ofrece las tools de
        # la story bible por un servidor MCP. Solo el Escritor y el Editor lo tienen.
        self.herramientas = None

    def __repr__(self):
        return "SesionDelegada(modelo={0!r}, agente={1!r})".format(self.nombre, self.agente)

    def llamar(self, prompt: str) -> dict:
        """Devuelve la respuesta normalizada con sus `medidas` dentro."""
        try:
            extra = {}
            if self.reglas:
                extra["reglas"] = self.reglas
            if self.entorno:
                extra["entorno"] = self.entorno
            delegacion = None
            if self.herramientas:
                # Una por llamada: enlaza cada llamada a una tool con su traza.
                delegacion = uuid.uuid4().hex
                extra["herramientas"] = dict(self.herramientas, delegacion=delegacion)
            salida = self._ejecutar(_resolver_ejecutable(), self.nombre,
                                    self.agente, prompt, self.cwd, **extra)
        except FalloDeTransporte:
            raise
        except (OSError, subprocess.SubprocessError) as e:
            # Se envuelve tambien aqui y no solo en `_ejecutar_proceso` porque
            # el ejecutor es inyectable: un doble que reviente tiene que
            # producir el mismo fallo que el proceso real, o la prueba estaria
            # verificando un camino que no existe.
            raise FalloDeTransporte(
                "la delegacion no completo: {0}".format(type(e).__name__)) from None
        sobre = interpretar(salida)
        # La envoltura de `--output-format json` trae el texto del modelo en
        # `result` y las medidas al lado. Si no viene envuelta -un doble, o un
        # formato viejo- se interpreta como la respuesta misma.
        if "result" in sobre and "type" in sobre:
            respuesta = _normalizar(interpretar(sobre["result"]))
            respuesta["medidas"] = medidas_de(sobre)
            if delegacion:
                respuesta["medidas"]["delegacion"] = delegacion
            return respuesta
        return _normalizar(sobre)


SERVIDOR_DE_LA_STORY_BIBLE = RAIZ_DEL_REPOSITORIO / "backend" / "herramientas" / "story_bible.py"


def _configuracion_mcp(agente, herramientas):
    """`SPEC-28`: el servidor de la story bible, **en un fichero** y no como cadena. La
    orden pasa por un `.CMD`, y un JSON con comillas como argumento corre el riesgo de
    pasar por `cmd.exe` (hallazgo 13)."""
    datos = {"mcpServers": {SERVIDOR: {
        "command": sys.executable, "args": [str(SERVIDOR_DE_LA_STORY_BIBLE)],
        "env": {"HARNESS_DB": os.path.abspath(herramientas["db"]),
                "HARNESS_OBRA": herramientas["obra"], "HARNESS_AGENTE": agente or "",
                "HARNESS_DELEGACION": herramientas["delegacion"]}}}}
    fd, ruta = tempfile.mkstemp(prefix="mcp-", suffix=".json")
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False)
    return ruta


def _ejecutar_proceso(ejecutable, modelo, agente, prompt, cwd=None, reglas=None,
                      entorno=None, herramientas=None):
    """El prompt por **stdin**. Nunca como argumento: `cmd.exe` lo trunca.

    Se pide `--output-format json` porque devuelve **medidas de verdad**:
    `usage` con los tokens, `total_cost_usd` con el coste, y `modelUsage` con
    el desglose **por modelo**. `SPEC-14` C-3 supuso que los tokens los
    reportaria a mano la sesion y serian un suelo; con esto son una medida.
    """
    orden = [ejecutable, "-p", "--output-format", "json", "--model", modelo]
    if agente:
        # `PLAN-28` `D-2`: toda delegacion del pipeline apaga las herramientas
        # integradas; las unicas que quedan son las MCP que se le den abajo.
        orden += ["--agent", agente, "--tools", ""]
    config_mcp = None
    if herramientas:
        config_mcp = _configuracion_mcp(agente, herramientas)
        orden += ["--mcp-config", config_mcp, "--strict-mcp-config",
                  "--allowedTools", ",".join(PERMITIDAS.get(agente, ()))]
    # `SPEC-26` `RF-19`: los hooks solo actuan si ven `HARNESS_AGENTE`, y solo
    # lo ponemos aqui. Una sesion interactiva en el mismo proyecto no lo tiene.
    env = dict(os.environ, **(entorno or {}))
    if agente:
        env["HARNESS_AGENTE"] = agente
    if reglas:
        env["HARNESS_REGLAS"] = reglas
    try:
        r = subprocess.run(orden, input=prompt, capture_output=True,
                           text=True, encoding="utf-8", timeout=600, cwd=cwd,
                           env=env)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise FalloDeTransporte(
            "la delegacion no completo: {0}".format(type(e).__name__)
        ) from None
    finally:
        if config_mcp and os.path.exists(config_mcp):
            os.remove(config_mcp)
    if r.returncode != 0:
        raise FalloDeTransporte(
            "la delegacion termino con codigo {0}".format(r.returncode))
    return r.stdout


def medidas_de(sobre: dict) -> dict:
    """Saca de la envoltura JSON lo que hay que registrar en la traza.

    `modelos` es una **lista**, no un valor: una sola delegacion puede usar mas
    de un modelo -se midio: una llamada sin `--model` reporto `haiku` y `opus`
    en la misma respuesta-. Quien compruebe el modelo fijo tiene que saberlo.
    """
    uso = sobre.get("usage") or {}
    return {
        "tokens_entrada": uso.get("input_tokens"),
        "tokens_salida": uso.get("output_tokens"),
        "tokens_cache_creados": uso.get("cache_creation_input_tokens"),
        "tokens_cache_leidos": uso.get("cache_read_input_tokens"),
        "coste_usd": sobre.get("total_cost_usd"),
        "modelos": sorted((sobre.get("modelUsage") or {}).keys()),
        "duracion_ms": sobre.get("duration_ms"),
    }


def _normalizar(datos: dict) -> dict:
    """Devuelve la respuesta **tal cual**, sin imponerle ninguna forma.

    La primera version devolvia `{"texto": ..., "delta": ...}` porque era la
    forma del Escritor, y **se la imponia a todos**: en la primera ejecucion
    del ciclo completo el veredicto del Juez salio `None` y los `hechos_clave`
    del Resumidor se perdieron, sin que nada fallara. El ciclo informo exito
    habiendo tirado el juicio.

    Es la Regla 4 otra vez: **la forma de una respuesta es cosa del contrato de
    su agente, no del transporte**. El transporte entrega lo que llego; quien
    sabe que forma espera es quien la pidio.

    Lo unico que se toca es `delta` cuando llega como cadena, porque eso es un
    artefacto del transporte -un JSON dentro de un JSON- y no una decision del
    agente.
    """
    salida = dict(datos)
    if isinstance(salida.get("delta"), str):
        try:
            salida["delta"] = json.loads(salida["delta"])
        except ValueError:
            salida["delta"] = None
    if "texto" not in salida and "content" in salida:
        salida["texto"] = salida["content"]
    return salida
