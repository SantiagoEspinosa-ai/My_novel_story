"""Las tres tools de lectura de la story bible (`SPEC-28`).

Viven en `orquestacion/` porque cruzan features —escaleta, cronologia, consolidacion,
planificacion— y componer es solo de aqui (`A-02`).

**Todas acotadas a la obra de la delegacion** (`RF-06`): la obra la pasa el servidor, no
el agente. Y los usos de un hecho se filtran por las escenas de la obra, porque
`uso_de_hecho` no guarda la obra y todas las novelas llaman igual a sus imprescindibles
(`F-65`). Ninguna devuelve el texto de una escena (`RF-05`).
"""

import time

from pydantic import ValidationError

from app.commons.dominio import story_bible as sb
from app.commons.modelo.presupuesto import CARACTERES_POR_TOKEN
from app.features.consolidacion import aplicar
from app.features.cronologia import repository as cronologia
from app.features.escaleta import repository as escaleta
from app.features.observabilidad import repository as observabilidad
from app.features.planificacion import repository as planes


class NoExisteEnLaObra(LookupError):
    """El identificador no es de esta obra. No se dice si es de otra."""


def leer_hechos(con, obra, entrada: sb.EntradaHechos) -> sb.SalidaHechos:
    # `PLAN-23` A6: las escenas de la version vigente, no las de la obra entera.
    from app.features.orquestacion import regeneracion
    propias = {e["id"] for e in regeneracion.escenas_de_version(con, obra)}
    hechos = [h for h in escaleta.hechos_declarados(con, obra)
              if entrada.hecho is None or h["id"] == entrada.hecho]
    return sb.SalidaHechos(hechos=[
        sb.HechoConUsos(id=h["id"], enunciado=h["enunciado"], usos=[
            sb.UsoDeHecho(capitulo=u["capitulo"], tipo=u["tipo"])
            for u in cronologia.usos_de_hecho(con, h["id"]) if u["escena"] in propias])
        for h in hechos])


def leer_ficha(con, obra, entrada: sb.EntradaFicha) -> sb.SalidaFicha:
    plan = planes.aprobado(con, obra)
    if plan is None:
        raise NoExisteEnLaObra("la obra no tiene plan aprobado")
    # `PLAN-23` A7: el nombre de la version que se escribe, la vigente (`C-4`).
    from app.features.orquestacion import regeneracion
    nombres = regeneracion.nombres_de_version(con, obra)
    for p in plan.mundo.personajes:
        if p.id == entrada.id:
            vigente = aplicar.estado(con).get(p.id)
            return sb.SalidaFicha(personaje=sb.FichaDePersonaje(
                id=p.id, nombre_canonico=nombres.get(p.id, p.nombre),
                estado_vital=vigente[0] if vigente else p.estado_vital))
    for l in plan.mundo.lugares:
        if l.id == entrada.id:
            return sb.SalidaFicha(lugar=sb.FichaDeLugar(id=l.id, nombre=l.nombre))
    raise NoExisteEnLaObra("`{0}` no es un personaje ni un lugar de esta obra".format(entrada.id))


def leer_cronologia(con, obra, entrada: sb.EntradaCronologia) -> sb.SalidaCronologia:
    return sb.SalidaCronologia(eventos=[
        sb.EventoDeLaCronologia(
            id=e["id"], t_fabula=e["t_fabula"], duracion_min=e["duracion_min"],
            lugar=e["lugar"], capitulo=e["capitulo"],
            personajes_presentes=cronologia.participantes_de(con, e["id"]))
        for e in cronologia.eventos_de(con, obra)
        if entrada.capitulo is None or e["capitulo"] == entrada.capitulo])


# --- Atender una llamada (`PLAN-28` E3) -------------------------------------------

HERRAMIENTAS = {
    "hechos": (sb.EntradaHechos, leer_hechos,
               "Los hechos de la story bible, cada uno con los capitulos donde se usa y como."),
    "ficha": (sb.EntradaFicha, leer_ficha,
              "La ficha de un personaje o de un lugar de esta obra, por su id."),
    "cronologia": (sb.EntradaCronologia, leer_cronologia,
                   "Los eventos de la cronologia en orden de fabula, con lugar y presentes."),
}


def atender(con_lectura, con_traza, obra, agente, delegacion, nombre, argumentos) -> dict:
    """Valida la entrada, lee, valida la salida, mide y registra (`SPEC-28` `RF-02`, `RF-08`).

    Devuelve la forma de un resultado de tool MCP: `{content, isError}`. Un error de
    entrada llega al agente con el mensaje de Pydantic, que es lo que `RF-02` pide: un
    error que el agente ve. Los tokens de lo devuelto se **estiman** —cuatro
    caracteres por token— y se guardan junto a la llamada, sin presupuestarlos: el
    harness no administra el contexto de la sesion delegada (`SPEC-28` § "Punto ciego").
    """
    inicio = time.perf_counter()

    def registrar(validacion, tokens=None):
        observabilidad.guardar_llamada(
            con_traza, delegacion, obra, agente, nombre, validacion,
            int((time.perf_counter() - inicio) * 1000), tokens)

    def error(validacion, mensaje):
        registrar(validacion)
        return {"content": [{"type": "text", "text": mensaje}], "isError": True}

    if nombre not in HERRAMIENTAS:
        return error("herramienta_desconocida", "no existe la tool `{0}`".format(nombre))
    entrada_cls, leer, _ = HERRAMIENTAS[nombre]
    try:
        entrada = entrada_cls.model_validate(argumentos or {})
    except ValidationError as e:
        return error("entrada_invalida", "entrada fuera de esquema: {0}".format(e))
    try:
        salida = leer(con_lectura, obra, entrada)
    except NoExisteEnLaObra as e:
        return error("no_existe", str(e))
    except ValidationError:
        return error("salida_invalida", "la story bible devolvio un dato fuera de esquema")
    texto = salida.model_dump_json()
    registrar("ok", len(texto) // CARACTERES_POR_TOKEN)
    return {"content": [{"type": "text", "text": texto}], "isError": False}
