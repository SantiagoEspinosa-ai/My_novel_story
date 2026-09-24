"""La novela regalo con agentes de verdad (`SPEC-26`, `PLAN-26` E13).

    python -X utf8 novela_regalo.py FICHA.json                 # la novela entera
    python -X utf8 novela_regalo.py FICHA.json --capitulos 1   # solo el primero
    python -X utf8 novela_regalo.py FICHA.json --base otra.db

**Gasta dinero**: cada capitulo delega en el Planificador, el Revisor, el
Escritor, el Editor y el Resumidor. Necesita los modelos en
`config/sistema.json` y se lanza con `-X utf8` porque la consola de Windows no
es UTF-8 por defecto.

FICHA.json es la ficha de la entrevista cerrada (`SPEC-25`): la que devuelve
`POST /entrevistas/{id}/cerrar`, o una escrita a mano con datos **inventados**
(`RF-22`).

QUE MIDE, Y QUE DICE QUE NO MIDE
--------------------------------
El coste y los tokens salen de `--output-format json` de cada delegacion. El
Planificador y el Revisor no pasan por las trazas del ciclo, asi que aqui se
envuelven para sumar lo suyo. Una delegacion que no trae coste se cuenta como
**sin medir**, no como cero. El contexto enviado es la suma de los bloques que
llegaron al prompt de cada escena (`F-58`).
"""

import argparse
import json
import os
import sqlite3
import sys
import tempfile
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.configuracion import carga  # noqa: E402
from app.commons.db import migraciones, procedencia  # noqa: E402
from app.commons.dominio.destinatario import FichaDeEntrevista  # noqa: E402
from app.commons.modelo import proveedor  # noqa: E402
from app.features.orquestacion import ciclo, novela  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))


class Contador:
    """Suma el coste de un agente que no pasa por las trazas del ciclo."""

    def __init__(self, sesion):
        self.sesion, self.nombre = sesion, sesion.nombre
        self.usd, self.delegaciones, self.sin_coste = 0.0, 0, 0

    @property
    def entorno(self):
        return self.sesion.entorno

    def llamar(self, prompt):
        self.delegaciones += 1
        r = self.sesion.llamar(prompt)
        usd = ((r or {}).get("medidas") or {}).get("coste_usd")
        if usd is None:
            self.sin_coste += 1
        else:
            self.usd += usd
        return r


def agentes(sistema, entorno):
    m = sistema.modelos
    faltan = [n for n in ("planificador", "revisor_plan", "editor", "escritor", "resumidor")
              if not getattr(m, n)]
    if faltan:
        raise SystemExit("faltan modelos en config/sistema.json: " + ", ".join(faltan))
    sesiones = {
        "planificador": Contador(proveedor.SesionDelegada(modelo=m.planificador,
                                                          agente="planificador")),
        "revisor": Contador(proveedor.SesionDelegada(modelo=m.revisor_plan,
                                                     agente="revisor_plan")),
        "escritor": proveedor.SesionDelegada(modelo=m.escritor, agente="escritor"),
        "editor": ciclo.editor_aislado(modelo=m.editor),
        "resumidor": proveedor.SesionDelegada(modelo=m.resumidor, agente="resumidor"),
    }
    for s in sesiones.values():
        (s.sesion if isinstance(s, Contador) else s).entorno.update(entorno)
    return sesiones


def codigo_de_salida(r) -> int:
    """`SPEC-30` `RF-04`: una novela que no pasa la puerta no sale como si hubiera ido
    bien. Sin puerta (`--capitulos`) no es un fallo: no se evaluo."""
    p = r.get("publicacion")
    return 0 if p is None or p.publicada else 1


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("ficha")
    p.add_argument("--capitulos", type=int, default=None)
    p.add_argument("--base", default=os.path.join(AQUI, "regalo.db"))
    p.add_argument("--obra", default="obra-regalo")
    args = p.parse_args(argv)

    with open(args.ficha, encoding="utf-8") as f:
        ficha = FichaDeEntrevista.model_validate(json.load(f))
    sistema = carga.cargar_sistema()
    con = sqlite3.connect(args.base)
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    procedencia.registrar(con, sistema=sistema.huella)
    registro_hooks = os.path.join(tempfile.gettempdir(), "hooks-{0}.jsonl".format(args.obra))
    if os.path.exists(registro_hooks):
        os.remove(registro_hooks)
    ag = agentes(sistema, {"HARNESS_DB": os.path.abspath(args.base),
                           "HARNESS_OBRA": args.obra,
                           "HARNESS_REGISTRO_HOOKS": registro_hooks})

    arranque = time.time()
    r = novela.escribir(con, args.obra, ficha, ag, hasta_capitulo=args.capitulos,
                        carpeta_de_reglas=tempfile.gettempdir(), sistema=sistema)
    g = r["generacion"]
    usd = g.coste["usd"] + ag["planificador"].usd + ag["revisor"].usd
    sin_coste = g.coste["sin_coste"] + ag["planificador"].sin_coste + ag["revisor"].sin_coste
    delegaciones = (g.coste["delegaciones"] + ag["planificador"].delegaciones
                    + ag["revisor"].delegaciones)

    print("\n=== PLAN ===")
    print("aprobado en la ronda {0}{1}".format(
        r["plan"].version, " (reutilizado al reanudar: no se volvio a planificar)"
        if r["plan"].reutilizado else ""))
    print("\n=== CAPITULOS ===")
    print("hechos: {0}".format(", ".join(g.escenas_hechas) or "(ninguno)"))
    print("rendidos: {0}".format(g.rendidas or "(ninguno)"))
    print("parada: {0}".format(g.parada or "(ninguna)"))
    for e in g.escenas_hechas:
        texto = con.execute("SELECT b.texto FROM borrador b JOIN escena s ON s.id = b.escena "
                            "WHERE s.id = ? AND b.version = s.borrador_aceptado",
                            (e,)).fetchone()
        palabras = len(texto[0].split()) if texto else None
        print("  {0}: {1} palabras".format(e, palabras if palabras is not None else "sin medir"))
    print("\n=== CONTEXTO ENVIADO (F-58) ===")
    for m in g.medidas:
        print("  {0}: {1} tokens estimados, recortes {2}".format(
            m["escena"], m["total"], m["recortes"] or "-"))
    print("\n=== COSTE ===")
    print("delegaciones: {0} | sin coste medido: {1}".format(delegaciones, sin_coste))
    print("coste leido: {0:.4f} USD{1}".format(
        usd, " (SUELO: hay delegaciones sin coste)" if sin_coste else ""))
    print("tiempo: {0:.0f} s".format(time.time() - arranque))
    print("\n=== HOOKS (lo que Claude Code ejecuto de verdad) ===")
    if os.path.exists(registro_hooks):
        with open(registro_hooks, encoding="utf-8") as f:
            filas = [json.loads(l) for l in f if l.strip()]
        for fila in filas:
            print("  {hook} sobre {agente}: codigo {codigo}".format(**fila))
    else:
        print("  NINGUNO: los hooks no dejaron constancia. O Claude Code no los "
              "lanzo, o no les llego HARNESS_REGISTRO_HOOKS.")
    if r["cierre"]:
        print("\n=== CIERRE ===")
        print(r["cierre"]["estado"], r["cierre"]["faltan"] or "")
    pub = r.get("publicacion")
    if pub is not None:
        print("\n=== PUBLICACION ===")
        print("publicada" if pub.publicada
              else "NO se publica ({0})".format(pub.parada.get("motivo")))
        print("rondas: {0}".format(pub.rondas))
        for c in (pub.parada or {}).get("condiciones", []):
            print("  [{0}] {1}: {2}".format(c["invariante"], c["capitulo"] or "(obra)",
                                            c["detalle"]))
        if (pub.parada or {}).get("diagnostico"):
            print("  diagnostico del editor: " + pub.parada["diagnostico"])
        if pub.evaluaciones:
            for n in pub.evaluaciones[-1].decision.no_ejecutadas:
                print("  no ejecutada: {0} ({1})".format(n.invariante, n.motivo))
    return codigo_de_salida(r)


if __name__ == "__main__":
    sys.exit(main())
