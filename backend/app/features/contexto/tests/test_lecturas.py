"""Qué leyó de verdad una escena: los hechos y el conocimiento que entraron.

La traza guardaba fichas, presagios y resúmenes, y **no hechos**. Por eso la
pregunta *«¿qué escenas dependen de este hecho?»* no se puede responder ni
a posteriori, y por eso tampoco se puede medir cuánto arrastra un cambio.

`SPEC-23` `S-5` dice de dónde puede salir ese conjunto, y el autor eligió la
variante **observada** —lo que el ensamblador metió de verdad en el prompt—
frente a la **declarada** por el modelo. El motivo no es que acierte más, es
**cómo se equivoca**: la observada sobre-aproxima y falla ruidoso —se regenera
de más y se ve—; la declarada se ajusta mejor y falla en silencio —omite algo
que sí se usó y deja una contradicción que nadie marca—.

Este módulo registra la observada. Las filas salen de código, no de un modelo,
así que son un **dato medido**.
"""

import sqlite3

import pytest

from app.features.contexto import ensamblado, repository


MATERIAL = {
    "hechos": [
        {"id": "hec-herencia", "enunciado": "Marta heredo la casa", "establecido_en": "e1"},
        {"id": "hec-llave", "enunciado": "La llave no aparece", "establecido_en": None},
    ],
    "mundo": {
        "conocimiento": {
            ("per-marta", "hec-herencia"): {"desde": "anterior_al_relato"},
            ("per-ana", "hec-llave"): {"desde": "e2"},
        },
    },
}


def test_las_lecturas_son_los_hechos_que_entraron(   ):
    leido = ensamblado.lecturas(MATERIAL)

    assert leido["hechos"] == ["hec-herencia", "hec-llave"]


def test_las_lecturas_traen_el_registro_de_conocimiento_con_su_sujeto():
    """Sin el sujeto no sirve: `INV-03` es sobre quién sabe qué, no sobre qué."""
    leido = ensamblado.lecturas(MATERIAL)

    assert leido["conocimiento"] == [
        {"sujeto": "per-ana", "hecho": "hec-llave"},
        {"sujeto": "per-marta", "hecho": "hec-herencia"},
    ]


def test_un_material_sin_hechos_ni_conocimiento_no_falla():
    """Una escena puede no llevar ninguno, y eso es un dato, no un error."""
    assert ensamblado.lecturas({}) == {"hechos": [], "conocimiento": []}


def test_las_lecturas_no_miran_el_recorte_y_eso_es_deliberado():
    """**Sobre-aproximar es la decisión, no un descuido.**

    El bloque 4 no se elimina pero sí se reduce, así que un hecho ofrecido
    puede acabar fuera del texto truncado. Aun así se registra: marcar de más
    hace regenerar de más, que cuesta dinero y se ve; marcar de menos deja una
    contradicción que nadie marca.

    Esta prueba existe para que quien "afine" esto más tarde tenga que borrarla
    a conciencia.
    """
    con_recorte = dict(MATERIAL, recortes=[{"bloque": "estado_y_conocimiento",
                                            "clase": "reduccion"}])

    assert ensamblado.lecturas(con_recorte) == ensamblado.lecturas(MATERIAL)


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repository.asegurar_tablas(c)
    return c


def test_las_lecturas_guardadas_vuelven_por_escena(con):
    repository.guardar_lecturas(con, "e3", ensamblado.lecturas(MATERIAL),
                               prompt_hash="abc123")

    filas = repository.lecturas_de(con, "e3")

    assert {f["hecho"] for f in filas} == {"hec-herencia", "hec-llave"}
    assert {(f["tipo"], f["sujeto"]) for f in filas if f["tipo"] == "conocimiento"} == {
        ("conocimiento", "per-ana"), ("conocimiento", "per-marta")}


def test_guardar_dos_veces_la_misma_llamada_no_duplica(con):
    """Un reintento del mismo prompt es la misma lectura, no dos."""
    leido = ensamblado.lecturas(MATERIAL)
    repository.guardar_lecturas(con, "e3", leido, prompt_hash="abc123")
    repository.guardar_lecturas(con, "e3", leido, prompt_hash="abc123")

    assert len(repository.lecturas_de(con, "e3")) == 4


def test_dos_intentos_distintos_se_guardan_los_dos(con):
    """Distinto `prompt_hash` es distinta llamada, y el contexto pudo cambiar."""
    repository.guardar_lecturas(con, "e3", {"hechos": ["hec-llave"], "conocimiento": []},
                               prompt_hash="aaa")
    repository.guardar_lecturas(con, "e3", {"hechos": ["hec-llave"], "conocimiento": []},
                               prompt_hash="bbb")

    assert len(repository.lecturas_de(con, "e3")) == 2


def test_que_escenas_leyeron_un_hecho(con):
    """La consulta que hace medible la pregunta 5 de `SPEC-23`."""
    repository.guardar_lecturas(con, "e1", {"hechos": ["hec-llave"], "conocimiento": []},
                               prompt_hash="a")
    repository.guardar_lecturas(con, "e2", {"hechos": ["hec-otro"], "conocimiento": []},
                               prompt_hash="b")
    repository.guardar_lecturas(con, "e3", {"hechos": ["hec-llave"], "conocimiento": []},
                               prompt_hash="c")

    assert repository.escenas_que_leyeron(con, "hec-llave") == ["e1", "e3"]


def test_una_llamada_sin_prompt_hash_se_guarda_ausente_y_no_vacia(con):
    """`RF-25` otra vez: un hueco no se rellena con una cadena vacia."""
    repository.guardar_lecturas(con, "e3", {"hechos": ["hec-llave"], "conocimiento": []})

    assert repository.lecturas_de(con, "e3")[0]["prompt_hash"] is None


def test_las_lecturas_de_otra_escena_no_se_cuelan(con):
    """Regla 9: hacen falta dos elementos en el lado que se desambigua.

    Con una sola escena en la tabla, un `lecturas_de` que se olvidara del
    `WHERE escena = ?` pasaria igual y la prueba no probaria nada. El defecto
    de la escena anterior de `F-40` sobrevivio exactamente asi: la primera
    prueba pasaba con un solo borrador porque el empate lo resolvia el rowid.
    """
    repository.guardar_lecturas(con, "e1", {"hechos": ["hec-mio"], "conocimiento": []},
                               prompt_hash="a")
    repository.guardar_lecturas(con, "e2", {"hechos": ["hec-ajeno"], "conocimiento": []},
                               prompt_hash="b")

    assert [f["hecho"] for f in repository.lecturas_de(con, "e1")] == ["hec-mio"]
