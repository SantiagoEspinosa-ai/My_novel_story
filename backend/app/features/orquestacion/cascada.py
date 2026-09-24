"""La rama `S-1` de la regeneracion: la cascada (`SPEC-23` v4, `PLAN-23` B-S1.1).

La medida eligio `S-1` (2,33 capitulos <= 3, `harness/evals/arrastre-SPEC-23.json`). Una
peticion aceptada produce la version `n+1`:

1. `k` es el primer capitulo de la version de partida que la peticion toca -el primero
   que usa el hecho o, en un renombrado, el primero cuyo texto aceptado contiene el nombre
   viejo o donde el personaje esta presente-. Lo decidio `regeneracion.proponer`, y la
   lista aceptada es `k..N`: aqui se comprueba que siga siendolo.
2. Se crea la version `n+1` con `1..k-1` **compartidos por referencia** y `k..N` nuevos
   (`C-6`: capitulo `{capitulo_de_origen}-v{numero}`, escena `{capitulo_nuevo}-e1`, con el
   `t_discurso` de la que sustituye). Un capitulo `cerrado` no se reabre: se escribe otro.
3. El mundo vivo se rebobina a la semilla mas los deltas de lo ya consolidado de la
   version (al empezar, `1..k-1`), **solo el de esta obra** (`F-123`).
4. Los capitulos nuevos se escriben con el mismo montaje que la novela entera
   (`novela.escribir_version`), diciendo la version a todo lo que lee.
5. Se reverifica la version entera (sin modelo) y, sin parada, pasa por la puerta de
   publicacion con **sus** rondas (`F-122`). Hasta que la puerta la publique, el lector
   sigue en la anterior (`F-121`).

Relanzar tras una parada sigue desde el ultimo consolidado: la version ya existe (es la de
esta peticion), las escenas hechas se saltan y el mundo se rebobina a lo que la version ya
consolido.

**Antes de escribir nada** se comprueba lo que hace falta -agentes, plan aprobado, ficha y
la lista aceptada-: si falta algo, se dice y no se crea ni la version.
"""

import contextlib
import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.commons.dominio.enumeraciones import SalidaDeRegeneracion as S
from app.features.brief import repository as brief
from app.features.consolidacion import deltas as modulo_deltas
from app.features.consolidacion import mundo as modulo_mundo
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela, regeneracion
from app.features.orquestacion.obra import YA_HECHAS
from app.features.planificacion import repository as planes


class NoSePuedeRegenerar(Exception):
    """Falta algo para escribir la version nueva. **No se ha escrito nada.**"""


def ficha_de(con, obra):
    """La ficha de la entrevista cerrada de la obra, de donde la lee el trabajo. `None` si
    no hay: se borra al entregar (`SPEC-25` `RF-21`, `F-91`)."""
    from app.features.entrevista import repository as entrevistas
    try:
        for i in entrevistas.de_la_obra(con, obra):
            e = entrevistas.leer(con, i)
            if e is not None and e.cerrada:
                return e.ficha
    except sqlite3.OperationalError:
        return None
    return None


def _k(capitulos, aceptada, numero):
    """La posicion (desde 1) del primer capitulo de la cascada, comprobando que la lista
    aceptada sea `k..N` de la version de partida."""
    if not aceptada or aceptada[0] not in capitulos:
        raise NoSePuedeRegenerar(
            "la lista aceptada no empieza por un capitulo de la version {0}".format(numero))
    k = capitulos.index(aceptada[0]) + 1
    if aceptada != capitulos[k - 1:]:
        raise NoSePuedeRegenerar(
            "la lista aceptada no es una cascada de la version {0}: con `S-1` va del "
            "capitulo {1} al final".format(numero, k))
    return k


def _version_de(con, obra, peticion, capitulos, k):
    """La version de esta peticion: la que ya existe si se relanza, o una nueva."""
    for v in brief.versiones_de(con, obra):
        if v["peticion"] == peticion["id"]:
            return v["numero"]
    prevista = max(v["numero"] for v in brief.versiones_de(con, obra)) + 1
    nuevos = capitulos[:k - 1] + ["{0}-v{1}".format(c, prevista) for c in capitulos[k - 1:]]
    numero = brief.crear_version(con, obra, nuevos, anterior=peticion["version_de_partida"],
                                 peticion=peticion["id"])
    assert numero == prevista, (numero, prevista)
    return numero


def _rebobinar(con, obra, numero):
    """El mundo vivo: la semilla mas los deltas de lo que la version ya consolido, en orden
    de lectura, hasta la primera escena sin hacer (`C-2`)."""
    prefijo = []
    for e in regeneracion.escenas_de_version(con, obra, numero):
        if EE(e["estado"]) not in YA_HECHAS:
            break
        prefijo.extend(modulo_deltas.de_escenas(con, [e["id"]]))
    semilla = regeneracion.semilla_de(con, obra)
    mundo, incompatibles = modulo_mundo.acumular(semilla, prefijo)
    if incompatibles:
        raise NoSePuedeRegenerar(
            "el prefijo de la version {0} no se sostiene sobre su semilla: {1}".format(
                numero, "; ".join("{escena}: {motivo}".format(**i) for i in incompatibles)))
    modulo_mundo.rebobinar(con, mundo, obra=obra)
    return len(prefijo)


def _reverificacion(r):
    por = {EV.VERIFICADA: [], EV.FALLIDA: [], EV.SIN_REVERIFICAR: []}
    for e in r.get("escenas", []):
        por[EV(e["estado"])].append(e["escena"])
    return {"reverificada": r.get("reverificada", False), "motivo": r.get("motivo"),
            "verificadas": por[EV.VERIFICADA], "fallidas": por[EV.FALLIDA],
            "sin_reverificar": por[EV.SIN_REVERIFICAR]}


def regenerar(con, peticion, agentes=None, ficha=None, sistema=None, lean=None,
              listas=None, carpeta_de_reglas=None, observacion=None):
    """Ejecuta la cascada de una peticion guardada. Devuelve un resultado que cabe en JSON
    (lo guarda la cola de trabajos). Lanza `NoSePuedeRegenerar` si falta algo, **antes**
    de escribir nada."""
    from app.commons.configuracion import carga
    from app.features.orquestacion import progreso

    obra = peticion["obra"]
    salida = peticion["salida"].value if peticion.get("salida") else None
    if salida != S.CASCADA.value:
        raise NoSePuedeRegenerar("la peticion {0} no es de la salida `cascada` sino de "
                                 "`{1}`".format(peticion["id"], salida))
    if not agentes:
        raise NoSePuedeRegenerar(
            "sin agentes no se puede escribir: el worker de la API no tiene agentes "
            "configurados, y regenerar gasta dinero (`backend/pedir_cambio.py`). No se ha "
            "escrito nada")
    plan = planes.aprobado(con, obra)
    if plan is None:
        raise NoSePuedeRegenerar("la obra {0} no tiene plan aprobado".format(obra))
    ficha = ficha or ficha_de(con, obra)
    if ficha is None:
        raise NoSePuedeRegenerar(
            "la obra {0} no tiene ficha: se borra al entregar (`F-91`, `SPEC-25` `RF-21`) "
            "y sin ella no hay con que montar el bloque inmutable del Escritor. No se "
            "inventa: no se ha escrito nada".format(obra))
    partida = peticion["version_de_partida"]
    capitulos = brief.capitulos_de_version(con, obra, partida)
    k = _k(capitulos, list(peticion["capitulos_propuestos"]), partida)
    regeneracion.semilla_de(con, obra)  # sin semilla no se sabe de que mundo parte

    numero = _version_de(con, obra, peticion, capitulos, k)
    de_la_version = brief.capitulos_de_version(con, obra, numero)
    for posicion in range(k, len(de_la_version) + 1):
        if not escaleta.escenas_de_capitulo(con, de_la_version[posicion - 1], obra):
            escaleta.guardar_escaleta(con, obra, [
                regeneracion.escena_para_regenerar(con, obra, numero, posicion)])
    _rebobinar(con, obra, numero)

    sistema = sistema or carga.cargar_sistema()
    donde = {"capitulo": None, "total": None}
    grupo = contextlib.nullcontext()
    if observacion is not None:
        # `SPEC-29`, como `novela._escribir_observado`: un span por llamada a cada rol, sin
        # prompt ni respuesta, colgado de `regeneracion` y de su capitulo.
        from app.features.observabilidad import repository as observabilidad
        from app.features.orquestacion import prompts
        prompts.enviar_nuevas(con, observacion)
        observacion.herramientas_de = lambda d: observabilidad.spans_de_herramientas(con, d)
        agentes = novela._observados(agentes, observacion)
        grupo = observacion.grupo("regeneracion")
    preparados = novela.preparar_agentes(con, obra, agentes, sistema, donde)
    try:
        with grupo:
            r = novela.escribir_version(
                con, obra, ficha, preparados, plan, brief.leer(con, obra)["premisa"],
                de_la_version[k - 1:], numero, sistema, donde, listas=listas, lean=lean,
                observacion=observacion, carpeta_de_reglas=carpeta_de_reglas, desde=k)
    except Exception as e:
        progreso.fijar(con, obra, "parada", motivo=type(e).__name__)
        raise
    g, publicada = r["generacion"], r["publicacion"]
    reverificada = _reverificacion(regeneracion.reverificar(con, obra, numero))
    if g.parada:
        progreso.fijar(con, obra, "parada", motivo=str(g.parada.get("motivo")))
    elif publicada is not None and publicada.publicada:
        progreso.fijar(con, obra, "publicada")
    else:
        progreso.fijar(con, obra, "esperando_revision")
    return {
        "obra": obra, "peticion": peticion["id"], "salida": salida,
        "version_de_partida": partida, "version": numero, "desde_capitulo": k,
        "capitulos_compartidos": de_la_version[:k - 1],
        "capitulos_cambiados": de_la_version[k - 1:],
        "escenas_hechas": list(g.escenas_hechas), "saltadas": list(g.saltadas),
        "rendidas": [list(x) for x in g.rendidas], "sin_resumen": list(g.sin_resumen),
        "parada": g.parada, "coste": dict(g.coste),
        "coste_del_cierre": r["coste_del_cierre"],
        "reverificacion": reverificada,
        "publicacion": None if publicada is None else {
            "publicada": publicada.publicada, "rondas": publicada.rondas,
            "parada": publicada.parada},
        "vigente": brief.version_vigente(con, obra),
    }
