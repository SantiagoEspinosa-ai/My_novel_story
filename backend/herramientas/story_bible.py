"""El servidor MCP de la story bible, que lanza Claude Code (`SPEC-28`, `PLAN-28` E4).

Claude Code lo arranca por stdio desde el fichero que le pasa `--mcp-config`, con estas
variables de entorno:

    HARNESS_DB           la base de la obra
    HARNESS_OBRA         la obra de la delegacion: **la unica que se puede leer**
    HARNESS_AGENTE       quien llama (escritor o editor)
    HARNESS_DELEGACION   para enlazar cada llamada con su traza

Sin `HARNESS_DB` o sin `HARNESS_OBRA` no arranca: sin obra no hay lectura por defecto
(`RF-06`). Abre **dos conexiones**: la de la story bible es de solo lectura, y asi `RF-04`
lo hace cumplir SQLite y no la disciplina; la otra solo escribe `llamada_a_herramienta`.
"""

import os
import pathlib
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# En Windows la consola no es UTF-8, y quien lee la salida es Claude Code.
for _flujo in (sys.stdin, sys.stdout, sys.stderr):
    if hasattr(_flujo, "reconfigure"):  # bajo pytest, stdin no se puede reconfigurar
        _flujo.reconfigure(encoding="utf-8")

from app.commons.modelo.mcp import servir  # noqa: E402
from app.features.orquestacion import story_bible as tools  # noqa: E402


def abrir_conexiones(base):
    lectura = sqlite3.connect("file:{0}?mode=ro".format(pathlib.Path(base).as_posix()), uri=True)
    lectura.row_factory = sqlite3.Row
    traza = sqlite3.connect(base)
    return lectura, traza


def catalogo():
    return [{"name": nombre, "description": descripcion,
             "inputSchema": entrada.model_json_schema()}
            for nombre, (entrada, _, descripcion) in tools.HERRAMIENTAS.items()]


def main():
    base, obra = os.environ.get("HARNESS_DB"), os.environ.get("HARNESS_OBRA")
    if not base or not obra:
        print("el servidor de la story bible necesita HARNESS_DB y HARNESS_OBRA: sin obra "
              "no hay lectura por defecto (SPEC-28 RF-06)", file=sys.stderr)
        return 2
    agente = os.environ.get("HARNESS_AGENTE", "desconocido")
    delegacion = os.environ.get("HARNESS_DELEGACION", "sin-delegacion")
    lectura, traza = abrir_conexiones(base)
    servir(sys.stdin, sys.stdout, catalogo(),
           lambda nombre, argumentos: tools.atender(lectura, traza, obra, agente, delegacion,
                                                    nombre, argumentos))
    return 0


if __name__ == "__main__":
    sys.exit(main())
