"""`F-133` (`PLAN-22` E18): la conexion de una peticion no puede depender del hilo.

FastAPI ejecuta una dependencia sincrona con `yield` en un hilo del pool y el endpoint
sincrono en **otro**, y la cierra en un tercero. `sqlite3` por defecto solo deja usar la
conexion en el hilo que la creo: con una sola peticion a la vez suele coincidir el hilo y
no falla nada; con la web pidiendo tres cosas a la vez (versiones, capitulo, progreso),
la inspeccion real de E18 vio `500` intermitentes. Cada peticion usa su conexion **en
serie**, nunca a la vez, asi que no comprobar el hilo es seguro.

Las pruebas con `TestClient` no lo cazaban: de una en una, el hilo coincide por suerte.
Esta la reproduce sin suerte: crea la conexion en un hilo y la usa en otro.
"""

import threading
from types import SimpleNamespace

import pytest

from app.features.brief import router as brief
from app.features.entrevista import router as entrevista
from app.features.lectura import router as lectura
from app.features.orquestacion import router as orquestacion


@pytest.mark.parametrize("modulo", [brief, entrevista, lectura, orquestacion],
                         ids=["brief", "entrevista", "lectura", "orquestacion"])
def test_la_conexion_de_una_peticion_se_puede_usar_desde_otro_hilo(modulo, tmp_path):
    peticion = SimpleNamespace(app=SimpleNamespace(state=SimpleNamespace(
        ruta_db=str(tmp_path / "hilos.db"))))
    generador = modulo.conexion(peticion)
    con = next(generador)
    errores = []

    def en_otro_hilo():
        try:
            con.execute("SELECT 1").fetchone()
        except Exception as e:  # lo que se quiere ver es precisamente el error
            errores.append(e)

    hilo = threading.Thread(target=en_otro_hilo)
    hilo.start()
    hilo.join()
    generador.close()
    assert errores == []
