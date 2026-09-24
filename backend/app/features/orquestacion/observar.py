"""De los resultados del pipeline salen los scores de Langfuse (`SPEC-29` `RF-04`).

Un score por validador: cada invariante de la puerta, `INV-22`, `INV-23` por
imprescindible, `schema`, cada criterio del Editor (`INV-26.<criterio>`), las rondas del
plan y el cierre. **Nada de `Hallazgo.descripcion` sube**, porque cita el texto, y el texto
lleva al destinatario dentro. Y lo que no se llego a mirar no se envia como «pasa»: un
validador que no corre no es un validador que paso.
"""

from app.commons.dominio.enumeraciones import EstadoDeHallazgo, NivelDeVeto
from app.features.verificacion.puertas import INVARIANTES_DE_LA_PUERTA

_SIN = EstadoDeHallazgo.SIN_VEREDICTO


def _categoria(hallazgos, invariante):
    propios = [h for h in hallazgos if h.invariante == invariante]
    if any(h.estado != _SIN for h in propios):
        return "falla"
    return "sin_veredicto" if propios else "pasa"


def del_ciclo(obs, c):
    """Un intento de una escena. Se para donde se paro el ciclo."""
    if obs is None or c is None or c.generacion is None:
        return
    g = c.generacion
    if g.fallo == "contrato":
        obs.score(nombre="schema", categoria="falla")
        return
    if g.fallo:
        return  # transporte o sin contexto: no hubo respuesta que juzgar, y el span lo dice
    obs.score(nombre="schema", categoria="pasa")
    for inv in INVARIANTES_DE_LA_PUERTA:
        obs.score(nombre=inv, categoria=_categoria(g.hallazgos, inv))
    _vetadas(obs, c)
    if c.fallo == "palabra_vetada":
        return
    if c.nombres_comprobados:
        obs.score(nombre="INV-22", valor=len(c.nombres_encontrados))
    if c.fallo == "nombre_mal_escrito":
        return
    for imp in c.imprescindibles_comprobados:
        obs.score(nombre="INV-23", referencia=imp,
                  categoria="falla" if imp in c.imprescindibles_ausentes else "pasa")
    v = c.veredicto or {}
    if v.get("valoraciones"):
        for val in v["valoraciones"]:
            obs.score(nombre="INV-26.{0}".format(val["criterio"]), valor=val["nota"])
    elif v.get("veredicto") == "SIN_VEREDICTO":
        obs.score(nombre="INV-26", categoria="sin_veredicto")


def _vetadas(obs, c):
    """`INV-21` (`RF-06`): un score por coincidencia, siempre con su nivel, y con el
    termino solo si es global. La coincidencia tambien queda en el audit log, que lo
    escribe `obra._intentar` y no cambia."""
    if not c.vetadas_comprobadas:
        return
    if not c.vetadas_encontradas:
        obs.score(nombre="INV-21", categoria="pasa")
        return
    for co in c.vetadas_encontradas:
        v = obs.vetadas.get(co.vetada)
        if v is None:
            # Sin catalogo no se sabe el nivel: se envia sin nada que la identifique.
            obs.score(nombre="INV-21", categoria="falla")
            continue
        obs.score(nombre="INV-21", categoria="falla", nivel=v.nivel,
                  referencia="vetada-{0}-{1}".format(v.nivel.value, v.id),
                  termino=v.forma if v.nivel is NivelDeVeto.GLOBAL else None)


def de_las_rondas_del_plan(obs, versiones):
    """Cada ronda del plan llega hasta donde llego: el esquema, la cobertura del codigo
    (`SPEC-26` `RF-06`) y el Revisor. Las objeciones no suben: citan la ficha."""
    if obs is None:
        return
    for v in versiones:
        ronda = "ronda-{0}".format(v["version"])
        obs.score(nombre="schema.plan", referencia=ronda,
                  categoria="falla" if v["origen"] == "esquema" else "pasa")
        if v["origen"] == "esquema":
            continue
        obs.score(nombre="cobertura.plan", referencia=ronda,
                  categoria="falla" if v["origen"] == "codigo" else "pasa")
        if v["origen"] == "revisor":
            obs.score(nombre="revisor.plan", referencia=ronda,
                      categoria="pasa" if v["aprobado"] else "falla")


def del_cierre(obs, cierre, ronda):
    """`INV-24`, `INV-25` e `INV-27`, por ronda de la puerta de publicacion."""
    if obs is None or not cierre:
        return
    ref = "ronda-{0}".format(ronda)
    obs.score(nombre="INV-24", referencia=ref,
              categoria="falla" if cierre["faltan"] else "pasa")
    obs.score(nombre="INV-25", referencia=ref,
              valor=len(cierre["repeticiones"]) + len(cierre["frases"]))
    if cierre["estado"] == "novela_incompleta":
        obs.score(nombre="INV-27", referencia=ref, categoria="no_aplica",
                  motivo="no se juzga una novela incompleta (INV-24)")
        return
    estados = {h["estado"] for h in cierre["juicio"]}
    obs.score(nombre="INV-27", referencia=ref,
              categoria="falla" if "abierto" in estados
              else "sin_veredicto" if estados else "pasa")
