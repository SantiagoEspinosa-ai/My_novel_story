"""Tests de `src/narracion.py`: convertir el estado en frases legibles.

Qué se protege aquí
-------------------
El panel tenía los datos y aun así no se entendía: enseñaba campos sueltos
—`rol: escritor`, `capitulo: 5`, `intento: 2`— y quien miraba recomponía la
frase en su cabeza. Peor: durante los pasos que no son una delegación decía
«sin actividad» mientras el servidor trabajaba.

Estos tests fijan **el tono**, no solo los datos. Una frase que diga
`escritor / 5 / 2 / opus` sería técnicamente correcta y no serviría, así que
se comprueba que la frase se lea como una frase.

Este módulo no toca disco ni red: recibe diccionarios y devuelve texto.
"""

import pytest

from src import narracion as n


CONFIG = {"modelos": {"escalera_escritor": ["haiku", "sonnet", "opus"],
                      "intentos_por_modelo": 2},
          "estructura": {"num_capitulos": 6}}


# ---------------------------------------------------------------------------
# La frase de quién está trabajando
# ---------------------------------------------------------------------------


def test_el_escritor_se_cuenta_entero():
    frase = n.frase_de_delegacion(
        {"rol": "escritor", "capitulo": 5, "intento": 2, "modelo": "opus"}, CONFIG)
    assert frase == "El escritor está redactando el capítulo 5, intento 2 de 6, con opus"


def test_el_tope_de_intentos_sale_de_la_escalera_configurada():
    """«intento 2 de 6» son 3 peldaños por 2 intentos, no un número fijo."""
    corta = {"modelos": {"escalera_escritor": ["opus"], "intentos_por_modelo": 3}}
    frase = n.frase_de_delegacion(
        {"rol": "escritor", "capitulo": 1, "intento": 1, "modelo": "opus"}, corta)
    assert "intento 1 de 3" in frase


def test_los_validadores_van_en_plural_porque_van_a_la_vez():
    """El rol `validadores` significa los tres a la vez, y la frase lo dice."""
    frase = n.frase_de_delegacion({"rol": "validadores", "capitulo": 5}, CONFIG)
    assert frase == "Los tres validadores están auditando el capítulo 5 a la vez"


def test_un_validador_suelto_se_nombra_y_el_genero_lleva_tilde():
    assert "validador de género" in n.frase_de_delegacion(
        {"rol": "genero", "capitulo": 2}, CONFIG)
    assert "validador de continuidad" in n.frase_de_delegacion(
        {"rol": "continuidad", "capitulo": 2}, CONFIG)


def test_el_resumidor_explica_para_que_sirve_lo_que_hace():
    frase = n.frase_de_delegacion({"rol": "resumidor", "capitulo": 4}, CONFIG)
    assert "Resumiendo el capítulo 4" in frase
    assert "para que los siguientes sepan qué pasó" in frase


def test_sin_delegacion_no_hay_frase():
    assert n.frase_de_delegacion(None, CONFIG) is None
    assert n.frase_de_delegacion({}, CONFIG) is None


# ---------------------------------------------------------------------------
# Las fases que lleva el servidor, no el harness
# ---------------------------------------------------------------------------


def test_copiar_se_cuenta_con_la_carpeta_por_su_nombre():
    frase = n.frase_de_fase(n.FASE_COPIANDO, {"destino": "salida-novela-2"})
    assert frase == "Copiando la novela actual a salida-novela-2, antes de tocar nada"


def test_el_arquitecto_dice_que_capitulos_esta_disenando():
    assert n.frase_de_fase(n.FASE_ARQUITECTO, {"capitulos_nuevos": [5, 6]}) == (
        "El arquitecto está diseñando qué pasa en los capítulos 5 y 6")
    assert n.frase_de_fase(n.FASE_ARQUITECTO, {"capitulos_nuevos": [5]}) == (
        "El arquitecto está diseñando qué pasa en el capítulo 5")
    assert "los capítulos 5, 6 y 7" in n.frase_de_fase(
        n.FASE_ARQUITECTO, {"capitulos_nuevos": [5, 6, 7]})


def test_ninguna_frase_usa_jerga_del_sistema():
    """Quien mira el panel no tiene por qué saber cómo se llaman las cosas."""
    frases = [
        n.frase_de_fase(n.FASE_COPIANDO, {}),
        n.frase_de_fase(n.FASE_ARQUITECTO, {"capitulos_nuevos": [5]}),
        n.frase_de_fase(n.FASE_VALIDANDO, {}),
        n.frase_de_fase(n.FASE_LANZANDO, {"capitulos_nuevos": [5]}),
        n.frase_de_delegacion({"rol": "escritor", "capitulo": 5, "intento": 1,
                               "modelo": "opus"}, CONFIG),
        n.frase_de_delegacion({"rol": "validadores", "capitulo": 5}, CONFIG),
    ]
    jerga = ["delegacion_en_curso", "ACEPTADO_POR_PUNTUACION", "FALLO", "PASA",
             "estado.json", "num_capitulos", "subagente", "outline"]
    for frase in frases:
        assert frase
        for palabra in jerga:
            assert palabra not in frase, (palabra, frase)


# ---------------------------------------------------------------------------
# Lo que pasó mientras no mirabas
# ---------------------------------------------------------------------------


def test_un_capitulo_aprobado_se_cuenta_y_dice_cual_viene():
    frases = n.eventos_entre(
        {"capitulos_aprobados": [1, 2, 3, 4]},
        {"capitulos_aprobados": [1, 2, 3, 4, 5]},
        total_capitulos=6)
    assert frases == ["Capítulo 5 aprobado limpio. Pasando al 6"]


def test_el_ultimo_capitulo_no_dice_pasando_al_siguiente():
    frases = n.eventos_entre(
        {"capitulos_aprobados": [1, 2, 3, 4, 5]},
        {"capitulos_aprobados": [1, 2, 3, 4, 5, 6]},
        total_capitulos=6)
    assert frases == ["Capítulo 6 aprobado limpio"]


def test_un_capitulo_marcado_dice_por_que_si_se_sabe():
    frases = n.eventos_entre(
        {"capitulos_aprobados": [1, 2, 3, 4], "capitulos_marcados": []},
        {"capitulos_aprobados": [1, 2, 3, 4], "capitulos_marcados": [5]},
        problemas_por_capitulo={5: "estilo encontró 3 problemas"},
        total_capitulos=6)
    assert frases == [
        "Capítulo 5 entregado sin pasar limpio: estilo encontró 3 problemas. "
        "Pasando al 6"]


def test_un_capitulo_marcado_sin_detalle_no_se_inventa_el_motivo():
    frases = n.eventos_entre(
        {"capitulos_marcados": []}, {"capitulos_marcados": [5]}, total_capitulos=6)
    assert "se agotaron los intentos" in frases[0]


def test_comparar_contra_una_foto_vacia_lo_cuenta_todo():
    """Comportamiento correcto de la función, y trampa para quien la use.

    Si se compara contra una foto vacía, todo lo que ya estaba hecho parece
    recién hecho. Por eso el servidor no cuenta eventos en su primera lectura:
    solo toma la foto. Este test deja la trampa escrita para que nadie la pise
    otra vez.
    """
    frases = n.eventos_entre({}, {"capitulos_aprobados": [1, 2, 3]}, total_capitulos=3)
    assert len(frases) == 3


def test_sin_cambios_no_se_cuenta_nada():
    foto = {"capitulos_aprobados": [1, 2], "capitulos_marcados": [3]}
    assert n.eventos_entre(foto, foto, total_capitulos=6) == []


def test_la_reescritura_nombra_a_quien_suspendio_y_cuanto_encontro():
    frase = n.frase_de_reescritura(5, [
        {"validador": "estilo", "veredicto": "FALLO", "problemas": [1, 2, 3]},
        {"validador": "genero", "veredicto": "PASA", "problemas": []},
    ])
    assert frase == "El capítulo 5 no pasó: estilo encontró 3 problemas. Reescribiendo"


def test_la_reescritura_junta_a_los_que_suspenden():
    frase = n.frase_de_reescritura(2, [
        {"validador": "estilo", "veredicto": "FALLO", "problemas": [1]},
        {"validador": "continuidad", "veredicto": "FALLO", "problemas": [1, 2]},
    ])
    assert "estilo encontró 1 problema y continuidad encontró 2 problemas" in frase


def test_si_todos_aprueban_no_hay_frase_de_reescritura():
    assert n.frase_de_reescritura(1, [
        {"validador": "estilo", "veredicto": "PASA"}]) is None


# ---------------------------------------------------------------------------
# Cuando no hay nada en marcha
# ---------------------------------------------------------------------------


def test_el_reposo_nunca_es_un_sin_actividad_a_secas():
    """«Sin actividad» no distingue una novela terminada de una caída."""
    frase = n.frase_de_reposo({"fase": n.FASE_TERMINADA,
                               "ultima_frase": "Capítulo 6 aprobado limpio"})
    assert "terminó bien" in frase
    assert "Lo último que pasó: Capítulo 6 aprobado limpio" in frase


def test_el_reposo_distingue_caida_de_parada_y_de_terminada():
    caida = n.frase_de_reposo({"fase": n.FASE_CAIDA})
    parada = n.frase_de_reposo({"fase": n.FASE_DETENIDA})
    fin = n.frase_de_reposo({"fase": n.FASE_TERMINADA})
    assert "se cayó sin terminar" in caida
    assert "se paró a mano" in parada
    assert "terminó bien" in fin
    assert caida != parada != fin


def test_una_ampliacion_fallida_dice_que_la_novela_quedo_igual():
    frase = n.frase_de_reposo({"fase": n.FASE_FALLO_AMPLIACION})
    assert "la novela quedó como estaba" in frase


# ---------------------------------------------------------------------------
# Cuando algo se alarga
# ---------------------------------------------------------------------------


def test_dentro_de_lo_normal_no_dice_nada():
    assert n.comentario_si_tarda("escritor", 120) is None
    assert n.comentario_si_tarda(n.FASE_ARQUITECTO, 60) is None


def test_pasado_lo_normal_lo_menciona_sin_alarmar():
    aviso = n.comentario_si_tarda("escritor", 400)
    assert "más de lo normal" in aviso
    assert "6 min 40 s" in aviso
    assert "puede terminar bien" in aviso   # no dice que este roto
    assert "se puede detener" in aviso      # y dice que se puede hacer


def test_una_fase_desconocida_usa_el_tope_por_defecto():
    assert n.comentario_si_tarda("lo-que-sea", 100) is None
    assert n.comentario_si_tarda("lo-que-sea", 700) is not None


def test_sin_tiempo_no_se_avisa_de_nada():
    assert n.comentario_si_tarda("escritor", None) is None


@pytest.mark.parametrize("segundos,esperado", [
    (0, "0 s"), (45, "45 s"), (60, "1 min 00 s"), (125, "2 min 05 s"),
    (3600, "1 h 00 min"), (4380, "1 h 13 min"),
])
def test_las_duraciones_se_leen(segundos, esperado):
    assert n.duracion_legible(segundos) == esperado
