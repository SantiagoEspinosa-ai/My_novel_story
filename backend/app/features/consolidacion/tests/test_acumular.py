"""`PLAN-23` A2: reconstruir el estado desde el delta guardado, y `VER-09`.

`acumular(semilla, deltas)` es **puro**: devuelve el mundo en la forma de
`mundo.leer`. La comparacion va contra el aplicador de produccion (consolidar y
leer) **y contra uno ingenuo escrito solo para esta prueba** (Regla 3: un
validador no comparte implementacion con lo que valida).
"""

import copy
import sqlite3

import pytest

from app.features.consolidacion import aplicar, deltas, mundo

SEMILLA = {
    "entidades_vivas": {"per-ana": "vivo", "per-leo": "vivo"},
    "ubicaciones": {"per-ana": "lug-casa", "per-leo": "lug-casa"},
    "accesos": {"lug-casa": ["lug-puerto"], "lug-puerto": ["lug-casa"]},
    "conocimiento": {("per-ana", "h-mapa"): {"desde": None, "grado": "sabe"}},
}

SECUENCIA = [
    ("esc-1", {"movimientos": [{"personaje": "per-ana", "a": "lug-puerto"}],
               "revelaciones": [{"sujeto": "per-leo", "hecho": "h-barco"}]}),
    # Un movimiento y una muerte en el mismo `t`: la fila negativa de `VER-09`.
    ("esc-2", {"movimientos": [{"personaje": "per-leo", "a": "lug-puerto"}],
               "cambios_de_estado_vital": [
                   {"personaje": "per-leo", "de": "vivo", "a": "muerto"}]}),
    ("esc-3", {"revelaciones": [{"sujeto": "per-ana", "hecho": "h-barco"},
                                {"sujeto": "per-ana", "hecho": "h-mapa"}]}),
]


def _base(semilla=SEMILLA):
    con = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(con)
    mundo.rebobinar(con, semilla)
    return con


def _ingenuo(semilla, secuencia):
    """El aplicador de referencia: diccionarios y un bucle, nada de SQL."""
    m = copy.deepcopy(semilla)
    for escena, d in secuencia:
        for mv in d.get("movimientos", []):
            m["ubicaciones"][mv["personaje"]] = mv["a"]
        for c in d.get("cambios_de_estado_vital", []):
            m["entidades_vivas"][c["personaje"]] = c["a"]
        for r in d.get("revelaciones", []):
            m["conocimiento"].setdefault((r["sujeto"], r["hecho"]),
                                         {"desde": escena, "grado": "sabe"})
    return m


def test_acumular_los_deltas_da_el_mismo_mundo_que_consolidarlos():
    con = _base()
    for escena, d in SECUENCIA:
        aplicar.consolidar(con, escena, d)
    acumulado, incompatibles = mundo.acumular(SEMILLA, SECUENCIA)
    assert incompatibles == []
    assert acumulado == mundo.leer(con)


def test_ver09_un_movimiento_y_una_muerte_en_el_mismo_t_coinciden_con_el_ingenuo():
    con = _base()
    for escena, d in SECUENCIA:
        aplicar.consolidar(con, escena, d)
    referencia = _ingenuo(SEMILLA, SECUENCIA)
    assert mundo.leer(con) == referencia
    assert mundo.acumular(SEMILLA, SECUENCIA)[0] == referencia
    assert referencia["entidades_vivas"]["per-leo"] == "muerto"
    assert referencia["ubicaciones"]["per-leo"] == "lug-puerto"


def test_acumular_no_toca_la_semilla():
    antes = copy.deepcopy(SEMILLA)
    mundo.acumular(SEMILLA, SECUENCIA)
    assert SEMILLA == antes


def test_un_delta_incompatible_se_informa_con_su_escena_y_no_revienta():
    malos = SECUENCIA + [
        ("esc-4", {"movimientos": [{"personaje": "per-ana", "a": "lug-casa"}],
                   "cambios_de_estado_vital": [
                       {"personaje": "per-leo", "de": "vivo", "a": "desaparecido"}]}),
        ("esc-5", {"movimientos": [{"personaje": "per-nadie", "a": "lug-casa"}]}),
    ]
    acumulado, incompatibles = mundo.acumular(SEMILLA, malos)
    assert [i["escena"] for i in incompatibles] == ["esc-4", "esc-5"]
    assert "per-leo" in incompatibles[0]["motivo"]
    # Como en produccion, un delta incompatible no entra **entero**: esc-4 no mueve a Ana.
    assert acumulado["ubicaciones"]["per-ana"] == "lug-puerto"


def test_rebobinar_y_volver_a_acumular_deja_el_mundo_igual():
    con = _base()
    for escena, d in SECUENCIA:
        aplicar.consolidar(con, escena, d)
    despues = mundo.leer(con)
    mundo.rebobinar(con, SEMILLA)
    assert mundo.leer(con) == SEMILLA
    mundo.rebobinar(con, mundo.acumular(SEMILLA, SECUENCIA)[0])
    assert mundo.leer(con) == despues


def test_rebobinar_conserva_la_fecha_de_nacimiento():
    con = _base()
    aplicar.fijar_fecha_de_nacimiento(con, "per-ana", "1990-01-02")
    mundo.rebobinar(con, SEMILLA)
    assert aplicar.fechas_de_nacimiento(con) == {"per-ana": "1990-01-02"}


def test_rebobinar_es_una_sola_transaccion():
    con = _base()
    roto = copy.deepcopy(SEMILLA)
    roto["conocimiento"][("per-ana", None)] = {"desde": None, "grado": "sabe"}
    with pytest.raises(sqlite3.IntegrityError):
        mundo.rebobinar(con, roto)
    assert mundo.leer(con) == SEMILLA


def test_los_deltas_de_una_lista_de_escenas_salen_en_ese_orden():
    con = _base()
    for escena, d in SECUENCIA:
        aplicar.consolidar(con, escena, d)
    assert deltas.de_escenas(con, ["esc-3", "esc-1", "esc-sin-delta"]) == [
        ("esc-3", SECUENCIA[2][1]), ("esc-1", SECUENCIA[0][1])]


def test_el_resumen_de_acciones_del_guion_lee_el_delta_guardado():
    """Hallazgo 2: el guion hacia `SELECT delta` y la columna es `contenido`."""
    con = _base()
    aplicar.consolidar(con, "esc-1", {"acciones": [{"personaje": "per-ana", "hecho": "h-mapa"}],
                                      "revelaciones": [{"sujeto": "per-ana", "hecho": "h-x"}]})
    aplicar.consolidar(con, "esc-2", {"acciones": [{"personaje": "per-ana", "hecho": "h-x"}]})
    assert deltas.contar_acciones(con, ["esc-1", "esc-2"]) == {
        "acciones": 2, "revelaciones": 1, "deltas": 2}
    from pathlib import Path
    guion = (Path(__file__).resolve().parents[4] / "obra_diez_capitulos.py").read_text(
        encoding="utf-8")
    assert "SELECT delta FROM" not in guion and "deltas.contar_acciones(" in guion


def test_rebobinar_una_obra_no_toca_el_mundo_de_otra_de_la_misma_base():
    """`F-123`: `rebobinar` borraba **todo** el mundo vivo -las entidades, los lugares y el
    conocimiento de las demas obras de la base- y los nombres de los lugares. Con `obra`,
    solo lo de su prefijo, que es como acota `F-100`."""
    con = _base()
    aplicar.sembrar(con, {"obra-a-per-ana": ("vivo", "obra-a-lug-casa"),
                          "obra-b-per-leo": ("vivo", "obra-b-lug-faro")})
    mundo.sembrar_lugares(con, {"obra-a-lug-casa": [], "obra-b-lug-faro": []})
    mundo.fijar_nombre_de_lugar(con, "obra-a-lug-casa", "Casa")
    mundo.fijar_nombre_de_lugar(con, "obra-b-lug-faro", "Faro")
    mundo.sembrar_conocimiento(con, [{"sujeto": "obra-b-per-leo", "hecho": "h-luz"}])
    de_b = mundo.leer(con, obra="obra-b")
    mundo.rebobinar(con, {"entidades_vivas": {"obra-a-per-ana": "muerto"},
                          "ubicaciones": {"obra-a-per-ana": "obra-a-lug-casa"},
                          "accesos": {"obra-a-lug-casa": []}, "conocimiento": {}},
                    obra="obra-a")
    assert mundo.leer(con, obra="obra-b") == de_b
    assert mundo.leer(con, obra="obra-a")["entidades_vivas"] == {"obra-a-per-ana": "muerto"}
    nombres = dict(con.execute("SELECT id, nombre FROM lugar WHERE id LIKE 'obra-%'"))
    assert nombres == {"obra-a-lug-casa": "Casa", "obra-b-lug-faro": "Faro"}
    # Y lo que no es de ninguna de las dos (la semilla del fixture, sin prefijo), tampoco.
    assert mundo.leer(con)["entidades_vivas"]["per-ana"] == "vivo"
