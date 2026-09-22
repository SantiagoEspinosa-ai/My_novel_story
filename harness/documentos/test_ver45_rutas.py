"""VER-45 — Las rutas citadas en los documentos existen tal cual están escritas.

Es la única clase de defecto con historial real en este repositorio: al renombrar
`defintions` → `definitions.md` y `SRS.md` → `SPEC - Backend.md` quedaron setenta
y tres referencias rotas, y ninguno de los cuarenta y tres validadores lo
cubría.

**Alcance, y por qué es el que es.** Los documentos citan tres cosas con forma de
ruta y solo una es una referencia:

1. **Referencias** a documentos que deberían existir ahora — `Docs/definitions.md`.
   Esto es lo que se comprueba.
2. **Planes**: dónde vivirá algo que todavía no se ha escrito — `backend/app/`,
   `features/contexto/tests/`. No son referencias rotas, son trabajo pendiente.
3. **Cosas que parecen rutas y no lo son**: endpoints (`/obras/{id}`), fragmentos
   de árbol (`commons/`), repositorios (`github.com/fastapi/fastapi`).

La regla que los separa sin listas escritas a mano: **una ruta se comprueba si su
primer segmento existe en la raíz del repositorio**, o si resuelve relativa al
documento que la cita. Todo lo demás queda fuera y está declarado como punto
ciego.
"""

from __future__ import annotations

import pathlib
import re
import subprocess

import pytest

from harness.documentos import parsers

# Las skills de terceros no son nuestras y citan rutas de su propio repositorio.
VENDORIZADAS = ("feature-sliced-design", "fastapi", "sqlite-vec")

# Un token con estas marcas es una plantilla, no una ruta concreta.
MARCAS_DE_PLANTILLA = ("NN", "{", "}", "...", "xx", "<")


def documentos_del_proyecto(raiz: pathlib.Path) -> list[pathlib.Path]:
    """Los markdown que mantenemos nosotros.

    Se excluye `harness/` a propósito: sus fixtures citan rutas rotas por
    encargo y su documentación cita literales desviados para explicarlos. Un
    validador que se comprobara a sí mismo fallaría siempre por la razón
    equivocada.
    """
    return [
        p
        for p in sorted(raiz.rglob("*.md"))
        if ".git" not in p.parts
        and "harness" not in p.parts
        and not any(v in p.parts for v in VENDORIZADAS)
    ]


def ignorada_por_git(ruta: str, raiz: pathlib.Path) -> bool:
    """Una ruta que git ignora no se espera que exista en un clon.

    `AGENTS.md` cita `.claude/skills/` justamente para explicar por qué está
    ignorada. Exigir que exista sería exigir lo contrario de lo que el documento
    dice.
    """
    try:
        return (
            subprocess.run(
                ["git", "check-ignore", "-q", ruta],
                cwd=raiz,
                capture_output=True,
                timeout=15,
            ).returncode
            == 0
        )
    except (OSError, subprocess.TimeoutExpired):
        return False


def rutas_citadas(texto: str) -> set[str]:
    """Tokens entre acentos graves que tienen forma de ruta.

    Se ignoran los bloques de código: describen árboles de carpetas futuros, no
    citan nada.
    """
    sin_bloques = re.sub(r"```.*?```", "", texto, flags=re.S)
    encontradas = set()
    for token in re.findall(r"`([^`\n]+)`", sin_bloques):
        if "/" not in token:
            continue
        if token.startswith(("/", "http", "#", "github.com")):
            continue
        if any(marca in token for marca in MARCAS_DE_PLANTILLA):
            continue
        encontradas.add(token)
    return encontradas


def ubicaciones_planificadas(texto_verification: str) -> set[str]:
    """La columna "Dónde vive" de `Docs/verification.md`.

    Esas rutas son planes por construcción: dicen dónde vivirá una prueba que
    todavía no se ha escrito. Eximirlas leyéndolas del propio documento evita
    una lista escrita a mano en el código, que es donde los permisos se
    convierten en silencio.
    """
    planificadas = set()
    for linea in texto_verification.splitlines():
        if not re.match(r"^\|\s*\*?\*?VER-\d+", linea):
            continue
        celdas = parsers.celdas(linea)
        if len(celdas) >= 7:
            planificadas.add(parsers.limpiar(celdas[-1]))
    return planificadas


def reservadas(texto_agents: str) -> set[str]:
    """Las rutas de la sección "Todavía no existe" de `AGENTS.md`.

    El documento declara que aparecerán cuando se creen. Citarlas no es un
    defecto: es el uso previsto.
    """
    m = re.search(r"## Todavía no existe(.*?)(?=\n## )", texto_agents, re.S)
    if not m:
        raise parsers.DocumentoIlegible(
            "AGENTS.md no tiene la sección 'Todavía no existe'."
        )
    return set(re.findall(r"^- `([^`]+)`", m.group(1), re.M))


def esta_exenta(ruta: str, exentas: set[str]) -> bool:
    """Una ruta bajo un prefijo exento también lo está."""
    return any(ruta == e or ruta.startswith(e) for e in exentas)


def rutas_rotas(
    documento: pathlib.Path, raiz: pathlib.Path, exentas: set[str]
) -> list[str]:
    """Las rutas de un documento que deberían existir y no existen."""
    rotas = []
    for ruta in rutas_citadas(documento.read_text(encoding="utf-8")):
        if esta_exenta(ruta, exentas) or ignorada_por_git(ruta, raiz):
            continue
        # Relativa al documento que la cita: así funcionan los enlaces de las skills.
        if (documento.parent / ruta).exists():
            continue
        primer_segmento = ruta.split("/")[0]
        if not (raiz / primer_segmento).exists():
            continue  # Fuera de alcance: plan o fragmento, no referencia.
        if not (raiz / ruta).exists():
            rotas.append(ruta)
    return rotas


# --------------------------------------------------------------------------
# Comprobación contra los documentos reales
# --------------------------------------------------------------------------


def test_ninguna_ruta_citada_esta_rota(raiz, verification):
    exentas = reservadas((raiz / "AGENTS.md").read_text(encoding="utf-8"))
    exentas |= ubicaciones_planificadas(verification)

    rotas: dict[str, list[str]] = {}
    for documento in documentos_del_proyecto(raiz):
        encontradas = rutas_rotas(documento, raiz, exentas)
        if encontradas:
            rotas[str(documento.relative_to(raiz))] = sorted(encontradas)

    assert not rotas, (
        "Hay rutas citadas que no existen tal cual están escritas:\n"
        + "\n".join(f"  {doc}: {rs}" for doc, rs in sorted(rotas.items()))
    )


def test_el_alcance_no_se_traga_los_documentos(raiz, verification):
    """Precondición: el validador tiene que estar mirando algo.

    Si los filtros se pasan de estrictos, el test anterior pasa por no comprobar
    nada. Aquí se exige que las referencias entre documentos —que sí existen y sí
    se comprueban— sean unas cuantas.
    """
    exentas = reservadas((raiz / "AGENTS.md").read_text(encoding="utf-8"))
    exentas |= ubicaciones_planificadas(verification)

    comprobadas = 0
    for documento in documentos_del_proyecto(raiz):
        for ruta in rutas_citadas(documento.read_text(encoding="utf-8")):
            if esta_exenta(ruta, exentas):
                continue
            if (raiz / ruta.split("/")[0]).exists():
                comprobadas += 1

    assert comprobadas >= 20, (
        f"Solo se están comprobando {comprobadas} rutas. El filtro se ha pasado "
        "de estricto y el validador ya no mira nada."
    )


# --------------------------------------------------------------------------
# Caso negativo
# --------------------------------------------------------------------------


def test_negativo_caza_una_ruta_rota(fixtures, raiz, verification):
    """El fixture cita `Docs/defintions.md`, con el typo que ya ocurrió."""
    exentas = reservadas((raiz / "AGENTS.md").read_text(encoding="utf-8"))
    exentas |= ubicaciones_planificadas(verification)

    roto = fixtures / "documento_con_ruta_rota.md"
    encontradas = rutas_rotas(roto, raiz, exentas)

    assert "Docs/defintions.md" in encontradas, (
        f"El fixture cita una ruta rota y el validador encontró {encontradas}. "
        "Si está vacío, el validador no sirve."
    )


def test_negativo_una_ruta_buena_no_dispara(fixtures, raiz, verification):
    """El mismo fixture cita `Docs/definitions.md`, que sí existe, y no salta."""
    exentas = reservadas((raiz / "AGENTS.md").read_text(encoding="utf-8"))
    exentas |= ubicaciones_planificadas(verification)

    encontradas = rutas_rotas(fixtures / "documento_con_ruta_rota.md", raiz, exentas)
    assert "Docs/definitions.md" not in encontradas


def test_negativo_agents_sin_su_seccion_revienta():
    """Si `AGENTS.md` pierde la sección de rutas reservadas, el parser falla."""
    with pytest.raises(parsers.DocumentoIlegible):
        reservadas("# Un AGENTS.md sin la sección\n")
