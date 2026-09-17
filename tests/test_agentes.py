"""Tests de la capa de modelos.

NINGUN test toca la red. Se inyecta un cliente falso en `ClienteModelos`, de
modo que se prueba toda la logica (parseo defensivo, reintentos, limites) sin
peticiones y sin necesidad de tener instalado el SDK de OpenAI.
"""

import pytest

from src import agentes
from tests.ayudas import config_minima

ENTORNO = {"OPENROUTER_API_KEY": "clave-de-prueba"}


# ---------------------------------------------------------------------------
# Cliente falso
# ---------------------------------------------------------------------------


class _Uso:
    def __init__(self, coste=0.0):
        self.prompt_tokens = 100
        self.completion_tokens = 50
        self.cost = coste


class _Mensaje:
    def __init__(self, contenido):
        self.content = contenido


class _Eleccion:
    def __init__(self, contenido):
        self.message = _Mensaje(contenido)


class _Respuesta:
    def __init__(self, contenido, coste=0.0):
        self.choices = [_Eleccion(contenido)]
        self.usage = _Uso(coste)


class ClienteFalso:
    """Imita `cliente.chat.completions.create`.

    Se le pasa una lista de respuestas. Cada elemento puede ser un texto (lo
    devuelve) o una excepcion (la lanza), que es como se simula un fallo de red.
    """

    def __init__(self, respuestas, coste_por_llamada=0.0):
        self._respuestas = list(respuestas)
        self._coste = coste_por_llamada
        self.peticiones = []

        cliente = self

        class _Completions:
            def create(self, **kwargs):
                cliente.peticiones.append(kwargs)
                if not cliente._respuestas:
                    raise AssertionError("El cliente falso se ha quedado sin respuestas")
                siguiente = cliente._respuestas.pop(0)
                if isinstance(siguiente, Exception):
                    raise siguiente
                return _Respuesta(siguiente, cliente._coste)

        class _Chat:
            completions = _Completions()

        self.chat = _Chat()


def cliente_con(respuestas, config=None, **extra):
    config = config or config_minima()
    return agentes.ClienteModelos(
        config,
        entorno=dict(ENTORNO),
        cliente=ClienteFalso(respuestas, **extra),
        dormir=lambda segundos: None,   # los tests no esperan de verdad
    )


def llamar(cliente, prompt_usuario="hola"):
    return cliente.llamar(
        prompt_sistema="sistema",
        prompt_usuario=prompt_usuario,
        modelo="proveedor/barato",
        temperatura=0.8,
        max_tokens=100,
        rol="prueba",
    )


# ---------------------------------------------------------------------------
# Lector de .env
# ---------------------------------------------------------------------------


def test_dotenv_carga_las_variables(tmp_path):
    archivo = tmp_path / ".env"
    archivo.write_text(
        "# un comentario\n"
        "\n"
        "OPENROUTER_API_KEY=abc123\n"
        'export OTRA="con comillas"\n',
        encoding="utf-8",
    )
    entorno = {}

    cargadas = agentes.cargar_dotenv(archivo, entorno)

    assert cargadas == ["OPENROUTER_API_KEY", "OTRA"]
    assert entorno["OPENROUTER_API_KEY"] == "abc123"
    assert entorno["OTRA"] == "con comillas"


def test_dotenv_no_pisa_lo_que_ya_hay_en_el_entorno(tmp_path):
    """Lo que escribes en la terminal manda sobre el archivo."""
    archivo = tmp_path / ".env"
    archivo.write_text("OPENROUTER_API_KEY=del-archivo\n", encoding="utf-8")
    entorno = {"OPENROUTER_API_KEY": "de-la-terminal"}

    cargadas = agentes.cargar_dotenv(archivo, entorno)

    assert cargadas == []
    assert entorno["OPENROUTER_API_KEY"] == "de-la-terminal"


def test_dotenv_sin_archivo_no_falla(tmp_path):
    assert agentes.cargar_dotenv(tmp_path / "no-existe", {}) == []


def test_dotenv_no_devuelve_valores(tmp_path):
    """Comprobacion de seguridad: por aqui pasa la clave de API."""
    archivo = tmp_path / ".env"
    archivo.write_text("OPENROUTER_API_KEY=secreto\n", encoding="utf-8")

    cargadas = agentes.cargar_dotenv(archivo, {})

    assert "secreto" not in "".join(cargadas)


# ---------------------------------------------------------------------------
# Parseo defensivo (adenda 3.5)
# ---------------------------------------------------------------------------


def test_parseo_de_json_limpio():
    assert agentes.extraer_json('{"veredicto": "PASA"}') == {"veredicto": "PASA"}


def test_parseo_con_backticks():
    respuesta = '```json\n{"veredicto": "PASA", "problemas": []}\n```'

    assert agentes.extraer_json(respuesta)["veredicto"] == "PASA"


def test_parseo_con_preambulo():
    respuesta = 'Claro, aqui tienes el JSON que me pides:\n\n{"veredicto": "FALLO"}'

    assert agentes.extraer_json(respuesta)["veredicto"] == "FALLO"


def test_parseo_con_preambulo_y_backticks_y_epilogo():
    respuesta = (
        "Aqui tienes el resultado:\n"
        '```json\n{"veredicto": "FALLO", "problemas": [{"gravedad": "alta"}]}\n```\n'
        "Espero que te sirva."
    )

    datos = agentes.extraer_json(respuesta)

    assert datos["problemas"][0]["gravedad"] == "alta"


def test_parseo_no_se_confunde_con_llaves_dentro_de_un_texto():
    respuesta = '{"hecho": "escribio } en la pared", "capitulo": 1}'

    assert agentes.extraer_json(respuesta)["capitulo"] == 1


def test_json_roto_lanza_error_de_parseo():
    with pytest.raises(agentes.ErrorDeParseo):
        agentes.extraer_json('{"veredicto": "PASA", ')


def test_respuesta_vacia_lanza_error_de_parseo():
    with pytest.raises(agentes.ErrorDeParseo):
        agentes.extraer_json("   ")


def test_json_valido_pero_que_no_es_un_objeto_lanza_error():
    with pytest.raises(agentes.ErrorDeParseo):
        agentes.extraer_json("[1, 2, 3]")


# ---------------------------------------------------------------------------
# llamar_json: el reintento del paso 4 de la adenda
# ---------------------------------------------------------------------------


def test_llamar_json_reintenta_una_vez_y_lo_consigue():
    cliente = cliente_con(["esto no es json", '{"veredicto": "PASA"}'])

    datos, _ = cliente.llamar_json(
        "sistema", "mensaje", "proveedor/barato", 0.1, 100, "estilo",
        reintentos_parseo=1,
    )

    assert datos == {"veredicto": "PASA"}
    assert cliente.llamadas == 2


def test_el_reintento_le_dice_al_modelo_cual_fue_el_error():
    cliente = cliente_con(["esto no es json", '{"veredicto": "PASA"}'])

    cliente.llamar_json(
        "sistema", "mensaje", "proveedor/barato", 0.1, 100, "estilo",
        reintentos_parseo=1,
    )

    segundo_mensaje = cliente._cliente.peticiones[1]["messages"][1]["content"]
    assert "ERROR_DE_PARSEO" in segundo_mensaje
    assert "mensaje" in segundo_mensaje


def test_si_falla_tambien_el_reintento_lanza_error_de_parseo():
    """Un validador que no parsea es FALLO, jamas PASA. Aqui nace esa regla."""
    cliente = cliente_con(["nada de json", "sigue sin ser json"])

    with pytest.raises(agentes.ErrorDeParseo):
        cliente.llamar_json(
            "sistema", "mensaje", "proveedor/barato", 0.1, 100, "continuidad",
            reintentos_parseo=1,
        )

    assert cliente.llamadas == 2


# ---------------------------------------------------------------------------
# Reintentos de red con backoff
# ---------------------------------------------------------------------------


def test_reintenta_los_fallos_de_red_y_acaba_respondiendo():
    cliente = cliente_con(
        [ConnectionError("cae la red"), ConnectionError("otra vez"), "por fin"]
    )

    assert llamar(cliente) == "por fin"
    assert cliente.llamadas == 1        # solo cuenta la que respondio


def test_agotados_los_reintentos_de_red_falla_con_mensaje_claro():
    cliente = cliente_con([ConnectionError("cae")] * 3)

    with pytest.raises(agentes.ErrorDeAgente) as error:
        llamar(cliente)

    assert "tras 3 intentos" in str(error.value)


def test_la_espera_entre_reintentos_va_creciendo():
    esperas = []
    config = config_minima()
    config["proveedor"]["backoff_segundos"] = 2
    cliente = agentes.ClienteModelos(
        config,
        entorno=dict(ENTORNO),
        cliente=ClienteFalso([ConnectionError("a"), ConnectionError("b"), "ok"]),
        dormir=esperas.append,
    )

    llamar(cliente)

    assert esperas == [2, 4]


# ---------------------------------------------------------------------------
# Limites de coste y de llamadas
# ---------------------------------------------------------------------------


def test_se_detiene_al_alcanzar_el_limite_de_llamadas():
    config = config_minima()
    config["limites"]["llamadas_max_totales"] = 2
    cliente = cliente_con(["uno", "dos", "tres"], config=config)

    llamar(cliente)
    llamar(cliente)

    with pytest.raises(agentes.LimiteSuperado) as error:
        llamar(cliente)

    assert "limite de 2 llamadas" in str(error.value)
    assert cliente.llamadas == 2        # la tercera nunca llego a hacerse


def test_se_detiene_al_alcanzar_el_limite_de_coste():
    config = config_minima()
    config["limites"]["coste_max_usd"] = 0.05
    cliente = cliente_con(["uno", "dos"], config=config, coste_por_llamada=0.04)

    llamar(cliente)                      # coste acumulado 0.04, por debajo
    llamar(cliente)                      # coste acumulado 0.08, por encima

    with pytest.raises(agentes.LimiteSuperado) as error:
        llamar(cliente)

    assert "coste_max_usd" in str(error.value)


def test_con_abortar_desactivado_el_coste_solo_avisa():
    config = config_minima()
    config["limites"]["coste_max_usd"] = 0.01
    config["limites"]["abortar_si_supera_coste"] = False
    cliente = cliente_con(["uno", "dos"], config=config, coste_por_llamada=0.04)

    llamar(cliente)
    llamar(cliente)                      # no lanza, solo registra un aviso

    assert cliente.llamadas == 2


def test_los_limites_se_comprueban_antes_de_llamar():
    """Mas vale no hacer la llamada que descubrir el exceso ya pagada."""
    config = config_minima()
    config["limites"]["llamadas_max_totales"] = 0
    cliente = cliente_con(["no deberia usarse"], config=config)

    with pytest.raises(agentes.LimiteSuperado):
        llamar(cliente)

    assert cliente._cliente.peticiones == []


def test_el_coste_se_acumula_entre_llamadas():
    cliente = cliente_con(["uno", "dos"], coste_por_llamada=0.01)

    llamar(cliente)
    llamar(cliente)

    assert cliente.coste_usd == pytest.approx(0.02)
    assert cliente.tokens_entrada == 200


# ---------------------------------------------------------------------------
# Clave de API
# ---------------------------------------------------------------------------


def test_sin_clave_exigir_clave_falla_con_mensaje_claro():
    cliente = agentes.ClienteModelos(config_minima(), entorno={})

    with pytest.raises(agentes.ErrorDeAgente) as error:
        cliente.exigir_clave()

    assert "OPENROUTER_API_KEY" in str(error.value)


def test_con_clave_no_falla():
    cliente = agentes.ClienteModelos(config_minima(), entorno=dict(ENTORNO))

    assert cliente.clave_disponible() is True
    cliente.exigir_clave()


# ---------------------------------------------------------------------------
# Eleccion de modelo por rol
# ---------------------------------------------------------------------------


def test_el_escritor_usa_el_peldano_pedido_de_la_escalera():
    config = config_minima()

    assert agentes.modelo_para_rol(config, "escritor", 0)["modelo"] == "proveedor/barato"
    assert agentes.modelo_para_rol(config, "escritor", 1)["modelo"] == "proveedor/medio"


def test_un_peldano_fuera_de_rango_se_queda_en_el_ultimo():
    config = config_minima()

    assert agentes.modelo_para_rol(config, "escritor", 9)["modelo"] == "proveedor/medio"


def test_los_tres_validadores_comparten_modelo_y_temperatura():
    """Si cambiaran de modelo, las puntuaciones dejarian de ser comparables."""
    config = config_minima()

    elecciones = [
        agentes.modelo_para_rol(config, rol) for rol in agentes.ROLES_VALIDADORES
    ]

    assert {e["modelo"] for e in elecciones} == {"proveedor/validador"}
    assert {e["temperatura"] for e in elecciones} == {0.1}


def test_slugs_configurados_no_repite():
    config = config_minima()
    config["modelos"]["arquitecto"]["modelo"] = "proveedor/medio"

    assert agentes.slugs_configurados(config) == [
        "proveedor/barato",
        "proveedor/medio",
        "proveedor/validador",
    ]


# ---------------------------------------------------------------------------
# Prompts: se leen de disco, no viven en el codigo
# ---------------------------------------------------------------------------


def test_los_prompts_se_leen_del_directorio_de_prompts():
    texto = agentes.cargar_prompt("arquitecto")

    assert "JSON" in texto


def test_la_referencia_de_genero_se_lee_del_subdirectorio():
    texto = agentes.cargar_referencia_genero("terror")

    assert len(texto) > 100


def test_un_prompt_inexistente_falla_con_mensaje_claro():
    with pytest.raises(agentes.ErrorDeAgente) as error:
        agentes.cargar_prompt("no-existe")

    assert "No encuentro el prompt" in str(error.value)
