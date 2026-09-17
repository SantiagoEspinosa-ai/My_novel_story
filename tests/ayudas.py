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
    """Una configuracion efectiva de juguete, ya fusionada.

    Tiene la forma que produce `src/config.py` DESPUES del cambio a subagentes:
    sin seccion `proveedor`, sin claves de API, y con los modelos como alias
    (`haiku`, `sonnet`, `opus`) en vez de diccionarios con temperatura y
    max_tokens. La temperatura ya no se puede fijar desde el harness, asi que
    tampoco aparece aqui: un fixture que la incluyera estaria describiendo un
    proyecto que no existe.
    """
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
        "modelos": {
            "escalera_escritor": ["haiku", "sonnet", "opus"],
            "intentos_por_modelo": 2,
            "mantener_voz_ganadora": True,
            "arquitecto": "sonnet",
            "validadores": "haiku",
            "resumidor": "haiku",
        },
        "validacion": {
            "validadores_activos": ["continuidad", "genero", "estilo"],
            "paralelo": True,
            "pesos_gravedad": {"alta": 5, "media": 2, "baja": 1},
            "reintentos_parseo_json": 1,
            "json_no_parseable_es": "FALLO",
        },
        "contexto": {
            "max_tokens_contexto": 100000,
            "ventana_hechos": 3,
            "umbral_compactacion": 60,
            "capitulos_completos_en_ventana": 1,
            "orden_recorte": ["hechos_efimeros", "resumenes", "capitulo_anterior"],
        },
        "runtime": {
            "directorio_salida": "./salida",
            "directorio_prompts": "./prompts",
            "reanudar_si_existe_estado": True,
            "conservar_intentos": False,
            "nivel_log": "info",
            "registrar_tamano_contexto": False,
        },
        "limites": {
            "delegaciones_max_totales": 300,
            "abortar_si_supera_delegaciones": True,
        },
    }
    for seccion, valores in extra.items():
        config.setdefault(seccion, {}).update(valores)
    return config


def veredicto(validador, capitulo=1, veredicto_texto="PASA", problemas=None, **extra):
    """Un veredicto de validador con la forma del spec 7.2, como texto JSON.

    Devuelve TEXTO y no un diccionario a proposito: lo que recibe el harness de
    un validador es siempre texto crudo, y los tests deben recorrer el mismo
    camino de parseo que la ejecucion real.
    """
    import json

    datos = {
        "validador": validador,
        "capitulo": capitulo,
        "veredicto": veredicto_texto,
        "problemas": problemas or [],
    }
    datos.update(extra)
    return json.dumps(datos, ensure_ascii=False)


def problema(gravedad="media", descripcion="Algo no encaja."):
    """Un problema con la forma del spec 7.2."""
    return {
        "gravedad": gravedad,
        "descripcion": descripcion,
        "evidencia": "un fragmento del capitulo",
        "correccion_sugerida": "arreglarlo",
    }
