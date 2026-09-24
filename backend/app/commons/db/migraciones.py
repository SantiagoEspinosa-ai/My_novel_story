"""Migraciones versionadas de SQLite.

`CLAUDE.md`: "Las migraciones de esquema se versionan. Un cambio en
`docs/definitions.md` que altere un atributo obligatorio necesita su migracion
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
    Migracion(
        7,
        "la memoria se ordena por el discurso y no por el orden de la escena",
        # `F-45`. `resumen.orden` y `ficha.orden` guardaban el `orden` de la
        # escena, que es **local al capitulo**: no ordena nada que cruce el
        # corte, y los resumenes tienen que cruzarlo. Pasan a `t_discurso`.
        #
        # QUE PUEDE Y QUE NO PUEDE ARREGLAR ESTA MIGRACION
        # -------------------------------------------------
        # Renombrar conserva los valores, y en una obra de **un solo capitulo**
        # el valor viejo ya era correcto porque alli `orden` y `t_discurso`
        # coinciden. En una obra de varios **no lo era**, asi que se recalcula
        # desde `escena.t_discurso` cuando consta. Lo que no conste se queda con
        # el valor viejo, que es chapucero y **se dice aqui en vez de fingir que
        # la migracion lo arregla todo**: esas filas hay que regenerarlas.
        lambda con: _migrar_memoria_a_t_discurso(con),
    ),
    Migracion(
        8,
        "la memoria recuerda de que obra es cada resumen y cada ficha",
        # Las columnas `obra` de `resumen` y `ficha` nacieron directamente en el
        # `CREATE TABLE` de la feature, **sin migracion**. Y
        # `CREATE TABLE IF NOT EXISTS` no toca una tabla que ya existe, asi que
        # ninguna base anterior las recibio nunca y **no se arreglaba sola**: al
        # escribir con el codigo de hoy moria con `no such column: obra`.
        #
        # Se midio contra la base de la obra de diez capitulos -60 escenas, 30
        # resumenes-, que no se podia continuar por esto. Es el caso exacto para
        # el que existe `anadir_columnas`, y el recordatorio de que **añadir una
        # columna al `CREATE TABLE` no es migrar**: solo sirve a las bases que
        # todavia no existen.
        lambda con: _migrar_memoria_a_obra(con),
    ),
    Migracion(
        9,
        "la obra guarda su dedicatoria",
        # `SPEC-32` `RF-01`..`RF-03`: es texto de la obra, no dato de la ficha. Se
        # copia al montar y sobrevive al borrado de la ficha al entregar
        # (`SPEC-25` `RF-21`), que es lo que hace falta para que la portada exista
        # despues de entregar. Opcional: una ficha puede no traerla.
        lambda con: anadir_columnas(con, "obra", {"dedicatoria": "TEXT"}),
    ),
    Migracion(
        10,
        "cada traza sabe de que delegacion es",
        # `SPEC-28` `RF-08`, `PLAN-28` E8: enlaza la traza con sus llamadas a tools
        # (`llamada_a_herramienta.delegacion`), para sumar lo que devolvieron sin
        # presupuestarlo. Opcional: una delegacion sin tools no tiene identificador.
        lambda con: anadir_columnas(con, "traza_de_delegacion", {"delegacion": "TEXT"}),
    ),
    Migracion(
        11,
        "personajes y lugares guardan su nombre",
        # `PLAN-27` E2: `Personaje.nombre_canonico` y `Lugar.nombre`, que el dominio ya
        # define y solo vivian en el JSON del plan. Las filas de antes se quedan a
        # `NULL`: no se finge un nombre que nadie guardo.
        lambda con: (anadir_columnas(con, "entidad", {"nombre_canonico": "TEXT"}),
                     anadir_columnas(con, "lugar", {"nombre": "TEXT"})),
    ),
    Migracion(
        12,
        "la obra tiene versiones con identidad, y un capitulo nuevo no pisa al viejo",
        # `SPEC-23` `D-2`, `PLAN-23` A3. Crea `version_de_obra` y
        # `capitulo_de_version`, da la version 1 a cada obra con sus capitulos por
        # `orden`, y recrea `capitulo` **sin** `UNIQUE (obra, orden)`: con esa
        # restriccion y el `INSERT OR REPLACE` del alta, el capitulo 3 de la version
        # 1 desaparecia al escribir el capitulo 3 de la version 2 (hallazgo 4, Regla 7).
        lambda con: _migrar_a_versiones(con),
    ),
    Migracion(
        13,
        "la reverificacion de una escena en una version, con la huella de su estado",
        # `SPEC-23` `D-1`, `PLAN-23` A4. Tabla nueva: no hay filas que migrar, pero
        # `esquema_version` tiene que decir cuando aparecio (`VER-21`).
        lambda con: [con.execute(s) for s in sentencias(REVERIFICACION_SQL)],
    ),
    Migracion(
        14,
        "la peticion de cambio del lector: un hecho o un nombre",
        # `SPEC-23`, `PLAN-23` A7, `C-4`. Tabla nueva, sin filas que migrar.
        lambda con: [con.execute(s) for s in sentencias(PETICION_SQL)],
    ),
    Migracion(
        15,
        "el progreso de una generacion, una fila por cambio de fase",
        # `SPEC-22` `RF-60`, `PLAN-22` E13c: `ProgresoDeGeneracion`. Solo se anade: la
        # ultima fila de una obra es su progreso de hoy, y las anteriores dicen por donde
        # paso. Tabla nueva, asi que no hay filas viejas que rellenar.
        """
        CREATE TABLE IF NOT EXISTS progreso_de_generacion (
            id                 INTEGER PRIMARY KEY AUTOINCREMENT,
            obra               TEXT NOT NULL,
            fase               TEXT NOT NULL,
            capitulo           INTEGER,
            total_de_capitulos INTEGER,
            motivo             TEXT,
            desde              TEXT NOT NULL DEFAULT (datetime('now'))
        );
        CREATE INDEX IF NOT EXISTS idx_progreso_por_obra ON progreso_de_generacion (obra, id);
        """,
    ),
    Migracion(
        16,
        "cada veredicto de la puerta es de una version, y las rondas se cuentan por version",
        # `PLAN-23` B-S1.1, `F-122` (TLC `CE-15`): con la clave `(obra, ronda)` la version
        # 2 heredaba las rondas que la 1 gasto para publicarse, y se detenia por tope sin
        # haber gastado las suyas. Se recrea la tabla con clave `(obra, version, ronda)`.
        # Las filas de antes son **de la version 1**, y no es un supuesto: hasta esta
        # migracion `regeneracion.RAMAS` estaba vacio, asi que ninguna version 2 pudo
        # escribirse ni pasar por la puerta.
        lambda con: _migrar_veredictos_a_version(con),
    ),
]

# `PLAN-23` A3. Vive aqui y no en `features/brief/` porque la necesitan los dos: la
# migracion, que no puede importar de una feature (`VER-14`), y `brief.asegurar_tablas`.
# Una sola copia: dos `CREATE TABLE` de la misma tabla acaban divergiendo.
#
# **Una version creada no cambia** (`VersionesSoloCrecen` de `specs/tla/`, en la
# base): los disparadores abortan cualquier `UPDATE` o `DELETE`.
VERSIONES_SQL = """
CREATE TABLE IF NOT EXISTS version_de_obra (
    obra      TEXT    NOT NULL,
    numero    INTEGER NOT NULL,
    anterior  INTEGER,
    peticion  INTEGER,
    "commit"  TEXT    NOT NULL,
    creada_en TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (obra, numero)
);
CREATE TABLE IF NOT EXISTS capitulo_de_version (
    obra     TEXT    NOT NULL,
    numero   INTEGER NOT NULL,
    orden    INTEGER NOT NULL,
    capitulo TEXT    NOT NULL,
    PRIMARY KEY (obra, numero, orden)
);
CREATE TRIGGER IF NOT EXISTS version_de_obra_no_se_modifica
    BEFORE UPDATE ON version_de_obra
    BEGIN SELECT RAISE(ABORT, 'una version creada no cambia'); END;
CREATE TRIGGER IF NOT EXISTS version_de_obra_no_se_borra
    BEFORE DELETE ON version_de_obra
    BEGIN SELECT RAISE(ABORT, 'una version creada no cambia'); END;
CREATE TRIGGER IF NOT EXISTS capitulo_de_version_no_se_modifica
    BEFORE UPDATE ON capitulo_de_version
    BEGIN SELECT RAISE(ABORT, 'una version creada no cambia'); END;
CREATE TRIGGER IF NOT EXISTS capitulo_de_version_no_se_borra
    BEFORE DELETE ON capitulo_de_version
    BEGIN SELECT RAISE(ABORT, 'una version creada no cambia'); END;
"""


# `PLAN-23` A4. Aqui por lo mismo que `VERSIONES_SQL`: una sola copia para la migracion
# y para `features/verificacion/`. **No son filas de `hallazgo`**, que no sabe de
# versiones: un fallo de reverificacion de un capitulo compartido apareceria tambien en
# la version anterior, y esa dejaria de poder cerrarse (hallazgo 7).
REVERIFICACION_SQL = """
CREATE TABLE IF NOT EXISTS reverificacion (
    obra              TEXT    NOT NULL,
    version           INTEGER NOT NULL,
    escena            TEXT    NOT NULL,
    huella_del_estado TEXT    NOT NULL,
    estado            TEXT    NOT NULL,
    hallazgos         TEXT    NOT NULL DEFAULT '[]',
    cuando            TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (obra, version, escena, huella_del_estado)
);
"""


# `PLAN-23` A7. Una sola copia, como las dos de arriba. `capitulos_propuestos` es la
# lista que el lector acepto, en JSON: la que se comparo con la propuesta.
PETICION_SQL = """
CREATE TABLE IF NOT EXISTS peticion_de_cambio (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    obra                 TEXT    NOT NULL,
    version_de_partida   INTEGER NOT NULL,
    clase                TEXT    NOT NULL,
    hecho                TEXT,
    enunciado_nuevo      TEXT,
    personaje            TEXT,
    nombre_nuevo         TEXT,
    texto                TEXT    NOT NULL,
    salida               TEXT,
    capitulos_propuestos TEXT    NOT NULL DEFAULT '[]',
    creada_en            TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


# `PLAN-23` B-S1.1, `F-122`. Aqui por lo mismo que `VERSIONES_SQL`: una sola copia para
# la migracion 16 y para `features/auditoria/`.
VEREDICTO_SQL = """
CREATE TABLE IF NOT EXISTS veredicto_de_publicacion (
    obra          TEXT    NOT NULL,
    version       INTEGER NOT NULL DEFAULT 1,
    ronda         INTEGER NOT NULL,
    publica       INTEGER NOT NULL,
    condiciones   TEXT    NOT NULL,
    codigo_lean   INTEGER,
    no_ejecutadas TEXT    NOT NULL,
    cuando        TEXT    NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (obra, version, ronda)
);
"""


def _migrar_veredictos_a_version(con):
    if not tiene_tabla(con, "veredicto_de_publicacion"):
        return 0
    columnas = {f[1] for f in con.execute("PRAGMA table_info(veredicto_de_publicacion)")}
    if "version" in columnas:
        return 0
    con.execute("ALTER TABLE veredicto_de_publicacion RENAME TO veredicto_sin_version")
    for sentencia in sentencias(VEREDICTO_SQL):
        con.execute(sentencia)
    con.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
                "condiciones, codigo_lean, no_ejecutadas, cuando) "
                "SELECT obra, 1, ronda, publica, condiciones, codigo_lean, no_ejecutadas, "
                "cuando FROM veredicto_sin_version")
    con.execute("DROP TABLE veredicto_sin_version")
    return 1


def sentencias(script):
    """Parte un script en sentencias completas, disparadores incluidos.

    `executescript` haria `COMMIT` en mitad de la transaccion de la migracion, y
    partir por `;` rompe un disparador, que lleva `;` dentro de su `BEGIN ... END`.
    """
    actual = ""
    for linea in script.splitlines(keepends=True):
        actual += linea
        if sqlite3.complete_statement(actual):
            if actual.strip():
                yield actual
            actual = ""


def _crear_versiones(con):
    for sentencia in sentencias(VERSIONES_SQL):
        con.execute(sentencia)


def _migrar_a_versiones(con):
    _crear_versiones(con)
    if not tiene_tabla(con, "capitulo"):
        return 0
    con.execute("""
        CREATE TABLE capitulo_nuevo (
            id     TEXT PRIMARY KEY,
            obra   TEXT NOT NULL REFERENCES obra(id),
            orden  INTEGER NOT NULL,
            estado TEXT NOT NULL DEFAULT 'abierto'
        )""")
    con.execute("INSERT INTO capitulo_nuevo (id, obra, orden, estado) "
                "SELECT id, obra, orden, estado FROM capitulo")
    con.execute("DROP TABLE capitulo")
    con.execute("ALTER TABLE capitulo_nuevo RENAME TO capitulo")
    # El commit de la version 1 de una obra ya escrita es el de la base, si consta.
    # Si no, `sin_determinar`: la version existe y no se sabe con que codigo se hizo.
    commit = "sin_determinar"
    if tiene_tabla(con, "procedencia"):
        fila = con.execute("SELECT valor FROM procedencia "
                           "WHERE clave = 'version_del_harness'").fetchone()
        commit = fila[0] if fila else commit
    obras = [f[0] for f in con.execute("SELECT DISTINCT obra FROM capitulo ORDER BY obra")]
    for obra in obras:
        if con.execute("SELECT 1 FROM version_de_obra WHERE obra = ?", (obra,)).fetchone():
            continue
        con.execute('INSERT INTO version_de_obra (obra, numero, "commit") VALUES (?, 1, ?)',
                    (obra, commit))
        capitulos = [f[0] for f in con.execute(
            "SELECT id FROM capitulo WHERE obra = ? ORDER BY orden, id", (obra,))]
        for orden, capitulo in enumerate(capitulos, 1):
            con.execute("INSERT INTO capitulo_de_version (obra, numero, orden, capitulo) "
                        "VALUES (?, 1, ?, ?)", (obra, orden, capitulo))
    return len(obras)


def _migrar_memoria_a_obra(con):
    """Añade `obra` a `resumen` y `ficha`, **y rellena lo que ya habia**.

    Dejarla vacia habria sido peor que no añadirla: `resumenes_hasta` acota por
    obra, asi que una fila sin ella **no la ve ninguna consulta**. Los treinta
    resumenes de la obra de diez capitulos habrian quedado invisibles y cada
    escena habria arrancado sin memoria **sin que nada fallara** — la Regla 8
    entrando por la puerta de una migracion.

    Se puede rellenar porque el dato existe en otro sitio: `resumen.escena` y
    `ficha.version_en_t` son los dos el identificador de la escena, y la escena
    sabe de que obra es.
    """
    anadidas = (anadir_columnas(con, "resumen", {"obra": "TEXT"})
                + anadir_columnas(con, "ficha", {"obra": "TEXT"}))
    if not tiene_tabla(con, "escena"):
        return anadidas
    for tabla, columna in (("resumen", "escena"), ("ficha", "version_en_t")):
        if not tiene_tabla(con, tabla):
            continue
        con.execute(
            "UPDATE {0} SET obra = ("
            "  SELECT e.obra FROM escena e WHERE e.id = {0}.{1}"
            ") WHERE obra IS NULL AND EXISTS ("
            "  SELECT 1 FROM escena e WHERE e.id = {0}.{1} "
            "  AND e.obra IS NOT NULL)".format(tabla, columna))
    return anadidas


def _migrar_memoria_a_t_discurso(con):
    """Renombra `orden` a `t_discurso` y recalcula lo que se pueda."""
    for tabla in ("resumen", "ficha"):
        if not tiene_tabla(con, tabla):
            continue
        columnas = {f[1] for f in con.execute("PRAGMA table_info({0})".format(tabla))}
        if "orden" in columnas and "t_discurso" not in columnas:
            con.execute(
                "ALTER TABLE {0} RENAME COLUMN orden TO t_discurso".format(tabla))
    if not tiene_tabla(con, "escena"):
        return 0
    # `resumen.escena` y `ficha.version_en_t` son los dos el id de la escena.
    recalculadas = 0
    for tabla, columna in (("resumen", "escena"), ("ficha", "version_en_t")):
        if not tiene_tabla(con, tabla):
            continue
        cur = con.execute(
            "UPDATE {0} SET t_discurso = ("
            "  SELECT e.t_discurso FROM escena e WHERE e.id = {0}.{1}"
            ") WHERE EXISTS ("
            "  SELECT 1 FROM escena e WHERE e.id = {0}.{1} "
            "  AND e.t_discurso IS NOT NULL)".format(tabla, columna))
        recalculadas += cur.rowcount
    return recalculadas


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
