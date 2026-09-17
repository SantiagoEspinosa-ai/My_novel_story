"""Veredictos de los validadores: parseo, puntuacion y mejor version.

Este modulo implementa dos reglas del contrato (`EJECUCION.md` seccion 4):

    Regla 2: un JSON que no parsea cuenta como FALLO, jamas como PASA.
    Regla 1 (parte f): agotada la escalera, se acepta la mejor version.

No hace llamadas de red, no lee configuracion y no escribe archivos: recibe
texto y diccionarios, y devuelve diccionarios y numeros. Eso lo hace facil de
probar sin delegar en ningun subagente.

POR QUE EL PARSEO ES TAN DESCONFIADO
------------------------------------
La respuesta de un validador llega como texto libre. Aunque su prompt le
prohiba las vallas de bloque de codigo y los preambulos, un modelo puede
anadirlos cualquier dia, y una sesion intermedia que imprima la respuesta puede
anadirlos por su cuenta (DECISIONES.md, hallazgo 7). Perder un veredicto por una
valla seria absurdo, asi que se intenta rescatar el JSON de tres formas antes de
rendirse.

Pero rendirse tiene una direccion obligatoria: hacia FALLO. Si un validador roto
aprobara por defecto, la validacion seria decorativa, y justo los capitulos con
problemas raros (los que hacen que un modelo se atragante) serian los que
pasarian sin mirar.

POR QUE LA PUNTUACION YA NO ES UNA MEDIDA
-----------------------------------------
Cuando se podia fijar la temperatura de los validadores en 0.1, juzgar dos veces
el mismo texto daba la misma lista de problemas y la puntuacion era casi una
medida. Con la arquitectura de subagentes la temperatura no se puede fijar
(DECISIONES.md, decision 9), asi que parte de la diferencia entre dos intentos es
ruido del propio validador.

La consecuencia practica esta en el codigo: `mejor_intento` solo ordena intentos
del MISMO capitulo de la MISMA generacion, y no existe ninguna funcion que
compare una puntuacion con un umbral. Aprobar sigue siendo cosa de los tres
PASA, nunca de un numero.
"""

from __future__ import annotations

import json

VALIDADORES = ("continuidad", "genero", "estilo")

# El cuarto auditor del capitulo, y el unico que no es un modelo. Se llama como
# los otros tres y devuelve un veredicto con la misma forma para que el resto
# del harness no tenga que distinguirlo: puntua igual, bloquea igual y sus
# problemas viajan igual con la reescritura. No esta en VALIDADORES porque
# VALIDADORES es la lista de los que hay que esperar antes de resolver, y a este
# no se le espera: ya ha contestado cuando se registra el intento.
VALIDADOR_LONGITUD = "longitud"

GRAVEDADES = ("alta", "media", "baja")

PESOS_POR_DEFECTO = {"alta": 5, "media": 2, "baja": 1}

PASA = "PASA"
FALLO = "FALLO"
INDETERMINADO = "INDETERMINADO"

# Gravedad que se asigna al problema sintetico de un veredicto ilegible. Es
# "alta" a proposito: un validador que no contesta es un agujero en la
# validacion, no una pega menor, y asi el intento nunca gana por defecto a otro
# que si se dejo auditar.
GRAVEDAD_INDETERMINADO = "alta"

# Gravedad de un capitulo fuera del rango de palabras. Es "media" y no "alta"
# porque un capitulo corto o largo sigue siendo un capitulo utilizable: si la
# escalera se agota, puede acabar en el manuscrito y eso es preferible a un
# hueco. Pero pesa mas que una muletilla, porque el rango es un requisito
# explicito de la configuracion y no una opinion sobre la prosa.
GRAVEDAD_LONGITUD = "media"


class ErrorDeVeredicto(Exception):
    """El texto de un validador no se pudo interpretar como veredicto."""


# ---------------------------------------------------------------------------
# Parseo defensivo
# ---------------------------------------------------------------------------


def quitar_vallas(texto):
    """Quita las vallas de bloque de codigo que algunos modelos anaden igual."""
    limpio = texto.strip()
    if limpio.startswith("```"):
        lineas = limpio.splitlines()
        lineas = lineas[1:]                      # la linea ```json
        if lineas and lineas[-1].strip().startswith("```"):
            lineas = lineas[:-1]
        limpio = "\n".join(lineas).strip()
    return limpio


def primer_bloque_equilibrado(texto):
    """Devuelve el primer objeto {...} con las llaves equilibradas, o None.

    Cuenta llaves respetando las cadenas y los escapes, para no confundirse con
    una llave que aparezca dentro de un texto. Sirve para rescatar el JSON
    cuando el modelo lo envuelve en un saludo o una explicacion.
    """
    inicio = texto.find("{")
    if inicio == -1:
        return None

    profundidad = 0
    dentro_de_cadena = False
    escapado = False

    for posicion in range(inicio, len(texto)):
        caracter = texto[posicion]
        if dentro_de_cadena:
            if escapado:
                escapado = False
            elif caracter == "\\":
                escapado = True
            elif caracter == '"':
                dentro_de_cadena = False
            continue
        if caracter == '"':
            dentro_de_cadena = True
        elif caracter == "{":
            profundidad += 1
        elif caracter == "}":
            profundidad -= 1
            if profundidad == 0:
                return texto[inicio:posicion + 1]
    return None


def extraer_json(texto):
    """Convierte la respuesta de un validador en un diccionario.

    Tres intentos, en este orden:
      1. json.loads directo;
      2. quitando las vallas de bloque de codigo;
      3. extrayendo el primer bloque {...} equilibrado, que sobrevive a
         preambulos del tipo "Aqui tienes el JSON:".

    Si los tres fallan, lanza ErrorDeVeredicto. Quien decide si toca reintentar
    la delegacion o dar el veredicto por INDETERMINADO es `src/orquestacion.py`:
    esa es una decision del flujo, no del parseo.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ErrorDeVeredicto("El validador devolvio una respuesta vacia.")

    candidatos = [texto, quitar_vallas(texto)]
    bloque = primer_bloque_equilibrado(quitar_vallas(texto))
    if bloque:
        candidatos.append(bloque)

    ultimo_error = None
    for candidato in candidatos:
        try:
            datos = json.loads(candidato)
        except json.JSONDecodeError as error:
            ultimo_error = error
            continue
        if isinstance(datos, dict):
            return datos
        ultimo_error = "el JSON es valido pero no es un objeto"

    raise ErrorDeVeredicto(
        "No he podido interpretar la respuesta como JSON. Detalle: {0}".format(
            ultimo_error
        )
    )


# ---------------------------------------------------------------------------
# Normalizacion de un veredicto
# ---------------------------------------------------------------------------


def _problema_sintetico(motivo):
    """El problema que se inventa para un veredicto que no se pudo leer.

    Lleva el motivo en la descripcion para que el informe pueda decir QUE fallo,
    no solo que algo fallo. La evidencia queda vacia a proposito: no hay
    fragmento del capitulo que ensenar, porque el problema no esta en el
    capitulo sino en el validador.
    """
    return {
        "gravedad": GRAVEDAD_INDETERMINADO,
        "descripcion": motivo,
        "evidencia": "",
        "correccion_sugerida": (
            "Revisar la respuesta cruda del validador en salida/.tmp/. Si se "
            "repite, cambiar modelos.validadores por un modelo que respete "
            "mejor el formato JSON."
        ),
    }


def veredicto_indeterminado(validador, capitulo, motivo):
    """Construye el veredicto de un validador que no se pudo leer.

    Cuenta como FALLO en todas partes (`es_fallo`, `aprueba`) y suma puntos en
    `puntuar`. La etiqueta INDETERMINADO se conserva aparte del campo
    `veredicto` para que el informe pueda distinguir "el validador dijo que no"
    de "el validador no dijo nada": la primera se arregla reescribiendo el
    capitulo, la segunda cambiando de modelo validador.
    """
    return {
        "validador": validador,
        "capitulo": capitulo,
        "veredicto": INDETERMINADO,
        "problemas": [_problema_sintetico(motivo)],
    }


def veredicto_longitud(capitulo, palabras, minimo, maximo):
    """El veredicto del unico auditor determinista: el contador de palabras.

    Devuelve `None` cuando el capitulo esta dentro de [minimo, maximo]. Fuera de
    rango devuelve un veredicto FALLO con un unico problema de gravedad media,
    con exactamente la misma forma que los de los tres validadores.

    POR QUE ESTO NO LO MIRA UN MODELO
    ---------------------------------
    Contar palabras es determinista: no hace falta delegar en nadie, no cuesta
    una llamada y no puede equivocarse. Dejarselo a los validadores era un hueco
    real del diseno, comprobado en ejecucion (DECISIONES.md, hallazgo 11): el
    validador de genero pidio acortar un capitulo de 1574 palabras, el escritor
    sobrecorrigio hasta 944 (por debajo del minimo de 1200) y ese mismo validador
    lo aprobo. Un aviso por pantalla no arregla eso, porque el aviso lo lee la
    sesion y no el escritor.

    Al entrar en la lista de problemas del intento, en cambio, el escritor recibe
    "te has quedado en 944 palabras y el minimo son 1200" en la reescritura, sin
    que nadie tenga que anadir texto suelto a su ventana: el mismo camino que ya
    recorren los problemas de continuidad, genero y estilo.
    """
    if minimo <= palabras <= maximo:
        return None

    if palabras < minimo:
        descripcion = (
            "El capitulo se queda corto: {0} palabras, y el minimo configurado "
            "son {1}.".format(palabras, minimo)
        )
        correccion = (
            "Desarrollar mas el capitulo hasta entrar en el rango "
            "{0}-{1} palabras. Ampliar escena y subtexto, no anadir relleno "
            "descriptivo.".format(minimo, maximo)
        )
    else:
        descripcion = (
            "El capitulo se pasa de largo: {0} palabras, y el maximo configurado "
            "son {1}.".format(palabras, maximo)
        )
        correccion = (
            "Recortar hasta entrar en el rango {0}-{1} palabras, quitando lo que "
            "no haga avanzar la escena.".format(minimo, maximo)
        )

    return {
        "validador": VALIDADOR_LONGITUD,
        "capitulo": capitulo,
        "veredicto": FALLO,
        "problemas": [{
            "gravedad": GRAVEDAD_LONGITUD,
            "descripcion": descripcion,
            # La evidencia es el propio recuento: no hay un fragmento del texto
            # que ensenar, porque el problema es del capitulo entero.
            "evidencia": "Recuento del intento: {0} palabras (rango configurado: "
                         "{1}-{2}).".format(palabras, minimo, maximo),
            "correccion_sugerida": correccion,
        }],
    }


def _normalizar_problemas(problemas):
    """Deja la lista de problemas con la forma del spec 7.2.

    Un problema sin gravedad reconocible se trata como `alta`. Es deliberado:
    un validador que describe un problema pero se equivoca al etiquetarlo no
    debe salir beneficiado con el peso mas bajo.
    """
    normalizados = []
    for problema in problemas:
        if not isinstance(problema, dict):
            normalizados.append(_problema_sintetico(
                "El validador devolvio un problema que no es un objeto: "
                "{0!r}.".format(problema)
            ))
            continue
        gravedad = str(problema.get("gravedad", "")).strip().lower()
        if gravedad not in GRAVEDADES:
            gravedad = GRAVEDAD_INDETERMINADO
        normalizados.append({
            "gravedad": gravedad,
            "descripcion": str(problema.get("descripcion", "")).strip(),
            "evidencia": str(problema.get("evidencia", "")).strip(),
            "correccion_sugerida": str(
                problema.get("correccion_sugerida", "")
            ).strip(),
        })
    return normalizados


def normalizar(datos, validador, capitulo):
    """Valida y normaliza un veredicto ya parseado (spec 7.2).

    Devuelve siempre un diccionario con la forma del contrato. Cuando los datos
    no cumplen el contrato, devuelve un INDETERMINADO en vez de lanzar: el flujo
    no se detiene por un validador, y la regla 1 dice que ningun capitulo para
    la generacion.

    Las dos comprobaciones que no se perdonan:

    - un veredicto que no sea PASA ni FALLO es INDETERMINADO;
    - un PASA con problemas es INDETERMINADO, porque el spec 7.2 obliga a
      `problemas: []`. Un validador que dice "pasa, pero hay tres cosas mal"
      no ha entendido su trabajo, y creerle seria colar esos tres problemas al
      manuscrito.
    """
    if not isinstance(datos, dict):
        return veredicto_indeterminado(
            validador, capitulo, "La respuesta no es un objeto JSON."
        )

    etiqueta = str(datos.get("veredicto", "")).strip().upper()
    problemas = datos.get("problemas", [])
    if not isinstance(problemas, list):
        return veredicto_indeterminado(
            validador, capitulo,
            "La clave problemas tiene que ser una lista y vino un {0}.".format(
                type(problemas).__name__
            ),
        )

    problemas = _normalizar_problemas(problemas)

    if etiqueta not in (PASA, FALLO):
        return veredicto_indeterminado(
            validador, capitulo,
            "El campo veredicto vale {0!r} y solo se admiten PASA y "
            "FALLO.".format(datos.get("veredicto")),
        )

    if etiqueta == PASA and problemas:
        return veredicto_indeterminado(
            validador, capitulo,
            "El validador devolvio PASA con {0} problema(s). El contrato "
            "obliga a problemas vacio cuando el veredicto es PASA.".format(
                len(problemas)
            ),
        )

    veredicto = {
        "validador": validador,
        "capitulo": capitulo,
        "veredicto": etiqueta,
        "problemas": problemas,
    }

    # El validador de estilo devuelve un campo de mas, `nuevas_frases_recurrentes`,
    # que no es un problema sino material para la memoria de estilo de los
    # capitulos siguientes (prompts/estilo.md). Se conserva tal cual porque un
    # PASA tambien puede traerlo: la frase llamativa de hoy es la muletilla del
    # capitulo ocho, y perderla aqui seria perder la unica senal que detecta
    # repeticiones ENTRE capitulos.
    frases = datos.get("nuevas_frases_recurrentes")
    if isinstance(frases, list):
        veredicto["nuevas_frases_recurrentes"] = [
            str(frase).strip() for frase in frases if str(frase).strip()
        ]

    return veredicto


def leer(texto, validador, capitulo):
    """Texto crudo de un validador -> veredicto normalizado.

    Es la puerta de entrada que usa el orquestador. Nunca lanza: si el texto no
    se puede interpretar, devuelve INDETERMINADO, que cuenta como FALLO.
    """
    try:
        datos = extraer_json(texto)
    except ErrorDeVeredicto as error:
        return veredicto_indeterminado(validador, capitulo, str(error))
    return normalizar(datos, validador, capitulo)


# ---------------------------------------------------------------------------
# Puntuacion y decision
# ---------------------------------------------------------------------------


def es_fallo(veredicto):
    """True salvo que el validador haya dicho PASA explicitamente.

    Escrito en positivo hacia el fallo a proposito: cualquier estado que no sea
    un PASA limpio (FALLO, INDETERMINADO, un diccionario a medias) tiene que
    bloquear.
    """
    return str(veredicto.get("veredicto", "")).strip().upper() != PASA


def aprueba(veredictos):
    """True solo si los tres validadores dijeron PASA (spec 6.1).

    Exige que esten los tres: si falta uno, no hay aprobacion. Un validador que
    no llego a ejecutarse no es un validador que aprueba.

    La lista puede traer un cuarto veredicto, el de `longitud`, que no es un
    modelo sino el contador de palabras (`veredicto_longitud`). No se exige su
    presencia —solo aparece cuando el capitulo esta fuera de rango— pero si
    aparece bloquea como cualquier otro FALLO.
    """
    presentes = {v.get("validador") for v in veredictos}
    if not set(VALIDADORES).issubset(presentes):
        return False
    return all(not es_fallo(veredicto) for veredicto in veredictos)


def puntuar(veredictos, pesos=None):
    """Suma de los problemas por el peso de su gravedad (spec 6.4).

    Menor es mejor. Solo tiene sentido comparar puntuaciones de intentos del
    mismo capitulo dentro de la misma generacion; ver la cabecera del modulo.
    """
    pesos = pesos or PESOS_POR_DEFECTO
    total = 0
    for veredicto in veredictos:
        for problema in veredicto.get("problemas", []):
            gravedad = problema.get("gravedad", GRAVEDAD_INDETERMINADO)
            total += pesos.get(gravedad, pesos.get(GRAVEDAD_INDETERMINADO, 5))
    return total


def problemas_acumulados(intentos):
    """Todos los problemas de todos los intentos, sin repetir descripciones.

    El contrato dice que la lista de problemas se acumula entre intentos y
    viaja con cada reescritura (`EJECUCION.md` 3.5e). Se deduplica por
    descripcion porque los validadores tienden a repetir la misma pega intento
    tras intento, y una lista con la misma frase seis veces le dice al escritor
    menos que una lista con seis pegas distintas.
    """
    vistos = set()
    acumulados = []
    for intento in intentos:
        for veredicto in intento.get("veredictos", []):
            for problema in veredicto.get("problemas", []):
                clave = (veredicto.get("validador"), problema.get("descripcion"))
                if clave in vistos:
                    continue
                vistos.add(clave)
                acumulados.append(dict(problema, validador=veredicto.get("validador")))
    return acumulados


def mejor_intento(intentos):
    """El intento de menor puntuacion; en caso de empate, el mas tardio.

    Cada intento es un diccionario con al menos `intento` (el numero) y
    `puntuacion`. Devuelve None si no hay ninguno.

    El desempate hacia el intento mas tardio no es un capricho: ese intento ha
    incorporado mas feedback acumulado, y eso si es una propiedad real del
    texto, a diferencia de una diferencia de un punto en la puntuacion, que
    desde que no se puede fijar la temperatura puede ser ruido del validador.
    """
    if not intentos:
        return None
    return min(
        intentos,
        key=lambda intento: (intento.get("puntuacion", 0), -intento.get("intento", 0)),
    )
