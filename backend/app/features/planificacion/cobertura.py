"""Lo que se comprueba del plan sin juicio (`SPEC-26` `RF-06`).

El Revisor del plan juzga la fidelidad; **la cobertura la cuenta el codigo**.
Un plan con huecos vuelve al Planificador sin pasar por el Revisor: pagar un
juicio sobre un plan al que le falta un capitulo es pagar por algo que el
codigo ya sabe.

Cada hueco es una frase que nombra que falta y donde, porque es lo que el
Planificador leera en su siguiente intento.
"""

from app.commons.dominio.destinatario import EXTENSION
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal as TE
from app.commons.politica.vetadas import coincidencias, formas_de_nombre
from app.commons.politica.personalizacion import nombres_mal_escritos


def _textos_del_plan(plan):
    """Todo lo que el plan escribe con palabras, con donde lo escribe."""
    for c in plan.capitulos:
        yield c.id, c.titulo
        for e in c.escenas:
            yield c.id, e.sinopsis
    for p in plan.mundo.personajes:
        yield "personajes", p.nombre
    for imp in plan.imprescindibles:
        yield imp.capitulo, " ".join(imp.palabras_clave)


def huecos(plan, ficha) -> list:
    faltan = []
    n = EXTENSION["capitulos"]
    if len(plan.capitulos) != n:
        faltan.append("el plan tiene {0} capitulos y tienen que ser {1} capitulos".format(
            len(plan.capitulos), n))
    for c in plan.capitulos:
        if len(c.escenas) != 1:
            faltan.append("{0} tiene {1} escenas: un capitulo es una escena "
                          "(`RF-01`)".format(c.id, len(c.escenas)))

    asignados = {imp.elemento for imp in plan.imprescindibles}
    for e in ficha.destinatario.elementos:
        if e.imprescindible and e.descripcion not in asignados:
            faltan.append("el imprescindible «{0}» no tiene capitulo en el "
                          "plan".format(e.descripcion))

    nombres_del_plan = {p.nombre for p in plan.mundo.personajes}
    # `SPEC-40` `RF-03`: estas objeciones vuelven al Planificador; ahi es «el protagonista».
    esperados = [("el protagonista", ficha.destinatario.nombre)] + [
        (e.tipo.value, e.nombre) for e in ficha.destinatario.elementos
        if e.imprescindible and e.tipo in (TE.PERSONA, TE.MASCOTA) and e.nombre]
    for quien, nombre in esperados:
        if nombre and nombre not in nombres_del_plan:
            faltan.append("{0} se llama «{1}» en la ficha y el plan no tiene ningun "
                          "personaje con ese nombre exacto".format(quien, nombre))
    conocidos = [n for _, n in esperados if n]
    for p in plan.mundo.personajes:
        for m in nombres_mal_escritos(p.nombre, conocidos):
            faltan.append("el personaje «{0}» parece «{1}» mal escrito".format(
                p.nombre, m.correcto))

    vetadas = list(ficha.vetadas) + [f for nombre in ficha.nombres_vetados
                                     for f in formas_de_nombre(nombre)]
    for donde, texto in _textos_del_plan(plan):
        for co in coincidencias(texto or "", vetadas):
            faltan.append("{0} usa «{1}», que esta vetado".format(donde, co.fragmento))
    return faltan
