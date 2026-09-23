"""F6 — Seis escenas seguidas, midiendo.

EL CRITERIO DE TERMINACION NO ES UNA PRUEBA VERDE
---------------------------------------------------
Es el primero del proyecto que no lo es: **la Fase F termina cuando el contexto
crece solo**. Una suite en verde con un contexto de 9.000 tokens ya la teniamos
y no contestaba nada.

Lo que esta ejecucion contesta:

    VER-37  si el reparto por niveles de `CLAUDE.md` basta para una escena real.
            Se midio dos veces con fixtures y las dos el contexto se quedo
            corto, porque **a mano no se llega al techo**.
    VER-64  con que frecuencia `INV-03` bloquea una generacion larga. No hay ni
            una medida.

Y SI SE PARA EN LA TERCERA, NO ES UN FRACASO
----------------------------------------------
`INV-03` es `bloqueante` y no admite rendicion: rendirse meteria un hecho falso
en el registro de conocimiento y todas las escenas siguientes se generarian
encima. **Una parada es el dato**, no una incidencia.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.modelo import proveedor
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, obra

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "f6.db")

INMUTABLE = """Terror domestico. Tercera persona limitada sobre Marta, pasado.
Prosa seca; el miedo viene de lo que no se explica. Nada de sangre.
La casa heredada no es hostil: es exacta, y eso es lo que asusta."""

ACCESOS = {"lug-salon": ["lug-cocina", "lug-pasillo"],
           "lug-cocina": ["lug-salon"],
           "lug-pasillo": ["lug-salon", "lug-sotano", "lug-dormitorio"],
           "lug-sotano": ["lug-pasillo"],
           "lug-dormitorio": ["lug-pasillo"]}

# `SPEC-15`: los hechos los declara el plan, no el texto. Derivarlos del
# registro de conocimiento fue el punto muerto de `F-29`, y por eso la
# ejecucion anterior salio con conocimiento 0 y fichas 0.
HECHOS = [
    {"id": "hec-herencia", "enunciado": "Marta heredo la casa de su tia"},
    {"id": "hec-sotano-cerrado", "enunciado": "El sotano esta cerrado por fuera"},
    {"id": "hec-llave-perdida", "enunciado": "La llave del sotano no aparece"},
    {"id": "hec-reloj-sin-cuerda", "enunciado": "El reloj del salon anda sin cuerda"},
    {"id": "hec-peldano-de-mas", "enunciado": "La escalera tiene un peldano mas al bajar"},
]

# `SPEC-18` C-2: el POV es del plan. Antes no se declaraba y el modelo elegia
# -y eligio a Ana con la escaleta pidiendo Marta (`F-34`)-.
ESCALETA = [
    (1, "cordura", "lug-salon", "Marta recorre la casa heredada y cuenta los peldanos."),
    (2, "seguridad", "lug-pasillo", "Marta encuentra el sotano cerrado y no aparece la llave."),
    (3, "conocimiento", "lug-salon", "Ana llega y niega lo que Marta cree haber visto."),
    (4, "vinculo", "lug-cocina", "Las hermanas discuten; Marta deja de contarle lo que ve."),
    (5, "control", "lug-pasillo", "Marta fuerza la puerta del sotano."),
    (6, "cordura", "lug-sotano", "Lo que hay abajo es exactamente lo que Marta esperaba."),
]

# `SPEC-17` C-1: quien sabe que **antes de la escena 1**. Sin esto el registro
# arranca vacio y ninguna accion es posible en la primera escena (`F-32`):
# Marta heredo la casa antes del relato, y eso no lo revela ninguna escena.
CONOCIMIENTO_INICIAL = [
    {"sujeto": "per-marta", "hecho": "hec-herencia", "grado": "sabe"},
    {"sujeto": "per-ana", "hecho": "hec-herencia", "grado": "sabe"},
    {"sujeto": "per-marta", "hecho": "hec-reloj-sin-cuerda", "grado": "ignora"},
]


def main():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    con = sqlite3.connect(RUTA)
    for m in (repo, aplicar, memoria):
        m.asegurar_tablas(con)
    aplicar.sembrar(con, {"per-marta": ("vivo", "lug-salon"),
                          "per-ana": ("vivo", "lug-cocina")})
    mundo.sembrar_lugares(con, ACCESOS)
    repo.guardar_escaleta(con, "cap-1", [
        {"id": "e{0}".format(n), "orden": n,
         "cambio_de_valor": {"eje": eje, "signo": "negativo"},
         "pov": "per-marta", "lugar": lugar,
         "beats": ["b{0}".format(n)], "longitud_objetivo": [300, 900]}
        for n, eje, lugar, _ in ESCALETA])
    repo.declarar_hechos(con, "cap-1", HECHOS)
    mundo.sembrar_conocimiento(con, CONOCIMIENTO_INICIAL)

    escritor = proveedor.SesionDelegada(agente="escritor")
    juez = ciclo.juez_aislado()
    resumidor = proveedor.SesionDelegada(
        modelo=os.environ.get("HARNESS_MODELO_RESUMIDOR", "haiku"), agente="resumidor")

    g = obra.generar_obra(con, "cap-1", escritor, juez, resumidor,
                          inmutable=INMUTABLE, techo=100_000)

    print("\n=== EL CONTEXTO, ESCENA A ESCENA (VER-37) ===")
    print(obra.informe(g))
    print("\n=== DESGLOSE POR BLOQUE ===")
    if g.medidas:
        nombres = [n for n in g.medidas[0]["bloques"] if n != "reserva_de_salida"]
        print("escena  " + "  ".join(n[:11].rjust(11) for n in nombres))
        for m in g.medidas:
            print("{0:6}  ".format(m["escena"]) +
                  "  ".join(str(m["bloques"][n]).rjust(11) for n in nombres))
    print("\n=== LOS HECHOS DECLARADOS, Y DONDE LOS ESTABLECE EL TEXTO ===")
    for h in repo.hechos_declarados(con, "cap-1"):
        print("  {0:22} {1}".format(
            h["id"], h["establecido_en"] or "SIN ESTABLECER"))
    print("entradas de conocimiento:", len(mundo.leer(con)["conocimiento"]))

    print("\n=== RENDICIONES, COSTE Y CIERRE ===")
    print("escenas rendidas:", g.rendidas or "ninguna")
    print("delegaciones:", g.coste["delegaciones"],
          "| con coste medido:", g.coste["delegaciones"] - g.coste["sin_coste"],
          "| SIN MEDIR:", g.coste["sin_coste"])
    print("coste leido: {0:.4f} USD".format(g.coste["usd"]))
    print("cierre:", json.dumps(g.cierre, ensure_ascii=False)[:300] if g.cierre
          else "no se evalua: la obra se detuvo")

    print("\nescenas completas:", len(g.escenas_hechas))
    print("parada:", json.dumps(g.parada, ensure_ascii=False)[:400] if g.parada
          else "ninguna: llego al final")
    con.close()


if __name__ == "__main__":
    main()
