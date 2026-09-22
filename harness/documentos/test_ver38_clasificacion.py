"""VER-38 — La clasificación de cada invariante coincide en las tres fuentes.

`Docs/verification.md` § VER-38: *"La severidad, el nivel y el tipo declarados en
el código para cada invariante coinciden con la tabla de `Docs/definitions.md`"*.

Todavía no hay código que declare nada, así que esta primera versión compara las
tres fuentes documentales que sí existen:

1. `Docs/definitions.md` — normativa: nivel, severidad y tipo de las dieciséis.
2. `Docs/architecture.md` — qué agente ejecuta cada una, y qué nivel les atribuye
   la fila del Auditor de obra.
3. `.agents/skills/harness-invariantes/SKILL.md` — su propia lista de niveles y
   su recuento de tipos.

Va el primero de todo el harness porque **es el validador que valida a otros
tres**: hoy `VER-11`, `VER-12` y `VER-22` pueden estar los tres en verde con una
severidad mal puesta, que es justo el anti-patrón *"bajar una bloqueante a mayor
para desatascar"* que la propia skill lista.
"""

from __future__ import annotations

import pytest

from harness.documentos import parsers


# --------------------------------------------------------------------------
# El validador, como funciones puras sobre texto.
# --------------------------------------------------------------------------


def niveles_declarados(texto_definitions: str) -> dict[str, set[str]]:
    """Agrupa las invariantes de `definitions.md` por nivel."""
    agrupadas: dict[str, set[str]] = {}
    for inv in parsers.invariantes(texto_definitions).values():
        agrupadas.setdefault(inv.nivel, set()).add(inv.id)
    return agrupadas


def tipos_declarados(texto_definitions: str) -> dict[str, set[str]]:
    """Agrupa las invariantes de `definitions.md` por tipo de verificador."""
    agrupadas: dict[str, set[str]] = {}
    for inv in parsers.invariantes(texto_definitions).values():
        agrupadas.setdefault(inv.tipo, set()).add(inv.id)
    return agrupadas


# --------------------------------------------------------------------------
# Comprobaciones contra los documentos reales.
# --------------------------------------------------------------------------


def test_definitions_declara_las_dieciseis(definitions):
    """Precondición: si no están las dieciséis, el resto no significa nada."""
    encontradas = parsers.invariantes(definitions)
    esperadas = {f"INV-{n:02d}" for n in range(1, 17)}
    assert set(encontradas) == esperadas


def test_severidad_y_nivel_son_valores_de_su_enumeracion(definitions):
    """Toda invariante usa literales de los vocabularios controlados.

    No cruza fuentes: comprueba que `definitions.md` es coherente consigo mismo.
    Hace falta porque el resto de comparaciones dan por hecho que estos valores
    son los literales, no una variante escrita a mano.
    """
    severidades = parsers.valores_de_enumeracion(definitions, "severidad")
    niveles = parsers.valores_de_enumeracion(definitions, "nivel_de_evaluacion")
    tipos = parsers.valores_de_enumeracion(definitions, "tipo_de_verificador")

    fuera_de_vocabulario = [
        (inv.id, inv.nivel, inv.severidad, inv.tipo)
        for inv in parsers.invariantes(definitions).values()
        if inv.nivel not in niveles
        or inv.severidad not in severidades
        or inv.tipo not in tipos
    ]
    assert not fuera_de_vocabulario, (
        "Hay invariantes con nivel, severidad o tipo fuera de su vocabulario "
        f"controlado: {fuera_de_vocabulario}"
    )


def test_nivel_coincide_entre_las_tres_fuentes(definitions, architecture, skill_invariantes):
    """El nivel de cada invariante dice lo mismo en los tres documentos."""
    normativo = niveles_declarados(definitions)
    del_auditor = parsers.niveles_del_auditor(architecture)
    de_la_skill = parsers.niveles_de_la_skill(skill_invariantes)

    for nivel in ("obra", "capitulo"):
        assert normativo.get(nivel, set()) == del_auditor[nivel], (
            f"Nivel '{nivel}': definitions.md y la fila del Auditor de obra de "
            f"architecture.md no coinciden.\n"
            f"  definitions.md: {sorted(normativo.get(nivel, set()))}\n"
            f"  architecture.md: {sorted(del_auditor[nivel])}"
        )
        assert normativo.get(nivel, set()) == de_la_skill[nivel], (
            f"Nivel '{nivel}': definitions.md y la skill harness-invariantes no "
            f"coinciden.\n"
            f"  definitions.md: {sorted(normativo.get(nivel, set()))}\n"
            f"  skill: {sorted(de_la_skill[nivel])}"
        )


def test_tipo_coincide_con_el_agente_que_la_ejecuta(definitions, architecture):
    """Las invariantes de tipo `juez_llm` son exactamente las del Juez de rúbrica."""
    de_juez = tipos_declarados(definitions).get("juez_llm", set())
    por_agente = parsers.invariantes_por_agente(architecture)

    assert "Juez de rúbrica" in por_agente, (
        f"No encontré al Juez de rúbrica en la tabla de agentes. "
        f"Agentes leídos: {sorted(por_agente)}"
    )
    assert de_juez == por_agente["Juez de rúbrica"], (
        "Las invariantes de tipo `juez_llm` no son las que ejecuta el Juez.\n"
        f"  definitions.md: {sorted(de_juez)}\n"
        f"  architecture.md: {sorted(por_agente['Juez de rúbrica'])}"
    )


def test_recuento_de_tipos_de_la_skill_cuadra(definitions, skill_invariantes):
    """La skill afirma en prosa 'doce son de regla, cuatro son de juez'."""
    por_tipo = tipos_declarados(definitions)
    afirmado = parsers.recuento_de_tipos_de_la_skill(skill_invariantes)

    real = {tipo: len(ids) for tipo, ids in por_tipo.items()}
    for tipo, cuantas in afirmado.items():
        assert real.get(tipo, 0) == cuantas, (
            f"La skill dice que hay {cuantas} invariantes de tipo '{tipo}' y en "
            f"definitions.md hay {real.get(tipo, 0)}."
        )


def test_toda_invariante_tiene_al_menos_un_agente(definitions, architecture):
    """Ninguna invariante se queda sin nadie que la ejecute.

    Es el fallo que la auditoría encontró con `INV-14`: estaba declarada y no
    aparecía en la fila de ningún agente capaz de ejecutarla.
    """
    todas = set(parsers.invariantes(definitions))
    asignadas: set[str] = set()
    for ids in parsers.invariantes_por_agente(architecture).values():
        asignadas |= ids

    huerfanas = sorted(todas - asignadas)
    assert not huerfanas, (
        f"Estas invariantes no las ejecuta ningún agente de architecture.md: {huerfanas}"
    )


# --------------------------------------------------------------------------
# Casos negativos: el validador tiene que fallar cuando debe.
# --------------------------------------------------------------------------


def test_negativo_caza_un_nivel_cambiado(fixtures, architecture, skill_invariantes):
    """Si alguien mueve INV-14 de `obra` a `escena`, el validador salta."""
    roto = (fixtures / "definitions_nivel_cambiado.md").read_text(encoding="utf-8")

    normativo = niveles_declarados(roto)
    del_auditor = parsers.niveles_del_auditor(architecture)

    assert normativo.get("obra", set()) != del_auditor["obra"], (
        "El fixture debería tener INV-14 fuera del nivel obra y el validador "
        "debería notarlo. Si esto pasa, el fixture dejó de estar roto."
    )
    assert "INV-14" not in normativo.get("obra", set())
    assert "INV-14" in del_auditor["obra"]
    assert "INV-14" in parsers.niveles_de_la_skill(skill_invariantes)["obra"]


def test_negativo_caza_un_recuento_desfasado(definitions, fixtures):
    """Si la skill se queda con el recuento viejo, el validador salta."""
    rota = (fixtures / "skill_recuento_desfasado.md").read_text(encoding="utf-8")

    afirmado = parsers.recuento_de_tipos_de_la_skill(rota)
    real = {tipo: len(ids) for tipo, ids in tipos_declarados(definitions).items()}

    assert afirmado != {t: real.get(t, 0) for t in afirmado}, (
        "El fixture debería afirmar un recuento distinto del real."
    )
    assert afirmado == {"regla": 11, "juez_llm": 5}


def test_negativo_un_documento_ilegible_revienta_en_vez_de_pasar(fixtures):
    """Un parser que no encuentra su tabla falla; no devuelve vacío.

    Es la diferencia entre un validador y un test que siempre pasa.
    """
    with pytest.raises(parsers.DocumentoIlegible):
        parsers.invariantes("# Un documento sin ninguna tabla de invariantes\n")

    with pytest.raises(parsers.DocumentoIlegible):
        parsers.niveles_del_auditor("# Sin fila del Auditor\n")
