"""De la ficha a un plan aprobado (`SPEC-26` `RF-02`..`RF-07`).

Cada ronda: el Planificador propone; el codigo cuenta la cobertura; si no hay
huecos, el Revisor compara el plan con la ficha. Un rechazo de cobertura o del
Revisor gasta una ronda y sus objeciones entran en la siguiente. Tras `tope`
rondas sin aprobar, **la generacion no empieza** (`PlanNoAprobado`).

`F-68`: un plan que no cumple el esquema **no gasta ronda**. Se repite, con el
error como objecion, hasta `tope_de_formato` veces en toda la planificacion -el
mismo tope que un fallo de transporte-; pasado ese tope, tampoco empieza. En la
segunda ejecucion real dos de las tres rondas se fueron en formato y el Revisor
solo llego a ver un plan.

Solo entran las objeciones **de la ronda anterior**: acumularlas todas haria que
el Planificador siguiera corrigiendo cosas que ya arreglo.
"""

import json
from dataclasses import dataclass

from pydantic import ValidationError

from app.commons import config
from app.commons.configuracion.esquemas import PlanDeLaObra
from app.commons.dominio.destinatario import EXTENSION
from app.commons.configuracion.esquemas import rango_de_palabras
from app.features.planificacion.ids import acotar_a_la_obra
from app.commons.politica import vista_de_agentes
from app.features.planificacion import cobertura
from app.features.planificacion import repository as repo

PROMPT_PLANIFICADOR = """Planifica una novela personalizada a partir de esta ficha.

FICHA (lo unico que se sabe; no inventes nada que la contradiga)
{ficha}

PREMISA Y TITULO (los decidio la entrevista; no los cambies)
{premisa}
{titulo}

FORMA
{capitulos} capitulos. Cada capitulo es UNA escena de {minimo} a {maximo} palabras.
{objeciones}
Devuelve un unico objeto JSON: {{"plan": {{...}}}}, con el plan de esta forma:
  mundo: lugares [{{id, nombre, accesos}}] y personajes [{{id, nombre,
    empieza_en, fecha_de_nacimiento}}]. El protagonista y cada persona o
    mascota de la ficha van con su nombre EXACTO.
  capitulos: [{{id: "cap-01".."cap-10", titulo, escenas: [{{eje, signo, lugar,
    pov, sinopsis, t_fabula, personajes_presentes}}]}}], con una sola escena.
    personajes_presentes son los id de los personajes que estan en la escena,
    el pov incluido; cada uno tiene que estar declarado en personajes.
    t_fabula es la fecha y la hora de la escena (AAAA-MM-DDTHH:MM), distinta
    en cada escena y posterior a la de la anterior: la t_fabula no retrocede
    ni se repite. Un recuerdo se cuenta desde el presente, con la fecha de la
    escena en el presente, porque hoy no se puede declarar una analepsis.
  imprescindibles: [{{elemento, capitulo, palabras_clave}}]: elemento es la
    descripcion literal de cada elemento imprescindible de la ficha.
  exclusiones_previstas: [{{personaje, capitulo, estado_vital}}] si alguien
    sale de la historia.
Ejes validos: seguridad, conocimiento, control, vinculo, cordura, vida.
Signos: positivo, negativo. Ninguna palabra ni nombre vetado en el plan.
No anadas ningun campo que no este en esta forma: el sistema rechaza el plan
entero si trae un campo de mas. Los `accesos` de un lugar son identificadores
de otros lugares declarados en `lugares` (por ejemplo "lug-cocina"), nunca una
descripcion.
"""

PROMPT_REVISOR = """Revisa si este plan es fiel a su ficha.

FICHA
{ficha}

PLAN
{plan}

Comprueba que se respetan el genero, el tono, la ocasion y el papel del
protagonista; que el plan no contradice ni inventa datos de la ficha; y que la
historia tiene arco: empieza, se complica y cierra. No juzgues el recuento de
capitulos ni las palabras clave: eso ya lo comprobo el sistema.

Devuelve un unico objeto JSON: {{"aprobado": true|false, "objeciones": ["..."]}}.
Cada objecion dice que cambiar y donde.
"""


class PlanNoAprobado(RuntimeError):
    pass


@dataclass
class PlanAprobado:
    plan: PlanDeLaObra
    version: int
    titulo: str
    premisa: str
    reutilizado: bool = False
    """Se tomo de `plan_de_obra` al reanudar, sin volver a planificar."""


def _objeciones(lista):
    if not lista:
        return ""
    return ("\nOBJECIONES A TU PLAN ANTERIOR, QUE HAY QUE CORREGIR\n"
            + "\n".join("- " + o for o in lista) + "\n")


def _leer_plan(bruto):
    """El plan. El titulo y la premisa **no** salen de aqui: los propone el
    entrevistador y vienen en la ficha (`SPEC-25` v3). Si el Planificador
    devuelve otros, se ignoran."""
    if not isinstance(bruto, dict) or not isinstance(bruto.get("plan"), dict):
        raise ValueError("la respuesta no trae `plan` como objeto")
    return PlanDeLaObra.model_validate(bruto["plan"])


def _leer_veredicto(bruto):
    if (not isinstance(bruto, dict) or not isinstance(bruto.get("aprobado"), bool)
            or not isinstance(bruto.get("objeciones", []), list)):
        return False, ["el Revisor no devolvio un veredicto legible"]
    objeciones = [str(o) for o in bruto.get("objeciones") or []]
    if not bruto["aprobado"] and not objeciones:
        objeciones = ["el Revisor rechazo el plan sin decir por que"]
    return bruto["aprobado"], objeciones


def planificar(con, obra, ficha, planificador, revisor,
               tope=config.TOPE_REVISIONES_DE_PLAN, sistema=None,
               tope_de_formato=None) -> PlanAprobado:
    repo.asegurar_tablas(con)
    if tope_de_formato is None:
        tope_de_formato = (sistema.topes.reintentos_de_transporte if sistema
                           else config.TOPE_REINTENTOS_TRANSPORTE)
    # `SPEC-34` `RF-07`: los nombres vetados no salen hacia ningun agente. La cobertura los
    # sigue mirando con la ficha entera.
    # `SPEC-40` `RF-01`: la vista de los agentes, con el protagonista y sin nada del regalo
    # (tampoco los nombres vetados: `SPEC-34` `RF-07`). La cobertura mira la ficha entera.
    ficha_json = json.dumps(vista_de_agentes.ficha_para_agentes(ficha), ensure_ascii=False,
                            indent=2)
    anteriores = []
    rondas = fallos_de_formato = 0
    # `F-111`, TLC `CE-8`: al relanzar se sigue numerando desde la ultima version de la obra;
    # empezar en 0 pisaba, con `INSERT OR REPLACE`, las rondas de la ejecucion anterior.
    version = con.execute("SELECT COALESCE(MAX(version), 0) FROM plan_de_obra WHERE obra = ?",
                          (obra,)).fetchone()[0]
    while rondas < tope:
        version += 1
        bruto = planificador.llamar(PROMPT_PLANIFICADOR.format(
            ficha=ficha_json, premisa=ficha.premisa or "(sin premisa)",
            titulo=ficha.titulo or "(sin titulo)", capitulos=EXTENSION["capitulos"],
            minimo=rango_de_palabras(ficha.extension, sistema)[0],
            maximo=rango_de_palabras(ficha.extension, sistema)[1],
            objeciones=_objeciones(anteriores)))
        try:
            # `F-64`: acotados a la obra en el unico punto por el que entran.
            plan = acotar_a_la_obra(_leer_plan(bruto), obra)
        except (ValueError, ValidationError) as e:
            anteriores = ["el plan no cumple el esquema: {0}".format(str(e)[:600])]
            repo.guardar(con, obra, version, None, False, "esquema", anteriores)
            fallos_de_formato += 1
            if fallos_de_formato > tope_de_formato:
                raise PlanNoAprobado(
                    "el plan no cumplio el esquema en {0} intentos: {1}".format(
                        fallos_de_formato, anteriores[0]))
            continue
        rondas += 1
        # `SPEC-34` `RF-04`: un pseudonimo que volvio con otra forma no se restituyo; el
        # plan vuelve al Planificador, como cualquier otro hueco.
        huecos = cobertura.huecos(plan, ficha) + [
            "«{0}» parece una forma de un nombre de la ficha que no es la exacta: usa el "
            "nombre tal como esta en la ficha [INV-31]".format(r)
            for r in getattr(planificador, "residuos", None) or []]
        if huecos:
            anteriores = huecos
            repo.guardar(con, obra, version, plan, False, "codigo", huecos)
            continue
        aprobado, objeciones = _leer_veredicto(revisor.llamar(PROMPT_REVISOR.format(
            ficha=ficha_json, plan=json.dumps(plan.model_dump(mode="json"),
                                              ensure_ascii=False, indent=2))))
        repo.guardar(con, obra, version, plan, aprobado, "revisor", objeciones)
        if aprobado:
            return PlanAprobado(plan, version, ficha.titulo, ficha.premisa)
        anteriores = objeciones
    raise PlanNoAprobado(
        "el plan no se aprobo en {0} rondas; las ultimas objeciones: {1}".format(
            tope, "; ".join(anteriores)))


def reanudar_o_planificar(con, obra, ficha, planificador, revisor,
                          tope=config.TOPE_REVISIONES_DE_PLAN, **kw) -> PlanAprobado:
    """El plan aprobado de la obra si ya lo tiene; si no, se planifica.

    Relanzar tras una caida volvia a pagar al Planificador y al Revisor, y el
    plan nuevo podia no cuadrar con la obra ya montada, que `montar` no reinicia.
    El checkpoint que pide el enunciado tiene que reanudar, no rehacer. El
    titulo y la premisa salen de la ficha (`SPEC-25` v3), asi que no hace falta
    guardarlos con el plan.
    """
    repo.asegurar_tablas(con)
    plan = repo.aprobado(con, obra)
    if plan is None:
        return planificar(con, obra, ficha, planificador, revisor, tope=tope, **kw)
    version = con.execute("SELECT MAX(version) FROM plan_de_obra WHERE obra = ? AND "
                          "aprobado = 1", (obra,)).fetchone()[0]
    return PlanAprobado(plan, version, ficha.titulo, ficha.premisa, reutilizado=True)
