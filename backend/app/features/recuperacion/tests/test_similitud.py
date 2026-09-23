"""La recuperacion por similitud: el bloque 5 del contexto.

QUE SE INDEXA Y QUE NO
-----------------------
`CLAUDE.md` lo fija: fichas de entidad, resumenes de escena y presagios
pendientes. **El texto completo de las escenas se guarda pero no se recupera
por similitud**: para eso estan los resumenes. Indexar el texto entero seria
volver a meter la obra en el contexto por otra puerta.

DE DONDE SALEN LOS EMBEDDINGS
------------------------------
De un proveedor que se inyecta. Aqui se prueba contra uno determinista, porque
lo que estas pruebas verifican es **la recuperacion**, no la calidad semantica
del modelo: si el doble y el real se distinguen, el fallo aparece al cambiar de
proveedor y no al escribir la consulta.
"""

import sqlite3

import pytest

from app.features.recuperacion import similitud


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    similitud.asegurar_tablas(c, dimensiones=4)
    return c


def test_sin_la_extension_se_dice_y_no_se_finge(monkeypatch):
    """`sqlite-vec` puede no estar. Lo que no vale es degradar a una busqueda
    lexica en silencio: devolveria resultados plausibles por otro criterio y
    nadie sabria que la similitud no esta funcionando."""
    monkeypatch.setattr(similitud, "_cargar_extension",
                        lambda con: (_ for _ in ()).throw(ImportError("no hay")))
    with pytest.raises(similitud.SinSoporteVectorial):
        similitud.asegurar_tablas(sqlite3.connect(":memory:"), dimensiones=4)


def test_se_indexa_una_ficha_y_se_recupera_por_cercania(con):
    similitud.indexar(con, "ficha", "per-marta", [1.0, 0.0, 0.0, 0.0])
    similitud.indexar(con, "ficha", "per-ana", [0.0, 1.0, 0.0, 0.0])
    cercanos = similitud.buscar(con, [0.9, 0.1, 0.0, 0.0], limite=1)
    assert [c["referencia"] for c in cercanos] == ["per-marta"]


def test_los_tres_tipos_del_documento_se_indexan(con):
    """Fichas, resumenes y setups pendientes (`SPEC-26` v3: los presagios se
    retiraron y su sitio lo ocupa el setup, que es narrativa general)."""
    for tipo in similitud.TIPOS:
        similitud.indexar(con, tipo, "x-" + tipo, [0.0, 0.0, 0.0, 1.0])
    assert len(similitud.buscar(con, [0.0, 0.0, 0.0, 1.0], limite=10)) == 3


def test_el_texto_de_escena_no_se_puede_indexar(con):
    """`CLAUDE.md`: se guarda pero **no se recupera por similitud**. Si una
    tarea parece necesitarlo, el fallo esta en los resumenes."""
    with pytest.raises(ValueError, match="resumen"):
        similitud.indexar(con, "texto_de_escena", "e1", [1.0, 0.0, 0.0, 0.0])


def test_se_puede_filtrar_por_tipo(con):
    similitud.indexar(con, "ficha", "per-marta", [1.0, 0.0, 0.0, 0.0])
    similitud.indexar(con, "setup", "set-1", [1.0, 0.0, 0.0, 0.0])
    solo = similitud.buscar(con, [1.0, 0.0, 0.0, 0.0], limite=10, tipo="setup")
    assert [c["referencia"] for c in solo] == ["set-1"]


def test_reindexar_la_misma_referencia_la_sustituye(con):
    """Una ficha tiene versiones, y la recuperacion busca la vigente. Dos
    vectores para la misma referencia devolverian la misma entidad dos veces y
    gastarian sitio del bloque 5 en repetirse."""
    similitud.indexar(con, "ficha", "per-marta", [1.0, 0.0, 0.0, 0.0])
    similitud.indexar(con, "ficha", "per-marta", [0.0, 0.0, 0.0, 1.0])
    todos = similitud.buscar(con, [0.0, 0.0, 0.0, 1.0], limite=10)
    assert len(todos) == 1


def test_una_dimension_distinta_falla_al_indexar(con):
    """Un vector de otro tamaño significa que alguien cambio de modelo de
    embeddings sin reindexar. Mezclarlos daria distancias sin sentido."""
    with pytest.raises(ValueError, match="dimensiones"):
        similitud.indexar(con, "ficha", "per-x", [1.0, 0.0])


def test_buscar_en_un_indice_vacio_devuelve_vacio_y_no_revienta(con):
    assert similitud.buscar(con, [1.0, 0.0, 0.0, 0.0], limite=5) == []


def test_un_presagio_ya_no_se_indexa(con):
    """`SPEC-26` v3 `RF-21`: retirado. Indexarlo en silencio dejaria un tipo que
    ninguna consulta busca."""
    with pytest.raises(ValueError):
        similitud.indexar(con, "presagio", "pre-1", [1.0, 0.0, 0.0, 0.0])
