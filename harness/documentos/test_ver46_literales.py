"""VER-46 — Los literales de enumeración citados son los de la tabla.

La segunda clase de defecto con historial real: el diagrama de ciclo de vida de
`Docs/domain-knowledge.md` escribía los estados en `PascalCase` —`EnVerificacion`,
`EnRevision`— donde la enumeración `estado_de_escena` dice `en_verificacion` y
`en_revision`. `definitions.md` advierte del riesgo en prosa —*"los literales se
copian de esta tabla, nunca del diagrama"*— y ningún validador lo comprobaba.

**Cómo detecta una variante sin dar falsos positivos.** Normaliza el token
—minúsculas, sin tildes, sin guiones bajos— y lo compara con los valores de la
tabla normalizados igual. Si dos normalizan igual pero se escriben distinto, es
una variante del mismo literal: `EnVerificacion` y `en_verificacion` normalizan
los dos a `enverificacion`.

Para no marcar prosa, solo se miran tokens **con forma de identificador**: los
que llevan guion bajo, los que tienen una mayúscula interna, o los que van entre
acentos graves. Así `Obra` al principio de una frase no se confunde con el valor
`obra` de `nivel_de_evaluacion`.
"""

from __future__ import annotations

import pathlib
import re
import unicodedata

import pytest

from harness.documentos import parsers
from harness.documentos.test_ver45_rutas import documentos_del_proyecto

# Enumeraciones cuyos valores son palabras sueltas y comunes en prosa
# (`obra`, `escena`, `regla`, `humano`, `vivo`…). Comprobarlas produciría ruido
# sin señal: se declaran fuera de alcance y consta como punto ciego.
DEMASIADO_COMUNES = {"nivel_de_evaluacion", "severidad", "tipo_de_verificador"}


def normalizar(token: str) -> str:
    """Minúsculas, sin tildes y sin separadores."""
    sin_tildes = "".join(
        c
        for c in unicodedata.normalize("NFD", token)
        if unicodedata.category(c) != "Mn"
    )
    return sin_tildes.lower().replace("_", "").replace("-", "")


def literales_canonicos(texto_definitions: str) -> dict[str, set[str]]:
    """De forma normalizada a las escrituras legítimas de la tabla."""
    canonicos: dict[str, set[str]] = {}
    for linea in texto_definitions.splitlines():
        m = re.match(r"^\|\s*`(?P<enum>\w+)`\s*\|(?P<resto>.*)", linea)
        if not m or m.group("enum") in DEMASIADO_COMUNES:
            continue
        celdas = parsers.celdas(m.group("resto"))
        if len(celdas) < 2:
            continue
        for valor in celdas[-1].split(","):
            limpio = parsers.limpiar(valor)
            if limpio:
                canonicos.setdefault(normalizar(limpio), set()).add(limpio)

    if not canonicos:
        raise parsers.DocumentoIlegible(
            "No pude leer ningún valor de la tabla de vocabularios controlados."
        )
    return canonicos


def _con_forma_de_identificador(token: str) -> bool:
    """Lleva guion bajo, o tiene una mayúscula que no es la primera."""
    return "_" in token or bool(re.search(r"[a-z][A-Z]", token))


def variantes(texto: str, canonicos: dict[str, set[str]]) -> set[tuple[str, str]]:
    """Pares (escrito, esperado) de literales escritos de otra forma."""
    candidatos = set(re.findall(r"[A-Za-zÁÉÍÓÚÜÑáéíóúüñ][\wÀ-ſ]*", texto))
    candidatos |= {
        parsers.limpiar(t) for t in re.findall(r"`([^`\n]+)`", texto) if " " not in t
    }

    encontradas = set()
    for token in candidatos:
        if not _con_forma_de_identificador(token):
            continue
        legitimos = canonicos.get(normalizar(token))
        if legitimos and token not in legitimos:
            encontradas.add((token, sorted(legitimos)[0]))
    return encontradas


# --------------------------------------------------------------------------
# Comprobación contra los documentos reales
# --------------------------------------------------------------------------


# Documentos cuyo trabajo es **citar** el defecto para explicarlo. Comprobarlos
# haría fallar al validador por la razón contraria a la que existe.
CITAN_DEFECTOS_A_PROPOSITO = ("revisiones",)

# Defecto registrado y pendiente de decisión: `D1-2` de `REV-01`. El diagrama de
# `SPEC-01` sigue en `PascalCase` porque corregirlo va junto con quitar la
# transición `en_verificacion → en_revision`, que depende de la decisión `C-1`.
# Se marca como fallo esperado **estricto**: cuando se arregle, este test fallará
# avisando de que hay que quitar la marca, para que no se quede aquí para siempre.
PENDIENTES = {"specs/SPEC - Backend.md": "D1-2 de REV-01, pendiente del paso 2"}


def _documentos_a_comprobar(raiz: pathlib.Path) -> list[pathlib.Path]:
    return [
        d
        for d in documentos_del_proyecto(raiz)
        if not any(p in d.parts for p in CITAN_DEFECTOS_A_PROPOSITO)
    ]


def test_hay_documentos_que_comprobar(raiz):
    """Si los filtros dejan la lista vacía, el validador no mira nada."""
    assert len(_documentos_a_comprobar(raiz)) >= 5


def test_ningun_documento_cita_una_variante_de_un_literal(raiz, definitions, request):
    """Un documento por vez, para que un defecto registrado no tape a los demás."""
    canonicos = literales_canonicos(definitions)

    desviaciones: dict[str, list[tuple[str, str]]] = {}
    for documento in _documentos_a_comprobar(raiz):
        relativa = documento.relative_to(raiz).as_posix()
        if relativa in PENDIENTES:
            continue
        halladas = variantes(documento.read_text(encoding="utf-8"), canonicos)
        if halladas:
            desviaciones[relativa] = sorted(halladas)

    assert not desviaciones, (
        "Hay literales de enumeración escritos de otra forma que en la tabla de "
        "`Docs/definitions.md`:\n"
        + "\n".join(
            f"  {doc}: " + ", ".join(f"{escrito!r} debería ser {esperado!r}" for escrito, esperado in pares)
            for doc, pares in sorted(desviaciones.items())
        )
    )


@pytest.mark.xfail(strict=True, reason=PENDIENTES["specs/SPEC - Backend.md"])
def test_spec_01_ya_no_cita_literales_en_pascalcase(raiz, definitions):
    """Defecto conocido, no silenciado.

    `SPEC-01` escribe los estados en `PascalCase` en su diagrama de §2.2.1. Está
    registrado como `D1-2` y su corrección va junto con la decisión `C-1`, así
    que todavía no toca. Queda como fallo esperado estricto: en cuanto se
    corrija, este test avisará de que hay que borrar la marca.
    """
    canonicos = literales_canonicos(definitions)
    spec = (raiz / "specs" / "SPEC - Backend.md").read_text(encoding="utf-8")
    assert variantes(spec, canonicos) == set()


def test_la_tabla_de_vocabularios_se_lee_entera(definitions):
    """Precondición: si el parser lee dos valores, el test anterior no vale."""
    canonicos = literales_canonicos(definitions)
    assert len(canonicos) >= 40, (
        f"Solo leí {len(canonicos)} literales de la tabla de vocabularios. "
        "O cambió el formato o el validador dejó de mirar."
    )
    assert normalizar("en_verificacion") in canonicos


# --------------------------------------------------------------------------
# Caso negativo
# --------------------------------------------------------------------------


def test_negativo_caza_un_literal_en_pascalcase(fixtures, definitions):
    """El fixture reproduce el defecto real: el diagrama en `PascalCase`."""
    canonicos = literales_canonicos(definitions)
    roto = (fixtures / "diagrama_con_literales_en_pascalcase.md").read_text(
        encoding="utf-8"
    )

    halladas = dict(variantes(roto, canonicos))
    assert "EnVerificacion" in halladas, (
        f"El fixture escribe los estados en PascalCase y el validador encontró "
        f"{halladas}. Si está vacío, el validador no sirve."
    )
    assert halladas["EnVerificacion"] == "en_verificacion"
    assert "EnRevision" in halladas


def test_negativo_caza_un_literal_con_tilde(fixtures, definitions):
    """El mismo fixture escribe `perdida_de_control` con tilde."""
    canonicos = literales_canonicos(definitions)
    roto = (fixtures / "diagrama_con_literales_en_pascalcase.md").read_text(
        encoding="utf-8"
    )

    halladas = dict(variantes(roto, canonicos))
    assert "pérdida_de_control" in halladas
    assert halladas["pérdida_de_control"] == "perdida_de_control"


def test_negativo_un_literal_correcto_no_dispara(definitions):
    """Escribir el literal bien no produce hallazgo."""
    canonicos = literales_canonicos(definitions)
    assert variantes("El estado es `en_verificacion` y pasa a `aceptada`.", canonicos) == set()
