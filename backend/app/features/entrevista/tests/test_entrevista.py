"""`SPEC-25` `RF-06`..`RF-10`: la entrevista por turnos (`PLAN-25` E8).

El doble del Entrevistador sigue un guion de fichas: en cada turno devuelve la
ficha que le toca y una pregunta. Lo que se comprueba es lo que decide el
**codigo** —que falta, que se contradice, si se puede cerrar—, que es lo que no
puede depender de que el modelo lo haga bien.
"""

import sqlite3

import pytest

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.features.entrevista import repository as repo
from app.features.entrevista import service
from app.features.entrevista.tests.conftest import ficha_completa

REGLAS = ReglasDeContradiccion()


class Entrevistador:
    """Devuelve, turno a turno, lo que dice su guion."""

    nombre = "doble-entrevistador"

    def __init__(self, respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        r = self.respuestas[min(len(self.llamadas) - 1, len(self.respuestas) - 1)]
        return r() if callable(r) else r


def _dice(ficha, pregunta="¿Y que mas?", **extra):
    datos = ficha if isinstance(ficha, dict) else ficha.model_dump(mode="json")
    return dict({"ficha": datos, "pregunta": pregunta}, **extra)


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    repo.asegurar_tablas(c)
    auditoria.asegurar_tabla(c)
    return c


def _turno(con, id_e, agente, respuesta="respuesta del comprador"):
    return service.turno(con, id_e, respuesta, agente, REGLAS, anio_actual=2026)


def test_crear_una_entrevista_devuelve_la_primera_pregunta_y_la_ficha_vacia(con):
    e = service.crear(con)
    assert e.obra.startswith("obra-")
    assert e.tema == "nombre"
    assert "10 capitulos" in e.pregunta


def test_la_entrevista_no_cierra_con_un_obligatorio_vacio(con):
    e = service.crear(con)
    sin_tono = ficha_completa().model_dump(mode="json")
    sin_tono["tono"] = None
    t = _turno(con, e.id, Entrevistador([_dice(sin_tono)]))
    assert t.falta == ["tono"] and t.tema == "tono"
    assert t.puede_cerrar is False
    with pytest.raises(service.NoSePuedeCerrar) as err:
        service.cerrar(con, e.id)
    assert "tono" in str(err.value)


def test_una_ficha_completa_se_cierra_y_da_el_brief(con):
    e = service.crear(con)
    t = _turno(con, e.id, Entrevistador([_dice(ficha_completa())]))
    assert t.puede_cerrar
    brief = service.cerrar(con, e.id)
    assert brief.destinatario.nombre == "Irene Valdés"


def test_una_contradiccion_bloquea_hasta_que_un_turno_la_resuelve(con):
    e = service.crear(con)
    nina = ficha_completa().model_dump(mode="json")
    nina["destinatario"]["edad"] = 8
    nina["genero"] = "romance"
    nina["destinatario"]["elementos"] = [
        x for x in nina["destinatario"]["elementos"] if x["tipo"] != "recuerdo"] + [
        {"tipo": "recuerdo", "descripcion": "su primer dia de cole",
         "momento": {"edad": 6}}]
    t1 = _turno(con, e.id, Entrevistador([_dice(nina)]))
    assert t1.puede_cerrar is False
    [c] = t1.contradicciones
    assert t1.tema == c.descripcion
    resuelta = dict(nina, contradicciones_resueltas=[
        {"tipo": c.tipo.value, "descripcion": c.descripcion,
         "resolucion": "un cuento de principes, sin romance adulto"}])
    t2 = _turno(con, e.id, Entrevistador([_dice(resuelta)]))
    assert t2.contradicciones == [] and t2.puede_cerrar
    tipos = [d["tipo"] for d in auditoria.decisiones(con, e.obra)]
    assert tipos == [TD.CONTRADICCION_DETECTADA, TD.CONTRADICCION_RESUELTA]
    assert service.cerrar(con, e.id).contradicciones_resueltas[0].resolucion.startswith(
        "un cuento")


def test_con_otro_el_juicio_del_modelo_bloquea_como_una_contradiccion(con):
    """`RF-08b`: el juicio queda marcado como juicio, no como comprobacion."""
    e = service.crear(con)
    rara = ficha_completa(genero="otro",
                          literales_de_otro={"genero": "terror gore"}).model_dump(
                              mode="json")
    rara["destinatario"]["edad"] = 9
    rara["destinatario"]["elementos"] = [
        {"tipo": "rasgo", "descripcion": "valiente"},
        {"tipo": "recuerdo", "descripcion": "la feria", "momento": {"edad": 7}}]
    t = _turno(con, e.id, Entrevistador([_dice(
        rara, juicios=["terror gore para un niño de 9 años"])]))
    assert t.requiere_juicio == ["genero"]
    assert [j.tipo.value for j in t.contradicciones] == ["juicio_del_modelo"]
    assert t.puede_cerrar is False


def test_el_nombre_de_pila_vetado_que_coincide_con_otro_avisa(con):
    """`RF-10`: vetar a «Brisa Ortega» cuando la perra se llama Brisa."""
    e = service.crear(con)
    f = ficha_completa(nombres_vetados=["Brisa Ortega"])
    t = _turno(con, e.id, Entrevistador([_dice(f)]))
    assert t.avisos and "Brisa" in t.avisos[0]
    assert t.puede_cerrar is False
    confirmado = _turno(con, e.id, Entrevistador([_dice(
        f, avisos_confirmados=["Brisa Ortega"])]))
    assert confirmado.avisos == [] and confirmado.puede_cerrar


def test_un_json_invalido_del_agente_no_toca_la_ficha(con):
    e = service.crear(con)
    _turno(con, e.id, Entrevistador([_dice(ficha_completa())]))
    antes = repo.leer(con, e.id).ficha
    roto = Entrevistador([_dice({"destinatario": {"edad": "muchos"}})])
    with pytest.raises(service.EntrevistadorIlegible):
        _turno(con, e.id, roto)
    assert len(roto.llamadas) == 3, "reintenta con el tope de transporte"
    assert repo.leer(con, e.id).ficha == antes


def test_el_reintento_le_dice_al_agente_que_fallo(con):
    e = service.crear(con)
    agente = Entrevistador([_dice({"tono": "melancolico"}), _dice(ficha_completa())])
    _turno(con, e.id, agente)
    assert "melancolico" in agente.llamadas[1] or "tono" in agente.llamadas[1]


def test_el_agente_no_puede_tocar_los_hechos_propuestos(con):
    """Los hechos del texto libre los gestiona el codigo: un modelo que los
    confirmara por su cuenta se saltaria `RF-13`."""
    e = service.crear(con)
    colado = ficha_completa().model_dump(mode="json")
    colado["hechos_propuestos"] = [{"id": "h-x", "texto": "inventado",
                                    "estado": "confirmado"}]
    t = _turno(con, e.id, Entrevistador([_dice(colado)]))
    assert t.ficha.hechos_propuestos == []


def test_el_prompt_lleva_lo_que_calculo_el_codigo(con):
    e = service.crear(con)
    agente = Entrevistador([_dice(ficha_completa())])
    _turno(con, e.id, agente, respuesta="Se llama Irene")
    prompt = agente.llamadas[0]
    assert "LO QUE FALTA" in prompt and "nombre" in prompt
    assert "Se llama Irene" in prompt


def test_cada_turno_se_guarda(con):
    e = service.crear(con)
    _turno(con, e.id, Entrevistador([_dice(ficha_completa(), pregunta="¿Algo mas?")]),
           respuesta="Irene, 34")
    [t] = repo.turnos(con, e.id)
    assert t["respuesta"] == "Irene, 34" and t["pregunta"] == "¿Algo mas?"


def test_una_entrevista_cerrada_no_admite_turnos(con):
    e = service.crear(con)
    _turno(con, e.id, Entrevistador([_dice(ficha_completa())]))
    service.cerrar(con, e.id)
    with pytest.raises(service.EntrevistaCerrada):
        _turno(con, e.id, Entrevistador([_dice(ficha_completa())]))
