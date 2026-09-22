"""Lo que la API devuelve. Solo estado: el frontend no calcula nada.

`Docs/architecture.md`: "el frontend nunca toca la base y nunca calcula nada
del dominio. Si el frontend necesitara calcular algo para pintarlo, falta un
campo en la respuesta." Por eso `se_acepto_rindiendose` sale resuelto de aqui y
no se deduce comparando cadenas en el navegador.
"""

RENDIDA = "aceptada_por_rendicion"
SIN_MEDIR = "sin medir"


def escena(fila, hallazgos):
    """Nunca el texto solo. `RF-23`."""
    return {
        "id": fila["id"],
        "texto": fila.get("texto"),
        "estado": fila["estado"],
        "se_acepto_rindiendose": fila["estado"] == RENDIDA,
        "hallazgos_abiertos": list(hallazgos),
    }


def consumo(traza):
    """`RF-25`: ausente y distinguible de cero.

    Un cero se lee como un dato -"no gasto nada"- y un hueco como lo que es
    -"no se sabe"-. Confundirlos convierte un suelo en una medida.
    """
    t = traza.get("tokens_declarados")
    return {"tokens": SIN_MEDIR if t is None else t}


def trabajo(fila):
    """`RF-24` con la respuesta de `SPEC-08`: el ultimo fallo mas los intentos.

    El historial completo queda en los trabajos para quien lo necesite; la
    respuesta por defecto no lo arrastra.
    """
    return {"id": fila["id"], "estado": fila["estado"],
            "intentos": fila["intentos"],
            "motivo_ultimo_fallo": fila.get("motivo_ultimo_fallo")}
