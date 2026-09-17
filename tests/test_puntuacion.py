"""Tests de src/puntuacion.py.

El hilo conductor de casi todos: **rendirse siempre hacia FALLO**. Un validador
que no contesta, que contesta mal o que se contradice no puede acabar aprobando
un capitulo. Si alguno de estos tests se pone en rojo, la validacion ha dejado
de ser validacion.
"""

import json

from src import puntuacion
from tests.ayudas import problema, veredicto


# ---------------------------------------------------------------------------
# Parseo defensivo
# ---------------------------------------------------------------------------


def test_extrae_json_limpio():
    assert puntuacion.extraer_json('{"a": 1}') == {"a": 1}


def test_extrae_json_con_vallas_de_bloque():
    crudo = '```json\n{"a": 1}\n```'
    assert puntuacion.extraer_json(crudo) == {"a": 1}


def test_extrae_json_con_preambulo():
    crudo = 'Aqui tienes el JSON que me pides:\n{"a": 1}\nUn saludo.'
    assert puntuacion.extraer_json(crudo) == {"a": 1}


def test_las_llaves_dentro_de_una_cadena_no_confunden_al_extractor():
    crudo = '{"descripcion": "usa una { llave } en el texto", "a": 1}'
    assert puntuacion.extraer_json(crudo)["a"] == 1


def test_respuesta_vacia_es_error():
    try:
        puntuacion.extraer_json("   ")
    except puntuacion.ErrorDeVeredicto:
        return
    raise AssertionError("una respuesta vacia tenia que fallar")


# ---------------------------------------------------------------------------
# Regla 2: lo que no se entiende, falla
# ---------------------------------------------------------------------------


def test_texto_ilegible_da_indeterminado_y_cuenta_como_fallo():
    resultado = puntuacion.leer("no pienso contestarte en JSON", "estilo", 3)
    assert resultado["veredicto"] == puntuacion.INDETERMINADO
    assert puntuacion.es_fallo(resultado)
    assert resultado["problemas"], "un INDETERMINADO tiene que puntuar"


def test_pasa_con_problemas_es_indeterminado():
    """El spec 7.2 obliga a problemas vacio cuando el veredicto es PASA.

    Un validador que dice "pasa, pero hay tres cosas mal" no ha entendido su
    trabajo. Creerle colaria esos tres problemas al manuscrito.
    """
    crudo = veredicto("genero", 2, "PASA", [problema("alta")])
    resultado = puntuacion.leer(crudo, "genero", 2)
    assert resultado["veredicto"] == puntuacion.INDETERMINADO


def test_veredicto_desconocido_es_indeterminado():
    crudo = json.dumps({"veredicto": "REGULAR", "problemas": []})
    assert puntuacion.leer(crudo, "estilo", 1)["veredicto"] == puntuacion.INDETERMINADO


def test_problemas_que_no_son_lista_es_indeterminado():
    crudo = json.dumps({"veredicto": "FALLO", "problemas": "muchos"})
    assert puntuacion.leer(crudo, "estilo", 1)["veredicto"] == puntuacion.INDETERMINADO


def test_gravedad_desconocida_se_trata_como_alta():
    """No se premia al validador que describe bien y etiqueta mal."""
    crudo = veredicto("estilo", 1, "FALLO", [problema("gravisima")])
    resultado = puntuacion.leer(crudo, "estilo", 1)
    assert resultado["problemas"][0]["gravedad"] == "alta"


def test_un_fallo_limpio_se_conserva_tal_cual():
    crudo = veredicto("continuidad", 4, "FALLO", [problema("baja", "Ojos verdes.")])
    resultado = puntuacion.leer(crudo, "continuidad", 4)
    assert resultado["veredicto"] == "FALLO"
    assert resultado["problemas"][0]["descripcion"] == "Ojos verdes."
    assert resultado["problemas"][0]["evidencia"]


def test_se_conservan_las_frases_para_la_memoria_de_estilo():
    """Un PASA tambien puede traer frases que vigilar, y no se pueden perder."""
    crudo = veredicto(
        "estilo", 1, "PASA", [],
        nuevas_frases_recurrentes=["la luz mortecina", "  ", "un silencio espeso"],
    )
    resultado = puntuacion.leer(crudo, "estilo", 1)
    assert resultado["veredicto"] == "PASA"
    assert resultado["nuevas_frases_recurrentes"] == [
        "la luz mortecina", "un silencio espeso"
    ]


# ---------------------------------------------------------------------------
# Regla de bloqueo
# ---------------------------------------------------------------------------


def _tres(estado_continuidad="PASA", estado_genero="PASA", estado_estilo="PASA"):
    return [
        puntuacion.leer(veredicto("continuidad", 1, estado_continuidad), "continuidad", 1),
        puntuacion.leer(veredicto("genero", 1, estado_genero), "genero", 1),
        puntuacion.leer(veredicto("estilo", 1, estado_estilo), "estilo", 1),
    ]


def test_aprueba_solo_con_los_tres_pasa():
    assert puntuacion.aprueba(_tres()) is True


def test_un_solo_fallo_bloquea():
    assert puntuacion.aprueba(_tres(estado_estilo="FALLO")) is False


def test_un_validador_ausente_no_aprueba():
    """Un validador que no llego a ejecutarse no es un validador que aprueba."""
    assert puntuacion.aprueba(_tres()[:2]) is False


def test_un_indeterminado_bloquea():
    veredictos = _tres()[:2] + [puntuacion.leer("basura", "estilo", 1)]
    assert puntuacion.aprueba(veredictos) is False


# ---------------------------------------------------------------------------
# Puntuacion y mejor version
# ---------------------------------------------------------------------------


def test_dos_medios_puntuan_menos_que_uno_alto():
    """El ejemplo literal del spec 6.4: 2+2=4 gana a 5, porque menor es mejor."""
    dos_medios = [puntuacion.leer(
        veredicto("estilo", 1, "FALLO", [problema("media"), problema("media")]),
        "estilo", 1,
    )]
    uno_alto = [puntuacion.leer(
        veredicto("estilo", 1, "FALLO", [problema("alta")]), "estilo", 1
    )]
    assert puntuacion.puntuar(dos_medios) == 4
    assert puntuacion.puntuar(uno_alto) == 5


def test_los_pesos_se_pueden_configurar():
    veredictos = [puntuacion.leer(
        veredicto("estilo", 1, "FALLO", [problema("baja")]), "estilo", 1
    )]
    assert puntuacion.puntuar(veredictos, {"alta": 9, "media": 9, "baja": 7}) == 7


def test_mejor_intento_elige_la_puntuacion_mas_baja():
    intentos = [
        {"intento": 1, "puntuacion": 9},
        {"intento": 2, "puntuacion": 4},
        {"intento": 3, "puntuacion": 7},
    ]
    assert puntuacion.mejor_intento(intentos)["intento"] == 2


def test_en_empate_gana_el_intento_mas_tardio():
    """Ha incorporado mas feedback acumulado, que es una propiedad real."""
    intentos = [
        {"intento": 1, "puntuacion": 4},
        {"intento": 5, "puntuacion": 4},
        {"intento": 3, "puntuacion": 4},
    ]
    assert puntuacion.mejor_intento(intentos)["intento"] == 5


def test_sin_intentos_no_hay_mejor():
    assert puntuacion.mejor_intento([]) is None


def test_los_problemas_se_acumulan_sin_repetirse():
    """Los validadores repiten la misma pega intento tras intento.

    Una lista con la misma frase seis veces le dice al escritor menos que una
    lista con seis pegas distintas.
    """
    intentos = [
        {"veredictos": [puntuacion.leer(
            veredicto("estilo", 1, "FALLO", [problema("alta", "Repites 'sombra'.")]),
            "estilo", 1,
        )]},
        {"veredictos": [puntuacion.leer(
            veredicto("estilo", 1, "FALLO", [
                problema("alta", "Repites 'sombra'."),
                problema("baja", "El dialogo no tiene subtexto."),
            ]),
            "estilo", 1,
        )]},
    ]
    acumulados = puntuacion.problemas_acumulados(intentos)
    assert len(acumulados) == 2
    assert all(p["validador"] == "estilo" for p in acumulados)
