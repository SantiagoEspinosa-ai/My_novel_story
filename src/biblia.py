"""Gestor de la biblia de la novela (spec seccion 7.1).

La biblia es el ESTADO CANONICO de la novela: lo que ya esta decidido y no se
puede contradecir. La escribe el arquitecto al principio y se va engordando con
los hechos que ocurren en cada capitulo aprobado.

Este modulo se ocupa de cuatro cosas:

    - validar que una biblia cumple el contrato de datos del spec;
    - leerla y escribirla en disco;
    - anadir hechos y entradas de timeline;
    - decidir que hechos entran en la ventana de contexto del escritor.

No hace llamadas de red y no sabe nada de modelos: solo manipula datos.
"""

from __future__ import annotations

import json
from pathlib import Path

GENEROS_PERMITIDOS = ("romance", "drama", "terror")
ROLES_PERMITIDOS = ("protagonista", "antagonista", "secundario")
PERSISTENCIAS_PERMITIDAS = ("permanente", "efimero")

MINIMO_PERSONAJES = 3
MAXIMO_PERSONAJES = 6

NOMBRE_ARCHIVO = "biblia.json"


class ErrorDeBiblia(Exception):
    """La biblia no cumple el contrato de datos, o no se puede leer o escribir.

    El mensaje explica en espanol que falta o que sobra. Cuando el error viene
    de la respuesta del arquitecto, ese mismo mensaje se le devuelve al modelo
    en el reintento, asi que tiene que ser util tambien para el.
    """


# ---------------------------------------------------------------------------
# Validacion del contrato (spec 7.1)
# ---------------------------------------------------------------------------


def _exigir_texto(datos, clave, problemas, contexto=""):
    valor = datos.get(clave)
    if not isinstance(valor, str) or not valor.strip():
        problemas.append(
            "{0}{1} tiene que ser un texto no vacio.".format(contexto, clave)
        )
        return None
    return valor


def _exigir_lista(datos, clave, problemas, contexto=""):
    valor = datos.get(clave)
    if not isinstance(valor, list):
        problemas.append(
            "{0}{1} tiene que ser una lista.".format(contexto, clave)
        )
        return None
    return valor


def _validar_personajes(personajes, problemas):
    if not MINIMO_PERSONAJES <= len(personajes) <= MAXIMO_PERSONAJES:
        problemas.append(
            "personajes tiene {0} entradas y tiene que tener entre {1} y {2}.".format(
                len(personajes), MINIMO_PERSONAJES, MAXIMO_PERSONAJES
            )
        )

    protagonistas = 0
    for indice, personaje in enumerate(personajes):
        contexto = "personajes[{0}].".format(indice)
        if not isinstance(personaje, dict):
            problemas.append(contexto[:-1] + " tiene que ser un objeto.")
            continue

        _exigir_texto(personaje, "nombre", problemas, contexto)
        _exigir_texto(personaje, "motivacion", problemas, contexto)
        _exigir_texto(personaje, "secreto", problemas, contexto)

        rol = personaje.get("rol")
        if rol not in ROLES_PERMITIDOS:
            problemas.append(
                "{0}rol vale {1} y solo admite: {2}.".format(
                    contexto, repr(rol), ", ".join(ROLES_PERMITIDOS)
                )
            )
        if rol == "protagonista":
            protagonistas += 1

        rasgos = personaje.get("rasgos_fijos")
        if not isinstance(rasgos, list) or not rasgos:
            problemas.append(
                contexto + "rasgos_fijos tiene que ser una lista con al menos un rasgo."
            )
        elif not all(isinstance(rasgo, str) and rasgo.strip() for rasgo in rasgos):
            problemas.append(contexto + "rasgos_fijos solo admite textos no vacios.")

    if personajes and protagonistas != 1:
        problemas.append(
            "tiene que haber exactamente un personaje con rol 'protagonista', "
            "y hay {0}.".format(protagonistas)
        )


def _validar_outline(outline, problemas, num_capitulos):
    if num_capitulos is not None and len(outline) != num_capitulos:
        problemas.append(
            "outline tiene {0} entradas y tiene que tener exactamente {1}, una por "
            "capitulo.".format(len(outline), num_capitulos)
        )

    for indice, entrada in enumerate(outline):
        contexto = "outline[{0}].".format(indice)
        if not isinstance(entrada, dict):
            problemas.append(contexto[:-1] + " tiene que ser un objeto.")
            continue
        numero = entrada.get("capitulo")
        esperado = indice + 1
        if not isinstance(numero, int) or isinstance(numero, bool):
            problemas.append(contexto + "capitulo tiene que ser un numero entero.")
        elif numero != esperado:
            problemas.append(
                "{0}capitulo vale {1} y deberia valer {2}: los capitulos van "
                "numerados de 1 en adelante y sin saltos.".format(
                    contexto, numero, esperado
                )
            )
        _exigir_texto(entrada, "sinopsis", problemas, contexto)
        _exigir_texto(entrada, "cambio", problemas, contexto)


def _validar_timeline(timeline, problemas):
    for indice, entrada in enumerate(timeline):
        contexto = "timeline[{0}].".format(indice)
        if not isinstance(entrada, dict):
            problemas.append(contexto[:-1] + " tiene que ser un objeto.")
            continue
        if not isinstance(entrada.get("capitulo"), int) or isinstance(
            entrada.get("capitulo"), bool
        ):
            problemas.append(contexto + "capitulo tiene que ser un numero entero.")
        _exigir_texto(entrada, "momento", problemas, contexto)


def _validar_hechos(hechos, problemas):
    for indice, entrada in enumerate(hechos):
        contexto = "hechos_establecidos[{0}].".format(indice)
        if not isinstance(entrada, dict):
            problemas.append(contexto[:-1] + " tiene que ser un objeto.")
            continue
        if not isinstance(entrada.get("capitulo"), int) or isinstance(
            entrada.get("capitulo"), bool
        ):
            problemas.append(contexto + "capitulo tiene que ser un numero entero.")
        _exigir_texto(entrada, "hecho", problemas, contexto)
        persistencia = entrada.get("persistencia")
        if persistencia not in PERSISTENCIAS_PERMITIDAS:
            problemas.append(
                "{0}persistencia vale {1} y solo admite: {2}.".format(
                    contexto, repr(persistencia), ", ".join(PERSISTENCIAS_PERMITIDAS)
                )
            )


def validar(datos, num_capitulos=None):
    """Comprueba que `datos` cumple el contrato del spec 7.1.

    Si `num_capitulos` se pasa, exige ademas que el outline tenga exactamente
    ese numero de entradas, que es la regla que el arquitecto incumple mas a
    menudo.

    Devuelve los mismos datos si todo esta bien. Lanza ErrorDeBiblia con la
    lista completa de problemas si no. Se acumulan todos los problemas en vez
    de parar en el primero, porque este mensaje viaja al modelo en el reintento
    y conviene que lo arregle todo de una vez.
    """
    if not isinstance(datos, dict):
        raise ErrorDeBiblia(
            "La biblia tiene que ser un objeto JSON, y he recibido un "
            + type(datos).__name__ + "."
        )

    problemas = []

    _exigir_texto(datos, "titulo", problemas)
    _exigir_texto(datos, "premisa", problemas)
    _exigir_texto(datos, "conflicto_central", problemas)

    genero = datos.get("genero")
    if genero not in GENEROS_PERMITIDOS:
        problemas.append(
            "genero vale {0} y solo admite: {1}.".format(
                repr(genero), ", ".join(GENEROS_PERMITIDOS)
            )
        )

    ambientacion = datos.get("ambientacion")
    if not isinstance(ambientacion, dict):
        problemas.append("ambientacion tiene que ser un objeto.")
    else:
        _exigir_texto(ambientacion, "lugar", problemas, "ambientacion.")
        _exigir_texto(ambientacion, "epoca", problemas, "ambientacion.")
        if not isinstance(ambientacion.get("reglas"), list):
            problemas.append(
                "ambientacion.reglas tiene que ser una lista (vacia si el genero no "
                "necesita reglas de mundo)."
            )

    personajes = _exigir_lista(datos, "personajes", problemas)
    if personajes is not None:
        _validar_personajes(personajes, problemas)

    outline = _exigir_lista(datos, "outline", problemas)
    if outline is not None:
        _validar_outline(outline, problemas, num_capitulos)

    timeline = _exigir_lista(datos, "timeline", problemas)
    if timeline is not None:
        _validar_timeline(timeline, problemas)

    hechos = datos.get("hechos_establecidos", [])
    if not isinstance(hechos, list):
        problemas.append("hechos_establecidos tiene que ser una lista.")
    else:
        _validar_hechos(hechos, problemas)

    if problemas:
        lineas = ["La biblia no cumple el contrato de datos. Problemas encontrados:"]
        for numero, problema in enumerate(problemas, start=1):
            lineas.append("{0}. {1}".format(numero, problema))
        raise ErrorDeBiblia("\n".join(lineas))

    return datos


def normalizar(datos):
    """Rellena las claves opcionales que el arquitecto puede haber omitido."""
    datos.setdefault("hechos_establecidos", [])
    datos.setdefault("timeline", [])
    if isinstance(datos.get("ambientacion"), dict):
        datos["ambientacion"].setdefault("reglas", [])
    return datos


# ---------------------------------------------------------------------------
# Disco
# ---------------------------------------------------------------------------


def ruta(directorio_salida):
    """Ruta de biblia.json dentro del directorio de salida."""
    return Path(directorio_salida) / NOMBRE_ARCHIVO


def existe(directorio_salida):
    return ruta(directorio_salida).is_file()


def guardar(biblia, directorio_salida):
    """Escribe la biblia en disco.

    La escritura es atomica: primero a un archivo temporal y despues se
    renombra. Asi, si el proceso muere a media escritura, biblia.json nunca
    queda a medias.
    """
    destino = ruta(directorio_salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".json.tmp")
    temporal.write_text(
        json.dumps(biblia, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporal.replace(destino)
    return destino


def cargar(directorio_salida, num_capitulos=None):
    """Lee biblia.json del disco y la valida antes de devolverla."""
    origen = ruta(directorio_salida)
    if not origen.is_file():
        raise ErrorDeBiblia(
            "No encuentro {0}. Arreglo: lanza una generacion nueva para que el "
            "arquitecto la cree.".format(origen)
        )
    try:
        datos = json.loads(origen.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ErrorDeBiblia(
            "{0} no es JSON valido: {1}\n"
            "Arreglo: borra el directorio de salida y vuelve a empezar.".format(
                origen, error
            )
        ) from error
    return validar(normalizar(datos), num_capitulos)


# ---------------------------------------------------------------------------
# Modificaciones
# ---------------------------------------------------------------------------


def anadir_hecho(biblia, capitulo, hecho, persistencia="efimero"):
    """Anade un hecho establecido y devuelve la entrada creada.

    La persistencia decide su vida util en la ventana de contexto:

        permanente  siempre entra (una muerte, una revelacion estructural);
        efimero     entra solo mientras sea reciente (quien lleva que puesto).

    Etiquetar bien es lo que impide que la ventana del escritor crezca sin
    limite segun avanza la novela.
    """
    if persistencia not in PERSISTENCIAS_PERMITIDAS:
        raise ErrorDeBiblia(
            "persistencia vale {0} y solo admite: {1}.".format(
                repr(persistencia), ", ".join(PERSISTENCIAS_PERMITIDAS)
            )
        )
    if not isinstance(capitulo, int) or isinstance(capitulo, bool) or capitulo < 1:
        raise ErrorDeBiblia(
            "capitulo tiene que ser un entero mayor que cero, y vale "
            + repr(capitulo) + "."
        )
    if not isinstance(hecho, str) or not hecho.strip():
        raise ErrorDeBiblia("El hecho tiene que ser un texto no vacio.")

    entrada = {
        "capitulo": capitulo,
        "hecho": hecho.strip(),
        "persistencia": persistencia,
    }
    biblia.setdefault("hechos_establecidos", []).append(entrada)
    return entrada


def anadir_timeline(biblia, capitulo, momento):
    """Anade o actualiza la entrada de timeline de un capitulo.

    Si el capitulo ya tenia entrada, se sustituye: la timeline tiene como mucho
    una linea por capitulo, y el validador de continuidad la usa para detectar
    saltos temporales imposibles.
    """
    if not isinstance(capitulo, int) or isinstance(capitulo, bool) or capitulo < 1:
        raise ErrorDeBiblia(
            "capitulo tiene que ser un entero mayor que cero, y vale "
            + repr(capitulo) + "."
        )
    if not isinstance(momento, str) or not momento.strip():
        raise ErrorDeBiblia("El momento tiene que ser un texto no vacio.")

    entrada = {"capitulo": capitulo, "momento": momento.strip()}
    timeline = biblia.setdefault("timeline", [])
    for indice, existente in enumerate(timeline):
        if existente.get("capitulo") == capitulo:
            timeline[indice] = entrada
            break
    else:
        timeline.append(entrada)
    timeline.sort(key=lambda linea: linea.get("capitulo", 0))
    return entrada


# ---------------------------------------------------------------------------
# Lectura para la ventana de contexto
# ---------------------------------------------------------------------------


def hechos_vigentes(biblia, capitulo_actual, ventana_hechos=3):
    """Devuelve los hechos que deben entrar en el contexto del escritor.

    Entran:
      - TODOS los hechos permanentes, sin importar su antiguedad;
      - los hechos efimeros de los ultimos `ventana_hechos` capitulos.

    Con ventana_hechos = 3 y capitulo_actual = 10, entran los efimeros de los
    capitulos 7, 8 y 9. Los permanentes de los capitulos 1 y 2 tambien entran:
    si un personaje murio en el capitulo 1, sigue muerto en el 10.

    El orden de la lista original se conserva, porque es el orden cronologico.
    """
    hechos = biblia.get("hechos_establecidos", [])
    if ventana_hechos is None or ventana_hechos < 0:
        ventana_hechos = 0
    primero_visible = capitulo_actual - ventana_hechos

    vigentes = []
    for entrada in hechos:
        if entrada.get("persistencia") == "permanente":
            vigentes.append(entrada)
            continue
        capitulo = entrada.get("capitulo", 0)
        if capitulo >= primero_visible and capitulo < capitulo_actual:
            vigentes.append(entrada)
    return vigentes


def hechos_permanentes(biblia):
    """Solo los hechos permanentes. Es el minimo que nunca se puede recortar."""
    return [
        entrada
        for entrada in biblia.get("hechos_establecidos", [])
        if entrada.get("persistencia") == "permanente"
    ]


def entrada_outline(biblia, capitulo):
    """Devuelve la entrada del outline de un capitulo, o None si no existe."""
    for entrada in biblia.get("outline", []):
        if entrada.get("capitulo") == capitulo:
            return entrada
    return None


def necesita_compactacion(biblia, umbral_compactacion=60):
    """True si hay mas hechos establecidos que el umbral configurado."""
    return len(biblia.get("hechos_establecidos", [])) > umbral_compactacion


def compactar(biblia, umbral_compactacion=60, ventana_hechos=3, capitulo_actual=None):
    """Funde los hechos efimeros antiguos en un resumen por capitulo.

    Contrato (spec 2.3): cuando `hechos_establecidos` supera el umbral, los
    hechos efimeros anteriores a la ventana se fusionan en una unica entrada
    por capitulo y se retiran de la lista activa. Los hechos `permanente` NO se
    compactan nunca, sea cual sea su antiguedad.

    TODO (etapa 5, junto con src/contexto.py): implementar la fusion. Requiere
    una llamada al modelo para redactar el resumen fundido, asi que la hara el
    orquestador pasando aqui el texto ya redactado. Hasta entonces esta funcion
    devuelve la biblia sin tocar, que es el comportamiento seguro: gastar mas
    contexto del necesario no rompe nada, perder un hecho si.
    """
    return biblia
