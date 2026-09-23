"""`SPEC-21` C-2 — Cada consumidor cuenta los tipos que le sirven, y solo esos.

Estas son las pruebas que sostienen la parte parametrizable: no fijan que
significa "usar un hecho", fijan que **cada capacidad puede decidirlo por su
cuenta** y que cambiar de opinion es editar una constante, no migrar la base.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.cronologia import consultas, repository as repo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    # Un hecho con las cuatro relaciones repartidas en cuatro capitulos. Es el
    # caso que distingue a los cuatro consumidores: cada uno ve un subconjunto
    # distinto, y si alguno viera los cuatro capitulos estaria contando de mas.
    repo.registrar_usos(c, [
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA},
        {"hecho": "h-llave", "escena": "e2", "capitulo": "cap-2",
         "tipo": U.MENCIONA, "origen": O.REGLA},
        {"hecho": "h-llave", "escena": "e3", "capitulo": "cap-3",
         "tipo": U.DEPENDE, "origen": O.DELTA},
        {"hecho": "h-llave", "escena": "e4", "capitulo": "cap-4",
         "tipo": U.CONTRADICE, "origen": O.HUMANO},
    ])
    return c


def test_aparecer_en_un_capitulo_se_satisface_con_mencionarlo(con):
    """Si el lector pidio que salga un gato negro, lo pedido es que **salga**.

    Exigir que la trama dependa de el daria por incumplido un encargo que el
    texto cumplio.
    """
    r = consultas.aparece_en_algun_capitulo(con, "h-llave")
    assert r["aparece"] is True
    assert r["capitulos"] == ["cap-2"]


def test_un_hecho_que_solo_se_establece_no_cuenta_como_aparicion(con):
    """El caso negativo, y el que obliga a que los tipos sean cuatro.

    Un hecho que el delta declara establecido pero que el texto no llega a
    nombrar es exactamente el fallo que un validador de elementos
    personalizados existe para cazar: lo prometido en la estructura y ausente
    en la pagina.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-gato", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA}])
    assert consultas.aparece_en_algun_capitulo(con, "h-gato")["aparece"] is False


def test_la_regeneracion_selectiva_ignora_la_mencion_de_paso(con):
    """`cap-2` solo lo nombra: reescribirlo seria reescribir por una alusion."""
    assert consultas.capitulos_a_regenerar(con, "h-llave") == ["cap-1", "cap-3"]


def test_la_ficha_de_personaje_enlaza_a_los_tres_tipos_de_uso(con):
    """La ficha enlaza a donde el lector encontrara algo. `contradice` no es
    un sitio donde encontrar el hecho: es donde encontrarlo roto."""
    assert consultas.capitulos_de_la_ficha(con, "h-llave") == [
        "cap-1", "cap-2", "cap-3"]


def test_lean_recibe_el_grafo_entero_incluida_la_arista_negativa(con):
    """Un demostrador necesita las cuatro: sin `contradice` no puede probar
    que el canon es consistente, solo que se usa mucho."""
    assert consultas.capitulos_donde_se_usa(con, "h-llave", consultas.PARA_LEAN) == [
        "cap-1", "cap-2", "cap-3", "cap-4"]


def test_cambiar_de_opinion_es_pasar_otros_tipos_sin_migrar_nada(con):
    """La prueba de que la decision quedo parametrizada y no fijada.

    Si mañana se decide que la regeneracion selectiva tambien debe arrastrar
    las menciones, es pasar otro conjunto: las cuatro filas ya estan escritas.
    """
    assert consultas.capitulos_donde_se_usa(
        con, "h-llave", (U.ESTABLECE, U.DEPENDE, U.MENCIONA)) == [
        "cap-1", "cap-2", "cap-3"]


def test_un_uso_sin_capitulo_se_dice_y_no_se_cuela_como_capitulo(con):
    """Las escenas anteriores a `SPEC-21` no tienen capitulo. Devolver `None`
    dentro de la lista de capitulos lo convertiria en un capitulo llamado
    `None` en cuanto alguien lo pintara."""
    repo.registrar_usos(con, [
        {"hecho": "h-pozo", "escena": "e9", "capitulo": None,
         "tipo": U.MENCIONA, "origen": O.REGLA}])
    r = consultas.aparece_en_algun_capitulo(con, "h-pozo")
    assert r["capitulos"] == []
    assert r["usos_sin_capitulo"] == 1


def test_contradice_declara_que_nadie_lo_deduce(con):
    """`SPEC-21`: el tipo existe, la tabla lo admite y no lo rellena nadie.

    Quien pregunte tiene que poder distinguir "no hay contradicciones" de
    "nadie ha buscado contradicciones".
    """
    assert consultas.cobertura_de_tipos()[U.CONTRADICE] == "no_se_deduce"
    assert consultas.cobertura_de_tipos()[U.MENCIONA] == "regla"
