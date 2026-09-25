"""Lo que dice cada validador de una obra, reunido (`SPEC-31` `RF-02`, `PLAN-31` E6).

Vive en `orquestacion/` porque cruza features —escaleta, auditoria, planificacion,
entrevista y el audit log— y componer es solo de aqui (`A-02`). La tabla la escribe
`evaluacion/tabla.py` con lo que devuelve `resultados`.

LA REGLA DE LECTURA
-------------------
**Sin constancia de ejecucion no hay «pasó».** La tabla `hallazgo` solo registra
violaciones, asi que para dar un pase hace falta otra prueba de que el validador miro.
Cada validador tiene la suya, y el que no la tiene dice «sin veredicto»:

| Validador | Constancia de que se ejecuto |
| --- | --- |
| `INV-01`..`INV-04`, `INV-17`, `INV-18` | Un borrador: guardarlo y pasarle las puertas es el mismo paso (`bucle.generar`) |
| `INV-21`, `INV-22` | Una escena que llego al canon (consolidada o rendida), o su rastro en el audit log. **Supone** que la lista de vetadas y la de nombres no venian vacias, que en la novela regalo es cierto (global y destinatario) y aqui no se comprueba |
| `INV-23` | Un borrador y algun imprescindible declarado en la obra |
| `INV-26` y cada criterio | Las notas de `valoracion_del_editor` (`PLAN-31` E4) |
| `INV-24`, `INV-25`, `INV-27`, `INV-28` (Lean), `INV-29`, la puerta | Una ronda en `veredicto_de_publicacion` |
| `schema.plan` | Las rondas de `plan_de_obra` |
| Las dos de la entrevista | El audit log de la obra y la entrevista |
| Cualquier otra, tambien las que se anadan | **Ninguna declarada: «sin veredicto».** `INV-05`, `INV-07`, `INV-08`, `INV-09`, `INV-13`, `INV-14` e `INV-15` estan aqui: o no corren en la novela regalo o corren sin dejar rastro (`INV-08` se evalua al cerrar el capitulo y su resultado no se guarda) |

Un hallazgo `sin_veredicto` nunca se lee como pase. Un hallazgo de escena `abierto` se
resolvio si la escena termino limpia (consolidada o aceptada); en una escena rendida o
donde la generacion se paro, sigue vigente y la celda dice «falló». Uno de obra se
resuelve solo si alguien lo cerro (`resuelto` o `descartado`).
"""

from app.commons import config
from app.commons.dominio.enumeraciones import CriterioDeEdicion
from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import NivelDeEvaluacion
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.invariantes import registro
from app.commons.politica import auditoria as audit_log
from app.features.auditoria import repository as veredictos
from app.features.entrevista import repository as entrevistas
from app.features.escaleta import repository as escaleta
from app.features.evaluacion import tabla
from app.features.evaluacion.tabla import Celda
from app.features.evaluacion.tabla import Resultado as R
from app.features.planificacion import repository as planes
from app.features.verificacion.puertas import INVARIANTES_DE_LA_PUERTA

TERMINADAS_LIMPIAS = (EE.CONSOLIDADA.value, EE.ACEPTADA.value)
EN_EL_CANON = TERMINADAS_LIMPIAS + (EE.ACEPTADA_POR_RENDICION.value,)
DE_LA_PUERTA = ("INV-24", "INV-25", "INV-27")
DE_LA_ENTREVISTA = (TD.INSTRUCCION_EN_TEXTO_LIBRE, TD.CONTRADICCION_DETECTADA,
                    TD.CONTRADICCION_RESUELTA, TD.BORRADO_AL_ENTREGAR)


def _sin(motivo):
    return Celda(R.SIN_VEREDICTO, motivo=motivo)


class _Obra:
    """Lo que se lee una vez de la base para juzgar todas las columnas."""

    def __init__(self, con, obra):
        escaleta.asegurar_tablas(con)
        self.con, self.obra = con, obra
        self.escenas = escaleta.escenas_de(con, obra)
        self.estado = {e["id"]: e["estado"] for e in self.escenas}
        self.hallazgos = [dict(h, escena=e["id"]) for e in self.escenas
                          for h in escaleta.hallazgos_de(con, e["id"])]
        self.con_borrador = [e for e in self.escenas if escaleta.intentos_de(con, e["id"])]
        audit_log.asegurar_tabla(con)
        self.decisiones = audit_log.decisiones(con, obra)
        self.puerta = veredictos.ultimo(con, obra)
        try:
            self.plan = planes.versiones(con, obra)
        except Exception:  # la tabla la crea planificacion; sin ella no hubo plan
            self.plan = []
        entrevistas.asegurar_tablas(con)
        self.entrevistas = [entrevistas.leer(con, i) for i in entrevistas.de_la_obra(con, obra)]

    def existe(self):
        # El plan y el veredicto de la puerta tambien cuentan: una obra cuyo plan no aprobo
        # el Revisor se ejecuto, y sin esto salia «sin ejecutar» entera (el brief temporal,
        # `R3`); un veredicto de publicacion es constancia de que la puerta miro.
        return bool(self.escenas or self.entrevistas or self.plan or self.puerta
                    or any(d["tipo"] in DE_LA_ENTREVISTA for d in self.decisiones))

    def decisiones_de(self, tipo):
        return [d for d in self.decisiones if d["tipo"] is tipo]

    def en_el_canon(self):
        return [e for e in self.escenas if e["estado"] in EN_EL_CANON]


def _vigente(o, h, de_escena):
    if h["estado"] is not EH.ABIERTO:
        return False
    if de_escena:
        return o.estado.get(h["escena"]) not in TERMINADAS_LIMPIAS
    return True


def _por_hallazgos(o, inv, constancia, motivo_sin_constancia, de_escena=True):
    propios = [h for h in o.hallazgos if h["invariante"] == inv]
    disparos = len([h for h in propios if h["estado"] is not EH.SIN_VEREDICTO])
    if any(_vigente(o, h, de_escena) for h in propios):
        return Celda(R.FALLO, disparos)
    if any(h["estado"] is EH.SIN_VEREDICTO for h in propios):
        return _sin("un hallazgo sin veredicto: el validador no llego a juzgar")
    if not constancia and not propios:
        return _sin(motivo_sin_constancia)
    return Celda(R.PASO, disparos)


def _vetadas_o_nombres(o, disparo, parada, inv):
    disparos = len(o.decisiones_de(disparo))
    en_la_puerta = any(c.get("invariante") == inv for c in (o.puerta or {}).get("condiciones", []))
    if o.decisiones_de(parada) or en_la_puerta:
        return Celda(R.FALLO, disparos)
    if not (disparos or o.en_el_canon() or o.puerta):
        return _sin("ninguna escena llego al canon y no hay rastro en el audit log")
    return Celda(R.PASO, disparos)


def _editor(o, umbral):
    """Por criterio, la nota de la version que quedo como texto de cada escena."""
    celdas = {c.value: [] for c in CriterioDeEdicion}
    for e in o.con_borrador:
        notas = escaleta.valoraciones_del_editor(o.con, e["id"])
        if not notas:
            continue
        final = e.get("borrador_aceptado") or escaleta.intentos_de(o.con, e["id"])
        for criterio in celdas:
            propias = [n for n in notas if n["criterio"] == criterio]
            disparos = len([n for n in propias if n["nota"] < umbral])
            en_la_final = [n for n in propias if n["version"] == final]
            if not en_la_final:
                celdas[criterio].append(_sin("el texto elegido no tiene nota del Editor"))
            elif en_la_final[0]["nota"] < umbral:
                celdas[criterio].append(Celda(R.FALLO, disparos))
            else:
                celdas[criterio].append(Celda(R.PASO, disparos))
    salida = {}
    for criterio, lista in celdas.items():
        salida["INV-26." + criterio] = _peor(lista) if lista else _sin(
            "no hay ninguna nota del Editor guardada")
    ilegibles = [h for h in o.hallazgos if h["invariante"] == "INV-26"
                 and h["estado"] is EH.SIN_VEREDICTO]
    todas = list(salida.values())
    if ilegibles:
        todas.append(_sin("el Editor devolvio una valoracion ilegible"))
    salida["INV-26"] = _peor(todas)
    return salida


def _peor(celdas):
    for r in (R.FALLO, R.SIN_VEREDICTO):
        malas = [c for c in celdas if c.resultado is r]
        if malas:
            return Celda(r, sum(c.disparos for c in celdas), malas[0].motivo)
    return Celda(R.PASO, sum(c.disparos for c in celdas))


def _puerta(o):
    sin_puerta = "la puerta de publicacion no llego a ejecutarse"
    salida = {}
    for inv in DE_LA_PUERTA:
        salida[inv] = _por_hallazgos(o, inv, o.puerta is not None, sin_puerta, de_escena=False)
    if (salida["INV-24"].resultado is R.FALLO
            and not any(h["invariante"] == "INV-27" for h in o.hallazgos)):
        salida["INV-27"] = Celda(R.NO_APLICA, motivo="no se juzga una novela incompleta (INV-24)")
    if o.puerta is None:
        for inv in ("INV-28", "INV-29", "publicacion"):
            salida[inv] = _sin(sin_puerta)
        return salida
    codigo = o.puerta["codigo_lean"]
    lean = [h for h in o.hallazgos if h["invariante"] == "INV-28"]
    salida["INV-28"] = (Celda(R.PASO, len(lean)) if codigo == 0 else
                        Celda(R.FALLO, len(lean)) if codigo == 1 else
                        _sin("Lean devolvio {0}: 2 no es 0 (SPEC-30 RF-09)".format(codigo)))
    rendidos = any(c.get("invariante") == "INV-29" for c in o.puerta["condiciones"])
    salida["INV-29"] = Celda(R.FALLO if rendidos else R.PASO)
    no_publicadas = o.puerta["ronda"] - (1 if o.puerta["publica"] else 0)
    salida["publicacion"] = Celda(R.PASO if o.puerta["publica"] else R.FALLO, no_publicadas)
    return salida


def _plan(o):
    if not o.plan:
        return _sin("no hay ninguna ronda del plan")
    disparos = len([v for v in o.plan if v["origen"] == "esquema"])
    if any(v["aprobado"] for v in o.plan):
        return Celda(R.PASO, disparos)
    return Celda(R.FALLO, disparos)


def _revisor(o):
    """El Revisor del plan (decision del autor, 2026-09-25). Los disparos son las rondas
    que rechazo; falla si nunca lo aprobo. En el brief temporal, fallar es acertar: son las
    incoherencias que el brief provoca, y lo que esperaba lo dice el propio brief."""
    rondas = [v for v in o.plan if v["origen"] == "revisor"]
    if not rondas:
        return _sin("ninguna ronda del plan llego al Revisor")
    rechazos = len([v for v in rondas if not v["aprobado"]])
    if any(v["aprobado"] for v in rondas):
        return Celda(R.PASO, rechazos)
    return Celda(R.FALLO, rechazos)


def _entrevista(o):
    if not (o.entrevistas or any(d["tipo"] in DE_LA_ENTREVISTA for d in o.decisiones)):
        motivo = "el brief entra por ficha: no hubo entrevista"
        return {"entrevista.instrucciones": Celda(R.NO_APLICA, motivo=motivo),
                "entrevista.contradicciones": Celda(R.NO_APLICA, motivo=motivo)}
    inyecciones = len(o.decisiones_de(TD.INSTRUCCION_EN_TEXTO_LIBRE))
    detectadas = len(o.decisiones_de(TD.CONTRADICCION_DETECTADA))
    cerrada = any(e is not None and e.cerrada for e in o.entrevistas) or bool(
        o.decisiones_de(TD.BORRADO_AL_ENTREGAR))
    return {
        "entrevista.instrucciones": Celda(R.PASO, inyecciones) if inyecciones else _sin(
            "el detector no disparo: no consta si se pego texto libre, y una instruccion "
            "que no se parece a ningun patron tampoco dispara (ver el red-team log)"),
        "entrevista.contradicciones": Celda(R.PASO, detectadas) if cerrada else _sin(
            "la entrevista no cerro"),
    }


def resultados(con, obra, umbral=None) -> dict:
    """`{columna: Celda}` para todas las columnas de `tabla.columnas()`."""
    umbral = config.UMBRAL_DEL_EDITOR if umbral is None else umbral
    o = _Obra(con, obra)
    fijas = {c: tabla.celda_fija(c) for c in tabla.columnas()}
    if not o.existe():
        return {c: fijas[c] or Celda(R.SIN_EJECUTAR) for c in tabla.columnas()}
    calculadas = {}
    hay_borrador = bool(o.con_borrador)
    sin_borrador = "ninguna escena tiene un borrador: ninguna puerta miro nada"
    for inv in INVARIANTES_DE_LA_PUERTA:
        calculadas[inv] = _por_hallazgos(o, inv, hay_borrador, sin_borrador)
    imprescindibles = [h for h in escaleta.hechos_declarados(con, obra)
                       if h["id"].startswith("imp-")]
    calculadas["INV-23"] = _por_hallazgos(o, "INV-23", hay_borrador and bool(imprescindibles),
                                          "sin borrador o sin imprescindibles declarados")
    calculadas["INV-21"] = _vetadas_o_nombres(o, TD.COINCIDENCIA_VETADA, TD.PARADA_POR_VETADA,
                                              "INV-21")
    calculadas["INV-22"] = _vetadas_o_nombres(o, TD.NOMBRE_MAL_ESCRITO, TD.PARADA_POR_NOMBRE,
                                              "INV-22")
    calculadas.update(_editor(o, umbral))
    calculadas.update(_puerta(o))
    calculadas["schema.plan"] = _plan(o)
    calculadas["revisor.plan"] = _revisor(o)
    calculadas.update(_entrevista(o))
    salida = {}
    for c in tabla.columnas():
        salida[c] = fijas[c] or calculadas.get(c) or _por_hallazgos(
            o, c, False, "sin constancia de ejecucion: nadie declara donde queda que se "
                         "ejecuto", de_escena=_de_escena(c))
    return salida


def _de_escena(columna):
    inv = registro.TODAS.get(columna)
    return inv is None or inv.nivel is NivelDeEvaluacion.ESCENA
