"""Tests del filtro de redaccion.

Ninguno toca la red ni el config.json real: el que comprueba el volcado escribe
su propia configuracion en una carpeta temporal y le pasa a `cargar_config` un
diccionario de entorno inventado, igual que hacen los tests de configuracion.
"""

import json

from src.config import cargar_config
from src.redaccion import MARCA, es_clave_sensible, redactar


# ---------------------------------------------------------------------------
# Que nombres se consideran sensibles
# ---------------------------------------------------------------------------


def test_reconoce_los_cinco_patrones():
    """Los cinco patrones que el filtro tiene que cubrir, uno por uno."""
    for nombre in ("api_key", "auth_token", "client_secret", "authorization",
                   "credential_id"):
        assert es_clave_sensible(nombre), nombre


def test_no_distingue_mayusculas():
    """El mismo nombre, escrito de las tres formas habituales."""
    assert es_clave_sensible("LANGFUSE_AUTH_BASIC")
    assert es_clave_sensible("langfuse_auth_basic")
    assert es_clave_sensible("LangfuseAuthBasic")


def test_los_ajustes_normales_no_son_sensibles():
    """Ningun ajuste real del harness puede caer en el filtro por accidente."""
    for nombre in ("num_capitulos", "genero", "palabras_min", "escalera_escritor",
                   "directorio_salida", "pesos_gravedad", "titulo"):
        assert not es_clave_sensible(nombre), nombre


def test_los_contadores_de_tokens_estan_exentos():
    """`token` aqui significa token de modelo, no credencial.

    Sin la exencion, `max_tokens_contexto` salia redactado del volcado de la
    configuracion efectiva, que es un ajuste real y hace falta para reproducir
    una generacion.
    """
    for nombre in ("max_tokens_contexto", "tokens", "tokens_in", "tokens_out",
                   "sin_tokens"):
        assert not es_clave_sensible(nombre), nombre


def test_la_exencion_es_por_nombre_exacto_y_no_por_patron():
    """Una clave parecida pero distinta sigue cayendo en el filtro.

    Si la exencion fuese por subcadena, `token` dejaria de redactarse en
    cualquier sitio y el filtro no serviria de nada.
    """
    assert es_clave_sensible("langfuse_tokens_in")
    assert es_clave_sensible("tokens_de_acceso")


def test_una_clave_que_no_es_texto_no_revienta():
    """Un diccionario de Python admite claves que no son cadenas."""
    assert not es_clave_sensible(3)
    assert not es_clave_sensible(None)


# ---------------------------------------------------------------------------
# Que hace el filtro con una estructura
# ---------------------------------------------------------------------------


def test_enmascara_el_valor_y_conserva_la_clave():
    """La clave sigue visible: hay que poder ver QUE se redacto."""
    assert redactar({"api_key": "sk-lo-que-sea"}) == {"api_key": MARCA}


def test_baja_por_los_diccionarios_anidados():
    salida = redactar({"runtime": {"nivel_log": "info", "auth_basic": "xxx"}})
    assert salida == {"runtime": {"nivel_log": "info", "auth_basic": MARCA}}


def test_baja_por_las_listas_de_diccionarios():
    salida = redactar({"conexiones": [{"nombre": "a", "token": "t"}]})
    assert salida == {"conexiones": [{"nombre": "a", "token": MARCA}]}


def test_enmascara_valores_que_no_son_texto():
    """Un secreto mal tipado sigue siendo un secreto."""
    salida = redactar({"secret_id": 12345, "secret_list": ["a", "b"]})
    assert salida == {"secret_id": MARCA, "secret_list": MARCA}


def test_no_modifica_el_original():
    """El harness sigue trabajando con la configuracion completa en memoria."""
    original = {"api_key": "sk-real", "estructura": {"num_capitulos": 4}}
    redactar(original)
    assert original["api_key"] == "sk-real"


def test_deja_intacto_lo_que_no_es_sensible():
    original = {"estructura": {"num_capitulos": 4, "palabras_min": 1200}}
    assert redactar(original) == original


# ---------------------------------------------------------------------------
# El filtro puesto donde importa: el volcado de la configuracion efectiva
# ---------------------------------------------------------------------------


def test_el_volcado_no_escribe_el_valor_de_una_variable_sensible(tmp_path):
    """Una variable NOVELA_ con nombre de secreto no llega en claro al disco.

    Este es el motivo entero de que el modulo exista: la capa 4 copia variables
    de entorno dentro de la configuracion efectiva, y esa configuracion se
    escribe en salida/config-efectiva.json.
    """
    ruta_config = tmp_path / "config.json"
    ruta_config.write_text(
        json.dumps(
            {
                "novela": {"genero": "terror"},
                "estructura": {"num_capitulos": 2},
                "runtime": {"directorio_salida": str(tmp_path / "salida")},
                "limites": {"api_key": "valor-que-no-debe-salir"},
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    config = cargar_config(ruta_config=ruta_config, entorno={})

    # En memoria el valor sigue entero: el filtro solo actua al escribir.
    assert config["limites"]["api_key"] == "valor-que-no-debe-salir"

    volcado = (tmp_path / "salida" / "config-efectiva.json").read_text(
        encoding="utf-8"
    )
    assert "valor-que-no-debe-salir" not in volcado
    assert MARCA in volcado
    # Y lo que no es secreto sigue estando, que si no el volcado no sirve para
    # reproducir nada.
    assert json.loads(volcado)["estructura"]["num_capitulos"] == 2
