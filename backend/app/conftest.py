"""Lo que vale para todas las pruebas del backend.

**Ninguna prueba lee el `backend/.env` real** (`SPEC-29` `RF-08`). Cuando el autor ponga
sus claves de Langfuse para `PLAN-29` E13, una prueba que arrancara la aplicacion no puede
acabar enviando nada a su proyecto: la ruta de las credenciales apunta aqui a un fichero
que no existe, y quien necesite claves se las da a mano.
"""

import pytest


@pytest.fixture(autouse=True)
def _sin_claves_reales(monkeypatch, tmp_path):
    from app.commons.observabilidad import credenciales
    monkeypatch.setattr(credenciales, "RUTA", tmp_path / "no-existe.env")
