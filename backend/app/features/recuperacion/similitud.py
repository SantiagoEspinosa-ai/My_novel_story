"""Recuperacion por similitud sobre SQLite, sin servicio aparte.

`CLAUDE.md`: *"una sola base de datos guarda el estado estructurado y los
embeddings. La busqueda por similitud se hace con una extension vectorial de
SQLite; no se añade un servicio aparte."*

QUE SE INDEXA, Y LO QUE DELIBERADAMENTE NO
--------------------------------------------
Fichas de entidad, resumenes de escena y setups pendientes. **El texto
completo de las escenas se guarda pero no se recupera por similitud**: para eso
estan los resumenes. Indexarlo seria volver a meter la obra entera en el
contexto por otra puerta, que es justo lo que el presupuesto de `CLAUDE.md`
existe para impedir. Por eso `indexar` lo rechaza en vez de confiar en que
nadie lo intente.

SI LA EXTENSION NO ESTA, SE DICE
---------------------------------
No se degrada a una busqueda lexica. Una busqueda por palabras devolveria
resultados plausibles por un criterio distinto del que se pidio, y nadie sabria
que la similitud no esta funcionando: el sistema parece entero y recupera otra
cosa. Es la clase de fallo silencioso que este proyecto persigue, asi que
fallar ruidosamente es la opcion barata.

DE DONDE SALEN LOS VECTORES
----------------------------
**De fuera de este modulo.** Aqui no se calcula ningun embedding: se reciben.
El proyecto no tiene todavia una fuente de embeddings decidida —no hay clave de
API y la suscripcion delega en sesiones, que no producen vectores—, y elegir un
modelo local es una dependencia nueva que no se mete de tapadillo en un modulo
de persistencia.

Esto no bloquea nada de lo de aqui: la indexacion, la consulta KNN y el
reemplazo por referencia se prueban contra vectores dados, que es exactamente
lo que este modulo tiene que hacer bien.
"""

import struct

# Los tres que nombra `CLAUDE.md`, y ninguno mas. `SPEC-26` v3 retiro los
# presagios (especificos de terror); su sitio lo ocupa el setup, que es general.
TIPOS = ("ficha", "resumen", "setup")


class SinSoporteVectorial(RuntimeError):
    """La extension no esta. Se dice; no se finge."""


def _cargar_extension(con):
    import sqlite_vec

    con.enable_load_extension(True)
    sqlite_vec.load(con)
    con.enable_load_extension(False)


def _serializar(vector):
    """El formato que `vec0` espera: float32 en little-endian, sin cabecera."""
    return struct.pack("%df" % len(vector), *vector)


def asegurar_tablas(con, dimensiones: int):
    """La tabla `vec0` y la de metadatos que le falta.

    `vec0` guarda el vector y su `rowid`, y **no guarda a que se refiere**. La
    tabla de al lado lleva el tipo y la referencia, que es lo que hace util un
    vecino: saber que `per-marta` esta cerca no sirve si no se puede ir a por
    su ficha.
    """
    try:
        _cargar_extension(con)
    except Exception as e:
        raise SinSoporteVectorial(
            "no se pudo cargar `sqlite-vec`, asi que no hay recuperacion por "
            "similitud. **No se degrada a busqueda lexica**: devolveria "
            "resultados por un criterio distinto del pedido y nadie sabria que "
            "la similitud no esta funcionando. Causa: {0}".format(e)) from e
    with con:
        con.execute(
            "CREATE VIRTUAL TABLE IF NOT EXISTS vectores USING vec0("
            "embedding float[{0}])".format(dimensiones))
        con.execute(
            "CREATE TABLE IF NOT EXISTS vector_de (rowid_vec INTEGER PRIMARY KEY, "
            "tipo TEXT NOT NULL, referencia TEXT NOT NULL UNIQUE)")
        # Las dimensiones viven **en la base** y no en la conexion: son una
        # propiedad del indice, no de quien lo abre. Asi una base reabierta
        # mañana sigue sabiendo con que modelo se construyo, que es lo que
        # permite detectar que alguien cambio de modelo sin reindexar.
        con.execute("CREATE TABLE IF NOT EXISTS vector_config ("
                    "clave TEXT PRIMARY KEY, valor INTEGER NOT NULL)")
        con.execute("INSERT OR REPLACE INTO vector_config VALUES "
                    "('dimensiones', ?)", (dimensiones,))


def indexar(con, tipo: str, referencia: str, vector):
    """Guarda o **sustituye** el vector de una referencia.

    Sustituye y no acumula: una ficha tiene versiones y la recuperacion busca
    la vigente. Dos vectores de la misma entidad la devolverian dos veces y
    gastarian sitio del bloque 5 en repetirse.
    """
    if tipo not in TIPOS:
        raise ValueError(
            "`{0}` no se indexa. Solo {1}. El texto completo de una escena se "
            "guarda pero no se recupera por similitud: para eso esta su "
            "resumen (`CLAUDE.md`)".format(tipo, ", ".join(TIPOS)))
    fila = con.execute("SELECT valor FROM vector_config WHERE clave='dimensiones'"
                       ).fetchone()
    esperadas = fila[0] if fila else None
    if esperadas is not None and len(vector) != esperadas:
        raise ValueError(
            "el vector tiene {0} dimensiones y el indice {1}. Mezclarlos daria "
            "distancias sin sentido: si se cambio de modelo de embeddings hay "
            "que reindexar, no añadir".format(len(vector), esperadas))
    with con:
        previo = con.execute("SELECT rowid_vec FROM vector_de WHERE referencia = ?",
                             (referencia,)).fetchone()
        if previo:
            con.execute("DELETE FROM vectores WHERE rowid = ?", (previo[0],))
            con.execute("DELETE FROM vector_de WHERE rowid_vec = ?", (previo[0],))
        cur = con.execute("INSERT INTO vectores (embedding) VALUES (?)",
                          (_serializar(vector),))
        con.execute("INSERT INTO vector_de (rowid_vec, tipo, referencia) "
                    "VALUES (?, ?, ?)", (cur.lastrowid, tipo, referencia))


def buscar(con, vector, limite: int = 5, tipo: str | None = None):
    """Los `limite` mas cercanos, con su tipo y su referencia.

    El filtro por tipo se aplica **despues** del KNN y por eso pide de mas:
    `vec0` no sabe filtrar por una columna que no es suya, y pedir justo
    `limite` devolveria menos de los pedidos en cuanto los primeros vecinos
    fueran de otro tipo.
    """
    k = limite * len(TIPOS) if tipo else limite
    filas = con.execute(
        "SELECT v.rowid, v.distance FROM vectores v "
        "WHERE v.embedding MATCH ? AND k = ? ORDER BY v.distance",
        (_serializar(vector), k)).fetchall()
    salida = []
    for rowid, distancia in filas:
        meta = con.execute(
            "SELECT tipo, referencia FROM vector_de WHERE rowid_vec = ?",
            (rowid,)).fetchone()
        if meta is None or (tipo and meta[0] != tipo):
            continue
        salida.append({"tipo": meta[0], "referencia": meta[1],
                       "distancia": distancia})
        if len(salida) == limite:
            break
    return salida
