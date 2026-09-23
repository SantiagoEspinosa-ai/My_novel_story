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

from app.commons.modelo import proveedor
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, obra

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "obra10.db")

INMUTABLE = """Terror domestico. Tercera persona limitada sobre Marta, pasado.
Prosa seca; el miedo viene de lo que no se explica. Nada de sangre.
La casa heredada no es hostil: es exacta, y eso es lo que asusta.
Las escenas son cortas. Se corta antes de explicar."""

ACCESOS = {"lug-salon": ["lug-cocina", "lug-pasillo"],
           "lug-cocina": ["lug-salon"],
           "lug-pasillo": ["lug-salon", "lug-sotano", "lug-dormitorio", "lug-desvan"],
           "lug-sotano": ["lug-pasillo"],
           "lug-dormitorio": ["lug-pasillo"],
           "lug-desvan": ["lug-pasillo"]}

PERSONAS = {"per-marta": ("vivo", "lug-salon"), "per-ana": ("vivo", "lug-cocina")}

# Los hechos de la obra entera. `SPEC-15`: los declara el plan, no el texto.
HECHOS = [
    ("hec-herencia", "Marta heredo la casa de su tia Ubalda"),
    ("hec-sotano-cerrado", "El sotano esta cerrado por fuera"),
    ("hec-llave-perdida", "La llave del sotano no aparece"),
    ("hec-reloj-sin-cuerda", "El reloj del salon anda sin que nadie le de cuerda"),
    ("hec-peldano-de-mas", "La escalera tiene un peldano mas al bajar que al subir"),
    ("hec-ana-vivio-aqui", "Ana vivio en la casa de nina y no lo ha contado"),
    ("hec-ubalda-no-salia", "La tia Ubalda llevaba anos sin salir de la casa"),
    ("hec-cuarto-tapiado", "Hay un cuarto tapiado detras del desvan"),
    ("hec-cartas", "En el desvan hay cartas de Ubalda sin enviar"),
    ("hec-nombre-repetido", "En las cartas aparece el nombre de Marta antes de nacer"),
]

# `SPEC-17`: quien sabe que **antes de la escena 1**.
CONOCIMIENTO_INICIAL = [
    {"sujeto": "per-marta", "hecho": "hec-herencia", "grado": "sabe"},
    {"sujeto": "per-ana", "hecho": "hec-herencia", "grado": "sabe"},
    {"sujeto": "per-ana", "hecho": "hec-ana-vivio-aqui", "grado": "sabe"},
    {"sujeto": "per-marta", "hecho": "hec-ana-vivio-aqui", "grado": "ignora"},
]

# Diez capitulos de seis escenas. Cada escena: eje, lugar, sinopsis y los
# hechos que el plan promete que se establecen ahi (`SPEC-19`).
CAPITULOS = [
    ("cap-01", "Llegar", [
        ("cordura", "lug-salon", "Marta recorre la casa y cuenta los peldanos.", ["hec-peldano-de-mas"]),
        ("seguridad", "lug-pasillo", "La puerta del sotano no cede.", ["hec-sotano-cerrado"]),
        ("control", "lug-cocina", "Marta busca la llave en todos los cajones.", ["hec-llave-perdida"]),
        ("cordura", "lug-salon", "El reloj sigue andando por la noche.", ["hec-reloj-sin-cuerda"]),
        ("vinculo", "lug-salon", "Ana llama por telefono y no pregunta por la casa.", []),
        ("cordura", "lug-dormitorio", "Marta no duerme y cuenta desde la cama.", []),
    ]),
    ("cap-02", "Ana", [
        ("vinculo", "lug-salon", "Ana llega con una maleta pequena.", []),
        ("conocimiento", "lug-cocina", "Ana se mueve por la casa sin preguntar donde esta nada.", ["hec-ana-vivio-aqui"]),
        ("seguridad", "lug-pasillo", "Marta le ensena la puerta y Ana no la mira.", []),
        ("vinculo", "lug-salon", "Discuten por la herencia sin nombrarla.", []),
        ("cordura", "lug-dormitorio", "Marta cuenta los peldanos otra vez y salen distintos.", []),
        ("control", "lug-cocina", "Ana propone vender.", []),
    ]),
    ("cap-03", "Ubalda", [
        ("conocimiento", "lug-salon", "Aparecen las facturas: Ubalda no salia.", ["hec-ubalda-no-salia"]),
        ("cordura", "lug-pasillo", "Marta mide la escalera con una cinta.", []),
        ("vinculo", "lug-cocina", "Ana se enfada cuando Marta pregunta por la infancia.", []),
        ("seguridad", "lug-salon", "Alguien ha parado el reloj.", []),
        ("control", "lug-pasillo", "Marta decide forzar la puerta y no lo hace.", []),
        ("cordura", "lug-dormitorio", "La casa suena a la misma hora.", []),
    ]),
    ("cap-04", "El desvan", [
        ("seguridad", "lug-desvan", "Marta sube al desvan por primera vez.", []),
        ("conocimiento", "lug-desvan", "Encuentra las cartas de Ubalda.", ["hec-cartas"]),
        ("cordura", "lug-desvan", "Hay una pared que suena hueca.", ["hec-cuarto-tapiado"]),
        ("vinculo", "lug-salon", "Marta no le cuenta a Ana lo del desvan.", []),
        ("control", "lug-cocina", "Ana pregunta que hacia arriba.", []),
        ("cordura", "lug-dormitorio", "Marta lee una carta y la deja a medias.", []),
    ]),
    ("cap-05", "El nombre", [
        ("conocimiento", "lug-desvan", "En una carta esta su nombre, fechada antes.", ["hec-nombre-repetido"]),
        ("cordura", "lug-salon", "Marta comprueba la fecha tres veces.", []),
        ("vinculo", "lug-cocina", "Se lo ensena a Ana y Ana no se sorprende.", []),
        ("seguridad", "lug-pasillo", "La puerta del sotano esta entreabierta.", []),
        ("control", "lug-salon", "Marta cierra la puerta y no baja.", []),
        ("cordura", "lug-dormitorio", "Cuenta los peldanos desde arriba.", []),
    ]),
    ("cap-06", "Lo que Ana sabia", [
        ("conocimiento", "lug-cocina", "Ana cuenta que vivio aqui de nina.", []),
        ("vinculo", "lug-salon", "Marta deja de creer lo que Ana dice.", []),
        ("seguridad", "lug-pasillo", "Las dos oyen algo abajo.", []),
        ("cordura", "lug-dormitorio", "Marta duerme con la luz dada.", []),
        ("control", "lug-salon", "Ana se va a dormir temprano.", []),
        ("conocimiento", "lug-desvan", "Marta relee las cartas buscando a Ana.", []),
    ]),
    ("cap-07", "La pared", [
        ("control", "lug-desvan", "Marta golpea la pared hueca.", []),
        ("seguridad", "lug-desvan", "Detras hay un hueco y no un cuarto.", []),
        ("cordura", "lug-salon", "El reloj vuelve a andar.", []),
        ("vinculo", "lug-cocina", "Ana pregunta por los golpes y Marta miente.", []),
        ("conocimiento", "lug-desvan", "En el hueco hay ropa de nina.", []),
        ("cordura", "lug-dormitorio", "Marta no cuenta los peldanos esa noche.", []),
    ]),
    ("cap-08", "Bajar", [
        ("control", "lug-pasillo", "Marta fuerza la puerta del sotano.", []),
        ("seguridad", "lug-sotano", "El sotano esta vacio y limpio.", []),
        ("cordura", "lug-sotano", "Hay catorce peldanos bajando y quince subiendo.", []),
        ("vinculo", "lug-salon", "Ana la encuentra sentada en la escalera.", []),
        ("conocimiento", "lug-cocina", "Ana admite que Ubalda la echo de la casa.", []),
        ("cordura", "lug-dormitorio", "Marta cuenta en voz alta y no para.", []),
    ]),
    ("cap-09", "La exactitud", [
        ("cordura", "lug-salon", "Todo esta donde Marta lo dejo, y mas ordenado.", []),
        ("seguridad", "lug-pasillo", "La puerta vuelve a estar cerrada.", []),
        ("vinculo", "lug-cocina", "Ana hace la maleta.", []),
        ("control", "lug-salon", "Marta le pide que se quede y no lo dice asi.", []),
        ("conocimiento", "lug-desvan", "Falta una carta.", []),
        ("cordura", "lug-dormitorio", "Marta oye contar a alguien.", []),
    ]),
    ("cap-10", "Quedarse", [
        ("vinculo", "lug-salon", "Ana se va sin despedirse.", []),
        ("cordura", "lug-pasillo", "Marta baja al sotano sin linterna.", []),
        ("seguridad", "lug-sotano", "Abajo esta exactamente lo que esperaba.", []),
        ("control", "lug-salon", "Marta le da cuerda al reloj.", []),
        ("cordura", "lug-dormitorio", "Se acuesta y cuenta hasta catorce.", []),
        ("vinculo", "lug-salon", "La casa queda en orden.", []),
    ]),
]

# Lo unico que el desatasco automatico tiene permitido decir. Es materia de
# **contrato** -la diferencia entre revelar y actuar, `SPEC-16`- y no decide
# nada sobre la ficcion. Lo que el modelo haga con ella es cosa suya.
INSTRUCCION_DE_CONTRATO = [
    "Revisa la diferencia entre `revelaciones` y `acciones`. En `revelaciones` "
    "va todo hecho del que un personaje PASA A ENTERARSE en esta escena. En "
    "`acciones` va solo aquello de lo que el personaje YA estaba enterado "
    "antes de empezar. Si obra con algo que acaba de descubrir, declara las "
    "dos cosas.",
]


def preparar(con):
    for m in (repo, aplicar, memoria):
        m.asegurar_tablas(con)
    aplicar.sembrar(con, PERSONAS)
    mundo.sembrar_lugares(con, ACCESOS)
    for cap, _titulo, escenas in CAPITULOS:
        repo.guardar_escaleta(con, cap, [
            {"id": "{0}-e{1}".format(cap, n), "orden": n,
             "cambio_de_valor": {"eje": eje, "signo": "negativo"},
             "pov": "per-marta", "lugar": lugar,
             "beats": [{"id": "{0}-b{1}".format(cap, n), "establece": establece}],
             "longitud_objetivo": [250, 800]}
            for n, (eje, lugar, _sinopsis, establece) in enumerate(escenas, 1)])
        repo.declarar_hechos(con, cap, [
            {"id": h, "enunciado": e} for h, e in HECHOS])
    mundo.sembrar_conocimiento(con, CONOCIMIENTO_INICIAL)


def agentes():
    return (proveedor.SesionDelegada(agente="escritor"),
            ciclo.juez_aislado(),
            proveedor.SesionDelegada(
                modelo=os.environ.get("HARNESS_MODELO_RESUMIDOR", "haiku"),
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
    medidas = []
    parada_final = None

    for cap, titulo, _escenas in CAPITULOS:
        print("\n### {0} — {1}".format(cap, titulo), flush=True)
        instrucciones = None
        for vuelta in (1, 2):
            g = obra.generar_obra(con, cap, escritor, juez, resumidor,
                                  inmutable=INMUTABLE, techo=100_000,
                                  instrucciones=instrucciones)
            total["escenas"] += len(g.escenas_hechas)
            total["usd"] += g.coste["usd"]
            total["delegaciones"] += g.coste["delegaciones"]
            total["sin_coste"] += g.coste["sin_coste"]
            total["rendidas"] += len(g.rendidas)
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
    print("minutos: {0:.1f}".format((time.time() - arranque) / 60))

    if medidas:
        print("\n=== EL CONTEXTO (VER-37) ===")
        print("primera escena: {0} tokens".format(medidas[0]["total"]))
        print("ultima escena:  {0} tokens".format(medidas[-1]["total"]))
        print("maximo:         {0} tokens".format(max(m["total"] for m in medidas)))
        recortes = sum(1 for m in medidas if m["recortes"])
        print("escenas con recorte: {0} de {1}".format(recortes, len(medidas)))

    print("\n=== EL CANON ===")
    establecidos = repo.hechos_declarados(con, CAPITULOS[0][0])
    for h in establecidos:
        print("  {0:24} {1}".format(h["id"], h["establecido_en"] or "SIN ESTABLECER"))
    print("entradas de conocimiento:", len(mundo.leer(con)["conocimiento"]))

    print("\nparada final:", json.dumps(parada_final, ensure_ascii=False)[:400]
          if parada_final else "ninguna: la obra llego al final")
    con.close()


if __name__ == "__main__":
    main()
