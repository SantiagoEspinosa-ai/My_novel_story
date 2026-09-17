"""Capa de modelos: el UNICO modulo que toca la red (adenda seccion 3).

Todo lo que sale a internet pasa por aqui. Ningun otro modulo importa el SDK
ni hace peticiones. Cuando algo falle en tiempo de ejecucion, hay un solo sitio
donde poner un print.

Responsabilidades:

    - leer la clave de API del entorno (con lector de .env);
    - hablar con OpenRouter a traves del SDK de OpenAI;
    - cargar los prompts de sistema desde prompts/ en tiempo de ejecucion;
    - parsear JSON a la defensiva (adenda 3.5);
    - reintentar con espera creciente cuando la red falla;
    - contar llamadas y coste, y frenar antes de superar los limites;
    - la prueba de conexion documentada en EJECUCION.md 2.3.

La clave de API no se imprime, no se registra y no se guarda en ningun sitio:
solo se comprueba que existe y se le pasa al SDK.
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path

from src.config import RAIZ_PROYECTO

registro = logging.getLogger(__name__)

# Mensaje de diagnostico de la prueba de conexion. No es un prompt de sistema
# (esos viven en prompts/): es un ping de una linea para confirmar que la ruta
# hasta el modelo funciona.
PING_DE_DIAGNOSTICO = "Responde unicamente con la palabra OK."


class ErrorDeAgente(Exception):
    """Fallo en la capa de modelos que no es de parseo ni de limites."""


class ErrorDeParseo(ErrorDeAgente):
    """La respuesta del modelo no se pudo convertir en JSON ni tras el reintento.

    Quien la reciba decide que hacer: para un validador es INDETERMINADO y
    cuenta como FALLO; para el arquitecto es motivo de aborto.
    """


class LimiteSuperado(ErrorDeAgente):
    """Se alcanzo el limite de coste o de numero de llamadas."""


# ---------------------------------------------------------------------------
# Lector de .env
# ---------------------------------------------------------------------------


def cargar_dotenv(ruta=None, entorno=None):
    """Carga las variables de un archivo .env en el entorno del proceso.

    Formato aceptado: una linea por variable, `NOMBRE=valor`. Se ignoran las
    lineas vacias y las que empiezan por `#`. Se admite el prefijo `export` y
    las comillas alrededor del valor.

    Regla importante: una variable que YA existe en el entorno NO se pisa. Lo
    que escribes en la terminal manda sobre lo que hay en el archivo, que es lo
    que uno espera al hacer una prueba rapida.

    Devuelve la lista de NOMBRES cargados. Nunca devuelve ni registra valores:
    por aqui pasa la clave de API.
    """
    if ruta is None:
        ruta = RAIZ_PROYECTO / ".env"
    if entorno is None:
        entorno = os.environ

    ruta = Path(ruta)
    if not ruta.is_file():
        return []

    cargadas = []
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        linea = linea.strip()
        if not linea or linea.startswith("#"):
            continue
        if linea.lower().startswith("export "):
            linea = linea[len("export "):].strip()
        if "=" not in linea:
            continue
        nombre, _, valor = linea.partition("=")
        nombre = nombre.strip()
        valor = valor.strip()
        if len(valor) >= 2 and valor[0] == valor[-1] and valor[0] in ("'", '"'):
            valor = valor[1:-1]
        if not nombre or nombre in entorno:
            continue
        entorno[nombre] = valor
        cargadas.append(nombre)

    if cargadas:
        registro.debug("Variables cargadas de .env: %s", ", ".join(cargadas))
    return cargadas


# ---------------------------------------------------------------------------
# Prompts: se leen de disco en tiempo de ejecucion, nunca viven en el codigo
# ---------------------------------------------------------------------------

_cache_prompts = {}


def directorio_prompts(config=None):
    """Ruta absoluta del directorio de prompts."""
    relativa = "./prompts"
    if config:
        relativa = config.get("runtime", {}).get("directorio_prompts", relativa)
    ruta = Path(relativa)
    if not ruta.is_absolute():
        ruta = RAIZ_PROYECTO / ruta
    return ruta


def _leer_prompt(ruta):
    clave = str(ruta)
    if clave not in _cache_prompts:
        if not ruta.is_file():
            raise ErrorDeAgente(
                "No encuentro el prompt de sistema en {0}.\n"
                "Arreglo: comprueba que el archivo existe y que "
                "runtime.directorio_prompts apunta a la carpeta correcta.".format(ruta)
            )
        _cache_prompts[clave] = ruta.read_text(encoding="utf-8")
    return _cache_prompts[clave]


def cargar_prompt(nombre, config=None):
    """Lee prompts/<nombre>.md. Ejemplo: cargar_prompt('arquitecto')."""
    return _leer_prompt(directorio_prompts(config) / (nombre + ".md"))


def cargar_referencia_genero(genero, config=None):
    """Lee prompts/referencias/<genero>.md, las convenciones del genero."""
    return _leer_prompt(
        directorio_prompts(config) / "referencias" / (genero + ".md")
    )


# ---------------------------------------------------------------------------
# Parseo defensivo de JSON (adenda 3.5, pasos 1 a 3)
# ---------------------------------------------------------------------------


def _quitar_vallas(texto):
    """Quita las vallas de bloque de codigo que algunos modelos anaden igual."""
    limpio = texto.strip()
    if limpio.startswith("```"):
        lineas = limpio.splitlines()
        lineas = lineas[1:]                      # la linea ```json
        if lineas and lineas[-1].strip().startswith("```"):
            lineas = lineas[:-1]
        limpio = "\n".join(lineas).strip()
    return limpio


def _primer_bloque_equilibrado(texto):
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
    """Convierte la respuesta de un modelo en un diccionario.

    Tres intentos, en este orden (adenda 3.5):
      1. json.loads directo;
      2. quitando las vallas de bloque de codigo;
      3. extrayendo el primer bloque {...} equilibrado, que sobrevive a
         preambulos del tipo "Aqui tienes el JSON:".

    Si los tres fallan, lanza ErrorDeParseo. El reintento con el modelo (paso 4
    de la adenda) lo hace `ClienteModelos.llamar_json`.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ErrorDeParseo("El modelo devolvio una respuesta vacia.")

    candidatos = [texto, _quitar_vallas(texto)]
    bloque = _primer_bloque_equilibrado(_quitar_vallas(texto))
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

    raise ErrorDeParseo(
        "No he podido interpretar la respuesta como JSON. Detalle: {0}".format(
            ultimo_error
        )
    )


# ---------------------------------------------------------------------------
# Cliente de modelos
# ---------------------------------------------------------------------------

ROLES_VALIDADORES = ("continuidad", "genero", "estilo")


def modelo_para_rol(config, rol, escalon=0):
    """Devuelve {modelo, temperatura, max_tokens} para un rol.

    El escritor es el unico rol con escalera: `escalon` indica que peldano se
    esta usando. Los validadores y el arquitecto tienen un modelo fijo.
    """
    modelos = config.get("modelos", {})

    if rol == "escritor":
        escalera = modelos.get("escalera_escritor") or []
        if not escalera:
            raise ErrorDeAgente(
                "modelos.escalera_escritor esta vacia en config.json: no hay ningun "
                "modelo con el que escribir."
            )
        escalon = max(0, min(escalon, len(escalera) - 1))
        entrada = escalera[escalon]
    elif rol == "arquitecto":
        entrada = modelos.get("arquitecto", {})
    elif rol in ROLES_VALIDADORES:
        entrada = modelos.get("validadores", {})
    else:
        raise ErrorDeAgente("Rol desconocido: {0}.".format(rol))

    if not entrada.get("modelo"):
        raise ErrorDeAgente(
            "Falta el slug de modelo para el rol '{0}' en config.json.".format(rol)
        )

    return {
        "modelo": entrada["modelo"],
        "temperatura": entrada.get("temperatura", 0.7),
        "max_tokens": entrada.get("max_tokens", 4000),
    }


def slugs_configurados(config):
    """Todos los slugs de modelo que la configuracion va a usar, sin repetir."""
    modelos = config.get("modelos", {})
    slugs = []
    for entrada in modelos.get("escalera_escritor") or []:
        if entrada.get("modelo"):
            slugs.append(entrada["modelo"])
    for clave in ("arquitecto", "validadores"):
        slug = modelos.get(clave, {}).get("modelo")
        if slug:
            slugs.append(slug)
    unicos = []
    for slug in slugs:
        if slug not in unicos:
            unicos.append(slug)
    return unicos


class ClienteModelos:
    """Envoltorio sobre el SDK de OpenAI apuntando a OpenRouter.

    Se crea una vez por ejecucion y lleva la cuenta de llamadas y de coste, que
    es lo que permite frenar antes de superar los limites de config.json.

    Para los tests se puede inyectar un cliente falso con `cliente=`: asi se
    prueba toda la logica (reintentos, parseo, limites) sin tocar la red y sin
    necesidad de tener instalado el SDK.
    """

    def __init__(self, config, entorno=None, cliente=None, dormir=time.sleep):
        self.config = config
        self.entorno = entorno if entorno is not None else os.environ
        self._cliente = cliente
        self._dormir = dormir

        proveedor = config.get("proveedor", {})
        self.base_url = proveedor.get("base_url", "https://openrouter.ai/api/v1")
        self.nombre_variable = proveedor.get(
            "variable_entorno_clave", "OPENROUTER_API_KEY"
        )
        self.timeout = proveedor.get("timeout_segundos", 120)
        self.reintentos_red = proveedor.get("reintentos_red", 3)
        self.backoff = proveedor.get("backoff_segundos", 2)

        limites = config.get("limites", {})
        self.coste_max_usd = limites.get("coste_max_usd")
        self.abortar_si_supera_coste = limites.get("abortar_si_supera_coste", True)
        self.llamadas_max_totales = limites.get("llamadas_max_totales")

        self.llamadas = 0
        self.coste_usd = 0.0
        self.tokens_entrada = 0
        self.tokens_salida = 0

    # -- clave y cliente ----------------------------------------------------

    def clave_disponible(self):
        """True si la variable de entorno con la clave existe y no esta vacia.

        No devuelve la clave ni la registra en ningun sitio.
        """
        return bool(str(self.entorno.get(self.nombre_variable, "")).strip())

    def exigir_clave(self):
        if not self.clave_disponible():
            raise ErrorDeAgente(
                "Falta la variable de entorno {0}, que es donde vive la clave de "
                "OpenRouter.\n"
                "Arreglo: definela en tu terminal antes de ejecutar, o ponla en el "
                "archivo .env de la raiz.".format(self.nombre_variable)
            )

    @property
    def cliente(self):
        """Crea el cliente del SDK la primera vez que hace falta.

        La importacion del SDK esta aqui dentro, y no arriba del archivo, para
        que los tests y el cargador de configuracion funcionen sin tenerlo
        instalado.
        """
        if self._cliente is None:
            self.exigir_clave()
            try:
                from openai import OpenAI
            except ImportError as error:
                raise ErrorDeAgente(
                    "Falta el SDK de OpenAI, que es el cliente con el que se habla "
                    "con OpenRouter.\n"
                    "Arreglo: python -m pip install openai"
                ) from error
            self._cliente = OpenAI(
                base_url=self.base_url,
                api_key=self.entorno[self.nombre_variable],
                timeout=self.timeout,
            )
        return self._cliente

    # -- limites ------------------------------------------------------------

    def comprobar_limites(self):
        """Se llama ANTES de cada peticion, nunca despues.

        Un bucle de reintentos mal cerrado quema credito muy rapido, asi que la
        comprobacion va delante: mas vale no hacer la llamada que descubrir el
        exceso cuando ya esta pagada.
        """
        if (
            self.llamadas_max_totales is not None
            and self.llamadas >= self.llamadas_max_totales
        ):
            raise LimiteSuperado(
                "Se ha alcanzado el limite de {0} llamadas (limites."
                "llamadas_max_totales). La ejecucion se detiene aqui de forma "
                "ordenada.".format(self.llamadas_max_totales)
            )

        if self.coste_max_usd is not None and self.coste_usd >= self.coste_max_usd:
            mensaje = (
                "El coste acumulado ({0:.4f} USD) ha alcanzado el limite de {1} USD "
                "(limites.coste_max_usd).".format(self.coste_usd, self.coste_max_usd)
            )
            if self.abortar_si_supera_coste:
                raise LimiteSuperado(
                    mensaje + " La ejecucion se detiene aqui de forma ordenada."
                )
            registro.warning("%s Continuo porque abortar_si_supera_coste es false.", mensaje)

    # -- llamada ------------------------------------------------------------

    def _contabilizar(self, respuesta):
        """Suma tokens y coste de una respuesta, si el proveedor los informa."""
        uso = getattr(respuesta, "usage", None)
        if uso is None:
            return
        self.tokens_entrada += getattr(uso, "prompt_tokens", 0) or 0
        self.tokens_salida += getattr(uso, "completion_tokens", 0) or 0
        # OpenRouter devuelve el coste real en usage.cost cuando se pide
        # contabilidad de uso. Si el proveedor no lo informa, se queda a cero y
        # el limite de llamadas sigue siendo la red de seguridad.
        coste = getattr(uso, "cost", None)
        if coste is None and isinstance(uso, dict):
            coste = uso.get("cost")
        if coste:
            self.coste_usd += float(coste)

    def llamar(self, prompt_sistema, prompt_usuario, modelo, temperatura,
               max_tokens, rol="desconocido"):
        """Una llamada de completado. Devuelve el texto de la respuesta.

        Reintenta los fallos de red `reintentos_red` veces con espera creciente
        (2, 4, 8 segundos con la configuracion por defecto). Un error que no es
        de red no se reintenta: reintentar un slug invalido solo pierde tiempo.
        """
        self.comprobar_limites()

        # El cliente se resuelve ANTES del bucle de reintentos: que falte el SDK
        # o la clave no es un fallo de red y no tiene ningun sentido reintentarlo
        # tres veces con espera creciente.
        conexion = self.cliente

        mensajes = [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": prompt_usuario},
        ]

        ultimo_error = None
        for intento in range(1, self.reintentos_red + 1):
            try:
                respuesta = conexion.chat.completions.create(
                    model=modelo,
                    messages=mensajes,
                    temperature=temperatura,
                    max_tokens=max_tokens,
                    extra_body={"usage": {"include": True}},
                )
            except Exception as error:  # noqa: BLE001 - el SDK lanza de todo
                ultimo_error = error
                if intento >= self.reintentos_red:
                    break
                espera = self.backoff * (2 ** (intento - 1))
                registro.warning(
                    "Fallo de red llamando a %s (rol %s), intento %d de %d. "
                    "Reintento en %ss. Detalle: %s",
                    modelo, rol, intento, self.reintentos_red, espera, error,
                )
                self._dormir(espera)
                continue

            self.llamadas += 1
            self._contabilizar(respuesta)

            try:
                texto = respuesta.choices[0].message.content
            except (AttributeError, IndexError, TypeError) as error:
                raise ErrorDeAgente(
                    "La respuesta de {0} no tiene el formato esperado.".format(modelo)
                ) from error

            registro.info(
                "Llamada %d | rol=%s | modelo=%s | caracteres=%d | coste acumulado=%.4f USD",
                self.llamadas, rol, modelo, len(texto or ""), self.coste_usd,
            )
            return texto or ""

        raise ErrorDeAgente(
            "No he podido hablar con el modelo {0} (rol {1}) tras {2} intentos.\n"
            "Detalle: {3}\n"
            "Arreglo: comprueba tu conexion, el slug del modelo y el saldo de "
            "OpenRouter.".format(modelo, rol, self.reintentos_red, ultimo_error)
        )

    def llamar_json(self, prompt_sistema, prompt_usuario, modelo, temperatura,
                    max_tokens, rol="desconocido", reintentos_parseo=1):
        """Como `llamar`, pero exige que la respuesta sea un objeto JSON.

        Si no parsea, repite la llamada anadiendo al mensaje de usuario el error
        de parseo, tantas veces como diga `reintentos_parseo` (uno por defecto,
        segun validacion.reintentos_parseo_json). Si sigue sin parsear, lanza
        ErrorDeParseo y decide quien llama: para un validador eso es
        INDETERMINADO y cuenta como FALLO, jamas como PASA.

        Devuelve (datos, texto_crudo).
        """
        mensaje = prompt_usuario
        ultimo_error = None

        for intento in range(reintentos_parseo + 1):
            texto = self.llamar(
                prompt_sistema, mensaje, modelo, temperatura, max_tokens, rol
            )
            try:
                return extraer_json(texto), texto
            except ErrorDeParseo as error:
                ultimo_error = error
                registro.warning(
                    "Respuesta no parseable de %s (rol %s), intento de parseo %d. %s",
                    modelo, rol, intento + 1, error,
                )
                mensaje = (
                    prompt_usuario
                    + "\n\nERROR_DE_PARSEO: tu respuesta anterior no era JSON valido. "
                    + str(error)
                    + " Responde otra vez con un unico objeto JSON: el primer caracter "
                    "tiene que ser una llave de apertura y el ultimo una de cierre, "
                    "sin texto alrededor y sin bloque de codigo."
                )

        raise ErrorDeParseo(
            "El modelo {0} (rol {1}) no ha devuelto JSON parseable ni tras el "
            "reintento. Ultimo detalle: {2}".format(modelo, rol, ultimo_error)
        )

    # -- diagnostico --------------------------------------------------------

    def catalogo_de_modelos(self):
        """Pide a OpenRouter la lista de slugs disponibles."""
        try:
            catalogo = self.cliente.models.list()
        except ErrorDeAgente:
            # Falta el SDK o la clave: ese mensaje ya es claro, no lo envuelvo.
            raise
        except Exception as error:  # noqa: BLE001
            raise ErrorDeAgente(
                "No he podido leer el catalogo de modelos de OpenRouter.\n"
                "Detalle: {0}\n"
                "Arreglo: comprueba tu conexion y que la clave es valida.".format(error)
            ) from error
        return {modelo.id for modelo in catalogo.data}

    def verificar_slugs(self):
        """Comprueba que todos los slugs de config.json existen en OpenRouter.

        Un slug invalido no falla al arrancar sino en mitad de la generacion, y
        para entonces ya has pagado los capitulos anteriores. Por eso se
        comprueba por adelantado.
        """
        disponibles = self.catalogo_de_modelos()
        configurados = slugs_configurados(self.config)
        faltan = [slug for slug in configurados if slug not in disponibles]
        return configurados, faltan


def probar_conexion(config, entorno=None, salida=print):
    """Prueba de conexion de EJECUCION.md 2.3. Devuelve True si todo va bien.

    Tres comprobaciones, de la mas barata a la mas cara:
      1. la clave de API existe;
      2. todos los slugs de config.json estan en el catalogo de OpenRouter;
      3. una llamada minima al primer modelo de la escalera responde.
    """
    cargar_dotenv(entorno=entorno)
    cliente = ClienteModelos(config, entorno=entorno)

    salida("1. Clave de API...")
    if not cliente.clave_disponible():
        salida(
            "   FALLO: falta la variable de entorno {0}.\n"
            "   Arreglo: definela en la terminal o en el archivo .env de la "
            "raiz.".format(cliente.nombre_variable)
        )
        return False
    salida("   OK: la variable {0} esta definida.".format(cliente.nombre_variable))

    salida("2. Slugs de modelo contra el catalogo de OpenRouter...")
    try:
        configurados, faltan = cliente.verificar_slugs()
    except ErrorDeAgente as error:
        salida("   FALLO: {0}".format(error))
        return False
    for slug in configurados:
        marca = "NO EXISTE" if slug in faltan else "ok"
        salida("   {0:<45} {1}".format(slug, marca))
    if faltan:
        salida(
            "   FALLO: {0} slug(s) no existen en OpenRouter.\n"
            "   Arreglo: los slugs cambian a menudo. Busca el vigente en "
            "openrouter.ai/models y corrige config.json.".format(len(faltan))
        )
        return False

    salida("3. Llamada minima al primer modelo de la escalera...")
    try:
        eleccion = modelo_para_rol(config, "escritor", escalon=0)
        texto = cliente.llamar(
            prompt_sistema=PING_DE_DIAGNOSTICO,
            prompt_usuario=PING_DE_DIAGNOSTICO,
            modelo=eleccion["modelo"],
            temperatura=0,
            max_tokens=16,
            rol="diagnostico",
        )
    except ErrorDeAgente as error:
        salida("   FALLO: {0}".format(error))
        return False
    salida("   OK: {0} responde {1}".format(eleccion["modelo"], repr(texto.strip())))
    salida(
        "\nTodo correcto. Llamadas hechas: {0}. Coste acumulado: {1:.4f} USD.".format(
            cliente.llamadas, cliente.coste_usd
        )
    )
    return True


def _main():
    """Punto de entrada de `python -m src.agentes --probar-conexion`."""
    import argparse

    from src.config import cargar_config

    analizador = argparse.ArgumentParser(
        description="Capa de modelos del harness. Sin argumentos no hace nada."
    )
    analizador.add_argument(
        "--probar-conexion",
        action="store_true",
        help="Comprueba la clave, los slugs de modelo y una llamada minima.",
    )
    argumentos = analizador.parse_args()

    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(message)s")

    if not argumentos.probar_conexion:
        analizador.print_help()
        return 0

    cargar_dotenv()
    config = cargar_config(volcar=False)
    return 0 if probar_conexion(config) else 1


if __name__ == "__main__":
    raise SystemExit(_main())
