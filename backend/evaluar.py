"""La ejecucion real de un brief de evaluacion (`SPEC-31`, `PLAN-31` E3 y E10).

    python -X utf8 evaluar.py ../harness/evals/brief-base.json --pasada antes
    python -X utf8 evaluar.py ../harness/evals/brief-base.json --pasada antes --confirmo-el-gasto
    python -X utf8 evaluar.py ../harness/evals/brief-base.json --pasada antes --confirmo-el-gasto --capitulos 1

**Gasta dinero de verdad**: cada capitulo delega en el Planificador, el Revisor, el
Escritor, el Editor y el Resumidor, y un brief con guion ademas en el Entrevistador. Sin
`--confirmo-el-gasto` solo enseña el presupuesto y sale con 2.

QUE HACE, EN ORDEN
------------------
1. Lee el libro de gasto (`--libro`, `gasto_de_evaluacion`) y enseña **lo gastado, lo que
   queda hasta el techo y el mayor coste medido de una novela completa** (o «sin
   medir»). El techo, 150 USD, es una decision de presupuesto (`SPEC-31`), y se comprueba
   contra lo gastado, nunca contra una prevision. Con el techo alcanzado, sale con 3.
2. Sin `--confirmo-el-gasto`, sale con 2 sin pedir ningun agente.
3. **Una base por ejecucion** (`--base`, por defecto `evaluacion-<ejecucion>.db`): una base
   que ya tiene otra novela se rechaza con 4, porque la segunda veria el mundo de la
   primera (`F-100`). El libro si se comparte: es lo que acumula el techo.
4. Si el brief es un guion, hace la entrevista contra la API en proceso (sin uvicorn), y
   la obra es la que crea la entrevista. Si el guion se acaba sin cerrar, sale con 1.
5. Escribe la novela con `seguir` conectado al libro: cada capitulo se anota al terminar
   y, con el techo alcanzado, la generacion se para entre capitulos (`techo_de_gasto`).
   **Se puede pasar del techo en lo que cueste el capitulo en curso.**
6. Pasa el rastro de exfiltracion contra las novelas de las ejecuciones anteriores, sobre
   los textos guardados: el prompt enviado no se guarda, asi que un rastro limpio aqui
   no dice que el prompt lo fuera (`exfiltracion.py`).
7. Regenera `harness/evals/resultados.md` (`--tabla`) con todas las ejecuciones del libro.

`main(argv, dobles=...)` acepta dobles de los agentes, Lean, el exportador y el
Entrevistador: es como lo prueban `test_evaluar.py` y `test_entrevistar.py`, sin gastar.
"""

import argparse
import os
import sqlite3
import sys
import tempfile
import time
from dataclasses import dataclass, field

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import entrevista_cli  # noqa: E402

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(AQUI)


@dataclass
class Entrevista:
    """Lo que dejo una entrevista hecha desde un guion. `ficha` es `None` si no cerro."""

    obra: str | None
    ficha: dict | None
    dicho: list = field(default_factory=list)


class _Espia:
    """El cliente HTTP, con la respuesta de `POST /entrevistas` guardada: es la que trae
    la obra, y `dialogar` solo la enseña si la entrevista cierra."""

    def __init__(self, cliente):
        self.cliente, self.creada = cliente, None

    def post(self, url, **kw):
        r = self.cliente.post(url, **kw)
        if url == "/entrevistas" and self.creada is None:
            self.creada = r.json()
        return r

    def get(self, url, **kw):
        return self.cliente.get(url, **kw)


def entradas_del_guion(guion) -> list:
    """El guion, en lo que teclearia el comprador en `entrevista_cli`."""
    salida = []
    for t in guion.turnos:
        if t.accion == "respuesta":
            salida.append(t.respuesta)
        elif t.accion == "texto_libre":
            salida.append(":texto")
            salida.extend(t.texto_libre.splitlines() or [""])
            salida.append(".")
        else:
            salida.append(":cerrar")
    return salida


def entrevistar(cliente, guion, espera=0) -> Entrevista:
    """`PLAN-31` E3: la entrevista del guion contra la API. **El guion no escucha las
    preguntas**: contesta en su orden. Si se acaba sin cerrar, sale con `:salir` y la
    entrevista queda abierta, dicho en `dicho`; no se inventa un cierre."""
    pendientes = iter(entradas_del_guion(guion))
    espia, dicho = _Espia(cliente), []
    ficha = entrevista_cli.dialogar(espia, entrada=lambda _: next(pendientes, ":salir"),
                                    salida=dicho.append, espera=espera)
    return Entrevista(obra=(espia.creada or {}).get("obra"), ficha=ficha, dicho=dicho)


# --- E10: la ejecucion entera ----------------------------------------------------------

def _guion_novela_regalo():
    import importlib.util
    spec = importlib.util.spec_from_file_location("novela_regalo",
                                                  os.path.join(AQUI, "novela_regalo.py"))
    modulo = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modulo)
    return modulo


def buscar_brief(id_brief):
    """El fichero de un brief por su id, en `harness/evals/` o `harness/adversarial/`."""
    for carpeta in ("evals", "adversarial"):
        ruta = os.path.join(RAIZ, "harness", carpeta, id_brief + ".json")
        if os.path.exists(ruta):
            return ruta
    return None


def presupuesto(con_libro, techo) -> list:
    from app.features.evaluacion import repository as libro
    total = libro.gastado(con_libro)
    queda = techo - total.usd
    mayor = libro.mayor_coste_de_novela_completa(con_libro)
    lineas = ["=== PRESUPUESTO (SPEC-31: el techo es una decision, no una medida) ===",
              "gastado: " + libro.texto_del_total(total),
              "queda hasta el techo de {0:.2f} USD: {1:.4f} USD{2}".format(
                  techo, queda, " (como mucho: lo gastado es un suelo)" if total.es_suelo
                  else ""),
              "mayor coste medido de una novela completa: {0}".format(
                  "sin medir" if mayor is None else "{0:.4f} USD".format(mayor))]
    if mayor is not None and queda < mayor:
        lineas.append("AVISO: lo que queda es menos que la novela completa mas cara medida; "
                      "esta ejecucion probablemente no termine (PLAN-31, techo punto 2)")
    return lineas


def otras_novelas(con) -> list:
    try:
        return [f[0] for f in con.execute("SELECT DISTINCT obra FROM escena")]
    except sqlite3.OperationalError:
        return []


def textos_de(con, obra) -> list:
    from app.features.escaleta import repository as escaleta
    from app.features.orquestacion.obra import _texto_elegido
    return [_texto_elegido(con, e) or "" for e in escaleta.escenas_de(con, obra)]


def rastro_contra_anteriores(con_libro, ejecucion, con, obra) -> list:
    from app.features.evaluacion import briefs, exfiltracion
    from app.features.evaluacion import repository as libro
    lineas = ["\n=== RASTRO DE OTRAS NOVELAS ==="]
    textos = textos_de(con, obra)
    previas = [e for e in libro.ejecuciones(con_libro) if e["ejecucion"] != ejecucion]
    if not previas:
        lineas.append("  (no hay ejecuciones anteriores)")
    for e in previas:
        ruta = buscar_brief(e["brief"])
        if ruta is None:
            lineas.append("  {0}: sin veredicto (no se encuentra el brief {1})".format(
                e["ejecucion"], e["brief"]))
            continue
        huellas = exfiltracion.rastro(textos, exfiltracion.claves_de(briefs.cargar(ruta)))
        lineas.append("  {0}: {1}".format(e["ejecucion"], "limpio" if not huellas else
                                           "HUELLAS " + ", ".join(sorted({h.clave for h in huellas}))))
    lineas.append("  (sobre los textos guardados: el prompt enviado no se guarda)")
    return lineas


def regenerar_tabla(con_libro, ruta_tabla, umbral=None):
    from app.features.evaluacion import repository as libro
    from app.features.evaluacion import tabla
    from app.features.evaluacion.tabla import Celda, Resultado
    from app.features.orquestacion import evaluacion
    ultimas = {}
    for e in libro.ejecuciones(con_libro):
        ultimas[(e["brief"], e["pasada"])] = e
    filas = []
    for (brief, pasada), e in ultimas.items():
        coste = libro.texto_del_total(libro.gastado(con_libro, e["ejecucion"]))
        if not e["base"] or not os.path.exists(e["base"]) or not e["obra"]:
            celdas = {c: Celda(Resultado.SIN_VEREDICTO, motivo="la base de la ejecucion no esta")
                      for c in tabla.columnas()}
        else:
            con = sqlite3.connect(e["base"])
            con.row_factory = sqlite3.Row
            celdas = evaluacion.resultados(con, e["obra"], umbral)
            con.close()
        filas.append(tabla.Fila(brief, pasada, celdas, ejecucion=e["ejecucion"], coste=coste))
    with open(ruta_tabla, "w", encoding="utf-8") as f:
        f.write(tabla.generar(filas))
    return filas


def _argumentos(argv):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("brief")
    p.add_argument("--pasada", choices=("antes", "despues"), required=True)
    p.add_argument("--libro", default=os.path.join(AQUI, "evaluacion.db"),
                   help="La base del libro de gasto: se comparte entre ejecuciones")
    p.add_argument("--base", default=None,
                   help="La base de la novela. Por defecto, una por ejecucion (F-100)")
    p.add_argument("--tabla", default=os.path.join(RAIZ, "harness", "evals", "resultados.md"))
    p.add_argument("--capitulos", type=int, default=None)
    p.add_argument("--confirmo-el-gasto", action="store_true")
    return p.parse_args(argv)


def _entrevista(brief, base, dobles, exportador, anotar):
    from fastapi.testclient import TestClient
    from app.commons.modelo.contador import Contador
    from app.commons.observabilidad.observacion import Observacion
    from app.features.entrevista import router
    from app.main import app, preparar_base
    preparar_base(base).close()
    entrevistador = Contador((dobles.get("entrevistador") or router._sesion_del_entrevistador)())
    extractor = Contador((dobles.get("extractor") or router._sesion_del_entrevistador)())
    estado = {"ruta_db": base, "entrevistador": lambda: entrevistador,
              "extractor": lambda: extractor,
              "observabilidad": lambda obra, nombre, con: Observacion(
                  exportador, con=con, obra=obra, nombre=nombre)}
    antes = {k: getattr(app.state, k, None) for k in estado}
    for k, v in estado.items():
        setattr(app.state, k, v)
    try:
        r = entrevistar(TestClient(app), brief.guion)
    finally:
        for k, v in antes.items():
            if v is None:
                if hasattr(app.state, k):
                    delattr(app.state, k)
            else:
                setattr(app.state, k, v)
    anotar("entrevista", r.obra, {k: entrevistador.resumen()[k] + extractor.resumen()[k]
                                   for k in ("usd", "delegaciones", "sin_coste")})
    return r


def main(argv=None, dobles=None):
    from app.commons.configuracion import carga
    from app.commons.db import migraciones, procedencia
    from app.commons.dominio.destinatario import FichaDeEntrevista
    from app.commons.modelo import proveedor
    from app.commons.modelo.contador import Contador
    from app.commons.observabilidad.observacion import Observacion
    from app.features.evaluacion import briefs
    from app.features.evaluacion import repository as libro
    from app.features.orquestacion import novela
    from app.features.planificacion.service import PlanNoAprobado

    dobles = dobles or {}
    args = _argumentos(argv)
    brief = briefs.cargar(args.brief)
    sistema = carga.cargar_sistema()
    techo = sistema.evaluacion.techo_de_gasto_usd
    umbral = sistema.edicion.umbral_del_editor
    con_libro = sqlite3.connect(args.libro)
    libro.asegurar_tablas(con_libro)
    for linea in presupuesto(con_libro, techo):
        print(linea)
    if not libro.puede_empezar(con_libro, techo):
        print("\nTECHO ALCANZADO: no empieza ninguna ejecucion (SPEC-31 RF-06).")
        regenerar_tabla(con_libro, args.tabla, umbral)
        return 3
    if not args.confirmo_el_gasto:
        print("\nNo empieza: esta ejecucion gasta dinero. Con las tres cifras de arriba "
              "delante, relanza con --confirmo-el-gasto.")
        return 2

    ejecucion = libro.siguiente_ejecucion(con_libro, brief.meta.id, args.pasada)
    base = os.path.abspath(args.base or os.path.join(AQUI, "evaluacion-{0}.db".format(ejecucion)))
    con = sqlite3.connect(base)
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    otras = otras_novelas(con)
    if otras:
        print("\nNO EMPIEZA: la base {0} ya tiene otra novela ({1}). La segunda novela de una "
              "base recibe el mundo de la primera (F-100): una base por ejecucion.".format(
                  base, ", ".join(otras)))
        return 4
    procedencia.registrar(con, sistema=sistema.huella)
    print("\nejecucion: {0} | base: {1}".format(ejecucion, base))
    exportador = (dobles.get("exportador") or _crear_exportador)()

    def anotar(tramo, obra_, coste):
        libro.anotar(con_libro, ejecucion=ejecucion, brief=brief.meta.id, pasada=args.pasada,
                     capitulo=tramo, obra=obra_, base=base, **coste)

    if brief.guion is not None:
        r = _entrevista(brief, base, dobles, exportador, anotar)
        obra = r.obra
        print("\n=== ENTREVISTA ===")
        for d in r.dicho:
            print("  " + d)
        if r.ficha is None:
            print("ENTREVISTA SIN CERRAR: el guion se acabo; no se escribe novela.")
            regenerar_tabla(con_libro, args.tabla, umbral)
            return 1
        ficha = FichaDeEntrevista.model_validate(r.ficha)
    else:
        obra, ficha = ejecucion, brief.ficha

    guion = _guion_novela_regalo()
    entorno = {"HARNESS_DB": base, "HARNESS_OBRA": obra,
               "HARNESS_REGISTRO_HOOKS": os.path.join(tempfile.gettempdir(),
                                                      "hooks-{0}.jsonl".format(obra))}
    ag = (dobles["agentes"](sistema, entorno, ficha) if dobles.get("agentes")
          else guion.agentes(sistema, entorno))
    for rol in ("planificador", "revisor"):
        if not isinstance(ag[rol], Contador):
            ag[rol] = Contador(ag[rol])
    plan_anotado = []

    def anotar_plan():
        if not plan_anotado:
            plan_anotado.append(True)
            anotar("plan", obra, {k: ag["planificador"].resumen()[k] + ag["revisor"].resumen()[k]
                                  for k in ("usd", "delegaciones", "sin_coste")})

    def seguir(numero, coste):
        anotar_plan()
        anotar(str(numero), obra, coste)
        return libro.puede_empezar(con_libro, techo)

    observacion = Observacion(exportador, con=con, obra=obra, nombre="generacion")
    arranque = time.time()
    codigo = 0
    try:
        r = novela.escribir(con, obra, ficha, ag, hasta_capitulo=args.capitulos,
                            carpeta_de_reglas=tempfile.gettempdir(), sistema=sistema,
                            lean=dobles.get("lean"), observacion=observacion, seguir=seguir)
    except (PlanNoAprobado, proveedor.FalloDeTransporte) as e:
        anotar_plan()
        print("\n=== PARADA ===\n{0}: {1}".format(type(e).__name__, e))
        r, codigo = None, 1
    if r is not None:
        anotar_plan()
        if r["coste_del_cierre"] is not None:
            anotar("cierre", obra, r["coste_del_cierre"])
        g = r["generacion"]
        print("\n=== CAPITULOS ===")
        print("hechos: {0}".format(len(g.escenas_hechas)))
        print("parada: {0}".format((g.parada or {}).get("motivo") or "(ninguna)"))
        codigo = guion.codigo_de_salida(r)
    print("\n=== COSTE DE ESTA EJECUCION ===")
    print(libro.texto_del_total(libro.gastado(con_libro, ejecucion)))
    print("tiempo: {0:.0f} s".format(time.time() - arranque))
    for linea in rastro_contra_anteriores(con_libro, ejecucion, con, obra):
        print(linea)
    regenerar_tabla(con_libro, args.tabla, umbral)
    print("\ntabla: " + args.tabla)
    print("\n=== LANGFUSE ===")
    print(guion.estado_de_langfuse(observacion, observacion.vaciar()))
    return codigo


def _crear_exportador():
    from app.commons.observabilidad.langfuse import crear_exportador
    return crear_exportador()


if __name__ == "__main__":
    sys.exit(main())
