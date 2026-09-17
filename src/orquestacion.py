"""Maquina de estados de la generacion, con todo el estado en archivos.

QUE ES ESTO Y QUE NO ES
-----------------------
Esto NO es el orquestador. El orquestador es la sesion de Claude Code: es quien
delega en los subagentes, o sea, quien habla con los modelos. Este modulo es su
cuaderno: le dice en que punto de la novela esta, que le toca hacer ahora, y
recoge lo que el subagente devuelve.

El reparto es deliberado y se puede resumir en una frase: **el que razona no
recuerda, y el que recuerda no razona.**

    Claude Code (razona)     decide, redacta, juzga. No guarda nada.
    src/orquestacion.py      guarda, cuenta, decide el siguiente paso. No
    (recuerda)               razona ni llama a ningun modelo.

POR QUE EL ESTADO VIVE EN ARCHIVOS Y NO EN LA CONVERSACION
----------------------------------------------------------
Una novela de doce capitulos son unas cuarenta delegaciones y varios cientos de
miles de palabras entre intentos, veredictos y reescrituras. Eso no cabe en la
ventana de una sesion, y aunque cupiera seria una mala idea: al compactarse la
conversacion, lo primero que se pierde son los detalles, que es justo donde
viven "el capitulo 7 va por el intento 4" y "el validador de estilo se quejo de
la metafora del reloj".

Con el estado en disco, la sesion no necesita recordar nada. Puede cerrarse en
mitad del capitulo 7 y otra sesion distinta, dias despues, continuar con
`python -m src.orquestacion estado`. Esa propiedad es la que hace viable el
proyecto entero, y es la razon de que este modulo exista en vez de que la sesion
lleve la cuenta de cabeza.

COMO SE USA
-----------
El ciclo, desde la sesion orquestadora, es siempre el mismo:

    1. python -m src.orquestacion estado     -> que toca ahora
    2. python -m src.orquestacion ventana X  -> el mensaje que hay que delegar
    3. delegar en el subagente X             <- esto lo hace Claude Code
    4. python -m src.orquestacion registrar-... -> guardar lo que devolvio

y vuelta al 1. Ningun comando de este modulo sale a la red ni delega en nadie.
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path

from src import biblia as modulo_biblia
from src import contexto
from src import estado as modulo_estado
from src import puntuacion
from src.config import RAIZ_PROYECTO, ErrorDeConfiguracion, cargar_config

# Version del CLI a partir de la cual `omitClaudeMd` hace efecto. Por debajo de
# esta, el campo se ignora EN SILENCIO y los validadores reciben CLAUDE.md, con
# lo que el aislamiento del spec 2.2 deja de cumplirse sin que nada avise.
# El porque esta en DECISIONES.md, hallazgo 3.
VERSION_MINIMA_CLAUDE = (2, 1, 271)

SUBAGENTES = ("arquitecto", "escritor", "continuidad", "genero", "estilo")

# Roles que admite el comando `ventana`.
ROLES_VENTANA = ("arquitecto", "escritor") + puntuacion.VALIDADORES


class ErrorDeOrquestacion(Exception):
    """Algo impide continuar. El mensaje dice siempre que hay que arreglar."""


# ---------------------------------------------------------------------------
# Rutas de salida/
# ---------------------------------------------------------------------------


def directorio_salida(config):
    """Carpeta de trabajo, resuelta desde la raiz del proyecto.

    Se resuelve contra la raiz y no contra el directorio actual para que los
    comandos funcionen igual se lancen desde donde se lancen.
    """
    bruto = config.get("runtime", {}).get("directorio_salida", "./salida")
    ruta = Path(bruto)
    if not ruta.is_absolute():
        ruta = RAIZ_PROYECTO / ruta
    return ruta.resolve()


def _tmp(salida):
    return Path(salida) / ".tmp"


def ruta_capitulo(salida, numero):
    return Path(salida) / "capitulos" / "cap-{0:02d}.md".format(numero)


def ruta_resumen(salida, numero):
    return Path(salida) / "resumenes" / "cap-{0:02d}.md".format(numero)


def ruta_memoria_estilo(salida):
    return Path(salida) / "memoria-estilo.json"


def ruta_intento_texto(salida, capitulo, intento):
    return _tmp(salida) / "cap-{0:02d}-intento-{1}.md".format(capitulo, intento)


def ruta_intento_datos(salida, capitulo, intento):
    return _tmp(salida) / "cap-{0:02d}-intento-{1}.json".format(capitulo, intento)


def preparar_directorios(salida):
    """Crea el arbol de salida/. Idempotente."""
    for sub in ("", "capitulos", "resumenes", ".tmp"):
        (Path(salida) / sub).mkdir(parents=True, exist_ok=True)
    return Path(salida)


# ---------------------------------------------------------------------------
# Lectura y escritura de piezas sueltas
# ---------------------------------------------------------------------------


def _escribir(ruta, texto):
    """Escritura atomica: primero a un temporal, luego renombrado.

    Igual que en `src/estado.py`, y por el mismo motivo: un proceso que muere a
    media escritura no puede dejar un capitulo truncado en disco haciendose
    pasar por un capitulo entero.
    """
    ruta = Path(ruta)
    ruta.parent.mkdir(parents=True, exist_ok=True)
    temporal = ruta.with_suffix(ruta.suffix + ".tmp")
    temporal.write_text(texto, encoding="utf-8")
    temporal.replace(ruta)
    return ruta


def _leer_archivo(ruta, que_es):
    ruta = Path(ruta)
    if not ruta.is_file():
        raise ErrorDeOrquestacion(
            "No encuentro {0} en: {1}.\n"
            "Arreglo: guarda primero la respuesta del subagente en un archivo y "
            "pasa su ruta con --archivo.".format(que_es, ruta)
        )
    texto = ruta.read_text(encoding="utf-8")
    if not texto.strip():
        raise ErrorDeOrquestacion(
            "El archivo {0} esta vacio. El subagente no devolvio nada, o se "
            "guardo mal.".format(ruta)
        )
    return texto


def cargar_memoria_estilo(salida):
    """Memoria de estilo del spec 7.4, o una vacia si todavia no existe."""
    ruta = ruta_memoria_estilo(salida)
    if not ruta.is_file():
        return {"frases_recurrentes": [], "muletillas": []}
    try:
        datos = json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        # Una memoria de estilo corrupta no puede detener una novela (regla 1).
        # Se empieza de cero: se pierde la deteccion de repeticiones entre
        # capitulos, que es mucho menos grave que abortar.
        return {"frases_recurrentes": [], "muletillas": []}
    datos.setdefault("frases_recurrentes", [])
    datos.setdefault("muletillas", [])
    return datos


def actualizar_memoria_estilo(salida, capitulo, frases_nuevas):
    """Suma las frases que el validador de estilo manda vigilar.

    Si la frase ya estaba, se le suma una aparicion y se anota el capitulo. Ese
    contador es toda la memoria que tiene el harness sobre repeticiones ENTRE
    capitulos: el validador de estilo solo ve un capitulo cada vez, asi que sin
    esto no habria forma de detectar la imagen que se usa por cuarta vez.
    """
    memoria = cargar_memoria_estilo(salida)
    indice = {
        entrada.get("frase"): entrada
        for entrada in memoria["frases_recurrentes"]
        if isinstance(entrada, dict)
    }
    for frase in frases_nuevas or []:
        frase = str(frase).strip()
        if not frase:
            continue
        entrada = indice.get(frase)
        if entrada is None:
            entrada = {"frase": frase, "apariciones": 1, "capitulos": [capitulo]}
            memoria["frases_recurrentes"].append(entrada)
            indice[frase] = entrada
        elif capitulo not in entrada.get("capitulos", []):
            entrada["apariciones"] = entrada.get("apariciones", 0) + 1
            entrada.setdefault("capitulos", []).append(capitulo)
    _escribir(
        ruta_memoria_estilo(salida),
        json.dumps(memoria, indent=2, ensure_ascii=False) + "\n",
    )
    return memoria


def cargar_resumenes(salida):
    """Diccionario {numero_de_capitulo: resumen}, leido de salida/resumenes/."""
    resumenes = {}
    carpeta = Path(salida) / "resumenes"
    if not carpeta.is_dir():
        return resumenes
    for archivo in sorted(carpeta.glob("cap-*.md")):
        coincidencia = re.search(r"cap-(\d+)\.md$", archivo.name)
        if not coincidencia:
            continue
        resumenes[int(coincidencia.group(1))] = archivo.read_text(
            encoding="utf-8"
        ).strip()
    return resumenes


def texto_capitulo_anterior(salida, capitulo):
    """Texto completo del capitulo N-1, o None si no hay.

    Solo el N-1: es la regla que mantiene la ventana del escritor
    aproximadamente constante sea cual sea N (`EJECUCION.md` 3.5a).
    """
    if capitulo <= 1:
        return None
    ruta = ruta_capitulo(salida, capitulo - 1)
    return ruta.read_text(encoding="utf-8") if ruta.is_file() else None


# ---------------------------------------------------------------------------
# La escalera de modelos
# ---------------------------------------------------------------------------


def escalera(config):
    return list(config.get("modelos", {}).get("escalera_escritor", ["haiku"]))


def intentos_por_modelo(config):
    return int(config.get("modelos", {}).get("intentos_por_modelo", 2))


def escalon_de_intento(config, escalon_inicial, intento):
    """En que escalon de la escalera cae el intento numero `intento` (1..N).

    Los intentos se agrupan de `intentos_por_modelo` en `intentos_por_modelo`.
    El ultimo escalon absorbe cualquier intento de mas, por si alguien sube
    `intentos_por_modelo` a mitad de generacion.
    """
    pasos = escalera(config)
    avance = (max(1, intento) - 1) // max(1, intentos_por_modelo(config))
    return min(escalon_inicial + avance, len(pasos) - 1)


def modelo_de_escalon(config, escalon):
    pasos = escalera(config)
    return pasos[min(max(0, escalon), len(pasos) - 1)]


def intentos_maximos(config, escalon_inicial):
    """Cuantos intentos quedan desde el escalon en el que arranca el capitulo.

    Con la escalera completa (3 modelos x 2 intentos) son 6. Si el capitulo
    arranca en el escalon 1 porque `mantener_voz_ganadora` conservo el modelo
    que resolvio el anterior, quedan 4: la escalera empieza donde se quedo, no
    vuelve al principio.
    """
    restantes = len(escalera(config)) - escalon_inicial
    return max(1, restantes) * intentos_por_modelo(config)


# ---------------------------------------------------------------------------
# Los intentos en disco
# ---------------------------------------------------------------------------


def cargar_intento(salida, capitulo, numero):
    ruta = ruta_intento_datos(salida, capitulo, numero)
    if not ruta.is_file():
        return None
    try:
        return json.loads(ruta.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise ErrorDeOrquestacion(
            "{0} no es JSON valido: {1}\n"
            "Arreglo: borra ese archivo. Perderas los veredictos de ese "
            "intento, no el capitulo.".format(ruta, error)
        ) from error


def guardar_intento(salida, capitulo, datos):
    _escribir(
        ruta_intento_datos(salida, capitulo, datos["intento"]),
        json.dumps(datos, indent=2, ensure_ascii=False) + "\n",
    )
    return datos


def intentos_de_capitulo(salida, capitulo):
    """Todos los intentos registrados de un capitulo, ordenados."""
    intentos = []
    numero = 1
    while True:
        datos = cargar_intento(salida, capitulo, numero)
        if datos is None:
            break
        intentos.append(datos)
        numero += 1
    return intentos


# ---------------------------------------------------------------------------
# Estado extendido
# ---------------------------------------------------------------------------

# Dos campos que el spec 7.3 no contempla y que la arquitectura de subagentes
# necesita. Se anaden aqui y no en `src/estado.py` para que un estado.json
# antiguo (sin ellos) siga cargando: `estado.cargar` solo exige las claves del
# spec, y estas se rellenan al vuelo.
CAMPOS_EXTRA = {
    # Contador de la regla 6: el dinero ya no se puede medir, las delegaciones si.
    "delegaciones": 0,
    # Escalon de la escalera en el que ARRANCA el capitulo en curso. Es lo que
    # implementa `mantener_voz_ganadora`: si el capitulo 3 lo resolvio `sonnet`,
    # el capitulo 4 empieza en `sonnet` y no vuelve a `haiku`.
    "escalon_inicial": 0,
}


def _completar(estado):
    for clave, valor in CAMPOS_EXTRA.items():
        estado.setdefault(clave, valor)
    return estado


def cargar_estado(config, salida):
    if not modulo_estado.existe(salida):
        raise ErrorDeOrquestacion(
            "No hay ninguna generacion en marcha (falta {0}).\n"
            "Arreglo: lanza primero `python -m src.orquestacion "
            "iniciar`.".format(modulo_estado.ruta(salida))
        )
    return _completar(modulo_estado.cargar(salida))


def contar_delegacion(estado, salida, cuantas=1):
    """Suma delegaciones al contador y avisa si se pasa del limite."""
    estado["delegaciones"] = estado.get("delegaciones", 0) + cuantas
    modulo_estado.guardar(estado, salida)
    return estado


def limite_delegaciones(config):
    return int(config.get("limites", {}).get("delegaciones_max_totales", 300))


def delegaciones_agotadas(config, estado):
    if not config.get("limites", {}).get("abortar_si_supera_delegaciones", True):
        return False
    return estado.get("delegaciones", 0) >= limite_delegaciones(config)


# ---------------------------------------------------------------------------
# La maquina de estados
# ---------------------------------------------------------------------------


def siguiente_paso(config, salida):
    """Que toca hacer ahora. Es el corazon del modulo.

    Devuelve un diccionario con `paso` y lo que haga falta para ejecutarlo. La
    decision se toma SIEMPRE mirando el disco, nunca un valor recordado: si
    existe biblia.json, el arquitecto ya corrio; si existe el intento 3 con sus
    tres veredictos, toca resolver. Asi el resultado es el mismo lo pregunte
    quien lo pregunte y cuando lo pregunte.
    """
    if not modulo_estado.existe(salida):
        return {"paso": "iniciar"}

    estado = _completar(modulo_estado.cargar(salida))
    num_capitulos = config.get("estructura", {}).get("num_capitulos", 1)

    if delegaciones_agotadas(config, estado):
        return {
            "paso": "limite",
            "delegaciones": estado.get("delegaciones", 0),
            "maximo": limite_delegaciones(config),
        }

    if not modulo_biblia.existe(salida):
        return {"paso": "arquitecto", "modelo": config["modelos"]["arquitecto"]}

    pendientes = modulo_estado.capitulos_pendientes(estado, num_capitulos)
    if not pendientes:
        return {"paso": "ensamblar", "capitulos": num_capitulos}

    capitulo = pendientes[0]
    intentos = intentos_de_capitulo(salida, capitulo)
    escalon_inicial = estado.get("escalon_inicial", 0)
    maximo = intentos_maximos(config, escalon_inicial)

    ultimo = intentos[-1] if intentos else None

    # Un intento resuelto que no aprobo el capitulo significa "toca reescribir".
    if ultimo is None or ultimo.get("resuelto"):
        siguiente = len(intentos) + 1
        escalon = escalon_de_intento(config, escalon_inicial, siguiente)
        return {
            "paso": "escribir",
            "capitulo": capitulo,
            "intento": siguiente,
            "de": maximo,
            "escalon": escalon,
            "modelo": modelo_de_escalon(config, escalon),
        }

    emitidos = {v.get("validador") for v in ultimo.get("veredictos", [])}
    faltan = [v for v in puntuacion.VALIDADORES if v not in emitidos]
    if faltan:
        return {
            "paso": "validar",
            "capitulo": capitulo,
            "intento": ultimo["intento"],
            "faltan": faltan,
            "modelo": config["modelos"]["validadores"],
        }

    return {"paso": "resolver", "capitulo": capitulo, "intento": ultimo["intento"]}


# ---------------------------------------------------------------------------
# Presentacion del siguiente paso
# ---------------------------------------------------------------------------

_INSTRUCCIONES = {
    "iniciar": [
        "No hay ninguna generacion en marcha.",
        "  python -m src.orquestacion iniciar",
    ],
    "limite": [
        "LIMITE DE DELEGACIONES ALCANZADO. Parada ordenada (regla 6).",
        "  Sube limites.delegaciones_max_totales en config.json, o revisa por",
        "  que se han gastado tantas: casi siempre es un capitulo atascado.",
    ],
    "ensamblar": [
        "Todos los capitulos estan hechos. Toca ensamblar el manuscrito.",
        "  (etapa pendiente: src/ensamblador.py)",
    ],
}


def _lineas_del_paso(paso, salida):
    """Convierte el diccionario de `siguiente_paso` en instrucciones legibles.

    El destinatario de este texto es la sesion de Claude Code que orquesta, asi
    que cada paso dice literalmente los tres movimientos: que ventana pedir, en
    que subagente delegar y con que modelo, y con que comando registrar la
    respuesta. Que no haya que deducir nada es la gracia.
    """
    nombre = paso["paso"]
    if nombre in _INSTRUCCIONES:
        return _INSTRUCCIONES[nombre]

    if nombre == "arquitecto":
        return [
            "Toca el arquitecto: hay que generar la biblia de la novela.",
            "  1. python -m src.orquestacion ventana arquitecto",
            "  2. Delegar en el subagente `arquitecto` con model={0}".format(
                paso["modelo"]
            ),
            "  3. Guardar la respuesta cruda en un archivo y registrarla:",
            "     python -m src.orquestacion registrar-biblia --archivo <ruta>",
        ]

    if nombre == "escribir":
        return [
            "Toca escribir el capitulo {0} (intento {1} de {2}, escalon {3}).".format(
                paso["capitulo"], paso["intento"], paso["de"], paso["escalon"]
            ),
            "  1. python -m src.orquestacion ventana escritor --capitulo {0}".format(
                paso["capitulo"]
            ),
            "  2. Delegar en el subagente `escritor` con model={0}".format(
                paso["modelo"]
            ),
            "  3. Guardar el texto en un archivo y registrarlo:",
            "     python -m src.orquestacion registrar-intento --capitulo {0} "
            "--archivo <ruta>".format(paso["capitulo"]),
        ]

    if nombre == "validar":
        lineas = [
            "Toca validar el capitulo {0}, intento {1}.".format(
                paso["capitulo"], paso["intento"]
            ),
            "  Faltan los veredictos de: {0}".format(", ".join(paso["faltan"])),
            "  1. Pedir las ventanas que falten:",
        ]
        for validador in paso["faltan"]:
            lineas.append(
                "     python -m src.orquestacion ventana {0} --capitulo {1}".format(
                    validador, paso["capitulo"]
                )
            )
        lineas += [
            "  2. Delegar en los {0} subagentes EN UN SOLO MENSAJE, con "
            "model={1}.".format(len(paso["faltan"]), paso["modelo"]),
            "     Lanzarlos en mensajes distintos los pone en fila y pierde el",
            "     paralelismo, que es gratis y es la unica razon de que validar",
            "     no triplique el tiempo de cada intento.",
            "  3. Guardar cada respuesta cruda y registrarla:",
            "     python -m src.orquestacion registrar-veredicto --capitulo {0} "
            "--validador <nombre> --archivo <ruta>".format(paso["capitulo"]),
        ]
        return lineas

    if nombre == "resolver":
        return [
            "El capitulo {0} tiene sus tres veredictos del intento {1}.".format(
                paso["capitulo"], paso["intento"]
            ),
            "  python -m src.orquestacion resolver --capitulo {0}".format(
                paso["capitulo"]
            ),
        ]

    return ["Paso desconocido: {0}".format(nombre)]


def informe_de_estado(config, salida, escribir=print):
    """Imprime el estado completo y el siguiente paso."""
    estructura = config.get("estructura", {})
    novela = config.get("novela", {})
    paso = siguiente_paso(config, salida)

    escribir("== Estado de la generacion ==")
    escribir(
        "Genero: {0} | Capitulos: {1} | Palabras por capitulo: {2}-{3}".format(
            novela.get("genero"),
            estructura.get("num_capitulos"),
            estructura.get("palabras_min"),
            estructura.get("palabras_max"),
        )
    )
    escribir("Salida: {0}".format(salida))

    if modulo_estado.existe(salida):
        estado = _completar(modulo_estado.cargar(salida))
        escribir(
            modulo_estado.resumen_legible(estado, estructura.get("num_capitulos"))
        )
        escribir(
            "Delegaciones gastadas: {0} de {1}".format(
                estado.get("delegaciones", 0), limite_delegaciones(config)
            )
        )
        escribir("Biblia: {0}".format(
            "si" if modulo_biblia.existe(salida) else "todavia no"
        ))
    else:
        escribir("Sin estado: no se ha iniciado ninguna generacion.")

    escribir("")
    escribir("SIGUIENTE PASO: {0}".format(paso["paso"]))
    for linea in _lineas_del_paso(paso, salida):
        escribir(linea)
    return paso


# ---------------------------------------------------------------------------
# Comandos
# ---------------------------------------------------------------------------


def parsear_version(texto):
    """Saca (major, minor, patch) de la salida de `claude --version`, o None.

    Separado de la ejecucion del proceso para poder probarlo sin lanzar nada.
    """
    coincidencia = re.search(r"(\d+)\.(\d+)\.(\d+)", texto or "")
    if not coincidencia:
        return None
    return tuple(int(parte) for parte in coincidencia.groups())


def _version_de_claude():
    """(major, minor, patch) del CLI instalado, o None si no se puede saber.

    Se ejecuta `claude --version`, que no es una llamada de red: es un proceso
    local que pregunta por un numero.

    En Windows el CLI se instala como `claude.CMD`, y un `.cmd` no lo puede
    arrancar CreateProcess directamente: hace falta el interprete de ordenes.
    Sin este rodeo la comprobacion fallaba siempre en Windows y el comando
    `comprobar` decia "no esta en el PATH" de un CLI que si estaba, que es
    justo el tipo de falso negativo que este modulo intenta evitar.

    Si de verdad no se puede averiguar, devuelve None y quien llama lo dice, en
    vez de inventarse un resultado tranquilizador.
    """
    ejecutable = shutil.which("claude")
    if ejecutable is None:
        return None
    orden = [ejecutable, "--version"]
    if ejecutable.lower().endswith((".cmd", ".bat")):
        orden = ["cmd", "/c"] + orden
    try:
        completado = subprocess.run(
            orden, capture_output=True, text=True, timeout=60
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return parsear_version(completado.stdout)


def cmd_comprobar(config, salida, escribir=print):
    """Verifica el entorno antes de gastar la primera delegacion (flujo 3.2)."""
    problemas = []

    version = _version_de_claude()
    if version is None:
        escribir(
            "? Claude Code: no he podido leer la version (`claude` no esta en "
            "el PATH). Comprueba a mano que es {0} o superior.".format(
                ".".join(str(n) for n in VERSION_MINIMA_CLAUDE)
            )
        )
    elif version < VERSION_MINIMA_CLAUDE:
        problemas.append(
            "Claude Code {0} es anterior a la {1}: `omitClaudeMd` se ignora sin "
            "avisar y los validadores reciben CLAUDE.md. Actualiza el CLI.".format(
                ".".join(str(n) for n in version),
                ".".join(str(n) for n in VERSION_MINIMA_CLAUDE),
            )
        )
    else:
        escribir("OK Claude Code {0}".format(".".join(str(n) for n in version)))

    # La configuracion ya viene validada por cargar_config: si llegamos aqui, pasa.
    escribir(
        "OK Configuracion valida: {0}, {1} capitulos".format(
            config["novela"]["genero"], config["estructura"]["num_capitulos"]
        )
    )

    for nombre in SUBAGENTES:
        ruta = RAIZ_PROYECTO / ".claude" / "agents" / "{0}.md".format(nombre)
        if not ruta.is_file():
            problemas.append("Falta el subagente .claude/agents/{0}.md".format(nombre))
            continue
        cuerpo = ruta.read_text(encoding="utf-8")
        if "omitClaudeMd: true" not in cuerpo:
            problemas.append(
                "El subagente {0} no lleva `omitClaudeMd: true`. Sin esa linea "
                "recibe CLAUDE.md y deja de estar aislado (regla 5).".format(nombre)
            )
        if "novela-{0}".format(nombre) not in cuerpo:
            problemas.append(
                "El subagente {0} no declara su skill puente `novela-{0}`: sin "
                "ella responde SIN INSTRUCCIONES.".format(nombre)
            )

    for nombre in SUBAGENTES:
        ruta = RAIZ_PROYECTO / ".claude" / "skills" / "novela-{0}".format(nombre) / "SKILL.md"
        if not ruta.is_file():
            problemas.append("Falta la skill puente .claude/skills/novela-{0}/".format(nombre))

    for nombre in SUBAGENTES:
        ruta = RAIZ_PROYECTO / "prompts" / "{0}.md".format(nombre)
        if not ruta.is_file() or not ruta.read_text(encoding="utf-8").strip():
            problemas.append("Falta o esta vacio prompts/{0}.md".format(nombre))

    referencia = RAIZ_PROYECTO / "prompts" / "referencias" / "{0}.md".format(
        config["novela"]["genero"]
    )
    if not referencia.is_file():
        problemas.append("Falta la referencia de genero {0}".format(referencia))

    if problemas:
        escribir("")
        escribir("PROBLEMAS ({0}):".format(len(problemas)))
        for problema in problemas:
            escribir("  - {0}".format(problema))
        return 1

    escribir("OK Los cinco subagentes, sus skills y sus prompts estan en su sitio.")
    escribir("OK Todo listo. Siguiente: python -m src.orquestacion iniciar")
    return 0


def cmd_iniciar(config, salida, desde_cero=False, escribir=print):
    """Prepara salida/ y el estado. Idempotente salvo con --desde-cero."""
    preparar_directorios(salida)

    _escribir(
        Path(salida) / "config-efectiva.json",
        json.dumps(config, indent=2, ensure_ascii=False) + "\n",
    )

    if desde_cero and modulo_estado.existe(salida):
        modulo_estado.borrar(salida)
        escribir("Estado anterior borrado (--desde-cero).")

    estado, reanudado = modulo_estado.cargar_o_nuevo(
        config, salida, modelo_actual=modelo_de_escalon(config, 0)
    )
    modulo_estado.guardar(_completar(estado), salida)

    escribir("Generacion {0}.".format("reanudada" if reanudado else "iniciada"))
    escribir("Configuracion efectiva en {0}".format(Path(salida) / "config-efectiva.json"))
    escribir("")
    informe_de_estado(config, salida, escribir=escribir)
    return 0


def _problemas_legibles(salida, capitulo):
    """La lista acumulada de problemas, en frases que el escritor pueda usar."""
    intentos = intentos_de_capitulo(salida, capitulo)
    lineas = []
    for problema in puntuacion.problemas_acumulados(intentos):
        linea = "[{0}] ({1}) {2}".format(
            problema.get("gravedad", "?"),
            problema.get("validador", "?"),
            problema.get("descripcion", ""),
        )
        if problema.get("evidencia"):
            linea += " | evidencia: {0}".format(problema["evidencia"])
        if problema.get("correccion_sugerida"):
            linea += " | correccion: {0}".format(problema["correccion_sugerida"])
        lineas.append(linea)
    return lineas


def cmd_ventana(config, salida, rol, capitulo=None, escribir=print):
    """Imprime el mensaje de usuario que hay que pasarle a un subagente."""
    if rol == "arquitecto":
        ventana = contexto.ventana_arquitecto(config)
        escribir(ventana.texto)
        return 0

    if capitulo is None:
        paso = siguiente_paso(config, salida)
        capitulo = paso.get("capitulo")
        if capitulo is None:
            raise ErrorDeOrquestacion(
                "No se que capitulo quieres: no hay ninguno en curso. Pasa "
                "--capitulo N."
            )

    biblia = modulo_biblia.cargar(salida, config["estructura"]["num_capitulos"])

    if rol == "escritor":
        ventana = contexto.ventana_escritor(
            config,
            biblia,
            capitulo,
            resumenes=cargar_resumenes(salida),
            texto_anterior=texto_capitulo_anterior(salida, capitulo),
            problemas=_problemas_legibles(salida, capitulo),
        )
        escribir(ventana.texto)
        if ventana.recortes:
            # Los avisos van por stderr para que la ventana que sale por stdout
            # se pueda redirigir a un archivo sin que se cuele texto que no es
            # parte del mensaje del subagente.
            print(
                "AVISO recortes de contexto aplicados: " + "; ".join(ventana.recortes),
                file=sys.stderr,
            )
        return 0

    # Los validadores auditan el ULTIMO intento registrado, no el capitulo
    # aprobado: el capitulo aprobado todavia no existe cuando se valida.
    intentos = intentos_de_capitulo(salida, capitulo)
    if not intentos:
        raise ErrorDeOrquestacion(
            "El capitulo {0} no tiene ningun intento registrado todavia. "
            "Escribelo antes de validarlo.".format(capitulo)
        )
    texto = _leer_archivo(
        ruta_intento_texto(salida, capitulo, intentos[-1]["intento"]),
        "el texto del intento",
    )

    if rol == "continuidad":
        ventana = contexto.ventana_continuidad(config, biblia, capitulo, texto)
    elif rol == "genero":
        # Se pasa la RUTA de la referencia, no su contenido: el subagente la lee
        # dentro de su propio contexto, que muere al terminar. Copiarla aqui
        # meteria 2,5 KB de convenciones en el contexto del orquestador una vez
        # por capitulo (DECISIONES.md, decision 8).
        referencia = Path("prompts") / "referencias" / "{0}.md".format(
            config["novela"]["genero"]
        )
        ventana = contexto.ventana_genero(
            config, referencia.as_posix(), capitulo, texto
        )
    else:
        ventana = contexto.ventana_estilo(
            config, capitulo, texto, memoria_estilo=cargar_memoria_estilo(salida)
        )

    escribir(ventana.texto)
    return 0


def cmd_registrar_biblia(config, salida, archivo, escribir=print):
    """Valida la respuesta del arquitecto y la guarda como biblia.json."""
    estado = cargar_estado(config, salida)
    contar_delegacion(estado, salida)

    crudo = _leer_archivo(archivo, "la respuesta del arquitecto")
    _escribir(_tmp(salida) / "biblia-intento.raw", crudo)

    try:
        datos = puntuacion.extraer_json(crudo)
    except puntuacion.ErrorDeVeredicto as error:
        raise ErrorDeOrquestacion(
            "La respuesta del arquitecto no es JSON: {0}\n"
            "Arreglo: vuelve a delegar en el arquitecto pasandole este error en "
            "el mensaje. Si falla dos veces, la ejecucion aborta (flujo 3.4): "
            "sin biblia no hay novela.".format(error)
        ) from error

    try:
        biblia = modulo_biblia.validar(
            modulo_biblia.normalizar(datos), config["estructura"]["num_capitulos"]
        )
    except modulo_biblia.ErrorDeBiblia as error:
        raise ErrorDeOrquestacion(
            "La biblia no cumple el contrato del spec 7.1:\n{0}\n"
            "Arreglo: vuelve a delegar en el arquitecto pasandole esta lista "
            "entera. Se acumulan todos los problemas a proposito, para que los "
            "arregle de una vez y no de uno en uno.".format(error)
        ) from error

    modulo_biblia.guardar(biblia, salida)
    escribir("Biblia guardada en {0}".format(modulo_biblia.ruta(salida)))
    escribir("")
    informe_de_estado(config, salida, escribir=escribir)
    return 0


def cmd_registrar_intento(config, salida, capitulo, archivo, escribir=print):
    """Guarda el texto que devolvio el escritor como un intento nuevo."""
    estado = cargar_estado(config, salida)
    texto = _leer_archivo(archivo, "el texto del capitulo")

    intentos = intentos_de_capitulo(salida, capitulo)
    if intentos and not intentos[-1].get("resuelto"):
        raise ErrorDeOrquestacion(
            "El intento {0} del capitulo {1} todavia esta sin resolver.\n"
            "Arreglo: termina de validarlo y lanza `resolver` antes de escribir "
            "otro. Si no, tendrias dos intentos abiertos y ninguno "
            "contabilizado.".format(intentos[-1]["intento"], capitulo)
        )

    numero = len(intentos) + 1
    escalon = escalon_de_intento(config, estado.get("escalon_inicial", 0), numero)
    modelo = modelo_de_escalon(config, escalon)

    _escribir(ruta_intento_texto(salida, capitulo, numero), texto)
    guardar_intento(salida, capitulo, {
        "capitulo": capitulo,
        "intento": numero,
        "escalon": escalon,
        "modelo": modelo,
        "palabras": len(texto.split()),
        "veredictos": [],
        "resuelto": False,
    })

    if numero == 1:
        modulo_estado.empezar_capitulo(estado, capitulo, modelo)
    estado["capitulo_actual"] = capitulo
    estado["intento_actual"] = numero
    estado["modelo_actual"] = modelo
    contar_delegacion(estado, salida)

    palabras = len(texto.split())
    minimo = config["estructura"]["palabras_min"]
    maximo = config["estructura"]["palabras_max"]
    escribir(
        "Intento {0} del capitulo {1} guardado ({2} palabras, modelo {3}).".format(
            numero, capitulo, palabras, modelo
        )
    )
    if not minimo <= palabras <= maximo:
        # No es un fallo: el rango es cosa de los validadores, no de un contador
        # de palabras. Pero conviene verlo, porque suele explicar un FALLO.
        escribir(
            "  AVISO: fuera del rango configurado ({0}-{1} palabras).".format(
                minimo, maximo
            )
        )
    escribir("")
    informe_de_estado(config, salida, escribir=escribir)
    return 0


def cmd_registrar_veredicto(config, salida, capitulo, validador, archivo, escribir=print):
    """Parsea y guarda el veredicto de un validador sobre el ultimo intento."""
    estado = cargar_estado(config, salida)
    intentos = intentos_de_capitulo(salida, capitulo)
    if not intentos:
        raise ErrorDeOrquestacion(
            "El capitulo {0} no tiene ningun intento que validar.".format(capitulo)
        )
    intento = intentos[-1]
    if intento.get("resuelto"):
        raise ErrorDeOrquestacion(
            "El intento {0} del capitulo {1} ya esta resuelto. Un veredicto que "
            "llega tarde no puede cambiar una decision ya tomada.".format(
                intento["intento"], capitulo
            )
        )

    crudo = _leer_archivo(archivo, "la respuesta del validador")
    _escribir(
        _tmp(salida) / "cap-{0:02d}-intento-{1}-{2}.raw".format(
            capitulo, intento["intento"], validador
        ),
        crudo,
    )

    veredicto = puntuacion.leer(crudo, validador, capitulo)
    intento["veredictos"] = [
        v for v in intento.get("veredictos", []) if v.get("validador") != validador
    ] + [veredicto]
    guardar_intento(salida, capitulo, intento)
    contar_delegacion(estado, salida)

    etiqueta = veredicto["veredicto"]
    escribir(
        "Veredicto de {0} sobre el capitulo {1}, intento {2}: {3} ({4} "
        "problema(s)).".format(
            validador, capitulo, intento["intento"], etiqueta,
            len(veredicto["problemas"]),
        )
    )
    if etiqueta == puntuacion.INDETERMINADO:
        escribir(
            "  Su respuesta no se pudo interpretar. Cuenta como FALLO (regla 2)."
        )
        escribir("  Motivo: {0}".format(veredicto["problemas"][0]["descripcion"]))
    for problema in veredicto["problemas"]:
        escribir("  - [{0}] {1}".format(problema["gravedad"], problema["descripcion"]))
    escribir("")
    informe_de_estado(config, salida, escribir=escribir)
    return 0


def _aprobar(config, salida, estado, capitulo, intento, motivo, escribir):
    """Cierra un capitulo: escribe el texto, el resumen y la memoria larga."""
    texto = _leer_archivo(
        ruta_intento_texto(salida, capitulo, intento["intento"]),
        "el texto del intento ganador",
    )
    _escribir(ruta_capitulo(salida, capitulo), texto)

    # Resumen provisional: la sinopsis del outline. Es determinista y no cuesta
    # una delegacion. El resumen redactado por un modelo es una etapa posterior;
    # hasta entonces esto mantiene la ventana del escritor funcionando, que es
    # para lo que sirve el resumen.
    entrada = modulo_biblia.entrada_outline(
        modulo_biblia.cargar(salida, config["estructura"]["num_capitulos"]), capitulo
    ) or {}
    _escribir(
        ruta_resumen(salida, capitulo),
        (entrada.get("sinopsis") or "Capitulo {0}.".format(capitulo)).strip() + "\n",
    )

    for veredicto in intento.get("veredictos", []):
        if veredicto.get("validador") == "estilo":
            actualizar_memoria_estilo(
                salida, capitulo, veredicto.get("nuevas_frases_recurrentes", [])
            )

    if motivo == "APROBADO":
        modulo_estado.aprobar_capitulo(estado, capitulo)
        # `mantener_voz_ganadora`: el capitulo siguiente arranca en el escalon
        # que resolvio este, no al principio de la escalera.
        if config.get("modelos", {}).get("mantener_voz_ganadora", True):
            estado["escalon_inicial"] = intento.get("escalon", 0)
        else:
            estado["escalon_inicial"] = 0
    else:
        modulo_estado.marcar_capitulo(estado, capitulo)
        # Aceptado por puntuacion no es una victoria de nadie: la escalera del
        # capitulo siguiente vuelve a empezar por abajo.
        estado["escalon_inicial"] = 0

    estado["intento_actual"] = 0
    modulo_estado.guardar(estado, salida)

    escribir("Capitulo {0}: {1} (intento {2}, modelo {3}).".format(
        capitulo, motivo, intento["intento"], intento.get("modelo")
    ))
    escribir("  Texto en {0}".format(ruta_capitulo(salida, capitulo)))
    return 0


def cmd_resolver(config, salida, capitulo, escribir=print):
    """Decide que pasa con el ultimo intento: aprobar, reintentar o aceptar."""
    estado = cargar_estado(config, salida)
    intentos = intentos_de_capitulo(salida, capitulo)
    if not intentos:
        raise ErrorDeOrquestacion(
            "El capitulo {0} no tiene ningun intento que resolver.".format(capitulo)
        )
    intento = intentos[-1]
    if intento.get("resuelto"):
        raise ErrorDeOrquestacion(
            "El intento {0} del capitulo {1} ya estaba resuelto.".format(
                intento["intento"], capitulo
            )
        )

    veredictos = intento.get("veredictos", [])
    emitidos = {v.get("validador") for v in veredictos}
    faltan = [v for v in puntuacion.VALIDADORES if v not in emitidos]
    if faltan:
        raise ErrorDeOrquestacion(
            "Faltan los veredictos de: {0}. Un capitulo no se resuelve con "
            "validaciones a medias: un validador ausente no es un validador que "
            "aprueba (regla 5).".format(", ".join(faltan))
        )

    pesos = config.get("validacion", {}).get("pesos_gravedad", puntuacion.PESOS_POR_DEFECTO)
    intento["puntuacion"] = puntuacion.puntuar(veredictos, pesos)
    intento["resuelto"] = True

    if puntuacion.aprueba(veredictos):
        intento["resultado"] = "APROBADO"
        guardar_intento(salida, capitulo, intento)
        codigo = _aprobar(config, salida, estado, capitulo, intento, "APROBADO", escribir)
        escribir("")
        informe_de_estado(config, salida, escribir=escribir)
        return codigo

    maximo = intentos_maximos(config, estado.get("escalon_inicial", 0))
    if intento["intento"] < maximo:
        intento["resultado"] = "REINTENTAR"
        guardar_intento(salida, capitulo, intento)
        escribir(
            "Capitulo {0}, intento {1} de {2}: FALLO (puntuacion {3}).".format(
                capitulo, intento["intento"], maximo, intento["puntuacion"]
            )
        )
        for veredicto in veredictos:
            if puntuacion.es_fallo(veredicto):
                escribir("  {0}: {1} problema(s)".format(
                    veredicto["validador"], len(veredicto["problemas"])
                ))
        escribir(
            "  Los problemas se acumulan y viajan con la reescritura: la "
            "ventana del escritor los incluira sin que haya que copiarlos."
        )
        escribir("")
        informe_de_estado(config, salida, escribir=escribir)
        return 0

    # Escalera agotada: gana la mejor version intentada (spec 6.4).
    intento["resultado"] = "ESCALERA_AGOTADA"
    guardar_intento(salida, capitulo, intento)
    candidatos = intentos_de_capitulo(salida, capitulo)
    ganador = puntuacion.mejor_intento(candidatos)
    escribir(
        "Capitulo {0}: agotados los {1} intentos sin aprobacion.".format(
            capitulo, maximo
        )
    )
    for candidato in candidatos:
        marca = " <- elegido" if candidato["intento"] == ganador["intento"] else ""
        escribir("  intento {0} ({1}): puntuacion {2}{3}".format(
            candidato["intento"], candidato.get("modelo"),
            candidato.get("puntuacion", 0), marca,
        ))
    escribir(
        "  Menor puntuacion gana; en empate, el intento mas tardio. Ojo: sin "
        "temperatura fija esa puntuacion es una ordenacion aproximada, no una "
        "medida (DECISIONES.md, decision 9)."
    )
    codigo = _aprobar(
        config, salida, estado, capitulo, ganador, "ACEPTADO_POR_PUNTUACION", escribir
    )
    escribir("")
    informe_de_estado(config, salida, escribir=escribir)
    return codigo


# ---------------------------------------------------------------------------
# Linea de comandos
# ---------------------------------------------------------------------------


def construir_parser():
    parser = argparse.ArgumentParser(
        prog="python -m src.orquestacion",
        description=(
            "Cuaderno de la generacion: guarda el estado en archivos y dice que "
            "toca hacer ahora. No delega en ningun subagente."
        ),
    )
    sub = parser.add_subparsers(dest="comando", required=True)

    sub.add_parser("comprobar", help="verifica entorno, subagentes y prompts")

    iniciar = sub.add_parser("iniciar", help="prepara salida/ y el estado")
    iniciar.add_argument(
        "--desde-cero", action="store_true",
        help="borra el estado anterior y empieza una generacion nueva",
    )

    sub.add_parser("estado", help="que toca hacer ahora")

    ventana = sub.add_parser("ventana", help="imprime la ventana de un subagente")
    ventana.add_argument("rol", choices=ROLES_VENTANA)
    ventana.add_argument("--capitulo", type=int, default=None)

    biblia_cmd = sub.add_parser(
        "registrar-biblia", help="valida y guarda la respuesta del arquitecto"
    )
    biblia_cmd.add_argument("--archivo", required=True)

    intento = sub.add_parser(
        "registrar-intento", help="guarda el texto que devolvio el escritor"
    )
    intento.add_argument("--capitulo", type=int, required=True)
    intento.add_argument("--archivo", required=True)

    veredicto = sub.add_parser(
        "registrar-veredicto", help="parsea y guarda el veredicto de un validador"
    )
    veredicto.add_argument("--capitulo", type=int, required=True)
    veredicto.add_argument("--validador", choices=puntuacion.VALIDADORES, required=True)
    veredicto.add_argument("--archivo", required=True)

    resolver = sub.add_parser(
        "resolver", help="aprobar, reintentar o aceptar por puntuacion"
    )
    resolver.add_argument("--capitulo", type=int, required=True)

    return parser


def main(argv=None):
    parser = construir_parser()
    args = parser.parse_args(argv)

    try:
        config = cargar_config()
        salida = directorio_salida(config)

        if args.comando == "comprobar":
            return cmd_comprobar(config, salida)
        if args.comando == "iniciar":
            return cmd_iniciar(config, salida, desde_cero=args.desde_cero)
        if args.comando == "estado":
            informe_de_estado(config, salida)
            return 0
        if args.comando == "ventana":
            return cmd_ventana(config, salida, args.rol, args.capitulo)
        if args.comando == "registrar-biblia":
            return cmd_registrar_biblia(config, salida, args.archivo)
        if args.comando == "registrar-intento":
            return cmd_registrar_intento(config, salida, args.capitulo, args.archivo)
        if args.comando == "registrar-veredicto":
            return cmd_registrar_veredicto(
                config, salida, args.capitulo, args.validador, args.archivo
            )
        if args.comando == "resolver":
            return cmd_resolver(config, salida, args.capitulo)
    except (ErrorDeOrquestacion, ErrorDeConfiguracion,
            modulo_estado.ErrorDeEstado, modulo_biblia.ErrorDeBiblia) as error:
        print("ERROR: {0}".format(error), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
