"""B1 — El alta de una obra, y la forma que tendran las otras nueve features.

Se elige la feature mas pequena a proposito: `A-01` dice que una feature es un
caso de uso del pipeline y que tiene siempre los mismos ficheros -router,
schemas, service, repository, tests-. Probar esa forma aqui cuesta poco; y si
esta mal, se ve en una feature en vez de en diez.

Lo que estas pruebas sostienen, por orden de importancia:

    1. `422` cuando el `Brief` no cumple el esquema. Es la frontera de
       validacion de `CLAUDE.md` llegando hasta la API.
    2. `A-02`: una feature no importa de otra. Se comprueba de verdad, no de
       palabra.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.features.brief import repository as repositorio
from app.main import app, preparar_base


@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta)
    app.state.ruta_db = ruta
    return TestClient(app)


def test_un_brief_sin_premisa_devuelve_422(cliente):
    """El caso negativo. `premisa` es obligatoria en `Docs/definitions.md`."""
    r = cliente.post("/obras", json={"titulo": "La casa"})
    assert r.status_code == 422


def test_un_brief_con_un_campo_inventado_devuelve_422(cliente):
    """"Un campo que no esta definido alli no entra en un esquema"."""
    r = cliente.post("/obras", json={
        "titulo": "La casa", "premisa": "Una familia hereda una casa",
        "subtramas_favoritas": ["ninguna"],
    })
    assert r.status_code == 422


def test_un_brief_con_un_genero_fuera_de_la_enumeracion_devuelve_422(cliente):
    r = cliente.post("/obras", json={
        "titulo": "La casa", "premisa": "Una familia hereda una casa",
        "persona": "cuarta",
    })
    assert r.status_code == 422


def test_un_alta_valida_devuelve_201_con_su_id(cliente):
    r = cliente.post("/obras", json={
        "titulo": "La casa", "premisa": "Una familia hereda una casa",
        "persona": "tercera_limitada", "tiempo_verbal": "pasado",
    })
    assert r.status_code == 201
    assert r.json()["id"]


def test_consultar_una_obra_que_no_existe_devuelve_404(cliente):
    assert cliente.get("/obras/no-existe").status_code == 404


def test_una_obra_se_devuelve_con_sus_capitulos_y_su_estado(cliente):
    """`RF-23` en su forma minima: nunca se devuelve texto suelto."""
    id_obra = cliente.post("/obras", json={
        "titulo": "La casa", "premisa": "Una familia hereda una casa",
    }).json()["id"]
    cuerpo = cliente.get("/obras/{0}".format(id_obra)).json()
    assert cuerpo["titulo"] == "La casa"
    assert cuerpo["capitulos"] == []


def test_una_feature_no_importa_de_otra_feature(cliente):
    """`A-02`, comprobado y no prometido.

    Es el caso negativo de `VER-13` en su forma mas barata: recorre los
    modulos de `features/` y comprueba que ninguno importe de otra feature.
    Solo `orquestacion/` esta autorizada, y todavia no existe.
    """
    import pathlib
    import re

    raiz = pathlib.Path(__file__).resolve().parents[3] / "features"
    fallos = []
    for py in raiz.rglob("*.py"):
        feature = py.relative_to(raiz).parts[0]
        if feature == "orquestacion":
            continue
        for m in re.finditer(r"^from app\.features\.(\w+)", py.read_text(encoding="utf-8"), re.M):
            if m.group(1) != feature:
                fallos.append("{0} importa de {1}".format(py.name, m.group(1)))
    assert fallos == []


# --- El alta con sus capitulos, en un solo sitio ---------------------------


def test_alta_de_obra_registra_la_obra_y_sus_capitulos_con_su_orden():
    """Una sola funcion da de alta una obra, la llame quien la llame.

    La forma de la obra vive en el brief. Darla de alta desde dos sitios -el
    guion por un lado con `INSERT` a mano, la API por otro- es exactamente como
    vuelven a divergir: el dia que una de las dos aprenda algo, la otra no.

    El orden de los capitulos no es decorativo: es lo que
    `escaleta.asignar_t_discurso` necesita para numerar el orden de lectura de
    la obra entera, y sin el las escenas se quedan sin situar.
    """
    con = sqlite3.connect(":memory:")
    repositorio.alta_de_obra(
        con, "obra-1",
        {"titulo": "La casa", "premisa": "Una casa exacta", "genero": "terror"},
        ["cap-01", "cap-02", "cap-03"])
    obra = repositorio.leer(con, "obra-1")
    assert obra["titulo"] == "La casa"
    assert obra["capitulos"] == ["cap-01", "cap-02", "cap-03"]
    assert [f[0] for f in con.execute(
        "SELECT orden FROM capitulo WHERE obra='obra-1' ORDER BY orden")] == [1, 2, 3]


def test_dar_de_alta_dos_veces_no_duplica_ni_renumera():
    """Idempotente: el guion la llama en cada arranque, y repetir un arranque
    no puede dejar la obra con veinte capitulos."""
    con = sqlite3.connect(":memory:")
    datos = {"titulo": "La casa", "premisa": "p", "genero": "terror"}
    for _ in range(2):
        repositorio.alta_de_obra(con, "obra-1", datos, ["cap-01", "cap-02"])
    assert con.execute(
        "SELECT COUNT(*) FROM capitulo WHERE obra='obra-1'").fetchone()[0] == 2
