"""Tests del ensamblador de ventanas de contexto. Ninguno toca la red."""

from src import biblia as modulo_biblia
from src import contexto
from tests.ayudas import biblia_valida, config_minima


# ---------------------------------------------------------------------------
# Arquitecto
# ---------------------------------------------------------------------------


def test_la_ventana_del_arquitecto_lleva_la_configuracion_y_nada_mas():
    config = config_minima(num_capitulos=12)

    ventana = contexto.ventana_arquitecto(config)

    assert "CONFIGURACION:" in ventana.texto
    assert '"num_capitulos": 12' in ventana.texto
    assert '"palabras_min": 900' in ventana.texto
    assert "BIBLIA" not in ventana.texto


def test_los_valores_concretos_van_en_el_mensaje_y_no_en_el_prompt():
    """El prompt de sistema no lleva valores fijos: llegan desde config.json."""
    config = config_minima()
    config["novela"]["semilla_tematica"] = "una casa que se repara sola"

    ventana = contexto.ventana_arquitecto(config)

    assert "una casa que se repara sola" in ventana.texto


# ---------------------------------------------------------------------------
# Escritor: la regla del capitulo N-1
# ---------------------------------------------------------------------------


def _resumenes(hasta):
    return {numero: "Resumen del capitulo {0}.".format(numero) for numero in range(1, hasta + 1)}


def test_el_capitulo_anterior_entra_completo():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)

    ventana = contexto.ventana_escritor(
        config, biblia, capitulo=5,
        resumenes=_resumenes(4),
        texto_anterior="TEXTO INTEGRO DEL CAPITULO CUATRO",
    )

    assert "CAPITULO_ANTERIOR:" in ventana.texto
    assert "TEXTO INTEGRO DEL CAPITULO CUATRO" in ventana.texto


def test_los_capitulos_anteriores_al_n_menos_1_entran_solo_como_resumen():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)

    ventana = contexto.ventana_escritor(
        config, biblia, capitulo=5,
        resumenes=_resumenes(4),
        texto_anterior="TEXTO INTEGRO DEL CAPITULO CUATRO",
    )

    assert "Capitulo 3: Resumen del capitulo 3." in ventana.texto
    # El resumen del 4 no se repite: el 4 entra completo en su propio bloque.
    assert "Capitulo 4: Resumen del capitulo 4." not in ventana.texto


def test_el_primer_capitulo_no_lleva_bloque_de_capitulo_anterior():
    config = config_minima()
    biblia = biblia_valida(3)

    ventana = contexto.ventana_escritor(config, biblia, capitulo=1)

    assert "CAPITULO_ANTERIOR" not in ventana.texto
    assert "RESUMENES_ANTERIORES" not in ventana.texto


def test_la_ventana_lleva_el_outline_solo_del_capitulo_en_curso():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)

    ventana = contexto.ventana_escritor(config, biblia, capitulo=7)

    assert "Sinopsis del capitulo 7." in ventana.texto
    assert "Sinopsis del capitulo 9." not in ventana.texto


def test_los_problemas_solo_aparecen_si_se_pasan():
    config = config_minima()
    biblia = biblia_valida(3)

    sin_problemas = contexto.ventana_escritor(config, biblia, capitulo=1)
    con_problemas = contexto.ventana_escritor(
        config, biblia, capitulo=1, problemas=["El personaje cambia de ojos."]
    )

    assert "PROBLEMAS" not in sin_problemas.texto
    assert "El personaje cambia de ojos." in con_problemas.texto


def test_la_ventana_del_capitulo_12_no_es_mayor_que_la_del_3():
    """Criterio de aceptacion 9 del spec: la ventana no crece con N."""
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)
    for numero in range(1, 12):
        modulo_biblia.anadir_hecho(
            biblia, numero, "Hecho efimero del capitulo {0}.".format(numero), "efimero"
        )
    texto_anterior = "Parrafo. " * 500

    tercera = contexto.ventana_escritor(
        config, biblia, 3, _resumenes(2), texto_anterior
    )
    duodecima = contexto.ventana_escritor(
        config, biblia, 12, _resumenes(11), texto_anterior
    )

    # Los resumenes crecen un poco, pero el grueso (hechos y capitulo anterior)
    # se mantiene acotado. Un 30% de margen es de sobra para esa diferencia.
    assert duodecima.tokens <= tercera.tokens * 1.3


# ---------------------------------------------------------------------------
# Hechos vigentes dentro de la ventana
# ---------------------------------------------------------------------------


def test_la_ventana_incluye_los_hechos_permanentes_antiguos():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)
    modulo_biblia.anadir_hecho(biblia, 1, "Ubaldo muere en el sotano.", "permanente")
    modulo_biblia.anadir_hecho(biblia, 1, "Marta lleva abrigo rojo.", "efimero")

    ventana = contexto.ventana_escritor(config, biblia, capitulo=10)

    assert "Ubaldo muere en el sotano." in ventana.texto
    assert "Marta lleva abrigo rojo." not in ventana.texto


# ---------------------------------------------------------------------------
# Presupuesto: recortes en orden
# ---------------------------------------------------------------------------


def _config_apretada(maximo):
    config = config_minima(num_capitulos=12)
    config["contexto"]["max_tokens_contexto"] = maximo
    return config


def test_al_recortar_se_pierden_los_efimeros_pero_nunca_los_permanentes():
    config = _config_apretada(400)
    biblia = biblia_valida(12)
    modulo_biblia.anadir_hecho(biblia, 9, "PERMANENTE: la casa esta tapiada.", "permanente")
    for numero in range(1, 10):
        modulo_biblia.anadir_hecho(
            biblia, numero, "EFIMERO numero {0} con texto de relleno.".format(numero),
            "efimero",
        )

    ventana = contexto.ventana_escritor(
        config, biblia, capitulo=10, resumenes=_resumenes(9),
        texto_anterior="Parrafo largo. " * 200,
    )

    assert "PERMANENTE: la casa esta tapiada." in ventana.texto
    assert "EFIMERO numero 9" not in ventana.texto
    assert any("efimeros" in recorte for recorte in ventana.recortes)


def test_los_recortes_se_aplican_en_el_orden_configurado():
    config = _config_apretada(60)
    biblia = biblia_valida(12)
    modulo_biblia.anadir_hecho(biblia, 9, "Un hecho efimero.", "efimero")

    ventana = contexto.ventana_escritor(
        config, biblia, capitulo=10, resumenes=_resumenes(9),
        texto_anterior="Texto muy largo. " * 300,
    )

    assert ventana.recortes[0].startswith("hechos efimeros")
    assert any("capitulo anterior" in recorte for recorte in ventana.recortes)
    assert "Texto muy largo." not in ventana.texto


def test_sin_presion_de_presupuesto_no_hay_recortes():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)

    ventana = contexto.ventana_escritor(
        config, biblia, capitulo=5, resumenes=_resumenes(4), texto_anterior="Corto."
    )

    assert ventana.recortes == []


# ---------------------------------------------------------------------------
# Validadores
# ---------------------------------------------------------------------------


def test_continuidad_recibe_la_biblia_entera_y_el_capitulo():
    config = config_minima()
    biblia = biblia_valida(3)

    ventana = contexto.ventana_continuidad(config, biblia, 2, "El texto del capitulo.")

    assert "BIBLIA:" in ventana.texto
    assert "Sinopsis del capitulo 1." in ventana.texto      # outline completo
    assert "El texto del capitulo." in ventana.texto


def test_genero_recibe_convenciones_y_posicion_pero_no_la_biblia():
    config = config_minima(num_capitulos=12)
    biblia = biblia_valida(12)

    ventana = contexto.ventana_genero(
        config, "CONVENCIONES DEL TERROR", 6, "El texto del capitulo."
    )

    assert "CONVENCIONES DEL TERROR" in ventana.texto
    assert "POSICION_ARCO:" in ventana.texto
    assert biblia["premisa"] not in ventana.texto


def test_estilo_recibe_el_texto_y_la_memoria_pero_no_la_biblia():
    config = config_minima()
    memoria = {"frases_recurrentes": [{"frase": "un escalofrio", "apariciones": 4}],
               "muletillas": ["de pronto"]}

    ventana = contexto.ventana_estilo(config, 3, "El texto.", memoria)

    assert "un escalofrio" in ventana.texto
    assert "de pronto" in ventana.texto
    assert "BIBLIA" not in ventana.texto


def test_la_posicion_en_el_arco_reparte_en_cuatro_fases():
    assert "fase 1 de 4" in contexto.posicion_en_el_arco(1, 12)
    assert "fase 2 de 4" in contexto.posicion_en_el_arco(5, 12)
    assert "fase 4 de 4" in contexto.posicion_en_el_arco(12, 12)
    assert "quedan 0 capitulos" in contexto.posicion_en_el_arco(12, 12)


# ---------------------------------------------------------------------------
# Medida del tamano
# ---------------------------------------------------------------------------


def test_la_ventana_informa_de_su_tamano():
    config = config_minima()
    biblia = biblia_valida(3)

    ventana = contexto.ventana_escritor(config, biblia, capitulo=1)

    assert ventana.tokens == contexto.estimar_tokens(ventana.texto)
    assert ventana.tokens > 0
