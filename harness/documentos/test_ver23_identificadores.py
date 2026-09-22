"""VER-23 — Ningún identificador publicado se reutiliza ni se renumera.

`Docs/verification.md` § VER-23: *"El conjunto de identificadores solo crece; lo
retirado queda marcado obsoleto, no borrado"*. Su punto ciego está declarado: ve
el **conjunto**, no el **significado**, así que cambiar el enunciado de `INV-14`
manteniendo el número le pasa desapercibido.

Se puede escribir hoy porque la referencia es el historial de git, no el código.
"""

from __future__ import annotations

import subprocess

import pytest

from harness.documentos import parsers

# Familias de identificadores publicados y dónde viven.
FAMILIAS = {
    "INV": "Docs/definitions.md",
    "VER": "Docs/verification.md",
    "A": "Docs/architecture.md",
}


def solo_crece(antes: str, despues: str, prefijo: str) -> set[str]:
    """Identificadores que estaban y ya no están. Vacío es lo correcto."""
    return parsers.identificadores(antes, prefijo) - parsers.identificadores(
        despues, prefijo
    )


def _contenido_en(commit: str, ruta: str, raiz) -> str | None:
    """El contenido de un fichero en un commit, o `None` si no se puede leer."""
    try:
        resultado = subprocess.run(
            ["git", "show", f"{commit}:{ruta}"],
            cwd=raiz,
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if resultado.returncode != 0:
        return None
    return resultado.stdout.decode("utf-8", errors="replace")


@pytest.mark.parametrize(("prefijo", "ruta"), sorted(FAMILIAS.items()))
def test_ningun_identificador_desaparece_respecto_al_commit_anterior(prefijo, ruta, raiz):
    """Compara HEAD contra HEAD~1 para cada familia.

    Si el documento es nuevo en HEAD, no hay nada que comparar y la prueba se
    salta con motivo: es un caso legítimo, no un aprobado gratis.
    """
    antes = _contenido_en("HEAD~1", ruta, raiz)
    despues = _contenido_en("HEAD", ruta, raiz)

    if antes is None:
        pytest.skip(f"{ruta} no existía en HEAD~1: nada que comparar")
    if despues is None:
        pytest.skip(f"{ruta} no se puede leer en HEAD: ¿repositorio sin commits?")

    desaparecidos = sorted(solo_crece(antes, despues, prefijo))
    assert not desaparecidos, (
        f"Identificadores {prefijo}-xx que estaban en HEAD~1 y ya no están en "
        f"HEAD, en {ruta}: {desaparecidos}.\n"
        "Lo que deja de aplicar se marca como obsoleto, no se borra."
    )


# --------------------------------------------------------------------------
# Caso negativo
# --------------------------------------------------------------------------


def test_negativo_caza_un_identificador_borrado(fixtures):
    """`INV-02` desaparece entre las dos versiones del fixture."""
    antes = (fixtures / "identificadores_antes.md").read_text(encoding="utf-8")
    despues = (fixtures / "identificadores_despues.md").read_text(encoding="utf-8")

    desaparecidos = solo_crece(antes, despues, "INV")
    assert desaparecidos == {"INV-02"}, (
        f"El fixture borra INV-02 y el validador encontró {desaparecidos}. "
        "Si está vacío, el validador no sirve."
    )


def test_negativo_anadir_identificadores_no_dispara_el_validador(fixtures):
    """Crecer es legal: `A-03` aparece y no debe contar como violación."""
    antes = (fixtures / "identificadores_antes.md").read_text(encoding="utf-8")
    despues = (fixtures / "identificadores_despues.md").read_text(encoding="utf-8")

    assert solo_crece(antes, despues, "A") == set()
    assert "A-03" in parsers.identificadores(despues, "A")
