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
import uuid

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.configuracion import carga  # noqa: E402
from app.commons.db import migraciones, procedencia  # noqa: E402
from app.commons.dominio.destinatario import FichaDeEntrevista  # noqa: E402
from app.commons.modelo import gasto, proveedor  # noqa: E402
from app.commons.observabilidad.langfuse import crear_exportador  # noqa: E402
from app.commons.observabilidad.observacion import Observacion  # noqa: E402
from app.features.manuscrito import exportar  # noqa: E402
from app.features.orquestacion import novela  # noqa: E402
# `SPEC-33` `RF-11`: los mismos agentes y el mismo total que la web, no una copia.
from app.features.orquestacion.regalo import agentes, coste_total  # noqa: E402
from app.features.planificacion import repository as planes  # noqa: E402
from app.features.planificacion.service import PlanNoAprobado  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))




def estado_de_langfuse(observacion, vaciado) -> str:
    """`SPEC-29` `RF-09`: lo que paso con el envio, dicho. Apagado no es enviado, y un
    envio con perdidas no es un envio completo."""
    motivo = getattr(observacion.exportador, "motivo", None)
    if motivo:
        return "apagado: " + motivo
    if observacion.perdidas or not vaciado:
        return ("enviado con perdidas: {0} envios no llegaron{1}; ver la tabla "
                "envio_perdido".format(observacion.perdidas,
                                       "" if vaciado else ", y el vaciado final no termino"))
    return "enviado"


def scores_de_hooks(observacion, filas):
    """Lo que Claude Code ejecuto de verdad, como score: un `0` pasa, cualquier otro no."""
    for fila in filas:
        observacion.score(nombre="hook.{0}".format(fila["hook"]),
                          categoria="pasa" if fila.get("codigo") == 0 else "falla")


def palabras_de(con, escena):
    """`F-78`: las palabras del texto elegido -el aceptado o, si no consta, el ultimo-,
    que es lo que lee el manuscrito. `None` si no hay texto."""
    fila = con.execute("SELECT borrador_aceptado FROM escena WHERE id = ?", (escena,)).fetchone()
    texto = exportar._texto_de(con, escena, fila[0] if fila else None)
    return len(texto.split()) if texto is not None else None


def informe_sin_plan(con, obra, ag, error) -> str:
    """`F-69`: sin plan aprobado no hay capitulos, pero si rondas y coste. El coste del
    Planificador y del Revisor solo vive en sus `Contador`; si no se imprime aqui, se
    pierde sin que nadie lo diga."""
    lineas = ["\n=== PLAN NO APROBADO ===", str(error)]
    for v in planes.versiones(con, obra):
        lineas.append("  ronda {0}: {1}".format(v["version"], v["origen"]))
    usd = ag["planificador"].usd + ag["revisor"].usd
    sin_coste = ag["planificador"].sin_coste + ag["revisor"].sin_coste
    delegaciones = ag["planificador"].delegaciones + ag["revisor"].delegaciones
    lineas += ["\n=== COSTE ===",
               "delegaciones: {0} | sin coste medido: {1}".format(delegaciones, sin_coste),
               "coste leido: {0:.4f} USD{1}".format(
                   usd, " (SUELO: hay delegaciones sin coste)" if sin_coste else "")]
    return "\n".join(lineas)


def informe_de_hooks(observacion, registro_hooks):
    print("\n=== HOOKS (lo que Claude Code ejecuto de verdad) ===")
    if os.path.exists(registro_hooks):
        with open(registro_hooks, encoding="utf-8") as f:
            filas = [json.loads(l) for l in f if l.strip()]
        for fila in filas:
            print("  {hook} sobre {agente}: codigo {codigo}".format(**fila))
        scores_de_hooks(observacion, filas)
    else:
        print("  NINGUNO: los hooks no dejaron constancia. O Claude Code no los "
              "lanzo, o no les llego HARNESS_REGISTRO_HOOKS.")


def codigo_de_salida(r) -> int:
    """`SPEC-30` `RF-04`: una novela que no pasa la puerta no sale como si hubiera ido
    bien. Sin puerta (`--capitulos`) no es un fallo: no se evaluo. `F-115`: una generacion
    **parada** tampoco sale con 0, llegue o no a la puerta."""
    g = r.get("generacion")
    if g is not None and getattr(g, "parada", None):
        return 1
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
    # `SPEC-33` `RF-18`: cada delegacion deja su coste en la base, con el identificador de
    # esta ejecucion. Es lo que la web suma como gastado.
    generacion = "gen-" + uuid.uuid4().hex[:10]
    ag = agentes(sistema, {"HARNESS_DB": os.path.abspath(args.base),
                           "HARNESS_OBRA": args.obra,
                           "HARNESS_REGISTRO_HOOKS": registro_hooks},
                 anotar=gasto.anotador(con, args.obra, generacion))

    # `SPEC-29`: con claves en `backend/.env`, la generacion es una traza de Langfuse en la
    # sesion de su obra; sin ellas no se envia nada, y el informe lo dice.
    observacion = Observacion(crear_exportador(), con=con, obra=args.obra, nombre="generacion")
    arranque = time.time()
    try:
        r = novela.escribir(con, args.obra, ficha, ag, hasta_capitulo=args.capitulos,
                            carpeta_de_reglas=tempfile.gettempdir(), sistema=sistema,
                            observacion=observacion)
    except PlanNoAprobado as e:
        print(informe_sin_plan(con, args.obra, ag, e))
        print("tiempo: {0:.0f} s".format(time.time() - arranque))
        informe_de_hooks(observacion, registro_hooks)
        print("\n=== LANGFUSE ===")
        print(estado_de_langfuse(observacion, observacion.vaciar()))
        return 1
    except proveedor.FalloDeTransporte as e:
        # `F-72`: un agente agoto sus reintentos. Relanzar reanuda desde el ultimo
        # capitulo completado (`F-38`, `F-67`). El coste de lo escrito **no** esta en
        # `traza_de_delegacion`, que no tiene columna de coste (`F-144`): solo llega a
        # Langfuse. El del Planificador y el Revisor, aqui.
        print("\n=== PARADA POR TRANSPORTE ===")
        print(str(e))
        print("un agente agoto sus {0} reintentos; relanzar reanuda desde el ultimo "
              "capitulo completado".format(sistema.topes.reintentos_de_transporte))
        print("coste de los capitulos: sin medir en este informe (solo en "
              "Langfuse); del plan: {0:.4f} USD".format(
                  ag["planificador"].usd + ag["revisor"].usd))
        print("tiempo: {0:.0f} s".format(time.time() - arranque))
        informe_de_hooks(observacion, registro_hooks)
        print("\n=== LANGFUSE ===")
        print(estado_de_langfuse(observacion, observacion.vaciar()))
        return 1
    g = r["generacion"]
    total = coste_total(r, ag)
    usd, sin_coste, delegaciones = total["usd"], total["sin_coste"], total["delegaciones"]

    print("\n=== PLAN ===")
    print("aprobado en la ronda {0}{1}".format(
        r["plan"].version, " (reutilizado al reanudar: no se volvio a planificar)"
        if r["plan"].reutilizado else ""))
    print("\n=== CAPITULOS ===")
    print("hechos: {0}".format(", ".join(g.escenas_hechas) or "(ninguno)"))
    print("rendidos: {0}".format(g.rendidas or "(ninguno)"))
    print("parada: {0}".format(g.parada or "(ninguna)"))
    for e in g.escenas_hechas:
        palabras = palabras_de(con, e)
        print("  {0}: {1} palabras".format(e, palabras if palabras is not None else "sin medir"))
    print("\n=== CONTEXTO ENVIADO (F-58) ===")
    for m in g.medidas:
        print("  {0}: {1} tokens estimados, recortes {2}".format(
            m["escena"], m["total"], m["recortes"] or "-"))
    print("\n=== COSTE ===")
    print("delegaciones: {0} | sin coste medido: {1}".format(delegaciones, sin_coste))
    print("coste leido: {0:.4f} USD{1}".format(
        usd, " (SUELO: hay delegaciones sin coste)" if sin_coste else ""))
    # `PLAN-31` E9: el juicio de obra y la puerta ya estan en el total; se dicen aparte
    # porque hasta aqui no se sumaban, y quien compare con una medida vieja lo tiene que saber.
    cierre = r.get("coste_del_cierre")
    if cierre is not None:
        print("  cierre (juicio de obra y puerta de publicacion): {0} delegaciones, "
              "{1:.4f} USD{2}".format(cierre["delegaciones"], cierre["usd"],
                                      " (SUELO)" if cierre["sin_coste"] else ""))
    print("tiempo: {0:.0f} s".format(time.time() - arranque))
    informe_de_hooks(observacion, registro_hooks)
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
    print("\n=== LANGFUSE ===")
    print(estado_de_langfuse(observacion, observacion.vaciar()))
    return codigo_de_salida(r)


if __name__ == "__main__":
    sys.exit(main())
