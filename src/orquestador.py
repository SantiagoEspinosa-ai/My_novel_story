"""Orquestador: el bucle principal del harness.

ESTADO DE ESTA ETAPA (4 del orden de implementacion): pipeline minimo de
extremo a extremo, SIN validadores.

    arquitecto -> biblia -> escritor capitulo a capitulo -> salida/capitulos/

Lo que todavia NO hace, y llega en etapas posteriores:

    - lanzar los tres validadores en paralelo (etapas 6 y 8);
    - el bucle de reescritura con la lista acumulada de problemas (etapa 6);
    - la escalera de modelos y la puntuacion (etapa 7): aqui se usa siempre el
      primer modelo de `escalera_escritor`;
    - los resumenes redactados por un modelo (de momento se usa la sinopsis del
      outline, que es determinista y no cuesta nada);
    - el ensamblado del manuscrito y el informe (etapa 10).

El orquestador decide, no razona: aqui no hay ni una linea de prompt. Los
prompts viven en prompts/ y los carga `src.agentes`.
"""

from __future__ import annotations

import logging
import sys

from src import agentes, biblia as modulo_biblia, contexto, estado as modulo_estado
from src.config import ErrorDeConfiguracion, cargar_config, ruta_salida

registro = logging.getLogger("orquestador")

NIVELES = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


def configurar_log(config):
    nivel = config.get("runtime", {}).get("nivel_log", "info")
    logging.basicConfig(
        level=NIVELES.get(str(nivel).lower(), logging.INFO),
        format="%(asctime)s %(levelname)-7s %(message)s",
        datefmt="%H:%M:%S",
    )


# ---------------------------------------------------------------------------
# Archivos de capitulo
# ---------------------------------------------------------------------------


def directorio_capitulos(directorio_salida):
    return directorio_salida / "capitulos"


def ruta_capitulo(directorio_salida, numero):
    return directorio_capitulos(directorio_salida) / "cap-{0:02d}.md".format(numero)


def guardar_capitulo(directorio_salida, numero, texto):
    destino = ruta_capitulo(directorio_salida, numero)
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto.rstrip() + "\n", encoding="utf-8")
    return destino


def leer_capitulo(directorio_salida, numero):
    """Devuelve el texto de un capitulo ya generado, o None si no existe.

    Se lee de disco y no de memoria para que la reanudacion funcione: tras
    relanzar el proceso, el capitulo N-1 tiene que seguir estando disponible
    para la ventana del escritor.
    """
    origen = ruta_capitulo(directorio_salida, numero)
    if not origen.is_file():
        return None
    return origen.read_text(encoding="utf-8")


def resumenes_provisionales(biblia):
    """Resumen de cada capitulo a partir de la sinopsis del outline.

    Provisional: el resumen de verdad (2-3 frases sobre lo que acabo pasando
    de verdad en el texto) lo redactara un modelo cuando exista el bucle de
    aprobacion. Usar la sinopsis mientras tanto es determinista, no cuesta
    dinero y mantiene la ventana del escritor con la forma definitiva.
    """
    return {
        entrada["capitulo"]: entrada.get("sinopsis", "")
        for entrada in biblia.get("outline", [])
        if isinstance(entrada.get("capitulo"), int)
    }


# ---------------------------------------------------------------------------
# Paso 4: el arquitecto
# ---------------------------------------------------------------------------


def generar_biblia(cliente, config):
    """Llama al arquitecto y valida su salida contra el contrato 7.1.

    Dos intentos como mucho. En el segundo se le devuelve al modelo el error
    concreto: normalmente es un outline con un capitulo de mas o de menos, y
    con el mensaje delante lo corrige. Si el segundo tampoco vale, se aborta:
    sin biblia no hay novela que escribir.
    """
    eleccion = agentes.modelo_para_rol(config, "arquitecto")
    prompt_sistema = agentes.cargar_prompt("arquitecto", config)
    ventana = contexto.ventana_arquitecto(config)
    num_capitulos = config.get("estructura", {}).get("num_capitulos")

    mensaje = ventana.texto
    ultimo_error = None

    for intento in (1, 2):
        registro.info(
            "Arquitecto: intento %d con %s", intento, eleccion["modelo"]
        )
        try:
            datos, _ = cliente.llamar_json(
                prompt_sistema=prompt_sistema,
                prompt_usuario=mensaje,
                modelo=eleccion["modelo"],
                temperatura=eleccion["temperatura"],
                max_tokens=eleccion["max_tokens"],
                rol="arquitecto",
                reintentos_parseo=0,
            )
        except agentes.ErrorDeParseo as error:
            ultimo_error = error
            mensaje = ventana.texto + "\n\nERROR_ANTERIOR: " + str(error)
            continue

        try:
            return modulo_biblia.validar(
                modulo_biblia.normalizar(datos), num_capitulos
            )
        except modulo_biblia.ErrorDeBiblia as error:
            ultimo_error = error
            registro.warning("La biblia no valida en el intento %d.", intento)
            mensaje = ventana.texto + "\n\nERROR_ANTERIOR: " + str(error)

    raise SystemExit(
        "ABORTADO: el arquitecto no ha devuelto una biblia valida ni tras el "
        "reintento.\n{0}\n"
        "Arreglo: prueba con otro modelo de arquitecto en config.json, o baja "
        "num_capitulos.".format(ultimo_error)
    )


# ---------------------------------------------------------------------------
# Paso 5: el bucle de capitulos
# ---------------------------------------------------------------------------


def escribir_capitulo(cliente, config, biblia, numero, resumenes, directorio_salida):
    """Genera un capitulo y lo guarda. Devuelve el texto, o None si fallo.

    Sin validadores todavia: lo que salga del escritor se guarda tal cual.
    """
    eleccion = agentes.modelo_para_rol(config, "escritor", escalon=0)
    prompt_sistema = agentes.cargar_prompt("escritor", config)

    ventana = contexto.ventana_escritor(
        config=config,
        biblia=biblia,
        capitulo=numero,
        resumenes=resumenes,
        texto_anterior=leer_capitulo(directorio_salida, numero - 1),
    )
    if ventana.recortes:
        registro.warning(
            "Capitulo %d: recortes de contexto aplicados: %s",
            numero, "; ".join(ventana.recortes),
        )

    texto = cliente.llamar(
        prompt_sistema=prompt_sistema,
        prompt_usuario=ventana.texto,
        modelo=eleccion["modelo"],
        temperatura=eleccion["temperatura"],
        max_tokens=eleccion["max_tokens"],
        rol="escritor",
    )
    destino = guardar_capitulo(directorio_salida, numero, texto)
    registro.info(
        "Capitulo %d guardado en %s (%d palabras)",
        numero, destino, len(texto.split()),
    )
    return texto


def ejecutar(config):
    """El flujo completo de EJECUCION.md, con lo implementado hasta esta etapa."""
    directorio_salida = ruta_salida(config)
    directorio_salida.mkdir(parents=True, exist_ok=True)
    num_capitulos = config["estructura"]["num_capitulos"]

    # Paso 2: verificar el entorno antes de gastar una sola llamada.
    cliente = agentes.ClienteModelos(config)
    cliente.exigir_clave()
    configurados, faltan = cliente.verificar_slugs()
    if faltan:
        raise SystemExit(
            "ABORTADO: estos slugs de modelo no existen en OpenRouter: {0}.\n"
            "Arreglo: los slugs cambian a menudo. Busca el vigente en "
            "openrouter.ai/models y corrige config.json.".format(", ".join(faltan))
        )
    registro.info("Entorno verificado. Modelos configurados: %s", ", ".join(configurados))

    # Paso 3: reanudar si procede.
    estado, reanudado = modulo_estado.cargar_o_nuevo(config, directorio_salida)
    if reanudado:
        registro.info(
            "Reanudando ejecucion anterior: %s",
            modulo_estado.resumen_legible(estado, num_capitulos),
        )

    # Paso 4: la biblia.
    if reanudado and modulo_biblia.existe(directorio_salida):
        biblia = modulo_biblia.cargar(directorio_salida, num_capitulos)
        registro.info("Biblia cargada de disco: %s", biblia.get("titulo"))
    else:
        biblia = generar_biblia(cliente, config)
        modulo_biblia.guardar(biblia, directorio_salida)
        registro.info(
            "Biblia creada: %s (%d personajes, %d capitulos en el outline)",
            biblia.get("titulo"),
            len(biblia.get("personajes", [])),
            len(biblia.get("outline", [])),
        )

    # Paso 5: los capitulos.
    resumenes = resumenes_provisionales(biblia)
    pendientes = modulo_estado.capitulos_pendientes(estado, num_capitulos)
    registro.info("Capitulos por generar: %s", pendientes or "ninguno")

    for numero in pendientes:
        modulo_estado.empezar_capitulo(
            estado, numero, agentes.modelo_para_rol(config, "escritor")["modelo"]
        )
        modulo_estado.registrar_intento(estado)
        modulo_estado.guardar(estado, directorio_salida)

        try:
            escribir_capitulo(
                cliente, config, biblia, numero, resumenes, directorio_salida
            )
        except agentes.LimiteSuperado as error:
            # Parada ordenada: el estado ya esta en disco, asi que al relanzar
            # se retoma justo aqui sin repetir nada de lo pagado.
            registro.error("%s", error)
            modulo_estado.guardar(estado, directorio_salida)
            break
        except agentes.ErrorDeAgente as error:
            # Regla inviolable: ningun capitulo detiene la generacion. Sigo con
            # el siguiente. El capitulo NO se marca como hecho: se queda
            # pendiente, y al relanzar se vuelve a intentar. Marcarlo dejaria un
            # agujero permanente en el manuscrito por un fallo de red pasajero.
            registro.error(
                "Capitulo %d no generado: %s\n"
                "Sigo con el siguiente. Relanza el comando para reintentar este.",
                numero, error,
            )
            continue

        # TODO (etapa 6): aqui va la validacion en paralelo y, solo si los tres
        # PASAN, la actualizacion de biblia, resumenes y memoria de estilo.
        modulo_estado.aprobar_capitulo(estado, numero)
        modulo_estado.guardar(estado, directorio_salida)

    registro.info(
        "Fin. %s. Llamadas: %d. Coste acumulado: %.4f USD.",
        modulo_estado.resumen_legible(estado, num_capitulos),
        cliente.llamadas,
        cliente.coste_usd,
    )
    registro.info(
        "Los capitulos estan en %s. El manuscrito y el informe llegan en la etapa 10.",
        directorio_capitulos(directorio_salida),
    )
    return estado


def main():
    agentes.cargar_dotenv()
    try:
        config = cargar_config()
    except ErrorDeConfiguracion as error:
        print(error, file=sys.stderr)
        return 1

    configurar_log(config)

    try:
        ejecutar(config)
    except agentes.ErrorDeAgente as error:
        print(error, file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        registro.warning(
            "Interrumpido. El progreso esta guardado: relanza el mismo comando "
            "para continuar desde donde se quedo."
        )
        return 130
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
