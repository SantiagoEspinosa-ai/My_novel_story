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

    El rango de palabras se abre de par en par a proposito. Los capitulos de
    juguete de estos tests son frases sueltas ("Texto del capitulo 1."), y desde
    que el contador de palabras emite su propio veredicto (`EJECUCION.md` 3.5b)
    un rango realista los suspenderia todos por longitud, que no es lo que
    ninguno de ellos quiere medir. Los tests que SI prueban el rango montan su
    propia configuracion con un rango estrecho; asi cada test dice en su cuerpo
    que longitud espera, en vez de heredarla de aqui.
    """
    config = config_minima(
        3,
        runtime={"directorio_salida": str(tmp_path / "salida")},
        estructura={"palabras_min": 1, "palabras_max": 100000},
    )
    salida = orquestacion.directorio_salida(config)
    return config, salida
