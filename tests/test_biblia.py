"""Tests del gestor de la biblia. Ninguno toca la red."""

import json

import pytest

from src import biblia as modulo
from tests.ayudas import biblia_valida


# ---------------------------------------------------------------------------
# Validacion del contrato
# ---------------------------------------------------------------------------


def test_una_biblia_correcta_valida():
    datos = biblia_valida(3)
    assert modulo.validar(datos, num_capitulos=3) is datos


def test_outline_con_numero_de_capitulos_equivocado_falla():
    datos = biblia_valida(3)

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.validar(datos, num_capitulos=12)

    mensaje = str(error.value)
    assert "outline tiene 3 entradas" in mensaje
    assert "12" in mensaje


def test_falta_un_campo_obligatorio_y_el_mensaje_lo_dice():
    datos = biblia_valida()
    del datos["premisa"]

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.validar(datos)

    assert "premisa" in str(error.value)


def test_genero_invalido_falla():
    datos = biblia_valida()
    datos["genero"] = "comedia"

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.validar(datos)

    assert "genero" in str(error.value)


def test_exige_exactamente_un_protagonista():
    datos = biblia_valida()
    datos["personajes"][1]["rol"] = "protagonista"

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.validar(datos)

    assert "protagonista" in str(error.value)


def test_los_problemas_se_acumulan():
    """El mensaje viaja al modelo en el reintento: tiene que llevarlos todos."""
    datos = biblia_valida()
    datos["genero"] = "comedia"
    del datos["titulo"]
    datos["personajes"][0]["rasgos_fijos"] = []

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.validar(datos)

    mensaje = str(error.value)
    assert "1." in mensaje and "3." in mensaje


def test_normalizar_rellena_las_claves_opcionales():
    datos = biblia_valida()
    del datos["hechos_establecidos"]
    del datos["timeline"]

    normalizada = modulo.normalizar(datos)

    assert normalizada["hechos_establecidos"] == []
    assert normalizada["timeline"] == []


# ---------------------------------------------------------------------------
# Serializacion ida y vuelta
# ---------------------------------------------------------------------------


def test_guardar_y_cargar_devuelve_lo_mismo(tmp_path):
    original = biblia_valida(3)
    modulo.anadir_hecho(original, 1, "El sotano esta tapiado.", "permanente")

    modulo.guardar(original, tmp_path)
    recuperada = modulo.cargar(tmp_path, num_capitulos=3)

    assert recuperada == original


def test_guardar_escribe_json_legible_con_acentos(tmp_path):
    datos = biblia_valida()
    datos["titulo"] = "La casa de la calle Duero, en invierno"

    ruta = modulo.guardar(datos, tmp_path)
    texto = ruta.read_text(encoding="utf-8")

    assert json.loads(texto)["titulo"] == datos["titulo"]


def test_cargar_biblia_inexistente_falla_con_mensaje_claro(tmp_path):
    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.cargar(tmp_path)

    assert "No encuentro" in str(error.value)


def test_cargar_biblia_rota_falla_con_mensaje_claro(tmp_path):
    (tmp_path / "biblia.json").write_text("{esto no es json", encoding="utf-8")

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.cargar(tmp_path)

    assert "no es JSON valido" in str(error.value)


# ---------------------------------------------------------------------------
# Hechos y timeline
# ---------------------------------------------------------------------------


def test_anadir_hecho_registra_capitulo_y_persistencia():
    datos = biblia_valida()

    entrada = modulo.anadir_hecho(datos, 2, "Pilar pierde la llave.", "efimero")

    assert entrada == {
        "capitulo": 2,
        "hecho": "Pilar pierde la llave.",
        "persistencia": "efimero",
    }
    assert datos["hechos_establecidos"] == [entrada]


def test_anadir_hecho_con_persistencia_invalida_falla():
    datos = biblia_valida()

    with pytest.raises(modulo.ErrorDeBiblia) as error:
        modulo.anadir_hecho(datos, 1, "Algo.", "para siempre")

    assert "persistencia" in str(error.value)


def test_anadir_timeline_sustituye_la_entrada_del_mismo_capitulo():
    datos = biblia_valida(3)

    modulo.anadir_timeline(datos, 2, "Tres dias despues.")

    entradas = [linea for linea in datos["timeline"] if linea["capitulo"] == 2]
    assert entradas == [{"capitulo": 2, "momento": "Tres dias despues."}]


# ---------------------------------------------------------------------------
# Hechos vigentes: lo que decide el tamano de la ventana del escritor
# ---------------------------------------------------------------------------


def test_los_hechos_permanentes_no_se_filtran_nunca():
    """Un personaje que murio en el capitulo 1 sigue muerto en el 10."""
    datos = biblia_valida(12)
    modulo.anadir_hecho(datos, 1, "Ubaldo muere en el sotano.", "permanente")
    modulo.anadir_hecho(datos, 1, "Marta lleva el abrigo rojo.", "efimero")
    modulo.anadir_hecho(datos, 9, "La puerta del desvan queda abierta.", "efimero")

    vigentes = modulo.hechos_vigentes(datos, capitulo_actual=10, ventana_hechos=3)

    hechos = [entrada["hecho"] for entrada in vigentes]
    assert "Ubaldo muere en el sotano." in hechos          # permanente, capitulo 1
    assert "La puerta del desvan queda abierta." in hechos  # efimero reciente
    assert "Marta lleva el abrigo rojo." not in hechos      # efimero antiguo


def test_ventana_hechos_cero_deja_solo_los_permanentes():
    datos = biblia_valida(12)
    modulo.anadir_hecho(datos, 5, "Permanente.", "permanente")
    modulo.anadir_hecho(datos, 5, "Efimero.", "efimero")

    vigentes = modulo.hechos_vigentes(datos, capitulo_actual=6, ventana_hechos=0)

    assert [entrada["hecho"] for entrada in vigentes] == ["Permanente."]


def test_hechos_permanentes_devuelve_solo_los_permanentes():
    datos = biblia_valida()
    modulo.anadir_hecho(datos, 1, "Uno.", "permanente")
    modulo.anadir_hecho(datos, 1, "Dos.", "efimero")

    assert [e["hecho"] for e in modulo.hechos_permanentes(datos)] == ["Uno."]


def test_entrada_outline_encuentra_el_capitulo():
    datos = biblia_valida(3)

    assert modulo.entrada_outline(datos, 2)["capitulo"] == 2
    assert modulo.entrada_outline(datos, 99) is None


# ---------------------------------------------------------------------------
# Compactacion: todavia no implementada, pero con contrato
# ---------------------------------------------------------------------------


def test_necesita_compactacion_compara_con_el_umbral():
    datos = biblia_valida()
    for numero in range(5):
        modulo.anadir_hecho(datos, 1, "Hecho {0}.".format(numero), "efimero")

    assert modulo.necesita_compactacion(datos, umbral_compactacion=4) is True
    assert modulo.necesita_compactacion(datos, umbral_compactacion=10) is False


def test_compactar_todavia_no_pierde_ningun_hecho():
    """Mientras no este implementada, tiene que ser inofensiva."""
    datos = biblia_valida()
    modulo.anadir_hecho(datos, 1, "Permanente.", "permanente")
    modulo.anadir_hecho(datos, 1, "Efimero.", "efimero")
    antes = list(datos["hechos_establecidos"])

    modulo.compactar(datos, umbral_compactacion=1, ventana_hechos=3)

    assert datos["hechos_establecidos"] == antes
