"""La puerta de capítulo, pedida por HTTP, mira las escenas de **su** capítulo.

El camino interno ya se arregló con `escenas_de_capitulo`, y el endpoint se
quedó atrás: sigue llamando a `escenas_de`, que filtra **por obra**. Hoy no se
nota porque el guion de generación crea una obra por capítulo, así que obra y
capítulo son el mismo identificador y el resultado sale bien **por accidente**.

En cuanto la obra pase a tener diez capítulos dentro —que es a lo que va el
guion— `escenas_de(con, "cap-3")` no encontrará ninguna escena y cerrar un
capítulo contestará *«no existe»* sobre uno que sí existe.

Dos capítulos en la prueba, y no uno, por la Regla 9: con uno solo, una consulta
que se equivoque de columna sigue devolviendo lo correcto.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.features.escaleta import repository as repo
from app.main import app, preparar_base


def _escena(id_escena, orden, capitulo):
    return {"id": id_escena, "orden": orden, "capitulo": capitulo,
            "pov": "per-marta", "lugar": "lug-salon",
            "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
            "beats": ["b1"], "longitud_objetivo": [1200, 2200]}


@pytest.fixture
def cliente(tmp_path):
    """Una obra, dos capítulos. El primero terminado, el segundo a medias."""
    ruta = str(tmp_path / "obra.db")
    con = preparar_base(ruta)
    repo.guardar_escaleta(con, "obra-1", [
        _escena("e1", 1, "cap-1"),
        _escena("e2", 2, "cap-2"),
    ])
    con.execute("UPDATE escena SET estado = ? WHERE id = ?",
                (EE.CONSOLIDADA.value, "e1"))
    con.commit()
    con.close()
    app.state.ruta_db = ruta
    return TestClient(app)


def test_cerrar_un_capitulo_no_mira_las_escenas_del_otro(cliente):
    """`cap-1` está entero; que `cap-2` esté a medias no es asunto suyo."""
    r = cliente.post("/capitulos/cap-1/cerrar")

    assert r.status_code == 200, r.json()
    assert r.json()["capitulo"] == "cap-1"


def test_un_capitulo_que_existe_nunca_contesta_que_no_existe(cliente):
    """El 404 es la forma en que este defecto se disfraza.

    Preguntando por obra, un capítulo real devuelve cero escenas y el endpoint
    concluye que no existe. Es una respuesta creíble a una pregunta mal hecha.
    """
    r = cliente.post("/capitulos/cap-2/cerrar")

    assert r.status_code != 404, "cap-2 existe y tiene una escena"
    assert r.status_code == 409, "está a medias, así que no se puede cerrar"
