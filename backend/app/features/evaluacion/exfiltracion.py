"""El rastro de una novela en otra (`SPEC-31` `RF-12`, `PLAN-31` E7).

Busca las claves de una novela —sus nombres y sus palabras clave— en los textos de otra,
con la misma normalizacion que las vetadas (`commons/politica/`): mayusculas, tildes,
plurales y genero, y un nombre propio tambien por su nombre de pila. Una clave que
aparece es un dato que cruzo de una novela a otra.

LO QUE NO VE
------------
Lo que no se parece a la clave: una parafrasis («el de la feria» por «Rodrigo») o un dato
que cruza sin nombre. Y solo mira lo que se le da: con dobles, los prompts; en una
ejecucion real, los textos guardados, porque el prompt enviado no se guarda (solo su
`prompt_hash`). Un rastro limpio sobre los textos no dice que el prompt fuera limpio.
"""

from dataclasses import dataclass

from app.commons.politica.vetadas import coincidencias, formas_de_nombre


@dataclass(frozen=True)
class Huella:
    clave: str
    texto: int
    """Indice del texto en la lista que se le dio."""
    fragmento: str


def _formas(clave):
    return formas_de_nombre(clave) if len(clave.split()) == 2 and clave[:1].isupper() \
        else [clave]


def rastro(textos, claves) -> list:
    huellas = []
    for i, texto in enumerate(textos):
        for clave in claves:
            for c in coincidencias(texto or "", _formas(clave)):
                huellas.append(Huella(clave, i, c.fragmento))
                break
    return huellas


def claves_de(brief) -> list:
    """Las declaradas en el brief, o, si no declara ninguna, los nombres de su ficha: el
    del destinatario, los de sus personas y mascotas, y el titulo."""
    if brief.claves_de_rastro:
        return list(brief.claves_de_rastro)
    f = brief.ficha
    if f is None:
        return []
    nombres = [f.destinatario.nombre] + [e.nombre for e in f.destinatario.elementos if e.nombre]
    return [n for n in nombres + [f.titulo] if n]
