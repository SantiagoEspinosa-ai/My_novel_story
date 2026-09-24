"""El libro como dato (`SPEC-27`, `PLAN-27` E4), antes de ningun PDF.

Portada, capitulos en orden de lectura con el texto de `exportar.capitulos_de` -tal
cual, `VER-60`-, y fichas de personaje y de lugar con los capitulos donde aparece
cada uno:

- un **personaje** aparece donde **participa** (`participa_en`): en las escenas que lo
  declaran presente. Nombrarlo en el texto no cuenta.
- un **lugar** aparece donde **ocurre** una escena (`ocurre_en`).

**Sin estados ni hallazgos** (`RF-06`): el libro es lo que se regala, y quien lo lee
no tiene nada que hacer con un `sin_veredicto`. Lo que no se guardo se dice: un nombre
que no esta usa el `id` y lo marca, y unos presentes sin declarar no son «nadie».

Como `exportar.py`, lee las tablas por SQL y no importa ninguna feature.
"""

import json
from dataclasses import dataclass, field

from app.features.manuscrito import exportar


class LibroIncompleto(Exception):
    """Una escena sin texto: una version publicada no puede tener un hueco."""


@dataclass
class CapituloDelLibro:
    numero: int
    id: str
    texto: str


@dataclass
class Ficha:
    id: str
    nombre: str
    nombre_es_el_id: bool
    # `None`: no se puede calcular (presentes sin declarar). Una lista vacia es que no
    # aparece en ningun capitulo.
    capitulos: list | None = None


@dataclass
class Libro:
    titulo: str
    dedicatoria: str | None
    capitulos: list = field(default_factory=list)
    personajes: list = field(default_factory=list)
    lugares: list = field(default_factory=list)
    presentes_sin_declarar: bool = False


def _titulo_y_dedicatoria(con, obra):
    fila = con.execute("SELECT titulo, dedicatoria FROM obra WHERE id = ?", (obra,)).fetchone()
    return (fila[0] or obra, fila[1]) if fila else (obra, None)


def _nombres(con, tabla, columna, prefijo):
    filas = con.execute("SELECT id, {0} FROM {1} WHERE id LIKE ? ORDER BY id".format(
        columna, tabla), (prefijo + "%",)).fetchall()
    return dict(filas)


def componer(con, obra) -> Libro:
    titulo, dedicatoria = _titulo_y_dedicatoria(con, obra)
    capitulos, numero_de = [], {}
    for cap in exportar.capitulos_de(con, obra):
        huecos = [e.id for e in cap.escenas if e.texto is None]
        if huecos:
            raise LibroIncompleto("sin texto: {0}".format(", ".join(huecos)))
        numero = len(capitulos) + 1
        numero_de[cap.id] = numero
        capitulos.append(CapituloDelLibro(numero, cap.id,
                                          "\n\n".join(e.texto for e in cap.escenas)))

    escenas = con.execute("SELECT capitulo, lugar, personajes_presentes FROM escena "
                          "WHERE obra = ?", (obra,)).fetchall()
    sin_declarar = any(p is None for _, _, p in escenas)
    participa, ocurre = {}, {}
    for capitulo, lugar, presentes in escenas:
        n = numero_de.get(capitulo)
        if n is None:
            continue
        for p in json.loads(presentes) if presentes else []:
            participa.setdefault(p, set()).add(n)
        if lugar:
            ocurre.setdefault(lugar, set()).add(n)

    prefijo = obra + "-"
    personajes = []
    for id_, nombre in _nombres(con, "entidad", "nombre_canonico", prefijo).items():
        capitulos_de = None if sin_declarar else sorted(participa.get(id_, ()))
        personajes.append(Ficha(id_, nombre or id_, nombre is None, capitulos_de))
    lugares = [Ficha(id_, nombre or id_, nombre is None, sorted(ocurre.get(id_, ())))
               for id_, nombre in _nombres(con, "lugar", "nombre", prefijo).items()]
    return Libro(titulo, dedicatoria, capitulos, personajes, lugares, sin_declarar)
