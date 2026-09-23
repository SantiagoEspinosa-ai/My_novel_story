"""Corre la verificacion formal sobre una obra real y la contrasta con la puerta.

QUE HACE, EN UN COMANDO
-----------------------
    python comparar_con_la_puerta.py <base.db> <id-de-obra>

    1. Genera `Cronologia/Generado.lean` desde SQLite.
    2. Compila y ejecuta `verificar-real`: las cuatro invariantes.
    3. Calcula lo que veria la **puerta de capitulo** (`INV-08`) capitulo a
       capitulo, imitando `orquestacion.inversiones_del_capitulo`.
    4. Compara los dos conjuntos y dice si coinciden **exactamente**.

Existe para no perder tiempo cuando llegue la base de la repeticion, y para
que la comparacion se haga siempre igual en vez de a mano y distinta cada vez.

POR QUE LA COMPARACION ES UNA IGUALDAD EXACTA Y NO UN PARECIDO
---------------------------------------------------------------
Tras `0d7bd8b` la puerta y Lean **no miran el mismo conjunto**: la puerta mira
las escenas de **un capitulo** y Lean **todos los pares de la obra**. Eso es
alcance, no discrepancia, y se resuelve agregando los diez capitulos.

Pero la agregacion no es una union cualquiera. Una inversion que cruza dos
capitulos **se imputa una sola vez, al posterior** —que es ademas el capitulo
que Lean nombra al describir el par—, asi que agregar todos los capitulos debe
dar **exactamente** el conjunto de `L-1`:

    un par que salga dos veces al agregar   -> discrepancia real
    un par que Lean vea y ninguna puerta    -> discrepancia real

Eso es lo que convierte la redundancia en una segunda fuente util: **dos
conjuntos parecidos no verifican nada; dos conjuntos que deben coincidir, si.**

UN CASO QUE NO ES DISCREPANCIA Y HAY QUE SABER DISTINGUIR
----------------------------------------------------------
Una inversion cuyo evento posterior no tiene capitulo (`capitulo IS NULL`) **no
la reclama ningun capitulo**, asi que desaparece de la agregacion aunque Lean
la vea. No es que la puerta se equivoque: es que no hay puerta que la mire.
Se informa aparte, porque contarla como discrepancia culparia al inocente y
callarla escondera un hueco real.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import re
import sqlite3
import subprocess
import sys

AQUI = pathlib.Path(__file__).resolve().parent
RAIZ = AQUI.parents[1]          # .../My_novel_story-verificacion
BACKEND = RAIZ / "backend"


def _lean_env():
    """El entorno y la ruta de `lake`.

    Devuelve `(entorno, ruta_de_lake)`, y **no basta con poner elan en el PATH
    del hijo**: en Windows `CreateProcess` resuelve el nombre del ejecutable
    con el PATH del proceso ACTUAL, no con el que se le pasa al hijo, asi que
    `lake` daria "no se encuentra el archivo" aunque el entorno lo incluya.
    Por eso se invoca con su ruta completa.
    """
    elan = os.environ.get("ELAN_HOME")
    if not elan:
        raise SystemExit(
            "Falta ELAN_HOME: apuntalo a la instalacion de elan antes de correr esto.")
    bin_elan = pathlib.Path(elan) / "bin"
    entorno = dict(os.environ)
    entorno["PATH"] = str(bin_elan) + os.pathsep + entorno["PATH"]
    lake = bin_elan / ("lake.exe" if os.name == "nt" else "lake")
    if not lake.exists():
        raise SystemExit("No encuentro %s" % lake)
    return entorno, str(lake)


def correr_lean(base: str, obra: str):
    """Genera, compila y ejecuta. Devuelve (codigo, salida, pares, cobertura)."""
    subprocess.run([sys.executable, str(AQUI / "generar_lean.py"), base, obra],
                   cwd=AQUI, check=False)
    entorno, lake = _lean_env()
    subprocess.run([lake, "build"], cwd=AQUI, env=entorno, check=True,
                   stdout=subprocess.DEVNULL)
    r = subprocess.run([lake, "exe", "verificar-real"], cwd=AQUI, env=entorno,
                       capture_output=True, text=True)
    pares = set()
    cobertura = {}
    for linea in r.stdout.splitlines():
        if linea.startswith("#PAR L-1 "):
            _, _, antes, despues = linea.split(None, 3)
            pares.add((antes, despues.strip()))
        elif linea.startswith("#COBERTURA "):
            for trozo in linea.split()[1:]:
                clave, _, valor = trozo.partition("=")
                cobertura[clave] = valor
    return r.returncode, r.stdout, pares, cobertura


def lo_que_ve_la_puerta(base: str, obra: str):
    """Las inversiones agregadas capitulo a capitulo, como las ve `INV-08`.

    Imita `orquestacion.inversiones_del_capitulo`: cada inversion se le imputa
    al capitulo de su evento **posterior**. Se importa el backend en vez de
    reimplementar la consulta, porque comparar contra una copia mia de su
    logica no compararia nada.
    """
    sys.path.insert(0, str(BACKEND))
    from app.features.cronologia import consultas          # noqa: E402
    from app.features.orquestacion import obra as modulo_obra  # noqa: E402

    con = sqlite3.connect("file:%s?mode=ro" % base, uri=True)
    con.row_factory = sqlite3.Row
    try:
        temporal = consultas.orden_temporal(con, obra)
        eventos = consultas.repo.eventos_de(con, obra)
        capitulo_de = {e["id"]: e.get("capitulo") for e in eventos}
        capitulos = sorted({c for c in capitulo_de.values() if c})

        por_capitulo, agregado, repetidos = {}, set(), []
        for capitulo in capitulos:
            filtrado = modulo_obra.inversiones_del_capitulo(
                temporal, capitulo_de, capitulo)
            pares = {tuple(p) for p in filtrado.get("inversiones") or []}
            por_capitulo[capitulo] = pares
            for par in pares:
                if par in agregado:
                    repetidos.append(par)
                agregado.add(par)

        huerfanas = {tuple(p) for p in temporal.get("inversiones") or []
                     if not capitulo_de.get(p[1])}
        return {"por_capitulo": por_capitulo, "agregado": agregado,
                "repetidos": repetidos, "huerfanas": huerfanas,
                "sin_fecha_legible": temporal.get("sin_fecha_legible") or [],
                "capitulos": capitulos}
    finally:
        con.close()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base")
    ap.add_argument("obra")
    args = ap.parse_args(argv)

    print("=" * 72)
    print("1. VERIFICACION FORMAL")
    print("=" * 72)
    codigo, salida, pares_lean, cobertura = correr_lean(args.base, args.obra)
    print(salida)

    print("=" * 72)
    print("2. LO QUE VE LA PUERTA, CAPITULO A CAPITULO")
    print("=" * 72)
    puerta = lo_que_ve_la_puerta(args.base, args.obra)
    for capitulo in puerta["capitulos"]:
        pares = puerta["por_capitulo"][capitulo]
        print("  %-10s %s" % (capitulo, sorted(pares) if pares else "sin inversiones"))
    if puerta["sin_fecha_legible"]:
        print("  sin t_fabula legible: %s" % puerta["sin_fecha_legible"][:5])

    print("=" * 72)
    print("3. IGUALDAD EXACTA")
    print("=" * 72)
    agregado = puerta["agregado"]
    solo_lean = sorted(pares_lean - agregado)
    solo_puerta = sorted(agregado - pares_lean)

    print("  L-1 (obra entera):      %d par(es)" % len(pares_lean))
    print("  puerta (agregando):     %d par(es)" % len(agregado))

    # Lo que no es discrepancia y hay que descontar antes de juzgar.
    if puerta["huerfanas"]:
        print("  inversiones sin capitulo que las reclame: %s"
              % sorted(puerta["huerfanas"]))
        print("    -> no es discrepancia: no hay puerta que las mire. `G-01`.")
        solo_lean = [p for p in solo_lean if p not in puerta["huerfanas"]]

    problemas = []
    if puerta["repetidos"]:
        problemas.append("pares imputados a mas de un capitulo: %s"
                         % sorted(set(puerta["repetidos"])))
    if solo_lean:
        problemas.append("L-1 los ve y ninguna puerta los levanta: %s" % solo_lean)
    if solo_puerta:
        problemas.append("la puerta los levanta y L-1 no: %s" % solo_puerta)

    if cobertura.get("eventos") == "0":
        print("\n  SIN COMPARACION: cero eventos convertidos. No hay nada que")
        print("  contrastar, y eso no es lo mismo que coincidir.")
        return 2
    if problemas:
        print("\n  DISCREPANCIA REAL, no de alcance:")
        for p in problemas:
            print("    - %s" % p)
        print("\n  Uno de los dos esta mal y hay que averiguar cual.")
        return 1
    print("\n  COINCIDEN EXACTAMENTE. La redundancia es real: dos caminos")
    print("  independientes sobre el mismo conjunto, sin huecos ni duplicados.")
    print("\n  (verificar-real devolvio %d)" % codigo)
    return 0


if __name__ == "__main__":
    sys.exit(main())
