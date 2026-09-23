"""Leer los dos ficheros de configuracion y **fallar bien** si no valen.

POR QUE LOS ERRORES SON LARGOS
--------------------------------
Porque quien los lee esta a punto de lanzar una tanda que cuesta dinero y
horas. Un `FileNotFoundError` pelado obliga a adivinar cual de los dos ficheros
falta; un `ValidationError` de Pydantic dice el campo pero no dice **cual de
las dos configuraciones** lo traia ni donde esta el fichero.

Los tres modos de fallo son distintos y se distinguen a proposito:

    no existe       la ruta, para poder mirarla
    no es JSON      con la linea, porque una coma sobra en algun sitio concreto
    no valida       con el campo, y `extra=forbid` hace que un nombre mal
                    escrito salga aqui en vez de convertirse en un defecto

EL VALOR POR DEFECTO ES EL FICHERO DEL REPOSITORIO
----------------------------------------------------
`cargar_brief()` sin argumentos lee `config/brief.json`. Eso hace que los dos
ficheros que el proyecto trae pasen por el mismo codigo que los valida, y que
una prueba pueda comprobarlos: si alguien rompe el brief de ejemplo, se entera
al lanzar la suite y no al lanzar la tanda.
"""

import json
import pathlib

from pydantic import ValidationError

from app.commons.configuracion.esquemas import (
    BriefDeObra,
    ConfiguracionDelSistema,
    ListasVetadas,
)

# `backend/config/`. Sube desde `app/commons/configuracion/carga.py`.
RAIZ = pathlib.Path(__file__).resolve().parents[3]
CONFIG = RAIZ / "config"
SISTEMA_POR_DEFECTO = CONFIG / "sistema.json"
BRIEF_POR_DEFECTO = CONFIG / "brief.json"
VETADAS_POR_DEFECTO = CONFIG / "vetadas.json"


class ConfiguracionInvalida(Exception):
    """Una sola excepcion para los tres modos, con el fichero siempre dentro."""


def _leer_json(ruta, que):
    p = pathlib.Path(ruta)
    if not p.exists():
        raise ConfiguracionInvalida(
            "la configuracion de {0} no existe en {1}. Es un fichero de "
            "configuracion, no un valor por defecto: sin el no se sabe que "
            "obra hay que escribir ni con que".format(que, p))
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise ConfiguracionInvalida(
            "{0} no es JSON valido ({1}), en la linea {2} de {3}".format(
                p.name, e.msg, e.lineno, p)) from e


def _validar(modelo, datos, ruta, que):
    try:
        return modelo.model_validate(datos)
    except ValidationError as e:
        detalles = "; ".join(
            "{0}: {1}".format(".".join(str(x) for x in err["loc"]) or "(raiz)",
                              err["msg"])
            for err in e.errors())
        raise ConfiguracionInvalida(
            "la configuracion de {0} en {1} no es valida: {2}".format(
                que, ruta, detalles)) from e


def cargar_sistema(ruta=None) -> ConfiguracionDelSistema:
    """Lo que cambia con la maquina: modelos, topes, presupuesto, base."""
    ruta = ruta or SISTEMA_POR_DEFECTO
    return _validar(ConfiguracionDelSistema, _leer_json(ruta, "sistema"),
                    ruta, "sistema")


def cargar_brief(ruta=None) -> BriefDeObra:
    """Lo que cambia con la novela: premisa, forma, estilo."""
    ruta = ruta or BRIEF_POR_DEFECTO
    return _validar(BriefDeObra, _leer_json(ruta, "la obra"), ruta, "la obra")


def cargar_vetadas(ruta=None) -> ListasVetadas:
    """Las listas global y por franja de edad (`SPEC-25` `RF-15`)."""
    ruta = ruta or VETADAS_POR_DEFECTO
    return _validar(ListasVetadas, _leer_json(ruta, "las palabras vetadas"),
                    ruta, "las palabras vetadas")


def comprobar_forma(brief, capitulos: int, escenas_por_capitulo: int):
    """El plan concreto tiene que caber en la forma que el brief declara.

    El brief dice **cuantas** piezas tiene la obra; la escaleta trae **cuales**
    son. Si los dos pueden decir cosas distintas, la forma vuelve a estar en dos
    sitios y uno de ellos acabara mintiendo — que es lo que `F-53` costo
    descubrir, solo que entonces ni siquiera habia un sitio donde mirarla.

    Se comprueba **al arrancar**. Descubrirlo en la escena treinta y siete
    cuesta una tanda entera, y el fallo que sale ahi no menciona el brief.
    """
    f = brief.forma
    if f.capitulos != capitulos:
        raise ConfiguracionInvalida(
            "el brief declara {0} capitulos y el plan trae {1}. La forma la "
            "manda el brief: o se corrige el fichero, o se corrige el "
            "plan".format(f.capitulos, capitulos))
    if f.escenas_por_capitulo != escenas_por_capitulo:
        raise ConfiguracionInvalida(
            "el brief declara {0} escenas por capitulo y el plan trae {1}. "
            "Con esa diferencia, `forma.escenas_totales` miente y cualquier "
            "proyeccion de coste hecha sobre el brief sale mal".format(
                f.escenas_por_capitulo, escenas_por_capitulo))
    return None
