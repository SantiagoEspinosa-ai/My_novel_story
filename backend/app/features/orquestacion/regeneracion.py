"""Regenerar en una obra acumulativa (`SPEC-23` v2, `PLAN-23`).

Compone features, que es lo unico autorizado a `orquestacion/` (`A-02`): el plan
aprobado es de `planificacion/`, el mundo y los deltas de `consolidacion/`, las
versiones de `brief/` y las escenas de `escaleta/`.

**Ningun paso de este modulo llama al modelo.** Lo que cuesta dinero -escribir los
capitulos nuevos- es de la Parte B, y va con la salida que elija la medida.
"""

import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.features.auditoria.publicacion import NO_EJECUTADAS as NO_EJECUTADAS_EN_PUBLICACION
from app.features.brief import repository as brief
from app.features.consolidacion import deltas as modulo_deltas
from app.features.consolidacion import mundo as modulo_mundo
from app.features.consolidacion.mundo import ANTERIOR_AL_RELATO
from app.features.escaleta import repository as escaleta
from app.features.planificacion import repository as planes
from app.features.verificacion import puertas
from app.features.verificacion import repository as reverificaciones


class SinSemilla(Exception):
    """Sin plan aprobado no hay semilla: no se sabe de que mundo parte la obra."""


def semilla_de(con, obra):
    """El mundo **antes del capitulo 1** de la obra, en la forma de `mundo.leer`.

    Personajes, lugares y accesos salen del plan aprobado. El conocimiento inicial,
    de las filas `anterior_al_relato` del registro: es lo que sembro `novela.montar`,
    incluido lo que sale de la ficha -que el destinatario conoce sus imprescindibles-,
    y la ficha se borra al entregar (`SPEC-25` `RF-21`), asi que no se puede volver a
    calcular. Lo revelado por una escena no es semilla: es de su delta.
    """
    planes.asegurar_tablas(con)
    plan = planes.aprobado(con, obra)
    if plan is None:
        raise SinSemilla(
            "la obra {0} no tiene plan aprobado: sin el no se sabe de que mundo parte, "
            "y reconstruir su estado seria inventarlo".format(obra))
    conocimiento = {}
    try:
        filas = con.execute("SELECT sujeto, hecho, grado FROM conocimiento "
                            "WHERE desde_escena IS NULL AND fuente = ?",
                            (ANTERIOR_AL_RELATO,)).fetchall()
    except sqlite3.OperationalError:
        # Sin tabla de conocimiento nadie sembro nada: la semilla no sabe nada.
        filas = []
    for sujeto, hecho, grado in filas:
        conocimiento[(sujeto, hecho)] = {"desde": None, "grado": grado}
    return {
        "entidades_vivas": {p.id: p.estado_vital.value for p in plan.mundo.personajes},
        "ubicaciones": {p.id: p.empieza_en for p in plan.mundo.personajes},
        "accesos": {l.id: list(l.accesos) for l in plan.mundo.lugares},
        "conocimiento": conocimiento,
    }


# --- Las escenas de una version --------------------------------------------------

def escenas_de_version(con, obra, numero=None):
    """Las escenas de la version `numero` -la vigente si no se dice-, en orden de
    lectura: los capitulos en el orden de la version y, dentro, por `orden`.

    Una obra sin ninguna version (dada de alta antes de `PLAN-23`) no tiene a quien
    preguntar: se devuelven sus escenas como siempre, por obra."""
    if numero is None:
        numero = brief.version_vigente(con, obra)
    if numero is None:
        return escaleta.escenas_de(con, obra)
    escenas = []
    for capitulo in brief.capitulos_de_version(con, obra, numero):
        escenas.extend(escaleta.escenas_de_capitulo(con, capitulo))
    return escenas


# --- A4 · la reverificacion (`D-1`, `MF-26`) ---------------------------------------

# Lo que la reverificacion **no** vuelve a pasar, con su motivo. Se dice en cada
# resultado, porque una invariante que no se ejecuta no esta en verde (`F-34`).
NO_EJECUTADAS = tuple(NO_EJECUTADAS_EN_PUBLICACION) + (
    ("INV-04", "`Borrador.pov_usado` lo declara el Escritor y no se guarda con el "
               "borrador, asi que no hay con que volver a compararlo"),
)
_SIN_REPETIR = {i for i, _ in NO_EJECUTADAS}


def _prefijos(con, obra, numero, semilla):
    """Por cada escena de la version: la escena, su delta y el prefijo de deltas."""
    prefijo = []
    for escena in escenas_de_version(con, obra, numero):
        u = modulo_deltas.ultimo(con, escena["id"])
        yield escena, (u["delta"] if u else None), list(prefijo)
        if u is not None:
            prefijo.append((escena["id"], u["delta"]))


def _texto_elegido(con, escena):
    from app.features.orquestacion.obra import _texto_elegido as elegido
    return elegido(con, escena) or ""


def reverificar(con, obra, numero):
    """Vuelve a pasar las puertas deterministas de cada escena de la version `numero`
    contra el estado que **esa version** reconstruye, y guarda el resultado.

    Para cada escena, en orden de lectura: la huella de su estado previo (`C-3`), el
    mundo previo como `acumular(semilla, deltas del prefijo)` y las puertas con su
    delta guardado. Si el delta ya no entra en ese mundo, la fila es `fallida` con el
    motivo como hallazgo de `INV-05`, sin lanzar. **No escribe en `hallazgo` y no
    delega en nadie**: son reglas, no llamadas.
    """
    reverificaciones.asegurar_tablas(con)
    no_ejecutadas = [{"invariante": i, "motivo": m} for i, m in NO_EJECUTADAS]
    try:
        semilla = semilla_de(con, obra)
    except SinSemilla as e:
        return {"reverificada": False, "motivo": str(e), "version": numero,
                "escenas": [], "no_ejecutadas": no_ejecutadas}
    resultado = []
    for escena, delta, prefijo in _prefijos(con, obra, numero, semilla):
        if delta is None:
            # Sin delta no hay nada que comprobar: la escena no se consolido. Queda
            # `sin_reverificar`, y se dice.
            resultado.append({"escena": escena["id"], "estado": EV.SIN_REVERIFICAR,
                              "hallazgos": [], "motivo": "no tiene delta guardado"})
            continue
        previo, _ = modulo_mundo.acumular(semilla, prefijo)
        huella = modulo_mundo.huella(semilla, prefijo)
        hallazgos = []
        _, incompatible = modulo_mundo.acumular(previo, [(escena["id"], delta)])
        for i in incompatible:
            hallazgos.append({"invariante": "INV-05", "descripcion": i["motivo"]})
        vista = dict(escena)
        vista["palabras"] = len(_texto_elegido(con, escena).split())
        vista["longitud_objetivo"] = tuple(escena.get("longitud_objetivo") or ()) or None
        vista["personajes_presentes"] = escena.get("personajes_presentes") or []
        for h in puertas.verificar(vista, delta, previo):
            if h.invariante in _SIN_REPETIR:
                continue
            hallazgos.append({"invariante": h.invariante, "descripcion": h.descripcion,
                              "severidad": h.severidad.value, "estado": h.estado.value})
        estado = EV.FALLIDA if hallazgos else EV.VERIFICADA
        reverificaciones.guardar(con, obra, numero, escena["id"], huella, estado, hallazgos)
        resultado.append({"escena": escena["id"], "estado": estado, "hallazgos": hallazgos,
                          "motivo": "; ".join(h["descripcion"] for h in hallazgos)})
    return {"reverificada": True, "version": numero, "escenas": resultado,
            "no_ejecutadas": no_ejecutadas}


def estado_de(con, obra, numero, escena):
    """`verificada` o `fallida` solo si hay fila **con la huella vigente** de la escena
    en esa version; si no, `sin_reverificar`. Un verde de otra version, o de otro
    estado de la misma, no cuenta (`D-1`)."""
    reverificaciones.asegurar_tablas(con)
    try:
        semilla = semilla_de(con, obra)
    except SinSemilla:
        return EV.SIN_REVERIFICAR
    for e, delta, prefijo in _prefijos(con, obra, numero, semilla):
        if e["id"] != escena:
            continue
        fila = reverificaciones.leer(con, obra, numero, escena,
                                     modulo_mundo.huella(semilla, prefijo))
        return fila["estado"] if fila else EV.SIN_REVERIFICAR
    return EV.SIN_REVERIFICAR
