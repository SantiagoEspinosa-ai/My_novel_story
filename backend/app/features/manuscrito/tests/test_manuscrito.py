"""La obra, leible de principio a fin.

EL TEXTO EXISTIA Y LA OBRA NO
-------------------------------
Despues de generar sesenta escenas, el texto vivia en cincuenta y siete filas
de la tabla `borrador` y **no habia forma de leerlo seguido**: hacia falta
saber que escena va en que capitulo, en que orden, y cual de sus versiones se
acepto. Tres cosas que estan en la base y ninguna en el texto.

Una novela que solo se puede leer con SQL no esta terminada.

QUE VERSION DE CADA ESCENA
----------------------------
La que dice `Escena.borrador_aceptado`, y si no consta, la ultima. No es lo
mismo: una escena rendida tiene varias versiones y `borrador_aceptado` dice
**cual se eligio** (`RF-24`). Coger siempre la ultima daria por buena una que
se descarto.

`VER-60` EXIGE QUE EL TEXTO SEA EL AUDITADO
---------------------------------------------
*"El texto de una escena en el manuscrito es byte a byte el del `Borrador` que
se audito."* Por eso este modulo **no toca el texto**: ni recorta, ni limpia,
ni junta parrafos. Lo unico que pone de su parte son los titulos, y van
marcados para que se puedan quitar.
"""

import sqlite3

import pytest

from app.features.manuscrito import exportar


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE obra (id TEXT PRIMARY KEY, titulo TEXT, premisa TEXT,
                           genero TEXT, subgenero TEXT, extension_objetivo INT,
                           guia_de_estilo TEXT);
        CREATE TABLE capitulo (id TEXT PRIMARY KEY, obra TEXT, orden INT,
                               estado TEXT DEFAULT 'abierto');
        CREATE TABLE escena (id TEXT PRIMARY KEY, obra TEXT, capitulo TEXT,
                             orden INT, estado TEXT, borrador_aceptado INT);
        CREATE TABLE borrador (escena TEXT, version INT, texto TEXT,
                               PRIMARY KEY (escena, version));
        INSERT INTO obra VALUES ('o1','La casa exacta','Marta hereda.','terror',
                                 NULL, NULL, NULL);
        INSERT INTO capitulo VALUES ('cap-01','o1',1,'abierto'),
                                    ('cap-02','o1',2,'abierto');
        INSERT INTO escena VALUES ('e1','o1','cap-01',1,'consolidada',NULL),
                                  ('e2','o1','cap-01',2,'consolidada',NULL),
                                  ('e3','o1','cap-02',1,'consolidada',NULL);
        INSERT INTO borrador VALUES ('e1',1,'Marta conto los peldanos.'),
                                    ('e2',1,'La puerta no cedia.'),
                                    ('e3',1,'Ana llego con una maleta.');
    """)
    c.commit()
    return c


def test_la_obra_se_lee_de_principio_a_fin(con):
    m = exportar.manuscrito(con, "o1")
    assert "Marta conto los peldanos." in m.texto
    assert "La puerta no cedia." in m.texto
    assert "Ana llego con una maleta." in m.texto


def test_las_escenas_salen_en_orden_de_lectura(con):
    m = exportar.manuscrito(con, "o1")
    i1 = m.texto.index("peldanos")
    i2 = m.texto.index("puerta")
    i3 = m.texto.index("maleta")
    assert i1 < i2 < i3, "capitulo 1 entero antes del capitulo 2"


def test_se_elige_el_borrador_aceptado_y_no_el_ultimo(con):
    """Una escena rendida tiene varias versiones y `borrador_aceptado` dice
    cual se eligio (`RF-24`). Coger la ultima daria por buena una descartada."""
    with con:
        con.execute("INSERT INTO borrador VALUES ('e1',2,'VERSION DESCARTADA')")
        con.execute("UPDATE escena SET borrador_aceptado=1 WHERE id='e1'")
    m = exportar.manuscrito(con, "o1")
    assert "Marta conto los peldanos." in m.texto
    assert "DESCARTADA" not in m.texto


def test_sin_borrador_aceptado_se_coge_la_ultima(con):
    """Compatibilidad con las escenas que salieron limpias: no se rindieron,
    asi que nadie eligio, y la ultima es la buena."""
    with con:
        con.execute("INSERT INTO borrador VALUES ('e2',2,'REESCRITA')")
    assert "REESCRITA" in exportar.manuscrito(con, "o1").texto


def test_una_escena_sin_texto_se_dice_y_no_se_salta(con):
    """Regla 8: un manuscrito al que le falta una escena **sin decirlo** se lee
    como una novela completa. `VER-60` avisa de esto mismo por el otro lado."""
    with con:
        con.execute("INSERT INTO escena VALUES ('e4','o1','cap-02',2,"
                    "'planificada',NULL)")
    m = exportar.manuscrito(con, "o1")
    assert m.escenas_sin_texto == ["e4"]
    assert "e4" in m.texto, "el hueco se marca en el propio texto"


def test_el_manuscrito_dice_cuantas_escenas_lleva(con):
    m = exportar.manuscrito(con, "o1")
    assert m.escenas == 3
    assert m.capitulos == 2
    assert m.palabras > 0


def test_el_texto_de_cada_escena_es_byte_a_byte_el_del_borrador(con):
    """`VER-60`. Este modulo no recorta, no limpia y no junta parrafos: lo
    unico que pone de su parte son los titulos."""
    m = exportar.manuscrito(con, "o1")
    for fila in con.execute("SELECT texto FROM borrador"):
        assert fila[0] in m.texto


def test_los_titulos_se_pueden_quitar(con):
    """Para comparar con `VER-60` hace falta poder mirar solo el texto."""
    sin = exportar.manuscrito(con, "o1", con_titulos=False)
    assert "Capitulo" not in sin.texto
    assert "Marta conto los peldanos." in sin.texto


def test_una_obra_que_no_existe_lo_dice(con):
    with pytest.raises(exportar.ObraSinTexto, match="o-que-no-existe"):
        exportar.manuscrito(con, "o-que-no-existe")


def test_una_obra_con_escenas_y_sin_cabecera_se_exporta_igual(con):
    """Las bases anteriores a `SPEC-21` no tienen tabla `obra`, y sus escenas
    son texto real que vale. Negarse a exportarlas seria perder una novela por
    una fila de cabecera que falta.

    Lo que **no** se hace es fingir que la cabecera estaba: el titulo es el
    identificador y consta que se uso ese.
    """
    with con:
        con.execute("DROP TABLE obra")
    m = exportar.manuscrito(con, "o1")
    assert "Marta conto los peldanos." in m.texto
    assert m.titulo == "o1"
    assert m.sin_cabecera is True


def test_un_identificador_sin_ninguna_escena_sigue_siendo_un_error(con):
    """Aqui no hay nada que exportar, y devolver un manuscrito vacio se leeria
    como 'no se escribio nada' en vez de 'pregunte por otra obra'."""
    with pytest.raises(exportar.ObraSinTexto, match="o-que-no-existe"):
        exportar.manuscrito(con, "o-que-no-existe")


def test_una_base_sin_tabla_capitulo_tambien_se_exporta(con):
    """Tercera ausencia de la misma familia. Las bases anteriores a `SPEC-21`
    no tienen ni `obra` ni `capitulo`, y sus escenas siguen siendo texto real.

    Sin capitulos no hay orden de capitulo que respetar, asi que se ordena por
    el de la escena — que es el unico que hay y es el correcto dentro de cada
    una."""
    with con:
        con.execute("DROP TABLE capitulo")
    m = exportar.manuscrito(con, "o1")
    assert "Marta conto los peldanos." in m.texto
    assert m.texto.index("peldanos") < m.texto.index("puerta")
    # Los capitulos se siguen contando: el identificador esta en la **escena**,
    # y lo que falta es la tabla que le da su orden.
    assert m.capitulos == 2


# --- `PLAN-27` E1: el texto de cada capitulo, sin recortar (`F-63`) ---------------

def test_el_borde_de_la_primera_y_la_ultima_escena_no_se_recorta(con):
    """`F-63`: `"".join(partes).strip()` se comia el blanco inicial de la primera escena
    y el final de la ultima, y la prueba de `VER-60` no lo veia porque comparaba con `in`
    y sus borradores no tenian blanco en los bordes."""
    con.execute("UPDATE borrador SET texto = '  Marta conto los peldanos.' WHERE escena = 'e1'")
    con.execute("UPDATE borrador SET texto = 'Ana llego con una maleta.\n\n' WHERE escena = 'e3'")
    m = exportar.manuscrito(con, "o1", con_titulos=False)
    assert m.texto.startswith("  Marta conto los peldanos.")
    assert "Ana llego con una maleta.\n\n" in m.texto


def test_capitulos_de_devuelve_el_texto_byte_a_byte_con_comillas_y_rayas(con):
    raya = "—«No», dijo. —Ya verás…\n"
    con.execute("UPDATE borrador SET texto = ? WHERE escena = 'e2'", (raya,))
    caps = exportar.capitulos_de(con, "o1")
    assert [c.id for c in caps] == ["cap-01", "cap-02"]
    assert [e.texto for e in caps[0].escenas] == ["Marta conto los peldanos.", raya]
    assert [e.id for e in caps[1].escenas] == ["e3"]
