"""Servidor local del panel: sirve, configura y arranca generaciones.

QUE ES
------
Un servidor HTTP minimo, para la maquina de quien lo lanza y para nadie mas,
que sirve `panel.html` y los archivos de `salida/`. Hasta ahora eso lo hacia
`python -m http.server`; este modulo hace lo mismo y ademas abre la puerta a los
endpoints de escritura que vienen despues (configuracion y generacion).

POR QUE FASTAPI
---------------
Porque es lo que se pidio, y porque de los endpoints que vendran despues dos
reciben JSON y tienen que validarlo antes de tocar el disco: eso con la libreria
estandar se escribe a mano y se equivoca uno. No hay ninguna otra razon; para
servir archivos, `http.server` habria bastado.

QUE NO HACE, Y ES DELIBERADO
----------------------------
- **No llama a ningun modelo.** Lanza un proceso, y solo uno: el CLI de Claude
  Code (`claude -p`), que es quien habla con los modelos. Aqui no hay
  credenciales, ni cliente HTTP, ni nada que configurar. La diferencia entre
  llamar a un modelo y arrancar el programa que llama a los modelos no es un
  tecnicismo: es toda la arquitectura de este proyecto.
- **No ejecuta nada que venga del navegador.** El comando y el prompt de
  generacion son constantes de este archivo. Desde fuera solo se puede decir
  «empieza» y «para», nunca «empieza con esto».
- **No sale a la red.** Escucha; no pide nada a nadie.
- **No sirve el proyecto entero.** Solo `panel.html` y lo que hay debajo de
  `salida/`. Esto no es una comodidad: en la raiz hay un `.env` con una clave
  de la arquitectura anterior, y un servidor que sirviera el directorio entero
  la dejaria a un `GET` de distancia. La lista blanca es la proteccion, no el
  filtro de rutas.

SEGURIDAD
---------
1. Escucha solo en `127.0.0.1`. La direccion no es configurable desde fuera: es
   una constante de este archivo.
2. Lista blanca de lo que se puede leer (`panel.html` y `salida/`).
3. Toda ruta pedida se resuelve y se comprueba que cae dentro del proyecto. Se
   resuelve DESPUES de normalizar, asi que ni `..`, ni rutas absolutas, ni un
   enlace simbolico que apunte fuera consiguen salir.
"""

from __future__ import annotations

import copy
import json
import mimetypes
import os
import shutil
import subprocess
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path

from fastapi import Body, FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse

from src import config as modulo_config
from src import delegaciones
from src import redaccion

# La raiz del proyecto: este archivo vive en <raiz>/src/servidor.py
RAIZ_PROYECTO = Path(__file__).resolve().parent.parent

# Direccion y puerto por defecto. La direccion es una constante y no un
# parametro a proposito: un servidor que escribe config.json y arranca procesos
# no puede quedar expuesto a la red local por un descuido en la linea de
# comandos.
DIRECCION = "127.0.0.1"
PUERTO = 8000

# Lo unico que se sirve, ademas de la pagina. Cualquier otra cosa del proyecto
# —codigo, documentacion, `.env`— es 404 aunque exista.
PREFIJO_SALIDA = "salida"

# Tipos que la libreria estandar no siempre conoce y que este panel necesita.
TIPOS = {
    ".md": "text/markdown; charset=utf-8",
    ".json": "application/json; charset=utf-8",
    ".html": "text/html; charset=utf-8",
    ".txt": "text/plain; charset=utf-8",
    ".raw": "text/plain; charset=utf-8",
}


class ErrorDeServidor(Exception):
    """El servidor no se puede montar con esta configuracion."""


def _tipo_de(ruta: Path) -> str:
    """Tipo MIME, siempre con charset utf-8 en lo que es texto.

    Sin el charset explicito, un manuscrito con acentos puede llegar al
    navegador mal descodificado segun quien lo sirva. Aqui se declara y se
    acaba el problema.
    """
    conocido = TIPOS.get(ruta.suffix.lower())
    if conocido:
        return conocido
    adivinado, _ = mimetypes.guess_type(ruta.name)
    if adivinado and adivinado.startswith("text/"):
        return adivinado + "; charset=utf-8"
    return adivinado or "application/octet-stream"


def directorio_salida(raiz: Path) -> Path:
    """Donde vive `salida/`, segun la configuracion, validado.

    Se lee de la configuracion en vez de darlo por hecho, porque
    `runtime.directorio_salida` se puede cambiar. Pero si apuntara fuera del
    proyecto, el servidor no arranca: servir por HTTP una carpeta cualquiera del
    disco es justo lo que este modulo no puede permitirse.
    """
    try:
        destino = modulo_config.ruta_salida(modulo_config.cargar_config(volcar=False))
    except Exception:
        # Si la configuracion no se puede leer, el panel todavia tiene sentido
        # (lee archivos, no configuracion), asi que se cae al sitio de siempre.
        destino = raiz / "salida"
    destino = Path(destino).resolve()
    if not _dentro(destino, raiz):
        raise ErrorDeServidor(
            "runtime.directorio_salida apunta fuera del proyecto ({0}).\n"
            "Arreglo: el servidor solo sirve rutas de dentro del proyecto. "
            "Devuelvelo a ./salida o lanza el panel sin servidor.".format(destino)
        )
    return destino


def _dentro(candidata: Path, raiz: Path) -> bool:
    """Dice si `candidata` esta dentro de `raiz`, ya resueltas las dos.

    `Path.resolve()` deshace `..` y sigue los enlaces simbolicos, asi que esta
    comprobacion se hace sobre la ruta real y no sobre la que escribio el
    cliente. Es la unica barrera que hace falta, pero tiene que ir DESPUES de
    resolver: comprobar la cadena antes de resolverla no sirve de nada.
    """
    try:
        return candidata == raiz or raiz in candidata.parents
    except Exception:
        return False


def resolver_peticion(relativa: str, raiz: Path, salida: Path) -> Path:
    """Traduce la ruta pedida por el navegador a un archivo real, o falla.

    Lanza `HTTPException` con 404 en todos los casos en los que no se sirve,
    incluidos los intentos de salirse del proyecto. Se devuelve 404 y no 403 a
    proposito: un 403 confirmaria que el archivo existe, y eso ya es informacion
    que nadie tiene por que obtener de aqui.
    """
    limpia = (relativa or "").strip("/")
    if not limpia or limpia == "panel.html":
        destino = (raiz / "panel.html").resolve()
        if not destino.is_file():
            raise HTTPException(status_code=404, detail="No encuentro panel.html")
        return destino

    partes = limpia.split("/")
    if partes[0] != PREFIJO_SALIDA:
        # Ni el codigo, ni la documentacion, ni .env. Solo el panel y salida/.
        raise HTTPException(status_code=404, detail="Aqui solo se sirve panel.html y salida/")

    destino = (salida.joinpath(*partes[1:])).resolve()
    if not _dentro(destino, salida) or not destino.is_file():
        raise HTTPException(status_code=404, detail="No encuentro ese archivo")
    return destino


# ---------------------------------------------------------------------------
# Configuracion: leerla y escribirla
# ---------------------------------------------------------------------------
#
# Escribir `config.json` desde el navegador es el primer punto en el que este
# servidor deja de ser inofensivo, asi que la escritura tiene cuatro puertas y
# hay que pasarlas todas, en este orden:
#
#   1. No hay una generacion en marcha.       (si la hay, 409 y no se toca nada)
#   2. Lo que llega solo toca claves que YA existen, con el tipo que ya tenian.
#   3. La configuracion resultante entera pasa por `src/config.py`.
#   4. Solo entonces se escribe, y de forma atomica.
#
# La 2 es la que evita que el archivo se escriba «tal como llegue»: no se
# acepta el cuerpo de la peticion como configuracion, se acepta como una lista
# de cambios sobre la que ya hay, y cualquier clave desconocida es un error, no
# un anadido.


def ruta_config(raiz: Path) -> Path:
    return raiz / "config.json"


def leer_config_archivo(raiz: Path) -> dict:
    """El contenido literal de config.json, sin fusionar con nada.

    Es distinto de la configuracion efectiva: esta es la que se edita, y la otra
    es la que de verdad se usa despues de aplicar valores por defecto, perfil de
    genero y variables de entorno.
    """
    destino = ruta_config(raiz)
    if not destino.is_file():
        raise HTTPException(status_code=404, detail="No encuentro config.json")
    try:
        return json.loads(destino.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=500,
            detail="config.json no es JSON valido: {0}".format(error),
        ) from error


def generacion_en_curso(salida: Path) -> dict | None:
    """La delegacion que el harness dice tener en marcha, o None.

    Se mira `delegacion_en_curso` de `estado.json`, que es la senal que la
    sesion escribe antes de cada delegacion (EJECUCION.md 2.4). Si no se puede
    leer el estado, se responde None: no haber podido comprobarlo no es lo
    mismo que haber comprobado que no hay nada, pero bloquear la edicion porque
    falta un archivo dejaria la configuracion inaccesible para siempre.
    """
    archivo = salida / "estado.json"
    if not archivo.is_file():
        return None
    try:
        datos = json.loads(archivo.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    marca = datos.get("delegacion_en_curso")
    return marca if isinstance(marca, dict) else None


def _nombre_tipo(valor) -> str:
    return {
        bool: "booleano", int: "numero entero", float: "numero",
        str: "texto", list: "lista", dict: "objeto", type(None): "nulo",
    }.get(type(valor), type(valor).__name__)


def _tipo_compatible(actual, nuevo) -> bool:
    """Dice si `nuevo` puede sustituir a `actual` sin cambiar de tipo.

    Un `None` en el archivo significa «sin valor todavia» —como
    `semilla_tematica` antes de escribirla—, asi que acepta cualquier valor
    simple: es el unico caso en el que no hay tipo previo del que fiarse.

    Los booleanos se comprueban antes que los enteros porque en Python `True`
    es un entero, y sin ese cuidado se podria colar un `true` donde va un
    numero de capitulos.
    """
    if actual is None:
        return isinstance(nuevo, (str, int, float, bool, type(None)))
    if isinstance(actual, bool):
        return isinstance(nuevo, bool)
    if isinstance(nuevo, bool):
        return False
    if isinstance(actual, int):
        return isinstance(nuevo, int)
    if isinstance(actual, float):
        return isinstance(nuevo, (int, float))
    if isinstance(actual, str):
        return isinstance(nuevo, str)
    if isinstance(actual, list):
        return isinstance(nuevo, list)
    return False


def revisar_cambios(actual: dict, entrante: dict, prefijo: str = ""):
    """Compara lo que llega con lo que hay. Devuelve (errores, cambios).

    No modifica nada: solo dice que se podria hacer y que no. Los errores van
    todos juntos y en texto llano, para que quien edita los arregle de una vez
    y no de uno en uno, que es el mismo criterio que usa el validador de la
    biblia.
    """
    errores: list[str] = []
    cambios: list[dict] = []

    if not isinstance(entrante, dict):
        return (["Lo que se envia tiene que ser un objeto JSON."], [])

    for clave, valor in entrante.items():
        donde = "{0}{1}".format(prefijo, clave)

        if str(clave).startswith("_"):
            errores.append(
                "'{0}': las claves que empiezan por guion bajo son metadatos y "
                "comentarios del archivo, no ajustes. No se pueden editar desde "
                "aqui.".format(donde)
            )
            continue

        if clave not in actual:
            errores.append(
                "'{0}': no existe en config.json. Desde aqui solo se pueden "
                "cambiar ajustes que ya estan en el archivo, no crear nuevos.".format(donde)
            )
            continue

        previo = actual[clave]

        if isinstance(previo, dict) or isinstance(valor, dict):
            if not (isinstance(previo, dict) and isinstance(valor, dict)):
                errores.append(
                    "'{0}': se esperaba {1} y ha llegado {2}.".format(
                        donde, _nombre_tipo(previo), _nombre_tipo(valor))
                )
                continue
            sub_err, sub_cam = revisar_cambios(previo, valor, donde + ".")
            errores.extend(sub_err)
            cambios.extend(sub_cam)
            continue

        # La marca del filtro de redaccion nunca se escribe de vuelta. Sin esto,
        # editar en el panel un ajuste que se mostro redactado guardaria la
        # palabra "[REDACTADO]" como si fuera el valor de verdad.
        if valor == redaccion.MARCA or (
            isinstance(valor, list) and redaccion.MARCA in valor
        ):
            errores.append(
                "'{0}': ese valor llego redactado al navegador y no se puede "
                "guardar de vuelta. Escribe el valor real o deja el ajuste como "
                "estaba.".format(donde)
            )
            continue

        if not _tipo_compatible(previo, valor):
            errores.append(
                "'{0}': se esperaba {1} y ha llegado {2}.".format(
                    donde, _nombre_tipo(previo), _nombre_tipo(valor))
            )
            continue

        if isinstance(previo, list) and previo and isinstance(valor, list):
            malos = [x for x in valor if not _tipo_compatible(previo[0], x)]
            if malos:
                errores.append(
                    "'{0}': la lista tiene que ser de {1}. No encajan: {2}.".format(
                        donde, _nombre_tipo(previo[0]), ", ".join(repr(m) for m in malos))
                )
                continue

        if previo != valor:
            cambios.append({"clave": donde, "antes": previo, "despues": valor})

    return errores, cambios


def fusionar_config(actual: dict, entrante: dict) -> dict:
    """Aplica los cambios sobre una copia. El original no se toca."""
    resultado = copy.deepcopy(actual)
    for clave, valor in entrante.items():
        if isinstance(resultado.get(clave), dict) and isinstance(valor, dict):
            resultado[clave] = fusionar_config(resultado[clave], valor)
        else:
            resultado[clave] = copy.deepcopy(valor)
    return resultado


def validar_config_candidata(candidata: dict) -> list[str]:
    """Pasa la configuracion entera por `src/config.py`. Devuelve los errores.

    Se valida escribiendola a un archivo temporal y cargandola como se cargaria
    de verdad, en vez de llamar solo a `validar()`: asi se comprueba tambien la
    fusion con los valores por defecto y con el perfil del genero, que es lo que
    el harness usara despues. Se pasa un entorno vacio a proposito, porque lo
    que se esta validando es el ARCHIVO, no lo que las variables `NOVELA_` de
    esta maquina harian con el.
    """
    with tempfile.TemporaryDirectory() as carpeta:
        temporal = Path(carpeta) / "config.json"
        temporal.write_text(
            json.dumps(candidata, ensure_ascii=False, indent=2), encoding="utf-8"
        )
        try:
            modulo_config.cargar_config(
                ruta_config=temporal, entorno={}, volcar=False
            )
        except modulo_config.ErrorDeConfiguracion as error:
            return [str(error)]
    return []


def escribir_config(raiz: Path, datos: dict) -> Path:
    """Escribe config.json de forma atomica.

    Primero a un temporal en la misma carpeta y despues renombrado: si el
    proceso muere a media escritura, el archivo de siempre sigue entero. Es la
    misma precaucion que toma `src/estado.py`, y aqui importa mas todavia,
    porque un `config.json` a medias deja el harness sin arrancar.
    """
    destino = ruta_config(raiz)
    temporal = destino.with_suffix(".json.tmp")
    temporal.write_text(
        json.dumps(datos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    os.replace(temporal, destino)
    return destino


# ---------------------------------------------------------------------------
# Generar: arrancar una sesion de Claude Code en segundo plano
# ---------------------------------------------------------------------------
#
# Aqui es donde este servidor deja de ser un lector de archivos. Lo que lanza es
# el CLI de Claude Code en modo headless, que es el orquestador de verdad: el
# harness sigue sin llamar a ninguna API de modelos, y este modulo tampoco. La
# diferencia entre «llamar a un modelo» y «arrancar el programa que llama a los
# modelos» no es un tecnicismo: aqui no hay credenciales, no hay cliente HTTP y
# no hay nada que configurar. Solo un `subprocess`.
#
# Lo que el navegador puede pedir es «empieza» y «para». Nada mas. El comando y
# el prompt son constantes de este archivo y no se pueden influir desde fuera.

NOMBRE_LOG = ".log-generacion.txt"
NOMBRE_MARCA_GENERACION = ".generacion.json"

# El prompt es fijo. No se compone con nada que venga de la peticion, ni
# siquiera indirectamente: es esta constante y punto. Arranca el flujo por donde
# manda el propio contrato de ejecucion.
PROMPT_GENERACION = (
    "Genera la novela configurada en config.json, de principio a fin, siguiendo "
    "EJECUCION.md. Empieza ejecutando `python -m src.orquestacion estado` y haz "
    "lo que diga: delega en el subagente y con el modelo exactos que indique, "
    "marca cada delegacion con `empezar-delegacion` ANTES de lanzarla, registra "
    "el resultado despues, y vuelve a preguntar por el estado. No pidas "
    "confirmacion entre intentos ni entre capitulos. Termina ensamblando el "
    "manuscrito."
)


def comando_generacion() -> list[str]:
    """El comando exacto que se lanza. Sin shell y sin nada de fuera.

    Va como lista, nunca como cadena, para que no exista la posibilidad de que
    algo se interprete: no hay shell que interprete nada.
    """
    return ["claude", "-p", PROMPT_GENERACION]


def siguiente_carpeta_copia(raiz: Path) -> Path:
    """La primera `salida-novela-N/` libre. No pisa ninguna existente."""
    n = 1
    while (raiz / "salida-novela-{0}".format(n)).exists():
        n += 1
    return raiz / "salida-novela-{0}".format(n)


def copiar_novela(raiz: Path, salida: Path) -> dict:
    """Pone a salvo la novela actual antes de que la proxima la pise.

    Devuelve que se hizo. Si habia algo y no se pudo copiar, lanza excepcion:
    generar sin copia perderia una novela terminada, y eso no se arregla
    despues.
    """
    if not salida.is_dir() or not any(salida.iterdir()):
        return {"copiado": False, "destino": None,
                "motivo": "no habia ninguna novela que copiar"}
    destino = siguiente_carpeta_copia(raiz)
    shutil.copytree(salida, destino)
    return {"copiado": True, "destino": destino.name, "motivo": None}


def _ahora() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def ultimas_lineas(archivo: Path, cuantas: int = 40) -> list[str]:
    """Las ultimas lineas del log, sin cargarlo entero en memoria."""
    if not archivo.is_file():
        return []
    try:
        with archivo.open("rb") as f:
            f.seek(0, os.SEEK_END)
            fin = f.tell()
            trozo = min(fin, 64 * 1024)
            f.seek(fin - trozo)
            datos = f.read(trozo)
    except OSError:
        return []
    texto = datos.decode("utf-8", errors="replace")
    return [l for l in texto.splitlines()[-cuantas:]]


class Generacion:
    """Lleva la cuenta del proceso de generacion, si lo hay.

    Vive mientras vive el servidor. Si el servidor se reinicia con una
    generacion en marcha, esta clase **no la reconoce**, y eso se dice tal cual
    en vez de adivinar: comprobar si un PID sigue vivo de forma portable es
    justo el tipo de cosa que en Windows sale mal y mata el proceso equivocado.
    """

    def __init__(self, raiz: Path, salida: Path, comando=None):
        self.raiz = raiz
        self.salida = salida
        self._construir_comando = comando or comando_generacion
        self.proceso: subprocess.Popen | None = None
        self.info: dict = {}

    # --- archivos ---
    @property
    def log(self) -> Path:
        return self.salida / NOMBRE_LOG

    @property
    def marca(self) -> Path:
        return self.salida / NOMBRE_MARCA_GENERACION

    def _guardar_marca(self):
        try:
            self.marca.write_text(
                json.dumps(self.info, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            pass

    def _leer_marca(self) -> dict:
        if not self.marca.is_file():
            return {}
        try:
            return json.loads(self.marca.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {}

    # --- ciclo de vida ---
    def viva(self) -> bool:
        return self.proceso is not None and self.proceso.poll() is None

    def lanzar(self) -> dict:
        """Copia la novela, arranca el proceso y vuelve enseguida."""
        if self.viva():
            raise HTTPException(status_code=409, detail={
                "mensaje": "Ya hay una generacion en marcha.",
                "generacion": self.estado(),
            })

        if shutil.which(self._construir_comando()[0]) is None:
            # Se comprueba ANTES de copiar: si no se va a poder generar, no
            # tiene sentido dejar una carpeta de copia suelta.
            raise HTTPException(status_code=503, detail={
                "mensaje": "No encuentro el ejecutable '{0}' en el PATH. Sin el "
                           "no hay quien genere la novela: el harness no llama a "
                           "ninguna API, delega en Claude Code."
                           .format(self._construir_comando()[0]),
            })

        self.salida.mkdir(parents=True, exist_ok=True)
        try:
            copia = copiar_novela(self.raiz, self.salida)
        except OSError as error:
            raise HTTPException(status_code=500, detail={
                "mensaje": "No se ha lanzado nada. No he podido copiar la novela "
                           "actual, y generar encima la perderia para siempre.",
                "error": str(error),
            }) from error

        inicio = _ahora()
        with self.log.open("a", encoding="utf-8") as f:
            f.write("\n===== GENERACION LANZADA {0} =====\n".format(inicio))
            if copia["copiado"]:
                f.write("Novela anterior copiada a {0}/\n".format(copia["destino"]))
            else:
                f.write("Sin copia previa: {0}.\n".format(copia["motivo"]))
            f.flush()

        # `stdout` y `stderr` al mismo archivo, en modo anadir: el log es el
        # unico rastro que queda si el proceso muere, asi que no se trunca.
        salida_log = self.log.open("a", encoding="utf-8", errors="replace")
        self.proceso = subprocess.Popen(
            self._construir_comando(),
            cwd=str(self.raiz),
            stdout=salida_log,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            shell=False,          # nunca shell: no hay nada que interpretar
        )
        self.info = {
            "estado": "en_marcha",
            "pid": self.proceso.pid,
            "inicio": inicio,
            "fin": None,
            "codigo_salida": None,
            "copia": copia,
            "detenida_a_mano": False,
        }
        self._guardar_marca()

        # Un vigilante que espera al proceso y escribe el cierre en cuanto
        # termine, sin que nadie tenga que preguntar. Es demonio para no impedir
        # que el servidor se apague; si el servidor muere antes, el cierre lo
        # escribe la reconciliacion perezosa de `estado()`.
        hilo = threading.Thread(target=self._vigilar, args=(salida_log,), daemon=True)
        hilo.start()
        return self.estado()

    def _vigilar(self, archivo_abierto):
        try:
            self.proceso.wait()
        finally:
            try:
                archivo_abierto.close()
            except Exception:
                pass
            self._cerrar()

    def _cerrar(self):
        """Deja constancia de que el proceso ya no esta. Se puede llamar dos veces.

        Hace las tres cosas que tienen que pasar SIEMPRE que una generacion
        termina, salga bien o se caiga:

          1. escribir en el log como termino y con que codigo;
          2. quitar `delegacion_en_curso` del estado si quedo pegada;
          3. dejar el resultado anotado para que el panel pueda contarlo.

        La 2 es la importante. Una generacion que muere a media delegacion deja
        esa marca puesta, y sin limpiarla el panel enseñaria «escritor,
        trabajando» para siempre: una mentira que ademas bloquea la edicion de
        la configuracion.
        """
        if not self.info or self.info.get("estado") != "en_marcha":
            return
        codigo = self.proceso.poll() if self.proceso else None
        fin = _ahora()
        detenida = self.info.get("detenida_a_mano")

        if detenida:
            titular = "DETENIDA A MANO"
        elif codigo == 0:
            titular = "TERMINADA"
        else:
            titular = "CAIDA"

        try:
            with self.log.open("a", encoding="utf-8") as f:
                f.write("\n===== {0} {1} (codigo {2}) =====\n".format(titular, fin, codigo))
                if titular == "CAIDA":
                    f.write(
                        "El proceso termino sin que nadie lo parara y sin llegar al "
                        "final. Lo que haya en salida/ es lo que quedo a medias; el "
                        "estado se puede retomar con `python -m src.orquestacion "
                        "estado`.\n"
                    )
        except OSError:
            pass

        marca_colgada = self._limpiar_delegacion_en_curso()

        self.info.update({
            "estado": "detenida" if detenida else ("terminada" if codigo == 0 else "caida"),
            "fin": fin,
            "codigo_salida": codigo,
            "delegacion_colgada": marca_colgada,
        })
        self._guardar_marca()

    def _limpiar_delegacion_en_curso(self) -> dict | None:
        """Quita la marca de delegacion en curso y devuelve la que hubiera.

        Se devuelve para poder contarlo: «murio mientras el escritor llevaba
        3 min con el capitulo 2» es mucho mas util que «murio».
        """
        archivo = self.salida / "estado.json"
        if not archivo.is_file():
            return None
        try:
            datos = json.loads(archivo.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
        colgada = datos.pop(delegaciones.CLAVE_EN_CURSO, None)
        if colgada is None:
            return None
        try:
            archivo.write_text(
                json.dumps(datos, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        except OSError:
            return colgada
        return colgada if isinstance(colgada, dict) else None

    def detener(self) -> dict:
        if not self.viva():
            return {"paro": False, "mensaje": "No habia ninguna generacion en marcha.",
                    "generacion": self.estado()}
        self.info["detenida_a_mano"] = True
        self.proceso.terminate()
        try:
            self.proceso.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.proceso.kill()
            self.proceso.wait(timeout=10)
        self._cerrar()
        return {"paro": True, "mensaje": "Generacion detenida.", "generacion": self.estado()}

    def estado(self, lineas: int = 40) -> dict:
        """Que esta pasando, con las ultimas lineas del log.

        Aqui va la reconciliacion perezosa: si el proceso ya termino y el
        vigilante no llego a cerrarlo, se cierra ahora. Asi nunca se informa de
        una generacion «en marcha» que en realidad acabo hace rato.
        """
        if self.info.get("estado") == "en_marcha" and not self.viva():
            self._cerrar()

        guardado = self.info or self._leer_marca()
        viva = self.viva()

        # Si en disco pone «en_marcha» pero este servidor no es el dueño del
        # proceso, se dice que no se sabe. Es lo unico honesto: comprobar un PID
        # ajeno de forma portable no es fiable, y en Windows la forma obvia mata
        # el proceso.
        estado = guardado.get("estado")
        if estado == "en_marcha" and not viva and self.proceso is None:
            estado = "desconocida"

        respuesta = {
            "viva": viva,
            "estado": estado or "sin_datos",
            "inicio": guardado.get("inicio"),
            "fin": guardado.get("fin"),
            "pid": guardado.get("pid"),
            "codigo_salida": guardado.get("codigo_salida"),
            "copia": guardado.get("copia"),
            "delegacion_colgada": guardado.get("delegacion_colgada"),
            "log": ultimas_lineas(self.log, lineas),
            "log_existe": self.log.is_file(),
            # Para que la confirmacion del panel pueda decir, ANTES de pulsar,
            # a que carpeta exacta se va a copiar la novela de ahora. Avisar
            # con el nombre real es lo que convierte un «¿seguro?» en una
            # advertencia util.
            "proxima_copia": siguiente_carpeta_copia(self.raiz).name,
            "hay_novela_que_copiar": (
                self.salida.is_dir() and any(self.salida.iterdir())
            ),
        }
        if respuesta["inicio"]:
            referencia = respuesta["fin"] if not viva and respuesta["fin"] else _ahora()
            respuesta["segundos"] = _segundos_entre(respuesta["inicio"], referencia)
        else:
            respuesta["segundos"] = None

        respuesta["mensaje"] = _mensaje_de_generacion(respuesta)
        return respuesta


def _segundos_entre(desde: str, hasta: str):
    try:
        a = datetime.strptime(desde, "%Y-%m-%dT%H:%M:%SZ")
        b = datetime.strptime(hasta, "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    return max(0, int((b - a).total_seconds()))


def _mensaje_de_generacion(r: dict) -> str:
    """Una frase que explique el estado sin tener que interpretar campos."""
    if r["viva"]:
        return "Generando desde hace {0} s.".format(r.get("segundos") or 0)
    estado = r.get("estado")
    if estado == "terminada":
        return "La ultima generacion termino bien."
    if estado == "detenida":
        return "La ultima generacion se detuvo a mano."
    if estado == "caida":
        base = ("La ultima generacion se cayo: el proceso termino con codigo {0} "
                "sin llegar al final.".format(r.get("codigo_salida")))
        colgada = r.get("delegacion_colgada")
        if colgada:
            base += (" Murio con una delegacion abierta ({0}{1}), que se ha "
                     "limpiado del estado.".format(
                         colgada.get("rol", "?"),
                         "" if colgada.get("capitulo") is None
                         else " del capitulo {0}".format(colgada["capitulo"])))
        return base
    if estado == "desconocida":
        return ("Hay una generacion anotada como en marcha, pero este servidor no "
                "es su dueño: se lanzo antes de reiniciarlo y no puedo saber si "
                "sigue viva. Mira el log.")
    return "No se ha lanzado ninguna generacion todavia."


def crear_app(raiz: Path | None = None, comando=None) -> FastAPI:
    """Monta la aplicacion. `raiz` se puede pasar para los tests.

    Que la raiz sea un parametro y no una constante es lo que permite probar el
    servidor contra un proyecto de juguete en una carpeta temporal, en vez de
    contra el trabajo de verdad del usuario.
    """
    raiz = Path(raiz or RAIZ_PROYECTO).resolve()
    salida = directorio_salida(raiz)
    # El comando de generacion se puede sustituir al construir la aplicacion, y
    # eso es lo que permite probar el ciclo entero sin gastar delegaciones. Es
    # un parametro de Python, no de HTTP: desde el navegador no hay forma de
    # tocarlo.
    generacion = Generacion(raiz, salida, comando)

    def bloqueo_actual():
        """Por que no se puede editar la configuracion ahora mismo, si es que no.

        Hay dos motivos distintos y los dos valen: que el harness diga que esta
        delegando, y que este servidor tenga un proceso vivo. El segundo cubre
        el hueco entre lanzar la generacion y la primera delegacion, que si no
        seria una ventana en la que la configuracion se podria cambiar debajo
        de un proceso ya arrancado.
        """
        if generacion.viva():
            return {"motivo": "generacion", "detalle": generacion.estado(lineas=0)}
        marca = generacion_en_curso(salida)
        if marca is not None:
            return {"motivo": "delegacion", "detalle": marca}
        return None

    app = FastAPI(
        title="Panel del harness de novelas",
        description="Servidor local de solo lectura. No sale a la red.",
        docs_url=None,       # sin documentacion interactiva: no es una API publica
        redoc_url=None,
    )

    @app.get("/api/salud")
    def salud():
        """Lo minimo para saber que el servidor esta en pie y donde mira."""
        return JSONResponse({
            "ok": True,
            "raiz": str(raiz),
            "salida": str(salida),
            "salida_existe": salida.is_dir(),
            "panel_existe": (raiz / "panel.html").is_file(),
            "escucha_en": DIRECCION,
            # Lo que este servidor puede tocar. La lista crece solo cuando
            # gana un permiso nuevo, y hay un test que hay que cambiar a mano.
            "escribe": ["config.json", "salida/" + NOMBRE_LOG,
                        "salida/" + NOMBRE_MARCA_GENERACION,
                        "salida-novela-N/ (copia antes de generar)"],
            "lanza_procesos": [comando_generacion()[0]],
        })

    @app.get("/api/config")
    def leer_configuracion():
        """La configuracion, en sus dos formas, y si ahora mismo se puede tocar.

        Se devuelven las dos porque responden a preguntas distintas: `archivo`
        es lo que se edita, y `efectiva` es lo que el harness usara de verdad
        despues de aplicar valores por defecto, el perfil del genero y las
        variables `NOVELA_`. Ensenar solo una de las dos confunde: se editaria
        un valor y la generacion usaria otro sin explicacion.
        """
        archivo = leer_config_archivo(raiz)
        try:
            efectiva = modulo_config.cargar_config(
                ruta_config=ruta_config(raiz), volcar=False
            )
            errores = []
        except modulo_config.ErrorDeConfiguracion as error:
            # Una configuracion rota se puede seguir editando: es justo cuando
            # mas falta hace. Se devuelve el archivo con su error al lado.
            efectiva, errores = None, [str(error)]

        bloqueo = bloqueo_actual()
        marca = generacion_en_curso(salida)
        return JSONResponse({
            "archivo": redaccion.redactar(archivo),
            "efectiva": redaccion.redactar(efectiva) if efectiva else None,
            "errores": errores,
            "editable": bloqueo is None,
            "bloqueo": bloqueo,
            "generacion_en_curso": marca,
        })

    @app.put("/api/config")
    def escribir_configuracion(cambios: dict = Body(...)):
        """Aplica cambios sobre config.json. Valida ANTES de escribir.

        El cuerpo de la peticion no es la configuracion nueva: es la lista de
        ajustes a cambiar. Todo lo que no venga se queda como esta.
        """
        bloqueo = bloqueo_actual()
        if bloqueo is not None:
            # 409: el estado del servidor impide la operacion, pero la peticion
            # no tiene nada de malo. Probar mas tarde tiene sentido.
            raise HTTPException(
                status_code=409,
                detail={
                    "mensaje": "Hay una generacion en marcha; la configuracion "
                               "no se toca mientras tanto. Cambiarla a media "
                               "novela dejaria unos capitulos escritos con unos "
                               "ajustes y el resto con otros.",
                    "bloqueo": bloqueo,
                    "generacion_en_curso": (
                        bloqueo["detalle"] if bloqueo["motivo"] == "delegacion" else None
                    ),
                },
            )

        actual = leer_config_archivo(raiz)
        errores, lista_cambios = revisar_cambios(actual, cambios)
        if errores:
            raise HTTPException(status_code=400, detail={
                "mensaje": "No se ha escrito nada. Estos ajustes no se pueden aplicar:",
                "errores": errores,
            })

        candidata = fusionar_config(actual, cambios)
        errores = validar_config_candidata(candidata)
        if errores:
            raise HTTPException(status_code=400, detail={
                "mensaje": "No se ha escrito nada. La configuracion resultante "
                           "no es valida:",
                "errores": errores,
            })

        if not lista_cambios:
            return JSONResponse({
                "ok": True, "escrito": False, "cambios": [],
                "mensaje": "No habia nada que cambiar: los valores enviados ya "
                           "eran los que habia.",
            })

        escribir_config(raiz, candidata)
        return JSONResponse({
            "ok": True,
            "escrito": True,
            "cambios": lista_cambios,
            "mensaje": "config.json actualizado con {0} cambio(s).".format(
                len(lista_cambios)),
        })

    @app.get("/api/generacion")
    def ver_generacion(lineas: int = 40):
        """Que esta pasando con la generacion, y las ultimas lineas de su log."""
        return JSONResponse(generacion.estado(lineas=max(0, min(lineas, 500))))

    @app.post("/api/generar")
    def lanzar_generacion():
        """Copia la novela actual y arranca una generacion en segundo plano.

        No recibe nada. El comando y el prompt son constantes del servidor: el
        navegador solo puede decir «empieza», nunca «empieza con esto».

        Vuelve enseguida, sin esperar: una generacion son minutos, y dejar la
        peticion HTTP colgada todo ese rato no sirve para nada cuando el
        seguimiento en vivo ya se hace por `estado.json`.
        """
        return JSONResponse(generacion.lanzar())

    @app.post("/api/detener")
    def parar_generacion():
        """Para la generacion en marcha, si la hay."""
        return JSONResponse(generacion.detener())

    @app.get("/{ruta:path}")
    def servir(ruta: str = ""):
        destino = resolver_peticion(ruta, raiz, salida)
        return FileResponse(
            destino,
            media_type=_tipo_de(destino),
            # Sin cache: el panel repregunta por estado.json cada pocos segundos
            # y una respuesta cacheada haria que el seguimiento en vivo ensenara
            # datos viejos, que es peor que no tener seguimiento.
            headers={"Cache-Control": "no-store"},
        )

    return app


def main(argv=None):
    """Levanta el servidor en 127.0.0.1. Es el punto de entrada del modulo."""
    import argparse
    import uvicorn

    parser = argparse.ArgumentParser(
        description="Servidor local del panel. Escucha solo en 127.0.0.1.",
    )
    parser.add_argument("--puerto", type=int, default=PUERTO)
    args = parser.parse_args(argv)

    print("Panel en http://{0}:{1}/".format(DIRECCION, args.puerto))
    print("Solo lectura. Ctrl+C para parar.")
    # `host` no se toma de la linea de comandos: ver el comentario de DIRECCION.
    uvicorn.run(crear_app(), host=DIRECCION, port=args.puerto, log_level="warning")


if __name__ == "__main__":
    main()
