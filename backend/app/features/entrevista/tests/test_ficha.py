"""`SPEC-25` `RF-01`..`RF-05`: la ficha, lo que falta y el paso a brief."""

import pytest
from pydantic import ValidationError

from app.commons.configuracion import carga
from app.commons.configuracion.esquemas import BriefDeObra
from app.commons.dominio.destinatario import EXTENSION, FichaDeEntrevista
from app.features.entrevista import ficha as modulo
from app.features.entrevista.tests.conftest import ficha_completa

OBLIGATORIOS_EN_ORDEN = ["nombre", "edad", "ocasion", "genero", "tono", "papel",
                         "rasgo", "recuerdo", "premisa", "titulo"]


def test_una_ficha_vacia_pide_los_diez_obligatorios_en_el_orden_del_anexo():
    """`SPEC-25` v3: la premisa y el titulo van despues de los recuerdos, porque
    salen de ellos (`RF-02b`)."""
    assert modulo.que_falta(FichaDeEntrevista()) == OBLIGATORIOS_EN_ORDEN


def test_una_ficha_completa_no_pide_nada(completa):
    assert modulo.que_falta(completa) == []


def test_un_rasgo_no_cuenta_como_recuerdo():
    datos = ficha_completa().model_dump(mode="json")
    datos["destinatario"]["elementos"] = [
        e for e in datos["destinatario"]["elementos"] if e["tipo"] != "recuerdo"]
    assert modulo.que_falta(FichaDeEntrevista.model_validate(datos)) == ["recuerdo"]


def test_otro_sin_sus_palabras_literales_es_error():
    with pytest.raises(ValidationError):
        ficha_completa(genero="otro")


def test_otro_con_sus_palabras_literales_vale():
    f = ficha_completa(genero="otro",
                       literales_de_otro={"genero": "piratas en el espacio"})
    assert f.literales_de_otro["genero"] == "piratas en el espacio"


def test_un_valor_fuera_de_la_lista_es_error():
    with pytest.raises(ValidationError):
        ficha_completa(tono="melancolico")


def test_la_extension_no_se_puede_fijar():
    """`RF-03`: no se pregunta, y un campo desconocido no entra en silencio."""
    with pytest.raises(ValidationError):
        ficha_completa(extension={"capitulos": 3})
    assert EXTENSION == {"capitulos": 10, "palabras_por_capitulo": [1000, 1500]}


def test_a_brief_de_una_ficha_incompleta_falla_en_vez_de_dar_medio_brief():
    with pytest.raises(modulo.FichaIncompleta) as e:
        modulo.a_brief(FichaDeEntrevista(ocasion="boda"))
    assert "nombre" in str(e.value)


def test_a_brief_solo_lleva_los_hechos_confirmados():
    f = ficha_completa(hechos_propuestos=[
        {"id": "h1", "texto": "vivio en Oporto", "estado": "confirmado"},
        {"id": "h2", "texto": "odia el cafe", "estado": "propuesto"},
        {"id": "h3", "texto": "tiene un barco", "estado": "descartado"}])
    brief = modulo.a_brief(f)
    assert [h.id for h in brief.hechos_propuestos] == ["h1"]


def test_el_brief_acepta_la_seccion_destinatario(completa):
    datos = carga.cargar_brief().model_dump(mode="json")
    datos["destinatario"] = modulo.a_brief(completa).model_dump(mode="json")
    b = BriefDeObra.model_validate(datos)
    assert b.destinatario.destinatario.nombre == "Irene Valdés"


def test_el_brief_de_hoy_sigue_cargando_sin_destinatario():
    assert carga.cargar_brief().destinatario is None
