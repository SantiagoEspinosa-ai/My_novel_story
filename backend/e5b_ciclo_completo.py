"""E5b — Segunda ejecucion: ciclo completo, tres agentes, estado real.

CIERRA TRES COSAS A LA VEZ
---------------------------
    VER-34   el reparto de tokens por agente. La primera ejecucion tuvo un
             solo agente, asi que no habia reparto que medir.
    VER-37   la suficiencia del reparto por niveles. Alli el contexto fueron
             138 tokens y no hubo ni un recorte: los niveles no se rozaron.
    El caché Si amortiza entre delegaciones. En la primera `cache_read` fue
             **cero** -era la primera llamada- y eso es lo unico que separa una
             obra de 150 dolares de una de 1.428.

Por eso el contexto de aqui es **grande a proposito**: un estado del mundo con
entidades, hechos, resumenes y una escena anterior entera. Medir la
amortizacion con un contexto de juguete no mediria nada.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.modelo import proveedor
from app.features.consolidacion import aplicar
from app.features.contexto.bloques import BLOQUES
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e5b.db")

PERSONAJES = ["per-marta", "per-ana", "per-tia-remedios"]
HECHOS = ["hec-herencia", "hec-sotano-cerrado", "hec-llave-perdida",
          "hec-reloj-sin-cuerda", "hec-peldano-de-mas"]

ESTADO_REAL = {
    "entidades_vivas": {"per-marta": "vivo", "per-ana": "vivo",
                        "per-tia-remedios": "muerto"},
    "ubicaciones": {"per-marta": "lug-salon", "per-ana": "lug-cocina"},
    "accesos": {"lug-salon": ["lug-cocina", "lug-sotano"],
                "lug-cocina": ["lug-salon"], "lug-sotano": ["lug-salon"]},
    # Los dos personajes conocen los mismos hechos. En la ejecucion anterior
    # solo `per-marta` conocia el sotano, el modelo hizo revelar a `per-ana`, e
    # `INV-03` lo detuvo: la puerta funcionando, no un fallo. Aqui se abre el
    # registro para que el ciclo llegue entero y se pueda medir el cache.
    "conocimiento": {(p, h): {"desde": 1, "grado": "sabe"}
                     for p in ("per-marta", "per-ana")
                     for h in ("hec-herencia", "hec-sotano-cerrado",
                               "hec-llave-perdida", "hec-reloj-sin-cuerda",
                               "hec-peldano-de-mas")},
}

# Escena anterior entera, fichas y resumenes: el bloque `Local` de verdad.
ESCENA_ANTERIOR = ("La llave no estaba en el cajon de la cocina, ni en el "
                   "bolsillo del abrigo de la tia, ni colgada del clavo donde "
                   "colgaban todas las llaves de la casa. " * 40)

ESCENA = {"id": "e2", "orden": 2,
          "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
          "beats": ["b2"], "longitud_objetivo": [400, 900]}


def main():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    con = sqlite3.connect(RUTA)
    repo.asegurar_tablas(con)
    aplicar.asegurar_tablas(con)
    aplicar.sembrar(con, {"per-marta": ("vivo", "lug-salon"),
                          "per-ana": ("vivo", "lug-cocina")})
    repo.guardar_escaleta(con, "cap-1", [ESCENA])

    escritor = proveedor.SesionDelegada(agente="escritor")
    juez = ciclo.juez_aislado()
    resumidor = proveedor.SesionDelegada(
        modelo=os.environ.get("HARNESS_MODELO_RESUMIDOR", "haiku"),
        agente="resumidor")

    print("escritor : {0}".format(escritor.nombre))
    print("juez     : {0}  (cwd aislado: {1})".format(juez.nombre, juez.cwd))
    print("resumidor: {0}".format(resumidor.nombre))

    contexto = {b.nombre: 0 for b in BLOQUES}
    contexto["estado_y_conocimiento"] = len(repr(ESTADO_REAL)) // 4
    contexto["escena_anterior"] = len(ESCENA_ANTERIOR) // 4
    contexto["fichas_y_setups"] = 900
    contexto["condensaciones"] = 400
    contexto["inmutable"] = 1200
    contexto["reserva_de_salida"] = 5000
    print("\ncontexto ensamblado: {0} tokens estimados".format(sum(contexto.values())))

    c = ciclo.ejecutar(con, "e2", contexto, escritor, juez, resumidor,
                       ESTADO_REAL, techo=100_000, trabajo="e5b")

    print("\n--- RESULTADO ---")
    print("fallo      :", c.fallo)
    print("veredicto  :", (c.veredicto or {}).get("veredicto"))
    print("consolidada:", c.consolidada)
    print("hallazgos  :", [(h.invariante, str(h.severidad))
                           for h in (c.generacion.hallazgos if c.generacion else [])])
    if c.resumen:
        print("resumen    :", str(c.resumen.get("texto"))[:160])

    print("\n--- REPARTO POR AGENTE (VER-34) ---")
    for t in c.trazas:
        m = getattr(t, "tokens_estimados", None)
        print("  {0:10} modelos={1}  tokens={2}".format(
            t.agente, getattr(t, "modelos", None) or "(sin registrar)",
            m if m is not None else "sin medir"))
    print("\ncoste_total:", json.dumps(ciclo.coste_total(c.trazas)))

    print("\n--- EL CACHE, QUE ES LA INCOGNITA ---")
    total = 0.0
    for t in c.trazas:
        m = getattr(t, "medidas", None) or {}
        total += m.get("coste_usd") or 0.0
        print("  {0:10} creados={1:>7}  leidos={2:>7}  coste={3}".format(
            t.agente, m.get("tokens_cache_creados"), m.get("tokens_cache_leidos"),
            m.get("coste_usd")))
    print("  {0:10} {1:.4f} USD".format("TOTAL", total))
    con.close()


if __name__ == "__main__":
    main()
