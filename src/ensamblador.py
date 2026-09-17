"""Ensamblador: el manuscrito y el informe de validacion (spec 5.2).

Este modulo NO lee ni escribe archivos, NO toca la red y NO reescribe nada de lo
que le pasan. Recibe datos ya cargados y devuelve texto. Quien lo guarda en
disco es `src/orquestacion.py`.

POR QUE EL ENSAMBLADOR NO CORRIGE NADA
--------------------------------------
Es la regla mas facil de romper y la que mas importa. Cuando se tiene delante el
manuscrito entero es muy tentador arreglar aqui una transicion floja o unificar
un nombre que baila. No se hace. Un capitulo que llega al manuscrito ha pasado
por tres validadores y, si no los paso, esta marcado como tal en el informe. Si
el ensamblador retocara el texto, el informe dejaria de describir el manuscrito:
diria que el capitulo 7 se acepto con tres problemas, pero el capitulo 7 del
manuscrito ya no seria ese. La trazabilidad entre lo que se audito y lo que se
entrega es lo unico que hace util al informe.

QUE TIENE QUE PODER CONTESTAR EL INFORME
----------------------------------------
No es un registro de todo lo que paso, sino la respuesta a cinco preguntas que
alguien se hara al leer una novela generada:

    1. Que capitulos no pasaron limpios, y con que problemas concretos.
    2. Cuantos intentos costo cada uno, y que modelo acabo resolviendolo.
    3. Que problemas quedaron sin resolver en el texto que se entrega.
    4. Si las ventanas de contexto crecian con el numero de capitulo, que es la
       senal de que el proyecto no escalaria a una novela larga.
    5. Cuanto costo todo, en delegaciones.
"""

from __future__ import annotations

from src import puntuacion

# Estados posibles de un capitulo en el informe.
APROBADO = "APROBADO"
ACEPTADO = "ACEPTADO_POR_PUNTUACION"
SIN_GENERAR = "SIN_GENERAR"


# ---------------------------------------------------------------------------
# Manuscrito
# ---------------------------------------------------------------------------


def portada(biblia, config, fecha):
    """La portada del manuscrito.

    Lleva el titulo, el genero y la fecha, y nada mas. En concreto no lleva la
    premisa ni el conflicto central, que estan en la biblia: una portada que
    resume la trama le estropea la lectura a quien abra el archivo por arriba,
    que es lo que hace todo el mundo.
    """
    titulo = (biblia.get("titulo") or "Sin titulo").strip()
    genero = config.get("novela", {}).get("genero", "")
    lineas = [
        "# {0}".format(titulo),
        "",
        "*{0}*".format(genero.capitalize()) if genero else "",
        "",
        "Generada el {0}.".format(fecha),
        "",
        "---",
        "",
    ]
    return "\n".join(linea for linea in lineas if linea is not None)


def manuscrito(biblia, config, fecha, capitulos):
    """Portada mas los capitulos concatenados en orden (spec 5.2).

    `capitulos` es una lista de (numero, texto) ya ordenada. Los capitulos que
    no llegaron a generarse NO se inventan ni se rellenan con un hueco: no
    aparecen, y el informe explica por que. Un manuscrito con un capitulo vacio
    seria un manuscrito que miente.

    Cada texto ya trae su propia linea de titulo (`# Capitulo N — ...`), que la
    pone el escritor, asi que aqui no se anade ninguna cabecera mas.
    """
    partes = [portada(biblia, config, fecha)]
    for _, texto in capitulos:
        partes.append(texto.strip())
        partes.append("")
    return "\n".join(partes).rstrip() + "\n"


# ---------------------------------------------------------------------------
# Informe de validacion
# ---------------------------------------------------------------------------


def _intento_elegido(intentos):
    """El intento cuyo texto acabo en el manuscrito."""
    for intento in intentos:
        if intento.get("elegido"):
            return intento
    return intentos[-1] if intentos else None


def estado_de_capitulo(numero, intentos, aprobados, marcados):
    """APROBADO, ACEPTADO_POR_PUNTUACION o SIN_GENERAR."""
    if numero in aprobados:
        return APROBADO
    if numero in marcados:
        return ACEPTADO
    return SIN_GENERAR


def _problemas_sin_resolver(intento):
    """Los problemas del intento que se entrega, no los de todos los intentos.

    Es la diferencia entre "esto se llego a detectar alguna vez" y "esto sigue
    estando en el texto que vas a leer". Solo la segunda lista sirve para
    decidir si retocas un capitulo a mano.
    """
    if intento is None:
        return []
    problemas = []
    for veredicto in intento.get("veredictos", []):
        for problema in veredicto.get("problemas", []):
            problemas.append(dict(problema, validador=veredicto.get("validador")))
    return problemas


def _tabla_resumen(capitulos):
    lineas = [
        "| Capitulo | Estado | Intentos | Modelo que lo resolvio | Puntuacion | Problemas sin resolver |",
        "|---|---|---|---|---|---|",
    ]
    for capitulo in capitulos:
        intentos = capitulo["intentos"]
        elegido = _intento_elegido(intentos)
        lineas.append(
            "| {0} | {1} | {2} | {3} | {4} | {5} |".format(
                capitulo["numero"],
                capitulo["estado"],
                len(intentos),
                (elegido or {}).get("modelo", "—"),
                (elegido or {}).get("puntuacion", "—"),
                len(_problemas_sin_resolver(elegido)),
            )
        )
    return lineas


def _tabla_ventanas(capitulos):
    """Tabla de tamano de la ventana del escritor, capitulo a capitulo.

    Es el criterio de aceptacion 9 del spec convertido en algo que se mira de un
    vistazo: si la ventana del capitulo 12 es mayor que la del 3, la
    compactacion no esta haciendo su trabajo y la arquitectura no escala.
    """
    lineas = [
        "| Capitulo | Tokens estimados de la ventana del escritor | Recortes aplicados |",
        "|---|---|---|",
    ]
    for capitulo in capitulos:
        ventana = capitulo.get("ventana") or {}
        recortes = ventana.get("recortes") or []
        lineas.append(
            "| {0} | {1} | {2} |".format(
                capitulo["numero"],
                ventana.get("tokens", "—"),
                "; ".join(recortes) if recortes else "ninguno",
            )
        )
    return lineas


# Primer capitulo cuya ventana tiene ya la forma completa: biblia, hechos,
# resumenes de 1..N-2 y texto entero del capitulo N-1. El 1 no tiene capitulo
# anterior ni resumenes, y el 2 tiene capitulo anterior pero todavia ningun
# resumen, asi que sus ventanas son estructuralmente mas pequenas. Compararlas
# con las del final daria una alarma en toda novela, incluida una sana.
PRIMER_CAPITULO_COMPARABLE = 3


def _alarma_de_ventanas(capitulos):
    """Avisa si las ventanas crecen con el numero de capitulo.

    Compara solo capitulos con la ventana completa (del 3 en adelante), que es
    exactamente lo que pide el criterio de aceptacion 9 del spec cuando dice
    "el capitulo 12 no es mayor que el capitulo 3".
    """
    medidos = [
        (c["numero"], (c.get("ventana") or {}).get("tokens"))
        for c in capitulos
        if c["numero"] >= PRIMER_CAPITULO_COMPARABLE
        and (c.get("ventana") or {}).get("tokens") is not None
    ]
    if len(medidos) < 2:
        return [
            "",
            "Esta novela es demasiado corta para medir si la ventana crece: "
            "hacen falta al menos dos capitulos a partir del {0}, que es el "
            "primero cuya ventana ya lleva resumenes y capitulo anterior. Con "
            "menos, la comparacion solo mediria que el capitulo 1 no tiene "
            "pasado.".format(PRIMER_CAPITULO_COMPARABLE),
        ]

    primero, ultimo = medidos[0], medidos[-1]
    if ultimo[1] <= primero[1]:
        return [
            "",
            "La ventana del capitulo {0} ({1} tokens) no es mayor que la del "
            "capitulo {2} ({3} tokens): el presupuesto de contexto aguanta.".format(
                ultimo[0], ultimo[1], primero[0], primero[1]
            ),
        ]
    return [
        "",
        "**ALARMA.** La ventana del capitulo {0} ({1} tokens) es mayor que la "
        "del capitulo {2} ({3} tokens). La ventana esta creciendo con N. En una "
        "novela mas larga esto acaba en recortes, y los recortes se comen "
        "primero los hechos y los resumenes, que es justo lo que sostiene la "
        "continuidad. Es la senal de alarma mas importante de este "
        "informe.".format(ultimo[0], ultimo[1], primero[0], primero[1]),
    ]


def _bloque_de_capitulo(capitulo):
    numero = capitulo["numero"]
    intentos = capitulo["intentos"]
    elegido = _intento_elegido(intentos)
    lineas = ["### Capitulo {0} — {1}".format(numero, capitulo["estado"]), ""]

    if capitulo["estado"] == SIN_GENERAR:
        lineas += [
            "Este capitulo no llegó a generarse, asi que no aparece en el "
            "manuscrito. No cuenta como hecho: al relanzar la generacion se "
            "reintentara.",
            "",
        ]
        return lineas

    lineas += [
        "- Intentos: **{0}**".format(len(intentos)),
        "- Modelo que lo resolvio: **{0}**".format((elegido or {}).get("modelo", "—")),
        "- Puntuacion del intento entregado: **{0}**".format(
            (elegido or {}).get("puntuacion", "—")
        ),
        "",
    ]

    if len(intentos) > 1:
        lineas.append("#### Recorrido de los intentos")
        lineas.append("")
        lineas.append("| Intento | Modelo | Veredictos | Puntuacion | |")
        lineas.append("|---|---|---|---|---|")
        for intento in intentos:
            veredictos = "; ".join(
                "{0}: {1}".format(v.get("validador"), v.get("veredicto"))
                for v in intento.get("veredictos", [])
            )
            lineas.append("| {0} | {1} | {2} | {3} | {4} |".format(
                intento.get("intento"),
                intento.get("modelo"),
                veredictos or "—",
                intento.get("puntuacion", "—"),
                "**entregado**" if intento is elegido else "",
            ))
        lineas.append("")

    problemas = _problemas_sin_resolver(elegido)
    if not problemas:
        lineas += ["Los tres validadores dijeron `PASA`. Sin problemas pendientes.", ""]
        return lineas

    lineas += [
        "#### Problemas sin resolver en el texto entregado",
        "",
        "Cada problema trae la evidencia: el fragmento concreto del capitulo. "
        "Es lo que te permite ir al manuscrito y juzgar por ti mismo si el "
        "validador tenia razon.",
        "",
    ]
    orden = {"alta": 0, "media": 1, "baja": 2}
    for problema in sorted(problemas, key=lambda p: orden.get(p.get("gravedad"), 9)):
        lineas.append("- **[{0}]** ({1}) {2}".format(
            problema.get("gravedad", "?"),
            problema.get("validador", "?"),
            problema.get("descripcion", ""),
        ))
        if problema.get("evidencia"):
            lineas.append("  - *Evidencia:* {0}".format(problema["evidencia"]))
        if problema.get("correccion_sugerida"):
            lineas.append("  - *Correccion sugerida:* {0}".format(
                problema["correccion_sugerida"]
            ))
    lineas.append("")
    return lineas


def informe(biblia, config, fecha, capitulos, estado):
    """El informe de validacion completo (spec 5.2).

    `capitulos` es una lista de diccionarios con `numero`, `estado`, `intentos`
    y `ventana`. `estado` es el contenido de estado.json.
    """
    titulo = (biblia.get("titulo") or "Sin titulo").strip()
    total = config.get("estructura", {}).get("num_capitulos", len(capitulos))
    aprobados = sum(1 for c in capitulos if c["estado"] == APROBADO)
    aceptados = sum(1 for c in capitulos if c["estado"] == ACEPTADO)
    sin_generar = sum(1 for c in capitulos if c["estado"] == SIN_GENERAR)

    lineas = [
        "# Informe de validacion — {0}".format(titulo),
        "",
        "Generado el {0}. Genero: {1}. Capitulos previstos: {2}.".format(
            fecha, config.get("novela", {}).get("genero", "?"), total
        ),
        "",
        "- Aprobados limpios (los tres validadores dijeron `PASA`): **{0}**".format(
            aprobados
        ),
        "- Aceptados por puntuacion (se agoto la escalera): **{0}**".format(aceptados),
        "- Sin generar: **{0}**".format(sin_generar),
        "- Delegaciones a subagentes gastadas: **{0}**".format(
            estado.get("delegaciones", "?")
        ),
        "",
        "## Resumen por capitulo",
        "",
    ]
    lineas += _tabla_resumen(capitulos)
    lineas += [
        "",
        "Menor puntuacion es mejor. **Solo tiene sentido comparar puntuaciones "
        "entre intentos de un mismo capitulo de esta misma generacion**: la "
        "temperatura de los validadores no se puede fijar, asi que una "
        "diferencia de uno o dos puntos puede ser ruido del validador y no una "
        "propiedad del texto (`DECISIONES.md`, decision 9).",
        "",
        "## Presupuesto de contexto",
        "",
    ]
    lineas += _tabla_ventanas(capitulos)
    lineas += _alarma_de_ventanas(capitulos)
    lineas += ["", "## Detalle por capitulo", ""]

    for capitulo in capitulos:
        lineas += _bloque_de_capitulo(capitulo)

    indeterminados = sum(
        1
        for capitulo in capitulos
        for intento in capitulo["intentos"]
        for veredicto in intento.get("veredictos", [])
        if veredicto.get("veredicto") == puntuacion.INDETERMINADO
    )
    if indeterminados:
        lineas += [
            "## Validadores que no devolvieron JSON",
            "",
            "Hubo **{0}** veredicto(s) `INDETERMINADO`: el validador no "
            "devolvio JSON interpretable y conto como `FALLO` (regla 2). Uno "
            "suelto es ruido; varios seguidos significan que el modelo "
            "validador no respeta el formato y hay que cambiar "
            "`modelos.validadores`.".format(indeterminados),
            "",
        ]

    return "\n".join(lineas).rstrip() + "\n"
