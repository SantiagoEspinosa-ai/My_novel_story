"""Las claves de Langfuse, leidas de `backend/.env` (`SPEC-29` `RF-08`, `PLAN-29` E10).

**No se escriben en `os.environ`.** Si estuvieran en el entorno, las heredaria cualquier
subproceso —la sesion delegada de Claude Code, un hook— y el limite dependeria de que
`proveedor.py` las quitara. Se leen a un diccionario y solo las recibe el adaptador.

Un parser minimo y no `python-dotenv`: son tres variables `CLAVE=valor`, y el proyecto no
añade dependencias que una spec no pide.
"""

import pathlib

VARIABLES = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY", "LANGFUSE_BASE_URL")
OBLIGATORIAS = ("LANGFUSE_PUBLIC_KEY", "LANGFUSE_SECRET_KEY")

RUTA = pathlib.Path(__file__).resolve().parents[3] / ".env"


def leer(ruta=None) -> dict:
    ruta = pathlib.Path(ruta or RUTA)
    if not ruta.exists():
        return {}
    salida = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        clave, valor = (p.strip() for p in linea.split("=", 1))
        if clave in VARIABLES and valor:
            salida[clave] = valor.strip("\"'")
    return salida


def faltan(claves) -> list:
    return [v for v in OBLIGATORIAS if not claves.get(v)]
