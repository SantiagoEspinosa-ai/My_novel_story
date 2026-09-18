"""Filtro de redaccion: enmascara valores sensibles antes de escribirlos a disco.

Por que existe
--------------
Este harness no gestiona credenciales: las llaves son de Claude Code, no del
proyecto (regla de CLAUDE.md). Aun asi, hay un sitio por el que un secreto
podria colarse a un archivo: la capa 4 de la configuracion copia variables de
entorno con prefijo `NOVELA_` dentro de la configuracion efectiva, y esa
configuracion se vuelca a `salida/config-efectiva.json`. Ese archivo se guarda,
se comparte para reproducir una generacion y lo lee el panel por red.

Basta con que alguien defina una variable del estilo `NOVELA_..._TOKEN` para que
su valor acabe escrito en claro. Este modulo es el cinturon de seguridad: se
pasa por el cualquier estructura antes de serializarla, y los valores cuya
CLAVE parece nombrar un secreto salen sustituidos por una marca.

Que se considera sensible
-------------------------
Se mira el NOMBRE de la clave, nunca el valor: adivinar si una cadena "parece"
una clave de API da falsos positivos sin fin, mientras que quien nombra un
ajuste `api_key` esta diciendo lo que guarda. La comparacion no distingue
mayusculas y busca el patron como subcadena, de modo que `API_KEY`,
`clave_token`, `x-auth-header` o `credentials` caen todos.

Buscar como subcadena enmascara de mas en casos raros (una clave llamada
`monkey` contiene `key`, y `author` contiene `auth`). Es deliberado: enmascarar
de mas estropea la legibilidad de un volcado, enmascarar de menos filtra un
secreto. Ante la duda, gana la seguridad.
"""

# Los patrones se comparan en minusculas contra el nombre de la clave. Se
# guardan en mayusculas porque asi es como se nombran las variables de entorno,
# que es de donde viene el riesgo.
PATRONES_SENSIBLES = ("KEY", "TOKEN", "SECRET", "AUTH", "CREDENTIAL")

# Excepciones: claves de ESTE harness que contienen un patron pero no guardan
# ningun secreto. Aqui `token` significa token de modelo, la unidad en la que se
# mide una ventana de contexto, y redactarlas estropearia datos que hacen falta
# para reproducir una generacion y para el panel.
#
# La lista es de nombres exactos, no de patrones: una excepcion amplia volveria
# a abrir el agujero que el filtro cierra. Si aparece un ajuste nuevo que caiga
# por error, se anade aqui con su nombre completo.
CLAVES_EXENTAS = (
    "max_tokens_contexto",  # presupuesto de la ventana de contexto
    "tokens",               # tamano de una ventana ya montada
    "tokens_in",            # tokens de entrada de una delegacion
    "tokens_out",           # tokens de salida de una delegacion
    "sin_tokens",           # cuantas delegaciones se anotaron sin cifras
)

# Lo que se escribe en lugar del valor. Es un texto reconocible a simple vista:
# quien abra el archivo tiene que entender que ahi habia algo y que se quito a
# proposito, en vez de creer que el ajuste estaba vacio.
MARCA = "[REDACTADO]"


def es_clave_sensible(nombre):
    """Dice si el nombre de una clave sugiere que guarda un secreto.

    `nombre` puede no ser una cadena: en un JSON cargado las claves siempre lo
    son, pero un diccionario de Python admite otras cosas. En ese caso se
    convierte a texto antes de comparar, para no reventar por un tipo raro.

    Las claves de `CLAVES_EXENTAS` se descartan antes de mirar los patrones.
    """
    texto = str(nombre).lower()
    if texto in CLAVES_EXENTAS:
        return False
    return any(patron.lower() in texto for patron in PATRONES_SENSIBLES)


def redactar(dato):
    """Devuelve una copia de `dato` con los valores sensibles enmascarados.

    Recorre diccionarios y listas en profundidad. No modifica el original: el
    harness sigue trabajando con la configuracion completa en memoria y lo unico
    redactado es la copia que se va a escribir.

    Se enmascara el valor entero, sea del tipo que sea, y no solo las cadenas:
    un secreto mal tipado (un numero, una lista de dos claves) sigue siendo un
    secreto.
    """
    if isinstance(dato, dict):
        return {
            clave: (MARCA if es_clave_sensible(clave) else redactar(valor))
            for clave, valor in dato.items()
        }
    if isinstance(dato, (list, tuple)):
        # Las listas se recorren porque pueden contener diccionarios; una lista
        # de valores sueltos no se toca, ya que sin clave no hay nada que
        # delate un secreto.
        return [redactar(elemento) for elemento in dato]
    return dato
