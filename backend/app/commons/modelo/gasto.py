"""Lo que costo cada delegacion, en la base: `GastoDeDelegacion` (`SPEC-33` `RF-18`).

`SesionDelegada.anotador` se llama una vez por delegacion con su coste; esto lo escribe.
Vive en `commons/` porque lo necesitan la entrevista (el Entrevistador) y la orquestacion
(el resto de agentes), y una feature no importa de otra (`docs/architecture.md`).

LO AUSENTE NO ES CERO
---------------------
Una delegacion sin coste medido se guarda con `coste_usd = NULL` (`RF-19`). Quien sume lo
gastado tiene que contarlas aparte y decir que el total es un suelo, como `Contador`.
"""


def anotador(con, obra, generacion=None):
    """Un `(agente, coste_usd) -> None` que deja una fila por delegacion."""

    def anotar(agente, coste_usd):
        with con:
            con.execute("INSERT INTO gasto_de_delegacion (obra, agente, generacion, coste_usd) "
                        "VALUES (?, ?, ?, ?)", (obra, agente or "desconocido", generacion,
                                                coste_usd))

    return anotar
