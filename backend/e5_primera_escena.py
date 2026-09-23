"""E5 — La primera escena real, de principio a fin, medida.

No es una prueba: es una **ejecucion**. Gasta. Se deja en el repositorio
porque el paso E5 de `PLAN-01` dice que produce el primer dato que este
proyecto habra medido, y quien quiera repetirlo tiene que poder.

Usa el mismo bucle que se probo contra el doble en E2. Lo unico que cambia es
que el modelo es `SesionDelegada` en vez de `DobleDelModelo`.
"""

import json
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.modelo import proveedor
from app.features.contexto.bloques import BLOQUES
from app.features.escaleta import repository as repo
from app.features.orquestacion import bucle

RUTA = os.path.join(os.path.dirname(os.path.abspath(__file__)), "e5.db")

ESCENA = {
    "id": "e1", "orden": 1,
    "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
    "beats": ["b1"], "longitud_objetivo": [300, 900],
}

CONTEXTO_REAL = """PARAMETROS
genero: terror
punto de vista: tercera limitada sobre Marta
tiempo verbal: pasado
longitud objetivo: entre 300 y 900 palabras

LO QUE YA ES VERDAD EN LA FICCION
- Marta ha heredado la casa de su tia y ha llegado esta tarde.
- La casa lleva once anos vacia.
- El sotano esta cerrado con llave y la llave no aparece.
- Marta esta viva y esta en el salon.

LO QUE ESTA ESCENA TIENE QUE HACER
Marta oye algo en el sotano y baja a mirar. Al terminar la escena, Marta esta
menos segura que al empezarla: el cambio de valor es seguridad en negativo.
"""


def main():
    if os.path.exists(RUTA):
        os.remove(RUTA)
    con = sqlite3.connect(RUTA)
    repo.asegurar_tablas(con)
    repo.guardar_escaleta(con, "cap-1", [ESCENA])

    modelo = proveedor.SesionDelegada(agente="escritor")
    print("modelo declarado: {0}".format(modelo.nombre))

    # El contexto que mide el recortador es el real, no uno de juguete.
    contexto = {b.nombre: 0 for b in BLOQUES}
    contexto["estado_y_conocimiento"] = len(CONTEXTO_REAL) // 4

    r = bucle.generar(con, "e1", contexto, modelo, techo=100_000,
                      trabajo="e5-primera", mundo={
                          "entidades_vivas": {"marta": "vivo"},
                          "ubicaciones": {"marta": "salon"},
                          "accesos": {"salon": ["sotano"]},
                          "conocimiento": {},
                      })

    print("\n--- RESULTADO ---")
    print("fallo:", r.fallo)
    print("version:", r.version)
    print("hallazgos:", [(h.invariante, str(h.severidad)) for h in r.hallazgos])
    if r.version:
        fila = con.execute("SELECT texto FROM borrador WHERE escena='e1' AND version=?",
                           (r.version,)).fetchone()
        texto = fila[0]
        print("palabras:", len(texto.split()))
        print("primeras lineas:", texto[:220].replace("\n", " "))
    print("\n--- TRAZA ---")
    print("tokens_para_recortar:", r.traza.tokens_para_recortar)
    print("tokens_reservados:", r.traza.tokens_reservados)
    print("prompt_hash:", r.traza.prompt_hash)
    print("recortes:", [(x.bloque, x.clase) for x in r.traza.recortes])
    print("medidas:", json.dumps(getattr(r, "medidas", None), indent=2))
    con.close()


if __name__ == "__main__":
    main()
