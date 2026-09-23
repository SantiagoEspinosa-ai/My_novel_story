"""Una obra de diez capitulos, de principio a fin.

QUE SE MIDE AQUI QUE NO SE HAYA MEDIDO ANTES
----------------------------------------------
Todo lo anterior fueron entre una y seis escenas. Esto es lo primero que puede
contestar tres cosas que solo aparecen con longitud:

    VER-37  si el contexto crece **hasta acercarse al techo** o se estanca.
            Cinco medidas dijeron que sobra; ninguna llego a diez escenas.
    VER-64  la frecuencia real de `INV-03`. Hay ~29% con n=7, que es poco.
    F-38    si la reanudacion aguanta de verdad: aqui se usa en serio.

EL DESATASCO AUTOMATICO SOLO DICE COSAS DEL CONTRATO
------------------------------------------------------
Cuando un capitulo se para, este guion reintenta **una vez** con una
instruccion humana. Esa instruccion **no decide nada sobre la novela**: le
recuerda al modelo la diferencia entre revelar y actuar, que es materia del
contrato y esta escrita en `SPEC-16`.

Lo que no hace, y es deliberado: **no inventa revelaciones ni toca el estado**.
Si el modelo hizo que un personaje supiera algo que no sabe, eso es una
decision sobre la ficcion y la toma una persona. El guion se para y lo dice.
"""

import json
import os
import sqlite3
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.configuracion import carga
from app.commons.db import migraciones, procedencia
from app.commons.modelo import proveedor
from app.features.consolidacion import deltas
from app.features.cronologia import consultas
from app.features.cronologia import repository as usos
from app.features.observabilidad import repository as observabilidad
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.brief import repository as brief
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, obra

# La ruta la dice `config/sistema.json`. `HARNESS_BASE` la sustituye para
# poder repetir una obra sin pisar la anterior: **la comparacion entre las dos
# es el dato**, asi que borrar la primera seria tirar la mitad de la medida.
#
# Se define despues de cargar el sistema, mas abajo, para que no haya dos
# sitios que digan donde vive la base.

# LA FORMA Y EL TONO SALEN DE `config/brief.json`; LA MAQUINA, DE `sistema.json`
# ------------------------------------------------------------------------------
# Estaban aqui dentro, y por eso nadie noto durante diez capitulos que se
# estaban modelando **diez obras** (`F-53`, `F-56`). Lo que sigue en el guion es
# el plan concreto -las sinopsis, los hechos, el mundo-; lo que se puede cambiar
# sin tocar codigo esta en los dos ficheros.
BRIEF = carga.cargar_brief()
SISTEMA = carga.cargar_sistema()

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                    os.environ.get("HARNESS_BASE", SISTEMA.ruta_de_la_base))

INMUTABLE = BRIEF.inmutable

# TODO LO QUE DEFINE LA OBRA SALE DE `config/brief.json`
# -------------------------------------------------------
# Aqui vivian el mundo, los hechos, el conocimiento inicial y las sesenta
# escenas con su sinopsis. Mientras estuvieron aqui, cambiar `capitulos: 3` en
# el fichero **fallaba**: el fichero decia una cosa y el codigo traia otra, que
# es la ventana donde vivio `F-53` durante diez capitulos.
#
# Ahora editar el fichero cambia la obra, que es lo unico que hace verdad la
# frase. Lo que queda en este guion es **como se genera**, no **que** se genera.
PLAN = BRIEF.plan
OBRA = BRIEF.obra_id

ACCESOS = {l.id: l.accesos for l in PLAN.mundo.lugares}
PERSONAS = {p.id: (str(p.estado_vital), p.empieza_en) for p in PLAN.mundo.personajes}
HECHOS = [(h.id, h.enunciado) for h in PLAN.hechos]
CONOCIMIENTO_INICIAL = [
    {"sujeto": k.sujeto, "hecho": k.hecho, "grado": str(k.grado)}
    for k in PLAN.mundo.conocimiento_inicial]
CAPITULOS = [
    (c.id, c.titulo,
     [(e.eje, e.lugar, e.sinopsis, e.establece, e.pov, e.signo)
      for e in c.escenas])
    for c in PLAN.capitulos]


def preparar(con):
    """Deja la base **completa** antes de escribir la primera escena.

    La primera ejecucion no hacia esto y acabo con **diez de las veintitres
    tablas del arbol** (`F-52`): faltaban `delta_de_escena`, `uso_de_hecho`,
    `evento_cronologico`, `lectura_de_contexto` y hasta `esquema_version`. La
    consecuencia no fue un numero equivocado sino algo peor: **la base se quedo
    sin las columnas que harian falta para saber si sus numeros significan
    algo**. Sin `delta_de_escena` no hay forma de saber si `INV-03` tuvo una
    sola accion que comprobar, asi que su cero no se puede interpretar; y sin
    `evento_cronologico` la verificacion formal no puede correr en absoluto.

    Tres cosas que la primera no hizo, en este orden:

        migrar          lleva el esquema a la ultima version y deja
                        `esquema_version`, sin la cual ni siquiera consta por
                        donde va la base
        procedencia     con que commit se escribio. Es lo que `MF-27` pide y
                        lo que la primera base no puede tener ya nunca
        asegurar        todas las features que van a escribir, no solo tres
    """
    # La forma y el plan ya no pueden divergir: se valida **al cargar el
    # fichero**, dentro del esquema, asi que un brief mal escrito no llega
    # hasta aqui.
    migraciones.migrar(con)
    # Con que codigo **y con que brief**: las dos mitades del par que permite
    # repetir una tanda exactamente en vez de aproximadamente.
    procedencia.registrar(con, brief=BRIEF.huella,
                          sistema=SISTEMA.huella)
    for m in (repo, aplicar, memoria, deltas, usos, observabilidad):
        m.asegurar_tablas(con)
    aplicar.sembrar(con, PERSONAS)
    mundo.sembrar_lugares(con, ACCESOS)

    # El alta la hace **una sola funcion**, no este guion con `INSERT` a mano.
    # La forma de la obra vive en el brief; darla de alta desde dos sitios es
    # como vuelven a divergir (`F-56`). Los valores salen del brief y el orden
    # de los capitulos es el de `CAPITULOS`, que es lo que
    # `asignar_t_discurso` necesita para numerar el orden de lectura.
    brief.alta_de_obra(
        con, OBRA,
        {"titulo": BRIEF.titulo, "premisa": BRIEF.premisa, "genero": BRIEF.genero},
        [cap for cap, _t, _e in CAPITULOS])

    for cap, _titulo, escenas in CAPITULOS:
        repo.guardar_escaleta(con, OBRA, [
            {"id": "{0}-e{1}".format(cap, n), "orden": n,
             # `SPEC-21` C-1 y la decision del autor: el alcance de la escena
             # anterior es el **capitulo**. Sin declararlo, todas las escenas
             # de la obra caen en el mismo grupo y el corte no existe.
             "capitulo": cap,
             "cambio_de_valor": {"eje": eje, "signo": signo},
             "pov": pov, "lugar": lugar,
             "beats": [{"id": "{0}-b{1}".format(cap, n), "establece": establece}],
             # Del brief: `INV-17` compara contra esto, asi que cambiar el
             # rango en el fichero cambia lo que la invariante exige.
             "longitud_objetivo": list(BRIEF.forma.palabras_por_escena)}
            for n, (eje, lugar, _sinopsis, establece, pov, signo)
            in enumerate(escenas, 1)])
    # Una sola vez, para la obra entera. Declararlos por capitulo era lo que
    # los hacia colisionar: son los hechos de **la novela**, no de un capitulo.
    repo.declarar_hechos(con, OBRA, [{"id": h, "enunciado": e} for h, e in HECHOS])
    mundo.sembrar_conocimiento(con, CONOCIMIENTO_INICIAL)


def agentes():
    return (proveedor.SesionDelegada(modelo=SISTEMA.modelos.escritor,
                                     agente="escritor"),
            ciclo.juez_aislado(),
            proveedor.SesionDelegada(modelo=SISTEMA.modelos.resumidor,
                                     agente="resumidor"))


def main():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    con = sqlite3.connect(RUTA)
    preparar(con)
    escritor, juez, resumidor = agentes()

    arranque = time.time()
    total = {"escenas": 0, "usd": 0.0, "delegaciones": 0, "sin_coste": 0,
             "bloqueos": 0, "rendidas": 0, "desatascos": 0}
    # `F-41`: las escenas que se quedaron sin resumen. Se cuentan aparte
    # porque una escena sin memoria no es lo mismo que una que no tenia nada
    # que resumir, y con el silencio de antes eran indistinguibles.
    sin_resumen = []
    medidas = []
    parada_final = None

    for cap, titulo, _escenas in CAPITULOS:
        print("\n### {0} — {1}".format(cap, titulo), flush=True)
        instrucciones = None
        for vuelta in (1, 2):
            # `capitulo=cap` recorre solo ese capitulo y evalua su puerta
            # sobre el. Sin el, una sola llamada generaria las sesenta escenas
            # de un tiron y se perderia el reintento por capitulo.
            g = obra.generar_obra(con, OBRA, escritor, juez, resumidor,
                                  inmutable=INMUTABLE,
                                  techo=SISTEMA.presupuesto.techo_de_contexto,
                                  tope_intentos=SISTEMA.topes.intentos_por_escena,
                                  tope_delegaciones=SISTEMA.topes.delegaciones_por_obra,
                                  instrucciones=instrucciones, capitulo=cap)
            total["escenas"] += len(g.escenas_hechas)
            total["usd"] += g.coste["usd"]
            total["delegaciones"] += g.coste["delegaciones"]
            total["sin_coste"] += g.coste["sin_coste"]
            total["rendidas"] += len(g.rendidas)
            sin_resumen.extend(g.sin_resumen)
            medidas.extend(g.medidas)
            print("  hechas {0} | saltadas {1} | {2:.4f} USD".format(
                len(g.escenas_hechas), len(g.saltadas), g.coste["usd"]), flush=True)

            if g.parada is None:
                break
            total["bloqueos"] += 1
            print("  PARADA en {0}: {1}".format(
                g.parada["escena"], g.parada["motivo"]), flush=True)
            for inv, desc in g.parada.get("hallazgos", []):
                print("     [{0}] {1}".format(inv, desc), flush=True)
            if vuelta == 1 and g.parada["motivo"] == "bloqueante":
                # Un solo desatasco, y solo del contrato.
                total["desatascos"] += 1
                instrucciones = INSTRUCCION_DE_CONTRATO
                print("  desatascando con la instruccion de contrato...", flush=True)
                continue
            parada_final = dict(g.parada, capitulo=cap)
            break
        if parada_final:
            break

    print("\n" + "=" * 62)
    print("=== LA OBRA ===")
    print("escenas escritas: {0} de {1}".format(
        total["escenas"], sum(len(e) for _, _, e in CAPITULOS)))
    print("bloqueos: {0} | desatascados con instruccion: {1} | rendidas: {2}".format(
        total["bloqueos"], total["desatascos"], total["rendidas"]))
    print("delegaciones: {0} | SIN coste medido: {1}".format(
        total["delegaciones"], total["sin_coste"]))
    print("coste leido: {0:.4f} USD".format(total["usd"]))
    print("escenas SIN resumen (F-41): {0}{1}".format(
        len(sin_resumen), " -> " + ", ".join(sin_resumen) if sin_resumen else ""))
    print("minutos: {0:.1f}".format((time.time() - arranque) / 60))
    _p = procedencia.leer(con)
    print("procedencia -> codigo {0} | brief {1} | sistema {2}".format(
        _p["version"], _p["brief"], _p["sistema"]))

    # Lo que decide si el cero de `INV-03` es limpio o es ausencia de material
    # (`F-30`, `F-52`). Sin esto, un cero de bloqueos no se puede interpretar.
    print("\n=== TUVIERON LAS PUERTAS ALGO QUE RECHAZAR? ===")
    acciones = revelaciones = 0
    for fila in con.execute("SELECT delta FROM delta_de_escena"):
        d = json.loads(fila[0]) if fila[0] else {}
        acciones += len(d.get("acciones") or [])
        revelaciones += len(d.get("revelaciones") or [])
    filas = con.execute("SELECT COUNT(*) FROM delta_de_escena").fetchone()[0]
    print("acciones declaradas: {0}, leidas de {1} delta(s) de la obra {2}"
          "  <- lo que INV-03 compara".format(acciones, filas, OBRA))
    print("revelaciones declaradas: {0}, de los mismos {1} delta(s)"
          "  <- lo que alimenta el registro".format(revelaciones, filas))
    if filas == 0:
        print("  AVISO: cero deltas guardados. Los dos numeros de arriba son")
        print("  el resultado de no haber mirado nada, no una medida.")
    if acciones == 0:
        print("  AVISO: cero acciones significa que INV-03 no tuvo NADA que")
        print("  mirar. Su cero de bloqueos no dice que la obra este limpia.")

    if medidas:
        print("\n=== EL CONTEXTO (VER-37) ===")
        print("primera escena: {0} tokens".format(medidas[0]["total"]))
        print("ultima escena:  {0} tokens".format(medidas[-1]["total"]))
        # Lo que la longitud existe para contestar: si crece **entre**
        # capitulos o se reinicia en cada uno (`F-40`, `F-45`).
        por_capitulo = {}
        for m in medidas:
            cap = m["escena"].rsplit("-e", 1)[0]
            por_capitulo.setdefault(cap, []).append(m["total"])
        print("\nmedia por capitulo:")
        for cap in sorted(por_capitulo):
            v = por_capitulo[cap]
            print("  {0}  primera {1:5}  ultima {2:5}  media {3:6.0f}".format(
                cap, v[0], v[-1], sum(v) / len(v)))
        print("maximo:         {0} tokens".format(max(m["total"] for m in medidas)))
        recortes = sum(1 for m in medidas if m["recortes"])
        print("escenas con recorte: {0} de {1}".format(recortes, len(medidas)))

    # Pregunta 3: puede la verificacion formal correr sobre esto. Sin eventos
    # con `t_fabula` legible no hay eje de fabula que comparar, y Lean diria
    # "0 violaciones" sobre una obra que no ha mirado (`F-54`).
    print("\n=== LA CRONOLOGIA (puede correr la verificacion formal?) ===")
    try:
        eventos = usos.eventos_de(con, OBRA)
        con_fecha = [e for e in eventos if e.get("t_fabula")]
        print("{0} evento(s) de la obra {1}, {2} con `t_fabula` legible".format(
            len(eventos), OBRA, len(con_fecha)))
        if not eventos:
            print("  AVISO: sin eventos, las cuatro invariantes de Lean no")
            print("  pueden decir nada. Un cero suyo no seria un cero limpio.")
    except Exception as e:
        print("  no se pudo consultar:", type(e).__name__, e)

    # Pregunta 4: cuanto arrastra cambiar un hecho. Decide entre `S-1` y `S-2`
    # con un numero en vez de a ojo, y si `menciona` entra en la regeneracion.
    print("\n=== ARRASTRE POR HECHO (S-1 contra S-2) ===")
    try:
        ids = [h for h, _ in HECHOS]
        for h in ids:
            caps = consultas.capitulos_a_regenerar(con, h)
            print("  {0:24} regenera {1} capitulo(s)".format(h, len(caps)))
        print(" con mencion:",
              json.dumps(consultas.arrastre_de_incluir_mencion(con, ids),
                         ensure_ascii=False)[:300])
    except Exception as e:
        print("  no se pudo consultar:", type(e).__name__, e)

    print("\n=== EL CANON ===")
    # `OBRA` y no un capitulo: los hechos se declaran una vez para la obra
    # entera. Con el identificador de capitulo esto devolvia `[]` y la seccion
    # del canon salia **en blanco** — que es justo la que se lee para juzgar si
    # la generacion funciono, y la misma que `F-39` ya dejo muda una vez por
    # otra causa. Un canon vacio se lee como "no se establecio nada" y no como
    # "la consulta pregunto por otra cosa".
    establecidos = repo.hechos_declarados(con, OBRA)
    print("{0} hecho(s) declarado(s) para la obra {1}".format(
        len(establecidos), OBRA))
    if not establecidos:
        print("  AVISO: la obra no tiene hechos declarados. Esta seccion ha")
        print("  salido muda tres veces por tres causas distintas, asi que un")
        print("  vacio aqui es sospechoso antes que informativo.")
    for h in establecidos:
        print("  {0:24} {1}".format(h["id"], h["establecido_en"] or "SIN ESTABLECER"))
    print("entradas de conocimiento:", len(mundo.leer(con)["conocimiento"]))

    print("\nparada final:", json.dumps(parada_final, ensure_ascii=False)[:400]
          if parada_final else "ninguna: la obra llego al final")
    con.close()


if __name__ == "__main__":
    main()
