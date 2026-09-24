"""La puerta de publicacion, compuesta (`SPEC-30` v4, `PLAN-30` E8).

`auditoria/publicacion.decidir` decide sobre datos ya resueltos; aqui se resuelven,
porque cruzan features —escaleta, cronologia, politica, auditoria— y componer es solo
de `orquestacion/` (`A-02`).

UNA RONDA
---------
1. `novela.cerrar` vuelve a comprobar el nivel obra: `INV-24`, `INV-25` e `INV-27`.
2. Los capitulos rendidos se leen del estado de sus escenas (`INV-29`), que desde
   `SPEC-30` `RF-11` sobrevive a la consolidacion.
3. `INV-21` se vuelve a mirar sobre el texto elegido de cada capitulo.
4. Lean se ejecuta **siempre**, aunque otra condicion ya haya fallado: `RF-04`
   informa de todas. Un Lean con violaciones deja un hallazgo `INV-28`.
5. `decidir`, y el veredicto se guarda con su numero de ronda.

LO QUE LA RONDA NUEVA YA NO ENCUENTRA
-------------------------------------
Los hallazgos no se cerraban nunca (hallazgo 2 del plan), y sin cerrarlos la puerta
no se abriria jamas despues de un reintento. Pero solo se cierra lo que **se volvio a
comprobar**: si `INV-24` falla, `cerrar` no juzga la obra entera y un `INV-27`
anterior no se ha vuelto a mirar, asi que sigue abierto. Y lo que sigue fallando se
queda con su hallazgo de antes, sin abrir otro igual: ni se marca `resuelto` lo que
no se arreglo, ni se duplica.
"""

from dataclasses import dataclass

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S
from app.commons.invariantes.registro import TODAS
from app.commons.politica.vetadas import coincidencias
from app.features.auditoria import publicacion as puerta
from app.features.auditoria import repository as veredictos
from app.features.cronologia import repository as cronologia
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela
from app.features.orquestacion.obra import _texto_elegido

NIVEL_OBRA = ("INV-24", "INV-25", "INV-27", "INV-28")


@dataclass(frozen=True)
class Evaluacion:
    decision: puerta.Decision
    ronda: int
    implicados: puerta.Implicados
    lean: puerta.ResultadoLean


def _abiertos_de_obra(con, escenas):
    capitulo = {e["id"]: e.get("capitulo") for e in escenas}
    return [dict(h, capitulo=capitulo[e["id"]]) for e in escenas
            for h in escaleta.hallazgos_abiertos(con, e["id"])]


def _conciliar(con, antes, despues, comprobadas, ronda):
    """Lo que la ronda nueva no encuentra se cierra; lo que sigue, conserva su hallazgo."""
    clave = lambda h: (h["invariante"], h["descripcion"])
    viejos = {clave(h): h for h in antes if h["invariante"] in comprobadas}
    ids_antes = {h["id"] for h in antes}
    nuevos = [h for h in despues if h["invariante"] in NIVEL_OBRA and h["id"] not in ids_antes]
    siguen = set()
    for h in nuevos:
        if clave(h) in viejos:
            escaleta.borrar_hallazgo_repetido(con, h["id"])
            siguen.add(clave(h))
    for k, h in viejos.items():
        if k not in siguen:
            escaleta.cerrar_hallazgo(con, h["id"], EH.RESUELTO,
                                     "la ronda {0} de la puerta ya no lo encuentra".format(ronda))


def evaluar(con, obra, ficha, lean, juez_de_obra, vetadas=()) -> Evaluacion:
    veredictos.asegurar_tablas(con)
    ronda = veredictos.rondas(con, obra) + 1
    escenas = escaleta.escenas_de(con, obra)
    antes = [h for h in _abiertos_de_obra(con, escenas) if h["invariante"] in NIVEL_OBRA]

    cierre = novela.cerrar(con, obra, ficha, juez_de_obra)
    comprobadas = {"INV-24", "INV-25", "INV-28"}
    if cierre["estado"] != "novela_incompleta":
        comprobadas.add("INV-27")

    resultado = lean.verificar(con, obra)
    if resultado.codigo == 1:
        escaleta.guardar_hallazgo(
            con, invariante="INV-28", verificador="lean", escena=escenas[-1]["id"],
            severidad=TODAS["INV-28"].severidad, estado=EH.ABIERTO.value,
            descripcion="; ".join("{0} {1}: {2}".format(
                v["invariante"], ",".join(v.get("eventos", [])), v.get("detalle", ""))
                for v in resultado.violaciones) or "violaciones sin detalle")

    despues = _abiertos_de_obra(con, escenas)
    _conciliar(con, antes, despues, comprobadas, ronda)
    hallazgos = _abiertos_de_obra(con, escenas)

    for e in escenas:
        for c in coincidencias(_texto_elegido(con, e) or "", list(vetadas)):
            hallazgos.append({"invariante": "INV-21", "severidad": S.BLOQUEANTE,
                              "estado": EH.ABIERTO, "capitulo": e.get("capitulo"),
                              "descripcion": "vetada en el texto elegido: {0}".format(c)})

    rendidos = sorted({e.get("capitulo") for e in escenas
                       if e["estado"] == EE.ACEPTADA_POR_RENDICION.value})
    decision = puerta.decidir(rendidos, hallazgos, resultado)
    implicados = puerta.capitulos_implicados(
        resultado.violaciones, {ev["id"]: ev["capitulo"]
                                for ev in cronologia.eventos_de(con, obra)},
        [h for h in hallazgos if h["invariante"] == "INV-27"])
    veredictos.guardar(con, obra, decision, resultado.codigo)
    return Evaluacion(decision, ronda, implicados, resultado)
