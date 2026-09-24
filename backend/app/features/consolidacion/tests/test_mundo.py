"""F1 y F2 — El estado circula y el conocimiento se escribe.

Se prueban juntas porque la segunda no significa nada sin la primera: que
`INV-03` acepte en la escena 2 lo revelado en la 1 exige que el mundo de la 2
salga de los deltas y no de un fixture.
"""

import sqlite3

import pytest

from app.features.consolidacion import aplicar, mundo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon"),
                        "per-ana": ("vivo", "lug-cocina")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-cocina", "lug-sotano"],
                              "lug-cocina": ["lug-salon"], "lug-sotano": ["lug-salon"]})
    return c


def test_el_mundo_leido_refleja_el_delta_de_la_escena_anterior(con):
    """F1. Sin esto la escena 2 genera contra el mundo de la 1."""
    assert mundo.leer(con)["ubicaciones"]["per-marta"] == "lug-salon"
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "per-marta",
                                                    "a": "lug-sotano"}]})
    assert mundo.leer(con)["ubicaciones"]["per-marta"] == "lug-sotano"


def test_una_revelacion_queda_sabida_a_partir_de_su_escena(con):
    """F2. `INV-03` lo lee y hasta ahora nadie lo escribia."""
    assert mundo.leer(con)["conocimiento"] == {}
    aplicar.consolidar(con, "e1", {"revelaciones": [{"sujeto": "per-marta",
                                                     "hecho": "hec-llave"}]})
    c = mundo.leer(con)["conocimiento"]
    assert c[("per-marta", "hec-llave")]["desde"] == "e1"


def test_que_uno_lo_revele_no_hace_que_lo_sepa_otro(con):
    """Media novela de terror vive en esta distincion."""
    aplicar.consolidar(con, "e1", {"revelaciones": [{"sujeto": "per-marta",
                                                     "hecho": "hec-llave"}]})
    c = mundo.leer(con)["conocimiento"]
    assert ("per-marta", "hec-llave") in c
    assert ("per-ana", "hec-llave") not in c


def test_inv03_deja_de_bloquear_una_accion_cuando_ya_se_revelo(con):
    """La prueba que une F1 y F2, y el circuito que `F-31` tenia al reves.

    Aprender primero, actuar despues. Antes esta prueba revelaba en las dos
    escenas y esperaba que la segunda revelacion pasara, lo que escondia el
    punto muerto: la puerta exigia saber de antes **para poder aprender**.
    """
    from app.features.verificacion import puertas

    escena = {"id": "e2", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
              "personajes_presentes": ["per-marta"], "lugar": "lug-salon"}
    aprender = {"revelaciones": [{"sujeto": "per-marta", "hecho": "hec-llave"}]}
    actuar = {"acciones": [{"personaje": "per-marta", "hecho": "hec-llave"}]}

    antes = puertas.verificar(escena, actuar, mundo.leer(con))
    assert any(h.invariante == "INV-03" for h in antes), "sin registro, bloquea"

    aplicar.consolidar(con, "e1", aprender)
    despues = puertas.verificar(escena, actuar, mundo.leer(con))
    assert not any(h.invariante == "INV-03" for h in despues), "con registro, pasa"


def test_el_conocimiento_no_sobrevive_a_un_delta_que_falla(con):
    """Va en la misma transaccion, o quedaria sabido algo que no paso."""
    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", {
            "revelaciones": [{"sujeto": "per-marta", "hecho": "hec-llave"}],
            "movimientos": [{"personaje": "per-nadie", "a": "lug-salon"}]})
    assert mundo.leer(con)["conocimiento"] == {}


# --- SPEC-17: el conocimiento inicial, lo anterior al relato --------------

def test_el_conocimiento_inicial_existe_antes_de_la_escena_1(con):
    """`F-32`: el registro arrancaba vacio, asi que ninguna accion era posible
    en la primera escena. Ana sabe que heredo la casa desde antes del relato, y
    eso no es una revelacion de ninguna escena."""
    mundo.sembrar_conocimiento(con, [
        {"sujeto": "per-ana", "hecho": "hec-herencia", "grado": "sabe"}])
    c = mundo.leer(con)["conocimiento"]
    assert ("per-ana", "hec-herencia") in c
    assert c[("per-ana", "hec-herencia")]["desde"] is None, "anterior al relato"


def test_lo_anterior_al_relato_lleva_su_propia_fuente(con):
    """`SPEC-17` C-3: sin esto, la invariante de la fuente que `SPEC-16` dejo
    abierta nace ya incumplida por las entradas iniciales."""
    mundo.sembrar_conocimiento(con, [
        {"sujeto": "per-ana", "hecho": "hec-herencia", "grado": "sabe"}])
    fila = con.execute("SELECT fuente FROM conocimiento WHERE sujeto='per-ana'").fetchone()
    assert fila[0] == mundo.ANTERIOR_AL_RELATO


def test_una_accion_en_la_escena_1_es_posible_si_el_plan_lo_declaro(con):
    """El circuito de `F-32`, de punta a punta."""
    from app.features.verificacion import puertas

    mundo.sembrar_conocimiento(con, [
        {"sujeto": "per-marta", "hecho": "hec-herencia", "grado": "sabe"}])
    escena = {"id": "e1", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
              "pov": "per-marta", "lugar": "lug-salon", "pov_usado": "per-marta"}
    delta = {"acciones": [{"personaje": "per-marta", "hecho": "hec-herencia"}]}
    assert not any(h.invariante == "INV-03"
                   for h in puertas.verificar(escena, delta, mundo.leer(con)))


def test_una_revelacion_posterior_no_pisa_lo_que_ya_se_sabia(con):
    """`INSERT OR IGNORE`: si ya lo sabia de antes del relato, enterarse otra
    vez en la escena 4 no cambia desde cuando lo sabe."""
    mundo.sembrar_conocimiento(con, [
        {"sujeto": "per-marta", "hecho": "hec-herencia", "grado": "sabe"}])
    aplicar.consolidar(con, "e4", {
        "revelaciones": [{"sujeto": "per-marta", "hecho": "hec-herencia"}]})
    assert mundo.leer(con)["conocimiento"][("per-marta", "hec-herencia")]["desde"] is None


# --- `PLAN-27` E2: los nombres del canon ------------------------------------------

def test_volver_a_sembrar_no_borra_un_nombre_ya_fijado(con):
    """`INSERT OR REPLACE` borra la fila y la vuelve a escribir: todo lo que no va en el
    `INSERT` -el nombre- se quedaria a `NULL` sin que nada fallara (Regla 7)."""
    aplicar.fijar_nombre(con, "per-marta", "Marta Ibarra")
    mundo.fijar_nombre_de_lugar(con, "lug-salon", "El salón de la casa")
    aplicar.sembrar(con, {"per-marta": ("vivo", "lug-cocina")})
    mundo.sembrar_lugares(con, {"lug-salon": ["lug-cocina"]})
    assert con.execute("SELECT nombre_canonico, lugar FROM entidad WHERE id='per-marta'"
                       ).fetchone() == ("Marta Ibarra", "lug-cocina")
    assert con.execute("SELECT nombre FROM lugar WHERE id='lug-salon'"
                       ).fetchone() == ("El salón de la casa",)


def test_sembrar_lugares_no_depende_del_orden_de_las_columnas():
    """`mundo.sembrar_lugares` insertaba por posicion: con una columna mas en medio,
    los accesos habrian caido en otra."""
    c = sqlite3.connect(":memory:")
    c.execute("CREATE TABLE lugar (id TEXT PRIMARY KEY, nombre TEXT, "
              "accesos TEXT NOT NULL DEFAULT '[]')")
    mundo.sembrar_lugares(c, {"lug-a": ["lug-b"]})
    assert c.execute("SELECT nombre, accesos FROM lugar").fetchone() == (None, '["lug-b"]')
