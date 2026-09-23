"""Vuelca la novela a un fichero de texto, para leerla de principio a fin.

    python -X utf8 leer_obra.py                       # la obra del brief
    python -X utf8 leer_obra.py --base obra10.db      # otra base
    python -X utf8 leer_obra.py --obra cap-01         # una obra concreta
    python -X utf8 leer_obra.py --listar              # que obras hay

POR QUE ESTO EXISTE
--------------------
Despues de generar sesenta escenas, el texto vivia en la tabla `borrador` y
**no habia forma de leerlo seguido** sin abrir la base a mano: hacia falta
saber que escena va en que capitulo, en que orden, y cual de sus versiones se
acepto. Una novela que solo se puede leer con SQL no esta terminada.

`-X utf8` porque la consola de Windows no es UTF-8 por defecto y la novela
lleva acentos.
"""

import argparse
import os
import sqlite3
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.commons.configuracion import carga
from app.commons.db import procedencia
from app.features.manuscrito import exportar

AQUI = os.path.dirname(os.path.abspath(__file__))


def obras_de(con):
    """Que hay en esta base, con cuantas escenas y cuantas tienen texto."""
    filas = con.execute(
        "SELECT e.obra, COUNT(*), SUM(CASE WHEN b.escena IS NULL THEN 0 ELSE 1 END) "
        "FROM escena e LEFT JOIN (SELECT DISTINCT escena FROM borrador) b "
        "  ON b.escena = e.id GROUP BY e.obra ORDER BY e.obra")
    return [{"obra": f[0], "escenas": f[1], "con_texto": f[2] or 0} for f in filas]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--base", default=None, help="fichero .db (por defecto, el del sistema)")
    p.add_argument("--obra", default=None, help="identificador (por defecto, el del brief)")
    p.add_argument("--salida", default=None, help="fichero .md de salida")
    p.add_argument("--listar", action="store_true", help="solo di que obras hay")
    p.add_argument("--sin-titulos", action="store_true",
                   help="solo el texto, para comparar con `VER-60`")
    args = p.parse_args()

    sistema = carga.cargar_sistema()
    ruta = args.base or sistema.ruta_de_la_base
    if not os.path.isabs(ruta):
        ruta = os.path.join(AQUI, ruta)
    if not os.path.exists(ruta):
        print("no existe la base {0}".format(ruta))
        return 1
    con = sqlite3.connect("file:{0}?mode=ro".format(ruta), uri=True)

    if args.listar:
        print("obras en {0}:".format(ruta))
        for o in obras_de(con):
            print("  {0:20} {1} escena(s), {2} con texto".format(
                o["obra"], o["escenas"], o["con_texto"]))
        return 0

    obra = args.obra or carga.cargar_brief().obra_id
    salida = args.salida or os.path.join(AQUI, "{0}.md".format(obra))
    try:
        m = exportar.a_fichero(con, obra, salida,
                               con_titulos=not args.sin_titulos)
    except exportar.ObraSinTexto as e:
        print("no se pudo exportar:", e)
        print("\nlas obras que hay en esta base son:")
        for o in obras_de(con):
            print("  ", o["obra"])
        return 1

    print("{0}\n{1} capitulo(s), {2} escena(s), {3} palabras".format(
        m.titulo, m.capitulos, m.escenas, m.palabras))
    if m.sin_cabecera:
        print("AVISO: esta base no tiene fila en `obra`, asi que el titulo es "
              "el identificador y no el que se puso al darla de alta")
    if m.escenas_sin_texto:
        # Regla 8: el hueco se dice. Un manuscrito al que le falta una escena
        # **sin decirlo** se lee como una novela completa.
        print("AVISO: {0} escena(s) sin texto, marcadas en el fichero: {1}".format(
            len(m.escenas_sin_texto), ", ".join(m.escenas_sin_texto[:5])))
    pr = procedencia.leer(con)
    if pr["version"]:
        print("generada con codigo {0} | brief {1} | sistema {2}".format(
            pr["version"], pr["brief"], pr["sistema"]))
    print("\nescrito en:", salida)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
