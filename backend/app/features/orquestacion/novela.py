"""La novela regalo de principio a fin (`SPEC-26`): ficha → plan → obra → texto.

Compone features, que es lo unico autorizado a `orquestacion/` (`A-02`).

`montar` es lo que hacia `preparar` en `obra_diez_capitulos.py`, llevado a
`app/` para poder probarlo: la forma de la obra vivia en un guion y por eso nadie
la pudo discutir en diez capitulos (`F-56`).
"""

from app.commons import config
from app.commons.dominio.destinatario import EXTENSION
from app.commons.invariantes.registro import TODAS
from app.commons.politica.personalizacion import frases_repetidas, repeticiones
from app.features.brief import repository as brief
from app.features.consolidacion import aplicar, deltas, memoria, mundo
from app.features.cronologia import repository as usos
from app.features.escaleta import repository as escaleta
from app.features.observabilidad import repository as observabilidad
from app.features.orquestacion.obra import _texto_elegido


def _id_imprescindible(n):
    return "imp-{0:02d}".format(n)


def montar(con, obra, ficha, aprobado):
    """Deja la obra lista para escribir a partir del plan aprobado.

    **No reinicia una obra ya montada**: si la escaleta existe, no se toca. Es
    lo que hace que relanzar tras una caida siga desde el ultimo capitulo
    consolidado en vez de rehacer el plan encima.
    """
    plan = aprobado.plan
    for m in (escaleta, aplicar, memoria, deltas, usos, observabilidad):
        m.asegurar_tablas(con)
    if escaleta.escenas_de(con, obra):
        return False
    brief.alta_de_obra(con, obra, {"titulo": aprobado.titulo,
                                   "premisa": aprobado.premisa,
                                   "genero": ficha.genero.value if ficha.genero else None},
                       [c.id for c in plan.capitulos])
    aplicar.sembrar(con, {p.id: (p.estado_vital.value, p.empieza_en)
                          for p in plan.mundo.personajes})
    for p in plan.mundo.personajes:
        if p.fecha_de_nacimiento:
            aplicar.fijar_fecha_de_nacimiento(con, p.id, p.fecha_de_nacimiento)
    mundo.sembrar_lugares(con, {l.id: l.accesos for l in plan.mundo.lugares})
    minimo, maximo = EXTENSION["palabras_por_capitulo"]
    for c in plan.capitulos:
        e = c.escenas[0]
        escaleta.guardar_escaleta(con, obra, [{
            "id": "{0}-e1".format(c.id), "orden": 1, "capitulo": c.id,
            "cambio_de_valor": {"eje": e.eje, "signo": e.signo},
            "pov": e.pov, "lugar": e.lugar, "t_fabula": e.t_fabula,
            "beats": [{"id": "{0}-b1".format(c.id), "establece": e.establece}],
            "longitud_objetivo": [minimo, maximo]}])
    # Los imprescindibles son hechos de la novela: es lo que deja que `INV-24`
    # los busque en la relacion `usa` como cualquier otro hecho.
    escaleta.declarar_hechos(
        con, obra,
        [{"id": h.id, "enunciado": h.enunciado} for h in plan.hechos]
        + [{"id": _id_imprescindible(n), "enunciado": imp.elemento,
            "previsto_en": "{0}-e1".format(imp.capitulo)}
           for n, imp in enumerate(plan.imprescindibles, 1)])
    return True


# --- El nivel obra (`SPEC-26` `RF-12`, `RF-15`, `RF-16`) --------------------------

PROMPT_JUICIO_DE_OBRA = """Juzga una novela para regalar entera, a partir de los
resumenes de sus capitulos y del texto completo del ultimo.

¿Tiene arco -empieza, se complica y se cierra-? ¿El final es abrupto: corta sin
resolver lo que la historia abrio?

RESUMENES DE LOS CAPITULOS
{resumenes}

ULTIMO CAPITULO, COMPLETO
{ultimo}

Devuelve un unico objeto JSON:
{{"arco_cerrado": true|false, "final_abrupto": true|false, "justificacion": "..."}}
"""


def _hallazgo(con, inv, escena, estado, descripcion):
    escaleta.guardar_hallazgo(con, invariante=inv, verificador="auditor_de_obra",
                              escena=escena, severidad=TODAS[inv].severidad,
                              estado=estado, descripcion=descripcion)
    return {"invariante": inv, "escena": escena, "estado": estado,
            "descripcion": descripcion}


def _juicio_de_obra(con, obra, escenas, juez):
    """`INV-27`. **Nunca la obra entera** (`CLAUDE.md`): los resumenes y el
    ultimo capitulo, que es lo que hace falta para ver un final abrupto."""
    resumenes = memoria.resumenes_hasta(con, 10 ** 9, obra=obra)
    ultimo = escenas[-1]
    bruto = juez.llamar(PROMPT_JUICIO_DE_OBRA.format(
        resumenes="\n".join("- {0}: {1}".format(r["escena"], r["texto"])
                            for r in resumenes) or "(ninguno)",
        ultimo=_texto_elegido(con, ultimo) or ""))
    if (not isinstance(bruto, dict) or not isinstance(bruto.get("arco_cerrado"), bool)
            or not isinstance(bruto.get("final_abrupto"), bool)):
        return [_hallazgo(con, "INV-27", ultimo["id"], "sin_veredicto",
                          "el juicio de obra no devolvio un veredicto legible")]
    problemas = []
    if not bruto["arco_cerrado"]:
        problemas.append("el arco no se cierra")
    if bruto["final_abrupto"]:
        problemas.append("el final es abrupto")
    if not problemas:
        return []
    return [_hallazgo(con, "INV-27", ultimo["id"], "abierto", "{0}: {1}".format(
        " y ".join(problemas), bruto.get("justificacion") or ""))]


def cerrar(con, obra, ficha, juez_de_obra, umbral_nombre=None, longitud_frase=None):
    """Lo que solo se puede comprobar con la novela entera escrita.

    `INV-24` es `bloqueante`: con un imprescindible sin aparecer, la novela **no
    se da por terminada** y no se juzga entera. `INV-25` e `INV-27` dejan
    hallazgos; que bloquea la publicacion lo decide otra spec.
    """
    umbral_nombre = umbral_nombre or config.UMBRAL_REPETICION_NOMBRE
    longitud_frase = longitud_frase or config.LONGITUD_FRASE_REPETIDA
    escenas = escaleta.escenas_de(con, obra)

    faltan = []
    for h in escaleta.hechos_declarados(con, obra):
        if h["id"].startswith("imp-") and not usos.usos_de_hecho(con, h["id"]):
            faltan.append(h["enunciado"])
            _hallazgo(con, "INV-24", escenas[-1]["id"], "abierto",
                      "«{0}» no aparece en ningun capitulo".format(h["enunciado"]))

    textos = {e["id"]: _texto_elegido(con, e) or "" for e in escenas}
    repetidas = []
    for e in escenas:
        veces = repeticiones(textos[e["id"]], ficha.destinatario.nombre, umbral_nombre)
        if veces:
            repetidas.append((e["id"], veces))
            _hallazgo(con, "INV-25", e["id"], "abierto",
                      "el nombre del destinatario aparece {0} veces (umbral {1})".format(
                          veces, umbral_nombre))
    frases = frases_repetidas(textos, longitud_frase)
    for f in frases:
        _hallazgo(con, "INV-25", f.capitulos[0], "abierto",
                  "frase repetida en {0}: «{1}»".format(", ".join(f.capitulos), f.frase))

    if faltan:
        return {"estado": "novela_incompleta", "faltan": faltan,
                "repeticiones": repetidas, "frases": frases, "juicio": []}
    return {"estado": "terminada", "faltan": [], "repeticiones": repetidas,
            "frases": frases, "juicio": _juicio_de_obra(con, obra, escenas, juez_de_obra)}
