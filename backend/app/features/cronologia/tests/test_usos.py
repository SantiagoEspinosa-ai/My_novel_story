"""`SPEC-21` C-2 y C-4 — Donde se usa un hecho, y quien lo afirmo.

La tabla que faltaba. `hecho_canonico.escena_de_establecimiento` dice donde
**nace** un hecho; estas pruebas fijan lo otro: donde se **usa**, que son cuatro
relaciones distintas y no una.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.cronologia import extraccion, repository as repo

# `A-02`: esta feature no importa de ninguna otra, **ni en sus pruebas**. El
# fixture sembraba escenas con `escaleta/` y no hacian falta: `registrar_usos`
# recibe `escena` y `capitulo` como valores y **no consulta la tabla `escena`**,
# que es justo por lo que `repository.py` guarda el capitulo en la fila en vez
# de resolverlo por JOIN. El comprobador de importaciones lo cazó.


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    return c


# --- La tabla ---------------------------------------------------------------


def test_registrar_usos_guarda_el_capitulo_junto_al_uso(con):
    """La pregunta es «en que capitulos», asi que el capitulo va en la fila.

    Resolverlo por `JOIN` con `escena` cada vez tambien funcionaria; guardarlo
    hace la tabla autosuficiente para el consumidor mas caliente, que es la
    regeneracion selectiva recorriendo toda la obra.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA},
    ])
    filas = repo.usos_de_hecho(con, "h-llave")
    assert filas == [{"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
                      "tipo": U.ESTABLECE, "origen": O.DELTA}]


def test_escribir_dos_veces_el_mismo_uso_deja_una_sola_fila(con):
    """`SPEC-21` C-4: escribir es idempotente.

    Una escena ya consolidada no vuelve a pasar por aqui, pero la idempotencia
    no se apoya en esa garantia: apoyarse en ella la convierte en la unica que
    sostiene la tabla, y el dia que falle no habra nada debajo.
    """
    uso = {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
           "tipo": U.MENCIONA, "origen": O.REGLA}
    repo.registrar_usos(con, [uso])
    repo.registrar_usos(con, [uso])
    assert len(repo.usos_de_hecho(con, "h-llave")) == 1


def test_dos_tipos_sobre_el_mismo_par_son_dos_filas(con):
    """Mencionar y depender del mismo hecho en la misma escena es normal, y son
    dos hechos distintos sobre el mundo. La clave incluye el tipo por eso."""
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.MENCIONA, "origen": O.REGLA},
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.DEPENDE, "origen": O.DELTA},
    ])
    assert {f["tipo"] for f in repo.usos_de_hecho(con, "h-llave")} == {
        U.MENCIONA, U.DEPENDE}


def test_los_valores_vuelven_como_miembros_de_su_enumeracion(con):
    """La leccion de `hallazgos_abiertos`, que abrio la puerta de capitulo en
    silencio: si los modelos Pydantic son la frontera de validacion de la API,
    **la deserializacion es la frontera de validacion de la base**."""
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.DEPENDE, "origen": O.DELTA},
    ])
    fila = repo.usos_de_hecho(con, "h-llave")[0]
    assert fila["tipo"] is U.DEPENDE
    assert fila["origen"] is O.DELTA


# --- Los tres tipos que se rellenan solos -----------------------------------

DELTA = {
    "revelaciones": [{"sujeto": "per-marta", "hecho": "h-llave"}],
    "acciones": [{"personaje": "per-marta", "hecho": "h-sotano"}],
}
HECHOS = [
    {"id": "h-llave", "enunciado": "La llave del sotano esta en el costurero"},
    {"id": "h-sotano", "enunciado": "El sotano esta tapiado"},
    {"id": "h-pozo", "enunciado": "El pozo del patio no tiene fondo"},
]


def test_revelar_es_establecer_y_actuar_es_depender():
    """`SPEC-16` C-1 dejo escrita la distincion y aqui rinde dos veces.

    Revelar es **aprender**: el texto hace verdadero el hecho por primera vez.
    Actuar es **obrar sirviendose de lo ya sabido**: si el hecho fuera falso,
    la escena no se sostiene. Eso es exactamente `depende`, y por eso se puebla
    hoy sin tocar ningun prompt.
    """
    usos = extraccion.usos_de_la_escena(
        delta=DELTA, texto="", hechos=HECHOS, escena="e1", capitulo="cap-1")
    por_tipo = {(u["hecho"], u["tipo"]) for u in usos}
    assert ("h-llave", U.ESTABLECE) in por_tipo
    assert ("h-sotano", U.DEPENDE) in por_tipo


def test_mencionar_lo_calcula_el_codigo_sobre_el_texto():
    """`menciona` es el unico de los cuatro que es un dato **medido**.

    Sale de buscar el enunciado en el texto, no de que nadie lo declare, y por
    eso su origen es `regla` y no `delta`.
    """
    texto = "El pozo del patio no tiene fondo, dijo Marta sin mirarlo."
    usos = extraccion.usos_de_la_escena(
        delta={}, texto=texto, hechos=HECHOS, escena="e1", capitulo="cap-1")
    assert usos == [{"hecho": "h-pozo", "escena": "e1", "capitulo": "cap-1",
                     "tipo": U.MENCIONA, "origen": O.REGLA}]


def test_un_hecho_que_no_esta_ni_en_el_delta_ni_en_el_texto_no_produce_fila():
    """El caso negativo. Sin el, la extraccion podria estar marcando todo y
    estas pruebas seguirian en verde."""
    usos = extraccion.usos_de_la_escena(
        delta={}, texto="No pasa nada en absoluto.", hechos=HECHOS,
        escena="e1", capitulo="cap-1")
    assert usos == []


def test_contradice_no_se_deduce_solo_y_se_dice(con):
    """`SPEC-21` C-2: el valor existe, la tabla lo admite y nadie lo rellena.

    Un dato ausente no es un verde: preguntar por `contradice` no puede
    devolver una lista vacia como si fuera un resultado limpio, porque nadie ha
    mirado.
    """
    assert U.CONTRADICE in repo.TIPOS_QUE_NADIE_DEDUCE
    usos = extraccion.usos_de_la_escena(
        delta=DELTA, texto="El sotano esta tapiado", hechos=HECHOS,
        escena="e1", capitulo="cap-1")
    assert all(u["tipo"] is not U.CONTRADICE for u in usos)
