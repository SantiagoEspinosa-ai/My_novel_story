"""`PLAN-22` E13b: la inspeccion visual lanzada por el harness, con hallazgo y scores.

`backend/inspeccion_visual.py` delega en el agente `inspector_visual`, juzga su veredicto
(`auditoria/visual.py`), deja el hallazgo `INV-30` si hace falta y sube un score
`INV-30.<pieza>` por comprobacion en la sesion de la obra. Aqui con un doble del agente:
la ejecucion real es E13b.2.
"""

import sqlite3

import inspeccion_visual
import semilla_lectura
from app.commons.observabilidad.envio import sesion_de
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.commons.observabilidad.observacion import Observacion
from app.features.auditoria import visual


class Inspector:
    def __init__(self, respuesta):
        self.respuesta, self.prompts = respuesta, []

    def llamar(self, prompt):
        self.prompts.append(prompt)
        return self.respuesta


def _veredicto(falla=None):
    return {"comprobaciones": [
        {"pieza": p, "veredicto": "falla" if p == falla else "pasa",
         "motivo": "motivo inventado de {0}".format(p)} for p in visual.PIEZAS]}


def _inv30(ruta):
    con = sqlite3.connect(ruta)
    filas = con.execute("SELECT invariante, estado, descripcion FROM hallazgo "
                        "WHERE invariante = 'INV-30'").fetchall()
    con.close()
    return filas


def _montar(tmp_path):
    ruta = str(tmp_path / "s.db")
    semilla_lectura.sembrar(ruta)
    obs = Observacion(ExportadorEnMemoria(), con=sqlite3.connect(ruta),
                      obra=semilla_lectura.OBRA, nombre="inspeccion_visual")
    return ruta, obs


def _scores(obs):
    return {s["nombre"]: s for t, s in obs.exportador.enviados if t == "score"}


def test_un_veredicto_con_una_pieza_que_falla_deja_inv30_y_su_score(tmp_path):
    ruta, obs = _montar(tmp_path)
    r = inspeccion_visual.inspeccionar(ruta, semilla_lectura.OBRA, "http://localhost:1/x",
                                       Inspector(_veredicto(falla="enlaces")), obs)
    assert r.estado == "falla"
    [(inv, estado, descripcion)] = _inv30(ruta)
    assert (inv, estado) == ("INV-30", "abierto") and "enlaces" in descripcion
    scores = _scores(obs)
    assert scores["INV-30.enlaces"]["categoria"] == "falla"
    assert scores["INV-30.portada"]["categoria"] == "pasa"
    assert scores["INV-30"]["categoria"] == "falla"


def test_cada_pieza_sube_como_score_en_la_sesion_de_la_obra(tmp_path):
    ruta, obs = _montar(tmp_path)
    inspeccion_visual.inspeccionar(ruta, semilla_lectura.OBRA, "http://localhost:1/x",
                                   Inspector(_veredicto()), obs)
    enviados = obs.exportador.enviados
    scores = [s for t, s in enviados if t == "score"]
    assert sorted(s["nombre"] for s in scores) == sorted(
        ["INV-30"] + ["INV-30.{0}".format(p) for p in visual.PIEZAS])
    assert all(s["categoria"] == "pasa" for s in scores)
    trazas = [e for t, e in enviados if t == "traza"]
    assert trazas and all(t["sesion"] == sesion_de(semilla_lectura.OBRA) for t in trazas)
    assert _inv30(ruta) == [], "un veredicto limpio no deja hallazgo"
    # El motivo del agente no sube: puede citar el texto de la obra.
    assert not any("motivo inventado" in str(s) for s in scores)


def test_un_inspector_ilegible_sube_sin_veredicto_y_deja_el_hallazgo(tmp_path):
    ruta, obs = _montar(tmp_path)
    r = inspeccion_visual.inspeccionar(ruta, semilla_lectura.OBRA, "http://localhost:1/x",
                                       Inspector({"texto": "me parece bien"}), obs)
    assert r.estado == "sin_veredicto"
    assert [(i, e) for i, e, _ in _inv30(ruta)] == [("INV-30", "sin_veredicto")]
    scores = _scores(obs)
    assert scores["INV-30"]["categoria"] == "sin_veredicto"
    assert not any(n.startswith("INV-30.") for n in scores)
