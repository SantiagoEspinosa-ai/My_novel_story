"""El validador visual `INV-30` sobre una base y una URL (`SPEC-22` `RF-58`, `PLAN-22` E13b).

    cd backend && python -X utf8 inspeccion_visual.py BASE.db OBRA URL [--modelo sonnet]

**Gasta dinero**: delega en el agente `inspector_visual` (`.claude/agents/`), que abre la
web servida con Playwright MCP -`.mcp.json`, con MCP estricto y solo las tools del
browser-. La web tiene que estar servida en `URL`: `uvicorn` con `HARNESS_BASE=BASE.db` y
el frontend con `npm run dev`.

Juzga el veredicto (`auditoria/visual.py`), deja el hallazgo `INV-30` en la ultima escena
de la obra si alguna pieza falla o si el veredicto es ilegible -como `INV-27`, que tambien
es de obra-, y sube un score `INV-30.<pieza>` por comprobacion en la sesion de la obra
(Langfuse, si hay claves en `backend/.env`; si no, lo dice).

**No hace**: devolver el fallo al Escritor ni a nadie. El hallazgo queda abierto y lo
resuelve una persona (fuera de `RF-58`).
"""

import argparse
import sqlite3
import sys

from app.commons.modelo.proveedor import RAIZ_DEL_REPOSITORIO, RespuestaIlegible, SesionDelegada
from app.features.auditoria import visual
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import observar

MCP_DEL_BROWSER = RAIZ_DEL_REPOSITORIO / ".mcp.json"


def _ultima_escena(con, obra):
    escenas = escaleta.escenas_de(con, obra)
    if not escenas:
        raise SystemExit("la obra {0} no tiene escenas en esta base".format(obra))
    return sorted(escenas, key=lambda e: (e["t_discurso"] is None, e["t_discurso"] or 0,
                                          e["orden"]))[-1]["id"]


def inspeccionar(ruta, obra, url, inspector, obs=None):
    """Delega, juzga, guarda el hallazgo y sube los scores. Devuelve el `Juicio`."""
    medidas = None
    try:
        bruto = inspector.llamar(visual.prompt(url))
        if isinstance(bruto, dict):
            medidas = bruto.pop("medidas", None)
    except RespuestaIlegible as e:
        bruto, medidas = None, getattr(e, "medidas", None)
    juicio = visual.juzgar(bruto)
    juicio.medidas = medidas
    con = sqlite3.connect(ruta)
    try:
        if juicio.hallazgo:
            h = juicio.hallazgo
            escaleta.guardar_hallazgo(con, h["invariante"], h["verificador"],
                                      _ultima_escena(con, obra), h["severidad"], h["estado"],
                                      h["descripcion"])
    finally:
        con.close()
    observar.del_inspector_visual(obs, juicio)
    return juicio


def main(argv=None):
    from app.commons.observabilidad.exportador import ExportadorEnMemoria
    from app.commons.observabilidad.langfuse import crear_exportador
    from app.commons.observabilidad.observacion import Observacion

    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("base")
    p.add_argument("obra")
    p.add_argument("url")
    p.add_argument("--modelo", default="sonnet")
    a = p.parse_args(argv)

    inspector = SesionDelegada(modelo=a.modelo, agente="inspector_visual")
    inspector.mcp_fijo = str(MCP_DEL_BROWSER)
    exportador = crear_exportador()
    if getattr(exportador, "motivo", None):
        print("no se envia a Langfuse: {0}".format(exportador.motivo))
        exportador = ExportadorEnMemoria()
    obs = Observacion(exportador, con=sqlite3.connect(a.base), obra=a.obra,
                      nombre="inspeccion_visual")
    juicio = inspeccionar(a.base, a.obra, a.url, inspector, obs)
    obs.vaciar()
    print("INV-30: {0}".format(juicio.estado))
    for c in juicio.comprobaciones:
        print("  {0:<10} {1:<6} {2}".format(c.pieza, c.veredicto, c.motivo))
    if juicio.hallazgo:
        print("hallazgo {0} ({1}): {2}".format(juicio.hallazgo["invariante"],
                                              juicio.hallazgo["estado"],
                                              juicio.hallazgo["descripcion"]))
    m = juicio.medidas or {}
    print("coste de la delegacion: {0}".format(
        "{0} USD".format(m["coste_usd"]) if m.get("coste_usd") is not None else "sin medir"))
    print("perdidas de envio: {0}".format(obs.perdidas))
    return 0 if juicio.estado == "pasa" else 1


if __name__ == "__main__":
    sys.exit(main())
