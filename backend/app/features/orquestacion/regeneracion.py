"""Regenerar en una obra acumulativa (`SPEC-23` v2, `PLAN-23`).

Compone features, que es lo unico autorizado a `orquestacion/` (`A-02`): el plan
aprobado es de `planificacion/`, el mundo y los deltas de `consolidacion/`, las
versiones de `brief/` y las escenas de `escaleta/`.

**Ningun paso de este modulo llama al modelo.** Lo que cuesta dinero -escribir los
capitulos nuevos- es de la Parte B, y va con la salida que elija la medida.
"""

import re
import sqlite3

from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.commons.dominio.enumeraciones import ClaseDePeticion as CP
from app.commons.dominio.enumeraciones import SalidaDeRegeneracion as S
from app.commons.politica.vetadas import coincidencias, formas_de_nombre
from app.commons.trabajos import cola
from app.features.cronologia import consultas as usos_consultas
from app.features.cronologia import repository as usos
from app.features.revision import repository as peticiones
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
        escenas.extend(escaleta.escenas_de_capitulo(con, capitulo, obra))
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


# --- A5 · que cambio (`RF-52`, `CE-5`) ----------------------------------------------

def comparar(con, obra, a, b):
    """Por **posicion** de la version `b`: si el capitulo es el mismo que el de esa
    posicion en `a` (compartido) o no. **Por identidad, no por texto**: un capitulo
    nuevo con el mismo texto sigue contando como cambiado, porque es otra fila."""
    de_a = brief.capitulos_de_version(con, obra, a)
    return [{"orden": orden, "capitulo": capitulo,
             "compartido": orden <= len(de_a) and de_a[orden - 1] == capitulo}
            for orden, capitulo in enumerate(brief.capitulos_de_version(con, obra, b), 1)]


def vista_de_version(con, obra, numero):
    """Lo que devuelve `GET /obras/{id}/versiones/{numero}`, o `None` si no existe.

    Por capitulo, si es compartido con la anterior (`None` en una version sin
    anterior), su `estado_de_capitulo`; por escena, su `estado_de_escena` **y** su
    `estado_de_verificacion` en esta version (`RF-54`)."""
    version = next((v for v in brief.versiones_de(con, obra) if v["numero"] == numero), None)
    if version is None:
        return None
    anterior = version["anterior"]
    compartidos = ({c["orden"]: c["compartido"] for c in comparar(con, obra, anterior, numero)}
                   if anterior is not None else {})
    capitulos = []
    for orden, capitulo in enumerate(brief.capitulos_de_version(con, obra, numero), 1):
        capitulos.append({
            "orden": orden, "capitulo": capitulo,
            "compartido": compartidos.get(orden) if anterior is not None else None,
            "estado": brief.estado_de_capitulo(con, capitulo),
            "escenas": [{"id": e["id"], "estado": e["estado"],
                         "estado_de_verificacion": estado_de(con, obra, numero, e["id"])}
                        for e in escaleta.escenas_de_capitulo(con, capitulo, obra)]})
    return dict(version, obra=obra, capitulos=capitulos)


# --- A7 · la peticion, el hecho y el nombre de una version (`C-4`) -----------------

# `SPEC-23` v2: la elige la medida (B1, B2), no una opinion. Mientras sea `None`,
# pedir un cambio responde `409` y no encola nada.
SALIDA = None

# `SPEC-23` `D-3`, literales: la promesa y su punto ciego, dichos al lector.
PROMESA = "reescribimos lo que dependía de esto"
PUNTO_CIEGO = "si la prosa contradice sin que el delta lo declare, no se toca"
SIN_SALIDA = "salida sin elegir: falta la medida"

TIPO_DE_TRABAJO = "regenerar_obra"


def _tipos_que_usan():
    """Que tipos de uso cuentan como «usar el hecho» para regenerar: la constante de
    `SPEC-21` C-2. Si B-S2.0 mete `menciona`, entra aqui sola."""
    return usos_consultas.PARA_REGENERACION


class PeticionNoAdmitida(Exception):
    """Lo que `C-4` no admite, con su motivo. La API responde `409`."""


class SalidaSinElegir(Exception):
    pass


class ListaCambiada(Exception):
    pass


def cadena(con, obra, numero):
    """Las peticiones que llevan de la version 1 a la `numero`, de la mas vieja a la
    mas nueva. Una version sin peticion (la 1, o una creada a mano) no aporta ninguna."""
    if numero is None:
        return []
    por_numero = {v["numero"]: v for v in brief.versiones_de(con, obra)}
    resultado, vistas = [], set()
    while numero is not None and numero in por_numero and numero not in vistas:
        vistas.add(numero)
        v = por_numero[numero]
        if v["peticion"] is not None:
            p = peticiones.leer(con, v["peticion"])
            if p is not None:
                resultado.append(p)
        numero = v["anterior"]
    return list(reversed(resultado))


def _plan(con, obra):
    try:
        return planes.aprobado(con, obra)
    except sqlite3.OperationalError:
        return None


def _renombrados(con, obra, numero):
    """Pares `(viejo, nuevo)` de la cadena, en orden, y los nombres que quedan."""
    plan = _plan(con, obra)
    actuales = {p.id: p.nombre for p in plan.mundo.personajes} if plan else {}
    pares = []
    for p in cadena(con, obra, numero):
        if p["clase"] is CP.NOMBRE and p["personaje"] in actuales:
            pares.append((actuales[p["personaje"]], p["nombre_nuevo"]))
            actuales[p["personaje"]] = p["nombre_nuevo"]
    return pares, actuales


def nombres_de_version(con, obra, numero=None):
    """`{personaje: nombre}` de la version: los del plan con los renombrados de su
    cadena de peticiones (`C-4`, punto 1). **La identidad no cambia**: el `id` es el
    mismo, y la version anterior sigue leyendo el nombre viejo."""
    if numero is None:
        numero = brief.version_vigente(con, obra)
    return _renombrados(con, obra, numero)[1]


def sustituir_nombre(texto, viejo, nuevo):
    """El nombre viejo por el nuevo, **como palabra entera**: el completo y, si tiene
    mas de una palabra, tambien el de pila, que es como se veta (`RF-15`)."""
    if not texto:
        return texto
    formas_viejas, formas_nuevas = formas_de_nombre(viejo), formas_de_nombre(nuevo)
    for i, forma in enumerate(formas_viejas):
        sustituta = formas_nuevas[min(i, len(formas_nuevas) - 1)]
        texto = re.sub(r"(?<!\w){0}(?!\w)".format(re.escape(forma)), sustituta, texto)
    return texto


def _con_nombres(texto, pares):
    for viejo, nuevo in pares:
        texto = sustituir_nombre(texto, viejo, nuevo)
    return texto


def hechos_de_version(con, obra, numero=None):
    """Los hechos de la obra **en la version**: el enunciado nuevo de cada peticion de
    hecho de su cadena y los nombres nuevos de sus renombrados, en orden. En la forma
    de `escaleta.hechos_declarados`. `HechoCanonico` no se edita."""
    if numero is None:
        numero = brief.version_vigente(con, obra)
    hechos = [dict(h) for h in escaleta.hechos_declarados(con, obra)]
    por_id = {h["id"]: h for h in hechos}
    plan = _plan(con, obra)
    actuales = {p.id: p.nombre for p in plan.mundo.personajes} if plan else {}
    for p in cadena(con, obra, numero):
        if p["clase"] is CP.HECHO and p["hecho"] in por_id:
            por_id[p["hecho"]]["enunciado"] = p["enunciado_nuevo"]
        elif p["clase"] is CP.NOMBRE and p["personaje"] in actuales:
            viejo, nuevo = actuales[p["personaje"]], p["nombre_nuevo"]
            for h in hechos:
                h["enunciado"] = sustituir_nombre(h["enunciado"], viejo, nuevo)
            actuales[p["personaje"]] = nuevo
    return hechos


def vetadas_de_version(con, obra, numero, base=()):
    """Las vetadas de la version: las de siempre y, ademas, **el nombre viejo de cada
    renombrado de su cadena**, como vetada de nivel novela solo para esta version
    (`C-4`, punto 3). No se guarda en `palabra_vetada`, que es por obra: la version
    anterior dejaria de poder cerrarse con el nombre que si es el suyo."""
    resultado = list(base)
    pares, actuales = _renombrados(con, obra, numero)
    vigentes = {f for n in actuales.values() for f in formas_de_nombre(n)}
    for viejo, _ in pares:
        for forma in formas_de_nombre(viejo):
            if forma not in resultado and forma not in vigentes:
                resultado.append(forma)
    return resultado


def _destinatarios(con, obra, plan):
    """Los personajes que son el destinatario, segun la ficha. `None` si no hay ficha:
    se borra al entregar (`SPEC-25` `RF-21`), y entonces **no consta**."""
    from app.features.entrevista import repository as entrevistas
    try:
        fichas = [entrevistas.leer(con, i).ficha for i in entrevistas.de_la_obra(con, obra)]
    except sqlite3.OperationalError:
        return None
    nombres = {f.destinatario.nombre for f in fichas
               if f.destinatario is not None and f.destinatario.nombre}
    if not nombres:
        return None
    return {p.id for p in plan.mundo.personajes if p.nombre in nombres}


def _validar(con, obra, numero, peticion):
    try:
        clase = CP(peticion.get("clase"))
    except ValueError:
        raise PeticionNoAdmitida("la clase de peticion es `hecho` o `nombre`")
    if not (peticion.get("texto") or "").strip():
        raise PeticionNoAdmitida("la peticion necesita las palabras del lector")
    if clase is CP.HECHO:
        hecho, nuevo = peticion.get("hecho"), (peticion.get("enunciado_nuevo") or "").strip()
        if not hecho or not nuevo:
            raise PeticionNoAdmitida("un cambio de hecho necesita el hecho y su enunciado nuevo")
        if hecho not in {h["id"] for h in escaleta.hechos_declarados(con, obra)}:
            raise PeticionNoAdmitida("`{0}` no es un hecho de esta obra".format(hecho))
        return clase
    personaje, nuevo = peticion.get("personaje"), (peticion.get("nombre_nuevo") or "").strip()
    if not personaje or not nuevo:
        raise PeticionNoAdmitida("un cambio de nombre necesita el personaje y su nombre nuevo")
    plan = _plan(con, obra)
    nombres = nombres_de_version(con, obra, numero)
    if plan is None or personaje not in nombres:
        raise PeticionNoAdmitida("`{0}` no es un personaje de esta obra".format(personaje))
    destinatarios = _destinatarios(con, obra, plan)
    if destinatarios is None:
        raise PeticionNoAdmitida(
            "no consta quien es el destinatario -no hay ficha de la obra-, asi que no se "
            "puede comprobar que el renombrado no sea el suyo, y no se admite")
    if personaje in destinatarios:
        raise PeticionNoAdmitida(
            "el nombre del destinatario es un dato de la ficha del comprador, no del plan: "
            "no se renombra")
    for otro, nombre in nombres.items():
        if otro != personaje and nuevo in formas_de_nombre(nombre):
            raise PeticionNoAdmitida(
                "«{0}» ya es el nombre de otro personaje de la obra".format(nuevo))
    if nuevo == nombres[personaje]:
        raise PeticionNoAdmitida("«{0}» ya es su nombre".format(nuevo))
    return clase


def capitulos_afectados(con, obra, numero, peticion):
    """Los capitulos de la version que la peticion toca, en su orden.

    Un hecho: los que lo usan (`_tipos_que_usan`) en escenas de la version. Un nombre:
    los que contienen el nombre viejo **como palabra entera** en su texto aceptado, y
    los que tienen al personaje presente (`C-4`, punto 2). Lo decide el texto, no el
    modelo."""
    escenas = escenas_de_version(con, obra, numero)
    tocados = set()
    if CP(peticion["clase"]) is CP.HECHO:
        propias = {e["id"]: e["capitulo"] for e in escenas}
        for u in usos.usos_de_hecho(con, peticion["hecho"], _tipos_que_usan()):
            if u["escena"] in propias:
                tocados.add(propias[u["escena"]])
    else:
        formas = formas_de_nombre(nombres_de_version(con, obra, numero)[peticion["personaje"]])
        for e in escenas:
            presente = peticion["personaje"] in (e.get("personajes_presentes") or [])
            if presente or coincidencias(_texto_elegido(con, e), formas):
                tocados.add(e["capitulo"])
    return [c for c in brief.capitulos_de_version(con, obra, numero) if c in tocados]


def proponer(con, obra, peticion):
    """Lo que se haria, **sin modelo y sin tocar nada** (`RF-51`, `RF-55`): los
    capitulos de cada salida, la elegida si la hay, la promesa y su punto ciego."""
    numero = peticion.get("version_de_partida") or brief.version_vigente(con, obra)
    if numero is None:
        raise PeticionNoAdmitida("la obra {0} no tiene versiones".format(obra))
    clase = _validar(con, obra, numero, peticion)
    afectados = capitulos_afectados(con, obra, numero, peticion)
    if not afectados:
        raise PeticionNoAdmitida(
            "ninguna escena de la version {0} usa lo que se pide cambiar: no hay nada que "
            "regenerar".format(numero))
    capitulos = brief.capitulos_de_version(con, obra, numero)
    por_salida = {S.CASCADA.value: capitulos[capitulos.index(afectados[0]):],
                  S.SELECTIVA.value: afectados}
    salida = S(SALIDA).value if SALIDA else None
    return {"obra": obra, "version_de_partida": numero, "clase": clase.value,
            "capitulos": por_salida, "salida": salida,
            "capitulos_propuestos": por_salida[salida] if salida else None,
            "motivo": None if salida else SIN_SALIDA,
            "promesa": PROMESA, "punto_ciego": PUNTO_CIEGO}


def pedir(con, obra, peticion):
    """Guarda la peticion y encola su trabajo. Devuelve `(id_trabajo, id_peticion)`.

    Sin salida elegida **no guarda ni encola nada**. Si la lista aceptada no es la que
    la propuesta da hoy, tampoco: el lector acepto otra cosa."""
    propuesta = proponer(con, obra, peticion)
    if propuesta["salida"] is None:
        raise SalidaSinElegir(SIN_SALIDA)
    aceptada = list(peticion.get("capitulos_propuestos") or [])
    if aceptada != propuesta["capitulos_propuestos"]:
        raise ListaCambiada(
            "la lista aceptada no es la que se propone hoy ({0}): la propuesta cambio o se "
            "acepto otra".format(", ".join(propuesta["capitulos_propuestos"])))
    id_p = peticiones.guardar(con, obra, dict(
        peticion, version_de_partida=propuesta["version_de_partida"],
        salida=propuesta["salida"], capitulos_propuestos=aceptada))
    return cola.encolar(con, TIPO_DE_TRABAJO, {"obra": obra, "peticion": id_p}), id_p


def escena_para_regenerar(con, obra, numero, posicion):
    """La escaleta del capitulo nuevo en `posicion` de la version `numero` (`C-6`): el
    capitulo `{capitulo_de_origen}-v{numero}` ya creado en la version, y su escena
    `{capitulo_nuevo}-e1`, copiada de la que sustituye y con su `t_discurso`. Los beats
    -la sinopsis del plan- salen con los nombres nuevos de la cadena (`C-4`, punto 4):
    si no, el prompt pediria el nombre viejo y la vetada lo rechazaria hasta el tope."""
    version = next(v for v in brief.versiones_de(con, obra) if v["numero"] == numero)
    nuevo = brief.capitulos_de_version(con, obra, numero)[posicion - 1]
    viejo = brief.capitulos_de_version(con, obra, version["anterior"])[posicion - 1]
    origen = escaleta.escenas_de_capitulo(con, viejo, obra)[0]
    pares, _ = _renombrados(con, obra, numero)
    beats = []
    for b in origen["beats"] or []:
        if isinstance(b, dict):
            b = dict(b, texto=_con_nombres(b.get("texto"), pares))
        else:
            b = _con_nombres(b, pares)
        beats.append(b)
    return {"id": "{0}-e1".format(nuevo), "orden": origen["orden"], "capitulo": nuevo,
            "cambio_de_valor": origen["cambio_de_valor"], "beats": beats,
            "pov": origen["pov"], "lugar": origen["lugar"],
            "longitud_objetivo": origen["longitud_objetivo"],
            "t_fabula": origen["t_fabula"], "t_discurso": origen["t_discurso"],
            "duracion_ficcional": origen["duracion_ficcional"],
            "personajes_presentes": origen["personajes_presentes"]}


# --- El worker del trabajo de regeneracion -------------------------------------------

# Las ramas de la Parte B (`B-S1.1`, `B-S2.1`), por salida. **Vacio hasta la medida**:
# el worker no escribe nada que la medida no haya elegido.
RAMAS = {}


def atender(con, id_trabajo):
    """Toma un trabajo `regenerar_obra` y lo ejecuta con la rama de su salida. Sin
    rama, lo da por fallido con el motivo: **no se escribe nada**."""
    t = cola.leer(con, id_trabajo)
    if t is None or t.tipo != TIPO_DE_TRABAJO:
        return False
    cola.tomar(con, id_trabajo)
    peticion = peticiones.leer(con, t.carga["peticion"])
    salida = peticion["salida"].value if peticion and peticion["salida"] else None
    rama = RAMAS.get(salida)
    if rama is None:
        cola.registrar_fallo(con, id_trabajo, (
            "la rama de la salida {0} es de la Parte B de PLAN-23 y no existe todavia: no "
            "se ha escrito nada".format(salida or "(ninguna)")))
        return False
    try:
        resultado = rama(con, peticion)
    except Exception as e:  # el motivo tiene que llegar al cliente, sea cual sea
        cola.registrar_fallo(con, id_trabajo, "{0}: {1}".format(type(e).__name__, e))
        return False
    return cola.registrar_resultado(con, id_trabajo, resultado)
