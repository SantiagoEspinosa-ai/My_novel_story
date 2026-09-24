"""La medida del arrastre de `SPEC-23` v2, desde la terminal (`PLAN-23` A1).

    python -X utf8 medir_arrastre.py --base BASE.db --obra OBRA

Imprime el objeto de la medida en JSON: el arrastre medio con su numerador y su
denominador, la obra, el commit, la salida que da la regla (≤ 3 → cascada; > 3 →
selectiva), el detalle por hecho y **la direccion del sesgo**. Sale con 0 si midio
y con 1 si se nego, con lo que falta.

**No escribe en la base**: la abre en solo lectura. No gasta: lee tablas.
"""

import argparse
import json
import os
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.features.orquestacion import arrastre


def main(argv=None):
    p = argparse.ArgumentParser(description="La medida del arrastre de SPEC-23 v2")
    p.add_argument("--base", required=True)
    p.add_argument("--obra", required=True)
    args = p.parse_args(argv)
    ruta = Path(args.base).resolve()
    if not ruta.exists():
        print(json.dumps({"medido": False, "motivo": "no existe la base {0}".format(ruta)},
                         ensure_ascii=False))
        return 1
    con = sqlite3.connect(ruta.as_uri() + "?mode=ro", uri=True)
    try:
        r = arrastre.medir(con, args.obra)
    finally:
        con.close()
    print(json.dumps(r, ensure_ascii=False, indent=2))
    return 0 if r.get("medido") else 1


if __name__ == "__main__":
    sys.exit(main())
