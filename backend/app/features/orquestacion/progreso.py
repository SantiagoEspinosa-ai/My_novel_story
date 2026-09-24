"""En que punto va una generacion: `ProgresoDeGeneracion` (`SPEC-22` `RF-60`, `PLAN-22` E13c).

`novela.escribir` llama a `fijar` al entrar en cada fase. Se **anade** una fila por
cambio; la ultima de la obra es su progreso. La tabla nace en la migracion 11. Una fase
repetida seguida (el mismo capitulo, la misma fase) no se vuelve a escribir: `desde` dice
cuando se entro, no cuando se llamo por ultima vez al agente.
"""

from app.commons.db import migraciones
from app.commons.dominio.enumeraciones import FaseDeGeneracion

_COLUMNAS = "fase, capitulo, total_de_capitulos, motivo, desde"


def _asegurar(con):
    if not migraciones.tiene_tabla(con, "progreso_de_generacion"):
        migraciones.migrar(con)


def _fila(f):
    return {"fase": f[0], "capitulo": f[1], "total_de_capitulos": f[2], "motivo": f[3],
            "desde": f[4]}


def actual(con, obra):
    _asegurar(con)
    f = con.execute("SELECT {0} FROM progreso_de_generacion WHERE obra = ? "
                    "ORDER BY id DESC LIMIT 1".format(_COLUMNAS), (obra,)).fetchone()
    return None if f is None else _fila(f)


def historia(con, obra):
    _asegurar(con)
    return [_fila(f) for f in con.execute(
        "SELECT {0} FROM progreso_de_generacion WHERE obra = ? ORDER BY id".format(_COLUMNAS),
        (obra,))]


def fijar(con, obra, fase, capitulo=None, total=None, motivo=None):
    fase = FaseDeGeneracion(fase)
    ultima = actual(con, obra)
    if ultima and (ultima["fase"], ultima["capitulo"]) == (fase.value, capitulo) \
            and fase is not FaseDeGeneracion.PARADA:
        return
    with con:
        con.execute("INSERT INTO progreso_de_generacion (obra, fase, capitulo, "
                    "total_de_capitulos, motivo) VALUES (?, ?, ?, ?, ?)",
                    (obra, fase.value, capitulo, total, motivo))


class ConFase:
    """Envuelve un agente: al llamarlo, la obra entra en su fase. Todo lo demas -`reglas`,
    `herramientas`, `nombre`- pasa al agente de dentro, como en `SesionObservada`."""

    def __init__(self, agente, con, obra, fase, donde):
        object.__setattr__(self, "_agente", agente)
        object.__setattr__(self, "_fase", (con, obra, fase, donde))

    def __getattr__(self, nombre):
        return getattr(self._agente, nombre)

    def __setattr__(self, nombre, valor):
        setattr(self._agente, nombre, valor)

    def llamar(self, prompt):
        con, obra, fase, donde = self._fase
        capitulo, total = donde()
        fijar(con, obra, fase, capitulo, total)
        return self._agente.llamar(prompt)
