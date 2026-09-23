"""Lo que preguntan las cuatro capacidades que cuelgan de estas dos tablas.

QUE SIGNIFICA "USAR UN HECHO": AQUI NO SE DECIDE, AQUI SE PARAMETRIZA
----------------------------------------------------------------------
Es la pregunta que `SPEC-21` C-2 dejo deliberadamente abierta. Mencionar un
hecho, depender de el y contradecirlo no son lo mismo, y cada consumidor
necesita un subconjunto distinto:

    aparece en algun capitulo   `menciona`
    regeneracion selectiva      `establece`, `depende`
    ficha de personaje          `establece`, `menciona`, `depende`
    fichero Lean                los cuatro

Las cuatro constantes de abajo **son** esa decision, y estan sueltas a
proposito: cambiarlas es editar una linea. No hay migracion detras porque las
cuatro clases de fila ya estan escritas en la tabla; lo unico que cambia es
cuales se cuentan al preguntar.

POR QUE ESTE MODULO NO IMPORTA DE NINGUNA OTRA FEATURE
--------------------------------------------------------
`A-02`. Las fechas de nacimiento viven en la tabla `entidad`, que es de
`consolidacion/`, y aun asi no se leen desde aqui: se reciben como argumento.
El acoplamiento entre features viaja por SQL sin que ningun `import` lo delate
(`F-28`), y una consulta a la tabla de otra feature es exactamente eso. Quien
compone es `orquestacion/`.
"""

from datetime import datetime

from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.cronologia import repository as repo

# --- La decision parametrizada ---------------------------------------------

PARA_APARICION = (U.MENCIONA,)
PARA_REGENERACION = (U.ESTABLECE, U.DEPENDE)
PARA_FICHA = (U.ESTABLECE, U.MENCIONA, U.DEPENDE)
PARA_LEAN = tuple(U)


def cobertura_de_tipos():
    """Quien rellena cada tipo hoy. Lo que permite no leer un vacio como un cero.

    `contradice` se puede escribir y **no lo deduce nadie**, asi que una
    consulta que no devuelva contradicciones no esta diciendo que no las haya:
    esta diciendo que nadie ha mirado. Sin este mapa, las dos respuestas son la
    misma lista vacia.
    """
    return {
        U.ESTABLECE: "delta",
        U.DEPENDE: "delta",
        U.MENCIONA: "regla",
        U.CONTRADICE: "no_se_deduce",
    }


# --- Donde se usa un hecho --------------------------------------------------


def _capitulos(filas):
    """Los capitulos distintos, en orden, **sin los vacios**.

    Una escena anterior a `SPEC-21` no tiene capitulo. Colar ese `None` en la
    lista lo convertiria en un capitulo llamado `None` en cuanto alguien la
    pintara, que es la forma mas rapida de que un hueco se lea como un dato.
    """
    return sorted({f["capitulo"] for f in filas if f["capitulo"]})


def capitulos_donde_se_usa(con, hecho, tipos=PARA_FICHA):
    return _capitulos(repo.usos_de_hecho(con, hecho, tipos))


def capitulos_a_regenerar(con, hecho):
    """Que hay que reescribir si el lector cambia este hecho.

    Solo `establece` y `depende`. Un capitulo que se limita a nombrarlo sigue
    siendo cierto con el hecho cambiado, y arrastrarlo multiplicaria el coste
    de un cambio pequeño por toda la novela.
    """
    return _capitulos(repo.usos_de_hecho(con, hecho, PARA_REGENERACION))


def capitulos_de_la_ficha(con, hecho):
    return _capitulos(repo.usos_de_hecho(con, hecho, PARA_FICHA))


def aparece_en_algun_capitulo(con, hecho):
    """Lo que necesita el validador de elementos personalizados.

    Devuelve tambien cuantos usos no tienen capitulo: si el hecho solo se usa
    en escenas sin capitulo, `aparece` es falso **y hay algo que mirar**, que no
    es lo mismo que no aparecer en ninguna parte.
    """
    filas = repo.usos_de_hecho(con, hecho, PARA_APARICION)
    capitulos = _capitulos(filas)
    return {"aparece": bool(capitulos),
            "capitulos": capitulos,
            "usos_sin_capitulo": len([f for f in filas if not f["capitulo"]])}


# --- Las tres que sostienen el fichero Lean --------------------------------


def _instante(texto):
    """La fecha como objeto, o `None` si no se deja leer. Nunca revienta."""
    try:
        return datetime.fromisoformat(texto)
    except (TypeError, ValueError):
        return None


def orden_temporal(con, obra):
    """Compara el orden de la fabula con el del discurso.

    Son **dos ejes**, y esa es la mitad del genero: casi todo el miedo vive en
    la diferencia entre lo que ya ocurrio y el lector aun no sabe. Una
    inversion no es un error por si misma -una analepsis es exactamente eso-,
    es lo que `INV-08` exige que este declarado.

    Devuelve los eventos en orden de fabula y los pares de eventos en que el
    capitulo avanza y el tiempo retrocede.
    """
    eventos = repo.eventos_de(con, obra)
    por_capitulo = sorted(
        [e for e in eventos if e["capitulo"]],
        key=lambda e: (e["capitulo"], e["id"]))
    inversiones = []
    for anterior, siguiente in zip(por_capitulo, por_capitulo[1:]):
        t1, t2 = _instante(anterior["t_fabula"]), _instante(siguiente["t_fabula"])
        if t1 is not None and t2 is not None and t2 < t1:
            inversiones.append((anterior["id"], siguiente["id"]))
    return {"ordenados": [e["id"] for e in eventos],
            "inversiones": inversiones,
            "sin_fecha_legible": [e["id"] for e in eventos
                                  if _instante(e["t_fabula"]) is None]}


def edades(con, obra, fechas_de_nacimiento):
    """Quien aparece antes de haber nacido, y de quien no se puede saber.

    `fechas_de_nacimiento` llega como argumento y no se consulta aqui: la tabla
    `entidad` es de otra feature (`A-02`).

    **La fecha es opcional, asi que la comprobacion se salta y lo dice.** Un
    `incoherentes` vacio junto a un `sin_fecha_de_nacimiento` lleno no significa
    que las edades cuadren; significa que no se han podido mirar. Separarlos es
    la unica forma de que quien lea el resultado no confunda las dos cosas.
    """
    incoherentes, sin_fecha, sin_leer = [], set(), []
    for evento in repo.eventos_de(con, obra):
        t = _instante(evento["t_fabula"])
        if t is None:
            sin_leer.append(evento["id"])
            continue
        for personaje in repo.participantes_de(con, evento["id"]):
            nacimiento = _instante(fechas_de_nacimiento.get(personaje))
            if nacimiento is None:
                sin_fecha.add(personaje)
                continue
            if t < nacimiento:
                incoherentes.append({
                    "personaje": personaje, "evento": evento["id"],
                    "t_fabula": evento["t_fabula"],
                    "fecha_de_nacimiento": fechas_de_nacimiento[personaje]})
    return {"incoherentes": incoherentes,
            "sin_fecha_de_nacimiento": sorted(sin_fecha),
            "sin_fecha_legible": sin_leer}


def _solapan(a, b):
    """Dos intervalos `[t, t+duracion)`. Sin duracion, un instante.

    El intervalo es medio abierto, asi que dos eventos pegados -uno acaba a las
    21:30 y el otro empieza a las 21:30- **no** solapan: dar por conflictivo un
    personaje que sale de una habitacion y entra en otra llenaria de falsos
    positivos cualquier novela con movimiento.

    Dos eventos instantaneos en el mismo momento si solapan, y por eso hay una
    segunda condicion: con duracion cero el intervalo esta vacio y la primera
    no se cumple nunca, de modo que dos cosas que pasan a la vez en dos sitios
    se colarian sin que nadie las viera.
    """
    inicio_a, duracion_a = a[0], a[1]
    inicio_b, duracion_b = b[0], b[1]
    se_cruzan = inicio_a < inicio_b + duracion_b and inicio_b < inicio_a + duracion_a
    mismo_instante = inicio_a == inicio_b
    return se_cruzan or mismo_instante


def ubicuidades(con, obra, con_incidencias=False):
    """Nadie en dos lugares a la vez.

    Recorre por personaje y no por evento: la pregunta es sobre una persona
    cruzando el tiempo, y por eso el indice de `participacion_en_evento` va por
    `personaje`.

    Con `con_incidencias` devuelve tambien los eventos cuya fecha no se deja
    leer. Sin ese dato, una obra entera con fechas en prosa daria cero
    conflictos y pareceria limpia.
    """
    from datetime import timedelta

    eventos = repo.eventos_de(con, obra)
    sin_leer = [e["id"] for e in eventos if _instante(e["t_fabula"]) is None]

    personajes = {p for e in eventos for p in repo.participantes_de(con, e["id"])}
    conflictos = []
    for personaje in sorted(personajes):
        presencias = []
        for p in repo.presencias_de_personaje(con, obra, personaje):
            t = _instante(p["t_fabula"])
            if t is None:
                continue
            presencias.append(
                (t, timedelta(minutes=p["duracion_min"] or 0), p))
        for i, a in enumerate(presencias):
            for b in presencias[i + 1:]:
                if a[2]["lugar"] == b[2]["lugar"]:
                    continue
                if _solapan(a, b):
                    conflictos.append({
                        "personaje": personaje,
                        "eventos": [a[2]["evento"], b[2]["evento"]],
                        "lugares": [a[2]["lugar"], b[2]["lugar"]]})
    if con_incidencias:
        return {"conflictos": conflictos, "sin_fecha_legible": sin_leer}
    return conflictos
