"""Datos de juguete compartidos por los tests.

Tener la biblia valida en un solo sitio evita que cada test invente la suya y
que, al cambiar el contrato, haya que tocar quince archivos.
"""


def biblia_valida(num_capitulos=3):
    """Una biblia minima que cumple el contrato del spec 7.1."""
    return {
        "titulo": "La casa de la calle Duero",
        "genero": "terror",
        "premisa": "Una restauradora acepta un encargo en una casa que no quiere ser reparada.",
        "conflicto_central": (
            "Marta necesita el dinero del encargo. La casa responde a cada arreglo "
            "con un dano nuevo. Si se marcha sin terminar, pierde el taller."
        ),
        "ambientacion": {
            "lugar": "Un pueblo de la ribera del Duero",
            "epoca": "Invierno de 1998",
            "reglas": [],
        },
        "personajes": [
            {
                "nombre": "Marta",
                "rol": "protagonista",
                "rasgos_fijos": ["ojos grises", "cuarenta y dos anos"],
                "motivacion": "Salvar el taller de su padre.",
                "secreto": "Ya estuvo en esa casa de nina.",
            },
            {
                "nombre": "Ubaldo",
                "rol": "antagonista",
                "rasgos_fijos": ["cojea de la pierna izquierda", "voz ronca"],
                "motivacion": "Que la casa no se termine nunca.",
                "secreto": "Firmo el contrato sabiendo lo que pasaria.",
            },
            {
                "nombre": "Pilar",
                "rol": "secundario",
                "rasgos_fijos": ["pelirroja", "lleva siempre botas de agua"],
                "motivacion": "Vender la finca de al lado.",
                "secreto": "Sabe quien vivio alli antes.",
            },
        ],
        "outline": [
            {
                "capitulo": numero,
                "sinopsis": "Sinopsis del capitulo {0}.".format(numero),
                "cambio": "Algo cambia en el capitulo {0}.".format(numero),
            }
            for numero in range(1, num_capitulos + 1)
        ],
        "timeline": [
            {"capitulo": numero, "momento": "Dia {0}.".format(numero)}
            for numero in range(1, num_capitulos + 1)
        ],
        "hechos_establecidos": [],
    }


def config_minima(num_capitulos=3, **extra):
    """Una configuracion efectiva de juguete, ya fusionada."""
    config = {
        "novela": {
            "genero": "terror",
            "tono": "sobrio",
            "punto_de_vista": "tercera persona limitada",
            "idioma": "es",
            "titulo": None,
            "semilla_tematica": None,
        },
        "estructura": {
            "num_capitulos": num_capitulos,
            "palabras_min": 900,
            "palabras_max": 1600,
        },
        "proveedor": {
            "base_url": "https://openrouter.ai/api/v1",
            "variable_entorno_clave": "OPENROUTER_API_KEY",
            "timeout_segundos": 120,
            "reintentos_red": 3,
            "backoff_segundos": 0,
        },
        "modelos": {
            "escalera_escritor": [
                {"modelo": "proveedor/barato", "temperatura": 0.8, "max_tokens": 4000},
                {"modelo": "proveedor/medio", "temperatura": 0.8, "max_tokens": 4000},
            ],
            "intentos_por_modelo": 2,
            "arquitecto": {"modelo": "proveedor/medio", "temperatura": 0.9, "max_tokens": 6000},
            "validadores": {"modelo": "proveedor/validador", "temperatura": 0.1, "max_tokens": 2000},
        },
        "validacion": {"reintentos_parseo_json": 1},
        "contexto": {
            "max_tokens_contexto": 100000,
            "ventana_hechos": 3,
            "umbral_compactacion": 60,
            "orden_recorte": ["hechos_efimeros", "resumenes", "capitulo_anterior"],
        },
        "runtime": {
            "directorio_salida": "./salida",
            "directorio_prompts": "./prompts",
            "reanudar_si_existe_estado": True,
            "nivel_log": "info",
            "registrar_tamano_contexto": True,
        },
        "limites": {
            "coste_max_usd": 5.0,
            "abortar_si_supera_coste": True,
            "llamadas_max_totales": 300,
        },
    }
    for seccion, valores in extra.items():
        config.setdefault(seccion, {}).update(valores)
    return config
