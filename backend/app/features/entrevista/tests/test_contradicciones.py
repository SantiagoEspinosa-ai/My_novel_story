"""`SPEC-25` `RF-08`, `RF-08b` y `RF-09`: tres contradicciones deterministas.

Cada tipo tiene su caso positivo **y** su negativo: una comprobacion que solo se
ha visto disparar podria estar disparando siempre.
"""

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.dominio.enumeraciones import TipoDeContradiccion as TC
from app.features.entrevista.contradicciones import contradicciones
from app.features.entrevista.tests.conftest import ficha_completa

REGLAS = ReglasDeContradiccion()
HOY = 2026


def _tipos(ficha, reglas=REGLAS):
    return [c.tipo for c in contradicciones(ficha, reglas, HOY).abiertas]


def _con_edad(edad, **cambios):
    f = ficha_completa(**cambios).model_dump(mode="json")
    f["destinatario"]["edad"] = edad
    f["destinatario"]["elementos"] = [
        e for e in f["destinatario"]["elementos"] if e["tipo"] != "recuerdo"]
    return type(ficha_completa()).model_validate(f)


def _con_recuerdo(edad, momento):
    f = ficha_completa().model_dump(mode="json")
    f["destinatario"]["edad"] = edad
    f["destinatario"]["elementos"] = [
        {"tipo": "recuerdo", "descripcion": "algo", "momento": momento}]
    return type(ficha_completa()).model_validate(f)


def test_edad_frente_a_genero_positivo():
    assert _tipos(_con_edad(8, genero="romance")) == [TC.EDAD_FRENTE_A_GENERO]


def test_edad_frente_a_genero_negativo():
    assert _tipos(_con_edad(30, genero="romance")) == []
    assert _tipos(_con_edad(8, genero="aventura")) == []


def test_edad_frente_a_ocasion_positivo():
    assert _tipos(_con_edad(15, ocasion="boda")) == [TC.EDAD_FRENTE_A_OCASION]


def test_edad_frente_a_ocasion_negativo():
    assert _tipos(_con_edad(15, ocasion="cumpleanos")) == []
    assert _tipos(_con_edad(40, ocasion="jubilacion")) == []


def test_recuerdo_antes_de_nacer():
    assert _tipos(_con_recuerdo(10, {"anio": 2001})) == [TC.RECUERDO_FRENTE_A_EDAD]


def test_recuerdo_a_una_edad_que_no_ha_cumplido():
    assert _tipos(_con_recuerdo(25, {"edad": 30})) == [TC.RECUERDO_FRENTE_A_EDAD]


def test_recuerdo_coherente():
    assert _tipos(_con_recuerdo(25, {"edad": 20, "anio": 2021})) == []


def test_las_parejas_son_configuracion():
    """`RF-08`: cambiar la regla cambia el resultado sin tocar codigo."""
    reglas = ReglasDeContradiccion(edad_minima_por_genero={"misterio": 10})
    assert _tipos(_con_edad(8, genero="misterio"), reglas) == [TC.EDAD_FRENTE_A_GENERO]


def test_otro_pide_juicio_y_nunca_dice_sin_contradiccion():
    """`RF-08b`: con `otro` el codigo no sabe, y lo dice."""
    r = contradicciones(
        _con_edad(8, genero="otro", literales_de_otro={"genero": "de miedo"}),
        REGLAS, HOY)
    assert r.abiertas == []
    assert r.requiere_juicio == ["genero"]


def test_una_contradiccion_resuelta_no_vuelve_a_abrirse():
    """`RF-09`: confirmar que es intencionado la cierra, y queda anotado."""
    f = _con_edad(8, genero="romance")
    [c] = contradicciones(f, REGLAS, HOY).abiertas
    datos = f.model_dump(mode="json")
    datos["contradicciones_resueltas"] = [
        {"tipo": c.tipo.value, "descripcion": c.descripcion,
         "resolucion": "es un cuento de princesas, sin romance adulto"}]
    resuelta = type(f).model_validate(datos)
    assert contradicciones(resuelta, REGLAS, HOY).abiertas == []


def test_sin_edad_no_se_afirma_nada():
    f = ficha_completa(genero="romance").model_dump(mode="json")
    f["destinatario"]["edad"] = None
    assert _tipos(type(ficha_completa()).model_validate(f)) == []
