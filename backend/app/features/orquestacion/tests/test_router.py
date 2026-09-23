"""E4 — Los endpoints del ciclo, con el doble todavia.

Ninguna prueba de aqui llama a un modelo: los endpoints **encolan**, y el
trabajo lo ejecuta el worker. Eso es justo lo que se comprueba.
"""

import pytest
from fastapi.testclient import TestClient

from app.features.escaleta import repository as repo
from app.main import app, preparar_base


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    con = preparar_base(ruta)
    # `capitulo` explicito: la puerta de cierre pregunta por capitulo, y sin
    # este campo estas pruebas pasaban solo porque obra y capitulo eran el
    # mismo identificador. Era la coincidencia la que las sostenia, no la
    # consulta.
    repo.guardar_escaleta(con, "cap-1", [
        {"id": "e1", "orden": 1, "capitulo": "cap-1",
         "pov": "per-marta", "lugar": "lug-salon",
         "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
         "beats": ["b1"], "longitud_objetivo": [1200, 2200]},
    ])
    con.close()
    app.state.ruta_db = ruta
    return TestClient(app)


def test_generar_devuelve_202_y_un_identificador_nunca_el_texto(cliente):
    r = cliente.post("/escenas/e1/generar")
    assert r.status_code == 202
    assert r.json()["id_trabajo"]
    assert "texto" not in r.json()


def test_generar_una_escena_que_no_existe_devuelve_404(cliente):
    assert cliente.post("/escenas/no-existe/generar").status_code == 404


def test_aceptar_con_una_bloqueante_abierta_devuelve_409_y_dice_cual(cliente):
    """Una `bloqueante` no se rinde: el 409 tiene que decir que lo impide."""
    import sqlite3
    from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
    from app.commons.dominio.enumeraciones import Severidad as S

    con = sqlite3.connect(app.state.ruta_db)
    repo.guardar_borrador(con, "e1", texto="x", modelo="doble", prompt_hash="aa")
    repo.guardar_hallazgo(con, invariante="INV-02", verificador="verificador_de_reglas",
                          escena="e1", severidad=S.BLOQUEANTE, estado=EH.ABIERTO,
                          descripcion="un muerto presente")
    con.close()

    r = cliente.post("/escenas/e1/aceptar", params={"version": 1})
    assert r.status_code == 409
    assert "INV-02" in str(r.json())


def test_aceptar_rindiendose_deja_el_estado_distinguible(cliente):
    import sqlite3
    con = sqlite3.connect(app.state.ruta_db)
    repo.guardar_borrador(con, "e1", texto="x", modelo="doble", prompt_hash="aa")
    con.close()
    r = cliente.post("/escenas/e1/aceptar",
                     params={"version": 1, "rindiendose": True})
    assert r.status_code == 200
    assert r.json()["estado"] == "aceptada_por_rendicion"


def test_cerrar_un_capitulo_a_medias_devuelve_409_y_dice_que_lo_bloquea(cliente):
    """El cuerpo dice que arreglar, no solo que no se puede."""
    r = cliente.post("/capitulos/cap-1/cerrar")
    assert r.status_code == 409
    cuerpo = r.json()["detail"]
    assert cuerpo["escenas_sin_consolidar"] == ["e1"]


def test_cerrar_un_capitulo_limpio_devuelve_los_menores_que_se_dejan_pasar(cliente):
    import sqlite3
    from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
    from app.commons.dominio.enumeraciones import Severidad as S

    con = sqlite3.connect(app.state.ruta_db)
    repo.guardar_borrador(con, "e1", texto="x", modelo="doble", prompt_hash="aa")
    repo.aceptar_borrador(con, "e1", version=1, rindiendose=True)
    repo.guardar_hallazgo(con, invariante="INV-15", verificador="auditor_de_obra",
                          escena="e1", severidad=S.MENOR, estado=EH.ABIERTO,
                          descripcion="deriva de estilo")
    con.close()

    r = cliente.post("/capitulos/cap-1/cerrar")
    assert r.status_code == 200
    assert r.json()["estado"] == "cerrado"
    assert len(r.json()["menores_que_se_dejan_pasar"]) == 1
