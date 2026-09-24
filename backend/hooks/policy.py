"""Hook `PreToolUse` de Claude Code: una allowlist por agente (`SPEC-26` `RF-18`,
`SPEC-28` `RF-07`).

El Escritor y el Editor pueden llamar a las tres tools de lectura de la story bible;
nada mas, y ningun otro agente nada. Lo que no esta en la lista sale con **codigo 2**,
que niega la herramienta, y la negacion queda en el audit log si `HARNESS_DB` dice
donde. Sin `HARNESS_AGENTE` no hace nada (`RF-19`): una sesion interactiva en el mismo
proyecto conserva sus herramientas.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# En Windows la consola no es UTF-8: sin esto el motivo sale en cp1252 y quien lo
# lee -Claude Code- recibe las comillas y las tildes rotas. Lo cazo la prueba.
for _flujo in (sys.stdin, sys.stdout, sys.stderr):
    _flujo.reconfigure(encoding="utf-8")

from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD  # noqa: E402
from app.commons.politica import auditoria  # noqa: E402
from app.commons.politica.herramientas import permitida  # noqa: E402


def main():
    agente = os.environ.get("HARNESS_AGENTE")
    if not agente:
        return 0
    entrada = json.loads(sys.stdin.read() or "{}")
    herramienta = entrada.get("tool_name") or "(desconocida)"
    if permitida(agente, herramienta):
        return 0
    db = os.environ.get("HARNESS_DB")
    if db:
        con = sqlite3.connect(db)
        try:
            auditoria.asegurar_tabla(con)
            auditoria.registrar_decision(con, TD.HERRAMIENTA_DENEGADA,
                                         os.environ.get("HARNESS_OBRA"),
                                         {"agente": agente, "herramienta": herramienta})
        finally:
            con.close()
    print("El agente «{0}» del pipeline no puede usar {1}. Responde solo con lo que se te "
          "pide.".format(agente, herramienta), file=sys.stderr)
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
    registrar("policy", _codigo)
    sys.exit(_codigo)
