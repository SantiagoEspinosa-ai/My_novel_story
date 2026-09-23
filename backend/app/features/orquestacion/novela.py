"""La novela regalo de principio a fin (`SPEC-26`): ficha → plan → obra → texto.

Compone features, que es lo unico autorizado a `orquestacion/` (`A-02`).

`montar` es lo que hacia `preparar` en `obra_diez_capitulos.py`, llevado a
`app/` para poder probarlo: la forma de la obra vivia en un guion y por eso nadie
la pudo discutir en diez capitulos (`F-56`).
"""

from app.commons.dominio.destinatario import EXTENSION
from app.features.brief import repository as brief
from app.features.consolidacion import aplicar, deltas, memoria, mundo
from app.features.cronologia import repository as usos
from app.features.escaleta import repository as escaleta
from app.features.observabilidad import repository as observabilidad


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
