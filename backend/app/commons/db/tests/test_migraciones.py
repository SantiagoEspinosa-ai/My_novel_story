"""A3 — Las migraciones se versionan, y eso se comprueba.

`CLAUDE.md` y `D-5` de `SPEC-01`:

    "Las migraciones de esquema se versionan. Un cambio en
     `docs/definitions.md` que altere un atributo obligatorio necesita su
     migracion en el mismo commit."

La segunda mitad es la que `VER-21` comprueba y la que esta prueba sostiene:
sin version aplicada registrada, una base no sabe en que esquema esta y la
siguiente migracion se aplica sobre un supuesto.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.consolidacion import aplicar
from app.features.escaleta import repository as repo


def test_una_base_nueva_arranca_sin_version():
    con = sqlite3.connect(":memory:")
    assert migraciones.version_aplicada(con) == 0


def test_migrar_deja_la_base_en_la_ultima_version():
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    assert migraciones.version_aplicada(con) == migraciones.ULTIMA_VERSION
    assert migraciones.ULTIMA_VERSION >= 1


def test_migrar_dos_veces_no_hace_nada_la_segunda():
    """Reanudar una base ya migrada no puede romperla."""
    con = sqlite3.connect(":memory:")
    aplicadas = migraciones.migrar(con)
    assert aplicadas == migraciones.ULTIMA_VERSION
    assert migraciones.migrar(con) == 0


def test_las_versiones_son_consecutivas_y_sin_huecos():
    """Un hueco significa que alguien borro una migracion publicada."""
    versiones = sorted(m.version for m in migraciones.TODAS)
    assert versiones == list(range(1, migraciones.ULTIMA_VERSION + 1))


def test_caso_negativo_una_migracion_con_version_repetida():
    """El caso negativo de `VER-21`: dos migraciones no pueden compartir numero."""
    with pytest.raises(ValueError, match="repetida"):
        migraciones.validar_secuencia(
            [
                migraciones.Migracion(1, "crea algo", "SELECT 1"),
                migraciones.Migracion(1, "crea otra cosa", "SELECT 1"),
            ]
        )


def test_caso_negativo_un_hueco_en_la_secuencia():
    with pytest.raises(ValueError, match="hueco"):
        migraciones.validar_secuencia(
            [
                migraciones.Migracion(1, "crea algo", "SELECT 1"),
                migraciones.Migracion(3, "crea otra cosa", "SELECT 1"),
            ]
        )


def test_la_migracion_2_permite_conocimiento_anterior_al_relato():
    """`SPEC-17` C-2: `desde_escena` pierde su `NOT NULL`, porque lo que se sabe
    desde antes de la escena 1 no tiene escena de origen. Es la primera
    migracion del proyecto que no es gratis."""
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    assert migraciones.version_aplicada(con) >= 2
    con.execute("INSERT INTO conocimiento (sujeto, hecho, desde_escena, grado, "
                "fuente) VALUES ('per-ana', 'hec-1', NULL, 'sabe', "
                "'anterior_al_relato')")
    assert con.execute("SELECT desde_escena FROM conocimiento").fetchone()[0] is None


# --- `SPEC-21`: una migracion que añade columnas tiene que ser idempotente --


def test_anadir_columnas_funciona_si_la_tabla_no_existe_todavia():
    """Las tablas las crea su feature con `CREATE TABLE IF NOT EXISTS`, asi que
    al migrar una base nueva la tabla puede no existir. La migracion no puede
    reventar por eso: no hay nada que migrar, y eso no es un error."""
    con = sqlite3.connect(":memory:")
    assert migraciones.anadir_columnas(con, "escena", {"capitulo": "TEXT"}) == 0


def test_anadir_columnas_no_falla_si_la_columna_ya_esta():
    """El caso que rompe un `ALTER TABLE ADD COLUMN` a secas.

    Si la feature creo la tabla ya con la columna -una instalacion nueva en la
    que el repositorio corrio antes que el migrador-, repetir el `ALTER` da
    `duplicate column name` y deja la base sin migrar a partir de ahi.
    """
    con = sqlite3.connect(":memory:")
    con.execute("CREATE TABLE escena (id TEXT, capitulo TEXT)")
    assert migraciones.anadir_columnas(con, "escena", {"capitulo": "TEXT"}) == 0
    assert migraciones.anadir_columnas(
        con, "escena", {"capitulo": "TEXT", "t_fabula": "TEXT"}) == 1


def test_migrar_dos_veces_seguidas_con_las_tablas_ya_creadas():
    """La base completa: features primero, migrador despues, dos veces."""
    con = sqlite3.connect(":memory:")
    repo.asegurar_tablas(con)
    aplicar.asegurar_tablas(con)
    migraciones.migrar(con)
    assert migraciones.migrar(con) == 0
    assert migraciones.version_aplicada(con) == migraciones.ULTIMA_VERSION


def test_una_base_anterior_a_las_columnas_obra_se_puede_migrar():
    """Las columnas `obra` de `resumen` y `ficha` nacieron en el `CREATE TABLE`
    y **sin migracion**, asi que toda base creada antes se quedaba sin ellas.

    `CREATE TABLE IF NOT EXISTS` no toca una tabla que ya existe, de modo que la
    base no se arreglaba sola nunca, y el codigo de hoy moria al escribir con un
    `no such column: obra`. Se midio contra la base de la obra de diez
    capitulos: 60 escenas y 30 resumenes que no se podian continuar.
    """
    con = sqlite3.connect(":memory:")
    # La forma **anterior**, tal como quedo en las bases de entonces.
    con.executescript("""
        CREATE TABLE resumen (escena TEXT NOT NULL, orden INTEGER NOT NULL,
            version_en_t TEXT NOT NULL, nivel TEXT NOT NULL, texto TEXT NOT NULL,
            hechos_clave TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (escena, version_en_t));
        CREATE TABLE ficha (entidad TEXT NOT NULL, orden INTEGER NOT NULL,
            version_en_t TEXT NOT NULL, resumen TEXT NOT NULL,
            PRIMARY KEY (entidad, version_en_t));
    """)
    # Y una escena que dice de que obra es, para poder rellenar lo de antes.
    con.executescript("""
        CREATE TABLE escena (id TEXT PRIMARY KEY, obra TEXT, orden INTEGER,
            t_discurso INTEGER);
        INSERT INTO escena VALUES ('e1', 'obra-1', 1, 4);
        INSERT INTO resumen VALUES ('e1', 1, 'e1', 'escena', 'texto', '[]');
        INSERT INTO ficha VALUES ('ent-1', 1, 'e1', 'ficha');
    """)
    migraciones.migrar(con)
    for tabla in ("resumen", "ficha"):
        columnas = {f[1] for f in con.execute("PRAGMA table_info({0})".format(tabla))}
        assert "obra" in columnas, "{0} sigue sin `obra`".format(tabla)
        assert "t_discurso" in columnas


def test_al_añadir_obra_se_rellena_lo_que_ya_habia():
    """Añadir la columna y dejarla vacia habria sido peor que no añadirla.

    `resumenes_hasta` acota por obra, asi que una fila con `obra` vacia **no la
    ve ninguna consulta**: los treinta resumenes de la obra de diez capitulos
    habrian quedado invisibles y cada escena habria arrancado sin memoria, sin
    que nada fallara. Es la Regla 8 entrando por la puerta de una migracion.

    Se puede rellenar porque el dato existe: `resumen.escena` y
    `ficha.version_en_t` son los dos el identificador de la escena, y la escena
    sabe de que obra es.
    """
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE resumen (escena TEXT NOT NULL, orden INTEGER NOT NULL,
            version_en_t TEXT NOT NULL, nivel TEXT NOT NULL, texto TEXT NOT NULL,
            hechos_clave TEXT NOT NULL DEFAULT '[]',
            PRIMARY KEY (escena, version_en_t));
        CREATE TABLE ficha (entidad TEXT NOT NULL, orden INTEGER NOT NULL,
            version_en_t TEXT NOT NULL, resumen TEXT NOT NULL,
            PRIMARY KEY (entidad, version_en_t));
        CREATE TABLE escena (id TEXT PRIMARY KEY, obra TEXT, orden INTEGER,
            t_discurso INTEGER);
        INSERT INTO escena VALUES ('e1', 'obra-1', 1, 1);
        INSERT INTO resumen VALUES ('e1', 1, 'e1', 'escena', 'texto', '[]');
        INSERT INTO ficha VALUES ('ent-1', 1, 'e1', 'ficha');
    """)
    migraciones.migrar(con)
    assert con.execute("SELECT obra FROM resumen").fetchone()[0] == "obra-1"
    assert con.execute("SELECT obra FROM ficha").fetchone()[0] == "obra-1"


def test_la_migracion_anade_dedicatoria_a_una_base_anterior():
    """`SPEC-32` `RF-01`: `Obra.dedicatoria`. Una base de antes, con obras ya
    dadas de alta, gana la columna sin perder filas (la leccion de `F-51`: añadir
    la columna al `CREATE TABLE` solo sirve a las bases que no existen)."""
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE obra (id TEXT PRIMARY KEY, titulo TEXT NOT NULL,
            premisa TEXT NOT NULL, genero TEXT, subgenero TEXT,
            extension_objetivo INTEGER, guia_de_estilo TEXT);
        INSERT INTO obra (id, titulo, premisa) VALUES ('obra-vieja', 'T', 'P');
    """)
    migraciones.migrar(con)
    columnas = {f[1] for f in con.execute("PRAGMA table_info(obra)")}
    assert "dedicatoria" in columnas
    assert con.execute("SELECT titulo, dedicatoria FROM obra").fetchone() == ("T", None)


def test_la_migracion_anade_delegacion_a_una_base_anterior():
    """`PLAN-28` E8: cada traza sabe de que delegacion es, para enlazarla con sus
    llamadas a tools. Una columna en una tabla que ya existe se migra (`F-51`)."""
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE traza_de_delegacion (escena TEXT NOT NULL, agente TEXT NOT NULL,
            prompt_hash TEXT NOT NULL DEFAULT '', trabajo TEXT, modelo TEXT,
            modelos TEXT NOT NULL DEFAULT '[]', recortes TEXT NOT NULL DEFAULT '[]',
            fichas TEXT NOT NULL DEFAULT '[]', tokens_para_recortar INTEGER,
            tokens_estimados INTEGER, resultado TEXT, clase_de_fallo TEXT,
            salida_fallida TEXT, cuando TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (escena, agente, prompt_hash));
        INSERT INTO traza_de_delegacion (escena, agente) VALUES ('e1', 'escritor');
    """)
    migraciones.migrar(con)
    columnas = {f[1] for f in con.execute("PRAGMA table_info(traza_de_delegacion)")}
    assert "delegacion" in columnas
    assert con.execute("SELECT agente, delegacion FROM traza_de_delegacion").fetchone() \
        == ("escritor", None)
