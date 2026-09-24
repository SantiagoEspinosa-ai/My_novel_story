"""Las pruebas de `harness/documentos/` importan el backend y el validador.

El validador del contrato cruza la frontera (`SPEC-22` §3.2.1): no vive ni con el
backend ni con el frontend, y por eso no lo recoge `python -m pytest app -q`. Se lanza
desde la raiz con `python -m pytest harness/documentos -q`.
"""

import sys
from pathlib import Path

AQUI = Path(__file__).resolve().parent
RAIZ = AQUI.parent.parent
for ruta in (RAIZ / "backend", AQUI):
    if str(ruta) not in sys.path:
        sys.path.insert(0, str(ruta))
