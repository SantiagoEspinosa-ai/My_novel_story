"""VER-28 — Ningún camino de `planificada` a `consolidada` salta `en_verificacion`.

`Docs/verification.md` § VER-28, metodología *model checking*. Su punto ciego está
declarado en el documento: **verifica el modelo, no la implementación**. Lo que se
comprueba aquí es la máquina de estados tal como la declara
`Docs/architecture.md`; que el código la respete es otra cosa y hoy no hay código.

Se puede escribir hoy precisamente porque la máquina vive en un documento.
"""

from __future__ import annotations

from harness.documentos import parsers

ORIGEN = "planificada"
DESTINO = "consolidada"
PUERTA = "en_verificacion"


def test_los_estados_de_la_tabla_son_los_de_la_enumeracion(definitions, architecture):
    """Precondición: la máquina usa los literales de `estado_de_escena`.

    Si la tabla de transiciones usara nombres inventados, explorarla no
    demostraría nada sobre la máquina real. `definitions.md` lo dice explícito:
    *"los literales se copian de esta tabla, nunca del diagrama"*.
    """
    legales = parsers.valores_de_enumeracion(definitions, "estado_de_escena")
    usados = {e for par in parsers.transiciones(architecture) for e in par}

    intrusos = sorted(usados - legales)
    assert not intrusos, (
        "La tabla de transiciones de architecture.md usa estados que no están en "
        f"la enumeración `estado_de_escena`: {intrusos}.\n"
        f"Legales: {sorted(legales)}"
    )


def test_no_hay_camino_que_salte_la_puerta(architecture):
    """El model check propiamente dicho."""
    aristas = parsers.transiciones(architecture)
    atajo = parsers.camino_evitando(aristas, ORIGEN, DESTINO, PUERTA)

    assert atajo is None, (
        f"Existe un camino de `{ORIGEN}` a `{DESTINO}` que no pasa por "
        f"`{PUERTA}`: {' → '.join(atajo)}.\n"
        "Una escena podría consolidarse sin pasar la puerta de verificación."
    )


def test_todo_estado_es_alcanzable_desde_planificada(definitions, architecture):
    """Un estado declarado al que no se llega es un estado muerto.

    No lo pide VER-28, pero sale gratis del mismo grafo y detecta lo contrario
    del atajo: una transición que se eliminó y dejó un estado colgando.
    """
    aristas = parsers.transiciones(architecture)
    declarados = parsers.valores_de_enumeracion(definitions, "estado_de_escena")

    inalcanzables = sorted(
        estado
        for estado in declarados
        if estado != ORIGEN
        and parsers.camino_evitando(aristas, ORIGEN, estado, "\x00") is None
    )
    assert not inalcanzables, (
        f"Estados declarados en `estado_de_escena` a los que no se llega desde "
        f"`{ORIGEN}`: {inalcanzables}"
    )


# --------------------------------------------------------------------------
# Caso negativo
# --------------------------------------------------------------------------


def test_negativo_caza_un_atajo(fixtures):
    """Con una transición `generada` → `aceptada`, el validador tiene que saltar."""
    roto = (fixtures / "architecture_atajo.md").read_text(encoding="utf-8")

    aristas = parsers.transiciones(roto)
    atajo = parsers.camino_evitando(aristas, ORIGEN, DESTINO, PUERTA)

    assert atajo is not None, (
        "El fixture tiene un atajo declarado y el validador no lo encontró. "
        "Si esto pasa, el validador no sirve."
    )
    assert "generada" in atajo and PUERTA not in atajo
