"""Donde sobrevive la traza de una delegacion (`F-49`).

QUE SE PERDIA, Y POR QUE NO ERA UN PROBLEMA DE REGISTROS
----------------------------------------------------------
`commons/modelo/traza.py` construye la traza en memoria y **nadie la
escribia**. Con el proceso se iban tres cosas:

    recortes            que bloques tiro el recortador
    modelos             lo unico que `modelo_fijo.comprobar` puede mirar
    clase_de_fallo      por que murio una delegacion

La que importa es la primera, y el motivo esta escrito en `PC-9`: lo que acota
el dano de que un agente rellene con invencion lo que el recorte dejo fuera es
que *"la traza registra que fichas quedaron fuera, asi que el fallo pasa de
invisible a atribuible"*. **Si la traza no sobrevive al proceso, esa contencion
solo vale dentro de la misma ejecucion** — y el diagnostico siempre se hace
despues.

LA LLAVE, Y POR QUE NO ES LA RESPUESTA
----------------------------------------
`(escena, agente, prompt_hash)`. El `prompt_hash` y no la respuesta, para que
**las delegaciones que fallaron tambien consten**: son las que mas dicen, y
atarlas a lo que devolvieron las perderia justo cuando no devolvieron nada.

Escena y agente estan en la llave por la Regla 7: el Escritor y el Juez
trabajan sobre la misma escena y son dos trazas distintas. Una llave que
omitiera el agente no fallaria — **pisaria**.

ESTO REGISTRA LO QUE SALE; `contexto/repository.py` REGISTRA LO QUE ENTRA
--------------------------------------------------------------------------
Misma llave y misma forma. Con las dos, una delegacion pasada se reconstruye
por los dos lados **sin releer ningun texto**, que es lo que `CLAUDE.md`
prohibe hacer para averiguar que paso.
"""

import json
import sqlite3

SQL = """
CREATE TABLE IF NOT EXISTS traza_de_delegacion (
    escena               TEXT NOT NULL,
    agente               TEXT NOT NULL,
    prompt_hash          TEXT NOT NULL DEFAULT '',
    trabajo              TEXT,
    modelo               TEXT,
    modelos              TEXT NOT NULL DEFAULT '[]',
    recortes             TEXT NOT NULL DEFAULT '[]',
    fichas               TEXT NOT NULL DEFAULT '[]',
    tokens_para_recortar INTEGER,
    tokens_estimados     INTEGER,
    resultado            TEXT,
    clase_de_fallo       TEXT,
    salida_fallida       TEXT,
    delegacion           TEXT,
    cuando               TEXT NOT NULL DEFAULT (datetime('now')),
    PRIMARY KEY (escena, agente, prompt_hash)
);
CREATE TABLE IF NOT EXISTS llamada_a_herramienta (
    id               INTEGER PRIMARY KEY AUTOINCREMENT,
    delegacion       TEXT NOT NULL,
    obra             TEXT NOT NULL,
    agente           TEXT NOT NULL,
    herramienta      TEXT NOT NULL,
    validacion       TEXT NOT NULL,
    latencia_ms      INTEGER,
    tokens_estimados INTEGER,
    cuando           TEXT NOT NULL DEFAULT (datetime('now'))
);
"""


def asegurar_tablas(con: sqlite3.Connection):
    with con:
        con.executescript(SQL)


def guardar_traza(con, t):
    """Idempotente por `(escena, agente, prompt_hash)`.

    Repetir el guardado **no** es una delegacion mas: contarlo como tal haria
    que `VER-61` viera trabajo que no existio, que es justo el error que esa
    reconciliacion existe para detectar.
    """
    asegurar_tablas(con)
    with con:
        con.execute(
            "INSERT OR REPLACE INTO traza_de_delegacion "
            "(escena, agente, prompt_hash, trabajo, modelo, modelos, recortes, "
            " fichas, tokens_para_recortar, tokens_estimados, resultado, "
            " clase_de_fallo, salida_fallida, delegacion) "
            "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (t.escena, t.agente, t.prompt_hash or "", t.trabajo, t.modelo,
             json.dumps(list(t.modelos or [])),
             json.dumps([[r.bloque, r.clase] if hasattr(r, "bloque") else list(r)
                         for r in (t.recortes or [])]),
             json.dumps([list(f) for f in (t.fichas or [])]),
             t.tokens_para_recortar, t.tokens_estimados, t.resultado,
             t.clase_de_fallo, t.salida_fallida,
             # `PLAN-28` E8: viaja en las medidas de la respuesta (`proveedor`), que
             # tanto `bucle` como `ciclo` ya copian a la traza.
             (t.medidas or {}).get("delegacion")))


def trazas_de(con, escena):
    asegurar_tablas(con)
    filas = con.execute(
        "SELECT escena, agente, prompt_hash, trabajo, modelo, modelos, recortes, "
        "fichas, tokens_para_recortar, tokens_estimados, resultado, "
        "clase_de_fallo, salida_fallida, cuando, delegacion FROM traza_de_delegacion "
        "WHERE escena = ? ORDER BY cuando, agente", (escena,))
    return [{"escena": f[0], "agente": f[1], "prompt_hash": f[2],
             "trabajo": f[3], "modelo": f[4], "modelos": json.loads(f[5]),
             "recortes": json.loads(f[6]), "fichas": json.loads(f[7]),
             "tokens_para_recortar": f[8], "tokens_estimados": f[9],
             "resultado": f[10], "clase_de_fallo": f[11],
             "salida_fallida": f[12], "cuando": f[13], "delegacion": f[14],
             "herramientas": _herramientas_de(con, f[14])} for f in filas]


def _herramientas_de(con, delegacion):
    """Cuantas llamadas a tools hizo la delegacion y cuantos tokens estimados
    devolvieron, sin presupuestarlos (`SPEC-28` `RF-08`). Sin llamadas, los tokens se
    quedan ausentes: un cero se leeria como una medida."""
    if not delegacion:
        return {"llamadas": 0, "tokens_estimados": None}
    f = con.execute("SELECT COUNT(*), SUM(tokens_estimados) FROM llamada_a_herramienta "
                    "WHERE delegacion = ?", (delegacion,)).fetchone()
    return {"llamadas": f[0], "tokens_estimados": f[1]}


def recortes_de_la_obra(con):
    """Que bloques se tiraron en toda la obra, por bloque y clase.

    Es la consulta de `PC-9`: cuando alguien encuentre invencion en una escena,
    esto dice si el contexto de esa escena habia perdido lo que hacia falta.
    """
    asegurar_tablas(con)
    cuenta = {}
    for fila in con.execute("SELECT recortes FROM traza_de_delegacion"):
        for bloque, clase in json.loads(fila[0]):
            cuenta[(bloque, clase)] = cuenta.get((bloque, clase), 0) + 1
    return cuenta


def guardar_llamada(con, delegacion, obra, agente, herramienta, validacion, latencia_ms,
                    tokens_estimados):
    """`SPEC-28` `RF-08`, `RF-09`: una fila por llamada a una tool.

    **Sin argumentos ni resultado**: llevan datos de la story bible, y la story bible
    lleva al destinatario (`SPEC-29` § "El limite", `VER-69`). `validacion` dice de
    donde sale la fila (`ok`, `entrada_invalida`, `salida_invalida`, `no_existe`,
    `herramienta_desconocida`); no es vocabulario del dominio, como `plan_de_obra.origen`.
    """
    asegurar_tablas(con)
    with con:
        con.execute(
            "INSERT INTO llamada_a_herramienta (delegacion, obra, agente, herramienta, "
            "validacion, latencia_ms, tokens_estimados) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (delegacion, obra, agente, herramienta, validacion, latencia_ms,
             tokens_estimados))


def llamadas_de(con, delegacion):
    asegurar_tablas(con)
    return [{"herramienta": f[0], "agente": f[1], "validacion": f[2], "latencia_ms": f[3],
             "tokens_estimados": f[4]}
            for f in con.execute(
                "SELECT herramienta, agente, validacion, latencia_ms, tokens_estimados "
                "FROM llamada_a_herramienta WHERE delegacion = ? ORDER BY id", (delegacion,))]


def spans_de_herramientas(con, delegacion):
    """El enganche de `SPEC-29`: exactamente lo que sube de cada llamada, y nada mas."""
    return [{"nombre": l["herramienta"], "latencia_ms": l["latencia_ms"],
             "validacion": l["validacion"], "tokens_estimados": l["tokens_estimados"]}
            for l in llamadas_de(con, delegacion)]
