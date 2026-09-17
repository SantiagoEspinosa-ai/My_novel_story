"""Gestor del estado de progreso (spec seccion 7.3).

`salida/estado.json` es lo que permite matar el proceso en el capitulo 5 y
relanzarlo sin regenerar (ni volver a pagar) los cuatro primeros. Se escribe
tras cada intento, que es la unidad de trabajo mas pequena que puede perderse.

Contrato del archivo:

    {
      "capitulo_actual": 4,
      "intento_actual": 2,
      "modelo_actual": "mistralai/mistral-small-2603",
      "capitulos_aprobados": [1, 2, 3],
      "capitulos_marcados": [],
      "iniciado": "2026-09-17T10:00:00Z"
    }

`capitulos_marcados` son los capitulos que no pasaron limpios: aceptados por
puntuacion o sin generar por un fallo. Nunca detienen la generacion, pero el
informe tiene que poder senalarlos.

Este modulo no hace llamadas de red.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

NOMBRE_ARCHIVO = "estado.json"

CLAVES = (
    "capitulo_actual",
    "intento_actual",
    "modelo_actual",
    "capitulos_aprobados",
    "capitulos_marcados",
    "iniciado",
)


class ErrorDeEstado(Exception):
    """El archivo de estado no se puede leer o no cumple el contrato."""


def _ahora_iso():
    """Marca de tiempo UTC en formato ISO 8601, como en el spec."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def nuevo(modelo_actual=None):
    """Crea un estado en blanco, antes del primer capitulo."""
    return {
        "capitulo_actual": 1,
        "intento_actual": 0,
        "modelo_actual": modelo_actual,
        "capitulos_aprobados": [],
        "capitulos_marcados": [],
        "iniciado": _ahora_iso(),
    }


# ---------------------------------------------------------------------------
# Disco
# ---------------------------------------------------------------------------


def ruta(directorio_salida):
    return Path(directorio_salida) / NOMBRE_ARCHIVO


def existe(directorio_salida):
    return ruta(directorio_salida).is_file()


def guardar(estado, directorio_salida):
    """Escribe el estado en disco de forma atomica.

    Primero a un temporal y despues renombrado: si el proceso muere a media
    escritura, estado.json conserva la version anterior completa en vez de
    quedarse en un JSON truncado que impediria reanudar.
    """
    destino = ruta(directorio_salida)
    destino.parent.mkdir(parents=True, exist_ok=True)
    temporal = destino.with_suffix(".json.tmp")
    temporal.write_text(
        json.dumps(estado, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    temporal.replace(destino)
    return destino


def cargar(directorio_salida):
    """Lee estado.json y comprueba que tiene la forma esperada."""
    origen = ruta(directorio_salida)
    if not origen.is_file():
        raise ErrorDeEstado(
            "No encuentro {0}. Arreglo: no hay nada que reanudar; lanza una "
            "generacion nueva.".format(origen)
        )
    try:
        datos = json.loads(origen.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ErrorDeEstado(
            "{0} no es JSON valido: {1}\n"
            "Arreglo: borra ese archivo para empezar de cero (perderas el "
            "progreso, no los capitulos ya escritos).".format(origen, error)
        ) from error

    if not isinstance(datos, dict):
        raise ErrorDeEstado(
            "{0} deberia contener un objeto JSON.".format(origen)
        )

    faltan = [clave for clave in CLAVES if clave not in datos]
    if faltan:
        raise ErrorDeEstado(
            "A {0} le faltan estas claves: {1}.\n"
            "Arreglo: borra el archivo para empezar de cero.".format(
                origen, ", ".join(faltan)
            )
        )

    for clave in ("capitulos_aprobados", "capitulos_marcados"):
        if not isinstance(datos[clave], list):
            raise ErrorDeEstado(
                "{0}: la clave {1} tiene que ser una lista.".format(origen, clave)
            )

    return datos


def borrar(directorio_salida):
    """Elimina estado.json si existe. Sirve para empezar de cero."""
    destino = ruta(directorio_salida)
    if destino.is_file():
        destino.unlink()
    return destino


# ---------------------------------------------------------------------------
# Reanudacion
# ---------------------------------------------------------------------------


def debe_reanudar(config, directorio_salida):
    """True si hay estado previo y la configuracion permite reanudar.

    Es la condicion del paso 3 del flujo: si existe estado.json y
    `runtime.reanudar_si_existe_estado` es true, se continua desde ahi en vez
    de empezar de cero.
    """
    if not config.get("runtime", {}).get("reanudar_si_existe_estado", True):
        return False
    return existe(directorio_salida)


def cargar_o_nuevo(config, directorio_salida, modelo_actual=None):
    """Devuelve (estado, reanudado).

    `reanudado` es True si el estado viene de disco y False si es nuevo. El
    orquestador lo usa para decidir si llama al arquitecto o carga la biblia
    que ya existe.
    """
    if debe_reanudar(config, directorio_salida):
        return cargar(directorio_salida), True
    return nuevo(modelo_actual), False


def capitulos_pendientes(estado, num_capitulos):
    """Lista de capitulos que todavia hay que generar, en orden.

    Un capitulo esta hecho si esta aprobado o si esta marcado. Marcado significa
    que TIENE TEXTO pero no paso limpio (aceptado por puntuacion): regenerarlo
    al reanudar seria tirar trabajo ya pagado.

    Un capitulo que no llego a generarse no esta marcado ni aprobado: sigue
    pendiente y se reintenta en la siguiente ejecucion. Un fallo de red pasajero
    no puede dejar un agujero permanente en el manuscrito.
    """
    hechos = set(estado.get("capitulos_aprobados", [])) | set(
        estado.get("capitulos_marcados", [])
    )
    return [numero for numero in range(1, num_capitulos + 1) if numero not in hechos]


# ---------------------------------------------------------------------------
# Transiciones
# ---------------------------------------------------------------------------


def empezar_capitulo(estado, capitulo, modelo):
    """Registra que empieza un capitulo nuevo con un modelo dado."""
    estado["capitulo_actual"] = capitulo
    estado["intento_actual"] = 0
    estado["modelo_actual"] = modelo
    return estado


def registrar_intento(estado, modelo=None):
    """Suma uno al contador de intentos del capitulo en curso."""
    estado["intento_actual"] = estado.get("intento_actual", 0) + 1
    if modelo is not None:
        estado["modelo_actual"] = modelo
    return estado


def aprobar_capitulo(estado, capitulo):
    """Marca un capitulo como aprobado, sin duplicarlo."""
    aprobados = estado.setdefault("capitulos_aprobados", [])
    if capitulo not in aprobados:
        aprobados.append(capitulo)
        aprobados.sort()
    marcados = estado.setdefault("capitulos_marcados", [])
    if capitulo in marcados:
        marcados.remove(capitulo)
    return estado


def marcar_capitulo(estado, capitulo):
    """Marca un capitulo como problematico (aceptado por puntuacion o fallido).

    No lo elimina de la generacion: el manuscrito lo incluira igualmente. Solo
    deja constancia para el informe, y evita que la reanudacion lo reintente en
    bucle.
    """
    marcados = estado.setdefault("capitulos_marcados", [])
    if capitulo not in marcados:
        marcados.append(capitulo)
        marcados.sort()
    return estado


def resumen_legible(estado, num_capitulos=None):
    """Una linea de texto para el log al arrancar."""
    aprobados = len(estado.get("capitulos_aprobados", []))
    marcados = len(estado.get("capitulos_marcados", []))
    total = " de {0}".format(num_capitulos) if num_capitulos else ""
    return (
        "capitulos aprobados: {0}{1}; marcados: {2}; iniciado: {3}".format(
            aprobados, total, marcados, estado.get("iniciado", "?")
        )
    )
