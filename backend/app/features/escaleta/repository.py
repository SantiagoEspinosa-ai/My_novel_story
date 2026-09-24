"""Persistencia de la escaleta, los borradores y los hallazgos.

`Borrador.version` crece **por escena y no globalmente**: la version 3 de la
escena 7 no tiene nada que ver con la version 3 de la escena 2, y numerarlas en
comun haria imposible leer "esta escena necesito cuatro intentos", que es una
de las señales que la otra rama identifico como mas utiles al interpretar un
informe.

`Escena.intentos` no se guarda aparte: es el numero de borradores. Un contador
que se lleva al lado de lo que cuenta se desincroniza en cuanto un camino de
codigo olvida incrementarlo.
"""

import json
import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad

SQL = """
CREATE TABLE IF NOT EXISTS escena (
    id                 TEXT PRIMARY KEY,
    obra               TEXT NOT NULL,
    orden              INTEGER NOT NULL,
    estado             TEXT NOT NULL,
    cambio_de_valor    TEXT NOT NULL,
    beats              TEXT NOT NULL,
    pov                TEXT NOT NULL,
    lugar              TEXT NOT NULL,
    longitud_objetivo  TEXT,
    borrador_aceptado  INTEGER,
    -- `SPEC-21` C-1. `capitulo` materializa la relacion `contiene`, que estaba
    -- en la tabla de relaciones y no existia en ninguna tabla. Las tres
    -- siguientes son `MomentoNarrativo`, atributo **obligatorio** de `Escena`
    -- desde el primer dia y hasta ahora inexpresable. Nacen NULL porque las
    -- escaletas anteriores no los traen, y un NULL se puede ver; un valor por
    -- defecto inventado, no.
    capitulo             TEXT,
    t_fabula             TEXT,
    t_discurso           INTEGER,
    duracion_ficcional   INTEGER,
    personajes_presentes TEXT
);
CREATE INDEX IF NOT EXISTS idx_escena_capitulo ON escena (capitulo, orden);
CREATE TABLE IF NOT EXISTS borrador (
    escena      TEXT NOT NULL,
    version     INTEGER NOT NULL,
    texto       TEXT NOT NULL,
    modelo      TEXT,
    prompt_hash TEXT,
    PRIMARY KEY (escena, version)
);
CREATE TABLE IF NOT EXISTS hecho_canonico (
    -- La clave es **(obra, id)** y no `id` solo (`F-39`). `hechos_declarados`
    -- filtra por obra, asi que el codigo ya trataba el mismo identificador en
    -- dos obras como dos hechos; la clave global decia lo contrario y el
    -- segundo `INSERT OR REPLACE` **pisaba** al primero. La obra anterior se
    -- quedaba sin ningun hecho y su prompt volvia a decir "hechos: (ninguno)",
    -- que es `F-29` otra vez por una puerta nueva. No fallaba: pisaba.
    id                      TEXT NOT NULL,
    obra                    TEXT NOT NULL,
    enunciado               TEXT NOT NULL,
    durabilidad             TEXT NOT NULL DEFAULT 'permanente',
    escena_de_establecimiento TEXT,
    previsto_en             TEXT,
    PRIMARY KEY (obra, id)
);
CREATE TABLE IF NOT EXISTS hallazgo (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invariante  TEXT NOT NULL,
    verificador TEXT NOT NULL,
    escena      TEXT NOT NULL,
    severidad   TEXT NOT NULL,
    estado      TEXT NOT NULL,
    descripcion TEXT NOT NULL,
    motivo_de_cierre TEXT
);
-- `PLAN-31` E4: la relacion `valorado_en` (`Borrador` -> `ValoracionDelEditor`). Las
-- seis notas de cada version, tambien las que pasan: el hallazgo `INV-26` solo guarda
-- las que bajan del umbral, y como texto.
CREATE TABLE IF NOT EXISTS valoracion_del_editor (
    escena        TEXT NOT NULL,
    version       INTEGER NOT NULL,
    criterio      TEXT NOT NULL,
    nota          INTEGER NOT NULL,
    justificacion TEXT NOT NULL,
    instruccion   TEXT,
    PRIMARY KEY (escena, version, criterio)
);
"""

CUENTAN_COMO_ABIERTOS = (EH.ABIERTO.value, EH.SIN_VEREDICTO.value)


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_escaleta(con, obra, escenas):
    asegurar_tablas(con)
    with con:
        for e in escenas:
            presentes = e.get("personajes_presentes")
            con.execute(
                "INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, "
                "beats, pov, lugar, longitud_objetivo, capitulo, t_fabula, "
                "t_discurso, duracion_ficcional, personajes_presentes) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (e["id"], obra, e["orden"], EE.PLANIFICADA.value,
                 json.dumps(e["cambio_de_valor"]), json.dumps(e["beats"]),
                 e.get("pov"), e.get("lugar"),
                 json.dumps(e.get("longitud_objetivo")),
                 e.get("capitulo"), e.get("t_fabula"), e.get("t_discurso"),
                 e.get("duracion_ficcional"),
                 json.dumps(presentes) if presentes is not None else None),
            )


def declarar_hechos(con, obra, hechos):
    """`SPEC-15`: los `HechoCanonico` los declara el plan, no el texto.

    `escena_de_establecimiento` queda **vacia** hasta que una escena lo
    establezca: es opcional desde `SPEC-15` y significa *donde lo establece el
    texto*, no *donde nacio*. Un hecho declarado y nunca establecido es un
    defecto nombrable, y antes ni siquiera se podia escribir.
    """
    asegurar_tablas(con)
    with con:
        for h in hechos:
            con.execute(
                "INSERT OR REPLACE INTO hecho_canonico (id, obra, enunciado, "
                "durabilidad, previsto_en) VALUES (?, ?, ?, ?, ?)",
                (h["id"], obra, h["enunciado"], h.get("durabilidad", "permanente"),
                 h.get("previsto_en")))


def hechos_declarados(con, obra):
    """Los hechos que el plan declaro. **Esto es lo que va al prompt.**

    Derivar la lista del registro de conocimiento creo un punto muerto: no
    habia hechos hasta que alguien los sabia, y nadie podia saberlos hasta que
    existian (`F-29`). Que hechos existen lo declara el plan; quien los sabe lo
    comprueba `INV-03`.
    """
    asegurar_tablas(con)
    return [{"id": f[0], "enunciado": f[1], "establecido_en": f[2]}
            for f in con.execute(
                "SELECT id, enunciado, escena_de_establecimiento FROM hecho_canonico "
                "WHERE obra = ? ORDER BY id", (obra,))]


def establecer_hecho(con, hecho, escena, obra=None):
    """Marca donde el texto lo establece. Solo la primera vez.

    `obra` acota el alcance: el mismo identificador en dos obras son **dos
    hechos** (`F-39`), y establecerlo en una no dice nada de la otra. Sin el
    filtro, una obra marcaba como establecidos los hechos de las demas.
    """
    with con:
        if obra is None:
            con.execute("UPDATE hecho_canonico SET escena_de_establecimiento = ? "
                        "WHERE id = ? AND escena_de_establecimiento IS NULL",
                        (escena, hecho))
        else:
            con.execute("UPDATE hecho_canonico SET escena_de_establecimiento = ? "
                        "WHERE id = ? AND obra = ? AND "
                        "escena_de_establecimiento IS NULL", (escena, hecho, obra))


# Las columnas de una escena y como se reconstruye la fila viven en un solo
# sitio. Antes estaban copiadas en `escenas_de` y en `escena`, y al añadir las
# cinco de `SPEC-21` habria habido que acertar dos veces: la copia que alguien
# olvide es justo la que lea quien pregunte por el capitulo.
_COLUMNAS = ("id, orden, estado, cambio_de_valor, beats, longitud_objetivo, "
             "borrador_aceptado, pov, lugar, capitulo, t_fabula, t_discurso, "
             "duracion_ficcional, personajes_presentes")


def _fila(f):
    return {"id": f[0], "orden": f[1], "estado": f[2],
            "cambio_de_valor": json.loads(f[3]), "beats": json.loads(f[4]),
            "longitud_objetivo": json.loads(f[5]) if f[5] else None,
            "borrador_aceptado": f[6], "pov": f[7], "lugar": f[8],
            # `capitulo` vacio se devuelve vacio. Sustituirlo por la obra daria
            # una respuesta con forma de capitulo que no es un capitulo.
            "capitulo": f[9], "t_fabula": f[10], "t_discurso": f[11],
            "duracion_ficcional": f[12],
            "personajes_presentes": json.loads(f[13]) if f[13] else None}


def escenas_de(con, obra):
    return [_fila(f) for f in con.execute(
        "SELECT {0} FROM escena WHERE obra = ? ORDER BY orden".format(_COLUMNAS),
        (obra,))]


def escenas_de_capitulo(con, id_capitulo, obra=None):
    """Las escenas de un capitulo, filtrando **por capitulo**.

    `orquestacion/router.py` lo resolvia llamando a `escenas_de`, que filtra
    por obra: con un solo capitulo por obra daba el resultado correcto por
    accidente, y con dos, cerrar el primero miraba las escenas del segundo.
    """
    # `obra` (`PLAN-23` A6): `escena.capitulo` no es clave, y dos obras de la misma base
    # pueden tener un capitulo con el mismo identificador. Quien sabe la obra la da.
    if obra is not None:
        return [_fila(f) for f in con.execute(
            "SELECT {0} FROM escena WHERE capitulo = ? AND obra = ? ORDER BY orden".format(
                _COLUMNAS), (id_capitulo, obra))]
    return [_fila(f) for f in con.execute(
        "SELECT {0} FROM escena WHERE capitulo = ? ORDER BY orden".format(_COLUMNAS),
        (id_capitulo,))]


def asignar_t_discurso(con, obra, orden_de_capitulos=None, escenas=None):
    """Numera el orden de lectura de la obra entera (`F-45`).

    POR QUE `orden` NO SIRVE Y ESTE CAMPO SI
    ------------------------------------------
    `Escena.orden` es **local al capitulo**, asi que no ordena nada que cruce el
    corte. Y los resumenes tienen que cruzarlo: una novela no olvida el capitulo
    uno al empezar el dos. `MomentoNarrativo.t_discurso` esta definido en el
    dominio justo para esto -la posicion en el **discurso**, el orden de
    lectura- y es obligatorio. Tenia columna desde la migracion 3 y no lo
    rellenaba nadie.

    Es un atributo del **plan**: si la escaleta lo declara, se respeta y no se
    toca. Esto solo lo deriva para las escenas que no lo traen.

    `orden_de_capitulos` es `{id_capitulo: posicion}` y llega como argumento
    porque la tabla `capitulo` es de `features/brief/` (`A-02`). No hace falta
    cuando la obra tiene un solo capitulo -o ninguno declarado-, porque entonces
    el orden de lectura **es** el `orden`.

    **Lo que no se puede situar se queda sin situar, y se dice.** Si falta la
    posicion de un capitulo, sus escenas no reciben un `t_discurso` inventado:
    colocarlas por orden alfabetico del identificador seria adivinar el orden de
    lectura de una novela, que es exactamente el dato que falta.
    """
    filas = [(f[0], f[1], f[2], f[3]) for f in con.execute(
        "SELECT id, orden, capitulo, t_discurso FROM escena WHERE obra = ?",
        (obra,))]
    # `PLAN-23` A6: solo las de la version que se escribe. Numerar a la vez las dos
    # versiones intercalaria sus capitulos en un solo orden de lectura.
    if escenas is not None:
        dentro = set(escenas)
        filas = [f for f in filas if f[0] in dentro]
    capitulos = {c for _, _, c, _ in filas}
    orden_de_capitulos = dict(orden_de_capitulos or {})

    # Un solo capitulo -o ninguno- no necesita que nadie declare su posicion.
    if len(capitulos) <= 1:
        orden_de_capitulos = {c: 1 for c in capitulos}

    situables, sin_asignar = [], []
    for id_escena, orden, capitulo, ya in filas:
        if ya is not None:
            continue
        if capitulo not in orden_de_capitulos:
            sin_asignar.append(id_escena)
            continue
        situables.append((orden_de_capitulos[capitulo], orden, id_escena))

    with con:
        for posicion, (_, _, id_escena) in enumerate(sorted(situables), start=1):
            con.execute("UPDATE escena SET t_discurso = ? WHERE id = ?",
                        (posicion, id_escena))
    return {"asignadas": len(situables), "sin_asignar": sorted(sin_asignar)}


def escena(con, id_escena):
    for f in con.execute(
            "SELECT {0} FROM escena WHERE id = ?".format(_COLUMNAS), (id_escena,)):
        return _fila(f)
    return None


def guardar_borrador(con, escena, texto, modelo, prompt_hash):
    """Devuelve la version, que crece por escena.

    **Una escena consolidada o rendida no se degrada a `generada`** (`SPEC-30`
    `RF-10`): su canon ya esta aplicado y no se deshace. Un borrador nuevo sobre ella
    es una reescritura a delta fijo, que decide ella si lo acepta.
    """
    with con:
        fila = con.execute("SELECT MAX(version) FROM borrador WHERE escena = ?",
                           (escena,)).fetchone()
        version = (fila[0] or 0) + 1
        con.execute("INSERT INTO borrador VALUES (?, ?, ?, ?, ?)",
                    (escena, version, texto, modelo, prompt_hash))
        con.execute("UPDATE escena SET estado = ? WHERE id = ? AND estado NOT IN (?, ?)",
                    (EE.GENERADA.value, escena, EE.CONSOLIDADA.value,
                     EE.ACEPTADA_POR_RENDICION.value))
    return version


def marcar_consolidada(con, escena):
    """`aceptada` -> `consolidada`, la transicion del Consolidador.

    Existia en la tabla de `docs/architecture.md` y **no la aplicaba nadie**:
    las escenas se quedaban en `generada` para siempre, asi que la puerta de
    capitulo veia un capitulo con tres escenas a medias y no podia cerrarse
    nunca. El delta se aplicaba igual, de modo que el estado del mundo era
    correcto y el de la escena mentia.

    **Una escena rendida no se toca** (`SPEC-30` v4 `RF-11`): pisarla con
    `consolidada` borraba el unico dato duradero de que se rindio, que
    `docs/definitions.md` define como estado para que quien lea la obra lo sepa.
    Que esta consolidada lo dice `escena_consolidada`.
    """
    with con:
        con.execute("UPDATE escena SET estado = ? WHERE id = ? AND estado <> ?",
                    (EE.CONSOLIDADA.value, escena, EE.ACEPTADA_POR_RENDICION.value))


def aceptar_reescritura(con, escena, version):
    """`SPEC-30` `RF-10`: una reescritura a delta fijo cambia **el texto aceptado** y
    nada mas. El estado no se toca —una escena consolidada sigue consolidada y una
    rendida sigue rendida— porque el canon no se ha movido."""
    with con:
        con.execute("UPDATE escena SET borrador_aceptado = ? WHERE id = ?", (version, escena))


def rendir_escena(con, escena, version):
    """`aceptada_por_rendicion`, y **no** `aceptada` (`RF-24`).

    Son dos estados y no uno porque quien lea el manuscrito tiene que poder
    distinguir una escena limpia de una que paso con hallazgos abiertos.
    `borrador_aceptado` dice **cual** de los intentos se eligio, que es la otra
    mitad: sin eso, "se eligio el menos malo" no es comprobable.
    """
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? "
                    "WHERE id = ?", (EE.ACEPTADA_POR_RENDICION.value, version, escena))


def intentos_de(con, escena):
    """No hay contador aparte: es cuantos borradores hay."""
    return con.execute("SELECT COUNT(*) FROM borrador WHERE escena = ?",
                       (escena,)).fetchone()[0]


# Los dos estados en los que un hallazgo deja de contar. `sin_veredicto` no
# esta: significa que **falta el juicio**, no que se haya emitido.
DE_CIERRE = (EH.RESUELTO, EH.DESCARTADO)


def cerrar_hallazgo(con, id_hallazgo, estado, motivo: str):
    """`resuelto` o `descartado`, **con motivo**.

    Los dos estados existian en `estado_de_hallazgo` desde el primer dia y
    **ninguna funcion los escribia** (`F-38`): un hallazgo nacia abierto y se
    quedaba abierto para siempre, asi que aunque alguien arreglara la causa el
    capitulo no podia cerrarse nunca.

    **Resuelto y descartado no son lo mismo** y por eso son dos valores:
    resuelto es *se arreglo*, descartado es *se decidio que no aplica*. Si se
    confundieran, el recuento por invariante mezclaria las veces que la regla
    acerto con las que se equivoco, y ese recuento es lo unico que dice si una
    regla sirve.

    El motivo es obligatorio porque un hallazgo cerrado sin motivo es
    indistinguible de uno que alguien cerro para que dejara de molestar.
    """
    if estado not in DE_CIERRE:
        raise ValueError(
            "`{0}` no es un estado de cierre. Solo {1}: `sin_veredicto` "
            "significa que falta el juicio, no que se haya emitido".format(
                estado, " y ".join(str(e) for e in DE_CIERRE)))
    if not (motivo or "").strip():
        raise ValueError(
            "cerrar un hallazgo exige un motivo: sin el, no se distingue de "
            "uno que se cerro para que dejara de molestar")
    with con:
        con.execute("UPDATE hallazgo SET estado = ?, motivo_de_cierre = ? "
                    "WHERE id = ?", (str(estado), motivo, id_hallazgo))


def borrar_hallazgo_repetido(con, id_hallazgo):
    """Borra un hallazgo **recien creado** que repite uno abierto (`PLAN-30` E8).

    La puerta de publicacion vuelve a comprobar el nivel obra en cada ronda, y
    `novela.cerrar` abre un hallazgo nuevo cada vez. Si el problema sigue, se queda el
    de la ronda anterior y este sobra: cerrarlo como `resuelto` falsearia el recuento
    por invariante, y dejar los dos lo duplicaria. Solo para eso: un hallazgo que
    alguien ya vio no se borra, se cierra con motivo (`cerrar_hallazgo`).
    """
    with con:
        con.execute("DELETE FROM hallazgo WHERE id = ?", (id_hallazgo,))


def guardar_hallazgo(con, invariante, verificador, escena, severidad, estado, descripcion):
    with con:
        con.execute(
            "INSERT INTO hallazgo (invariante, verificador, escena, severidad, "
            "estado, descripcion) VALUES (?, ?, ?, ?, ?, ?)",
            (invariante, verificador, escena, str(severidad), str(estado), descripcion))


def hallazgos_abiertos(con, escena):
    """Devuelve `severidad` y `estado` como **miembros de su enumeracion**.

    La primera version los devolvia como cadenas, y eso abrio la puerta de
    capitulo en silencio: `impide_cerrar_el_capitulo` compara con `is` contra
    `Severidad.MAYOR`, y `"mayor" is Severidad.MAYOR` es falso. Un `mayor`
    leido de la base **no bloqueaba nada**, y las pruebas unitarias de la puerta
    no lo veian porque le pasaban miembros directamente.

    La leccion es de frontera: si los modelos Pydantic son la frontera de
    validacion de la API, **la deserializacion es la frontera de validacion de
    la base**. Un dato que entra al dominio entra con el tipo del dominio o no
    entra.
    """
    filas = con.execute(
        "SELECT invariante, verificador, severidad, estado, descripcion, id "
        "FROM hallazgo WHERE escena = ? AND estado IN (?, ?)",
        (escena, CUENTAN_COMO_ABIERTOS[0], CUENTAN_COMO_ABIERTOS[1]))
    return [{"invariante": f[0], "verificador": f[1],
             "severidad": Severidad(f[2]), "estado": EH(f[3]),
             "descripcion": f[4], "id": f[5]} for f in filas]


def aceptar_borrador(con, escena, version, rindiendose):
    estado = EE.ACEPTADA_POR_RENDICION if rindiendose else EE.ACEPTADA
    with con:
        con.execute("UPDATE escena SET estado = ?, borrador_aceptado = ? WHERE id = ?",
                    (estado.value, version, escena))


def guardar_valoraciones_del_editor(con, escena, version, valoraciones):
    """Las notas del Editor a **esta version** del borrador (`PLAN-31` E4). Llegan ya
    validadas como `ValoracionDelEditor`: una ilegible no llega aqui."""
    asegurar_tablas(con)
    with con:
        for v in valoraciones:
            con.execute(
                "INSERT OR REPLACE INTO valoracion_del_editor (escena, version, criterio, "
                "nota, justificacion, instruccion) VALUES (?, ?, ?, ?, ?, ?)",
                (escena, version, str(v.criterio), v.nota, v.justificacion,
                 v.instruccion))


def valoraciones_del_editor(con, escena):
    asegurar_tablas(con)
    filas = con.execute(
        "SELECT escena, version, criterio, nota, justificacion, instruccion "
        "FROM valoracion_del_editor WHERE escena = ? ORDER BY version, criterio", (escena,))
    return [{"escena": f[0], "version": f[1], "criterio": f[2], "nota": f[3],
             "justificacion": f[4], "instruccion": f[5]} for f in filas]


def hallazgos_de(con, escena):
    """Todos los hallazgos de la escena, **en cualquier estado** (`PLAN-31` E6): la
    evaluacion cuenta tambien los que disparon y se resolvieron, que es lo que convierte
    un pase en un pase que dice algo."""
    filas = con.execute(
        "SELECT invariante, verificador, severidad, estado, descripcion, id "
        "FROM hallazgo WHERE escena = ? ORDER BY id", (escena,))
    return [{"invariante": f[0], "verificador": f[1], "severidad": Severidad(f[2]),
             "estado": EH(f[3]), "descripcion": f[4], "id": f[5]} for f in filas]
