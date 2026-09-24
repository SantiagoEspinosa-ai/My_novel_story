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


# --- `SPEC-32` `RF-06`, `RF-07`: la extension se pregunta ------------------------

def test_la_primera_pregunta_no_fija_las_palabras(con):
    """Antes anunciaba «de 1000 a 1500 palabras cada uno»: la extension no se
    preguntaba, se informaba. Ahora se pregunta; los diez capitulos si se anuncian."""
    e = service.crear(con)
    assert "10 capitulos" in e.pregunta
    assert "palabras" not in e.pregunta


def test_el_prompt_ofrece_las_tres_opciones_de_extension(con):
    e = service.crear(con)
    agente = Entrevistador([_dice(ficha_completa())])
    _turno(con, e.id, agente)
    prompt = agente.llamadas[0]
    assert "no se pregunta" not in prompt
    for opcion, (desde, hasta) in (("corta", (1000, 1150)), ("media", (1150, 1350)),
                                   ("larga", (1350, 1500))):
        assert "{0}: de {1} a {2} palabras".format(opcion, desde, hasta) in prompt


def test_las_opciones_del_prompt_salen_de_la_configuracion(con):
    """Si el prompt tuviera los rangos escritos, cambiar `sistema.json` no
    cambiaria lo que se le ofrece al comprador: dos copias que divergen."""
    from app.commons.dominio.enumeraciones import ExtensionDeCapitulo as X
    e = service.crear(con)
    agente = Entrevistador([_dice(ficha_completa())])
    service.turno(con, e.id, "r", agente, REGLAS, anio_actual=2026, extensiones={
        X.CORTA: (1000, 1100), X.MEDIA: (1100, 1300), X.LARGA: (1300, 1500)})
    assert "corta: de 1000 a 1100 palabras" in agente.llamadas[0]


def test_la_ficha_cerrada_lleva_la_extension_elegida(con):
    e = service.crear(con)
    _turno(con, e.id, Entrevistador([_dice(ficha_completa(extension="larga"))]))
    assert service.cerrar(con, e.id).extension.value == "larga"


# --- `PLAN-29` E8: la entrevista, en la misma sesion -------------------------------

def _observar(con):
    from app.commons.observabilidad.exportador import ExportadorEnMemoria
    from app.commons.observabilidad.observacion import Observacion
    exportador = ExportadorEnMemoria()

    def fabrica(obra, nombre, con_=None):
        return Observacion(exportador, con=con, obra=obra, nombre=nombre)
    return fabrica, exportador


def _enviados(exportador, tipo):
    return [e for t, e in exportador.enviados if t == tipo]


def test_un_turno_es_una_traza_en_la_sesion_de_su_obra(con):
    from app.commons.observabilidad.envio import sesion_de
    fabrica, exportador = _observar(con)
    t = service.crear(con)
    service.turno(con, t.id, "respuesta", Entrevistador([_dice(ficha_completa())]),
                  REGLAS, anio_actual=2026, observar=fabrica)
    trazas = _enviados(exportador, "traza")
    assert [tr["nombre"] for tr in trazas] == ["turno_de_entrevista"]
    assert trazas[0]["sesion"] == sesion_de(t.obra)
    spans = _enviados(exportador, "span")
    assert [s["nombre"] for s in spans] == ["entrevistador"]


def test_la_entrevista_y_la_generacion_de_la_misma_obra_comparten_sesion(con):
    """`SPEC-29` `RF-01`, `RF-12`: el valor nace con la entrevista y la obra lo hereda."""
    from app.commons.observabilidad.exportador import ExportadorEnMemoria
    from app.commons.observabilidad.observacion import Observacion
    fabrica, exportador = _observar(con)
    t = service.crear(con)
    service.turno(con, t.id, "respuesta", Entrevistador([_dice(ficha_completa())]),
                  REGLAS, anio_actual=2026, observar=fabrica)
    generacion = Observacion(ExportadorEnMemoria(), obra=t.obra)
    assert _enviados(exportador, "traza")[0]["sesion"] == generacion.sesion


def test_un_turno_con_ficha_invalida_da_score_schema_falla(con):
    fabrica, exportador = _observar(con)
    t = service.crear(con)
    service.turno(con, t.id, "respuesta",
                  Entrevistador([{"sin": "ficha"}, _dice(ficha_completa())]),
                  REGLAS, anio_actual=2026, observar=fabrica)
    schema = [s["categoria"] for s in _enviados(exportador, "score") if s["nombre"] == "schema"]
    assert schema == ["falla", "pasa"]
    assert len(_enviados(exportador, "span")) == 2


def test_nada_de_la_ficha_ni_de_la_respuesta_sube_en_un_turno(con):
    fabrica, exportador = _observar(con)
    t = service.crear(con)
    service.turno(con, t.id, "RESPUESTA-DEL-COMPRADOR-8812",
                  Entrevistador([_dice(ficha_completa(), pregunta="PREGUNTA-5530")]),
                  REGLAS, anio_actual=2026, observar=fabrica)
    todo = repr(exportador.enviados)
    for dato in ("RESPUESTA-DEL-COMPRADOR-8812", "PREGUNTA-5530", "Irene", "Brisa", "Lisboa"):
        assert dato not in todo, dato
