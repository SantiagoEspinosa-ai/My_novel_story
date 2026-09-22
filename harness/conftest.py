"""Fixtures compartidas del harness.

Aquí vive lo único que sabe dónde están los documentos. Los parsers y los
validadores trabajan sobre texto, así que este fichero es la frontera entre el
disco y el resto del harness.
"""

from __future__ import annotations

import pathlib

import pytest

# `conftest.py` está en `harness/`, así que la raíz del repositorio es su padre.
RAIZ = pathlib.Path(__file__).resolve().parent.parent

DOCUMENTOS = {
    "definitions": RAIZ / "Docs" / "definitions.md",
    "architecture": RAIZ / "Docs" / "architecture.md",
    "domain_knowledge": RAIZ / "Docs" / "domain-knowledge.md",
    "verification": RAIZ / "Docs" / "verification.md",
    "claude": RAIZ / "CLAUDE.md",
    "agents": RAIZ / "AGENTS.md",
    "skill_invariantes": RAIZ / ".agents" / "skills" / "harness-invariantes" / "SKILL.md",
}


def _leer(clave: str) -> str:
    ruta = DOCUMENTOS[clave]
    if not ruta.exists():
        pytest.fail(
            f"No existe {ruta.relative_to(RAIZ)}. "
            "Si el documento se renombró, hay que actualizar DOCUMENTOS en conftest.py "
            "en el mismo commit: es la regla de AGENTS.md sobre rutas literales."
        )
    return ruta.read_text(encoding="utf-8")


@pytest.fixture(scope="session")
def raiz() -> pathlib.Path:
    return RAIZ


@pytest.fixture(scope="session")
def definitions() -> str:
    return _leer("definitions")


@pytest.fixture(scope="session")
def architecture() -> str:
    return _leer("architecture")


@pytest.fixture(scope="session")
def verification() -> str:
    return _leer("verification")


@pytest.fixture(scope="session")
def skill_invariantes() -> str:
    return _leer("skill_invariantes")


@pytest.fixture(scope="session")
def fixtures() -> pathlib.Path:
    """Carpeta de los documentos rotos a propósito."""
    return pathlib.Path(__file__).resolve().parent / "fixtures"
