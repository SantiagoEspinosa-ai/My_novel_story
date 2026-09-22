"""Control del presupuesto de contexto.

Este modulo **no escribe `tokens_declarados`**, y esa ausencia es una regla, no
una casualidad: es la condicion que impide que `VER-41` se vuelva un eco
(`SPEC-08` C-4, regla 2). Lo comprueba una prueba estatica, no un comentario.

`P-2` de `SPEC-01`: una llamada reserva su presupuesto antes de salir y lo
libera al volver, tambien cuando falla. `MF-25` es lo que pasa cuando un worker
muere sin volver: el techo se queda retenido hasta que expire el margen de
abandono.
"""

from app.commons.config import MARGEN_ABANDONO_SEGUNDOS  # noqa: F401  (documenta la relacion)

TECHO_TOKENS = 100_000

# Aproximacion para decidir cuando recortar. No es una cuenta exacta y no hace
# falta que lo sea: decide "me paso o no", no "por cuanto". Contar exacto en
# cada vuelta del bucle paga el tokenizador sin ganar nada (`SPEC-12` C-3).
# En espanol, cerca de cuatro caracteres por token.
CARACTERES_POR_TOKEN = 4


def estimar_para_recortar(texto: str) -> int:
    """`tokens_para_recortar`. Conservadora y con su margen declarado."""
    return len(texto or "") // CARACTERES_POR_TOKEN


def reservar(estado_del_techo: dict, tokens: int) -> bool:
    """`tokens_reservados`. Aparta techo antes de salir; falso si no cabe."""
    if estado_del_techo.get("usado", 0) + tokens > TECHO_TOKENS:
        return False
    estado_del_techo["usado"] = estado_del_techo.get("usado", 0) + tokens
    return True


def liberar(estado_del_techo: dict, tokens: int) -> None:
    """Se libera al volver, **tambien cuando falla**. Un worker que muere no
    vuelve nunca y por eso no libera: eso es `MF-25`."""
    estado_del_techo["usado"] = max(0, estado_del_techo.get("usado", 0) - tokens)
