"""`PLAN-27` E4: el libro como dato, antes de ningun PDF.

Portada, capitulos en orden de lectura con el texto de E1, y fichas de personaje
(`participa_en`) y de lugar (`ocurre_en`). **Sin estados ni hallazgos** (`SPEC-27`
`RF-06`). Datos inventados; los `id` van acotados a la obra, como los deja `F-64`.
"""

import dataclasses
import json
import sqlite3

import pytest

from app.features.manuscrito import libro


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE obra (id TEXT PRIMARY KEY, titulo TEXT, dedicatoria TEXT);
        CREATE TABLE capitulo (id TEXT PRIMARY KEY, obra TEXT, orden INT, estado TEXT);
        CREATE TABLE escena (id TEXT PRIMARY KEY, obra TEXT, capitulo TEXT, orden INT,
                             estado TEXT, borrador_aceptado INT, lugar TEXT, pov TEXT,
                             personajes_presentes TEXT);
        CREATE TABLE borrador (escena TEXT, version INT, texto TEXT,
                               PRIMARY KEY (escena, version));
        CREATE TABLE entidad (id TEXT PRIMARY KEY, vital TEXT, lugar TEXT,
                              fecha_de_nacimiento TEXT, nombre_canonico TEXT);
        CREATE TABLE lugar (id TEXT PRIMARY KEY, accesos TEXT, nombre TEXT);
        INSERT INTO obra VALUES ('o1', 'La ruta del gato', 'Para Tula.');
        INSERT INTO capitulo VALUES ('o1-cap-02', 'o1', 2, 'cerrado'),
                                    ('o1-cap-01', 'o1', 1, 'cerrado');
        INSERT INTO entidad VALUES ('o1-per-tula', 'vivo', 'o1-lug-taller', NULL, 'Tula Brenes'),
                                   ('o1-per-gato', 'vivo', 'o1-lug-tejado', NULL, 'Canela'),
                                   ('o1-per-sin', 'vivo', 'o1-lug-taller', NULL, NULL),
                                   ('o2-per-otra', 'vivo', 'o2-lug-x', NULL, 'Otra');
        INSERT INTO lugar VALUES ('o1-lug-taller', '[]', 'El taller'),
                                 ('o1-lug-tejado', '[]', 'El tejado');
    """)
    escenas = [("o1-cap-01-e1", "o1-cap-01", "o1-lug-taller", ["o1-per-tula"],
                "Tula arreglaba una rueda. Pensaba en Canela."),
               ("o1-cap-02-e1", "o1-cap-02", "o1-lug-tejado", ["o1-per-tula", "o1-per-gato"],
                "—¡Canela!— grito Tula desde el tejado.")]
    for id_, cap, lugar, presentes, texto in escenas:
        c.execute("INSERT INTO escena VALUES (?, 'o1', ?, 1, 'consolidada', 1, ?, "
                  "'o1-per-tula', ?)", (id_, cap, lugar, json.dumps(presentes)))
        c.execute("INSERT INTO borrador VALUES (?, 1, ?)", (id_, texto))
    c.commit()
    return c


def _ficha(fichas, id_):
    return next(f for f in fichas if f.id == id_)


def test_un_personaje_aparece_en_los_capitulos_de_las_escenas_en_que_participa(con):
    l = libro.componer(con, "o1")
    assert _ficha(l.personajes, "o1-per-tula").capitulos == [1, 2]
    assert _ficha(l.personajes, "o1-per-gato").capitulos == [2]


def test_una_mencion_en_el_texto_no_cuenta_como_aparecer(con):
    """El capitulo 1 nombra a Canela, pero no esta presente: no aparece ahi."""
    assert 1 not in _ficha(libro.componer(con, "o1").personajes, "o1-per-gato").capitulos


def test_un_lugar_aparece_en_los_capitulos_donde_ocurre_una_escena(con):
    l = libro.componer(con, "o1")
    assert _ficha(l.lugares, "o1-lug-taller").capitulos == [1]
    assert _ficha(l.lugares, "o1-lug-tejado").nombre == "El tejado"


def test_los_capitulos_van_por_su_orden_y_con_el_texto_tal_cual(con):
    l = libro.componer(con, "o1")
    assert [c.numero for c in l.capitulos] == [1, 2]
    assert l.capitulos[1].texto == "—¡Canela!— grito Tula desde el tejado."


def test_presentes_sin_declarar_se_dicen_y_no_se_leen_como_nadie(con):
    with con:
        con.execute("UPDATE escena SET personajes_presentes = NULL")
    l = libro.componer(con, "o1")
    assert _ficha(l.personajes, "o1-per-tula").capitulos is None
    assert l.presentes_sin_declarar


def test_una_entidad_sin_nombre_usa_su_id_y_lo_dice(con):
    f = _ficha(libro.componer(con, "o1").personajes, "o1-per-sin")
    assert f.nombre == "o1-per-sin" and f.nombre_es_el_id


def test_solo_salen_las_entidades_de_la_obra(con):
    assert "o2-per-otra" not in {f.id for f in libro.componer(con, "o1").personajes}


def test_el_libro_no_lleva_estados_ni_hallazgos(con):
    """`RF-06`: el PDF no muestra estados ni hallazgos, asi que el dato no los tiene."""
    nombres = set()

    def recorrer(tipo):
        for f in dataclasses.fields(tipo):
            nombres.add(f.name)
    for tipo in (libro.Libro, libro.CapituloDelLibro, libro.Ficha):
        recorrer(tipo)
    assert not {n for n in nombres if "estado" in n or "hallazgo" in n}


def test_una_escena_sin_texto_impide_componer_el_libro(con):
    with con:
        con.execute("DELETE FROM borrador WHERE escena = 'o1-cap-02-e1'")
    with pytest.raises(libro.LibroIncompleto) as e:
        libro.componer(con, "o1")
    assert "o1-cap-02-e1" in str(e.value)


def test_la_portada_lleva_la_dedicatoria_de_la_obra(con):
    """`PLAN-27` E7: de `Obra.dedicatoria`, no de la ficha."""
    l = libro.componer(con, "o1")
    assert (l.titulo, l.dedicatoria) == ("La ruta del gato", "Para Tula.")


def test_una_obra_sin_dedicatoria_no_inventa_una(con):
    with con:
        con.execute("UPDATE obra SET dedicatoria = NULL")
    assert libro.componer(con, "o1").dedicatoria is None
