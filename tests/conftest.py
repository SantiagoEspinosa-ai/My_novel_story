"""Montaje compartido por los tests.

`conftest.py` es el archivo que pytest carga automaticamente antes que los
tests, y las fixtures que se definan aqui estan disponibles en todos los
archivos de test sin importar nada. Es lo que permite que
`tests/test_ensamblador.py` use el mismo entorno de juguete que
`tests/test_orquestacion.py` sin duplicarlo.
"""

import pytest

from src import orquestacion
from tests.ayudas import config_minima


@pytest.fixture
def entorno(tmp_path):
    """Configuracion de juguete con salida/ en una carpeta temporal.

    Devuelve (config, salida). El directorio de salida es absoluto para que
    `directorio_salida` no lo resuelva contra la raiz del proyecto real: los
    tests no pueden escribir en la salida de verdad, que es donde vive el
    trabajo del usuario.
    """
    config = config_minima(3, runtime={"directorio_salida": str(tmp_path / "salida")})
    salida = orquestacion.directorio_salida(config)
    return config, salida
