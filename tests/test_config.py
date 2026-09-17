"""Tests del cargador de configuracion.

Ningun test toca la red, ni el config.json real (salvo el ultimo, que solo lo
lee para comprobar que sigue siendo valido), ni las variables de entorno de tu
maquina: cada test escribe su propio config.json en una carpeta temporal y le
pasa a `cargar_config` un diccionario de entorno inventado. Asi los tests dan
siempre el mismo resultado, los ejecute quien los ejecute.
"""

import json

import pytest

from src.config import ErrorDeConfiguracion, cargar_config

# Entorno vacio. Desde el cambio de arquitectura no hace falta ninguna variable
# para cargar la configuracion: las credenciales son de Claude Code, no del
# proyecto. Se sigue pasando explicitamente para que los tests no dependan del
# entorno real de la maquina.
ENTORNO_MINIMO = {}


def escribir_config(carpeta, contenido):
    """Crea un config.json temporal y devuelve su ruta."""
    ruta = carpeta / "config.json"
    ruta.write_text(json.dumps(contenido, ensure_ascii=False), encoding="utf-8")
    return ruta


def config_base(**secciones):
    """Devuelve un config.json de juguete con la misma forma que el real."""
    contenido = {
        "novela": {"genero": "terror"},
        "estructura": {"num_capitulos": 12, "palabras_min": 1200, "palabras_max": 2200},
        "perfiles": {
            "romance": {
                "estructura": {"palabras_min": 1400, "palabras_max": 2400},
                "novela": {"tono": "calido"},
            },
            "terror": {
                "estructura": {"palabras_min": 900, "palabras_max": 1600},
                "novela": {"tono": "sobrio, contenido, sin adjetivacion excesiva"},
            },
        },
    }
    contenido.update(secciones)
    return contenido


# ---------------------------------------------------------------------------
# Capa 4: las variables de entorno pisan a config.json
# ---------------------------------------------------------------------------


def test_variable_de_entorno_pisa_config_json(tmp_path):
    """NOVELA_NUM_CAPITULOS=5 gana al 12 que pone config.json."""
    ruta = escribir_config(tmp_path, config_base())
    entorno = dict(ENTORNO_MINIMO, NOVELA_NUM_CAPITULOS="5")

    config = cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert config["estructura"]["num_capitulos"] == 5


def test_variable_de_entorno_se_convierte_a_entero(tmp_path):
    """El valor llega como texto '5' y tiene que acabar siendo el entero 5."""
    ruta = escribir_config(tmp_path, config_base())
    entorno = dict(ENTORNO_MINIMO, NOVELA_NUM_CAPITULOS="5")

    config = cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert config["estructura"]["num_capitulos"] == 5
    assert isinstance(config["estructura"]["num_capitulos"], int)


def test_variable_de_entorno_con_ruta_completa(tmp_path):
    """Tambien se puede nombrar la seccion: NOVELA_ESTRUCTURA__NUM_CAPITULOS."""
    ruta = escribir_config(tmp_path, config_base())
    entorno = dict(ENTORNO_MINIMO, NOVELA_ESTRUCTURA__NUM_CAPITULOS="7")

    config = cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert config["estructura"]["num_capitulos"] == 7


def test_variable_de_entorno_desconocida_falla_con_mensaje_claro(tmp_path):
    """Una NOVELA_ mal escrita avisa en vez de ignorarse en silencio."""
    ruta = escribir_config(tmp_path, config_base())
    entorno = dict(ENTORNO_MINIMO, NOVELA_NUM_CAPITULO="5")

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert "NOVELA_NUM_CAPITULO" in str(error.value)


# ---------------------------------------------------------------------------
# Capa 2: el perfil del genero
# ---------------------------------------------------------------------------


def test_perfil_de_terror_se_aplica(tmp_path):
    """Con genero terror y sin valores propios, mandan los del perfil."""
    contenido = config_base()
    # config.json no fija el rango de palabras, asi que lo pone el perfil.
    contenido["estructura"] = {"num_capitulos": 12}
    ruta = escribir_config(tmp_path, contenido)

    config = cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert config["estructura"]["palabras_min"] == 900
    assert config["estructura"]["palabras_max"] == 1600
    assert config["novela"]["tono"] == "sobrio, contenido, sin adjetivacion excesiva"


def test_perfil_pisa_a_los_valores_por_defecto(tmp_path):
    """El perfil de terror (900) gana al valor por defecto del codigo (1200)."""
    contenido = config_base()
    contenido["estructura"] = {}
    ruta = escribir_config(tmp_path, contenido)

    config = cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert config["estructura"]["palabras_min"] == 900
    assert config["estructura"]["num_capitulos"] == 12  # este si viene del defecto


def test_el_perfil_que_se_aplica_es_el_del_genero_activo(tmp_path):
    """Si el genero es romance, se aplica el perfil de romance, no el de terror."""
    contenido = config_base()
    contenido["novela"] = {"genero": "romance"}
    contenido["estructura"] = {"num_capitulos": 12}
    ruta = escribir_config(tmp_path, contenido)

    config = cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert config["estructura"]["palabras_min"] == 1400
    assert config["novela"]["tono"] == "calido"


def test_genero_cambiado_por_entorno_cambia_el_perfil(tmp_path):
    """NOVELA_GENERO=romance arrastra tambien el perfil de romance."""
    contenido = config_base()
    contenido["estructura"] = {"num_capitulos": 12}
    ruta = escribir_config(tmp_path, contenido)
    entorno = dict(ENTORNO_MINIMO, NOVELA_GENERO="romance")

    config = cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert config["novela"]["genero"] == "romance"
    assert config["estructura"]["palabras_min"] == 1400


# ---------------------------------------------------------------------------
# Capa 3: config.json pisa al perfil
# ---------------------------------------------------------------------------


def test_config_json_pisa_al_perfil(tmp_path):
    """El perfil de terror dice 900, pero config.json dice 1111: gana 1111."""
    contenido = config_base()
    contenido["estructura"] = {
        "num_capitulos": 12,
        "palabras_min": 1111,
        "palabras_max": 2222,
    }
    ruta = escribir_config(tmp_path, contenido)

    config = cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert config["estructura"]["palabras_min"] == 1111
    assert config["estructura"]["palabras_max"] == 2222


def test_orden_completo_de_las_cuatro_capas(tmp_path):
    """Defecto < perfil < config.json < entorno, todo en un mismo caso."""
    contenido = config_base()
    contenido["estructura"] = {"num_capitulos": 12, "palabras_min": 1111}
    ruta = escribir_config(tmp_path, contenido)
    entorno = dict(ENTORNO_MINIMO, NOVELA_PALABRAS_MIN="1500")

    config = cargar_config(ruta_config=ruta, entorno=entorno, volcar=False)

    assert config["estructura"]["palabras_min"] == 1500  # capa 4, entorno
    assert config["estructura"]["palabras_max"] == 1600  # capa 2, perfil terror
    assert config["runtime"]["nivel_log"] == "info"      # capa 1, defecto


# ---------------------------------------------------------------------------
# Validacion: configuraciones invalidas con mensaje claro
# ---------------------------------------------------------------------------


def test_num_capitulos_cero_falla(tmp_path):
    contenido = config_base()
    contenido["estructura"] = {"num_capitulos": 0}
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    mensaje = str(error.value)
    assert "num_capitulos" in mensaje
    assert "entero mayor que cero" in mensaje


def test_num_capitulos_no_entero_falla(tmp_path):
    contenido = config_base()
    contenido["estructura"] = {"num_capitulos": "doce"}
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert "num_capitulos" in str(error.value)


def test_palabras_min_mayor_que_max_falla(tmp_path):
    contenido = config_base()
    contenido["estructura"] = {
        "num_capitulos": 12,
        "palabras_min": 3000,
        "palabras_max": 1000,
    }
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    mensaje = str(error.value)
    assert "palabras_min" in mensaje
    assert "palabras_max" in mensaje


def test_genero_invalido_falla(tmp_path):
    contenido = config_base()
    contenido["novela"] = {"genero": "ciencia ficcion"}
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    mensaje = str(error.value)
    assert "genero" in mensaje
    assert "romance" in mensaje and "drama" in mensaje and "terror" in mensaje


def test_un_alias_de_modelo_invalido_falla(tmp_path):
    """Un alias mal escrito se caza al cargar, no en mitad de la generacion."""
    contenido = config_base()
    contenido["modelos"] = {
        "escalera_escritor": ["haiku", "opus-5"],
        "arquitecto": "sonnet",
        "validadores": "haiku",
    }
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    mensaje = str(error.value)
    assert "escalera_escritor[1]" in mensaje
    assert "haiku, sonnet, opus, fable" in mensaje


def test_una_escalera_vacia_falla(tmp_path):
    contenido = config_base()
    contenido["modelos"] = {
        "escalera_escritor": [],
        "arquitecto": "sonnet",
        "validadores": "haiku",
    }
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert "al menos un modelo" in str(error.value)


def test_el_modelo_de_los_validadores_tambien_se_valida(tmp_path):
    contenido = config_base()
    contenido["modelos"] = {
        "escalera_escritor": ["haiku"],
        "arquitecto": "sonnet",
        "validadores": "gemini",
    }
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert "modelos.validadores" in str(error.value)


def test_fable_es_un_alias_admitido(tmp_path):
    """Esta disponible en esta suscripcion; se admite aunque no este en uso."""
    contenido = config_base()
    contenido["modelos"] = {
        "escalera_escritor": ["haiku", "sonnet", "opus", "fable"],
        "arquitecto": "sonnet",
        "validadores": "haiku",
    }
    ruta = escribir_config(tmp_path, contenido)

    config = cargar_config(ruta_config=ruta, entorno=ENTORNO_MINIMO, volcar=False)

    assert config["modelos"]["escalera_escritor"][-1] == "fable"


def test_los_errores_se_acumulan_en_un_solo_mensaje(tmp_path):
    """Varias cosas mal: el mensaje las lista todas, no solo la primera."""
    contenido = config_base()
    contenido["novela"] = {"genero": "policiaco"}
    contenido["estructura"] = {
        "num_capitulos": -1,
        "palabras_min": 2000,
        "palabras_max": 100,
    }
    contenido["modelos"] = {
        "escalera_escritor": ["haiku"],
        "arquitecto": "sonnet",
        "validadores": "inventado",
    }
    ruta = escribir_config(tmp_path, contenido)

    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(ruta_config=ruta, entorno={}, volcar=False)

    mensaje = str(error.value)
    assert "1." in mensaje and "4." in mensaje


def test_config_json_inexistente_falla_con_mensaje_claro(tmp_path):
    with pytest.raises(ErrorDeConfiguracion) as error:
        cargar_config(
            ruta_config=tmp_path / "no-existe.json",
            entorno=ENTORNO_MINIMO,
            volcar=False,
        )

    assert "No encuentro el archivo de configuracion" in str(error.value)


# ---------------------------------------------------------------------------
# Volcado a salida/config-efectiva.json
# ---------------------------------------------------------------------------


def test_vuelca_la_config_efectiva(tmp_path):
    """El volcado escribe el JSON fusionado en el directorio de salida."""
    ruta = escribir_config(tmp_path, config_base())
    salida = tmp_path / "salida"
    entorno = dict(
        ENTORNO_MINIMO,
        NOVELA_DIRECTORIO_SALIDA=str(salida),
        NOVELA_NUM_CAPITULOS="5",
    )

    cargar_config(ruta_config=ruta, entorno=entorno, volcar=True)

    volcado = json.loads((salida / "config-efectiva.json").read_text(encoding="utf-8"))
    assert volcado["estructura"]["num_capitulos"] == 5
    assert "perfiles" not in volcado  # la fuente de la capa 2 no se vuelca


def test_el_volcado_solo_recoge_variables_con_prefijo_novela(tmp_path):
    """Nada del entorno acaba en disco salvo lo que lleve el prefijo NOVELA_.

    El proyecto ya no maneja credenciales propias, pero el entorno de cualquier
    maquina esta lleno de secretos ajenos y el volcado se comparte en informes.
    """
    ruta = escribir_config(tmp_path, config_base())
    salida = tmp_path / "salida"
    entorno = dict(
        ENTORNO_MINIMO,
        UNA_CLAVE_CUALQUIERA="sk-secreto-que-no-debe-salir",
        NOVELA_DIRECTORIO_SALIDA=str(salida),
    )

    cargar_config(ruta_config=ruta, entorno=entorno, volcar=True)

    texto = (salida / "config-efectiva.json").read_text(encoding="utf-8")
    assert "sk-secreto-que-no-debe-salir" not in texto


# ---------------------------------------------------------------------------
# El config.json real del proyecto
# ---------------------------------------------------------------------------


def test_el_config_json_del_proyecto_es_valido():
    """Prueba de humo: el config.json real carga sin errores."""
    config = cargar_config(entorno=ENTORNO_MINIMO, volcar=False)

    assert config["novela"]["genero"] in ("romance", "drama", "terror")
    assert config["estructura"]["num_capitulos"] > 0
    assert config["modelos"]["escalera_escritor"] == ["haiku", "sonnet", "opus"]
    assert config["modelos"]["arquitecto"] == "sonnet"
    assert config["modelos"]["validadores"] == "haiku"
    assert "proveedor" not in config      # la capa de OpenRouter ya no existe
