"""Cargador de configuracion del harness (paso 1 del orden de implementacion).

Responsabilidad unica: construir la CONFIGURACION EFECTIVA, es decir, el
diccionario final que el resto del programa usara, fusionando cuatro capas.

Precedencia de fusion (spec v3, seccion 4.1), de MENOR a MAYOR prioridad:

    1. Valores por defecto embebidos en este archivo.
    2. Perfil del genero activo, tomado de la clave "perfiles" de config.json.
    3. El resto del contenido de config.json.
    4. Variables de entorno con prefijo NOVELA_ (ej. NOVELA_NUM_CAPITULOS=5).

Lo posterior pisa a lo anterior.

Este modulo NO hace llamadas de red. Desde el cambio de arquitectura tampoco
sabe nada de proveedores ni de claves de API: quien habla con el modelo es
Claude Code, y las credenciales son suyas, no del proyecto.
"""

from __future__ import annotations

import copy
import json
import os
from pathlib import Path

# Raiz del proyecto: este archivo vive en <raiz>/src/config.py
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

RUTA_CONFIG_POR_DEFECTO = RAIZ_PROYECTO / "config.json"

PREFIJO_ENTORNO = "NOVELA_"
SEPARADOR_RUTA = "__"

GENEROS_PERMITIDOS = ("romance", "drama", "terror")

# Alias de modelo que acepta la herramienta de subagentes de Claude Code. No se
# usan identificadores completos (claude-opus-5 y compania) porque el alias es
# lo que admite el parametro `model` de la delegacion, y ademas sigue siendo
# valido cuando sale una version nueva del modelo.
MODELOS_PERMITIDOS = ("haiku", "sonnet", "opus", "fable")

# Claves de config.json que NO forman parte de la configuracion efectiva:
# "perfiles" es la fuente de la capa 2, y volcarla entera solo anadiria ruido.
CLAVES_NO_FUSIONABLES = ("perfiles",)


class ErrorDeConfiguracion(Exception):
    """Se lanza cuando la configuracion no se puede cargar o no es valida.

    El mensaje siempre dice, en espanol, que esta mal y como arreglarlo.
    """


# ---------------------------------------------------------------------------
# Capa 1: valores por defecto embebidos en el codigo
# ---------------------------------------------------------------------------

VALORES_POR_DEFECTO = {
    "novela": {
        "titulo": None,
        "genero": "terror",
        "tono": "sobrio, contenido",
        "punto_de_vista": "tercera persona limitada",
        "idioma": "es",
        "semilla_tematica": None,
    },
    "estructura": {
        "num_capitulos": 12,
        "palabras_min": 1200,
        "palabras_max": 2200,
    },
    "modelos": {
        "escalera_escritor": ["haiku", "sonnet", "opus"],
        "intentos_por_modelo": 2,
        "mantener_voz_ganadora": True,
        "arquitecto": "sonnet",
        "validadores": "haiku",
    },
    "validacion": {
        "validadores_activos": ["continuidad", "genero", "estilo"],
        "paralelo": True,
        "pesos_gravedad": {"alta": 5, "media": 2, "baja": 1},
        "reintentos_parseo_json": 1,
        "json_no_parseable_es": "FALLO",
    },
    "contexto": {
        "max_tokens_contexto": 100000,
        "ventana_hechos": 3,
        "umbral_compactacion": 60,
        "capitulos_completos_en_ventana": 1,
        "orden_recorte": ["hechos_efimeros", "resumenes", "capitulo_anterior"],
    },
    "runtime": {
        "directorio_salida": "./salida",
        "directorio_prompts": "./prompts",
        "reanudar_si_existe_estado": True,
        "conservar_intentos": False,
        "nivel_log": "info",
        "registrar_tamano_contexto": True,
    },
    "limites": {
        "delegaciones_max_totales": 300,
        "abortar_si_supera_delegaciones": True,
    },
}


# ---------------------------------------------------------------------------
# Utilidades de fusion
# ---------------------------------------------------------------------------


def _fusionar(base, encima):
    """Fusiona dos diccionarios en profundidad y devuelve uno nuevo.

    Si la misma clave existe en los dos y en ambos es un diccionario, se
    fusionan recursivamente. En cualquier otro caso, el valor de `encima`
    pisa al de `base`. Ninguno de los dos originales se modifica.
    """
    resultado = copy.deepcopy(base)
    for clave, valor in encima.items():
        if (
            clave in resultado
            and isinstance(resultado[clave], dict)
            and isinstance(valor, dict)
        ):
            resultado[clave] = _fusionar(resultado[clave], valor)
        else:
            resultado[clave] = copy.deepcopy(valor)
    return resultado


def _leer_json(ruta):
    """Lee un archivo JSON y falla con un mensaje util si algo va mal."""
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorDeConfiguracion(
            "No encuentro el archivo de configuracion en: {0}.\n"
            "Arreglo: crea ese archivo o pasa la ruta correcta a "
            "cargar_config().".format(ruta)
        )
    try:
        texto = ruta.read_text(encoding="utf-8")
    except OSError as error:
        raise ErrorDeConfiguracion(
            "No puedo leer {0}: {1}".format(ruta, error)
        ) from error
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError as error:
        raise ErrorDeConfiguracion(
            "El archivo {0} no es JSON valido.\n"
            "Detalle: {1}\n"
            "Arreglo: revisa la linea {2}; casi siempre es una coma de mas o "
            "unas comillas sin cerrar.".format(ruta, error, error.lineno)
        ) from error
    if not isinstance(datos, dict):
        raise ErrorDeConfiguracion(
            "El archivo {0} debe contener un objeto JSON (que empiece por una "
            "llave), no una lista ni un valor suelto.".format(ruta)
        )
    return datos


# ---------------------------------------------------------------------------
# Capa 4: variables de entorno NOVELA_
# ---------------------------------------------------------------------------


def _rutas_de_hojas(config, prefijo=()):
    """Devuelve todas las rutas 'hoja' de la configuracion.

    Una hoja es cualquier valor que no sea un diccionario. Por ejemplo, para
    {"estructura": {"num_capitulos": 12}} devuelve [("estructura",
    "num_capitulos")]. Sirve para saber a que ajuste se refiere una variable
    de entorno como NOVELA_NUM_CAPITULOS.
    """
    rutas = []
    for clave, valor in config.items():
        if clave in CLAVES_NO_FUSIONABLES or clave.startswith("_"):
            continue
        ruta = prefijo + (clave,)
        if isinstance(valor, dict) and valor:
            rutas.extend(_rutas_de_hojas(valor, ruta))
        else:
            rutas.append(ruta)
    return rutas


def _interpretar_valor(texto):
    """Convierte el texto de una variable de entorno al tipo que toca.

    Las variables de entorno siempre son cadenas. Se intenta leerlas como
    JSON, de modo que "5" pasa a ser el entero 5, "true" el booleano True y
    "[1, 2]" una lista. Si no es JSON valido (por ejemplo "terror"), se deja
    tal cual como cadena.
    """
    try:
        return json.loads(texto)
    except json.JSONDecodeError:
        return texto


def _asignar_en_ruta(destino, ruta, valor):
    """Escribe `valor` en `destino` siguiendo una ruta de claves anidadas."""
    actual = destino
    for clave in ruta[:-1]:
        actual = actual.setdefault(clave, {})
    actual[ruta[-1]] = valor


def _capa_de_entorno(referencia, entorno):
    """Construye la capa 4 a partir de las variables NOVELA_ del entorno.

    `referencia` es la configuracion ya fusionada de las capas 1 a 3, y se usa
    solo para saber que ajustes existen y donde viven.

    Dos formas de nombrar la variable:
      - Por nombre de ajuste:  NOVELA_NUM_CAPITULOS=5
      - Por ruta completa:     NOVELA_ESTRUCTURA__NUM_CAPITULOS=5
    La segunda hace falta cuando el mismo nombre existe en varias secciones.
    """
    hojas = _rutas_de_hojas(referencia)
    capa = {}

    for nombre, texto in sorted(entorno.items()):
        if not nombre.startswith(PREFIJO_ENTORNO):
            continue
        sufijo = nombre[len(PREFIJO_ENTORNO):]
        if not sufijo:
            continue

        if SEPARADOR_RUTA in sufijo:
            ruta = tuple(parte.lower() for parte in sufijo.split(SEPARADOR_RUTA))
            if ruta not in hojas:
                raise ErrorDeConfiguracion(
                    "La variable de entorno {0} apunta a un ajuste que no existe: "
                    "{1}.\n"
                    "Arreglo: revisa el nombre contra las claves de "
                    "config.json.".format(nombre, ".".join(ruta))
                )
            candidatas = [ruta]
        else:
            objetivo = sufijo.lower()
            candidatas = [ruta for ruta in hojas if ruta[-1] == objetivo]

        if not candidatas:
            raise ErrorDeConfiguracion(
                "La variable de entorno {0} no corresponde a ningun ajuste de la "
                "configuracion.\n"
                "Arreglo: usa el nombre exacto de una clave de config.json, por "
                "ejemplo NOVELA_NUM_CAPITULOS, o borra la variable.".format(nombre)
            )
        if len(candidatas) > 1:
            opciones = ", ".join(
                PREFIJO_ENTORNO + SEPARADOR_RUTA.join(p.upper() for p in ruta)
                for ruta in candidatas
            )
            raise ErrorDeConfiguracion(
                "La variable de entorno {0} es ambigua: ese nombre existe en varias "
                "secciones de la configuracion.\n"
                "Arreglo: usa la ruta completa. Opciones: {1}".format(nombre, opciones)
            )

        _asignar_en_ruta(capa, candidatas[0], _interpretar_valor(texto))

    return capa


# ---------------------------------------------------------------------------
# Validacion
# ---------------------------------------------------------------------------


def _es_entero(valor):
    """True si `valor` es un entero de verdad (True/False no cuentan)."""
    return isinstance(valor, int) and not isinstance(valor, bool)


def _validar_modelos(modelos, problemas):
    """Comprueba que los modelos son alias validos de la herramienta de subagentes.

    Un alias mal escrito (por ejemplo 'opus-5' o 'claude-haiku') no falla al
    arrancar: falla en mitad de la generacion, cuando el orquestador intenta
    delegar. Por eso se comprueba aqui, que es gratis.
    """
    admitidos = ", ".join(MODELOS_PERMITIDOS)

    escalera = modelos.get("escalera_escritor")
    if not isinstance(escalera, list) or not escalera:
        problemas.append(
            "modelos.escalera_escritor tiene que ser una lista con al menos un "
            "modelo. Arreglo: por ejemplo [\"haiku\", \"sonnet\", \"opus\"]."
        )
    else:
        for indice, alias in enumerate(escalera):
            if alias not in MODELOS_PERMITIDOS:
                problemas.append(
                    "modelos.escalera_escritor[{0}] vale {1} y solo se admiten "
                    "estos alias: {2}.".format(indice, repr(alias), admitidos)
                )

    for clave in ("arquitecto", "validadores"):
        alias = modelos.get(clave)
        if alias not in MODELOS_PERMITIDOS:
            problemas.append(
                "modelos.{0} vale {1} y solo se admiten estos alias: {2}.".format(
                    clave, repr(alias), admitidos
                )
            )


def validar(config):
    """Comprueba la configuracion efectiva y acumula todos los errores.

    Se revisan todas las reglas antes de fallar, para que un solo intento te
    liste todo lo que hay que arreglar en vez de ir de uno en uno.
    """
    problemas = []

    novela = config.get("novela", {})
    estructura = config.get("estructura", {})

    genero = novela.get("genero")
    if genero not in GENEROS_PERMITIDOS:
        problemas.append(
            "novela.genero vale {0} y solo se admiten estos tres: {1}. "
            "Arreglo: corrige 'genero' en config.json o la variable "
            "NOVELA_GENERO.".format(repr(genero), ", ".join(GENEROS_PERMITIDOS))
        )

    num_capitulos = estructura.get("num_capitulos")
    if not _es_entero(num_capitulos) or num_capitulos <= 0:
        problemas.append(
            "estructura.num_capitulos vale {0} y tiene que ser un numero entero "
            "mayor que cero. "
            "Arreglo: corrige 'num_capitulos' en config.json o la variable "
            "NOVELA_NUM_CAPITULOS.".format(repr(num_capitulos))
        )

    palabras_min = estructura.get("palabras_min")
    palabras_max = estructura.get("palabras_max")
    minimo_valido = _es_entero(palabras_min) and palabras_min > 0
    maximo_valido = _es_entero(palabras_max) and palabras_max > 0

    if not minimo_valido:
        problemas.append(
            "estructura.palabras_min vale {0} y tiene que ser un numero entero "
            "mayor que cero. "
            "Arreglo: corrige 'palabras_min' en config.json o la variable "
            "NOVELA_PALABRAS_MIN.".format(repr(palabras_min))
        )
    if not maximo_valido:
        problemas.append(
            "estructura.palabras_max vale {0} y tiene que ser un numero entero "
            "mayor que cero. "
            "Arreglo: corrige 'palabras_max' en config.json o la variable "
            "NOVELA_PALABRAS_MAX.".format(repr(palabras_max))
        )
    if minimo_valido and maximo_valido and palabras_min >= palabras_max:
        problemas.append(
            "estructura.palabras_min ({0}) tiene que ser menor que "
            "estructura.palabras_max ({1}). "
            "Arreglo: baja el minimo o sube el maximo en config.json, o revisa el "
            "perfil del genero.".format(palabras_min, palabras_max)
        )

    _validar_modelos(config.get("modelos", {}), problemas)

    if problemas:
        lineas = ["La configuracion no es valida. Problemas encontrados:"]
        for numero, problema in enumerate(problemas, start=1):
            lineas.append("{0}. {1}".format(numero, problema))
        raise ErrorDeConfiguracion("\n".join(lineas))


# ---------------------------------------------------------------------------
# API publica
# ---------------------------------------------------------------------------


def ruta_salida(config):
    """Devuelve el directorio de salida como ruta absoluta.

    Si en la configuracion es relativa (por defecto ./salida), se interpreta
    respecto a la raiz del proyecto, no respecto al directorio desde el que se
    lanza el programa.
    """
    directorio = Path(config.get("runtime", {}).get("directorio_salida", "./salida"))
    if not directorio.is_absolute():
        directorio = RAIZ_PROYECTO / directorio
    return directorio


def volcar_config_efectiva(config):
    """Escribe la configuracion efectiva en <salida>/config-efectiva.json.

    Sirve para que el informe sea reproducible: ahi queda, exactamente, con que
    valores se genero la novela despues de aplicar las cuatro capas.
    """
    directorio = ruta_salida(config)
    directorio.mkdir(parents=True, exist_ok=True)
    destino = directorio / "config-efectiva.json"
    destino.write_text(
        json.dumps(config, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    return destino


def cargar_config(ruta_config=None, entorno=None, volcar=True):
    """Carga, fusiona, valida y (opcionalmente) vuelca la configuracion.

    Argumentos:
        ruta_config: ruta a config.json. Por defecto, el de la raiz del proyecto.
        entorno: diccionario de variables de entorno. Por defecto os.environ.
                 Se puede pasar uno propio, y eso es lo que hacen los tests.
        volcar: si es True, escribe salida/config-efectiva.json.

    Devuelve el diccionario con la configuracion efectiva.
    Lanza ErrorDeConfiguracion si algo no cuadra.
    """
    if ruta_config is None:
        ruta_config = RUTA_CONFIG_POR_DEFECTO
    if entorno is None:
        entorno = os.environ

    desde_archivo = _leer_json(ruta_config)

    # El genero decide que perfil se aplica. Se resuelve antes de fusionar,
    # mirando las capas que pueden definirlo (archivo y entorno), porque el
    # perfil es una capa entera y hay que saber cual cargar.
    genero = desde_archivo.get("novela", {}).get(
        "genero", VALORES_POR_DEFECTO["novela"]["genero"]
    )
    if PREFIJO_ENTORNO + "GENERO" in entorno:
        genero = _interpretar_valor(entorno[PREFIJO_ENTORNO + "GENERO"])

    perfiles = desde_archivo.get("perfiles", {})
    perfil = perfiles.get(genero, {}) if isinstance(perfiles, dict) else {}
    if not isinstance(perfil, dict):
        raise ErrorDeConfiguracion(
            "El perfil del genero '{0}' en config.json deberia ser un objeto JSON. "
            "Arreglo: revisa la seccion 'perfiles'.".format(genero)
        )

    # Capa 3: config.json sin las claves que no forman parte de la fusion.
    capa_archivo = {
        clave: valor
        for clave, valor in desde_archivo.items()
        if clave not in CLAVES_NO_FUSIONABLES
    }

    config = _fusionar(VALORES_POR_DEFECTO, perfil)                # capas 1 y 2
    config = _fusionar(config, capa_archivo)                       # capa 3
    config = _fusionar(config, _capa_de_entorno(config, entorno))  # capa 4

    validar(config)

    if volcar:
        volcar_config_efectiva(config)

    return config
