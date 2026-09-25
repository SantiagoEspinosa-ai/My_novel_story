"""Lo que se comprueba del plan sin juicio (`SPEC-26` `RF-06`).

El Revisor del plan juzga la fidelidad; **la cobertura la cuenta el codigo**.
Un plan con huecos vuelve al Planificador sin pasar por el Revisor: pagar un
juicio sobre un plan al que le falta un capitulo es pagar por algo que el
codigo ya sabe.

Cada hueco es una frase que nombra que falta y donde, porque es lo que el
Planificador leera en su siguiente intento.
"""

from datetime import datetime

from app.commons.dominio.destinatario import EXTENSION
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal as TE
from app.commons.politica.vetadas import coincidencias, formas_de_nombre
from app.commons.politica.personalizacion import nombres_mal_escritos


def _instante(texto):
    """La fecha de la fabula como objeto, o `None` si no se deja leer. La misma lectura que
    `cronologia/consultas._instante`; aqui aparte porque esta feature no importa de otra
    (`A-02`)."""
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


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

    # `F-213`: `INV-08` en su forma prevista. Hoy no hay donde declarar una analepsis
    # (`SPEC-24` sin plan), asi que un capitulo que retrocede en la fabula acaba en la
    # puerta de publicacion (`L-1`) con los diez escritos. Se devuelve aqui, sin pagarlos.
    anterior = None
    for c in plan.capitulos:
        for e in c.escenas:
            t = _instante(e.t_fabula)
            if t is None:
                continue
            if anterior is not None and t < anterior[1]:
                faltan.append(
                    "{0} ocurre en la fabula antes que {1} ({2} < {3}) [INV-08]: hoy no se "
                    "puede declarar una analepsis, asi que el tiempo de la fabula no puede "
                    "retroceder entre capitulos. Cuenta el recuerdo desde el presente (el "
                    "personaje lo recuerda) y deja la fecha de la escena en el presente".format(
                        c.id, anterior[0], e.t_fabula, anterior[2]))
            elif anterior is not None and t == anterior[1]:
                # Mismo instante y otro lugar es un personaje en dos sitios a la vez (`L-3`).
                faltan.append(
                    "{0} y {1} ocurren en el mismo instante ({2}) [INV-08]: dale a cada "
                    "escena su fecha y hora (AAAA-MM-DDTHH:MM), posterior a la de la "
                    "anterior".format(c.id, anterior[0], e.t_fabula))
            anterior = (c.id, t, e.t_fabula)

    vetadas = list(ficha.vetadas) + [f for nombre in ficha.nombres_vetados
                                     for f in formas_de_nombre(nombre)]
    for donde, texto in _textos_del_plan(plan):
        for co in coincidencias(texto or "", vetadas):
            faltan.append("{0} usa «{1}», que esta vetado".format(donde, co.fragmento))
    return faltan
