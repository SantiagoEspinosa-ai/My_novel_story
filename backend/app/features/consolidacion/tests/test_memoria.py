"""F3 y F4 — Los resumenes se apilan y las fichas crecen.

Son los dos bloques que hacen crecer el contexto. Sin ellos el recorte opera
sobre una ficcion y `VER-37` no se puede contestar.

SIN TOCAR `escaleta`, Y ESO ES PARTE DE LA PRUEBA
---------------------------------------------------
La primera version de este fichero importaba el repositorio de `escaleta` para
sembrar escenas, porque `memoria` hacia `JOIN escena` para saber el orden. Eso
acoplaba dos features **por la base de datos**, que `A-02` prohibe y que el
comprobador de importaciones no podia ver: no habia `import`, el acoplamiento
viajaba por SQL. Ahora el orden entra como numero.
"""

import sqlite3

import pytest

from app.features.consolidacion import memoria


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    memoria.asegurar_tablas(c)
    return c


def test_los_resumenes_se_apilan_y_salen_en_orden(con):
    memoria.guardar_resumen(con, "e1", 1, "Marta llega.", ["hec-herencia"])
    memoria.guardar_resumen(con, "e2", 2, "Marta baja.", ["hec-sotano"])
    previos = memoria.resumenes_hasta(con, 3)
    assert [r["escena"] for r in previos] == ["e1", "e2"]
    assert previos[0]["hechos_clave"] == ["hec-herencia"]


def test_un_resumen_no_ve_los_de_escenas_posteriores(con):
    memoria.guardar_resumen(con, "e1", 1, "a")
    memoria.guardar_resumen(con, "e3", 3, "c")
    assert [r["escena"] for r in memoria.resumenes_hasta(con, 2)] == ["e1"]


def test_hechos_clave_en_prosa_no_entra(con):
    """`SPEC-03` y la Regla 4: se comprueba en la frontera."""
    with pytest.raises(memoria.HechoNoEsIdentificador, match="identificadores"):
        memoria.guardar_resumen(con, "e1", 1, "x", ["la llave no aparece"])


def test_una_ficha_gana_version_en_vez_de_sobrescribirse(con):
    """Sobrescribir haria irreconstruible el contexto de una escena pasada."""
    memoria.actualizar_fichas(con, "e1", 1, {"per-marta": "Recien llegada."})
    memoria.actualizar_fichas(con, "e2", 2, {"per-marta": "Ha bajado al sotano."})
    assert con.execute("SELECT COUNT(*) FROM ficha").fetchone()[0] == 2


def test_se_recupera_la_version_vigente_en_ese_orden(con):
    memoria.actualizar_fichas(con, "e1", 1, {"per-marta": "Recien llegada."})
    memoria.actualizar_fichas(con, "e3", 3, {"per-marta": "Ha bajado al sotano."})
    en_e2 = memoria.fichas_en(con, 2)
    assert en_e2[0]["resumen"] == "Recien llegada."
    assert en_e2[0]["version_en_t"] == "e1"


def test_el_contexto_crece_con_las_escenas(con):
    """El criterio de terminacion de la Fase F, en pequeño.

    Es la primera prueba del proyecto que no comprueba correccion sino
    **crecimiento**: que el material acumulado sea mayor tras cada escena.
    """
    tamanos = []
    for i in (1, 2, 3):
        memoria.guardar_resumen(con, "e{0}".format(i), i, "Resumen de escena. " * 5)
        memoria.actualizar_fichas(con, "e{0}".format(i), i,
                                  {"per-{0}".format(i): "Ficha. " * 10})
        tamanos.append(
            sum(len(r["texto"]) for r in memoria.resumenes_hasta(con, 99))
            + sum(len(f["resumen"]) for f in memoria.fichas_en(con, 99)))
    assert tamanos == sorted(tamanos), "no decrece"
    assert tamanos[0] < tamanos[-1], (
        "el contexto tiene que crecer solo: {0}".format(tamanos))


# --- F-40: la memoria no puede mezclar obras ------------------------------

def test_los_resumenes_no_mezclan_obras(con):
    """`F-40`, medido en la obra de diez capitulos.

    El `orden` de una escena es **por obra** -la escena 1 de cada capitulo
    tiene orden 1- y `resumenes_hasta` filtraba solo por `orden`. Con dos
    obras en la misma base, la escena 4 de la segunda recibia los resumenes de
    la primera **entremezclados y en orden equivocado**, y la escena 1 de un
    capitulo recibia cero: arrancaba sin memoria de todo lo anterior.
    """
    memoria.guardar_resumen(con, "a-e1", 1, "primera de A", [], obra="obra-a")
    memoria.guardar_resumen(con, "a-e2", 2, "segunda de A", [], obra="obra-a")
    memoria.guardar_resumen(con, "b-e1", 1, "primera de B", [], obra="obra-b")

    de_a = memoria.resumenes_hasta(con, 3, obra="obra-a")
    assert [r["escena"] for r in de_a] == ["a-e1", "a-e2"]
    de_b = memoria.resumenes_hasta(con, 3, obra="obra-b")
    assert [r["escena"] for r in de_b] == ["b-e1"]


def test_sin_obra_se_devuelve_todo_como_antes(con):
    """Compatibilidad: quien no la pase sigue viendo lo de siempre. La obra es
    un filtro que se añade, no un requisito que rompa lo que ya llamaba."""
    memoria.guardar_resumen(con, "a-e1", 1, "primera", [], obra="obra-a")
    assert len(memoria.resumenes_hasta(con, 3)) == 1


def test_las_fichas_tampoco_mezclan_obras(con):
    memoria.actualizar_fichas(con, "a-e1", 1, {"per-marta": "en A"}, obra="obra-a")
    memoria.actualizar_fichas(con, "b-e1", 1, {"per-ana": "en B"}, obra="obra-b")
    assert [f["entidad"] for f in memoria.fichas_en(con, 9, obra="obra-a")] == ["per-marta"]


# --- `F-45`: la memoria se ordena por el discurso, no por el orden ----------


def test_los_resumenes_se_ordenan_por_el_discurso_y_cruzan_el_capitulo(con):
    """`F-45`. El `orden` es local al capitulo y los resumenes tienen que
    cruzarlo: una novela no olvida el capitulo uno al empezar el dos.

    Con `orden`, la escena 1 del capitulo dos preguntaba por «lo anterior a 1» y
    recibia **cero**. Con `t_discurso`, que numera la obra entera, recibe las
    dos del capitulo uno.
    """
    memoria.guardar_resumen(con, "c1-e1", 1, "la primera", obra="obra-1")
    memoria.guardar_resumen(con, "c1-e2", 2, "la segunda", obra="obra-1")
    memoria.guardar_resumen(con, "c2-e1", 3, "la tercera", obra="obra-1")
    anteriores = memoria.resumenes_hasta(con, 3, obra="obra-1")
    assert [r["texto"] for r in anteriores] == ["la primera", "la segunda"]


def test_un_resumen_sin_posicion_en_el_discurso_no_se_guarda_en_silencio(con):
    """Frontera (Regla 4), y fallo ruidoso.

    Una escena que no se ha podido situar en el orden de lectura no tiene donde
    caer entre los resumenes. Guardarla con la posicion vacia la dejaria fuera
    de toda consulta ordenada **sin que nadie lo note**, que es la Regla 8 otra
    vez: el hueco se veria igual que no tener resumen.
    """
    with pytest.raises(memoria.SinPosicionEnElDiscurso):
        memoria.guardar_resumen(con, "e1", None, "texto", obra="obra-1")


def test_dos_obras_distintas_siguen_sin_mezclarse(con):
    """Lo que `F-40` cerro no se afloja: `t_discurso` numera **dentro** de una
    obra, asi que dos obras vuelven a tener las dos su posicion 1."""
    memoria.guardar_resumen(con, "a-e1", 1, "de la obra A", obra="obra-A")
    memoria.guardar_resumen(con, "b-e1", 1, "de la obra B", obra="obra-B")
    assert [r["texto"] for r in memoria.resumenes_hasta(con, 2, obra="obra-A")] == [
        "de la obra A"]
