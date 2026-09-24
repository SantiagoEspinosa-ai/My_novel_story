"""Validadores deterministas de la personalizacion (`SPEC-26`).

    nombres_mal_escritos   INV-22  un nombre parecido que no es el de la bible
    claves_ausentes        INV-23  las palabras clave de un imprescindible
    repeticiones           INV-25  el nombre del destinatario, demasiadas veces
    frases_repetidas       INV-25  una frase larga en dos capitulos

Funciones puras: reciben texto y devuelven lo que encuentran. Que se hace con
ello lo deciden la puerta de la escena y el nivel obra.

EL PUNTO CIEGO DE `nombres_mal_escritos`, DECLARADO
----------------------------------------------------
Solo mira palabras con mayuscula a distancia de edicion 1 de un nombre conocido
(2 si el nombre tiene mas de 6 letras). Un diminutivo («Ire» por «Irene») o un
apodo quedan fuera, y es deliberado: a esa distancia ya no es una errata, puede
ser un recurso. Una errata en minuscula tampoco se ve.
"""

import re
from dataclasses import dataclass

from app.commons.politica.normalizar import palabras as palabras_normalizadas
from app.commons.politica.normalizar import sin_acentos
from app.commons.politica.vetadas import coincidencias

PALABRA = re.compile(r"\w+", re.UNICODE)

# `F-71` (a), decision del autor: palabras comunes que **nunca** son la errata de un nombre,
# aunque abran frase y el texto no las use en minuscula («Nadie» junto a «Nadia»). Es una
# lista cerrada y a la vista, y **su punto ciego es ella misma**: una errata real que
# coincida con una de estas palabras pasa. Se amplia a mano, no se deduce.
PALABRAS_COMUNES = frozenset("""
Nada Nadie Nunca Ninguno Ninguna Ningún Ni No Nos Nosotros Nosotras Nuestro Nuestra
Nuestros Nuestras Un Una Uno Unos Unas El La Las Los Lo Le Les Él Ella Ellas Ellos Eso Esa
Ese Esos Esas Esto Esta Este Estos Estas Era Eran Fue Fueron Es Son Hay Había Hace Y O Pero
Porque Pues Que Qué Quien Quién Cuando Cuándo Como Cómo Donde Dónde Luego Después Antes
Ahora Ahí Allí Aquí Así Ya Yo Tú Te Me Mi Mis Su Sus Se Si Sí Sin Con Para Por Tal Tan
Todo Toda Todos Todas Otro Otra Otros Otras Algo Alguien Mucho Mucha Poco Poca Casi Siempre
Tampoco También Entonces Mientras Hasta Desde Sobre Tras Bien Mal Más Menos Muy
""".split())


@dataclass(frozen=True)
class NombreMalEscrito:
    escrito: str
    correcto: str
    inicio: int


@dataclass(frozen=True)
class FraseRepetida:
    frase: str
    capitulos: tuple


def _distancia(a: str, b: str) -> int:
    """Levenshtein. Los nombres son cortos: la version cuadratica sobra."""
    previa = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        actual = [i]
        for j, cb in enumerate(b, 1):
            actual.append(min(previa[j] + 1, actual[j - 1] + 1,
                              previa[j - 1] + (ca != cb)))
        previa = actual
    return previa[-1]


def _tolerancia(nombre: str) -> int:
    return 2 if len(nombre) > 6 else 1


def nombres_mal_escritos(texto: str, nombres) -> list:
    """`INV-22`: palabras con mayuscula que casi son un nombre conocido.

    Se compara en minusculas pero **con acentos**: «Valdes» por «Valdés» es un
    nombre mal escrito, porque la regla dice «exactamente».
    """
    conocidas = sorted({parte for n in nombres for parte in n.split() if len(parte) >= 3})
    exactas = set(conocidas)
    # `F-71`: una palabra que el propio texto usa en minuscula es una palabra, no un
    # nombre: «Nada» a principio de frase no es una errata de «Nala». Punto ciego: una
    # errata que coincida con una palabra comun usada en minuscula en el texto pasa.
    en_minuscula = {m.group() for m in PALABRA.finditer(texto) if m.group().islower()}
    encontrados = []
    for m in PALABRA.finditer(texto):
        palabra = m.group()
        if not palabra[0].isupper() or palabra in exactas:
            continue
        if palabra.lower() in en_minuscula or palabra in PALABRAS_COMUNES:
            continue
        candidatas = [(_distancia(palabra.casefold(), c.casefold()), c) for c in conocidas]
        candidatas = [(d, c) for d, c in candidatas if 0 < d <= _tolerancia(c)
                      or (d == 0 and palabra != c)]
        if candidatas:
            encontrados.append(NombreMalEscrito(palabra, min(candidatas)[1], m.start()))
    return encontrados


def claves_ausentes(texto: str, imprescindibles) -> list:
    """`INV-23`: `(elemento, clave)` por cada palabra clave que no aparece.

    Con la normalizacion de las vetadas: plurales, genero y acentos no cuentan
    como ausencia.
    """
    ausentes = []
    for imp in imprescindibles:
        for clave in imp["palabras_clave"]:
            if not coincidencias(texto, [clave]):
                ausentes.append((imp["elemento"], clave))
    return ausentes


def repeticiones(texto: str, nombre: str, umbral: int):
    """`INV-25`: cuantas veces aparece el nombre de pila, si pasa del umbral.

    Devuelve `None` si no lo pasa. El umbral es provisional y no medido
    (`commons/config.py`).
    """
    pila = nombre.split()[0]
    veces = sum(1 for m in PALABRA.finditer(texto) if m.group() == pila)
    return veces if veces > umbral else None


def _secuencia(texto):
    return [r for _, _, r in palabras_normalizadas(texto)]


def frases_repetidas(textos: dict, longitud: int) -> list:
    """`INV-25`: frases de al menos `longitud` palabras que aparecen en mas de un
    capitulo. Las ventanas solapadas de una misma frase se funden en una.

    Lee el texto de la base, **no lo manda al modelo**: `CLAUDE.md` permite que
    una comprobacion determinista lea la obra entera.
    """
    secuencias = {cap: _secuencia(t) for cap, t in textos.items()}
    donde = {}
    for cap, sec in secuencias.items():
        for i in range(len(sec) - longitud + 1):
            donde.setdefault(tuple(sec[i:i + longitud]), set()).add(cap)
    repetidas = {v for v, caps in donde.items() if len(caps) > 1}
    frases = {}
    for cap, sec in secuencias.items():
        i = 0
        while i <= len(sec) - longitud:
            if tuple(sec[i:i + longitud]) not in repetidas:
                i += 1
                continue
            fin = i + longitud
            while fin <= len(sec) - 1 and tuple(sec[fin - longitud + 1:fin + 1]) in repetidas:
                fin += 1
            frase = " ".join(sec[i:fin])
            frases.setdefault(frase, set()).add(cap)
            i = fin
    return [FraseRepetida(f, tuple(sorted(c))) for f, c in sorted(frases.items())
            if len(c) > 1]
