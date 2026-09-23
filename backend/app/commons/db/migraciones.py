"""Migraciones versionadas de SQLite.

`CLAUDE.md`: "Las migraciones de esquema se versionan. Un cambio en
`Docs/definitions.md` que altere un atributo obligatorio necesita su migracion
en el mismo commit." `VER-21` comprueba la segunda mitad cruzando commits;
este modulo sostiene la primera.

POR QUE UNA TABLA DE VERSION Y NO `PRAGMA user_version`
-------------------------------------------------------
`user_version` es un entero suelto: dice en que version esta la base y no dice
cuando se aplico ninguna. Una tabla cuesta lo mismo y deja rastro, y aqui el
rastro importa: una base que no sabe cuando se migro no se puede reconciliar
con el historial de commits que `VER-21` recorre.

POR QUE LAS VERSIONES NO PUEDEN TENER HUECOS
---------------------------------------------
Un hueco significa que alguien borro una migracion ya publicada. Las bases que
la aplicaron y las que no dejan de ser distinguibles, y a partir de ahi el
numero de version miente. Es la misma regla que gobierna los identificadores
del proyecto: lo que se publica no se borra ni se renumera.
"""

import sqlite3
from collections.abc import Callable
from dataclasses import dataclass


def tiene_tabla(con: sqlite3.Connection, tabla: str) -> bool:
    return con.execute(
        "SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (tabla,)
    ).fetchone() is not None


def anadir_columnas(con: sqlite3.Connection, tabla: str, columnas: dict) -> int:
    """Añade las que falten y devuelve cuantas añadio. Nunca falla por repetir.

    Si la tabla no existe devuelve 0: la creara su feature, ya con las columnas
    nuevas, porque el `CREATE TABLE` de la feature es el esquema al dia. Migrar
    lo que no hay no es un error, es que no habia nada que migrar.
    """
    if not tiene_tabla(con, tabla):
        return 0
    ya = {f[1] for f in con.execute("PRAGMA table_info({0})".format(tabla))}
    anadidas = 0
    for nombre, tipo in columnas.items():
        if nombre in ya:
            continue
        con.execute("ALTER TABLE {0} ADD COLUMN {1} {2}".format(tabla, nombre, tipo))
        anadidas += 1
    return anadidas


@dataclass(frozen=True)
class Migracion:
    """`sql` es un script, o una funcion que recibe la conexion.

    POR QUE UNA MIGRACION PUEDE SER UNA FUNCION
    --------------------------------------------
    Porque `ALTER TABLE ... ADD COLUMN` **no es idempotente en SQLite** y no
    existe `IF NOT EXISTS` para columnas. Y aqui las tablas no las crea el
    migrador: las crea cada feature con `CREATE TABLE IF NOT EXISTS` cuando le
    hace falta. Eso deja dos situaciones que un script suelto no sabe cubrir a
    la vez: la tabla todavia no existe -no hay nada que migrar, y eso no es un
    error- o la feature ya la creo con las columnas nuevas, y repetir el
    `ALTER` da `duplicate column name` y deja la base sin migrar de ahi en
    adelante.

    Decidirlo requiere **leer el esquema antes de escribirlo**, y eso es una
    consulta, no una sentencia. La alternativa -recrear la tabla entera, como
    hace la migracion 2- funciona cuando las dos formas tienen las mismas
    columnas, y aqui no las tienen: copiaria la tabla perdiendo por el camino
    justo las columnas nuevas.
    """

    version: int
    descripcion: str
    sql: str | Callable[[sqlite3.Connection], None]


# Ninguna clase del dominio tiene todavia tabla: llegan con la feature que las
# usa. Lo que existe desde el primer dia es el registro de versiones, porque
# sin el no se puede aplicar la segunda.
TODAS = [
    Migracion(
        1,
        "registro de versiones de esquema",
        """
        CREATE TABLE IF NOT EXISTS esquema_version (
            version     INTEGER PRIMARY KEY,
            descripcion TEXT    NOT NULL,
            aplicada_en TEXT    NOT NULL DEFAULT (datetime('now'))
        );
        """,
    ),
    Migracion(
        2,
        "el conocimiento anterior al relato no tiene escena de origen",
        # `SPEC-17` C-2. La tabla la crea `features/consolidacion/` con
        # `CREATE TABLE IF NOT EXISTS`, asi que una base nueva ya nace bien;
        # esta migracion existe para las que ya tenian la version con
        # `desde_escena NOT NULL`. SQLite no sabe quitar un `NOT NULL` con
        # `ALTER`, asi que se recrea la tabla y se copia, que es el camino que
        # su propia documentacion recomienda.
        """
        CREATE TABLE IF NOT EXISTS conocimiento (
            sujeto       TEXT NOT NULL,
            hecho        TEXT NOT NULL,
            desde_escena TEXT NOT NULL,
            grado        TEXT NOT NULL DEFAULT 'sabe',
            fuente       TEXT,
            PRIMARY KEY (sujeto, hecho)
        );
        CREATE TABLE conocimiento_nuevo (
            sujeto       TEXT NOT NULL,
            hecho        TEXT NOT NULL,
            desde_escena TEXT,
            grado        TEXT NOT NULL DEFAULT 'sabe',
            fuente       TEXT,
            PRIMARY KEY (sujeto, hecho)
        );
        INSERT INTO conocimiento_nuevo SELECT * FROM conocimiento;
        DROP TABLE conocimiento;
        ALTER TABLE conocimiento_nuevo RENAME TO conocimiento;
        """,
    ),
    Migracion(
        3,
        "la escena guarda su capitulo y su momento narrativo",
        # `SPEC-21` C-1. Las cinco nacen NULL a proposito: las escaletas
        # anteriores no traen ninguna, y un NULL se puede ver -y decir-
        # mientras que un valor por defecto inventado se lee como un dato.
        lambda con: (
            anadir_columnas(con, "escena", {
                "capitulo": "TEXT",
                "t_fabula": "TEXT",
                "t_discurso": "INTEGER",
                "duracion_ficcional": "INTEGER",
                "personajes_presentes": "TEXT",
            }),
            con.execute("CREATE INDEX IF NOT EXISTS idx_escena_capitulo "
                        "ON escena (capitulo, orden)")
            if tiene_tabla(con, "escena") else None,
        ),
    ),
    Migracion(
        4,
        "el personaje guarda su fecha de nacimiento",
        # `SPEC-21` C-3. Opcional: obligatoria romperia todas las obras ya
        # generadas. Como es opcional, quien no la tenga **no pasa** la
        # comprobacion de edad: la salta, y la consulta lo dice por separado.
        lambda con: anadir_columnas(
            con, "entidad", {"fecha_de_nacimiento": "TEXT"}),
    ),
    Migracion(
        5,
        "el hecho canonico se identifica por obra e id, no por id solo",
        # `F-39`. `hechos_declarados` filtra por obra, asi que el codigo ya
        # trataba el mismo identificador en dos obras como dos hechos; la clave
        # global decia lo contrario y el segundo declarar **pisaba** al
        # primero, dejando a la obra anterior sin ningun hecho. SQLite no sabe
        # cambiar una PRIMARY KEY con ALTER, asi que se recrea y se copia.
        """
        CREATE TABLE IF NOT EXISTS hecho_canonico (
            id                      TEXT PRIMARY KEY,
            obra                    TEXT NOT NULL,
            enunciado               TEXT NOT NULL,
            durabilidad             TEXT NOT NULL DEFAULT 'permanente',
            escena_de_establecimiento TEXT,
            previsto_en             TEXT
        );
        CREATE TABLE hecho_canonico_nuevo (
            id                      TEXT NOT NULL,
            obra                    TEXT NOT NULL,
            enunciado               TEXT NOT NULL,
            durabilidad             TEXT NOT NULL DEFAULT 'permanente',
            escena_de_establecimiento TEXT,
            previsto_en             TEXT,
            PRIMARY KEY (obra, id)
        );
        INSERT INTO hecho_canonico_nuevo
            SELECT id, obra, enunciado, durabilidad,
                   escena_de_establecimiento, previsto_en
            FROM hecho_canonico;
        DROP TABLE hecho_canonico;
        ALTER TABLE hecho_canonico_nuevo RENAME TO hecho_canonico;
        """,
    ),
    Migracion(
        6,
        "el uso de un hecho se identifica tambien por su origen",
        # `SPEC-21` C-2. La clave era `(hecho, escena, tipo)` y dejaba fuera el
        # origen, asi que un `depende` **observado** y uno **declarado** sobre
        # el mismo par no cabian a la vez: el segundo pisaba al primero y cual
        # sobrevivia dependia del orden de escritura. Eso borra la distincion
        # que `origen_de_uso` existe para guardar, y la borra en silencio.
        #
        # Importa mas de lo que parece: `SPEC-23` compara las dos formas de
        # saber de que depende una escena y deja escrito que, si hubiera que
        # elegir, la correcta es la observada -sobre-aproxima y falla ruidoso-.
        # Mientras las dos filas quepan, esa eleccion sigue siendo editar una
        # constante; sin esta migracion, seria volver a decidirla.
        #
        # SQLite no sabe cambiar una PRIMARY KEY con ALTER, asi que se recrea y
        # se copia. `INSERT OR IGNORE` porque la tabla vieja no pudo guardar
        # duplicados: lo que hay ya es unico bajo la clave nueva.
        """
        CREATE TABLE IF NOT EXISTS uso_de_hecho (
            hecho    TEXT NOT NULL,
            escena   TEXT NOT NULL,
            capitulo TEXT,
            tipo     TEXT NOT NULL,
            origen   TEXT NOT NULL,
            PRIMARY KEY (hecho, escena, tipo)
        );
        CREATE TABLE uso_de_hecho_nuevo (
            hecho    TEXT NOT NULL,
            escena   TEXT NOT NULL,
            capitulo TEXT,
            tipo     TEXT NOT NULL,
            origen   TEXT NOT NULL,
            PRIMARY KEY (hecho, escena, tipo, origen)
        );
        INSERT OR IGNORE INTO uso_de_hecho_nuevo
            SELECT hecho, escena, capitulo, tipo, origen FROM uso_de_hecho;
        DROP TABLE uso_de_hecho;
        ALTER TABLE uso_de_hecho_nuevo RENAME TO uso_de_hecho;
        CREATE INDEX IF NOT EXISTS idx_uso_por_hecho ON uso_de_hecho (hecho, tipo);
        CREATE INDEX IF NOT EXISTS idx_uso_por_capitulo ON uso_de_hecho (capitulo, tipo);
        """,
    ),
]


def validar_secuencia(migraciones):
    """Las versiones son consecutivas desde 1 y no se repiten.

    Se comprueba en cada arranque y no solo en las pruebas: una migracion mal
    numerada que llega en un despliegue es peor que una que falla en CI.
    """
    vistas = set()
    for m in migraciones:
        if m.version in vistas:
            raise ValueError(
                "version {0} repetida: dos migraciones no pueden compartir "
                "numero, porque entonces la version aplicada no dice cual se "
                "aplico".format(m.version)
            )
        vistas.add(m.version)
    esperadas = set(range(1, len(migraciones) + 1))
    if vistas != esperadas:
        raise ValueError(
            "hueco en la secuencia de migraciones: se esperaba {0} y hay {1}. "
            "Un hueco significa que se borro una migracion publicada".format(
                sorted(esperadas), sorted(vistas)
            )
        )
    return True


validar_secuencia(TODAS)
ULTIMA_VERSION = max(m.version for m in TODAS)


def version_aplicada(con: sqlite3.Connection) -> int:
    """0 si la base es nueva. No crea nada: preguntar no es migrar."""
    fila = con.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='esquema_version'"
    ).fetchone()
    if fila is None:
        return 0
    fila = con.execute("SELECT MAX(version) FROM esquema_version").fetchone()
    return fila[0] or 0


def migrar(con: sqlite3.Connection) -> int:
    """Aplica lo que falte y devuelve cuantas migraciones se aplicaron.

    Cada migracion va **en su propia transaccion**: si la tercera falla, la
    primera y la segunda siguen aplicadas y la version lo refleja. Lo contrario
    -una transaccion para todas- dejaria la base en un estado que la version no
    describe, que es el mismo problema del delta a medias de `SPEC-07`.
    """
    validar_secuencia(TODAS)
    desde = version_aplicada(con)
    aplicadas = 0
    for m in sorted(TODAS, key=lambda x: x.version):
        if m.version <= desde:
            continue
        with con:
            if callable(m.sql):
                m.sql(con)
            else:
                con.executescript(m.sql)
            con.execute(
                "INSERT INTO esquema_version (version, descripcion) VALUES (?, ?)",
                (m.version, m.descripcion),
            )
        aplicadas += 1
    return aplicadas
