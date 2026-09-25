"""`SPEC-35` `RF-10`, `PLAN-35` E2: qué petición originó una versión, con las palabras del lector.

La versión guarda solo el identificador de su petición (`VersionSalida.peticion`); el texto
vive en `peticion_de_cambio.texto`. Se lee aquí por SQL, sin importar `orquestacion`.
"""

from app.features.regalo.tests.conftest import OBRA, OTRA


def _version(con, obra, numero, peticion=None):
    with con:
        con.execute('INSERT INTO version_de_obra (obra, numero, anterior, peticion, "commit") '
                    "VALUES (?, ?, ?, ?, 'abc1234')",
                    (obra, numero, numero - 1 if numero > 1 else None, peticion))


def _peticion(con, obra, texto):
    with con:
        return con.execute(
            "INSERT INTO peticion_de_cambio (obra, version_de_partida, clase, hecho, "
            "enunciado_nuevo, texto) VALUES (?, 1, 'hecho', 'hec-viaje', 'Fuimos a Oporto', ?)",
            (obra, texto)).lastrowid


def test_la_version_trae_las_palabras_de_su_peticion(cliente, con):
    _version(con, OBRA, 1)
    # Otra petición antes, de otra obra: una lectura que no filtrara por obra se la llevaría.
    _peticion(con, OTRA, "que el perro se llame Lur")
    p = _peticion(con, OBRA, "En realidad fuimos a Oporto, y en coche")
    _version(con, OBRA, 2, peticion=p)
    r = cliente.get("/obras/{0}/versiones/2/peticion".format(OBRA))
    assert r.status_code == 200, r.text
    assert r.json() == {"texto": "En realidad fuimos a Oporto, y en coche"}


def test_una_version_sin_peticion_trae_texto_nulo(cliente, con):
    _version(con, OBRA, 1)
    assert cliente.get("/obras/{0}/versiones/1/peticion".format(OBRA)).json() == {"texto": None}


def test_version_que_no_existe_es_404(cliente, con):
    _version(con, OBRA, 1)
    r = cliente.get("/obras/{0}/versiones/7/peticion".format(OBRA))
    assert r.status_code == 404 and "no existe la version" in r.json()["detail"]
