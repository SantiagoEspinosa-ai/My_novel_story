"""Un cambio del lector sobre una novela ya escrita, sin la web (`SPEC-23`, `PLAN-23` B-S1.1).

    python -X utf8 pedir_cambio.py --base BASE --obra OBRA \\
        (--hecho ID --enunciado TEXTO | --personaje ID --nombre NOMBRE) --texto TEXTO \\
        [--ficha FICHA.json] [--confirmo-el-gasto]

Llama al mismo servicio que la API: `regeneracion.proponer` (sin modelo, sin tocar nada),
y con `--confirmo-el-gasto`, `regeneracion.pedir` -guarda la peticion y encola su
trabajo- y el worker de ese trabajo **en este proceso**, con los agentes reales de
`novela_regalo.agentes`. Con la salida elegida por la medida (`cascada`, `S-1`) eso es
reescribir desde el primer capitulo que toca la peticion hasta el final.

**Sin `--confirmo-el-gasto` solo imprime la propuesta** -los capitulos que se tocarian, la
promesa y su punto ciego- y sale con 2: no guarda nada ni delega en nadie. Con el, **gasta
dinero**: una delegacion por escena nueva, mas sus jueces y la puerta de publicacion.
Necesita los modelos en `config/sistema.json`, `lake` para la puerta (`SPEC-30`) y `-X
utf8` en la consola de Windows.

La ficha sale de la entrevista cerrada de la obra. **Se borra al entregar** (`F-91`): si la
base ya no la tiene, el guion lo dice y se para antes de escribir nada; `--ficha` da la
misma ficha con la que se genero la novela (la de `novela_regalo.py FICHA.json`).

Sale con 0 si la version nueva se publico; con 1 si la peticion no se admite, si falta
algo, si se paro o si la puerta no la publico; con 2 si no se confirmo el gasto.
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
from app.commons.observabilidad.langfuse import crear_exportador  # noqa: E402
from app.commons.observabilidad.observacion import Observacion  # noqa: E402
from app.commons.trabajos import cola  # noqa: E402
from app.features.orquestacion import cascada, regeneracion  # noqa: E402
from novela_regalo import agentes, estado_de_langfuse  # noqa: E402


def crear_lean(sistema):
    """La puerta de publicacion con Lean de verdad (`SPEC-30`)."""
    from app.features.auditoria.lean import VerificadorLean
    return VerificadorLean(tiempo=sistema.lean.tiempo_maximo_segundos)


def _peticion(args):
    if args.hecho:
        return {"clase": "hecho", "hecho": args.hecho, "enunciado_nuevo": args.enunciado,
                "texto": args.texto}
    return {"clase": "nombre", "personaje": args.personaje, "nombre_nuevo": args.nombre,
            "texto": args.texto}


def imprimir_propuesta(p):
    print("=== PROPUESTA ===")
    print("obra: {0} | version de partida: {1} | clase: {2}".format(
        p["obra"], p["version_de_partida"], p["clase"]))
    print("salida: {0}".format(p["salida"] or "(sin elegir: {0})".format(p["motivo"])))
    lista = p["capitulos_propuestos"] or []
    print("capitulos que se van a tocar ({0}): {1}".format(len(lista), ", ".join(lista)))
    print("promesa: {0}".format(p["promesa"]))
    print("punto ciego: {0}".format(p["punto_ciego"]))


def imprimir_resultado(r):
    print("\n=== VERSION NUEVA ===")
    print("version {0} (desde el capitulo {1}; la de partida era la {2})".format(
        r["version"], r["desde_capitulo"], r["version_de_partida"]))
    print("capitulos cambiados: {0}".format(", ".join(r["capitulos_cambiados"])))
    print("capitulos compartidos: {0}".format(", ".join(r["capitulos_compartidos"])
                                              or "(ninguno)"))
    print("escenas escritas: {0}".format(", ".join(r["escenas_hechas"]) or "(ninguna)"))
    print("rendidas: {0}".format(r["rendidas"] or "(ninguna)"))
    print("parada: {0}".format(r["parada"] or "(ninguna)"))
    rv = r["reverificacion"]
    print("\n=== REVERIFICACION (sin modelo) ===")
    print("verificadas: {0} | fallidas: {1} | sin reverificar: {2}".format(
        len(rv["verificadas"]), rv["fallidas"] or "ninguna", rv["sin_reverificar"] or "ninguna"))
    c = r["coste"]
    print("\n=== COSTE ===")
    print("delegaciones: {0} | sin coste medido: {1}".format(c["delegaciones"], c["sin_coste"]))
    print("coste leido: {0:.4f} USD{1}".format(
        c["usd"], " (SUELO: hay delegaciones sin coste)" if c["sin_coste"] else ""))
    cierre = r.get("coste_del_cierre")
    if cierre is not None:
        print("  cierre (juicio de obra y puerta de publicacion): {0} delegaciones, "
              "{1:.4f} USD{2}".format(cierre["delegaciones"], cierre["usd"],
                                      " (SUELO)" if cierre["sin_coste"] else ""))
    pub = r["publicacion"]
    print("\n=== PUBLICACION ===")
    if pub is None:
        print("no se llego a la puerta: la version se paro antes")
    else:
        print("publicada" if pub["publicada"]
              else "NO se publica ({0})".format((pub["parada"] or {}).get("motivo")))
        print("rondas de esta version: {0}".format(pub["rondas"]))
        for cond in (pub["parada"] or {}).get("condiciones", []):
            print("  [{0}] {1}: {2}".format(cond.get("invariante"),
                                            cond.get("capitulo") or "(obra)",
                                            cond.get("detalle")))
    print("version que ve el lector: {0}".format(r["vigente"]))


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--base", required=True)
    p.add_argument("--obra", required=True)
    clase = p.add_mutually_exclusive_group(required=True)
    clase.add_argument("--hecho")
    clase.add_argument("--personaje")
    p.add_argument("--enunciado")
    p.add_argument("--nombre")
    p.add_argument("--texto", required=True)
    p.add_argument("--ficha", default=None)
    p.add_argument("--confirmo-el-gasto", action="store_true", dest="confirmado")
    args = p.parse_args(argv)
    if args.hecho and not args.enunciado:
        p.error("--hecho necesita --enunciado")
    if args.personaje and not args.nombre:
        p.error("--personaje necesita --nombre")

    if not os.path.exists(args.base):
        print("no existe la base {0}: no se crea una vacia".format(args.base))
        return 1
    con = sqlite3.connect(args.base)
    con.row_factory = sqlite3.Row
    try:
        return _ejecutar(con, args)
    finally:
        con.close()


def _ejecutar(con, args):
    migraciones.migrar(con)
    peticion = _peticion(args)
    # `F-147`: la ficha se lee antes de proponer. La propuesta la necesita para saber
    # quien es el destinatario, y una obra entregada ya no la tiene en la base (`F-91`).
    ficha = None
    if args.ficha:
        with open(args.ficha, encoding="utf-8") as f:
            ficha = FichaDeEntrevista.model_validate(json.load(f))
    try:
        propuesta = regeneracion.proponer(con, args.obra, peticion, ficha)
    except regeneracion.PeticionNoAdmitida as e:
        print("la peticion no se admite: {0}".format(e))
        return 1
    imprimir_propuesta(propuesta)
    if propuesta["salida"] is None:
        return 1
    if not args.confirmado:
        print("\nNo se ha pedido nada: regenerar gasta dinero. Para hacerlo, repite con "
              "--confirmo-el-gasto.")
        return 2

    if ficha is None:
        ficha = cascada.ficha_de(con, args.obra)
    if ficha is None:
        print("\nla obra {0} no tiene ficha en la base: se borra al entregar (F-91). Sin "
              "ella no hay bloque inmutable y no se inventa. Da la ficha con la que se genero "
              "con --ficha FICHA.json. No se ha escrito nada.".format(args.obra))
        return 1

    sistema = carga.cargar_sistema()
    procedencia.registrar(con, sistema=sistema.huella)
    try:
        id_trabajo, id_peticion = regeneracion.pedir(con, args.obra, dict(
            peticion, capitulos_propuestos=propuesta["capitulos_propuestos"]), ficha)
    except (regeneracion.PeticionNoAdmitida, regeneracion.SalidaSinElegir,
            regeneracion.ListaCambiada) as e:
        print("\nno se pudo pedir: {0}".format(e))
        return 1
    print("\npeticion {0}, trabajo {1}".format(id_peticion, id_trabajo))

    registro_hooks = os.path.join(tempfile.gettempdir(),
                                  "hooks-{0}.jsonl".format(args.obra))
    ag = agentes(sistema, {"HARNESS_DB": os.path.abspath(args.base),
                           "HARNESS_OBRA": args.obra,
                           "HARNESS_REGISTRO_HOOKS": registro_hooks})
    observacion = Observacion(crear_exportador(), con=con, obra=args.obra,
                              nombre="regeneracion")
    arranque = time.time()
    regeneracion.atender(con, id_trabajo, agentes=ag, ficha=ficha, sistema=sistema,
                         lean=crear_lean(sistema), carpeta_de_reglas=tempfile.gettempdir(),
                         observacion=observacion)
    t = cola.leer(con, id_trabajo)
    codigo = 1
    if t.estado.value != "terminado":
        print("\nEL TRABAJO NO TERMINO: {0}".format(t.motivo_ultimo_fallo))
    else:
        r = t.resultado
        imprimir_resultado(r)
        publicada = r["publicacion"] is not None and r["publicacion"]["publicada"]
        codigo = 0 if publicada and not r["parada"] else 1
    print("tiempo: {0:.0f} s".format(time.time() - arranque))
    print("\n=== LANGFUSE ===")
    print(estado_de_langfuse(observacion, observacion.vaciar()))
    return codigo


if __name__ == "__main__":
    sys.exit(main())
