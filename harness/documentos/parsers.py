"""Lectores de las tablas de `Docs/`.

Los validadores de `harness/documentos/` comparan documentos entre sí, así que lo
primero que necesitan es leer tablas de markdown sin adivinar. Todo lo que hay
aquí son funciones puras sobre texto: no abren ficheros ni saben dónde viven los
documentos. Eso lo pone `conftest.py`.

Por qué funciones puras y no lectores de ficheros: el caso negativo de cada
validador necesita alimentarlo con un documento roto a propósito. Si el parser
leyera del disco, cada caso negativo tendría que escribir un fichero temporal.
Así basta con pasarle una cadena.

**Si un parser no encuentra lo que busca, revienta con un mensaje concreto en vez
de devolver vacío.** Un parser que devuelve un conjunto vacío cuando el documento
cambió de forma convierte el validador en un test que siempre pasa, que es
exactamente lo que no queremos.
"""

from __future__ import annotations

import re
from dataclasses import dataclass


class DocumentoIlegible(Exception):
    """El documento no tiene la forma que el parser espera.

    Es un fallo del validador o del documento, nunca un resultado. Se distingue
    de "el validador encontró una incoherencia", que es un `assert` fallido.
    """


@dataclass(frozen=True)
class Invariante:
    """Una fila de la tabla "Invariantes verificables" de `Docs/definitions.md`."""

    id: str
    enunciado: str
    nivel: str
    severidad: str
    tipo: str


def limpiar(celda: str) -> str:
    """Deja el contenido literal de una celda de tabla markdown.

    Quita los acentos graves del código, las negritas y el escape `\\_` que
    markdown necesita para los guiones bajos dentro de tablas. Sin esto,
    `juez\\_llm` no se compara nunca igual que `juez_llm`.
    """
    return celda.replace("\\_", "_").replace("`", "").replace("**", "").strip()


def celdas(linea: str) -> list[str]:
    """Parte una fila de tabla markdown en sus celdas, sin los bordes."""
    return [c.strip() for c in linea.strip().strip("|").split("|")]


def invariantes(texto_definitions: str) -> dict[str, Invariante]:
    """Las dieciséis invariantes con su nivel, severidad y tipo.

    Fuente: la tabla "Invariantes verificables" de `Docs/definitions.md`, que es
    normativa. Todo lo demás se compara contra esto.
    """
    encontradas: dict[str, Invariante] = {}
    for linea in texto_definitions.splitlines():
        if not re.match(r"^\|\s*INV-\d{2}\s*\|", linea):
            continue
        partes = celdas(linea)
        if len(partes) != 5:
            raise DocumentoIlegible(
                f"La fila de invariante tiene {len(partes)} celdas y esperaba 5: {linea!r}"
            )
        ident, enunciado, nivel, severidad, tipo = (limpiar(p) for p in partes)
        encontradas[ident] = Invariante(ident, enunciado, nivel, severidad, tipo)

    if not encontradas:
        raise DocumentoIlegible(
            "No encontré ninguna fila `| INV-xx |` en definitions.md. "
            "O cambió el formato de la tabla o el documento no es el que creo."
        )
    return encontradas


def _ids_inv(fragmento: str) -> set[str]:
    """Todos los `INV-xx` que aparecen en un trozo de texto."""
    return set(re.findall(r"INV-\d{2}", fragmento))


def invariantes_por_agente(texto_architecture: str) -> dict[str, set[str]]:
    """Qué invariantes declara ejecutar cada agente.

    Fuente: la última columna de la tabla "Agentes del pipeline" de
    `Docs/architecture.md`.
    """
    por_agente: dict[str, set[str]] = {}
    for linea in texto_architecture.splitlines():
        if not re.match(r"^\|\s*\*\*[A-ZÁÉÍÓÚ]", linea):
            continue
        partes = celdas(linea)
        if len(partes) != 5:
            continue
        agente = limpiar(partes[0])
        por_agente[agente] = _ids_inv(partes[4])

    if not por_agente:
        raise DocumentoIlegible(
            "No encontré la tabla de agentes en architecture.md."
        )
    return por_agente


def niveles_del_auditor(texto_architecture: str) -> dict[str, set[str]]:
    """Qué invariantes declara el Auditor de obra como de obra y como de capítulo.

    Es el único sitio de `architecture.md` donde el nivel de una invariante se
    declara explícitamente, así que es lo único que se puede contrastar contra
    `definitions.md`.
    """
    for linea in texto_architecture.splitlines():
        if "Auditor de obra" not in linea:
            continue
        ultima = celdas(linea)[-1]
        m = re.search(r"Obra:(?P<obra>.*?)Cap[ií]tulo:(?P<capitulo>.*)", ultima, re.S)
        if not m:
            raise DocumentoIlegible(
                "La fila del Auditor de obra no declara 'Obra: … Capítulo: …'. "
                f"Celda leída: {ultima!r}"
            )
        return {
            "obra": _ids_inv(m.group("obra")),
            "capitulo": _ids_inv(m.group("capitulo")),
        }
    raise DocumentoIlegible("No encontré la fila del Auditor de obra en architecture.md.")


def niveles_de_la_skill(texto_skill: str) -> dict[str, set[str]]:
    """Lo mismo, leído de la skill `harness-invariantes`.

    Es la tercera fuente: si las tres no coinciden, alguien copió una lista y no
    la actualizó.
    """
    m = re.search(
        r"De \*\*obra\*\*:(?P<obra>.*?)De \*\*cap[ií]tulo\*\*:(?P<capitulo>.*?)\.",
        texto_skill,
        re.S,
    )
    if not m:
        raise DocumentoIlegible(
            "La skill harness-invariantes no declara 'De **obra**: … De **capítulo**: …'."
        )
    return {
        "obra": _ids_inv(m.group("obra")),
        "capitulo": _ids_inv(m.group("capitulo")),
    }


def recuento_de_tipos_de_la_skill(texto_skill: str) -> dict[str, int]:
    """El recuento que la skill afirma en prosa: 'doce son de regla, cuatro son de juez'.

    Se lee en letra porque así está escrito. Es el único dato de tipo que la
    skill da, y aun siendo un recuento sirve: si `definitions.md` reclasifica una
    invariante y nadie toca la skill, los números dejan de cuadrar.
    """
    palabras = {
        "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5, "seis": 6,
        "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11, "doce": 12,
        "trece": 13, "catorce": 14, "quince": 15, "dieciséis": 16,
    }
    m = re.search(
        r"(?P<regla>\w+) son de regla,\s*(?P<juez>\w+) son de juez", texto_skill
    )
    if not m:
        raise DocumentoIlegible(
            "La skill harness-invariantes no dice 'N son de regla, M son de juez'."
        )
    try:
        return {
            "regla": palabras[m.group("regla").lower()],
            "juez_llm": palabras[m.group("juez").lower()],
        }
    except KeyError as exc:
        raise DocumentoIlegible(f"No sé convertir a número: {exc}") from exc


def transiciones(texto_architecture: str) -> list[tuple[str, str]]:
    """Las transiciones de la máquina de estados de la escena.

    Fuente: la tabla "La máquina de estados y quién dispara cada transición" de
    `Docs/architecture.md`, cuya primera celda tiene la forma `origen` → `destino`.
    """
    encontradas: list[tuple[str, str]] = []
    for linea in texto_architecture.splitlines():
        m = re.match(r"^\|\s*`(?P<origen>\w+)`\s*→\s*`(?P<destino>\w+)`\s*\|", linea)
        if m:
            encontradas.append((m.group("origen"), m.group("destino")))

    if not encontradas:
        raise DocumentoIlegible(
            "No encontré ninguna transición `origen` → `destino` en architecture.md."
        )
    return encontradas


def valores_de_enumeracion(texto_definitions: str, nombre: str) -> set[str]:
    """Los valores de una enumeración de la tabla "Vocabularios controlados"."""
    for linea in texto_definitions.splitlines():
        if not linea.startswith(f"| `{nombre}`"):
            continue
        return {limpiar(v) for v in celdas(linea)[2].split(",")}
    raise DocumentoIlegible(
        f"No encontré la enumeración `{nombre}` en la tabla de vocabularios."
    )


def identificadores(texto: str, prefijo: str) -> set[str]:
    """Todos los identificadores publicados de una familia (`INV`, `VER`, `A`…)."""
    return set(re.findall(rf"\b{prefijo}-\d+\b", texto))


def camino_evitando(
    aristas: list[tuple[str, str]], origen: str, destino: str, prohibido: str
) -> list[str] | None:
    """Busca un camino de `origen` a `destino` que no pase por `prohibido`.

    Devuelve el camino si existe, o `None`. Es una exploración en anchura
    deliberadamente ingenua: son siete estados y lo que importa es que se lea de
    un vistazo, no que sea rápida.
    """
    salientes: dict[str, list[str]] = {}
    for a, b in aristas:
        salientes.setdefault(a, []).append(b)

    pendientes: list[list[str]] = [[origen]]
    vistos = {origen}
    while pendientes:
        camino = pendientes.pop(0)
        if camino[-1] == destino:
            return camino
        for siguiente in salientes.get(camino[-1], []):
            if siguiente == prohibido or siguiente in vistos:
                continue
            vistos.add(siguiente)
            pendientes.append(camino + [siguiente])
    return None
