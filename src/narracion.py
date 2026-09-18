"""Traduce el estado del harness a frases que se entiendan sin conocerlo.

POR QUE EXISTE ESTE MODULO
--------------------------
El panel tenia los datos y aun asi no se entendia. Ensenaba campos sueltos
—`rol: escritor`, `capitulo: 5`, `intento: 2`, `modelo: opus`— y quien miraba
tenia que recomponer la frase en su cabeza cada vez. Peor: durante los pasos
que no son una delegacion (copiar archivos, pedir el outline al arquitecto) no
habia ningun campo que ensenar, asi que la pantalla decia «sin actividad»
mientras el servidor estaba trabajando.

Aqui se convierte todo eso en **una frase en lenguaje llano**. No es un adorno:
es la diferencia entre un panel que informa y uno que hay que interpretar.

EL TONO
-------
Sujeto, verbo y lo que hace, como se lo contarias a alguien por encima del
hombro:

    «El arquitecto esta disenando que pasa en los capitulos 5 y 6»
    «El escritor esta redactando el capitulo 5, intento 2 de 6, con opus»
    «Los tres validadores estan auditando el capitulo 5 a la vez»
    «El capitulo 5 no paso: estilo encontro 3 problemas. Reescribiendo»

Nada de jerga del sistema: ni `delegacion_en_curso`, ni `FALLO`, ni
`ACEPTADO_POR_PUNTUACION`. Quien mira el panel no tiene por que saber como se
llaman las cosas por dentro.

Este modulo no toca disco ni red: recibe diccionarios y devuelve texto.
"""

from __future__ import annotations

# Las fases que el servidor recorre por su cuenta, antes y alrededor de la
# generacion. Las de la generacion no estan aqui: esas se deducen del estado
# que escribe el propio harness.
FASE_INACTIVA = "inactiva"
FASE_COPIANDO = "copiando"
FASE_ARQUITECTO = "arquitecto"
FASE_VALIDANDO = "validando"
FASE_LANZANDO = "lanzando"
FASE_GENERANDO = "generando"
FASE_TERMINADA = "terminada"
FASE_CAIDA = "caida"
FASE_DETENIDA = "detenida"
FASE_FALLO_AMPLIACION = "fallo_ampliacion"

# Termino con codigo 0 y no escribio nada. Parece un exito y no lo es: paso de
# verdad cuando la sesion no pudo ejecutar los comandos del harness por
# permisos, lo explico en su log y salio limpiamente. El panel decia «terminó
# bien» sobre una novela que no se habia tocado.
FASE_SIN_EFECTO = "sin_efecto"

# Cuanto es «lo normal» en cada fase, en segundos. Pasado ese tiempo la frase
# se acompana de un comentario, porque la alternativa es que quien mira se
# quede adivinando si aquello se ha colgado.
#
# Los numeros salen de lo medido en este proyecto, no de una intuicion: una
# delegacion al arquitecto ronda el minuto, un escritor con opus dos o tres, y
# los validadores en paralelo tardan lo que el mas lento de los tres.
NORMAL_SEGUNDOS = {
    FASE_COPIANDO: 30,
    FASE_ARQUITECTO: 180,
    FASE_VALIDANDO: 20,
    FASE_LANZANDO: 60,
    "escritor": 300,
    "validadores": 240,
    "resumidor": 150,
    "arquitecto": 180,
}
NORMAL_POR_DEFECTO = 600

ROLES_VALIDADORES = ("continuidad", "genero", "estilo")

# Entre un paso y el siguiente no hay nadie trabajando, y aun asi la cosa
# avanza. La primera version de esta frase explicaba el mecanismo —«entre una
# delegacion y la siguiente no hay ningun subagente trabajando»— y eso es
# exactamente lo que este modulo existe para no hacer: quien mira la pantalla
# no tiene por que saber que hay delegaciones ni subagentes.
#
# Cuando no se sabe bien que esta pasando, la respuesta corta es mejor que una
# explicacion de por que no se sabe.
FRASE_ENTRE_PASOS = "Preparando el siguiente paso"


def _lista_en_castellano(numeros):
    """[5] -> '5'; [5, 6] -> '5 y 6'; [5, 6, 7] -> '5, 6 y 7'."""
    numeros = [str(n) for n in numeros]
    if not numeros:
        return ""
    if len(numeros) == 1:
        return numeros[0]
    return ", ".join(numeros[:-1]) + " y " + numeros[-1]


def duracion_legible(segundos):
    """'45 s', '2 min 05 s', '1 h 12 min'. None si no se sabe."""
    if segundos is None:
        return None
    segundos = int(segundos)
    if segundos < 60:
        return "{0} s".format(segundos)
    minutos, resto = divmod(segundos, 60)
    if minutos < 60:
        return "{0} min {1:02d} s".format(minutos, resto)
    horas, minutos = divmod(minutos, 60)
    return "{0} h {1:02d} min".format(horas, minutos)


def intentos_maximos(config):
    """Cuantos intentos caben por capitulo, segun la escalera configurada."""
    modelos = (config or {}).get("modelos", {}) or {}
    escalera = modelos.get("escalera_escritor")
    peldanos = len(escalera) if isinstance(escalera, list) and escalera else 3
    por_modelo = modelos.get("intentos_por_modelo")
    try:
        por_modelo = int(por_modelo)
    except (TypeError, ValueError):
        por_modelo = 2
    return max(1, peldanos * max(1, por_modelo))


# ---------------------------------------------------------------------------
# La frase de lo que esta pasando ahora
# ---------------------------------------------------------------------------


def frase_de_delegacion(marca, config=None):
    """Que esta haciendo el subagente que hay trabajando ahora mismo.

    `marca` es `delegacion_en_curso` de `estado.json`: el rol, el modelo, el
    capitulo y el intento. Aqui se convierte en una frase.

    El rol `validadores` significa los tres a la vez, que es como se lanzan de
    verdad, y la frase lo dice: «los tres validadores», no «validadores».
    """
    if not marca:
        return None
    rol = str(marca.get("rol") or "").lower()
    capitulo = marca.get("capitulo")
    intento = marca.get("intento")
    modelo = marca.get("modelo")

    if rol == "arquitecto":
        return "El arquitecto está escribiendo la biblia de la novela"

    if rol == "escritor":
        partes = ["El escritor está redactando el capítulo {0}".format(capitulo)]
        if intento:
            tope = intentos_maximos(config)
            partes.append("intento {0} de {1}".format(intento, tope))
        if modelo:
            partes.append("con {0}".format(modelo))
        return ", ".join(partes)

    if rol == "validadores":
        return ("Los tres validadores están auditando el capítulo {0} a la vez"
                .format(capitulo))

    if rol in ROLES_VALIDADORES:
        nombre = "género" if rol == "genero" else rol
        return "El validador de {0} está auditando el capítulo {1}".format(
            nombre, capitulo)

    if rol == "resumidor":
        return ("Resumiendo el capítulo {0}, que ya está cerrado, para que los "
                "siguientes sepan qué pasó".format(capitulo))

    if not rol:
        return None
    return "Trabajando: {0}".format(rol)


def frase_de_fase(fase, datos=None):
    """La frase de una fase que lleva el servidor, no el harness."""
    datos = datos or {}
    capitulos = datos.get("capitulos_nuevos") or []

    if fase == FASE_COPIANDO:
        destino = datos.get("destino")
        if destino:
            return "Copiando la novela actual a {0}, antes de tocar nada".format(destino)
        return "Copiando la novela actual antes de tocar nada"

    if fase == FASE_ARQUITECTO:
        if capitulos:
            return ("El arquitecto está diseñando qué pasa en {0} {1}".format(
                "el capítulo" if len(capitulos) == 1 else "los capítulos",
                _lista_en_castellano(capitulos)))
        return "El arquitecto está diseñando los capítulos nuevos"

    if fase == FASE_VALIDANDO:
        return "Comprobando que el plan nuevo encaja con la novela que ya existe"

    if fase == FASE_LANZANDO:
        if capitulos:
            # «del capítulo», no «de el capítulo»: la contracción no es un
            # detalle cosmético cuando la frase se proyecta a 80 píxeles.
            return ("Arrancando la escritura {0} {1}".format(
                "del capítulo" if len(capitulos) == 1 else "de los capítulos",
                _lista_en_castellano(capitulos)))
        return "Arrancando la generación"

    return None


def frase_de_reposo(resumen):
    """Que decir cuando no hay nada en marcha.

    Nunca «sin actividad» a secas: eso no distingue una novela terminada de una
    que se cayo hace una hora.

    Pero tampoco tres frases encadenadas. La primera version pegaba el estado Y
    lo ultimo que paso, y salia esto:

        «No hay nada en marcha. La última generación terminó bien. Lo último
         que pasó: La sesión está decidiendo el siguiente paso: entre una...»

    La tercera frase era ruido y ademas repetia lo que ya decia la segunda. Si
    se sabe como termino, con eso basta; solo cuando NO se sabe se recurre a
    contar lo ultimo que se vio.
    """
    resumen = resumen or {}
    fase = resumen.get("fase")

    conocidas = {
        FASE_TERMINADA: "No hay nada en marcha. La última generación terminó bien.",
        FASE_DETENIDA: "No hay nada en marcha. La última generación se paró a mano.",
        FASE_CAIDA: "No hay nada en marcha. La última generación se cayó sin terminar.",
        FASE_SIN_EFECTO: ("No hay nada en marcha. La última generación terminó sin "
                          "escribir nada; el log dice por qué."),
        FASE_FALLO_AMPLIACION: ("No hay nada en marcha. La ampliación no salió "
                                "adelante y la novela quedó como estaba."),
    }
    if fase in conocidas:
        return conocidas[fase]

    ultimo = resumen.get("ultima_frase")
    if ultimo:
        return "No hay nada en marcha. Lo último: {0}.".format(ultimo.rstrip("."))
    return "No hay nada en marcha."


def comentario_si_tarda(clave, segundos):
    """Un aviso cuando una fase se alarga mas de lo normal, o None.

    No dice que algo vaya mal, porque normalmente no va mal: dice cuanto lleva
    y que eso es mas de lo habitual. La alternativa —callarse— deja a quien
    mira preguntandose si se colgo, que es justo lo que este panel existe para
    evitar.
    """
    if segundos is None:
        return None
    normal = NORMAL_SEGUNDOS.get(clave, NORMAL_POR_DEFECTO)
    if segundos <= normal:
        return None
    return ("Lleva {0}, más de lo normal para este paso (suele tardar unos {1}). "
            "Todavía puede terminar bien; si te cansas de esperar, se puede "
            "detener.".format(duracion_legible(segundos), duracion_legible(normal)))


# ---------------------------------------------------------------------------
# Lo que acaba de pasar: eventos entre dos fotos del estado
# ---------------------------------------------------------------------------


def eventos_entre(antes, despues, problemas_por_capitulo=None, total_capitulos=None):
    """Frases de lo que ha cambiado entre dos lecturas de `estado.json`.

    Sirve para el historico: sin esto, el panel solo sabria decir que esta
    pasando ahora, y se perderia lo que paso mientras no mirabas, que es
    justo lo que hace falta para seguir una generacion larga.

    `problemas_por_capitulo` permite decir POR QUE no paso un capitulo, que es
    mas util que decir que no paso.
    """
    antes = antes or {}
    despues = despues or {}
    problemas_por_capitulo = problemas_por_capitulo or {}
    frases = []

    aprobados_antes = set(antes.get("capitulos_aprobados") or [])
    aprobados_ahora = set(despues.get("capitulos_aprobados") or [])
    marcados_antes = set(antes.get("capitulos_marcados") or [])
    marcados_ahora = set(despues.get("capitulos_marcados") or [])

    for capitulo in sorted(aprobados_ahora - aprobados_antes):
        frase = "Capítulo {0} aprobado limpio".format(capitulo)
        siguiente = _siguiente_pendiente(despues, capitulo, total_capitulos)
        if siguiente:
            frase += ". Pasando al {0}".format(siguiente)
        frases.append(frase)

    for capitulo in sorted(marcados_ahora - marcados_antes):
        detalle = problemas_por_capitulo.get(capitulo)
        if detalle:
            frase = ("Capítulo {0} entregado sin pasar limpio: {1}"
                     .format(capitulo, detalle))
        else:
            frase = ("Capítulo {0} entregado sin pasar limpio: se agotaron los "
                     "intentos y entró la mejor versión".format(capitulo))
        siguiente = _siguiente_pendiente(despues, capitulo, total_capitulos)
        if siguiente:
            frase += ". Pasando al {0}".format(siguiente)
        frases.append(frase)

    return frases


def frase_de_reescritura(capitulo, veredictos):
    """«El capitulo 5 no paso: estilo encontro 3 problemas. Reescribiendo».

    `veredictos` es la lista de veredictos de un intento, tal y como los guarda
    el harness. Se nombra a quien suspendio y cuanto encontro, porque «no paso»
    a secas no dice si hay que tocar la prosa o la continuidad.
    """
    suspenden = []
    for veredicto in veredictos or []:
        if str(veredicto.get("veredicto", "")).upper() == "PASA":
            continue
        nombre = veredicto.get("validador") or "un validador"
        if nombre == "genero":
            nombre = "género"
        cuantos = len(veredicto.get("problemas") or [])
        if cuantos:
            suspenden.append("{0} encontró {1} problema{2}".format(
                nombre, cuantos, "" if cuantos == 1 else "s"))
        else:
            suspenden.append("{0} lo suspendió".format(nombre))

    if not suspenden:
        return None
    return "El capítulo {0} no pasó: {1}. Reescribiendo".format(
        capitulo, _lista_en_castellano_texto(suspenden))


def _lista_en_castellano_texto(trozos):
    if len(trozos) == 1:
        return trozos[0]
    return ", ".join(trozos[:-1]) + " y " + trozos[-1]


def _siguiente_pendiente(estado, desde, total):
    """El primer capitulo que queda por hacer despues de `desde`."""
    if not total:
        return None
    hechos = set(estado.get("capitulos_aprobados") or []) | set(
        estado.get("capitulos_marcados") or [])
    for numero in range(desde + 1, int(total) + 1):
        if numero not in hechos:
            return numero
    return None
