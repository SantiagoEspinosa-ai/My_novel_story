"""Hook `Stop` de Claude Code: valida el capitulo antes de que el Escritor lo
entregue (`SPEC-26` `RF-17`).

Lo lanza Claude Code al terminar cada respuesta, con un JSON por stdin. Si el
capitulo no cumple, sale con **codigo 2** y el motivo por stderr: Claude Code se
lo devuelve al Escritor **dentro de la misma sesion**, que es mas barato que una
delegacion nueva. Las puertas del codigo siguen mandando: esto es una primera
linea, no la unica.

CUANDO NO HACE NADA
-------------------
- Sin `HARNESS_AGENTE` (`RF-19`): es una sesion interactiva, no del pipeline.
- Con un agente que no es el Escritor: solo el Escritor entrega capitulos.
- Con `stop_hook_active`: ya se le devolvio una vez. Se le deja terminar y lo
  que quede lo cazan las puertas; si no, un bucle sin tope.
- Sin reglas (`HARNESS_REGLAS`): lo dice por stderr y deja pasar. Un dato
  ausente no es un verde, pero tampoco es motivo para bloquear.
"""

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# En Windows la consola no es UTF-8: sin esto el motivo sale en cp1252 y quien lo
# lee -Claude Code- recibe las comillas y las tildes rotas. Lo cazo la prueba.
for _flujo in (sys.stdin, sys.stdout, sys.stderr):
    _flujo.reconfigure(encoding="utf-8")

from app.commons.modelo.proveedor import interpretar  # noqa: E402
from app.commons.politica.personalizacion import nombres_mal_escritos  # noqa: E402
from app.commons.politica.vetadas import coincidencias  # noqa: E402


def ultima_respuesta(entrada):
    if entrada.get("last_assistant_message"):
        return entrada["last_assistant_message"]
    ruta = entrada.get("transcript_path")
    if not ruta or not os.path.exists(ruta):
        return None
    ultimo = None
    with open(ruta, encoding="utf-8") as f:
        for linea in f:
            try:
                fila = json.loads(linea)
            except ValueError:
                continue
            if fila.get("type") != "assistant":
                continue
            contenido = (fila.get("message") or {}).get("content")
            if isinstance(contenido, str):
                ultimo = contenido
            elif isinstance(contenido, list):
                textos = [c.get("text", "") for c in contenido if c.get("type") == "text"]
                if textos:
                    ultimo = "".join(textos)
    return ultimo


def problemas(texto, reglas):
    salida = []
    minimo, maximo = reglas.get("longitud") or (0, 10 ** 9)
    palabras = len(texto.split())
    if not minimo <= palabras <= maximo:
        salida.append("el capitulo tiene {0} palabras y tienen que ser entre {1} y "
                      "{2}".format(palabras, minimo, maximo))
    for co in coincidencias(texto, reglas.get("vetadas") or []):
        salida.append("«{0}» no puede aparecer (vetada: {1})".format(co.fragmento, co.vetada))
    for m in nombres_mal_escritos(texto, reglas.get("nombres") or []):
        salida.append("escribiste «{0}»: el nombre es «{1}»".format(m.escrito, m.correcto))
    return salida


def main():
    if os.environ.get("HARNESS_AGENTE") != "escritor":
        return 0
    entrada = json.loads(sys.stdin.read() or "{}")
    if entrada.get("stop_hook_active"):
        return 0
    ruta = os.environ.get("HARNESS_REGLAS")
    if not ruta or not os.path.exists(ruta):
        print("validar_capitulo: sin reglas, no se comprueba nada", file=sys.stderr)
        return 0
    with open(ruta, encoding="utf-8") as f:
        reglas = json.load(f)
    bruto = ultima_respuesta(entrada)
    try:
        texto = str(interpretar(bruto or "").get("texto") or "")
    except Exception:
        print("Tu respuesta no es el objeto JSON pedido, con `texto` y `delta`. "
              "Devuelvelo otra vez con ese formato.", file=sys.stderr)
        return 2
    lista = problemas(texto, reglas)
    if not lista:
        return 0
    print("Antes de entregar, corrige esto y devuelve el JSON completo otra vez:\n"
          + "\n".join("- " + p for p in lista), file=sys.stderr)
    return 2


def registrar(hook, codigo):
    """Deja constancia de que el hook se ejecuto y de que decidio. Sin esto, una
    ejecucion real en la que nada falla no demuestra que se disparara."""
    ruta = os.environ.get("HARNESS_REGISTRO_HOOKS")
    if not ruta or not os.environ.get("HARNESS_AGENTE"):
        return
    with open(ruta, "a", encoding="utf-8") as f:
        f.write(json.dumps({"hook": hook, "agente": os.environ["HARNESS_AGENTE"],
                            "codigo": codigo}) + "\n")


if __name__ == "__main__":
    _codigo = main()
    registrar("validar_capitulo", _codigo)
    sys.exit(_codigo)
