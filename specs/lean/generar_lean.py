"""Genera el fichero Lean de una obra a partir de la base de datos.

QUE HACE
--------
Lee tres cosas de SQLite -`evento_cronologico`, `participacion_en_evento` y la
columna `entidad.fecha_de_nacimiento`- y escribe `Cronologia/Generado.lean`,
que contiene un unico `def obraReal : Obra` con la misma forma que el fixture
escrito a mano. A partir de ahi, `lake exe verificar` comprueba las cuatro
invariantes sobre datos reales.

POR QUE LEE SQL DIRECTAMENTE Y NO USA `features/cronologia/consultas.py`
------------------------------------------------------------------------
Porque esto no es backend: es una herramienta del harness que vive fuera de
`backend/`, y llamar a una feature desde aqui seria el acoplamiento que `A-02`
prohibe -y que `F-28` demostro que el comprobador de importaciones no siempre
ve-. La consulta es de tres tablas y cabe en pantalla; el precio de duplicarla
es menor que el de atar la verificacion formal a la estructura interna del
backend.

**El riesgo de esa decision, dicho en voz alta:** si la semantica de
`consultas.py` cambia -que cuenta como presente, como se solapan dos
intervalos- este fichero no se entera. Lo que lo protege es que Lean y Python
comprueban lo mismo por caminos distintos, asi que una divergencia aparece
como un desacuerdo entre los dos, no como un silencio.

POR QUE EL TIEMPO SE CONVIERTE AQUI Y NO EN LEAN
-------------------------------------------------
Un calendario de verdad necesita saber cuantos dias tiene febrero. Python lo
sabe -`datetime`- y Lean, sin Mathlib, no. Asi que aqui se calcula
`inicioMin`, los minutos desde una epoca, y Lean solo suma duraciones sobre un
numero. Comparar fechas si lo hace Lean, porque para eso basta el orden
lexicografico y no hace falta calendario.
"""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from datetime import datetime

# Epoca arbitraria. Solo importa que sea la misma para todos los eventos: los
# minutos se usan para restar y sumar duraciones, nunca para decir una fecha.
EPOCA = datetime(1900, 1, 1)


def _instante(texto):
    """La fecha como objeto, o `None` si no se deja leer. Nunca revienta.

    Misma politica que `cronologia/consultas.py`: una fecha ilegible no es una
    excepcion, es un evento que no se puede comprobar y que hay que contar
    aparte.
    """
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def _minutos(t: datetime) -> int:
    return int((t - EPOCA).total_seconds() // 60)


def _fecha_lean(t: datetime) -> str:
    return ("{{ anio := {0}, mes := {1}, dia := {2}, hora := {3}, minuto := {4} }}"
            .format(t.year, t.month, t.day, t.hour, t.minute))


def _txt(valor) -> str:
    """Un literal de cadena Lean, con las comillas escapadas."""
    return '"' + str(valor or "").replace("\\", "\\\\").replace('"', '\\"') + '"'


def leer(con: sqlite3.Connection, obra: str) -> dict:
    con.row_factory = sqlite3.Row
    eventos = [dict(f) for f in con.execute(
        "SELECT id, t_fabula, duracion_min, lugar, escena, capitulo "
        "FROM evento_cronologico WHERE obra = ? ORDER BY capitulo, id", (obra,))]

    participaciones = {}
    for e in eventos:
        participaciones[e["id"]] = [dict(f) for f in con.execute(
            "SELECT personaje, presencia FROM participacion_en_evento "
            "WHERE evento = ? ORDER BY personaje", (e["id"],))]

    # `entidad` es de otra feature, asi que se lee lo minimo y se pasa como
    # dato, igual que hace `consultas.edades`.
    nacimientos = {}
    for fila in con.execute("SELECT id, fecha_de_nacimiento FROM entidad"):
        nacimientos[fila["id"]] = fila["fecha_de_nacimiento"]

    # `delta_de_escena` guarda el delta entero como JSON, por escena y version
    # (`SPEC-01` 3.2.2). De ahi salen las exclusiones: ver `exclusiones_de`.
    deltas = {}
    for fila in con.execute(
            "SELECT escena, contenido FROM delta_de_escena ORDER BY orden"):
        deltas.setdefault(fila["escena"], []).append(fila["contenido"])

    return {"eventos": eventos, "participaciones": participaciones,
            "nacimientos": nacimientos, "deltas": deltas}


# Solo `muerto` saca a un personaje de la ficcion. `desaparecido` **no**, y la
# diferencia es del dominio, no un descuido: `Docs/definitions.md` dice que en
# terror "no se sabe si sigue vivo" es material narrativo, y un desaparecido
# puede volver. Tratarlo como exclusion convertiria el recurso mas comun del
# genero en una violacion.
ESTADOS_QUE_EXCLUYEN = ("muerto",)


def exclusiones_de(contenidos):
    """A quien sacan de la ficcion los deltas de una escena.

    Cada delta trae `cambios_de_estado_vital` con la forma
    `{"personaje": ..., "de": ..., "a": ...}` (ver `generacion/prompt.py`).
    Un delta ilegible no revienta y no se cuenta como "nadie muere": se
    devuelve aparte para que el informe lo diga.
    """
    fuera, ilegibles = [], 0
    for contenido in contenidos:
        try:
            delta = json.loads(contenido)
        except (TypeError, ValueError):
            ilegibles += 1
            continue
        for cambio in (delta or {}).get("cambios_de_estado_vital", []) or []:
            if cambio.get("a") in ESTADOS_QUE_EXCLUYEN and cambio.get("personaje"):
                fuera.append(cambio["personaje"])
    return sorted(set(fuera)), ilegibles


def generar(datos: dict, obra: str) -> tuple[str, dict]:
    """Devuelve el texto del fichero Lean y un informe de cobertura.

    El informe no es decoracion: dice cuantos eventos se han podido convertir
    y cuantos no, y **cuantos personajes se quedan sin comprobar la edad**. Un
    fichero Lean que pasa habiendo dejado fuera la mitad de los eventos no
    significa que la obra sea coherente.
    """
    eventos, sin_fecha_legible, personajes = [], [], {}
    eventos_con_exclusion, deltas_ilegibles = 0, 0

    # El orden de discurso es el mismo criterio que usa `consultas.orden_temporal`:
    # por capitulo y luego por identificador de evento. Se guarda como rango y no
    # como el `orden` de la escena porque no todos los eventos tienen escena.
    for discurso, e in enumerate(datos["eventos"], start=1):
        t = _instante(e["t_fabula"])
        if t is None:
            sin_fecha_legible.append(e["id"])
            continue

        fuera, ilegibles = exclusiones_de(datos["deltas"].get(e["escena"], []))
        deltas_ilegibles += ilegibles
        if fuera:
            eventos_con_exclusion += 1

        presentes = datos["participaciones"].get(e["id"], [])
        for p in presentes:
            personajes.setdefault(p["personaje"], datos["nacimientos"].get(p["personaje"]))

        partes = ", ".join(
            "{{ personaje := {0}, presencia := Presencia.{1} }}".format(
                _txt(p["personaje"]),
                "presente" if p["presencia"] == "presente" else "mencionado")
            for p in presentes)

        eventos.append(
            "    {{ id := {id}, tFabula := {fecha}, inicioMin := {min}, "
            "duracionMin := {dur}, lugar := {lugar}, tDiscurso := {disc}, "
            "capitulo := {cap}, analepsis := false, excluye := [{excluye}], "
            "participan := [{partes}] }}".format(
                id=_txt(e["id"]), fecha=_fecha_lean(t), min=_minutos(t),
                dur=int(e["duracion_min"] or 0), lugar=_txt(e["lugar"]),
                disc=discurso, cap=_txt(e["capitulo"]),
                excluye=", ".join(_txt(x) for x in fuera), partes=partes))

    sin_nacimiento = sorted(p for p, n in personajes.items() if not _instante(n))
    filas_personaje = []
    for pid in sorted(personajes):
        nac = _instante(personajes[pid])
        filas_personaje.append(
            "    {{ id := {0}, nacimiento := {1} }}".format(
                _txt(pid),
                "some " + _fecha_lean(nac) if nac else "none"))

    texto = CABECERA.format(
        obra=obra,
        n_eventos=len(eventos),
        n_personajes=len(personajes),
        n_sin_nacimiento=len(sin_nacimiento),
        n_sin_fecha=len(sin_fecha_legible),
        personajes=",\n".join(filas_personaje) or "",
        eventos=",\n".join(eventos) or "",
        obra_txt=_txt(obra))

    return texto, {
        "eventos_convertidos": len(eventos),
        "eventos_sin_fecha_legible": sin_fecha_legible,
        "personajes": len(personajes),
        "personajes_sin_fecha_de_nacimiento": sin_nacimiento,
        # Ya no es siempre cero: sale de `cambios_de_estado_vital` del delta
        # persistido. Si vale 0 en una obra donde alguien muere, el fallo esta
        # aqui o en el delta, no en la invariante (`F-46`).
        "eventos_con_exclusion": eventos_con_exclusion,
        "deltas_ilegibles": deltas_ilegibles,
    }


CABECERA = '''/-
  FICHERO GENERADO. No editar a mano: lo reescribe `generar_lean.py`.

  Obra: {obra}
  Eventos convertidos: {n_eventos}
  Personajes: {n_personajes} (sin fecha de nacimiento: {n_sin_nacimiento})
  Eventos descartados por fecha ilegible: {n_sin_fecha}

  `excluye` va vacia en todos los eventos, y no porque nadie muera: porque no
  hay de donde sacarlo. `entidad` guarda el estado vital **actual** y no en que
  evento cambio (`F-46`). Mientras siga asi, `L-4` no puede disparar sobre
  datos reales y un cero suyo no significa nada.
-/
import Cronologia.Basic

namespace Cronologia

def obraReal : Obra :=
  {{ id := {obra_txt}
  , personajes :=
  [
{personajes}
  ]
  , eventos :=
  [
{eventos}
  ]
  }}

end Cronologia
'''


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("base", help="ruta de la base SQLite")
    ap.add_argument("obra", help="identificador de la obra")
    ap.add_argument("--salida", default="Cronologia/Generado.lean")
    args = ap.parse_args(argv)

    con = sqlite3.connect(args.base)
    try:
        datos = leer(con, args.obra)
    finally:
        con.close()

    texto, informe = generar(datos, args.obra)
    with open(args.salida, "w", encoding="utf-8") as f:
        f.write(texto)

    print("escrito {0}".format(args.salida))
    for clave, valor in informe.items():
        print("  {0}: {1}".format(clave, valor))
    if informe["eventos_convertidos"] == 0:
        print("AVISO: cero eventos. Lean pasara sin haber comprobado nada.")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
