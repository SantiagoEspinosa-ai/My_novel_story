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
import re
import shutil
import subprocess

VARIABLES = {
    "ejecutable": "HARNESS_CLAUDE_BIN",
    "modelo_escritor": "HARNESS_MODELO_ESCRITOR",
    "modelo_juez": "HARNESS_MODELO_JUEZ",
}


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
        # de trabajo. `None` significa el del proyecto, que es lo que quiere el
        # Escritor; el Juez se lanza desde uno vacio.
        self.cwd = cwd
        self._ejecutar = ejecutar or _ejecutar_proceso

    def __repr__(self):
        return "SesionDelegada(modelo={0!r}, agente={1!r})".format(self.nombre, self.agente)

    def llamar(self, prompt: str) -> dict:
        """Devuelve la respuesta normalizada con sus `medidas` dentro."""
        try:
            salida = self._ejecutar(_resolver_ejecutable(), self.nombre,
                                    self.agente, prompt, self.cwd)
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
            return respuesta
        return _normalizar(sobre)


def _ejecutar_proceso(ejecutable, modelo, agente, prompt, cwd=None):
    """El prompt por **stdin**. Nunca como argumento: `cmd.exe` lo trunca.

    Se pide `--output-format json` porque devuelve **medidas de verdad**:
    `usage` con los tokens, `total_cost_usd` con el coste, y `modelUsage` con
    el desglose **por modelo**. `SPEC-14` C-3 supuso que los tokens los
    reportaria a mano la sesion y serian un suelo; con esto son una medida.
    """
    orden = [ejecutable, "-p", "--output-format", "json", "--model", modelo]
    if agente:
        orden += ["--agent", agente]
    try:
        r = subprocess.run(orden, input=prompt, capture_output=True,
                           text=True, encoding="utf-8", timeout=600, cwd=cwd)
    except (OSError, subprocess.TimeoutExpired) as e:
        raise FalloDeTransporte(
            "la delegacion no completo: {0}".format(type(e).__name__)
        ) from None
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
    """Deja la respuesta en la forma que el bucle espera.

    No hay `usage` que copiar: los tokens los ve la sesion que delego y los
    pasa aparte. Por eso `tokens_estimados` es **un suelo y no una medida**
    (`SPEC-14` C-3), y por eso el campo no se rellena aqui con un cero.
    """
    delta = datos.get("delta")
    if isinstance(delta, str):
        try:
            delta = json.loads(delta)
        except ValueError:
            delta = None
    return {"texto": datos.get("texto") or datos.get("content"), "delta": delta}
