"""Las tres tools de lectura de la story bible (`SPEC-28`).

Viven en `orquestacion/` porque cruzan features —escaleta, cronologia, consolidacion,
planificacion— y componer es solo de aqui (`A-02`).

**Todas acotadas a la obra de la delegacion** (`RF-06`): la obra la pasa el servidor, no
el agente. Y los usos de un hecho se filtran por las escenas de la obra, porque
`uso_de_hecho` no guarda la obra y todas las novelas llaman igual a sus imprescindibles
(`F-65`). Ninguna devuelve el texto de una escena (`RF-05`).
"""

from app.commons.dominio import story_bible as sb
from app.features.consolidacion import aplicar
from app.features.cronologia import repository as cronologia
from app.features.escaleta import repository as escaleta
from app.features.planificacion import repository as planes


class NoExisteEnLaObra(LookupError):
    """El identificador no es de esta obra. No se dice si es de otra."""


def leer_hechos(con, obra, entrada: sb.EntradaHechos) -> sb.SalidaHechos:
    propias = {e["id"] for e in escaleta.escenas_de(con, obra)}
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
    for p in plan.mundo.personajes:
        if p.id == entrada.id:
            vigente = aplicar.estado(con).get(p.id)
            return sb.SalidaFicha(personaje=sb.FichaDePersonaje(
                id=p.id, nombre_canonico=p.nombre,
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
