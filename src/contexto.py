"""Ensamblador de ventanas de contexto (spec seccion 2.2 y 2.4).

Cada agente recibe SOLO lo que necesita. No es tacaneria: una ventana mas
pequena es mas barata y ademas mas precisa, porque el modelo no se distrae con
material irrelevante.

La tabla que implementa este modulo:

    Arquitecto   configuracion de novela y estructura. Nada mas.
    Escritor     biblia, hechos vigentes, resumenes 1..N-2, texto completo
                 SOLO del capitulo N-1, y los problemas del intento anterior.
    Continuidad  biblia completa + texto del capitulo.
    Genero       convenciones del genero + posicion en el arco + texto.
    Estilo       texto + memoria de estilo.

La regla del capitulo N-1 es la que hace que la ventana del escritor se
mantenga aproximadamente constante sea cual sea N: el anterior entra entero
porque hace falta la voz y la transicion inmediata, y los demas entran
comprimidos como resumen.

Este modulo no hace llamadas de red ni lee archivos: recibe los datos ya
cargados y devuelve texto.
"""

from __future__ import annotations

import json
import logging

from src import biblia as modulo_biblia

registro = logging.getLogger(__name__)

# Aproximacion de tokens. Sin el tokenizador del proveedor no hay cuenta exacta,
# y no la necesitamos: esto solo decide cuando recortar, y para eso basta una
# estimacion conservadora. En espanol, cerca de 4 caracteres por token.
CARACTERES_POR_TOKEN = 4


class Ventana:
    """El resultado de ensamblar una ventana.

    Atributos:
        texto     el mensaje de usuario que se le manda al modelo;
        tokens    tamano estimado;
        recortes  lista de recortes aplicados, en espanol, para el informe.
    """

    def __init__(self, texto, tokens, recortes=None):
        self.texto = texto
        self.tokens = tokens
        self.recortes = recortes or []

    def __repr__(self):
        return "Ventana(tokens={0}, recortes={1})".format(self.tokens, self.recortes)


def estimar_tokens(texto):
    """Estimacion del tamano en tokens de un texto."""
    return len(texto or "") // CARACTERES_POR_TOKEN


def _bloque(etiqueta, contenido):
    """Un bloque con el nombre que esperan los prompts de `prompts/`."""
    return "{0}:\n{1}".format(etiqueta, contenido)


def _json(datos):
    return json.dumps(datos, indent=2, ensure_ascii=False)


def _montar(bloques):
    return "\n\n".join(bloque for bloque in bloques if bloque)


def _finalizar(nombre, texto, config, recortes=None):
    """Mide la ventana, la registra si toca y la devuelve."""
    ventana = Ventana(texto, estimar_tokens(texto), recortes)
    if config.get("runtime", {}).get("registrar_tamano_contexto", False):
        registro.info(
            "Ventana %s: %d tokens estimados (%d caracteres)%s",
            nombre,
            ventana.tokens,
            len(texto),
            "; recortes: " + "; ".join(ventana.recortes) if ventana.recortes else "",
        )
    return ventana


# ---------------------------------------------------------------------------
# Arquitecto
# ---------------------------------------------------------------------------


def ventana_arquitecto(config):
    """Configuracion de novela y estructura. Es la primera llamada: nada mas.

    Los valores concretos (genero, numero de capitulos, rango de palabras) van
    aqui, en el mensaje de usuario, y no en el prompt de sistema: asi el prompt
    sirve para cualquier novela.
    """
    novela = config.get("novela", {})
    estructura = config.get("estructura", {})

    parametros = {
        "genero": novela.get("genero"),
        "tono": novela.get("tono"),
        "punto_de_vista": novela.get("punto_de_vista"),
        "idioma": novela.get("idioma"),
        "num_capitulos": estructura.get("num_capitulos"),
        "palabras_min": estructura.get("palabras_min"),
        "palabras_max": estructura.get("palabras_max"),
    }
    if novela.get("titulo"):
        parametros["titulo"] = novela["titulo"]
    if novela.get("semilla_tematica"):
        parametros["semilla_tematica"] = novela["semilla_tematica"]

    return _finalizar(
        "arquitecto", _bloque("CONFIGURACION", _json(parametros)), config
    )


# ---------------------------------------------------------------------------
# Escritor
# ---------------------------------------------------------------------------


def _biblia_para_escritor(biblia, hechos):
    """La parte de la biblia que necesita el escritor.

    Entran personajes, ambientacion y hechos vigentes. NO entra el outline
    completo de otros capitulos en forma de sinopsis larga ni la timeline
    entera: el capitulo que toca viaja en su propio bloque.
    """
    return {
        "titulo": biblia.get("titulo"),
        "premisa": biblia.get("premisa"),
        "conflicto_central": biblia.get("conflicto_central"),
        "ambientacion": biblia.get("ambientacion", {}),
        "personajes": biblia.get("personajes", []),
        "hechos_vigentes": hechos,
    }


def _resumenes_previos(resumenes, capitulo):
    """Resumenes de los capitulos 1..N-2, en orden.

    El N-1 no entra aqui porque entra completo en su propio bloque.
    """
    lineas = []
    for numero in sorted(resumenes):
        if numero <= capitulo - 2:
            lineas.append("Capitulo {0}: {1}".format(numero, resumenes[numero]))
    return "\n".join(lineas)


def _acortar(texto, frases=1):
    """Se queda con las primeras `frases` frases de un texto."""
    trozos = texto.replace("\n", " ").split(". ")
    return ". ".join(trozos[:frases]).strip().rstrip(".") + "."


def ventana_escritor(config, biblia, capitulo, resumenes=None, texto_anterior=None,
                     problemas=None):
    """Monta la ventana del escritor y aplica el presupuesto de contexto.

    Si la ventana supera `contexto.max_tokens_contexto`, se recorta en el orden
    de `contexto.orden_recorte`, por defecto:

        1. hechos_efimeros   fuera los efimeros; los PERMANENTES nunca se tocan;
        2. resumenes         cada resumen se queda en su primera frase;
        3. capitulo_anterior se sustituye el texto completo por su resumen.

    Todo recorte se registra en `ventana.recortes` para que aparezca en el
    informe: si en el capitulo 12 hay recortes que no habia en el 3, la
    compactacion no esta funcionando.
    """
    resumenes = resumenes or {}
    problemas = problemas or []
    ajustes = config.get("contexto", {})
    maximo = ajustes.get("max_tokens_contexto", 100000)
    ventana_hechos = ajustes.get("ventana_hechos", 3)
    orden_recorte = ajustes.get(
        "orden_recorte", ["hechos_efimeros", "resumenes", "capitulo_anterior"]
    )

    novela = config.get("novela", {})
    estructura = config.get("estructura", {})
    entrada = modulo_biblia.entrada_outline(biblia, capitulo) or {}

    parametros = {
        "genero": novela.get("genero"),
        "tono": novela.get("tono"),
        "punto_de_vista": novela.get("punto_de_vista"),
        "idioma": novela.get("idioma"),
        "capitulo": capitulo,
        "palabras_min": estructura.get("palabras_min"),
        "palabras_max": estructura.get("palabras_max"),
    }

    hechos = modulo_biblia.hechos_vigentes(biblia, capitulo, ventana_hechos)
    resumenes_texto = _resumenes_previos(resumenes, capitulo)
    anterior = texto_anterior
    recortes = []

    def construir():
        bloques = [
            _bloque("PARAMETROS", _json(parametros)),
            _bloque("BIBLIA", _json(_biblia_para_escritor(biblia, hechos))),
            _bloque("OUTLINE_CAPITULO", _json(entrada)),
        ]
        if resumenes_texto:
            bloques.append(_bloque("RESUMENES_ANTERIORES", resumenes_texto))
        if anterior:
            bloques.append(_bloque("CAPITULO_ANTERIOR", anterior))
        if problemas:
            bloques.append(
                _bloque("PROBLEMAS", "\n".join("- " + str(p) for p in problemas))
            )
        return _montar(bloques)

    texto = construir()

    for paso in orden_recorte:
        if estimar_tokens(texto) <= maximo:
            break

        if paso == "hechos_efimeros":
            permanentes = modulo_biblia.hechos_permanentes(biblia)
            if len(permanentes) < len(hechos):
                hechos = permanentes
                recortes.append(
                    "hechos efimeros retirados; los permanentes se conservan"
                )
        elif paso == "resumenes":
            if resumenes_texto:
                resumenes_texto = "\n".join(
                    _acortar(linea) for linea in resumenes_texto.splitlines()
                )
                recortes.append("resumenes acortados a una frase")
        elif paso == "capitulo_anterior":
            if anterior:
                resumen_previo = resumenes.get(capitulo - 1)
                anterior = None
                if resumen_previo:
                    resumenes_texto = (
                        resumenes_texto + "\n" if resumenes_texto else ""
                    ) + "Capitulo {0}: {1}".format(capitulo - 1, resumen_previo)
                recortes.append(
                    "texto completo del capitulo anterior sustituido por su resumen"
                )

        texto = construir()

    if estimar_tokens(texto) > maximo:
        recortes.append(
            "la ventana sigue por encima del presupuesto tras todos los recortes"
        )

    return _finalizar("escritor cap {0}".format(capitulo), texto, config, recortes)


# ---------------------------------------------------------------------------
# Validadores
# ---------------------------------------------------------------------------


def ventana_continuidad(config, biblia, capitulo, texto_capitulo):
    """Biblia completa + texto del capitulo. Nada mas.

    No entran los capitulos anteriores, ni las convenciones de genero, ni la
    memoria de estilo: continuidad audita hechos, no calidad.
    """
    bloques = [
        _bloque("BIBLIA", _json(biblia)),
        _bloque("CAPITULO_NUMERO", str(capitulo)),
        _bloque("CAPÍTULO", texto_capitulo),
    ]
    return _finalizar(
        "continuidad cap {0}".format(capitulo), _montar(bloques), config
    )


def posicion_en_el_arco(capitulo, num_capitulos):
    """Describe donde cae el capitulo dentro del arco, sin nombrar las fases.

    Los nombres de las fases de cada genero viven en
    `prompts/referencias/<genero>.md`, que es lo que lee el validador. Aqui
    solo se calcula la aritmetica: en que cuarto del arco estamos y cuantos
    capitulos quedan.
    """
    if not num_capitulos or num_capitulos < 1:
        return "capitulo {0}".format(capitulo)
    fase = min(4, ((capitulo - 1) * 4) // num_capitulos + 1)
    return (
        "capitulo {0} de {1}; fase {2} de 4 del arco; quedan {3} capitulos "
        "despues de este".format(capitulo, num_capitulos, fase, num_capitulos - capitulo)
    )


def ventana_genero(config, convenciones, capitulo, texto_capitulo):
    """Convenciones del genero + posicion en el arco + texto del capitulo.

    `convenciones` es el contenido de prompts/referencias/<genero>.md, que lo
    lee y lo pasa el orquestador: este modulo no toca el disco.
    """
    num_capitulos = config.get("estructura", {}).get("num_capitulos")
    bloques = [
        _bloque("CONVENCIONES", convenciones),
        _bloque("POSICION_ARCO", posicion_en_el_arco(capitulo, num_capitulos)),
        _bloque("CAPITULO_NUMERO", str(capitulo)),
        _bloque("CAPÍTULO", texto_capitulo),
    ]
    return _finalizar("genero cap {0}".format(capitulo), _montar(bloques), config)


def ventana_estilo(config, capitulo, texto_capitulo, memoria_estilo=None):
    """Texto del capitulo + memoria de estilo. Ni biblia ni outline.

    La memoria de estilo es lo que permite ver lo que no se ve leyendo un
    capitulo suelto: una imagen que era buena la primera vez y ya va por su
    cuarta aparicion.
    """
    memoria = memoria_estilo or {"frases_recurrentes": [], "muletillas": []}
    bloques = [
        _bloque("CAPITULO_NUMERO", str(capitulo)),
        _bloque("CAPÍTULO", texto_capitulo),
        _bloque("MEMORIA_ESTILO", _json(memoria)),
    ]
    return _finalizar("estilo cap {0}".format(capitulo), _montar(bloques), config)
