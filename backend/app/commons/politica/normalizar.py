"""Normalizar una palabra antes de compararla (`SPEC-25` `RF-17`).

QUE REDUCE Y QUE NO
-------------------
Mayusculas, acentos, plurales (`-s`, `-es`) y genero gramatical (`-o`/`-a`).
Nada mas: la spec pide **variantes simples**, y un lematizador de verdad es una
dependencia nueva para cazar conjugaciones que nadie ha pedido. «mato» no
coincide con «matar», y es sabido.

POR QUE SE PREFIERE COINCIDIR DE MAS
------------------------------------
Quitar el genero hace que «caso» y «casa» compartan raiz. Es un falso positivo
posible, y es el lado bueno del error: una coincidencia de mas devuelve un
capitulo al Escritor, que se ve y cuesta una reescritura; una de menos deja
pasar el nombre de una expareja a una novela de regalo, y no se ve nunca.
"""

import re
import unicodedata

PALABRA = re.compile(r"\w+", re.UNICODE)
VOCALES = "aeiou"


def sin_acentos(texto: str) -> str:
    """Quita las tildes **pero no la de la ñ**, que no es un acento sino otra
    letra. Quitarla convertia «coño» en «cono» y, al recortar el genero, en
    «con»: la vetada global prohibia la preposicion y ningun capitulo podia
    pasar `INV-21` (`F-59`)."""
    protegido = texto.replace("ñ", "\x00").replace("Ñ", "\x01")
    descompuesto = unicodedata.normalize("NFD", protegido)
    limpio = "".join(c for c in descompuesto if not unicodedata.combining(c))
    return limpio.replace("\x00", "ñ").replace("\x01", "Ñ")


def raiz(palabra: str) -> str:
    """La forma comparable de una palabra suelta.

    Las longitudes minimas evitan dejar en nada las palabras cortas: «es» no
    pierde su `-s` y «la» no pierde su `-a`.
    """
    p = sin_acentos(palabra).casefold()
    if len(p) > 4 and p.endswith("es") and p[-3] not in VOCALES:
        p = p[:-2]
    elif len(p) > 3 and p.endswith("s"):
        p = p[:-1]
    if len(p) > 3 and p[-1] in "oa":
        p = p[:-1]
    return p


def palabras(texto: str):
    """Las palabras del texto con su posicion en el original.

    Se normaliza palabra a palabra y no el texto entero porque quitar acentos
    cambia las longitudes: el fragmento que se devuelve tiene que ser el que se
    escribio, no uno desplazado.
    """
    return [(m.start(), m.end(), raiz(m.group())) for m in PALABRA.finditer(texto)]
