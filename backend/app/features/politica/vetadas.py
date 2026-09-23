"""Buscar palabras vetadas en un texto (`INV-21`).

Una funcion pura: recibe el texto y las formas vetadas y devuelve las
coincidencias. De donde salen las formas (los tres niveles) lo decide
`repository.py`; que se hace con una coincidencia, la puerta.
"""

from dataclasses import dataclass

from app.features.politica.normalizar import palabras


@dataclass(frozen=True)
class Coincidencia:
    vetada: str
    """La forma vetada tal como esta en la lista."""
    fragmento: str
    """Lo que se escribio en el texto: es lo que lee el Escritor al reescribir."""
    inicio: int


def coincidencias(texto: str, vetadas) -> list:
    """Todas las apariciones de cada forma vetada, comparando palabras enteras.

    Una expresion de varias palabras coincide solo con esas palabras seguidas.
    Los saltos de linea y la puntuacion no cuentan como palabras, asi que una
    expresion partida entre dos lineas coincide igual.
    """
    del_texto = palabras(texto)
    raices = [r for _, _, r in del_texto]
    encontradas = []
    for vetada in vetadas:
        buscada = [r for _, _, r in palabras(vetada)]
        if not buscada:
            continue
        n = len(buscada)
        for i in range(len(raices) - n + 1):
            if raices[i:i + n] == buscada:
                inicio, fin = del_texto[i][0], del_texto[i + n - 1][1]
                encontradas.append(Coincidencia(vetada, texto[inicio:fin], inicio))
    return sorted(encontradas, key=lambda c: c.inicio)


def formas_de_nombre(nombre: str) -> list:
    """`RF-15`: un nombre propio se veta completo y por su nombre de pila."""
    partes = nombre.split()
    if len(partes) < 2:
        return [nombre]
    return [nombre, partes[0]]
