"""Hook `PreToolUse` de Claude Code: ningun agente del pipeline usa herramientas
(`SPEC-26` `RF-18`).

Sale con **codigo 2** para negar la herramienta, y la negacion queda en el audit
log si `HARNESS_DB` dice donde. Sin `HARNESS_AGENTE` no hace nada (`RF-19`): una
sesion interactiva en el mismo proyecto conserva sus herramientas.

**Mientras los agentes tengan `tools: []` no se dispara nunca.** Es una guarda
contra que alguien les de herramientas; su prueba lo lanza como proceso.
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


def main():
    agente = os.environ.get("HARNESS_AGENTE")
    if not agente:
        return 0
    entrada = json.loads(sys.stdin.read() or "{}")
    herramienta = entrada.get("tool_name") or "(desconocida)"
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
    print("El agente «{0}» del pipeline no puede usar herramientas ({1}). Responde "
          "solo con el texto que se te pide.".format(agente, herramienta), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
