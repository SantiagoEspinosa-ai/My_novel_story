"""El audit log del policy engine (`SPEC-25` `RF-20`).

Vive en `commons/` porque escriben en el dos casos de uso distintos: la puerta
de `INV-21`, desde `orquestacion/`, y la entrevista, que registra inyecciones,
contradicciones y borrados. Una feature no importa de otra.

**Solo se inserta.** Una decision registrada no se corrige ni se borra, ni
siquiera en el borrado al entregar: esa fila dice que se borro y cuando, nunca
lo que se borro.
"""

import json
from datetime import datetime, timezone

from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica

SQL = """
CREATE TABLE IF NOT EXISTS decision_de_politica (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo    TEXT NOT NULL,
    momento TEXT NOT NULL,
    obra    TEXT,
    detalle TEXT NOT NULL DEFAULT '{}'
);
"""


def asegurar_tabla(con):
    with con:
        con.executescript(SQL)


def registrar_decision(con, tipo, obra, detalle=None, dentro_de_transaccion=False):
    def _escribir():
        con.execute(
            "INSERT INTO decision_de_politica (tipo, momento, obra, detalle) "
            "VALUES (?, ?, ?, ?)",
            (str(TipoDeDecisionDePolitica(tipo)),
             datetime.now(timezone.utc).isoformat(), obra,
             json.dumps(detalle or {}, ensure_ascii=False)))

    if dentro_de_transaccion:
        _escribir()
    else:
        with con:
            _escribir()


def decisiones(con, obra=None) -> list:
    sql = "SELECT tipo, momento, obra, detalle FROM decision_de_politica"
    args = ()
    if obra is not None:
        sql += " WHERE obra = ?"
        args = (obra,)
    filas = con.execute(sql + " ORDER BY id", args).fetchall()
    return [{"tipo": TipoDeDecisionDePolitica(f[0]), "momento": f[1],
             "obra": f[2], "detalle": json.loads(f[3])} for f in filas]
