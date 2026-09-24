"""`PLAN-29` E6: los scores de los validadores (`SPEC-29` `RF-04`).

De cada intento, de las rondas del plan y del cierre sale un score por validador. Lo que
**no** sube es la descripcion de un hallazgo: cita el texto.
"""

import pathlib
import re
import sqlite3

import pytest

from app.commons.dominio.enumeraciones import EstadoDeHallazgo
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.commons.observabilidad.observacion import Observacion
from app.features.orquestacion import ciclo, observar
from app.features.orquestacion.bucle import Resultado
from app.features.verificacion import puertas


def _obs():
    return Observacion(ExportadorEnMemoria(), con=sqlite3.connect(":memory:"), obra="obra-a")


def _scores(obs):
    return [e for t, e in obs.exportador.enviados if t == "score"]


def _por_nombre(obs):
    return {s["nombre"]: s for s in _scores(obs)}


def _hallazgo(inv, estado=EstadoDeHallazgo.ABIERTO, descripcion="cita DATO-SECRETO-3301"):
    from app.commons.dominio.modelos import Hallazgo
    from app.commons.invariantes.registro import TODAS
    return Hallazgo(invariante=inv, verificador="verificador_de_reglas", escena="e1",
                    severidad=TODAS[inv].severidad, estado=estado, descripcion=descripcion)


def _ciclo(hallazgos=(), **kw):
    """`kw` va al `Ciclo`: su `fallo` es el del intento, no el de la generacion."""
    return ciclo.Ciclo(escena="e1", generacion=Resultado(escena="e1", version=1,
                                                          hallazgos=list(hallazgos)), **kw)


def test_la_lista_de_la_puerta_coincide_con_la_que_verificar_puede_emitir():
    fuente = pathlib.Path(puertas.__file__).read_text(encoding="utf-8")
    emitidas = set(re.findall(r'(?:_hallazgo|dato_ausente)\(\s*"(INV-\d+)"', fuente))
    assert emitidas and emitidas == set(puertas.INVARIANTES_DE_LA_PUERTA)


def test_cada_invariante_de_la_puerta_da_un_score_pasa_o_falla():
    obs = _obs()
    observar.del_ciclo(obs, _ciclo([_hallazgo("INV-17"),
                                    _hallazgo("INV-04", EstadoDeHallazgo.SIN_VEREDICTO)]))
    s = _por_nombre(obs)
    for inv in puertas.INVARIANTES_DE_LA_PUERTA:
        assert inv in s, inv
    assert s["INV-17"]["categoria"] == "falla"
    assert s["INV-04"]["categoria"] == "sin_veredicto", "un dato ausente no es un aprobado"
    assert s["INV-01"]["categoria"] == "pasa"
    assert s["schema"]["categoria"] == "pasa"
    assert "DATO-SECRETO-3301" not in repr(obs.exportador.enviados)


def test_una_nota_del_editor_es_un_score_numerico_por_criterio():
    obs = _obs()
    observar.del_ciclo(obs, _ciclo(veredicto={"valoraciones": [
        {"criterio": "tono", "nota": 4, "justificacion": "JUSTIFICACION-SECRETA"},
        {"criterio": "ritmo", "nota": 2, "justificacion": "otra"}]}))
    s = _por_nombre(obs)
    assert s["INV-26.tono"]["valor"] == 4 and s["INV-26.ritmo"]["valor"] == 2
    assert "JUSTIFICACION-SECRETA" not in repr(obs.exportador.enviados)


def test_un_editor_ilegible_es_sin_veredicto_y_no_aprobado():
    obs = _obs()
    observar.del_ciclo(obs, _ciclo(veredicto={"veredicto": "SIN_VEREDICTO"}))
    assert _por_nombre(obs)["INV-26"]["categoria"] == "sin_veredicto"


def test_un_fallo_de_contrato_es_score_schema_falla():
    obs = _obs()
    c = ciclo.Ciclo(escena="e1", generacion=Resultado(escena="e1", fallo="contrato"),
                    fallo="contrato")
    observar.del_ciclo(obs, c)
    s = _por_nombre(obs)
    assert s["schema"]["categoria"] == "falla"
    assert "INV-17" not in s, "sin texto, la puerta no miro nada y no se afirma que pase"


def test_inv22_da_cuantos_nombres_mal_escritos_y_nunca_los_nombres():
    from types import SimpleNamespace
    obs = _obs()
    observar.del_ciclo(obs, _ciclo(fallo="nombre_mal_escrito", nombres_comprobados=True,
                                   nombres_encontrados=[SimpleNamespace(escrito="Irena",
                                                                        correcto="Irene")]))
    assert _por_nombre(obs)["INV-22"]["valor"] == 1
    assert "Iren" not in repr(obs.exportador.enviados)


def test_inv23_da_un_score_por_imprescindible_con_su_id():
    obs = _obs()
    observar.del_ciclo(obs, _ciclo(imprescindibles_comprobados=["imp-01", "imp-02"],
                                   imprescindibles_ausentes=["imp-02"]))
    inv23 = {s["referencia"]: s["categoria"] for s in _scores(obs) if s["nombre"] == "INV-23"}
    assert inv23 == {"imp-01": "pasa", "imp-02": "falla"}


def test_inv24_inv25_inv27_llegan_al_cerrar():
    obs = _obs()
    observar.del_cierre(obs, {"estado": "terminada", "faltan": [],
                              "repeticiones": [("e3", 9)], "frases": [],
                              "juicio": [{"invariante": "INV-27", "estado": "abierto",
                                          "descripcion": "FINAL-SECRETO"}]}, ronda=1)
    s = _por_nombre(obs)
    assert s["INV-24"]["categoria"] == "pasa"
    assert s["INV-25"]["valor"] == 1
    assert s["INV-27"]["categoria"] == "falla"
    assert "FINAL-SECRETO" not in repr(obs.exportador.enviados)


def test_una_novela_incompleta_no_dice_que_inv27_pase():
    obs = _obs()
    observar.del_cierre(obs, {"estado": "novela_incompleta", "faltan": ["un galgo"],
                              "repeticiones": [], "frases": [], "juicio": []}, ronda=1)
    s = _por_nombre(obs)
    assert s["INV-24"]["categoria"] == "falla"
    assert s["INV-27"]["categoria"] == "no_aplica"
    assert "galgo" not in repr(obs.exportador.enviados)


def test_las_rondas_del_plan_dan_scores_de_schema_cobertura_y_revisor():
    obs = _obs()
    observar.de_las_rondas_del_plan(obs, [
        {"version": 1, "aprobado": False, "origen": "esquema", "objeciones": ["x"]},
        {"version": 2, "aprobado": False, "origen": "codigo", "objeciones": ["HUECO"]},
        {"version": 3, "aprobado": True, "origen": "revisor", "objeciones": []}])
    por_ronda = {(s["nombre"], s["referencia"]): s["categoria"] for s in _scores(obs)}
    assert por_ronda[("schema.plan", "ronda-1")] == "falla"
    assert ("cobertura.plan", "ronda-1") not in por_ronda
    assert por_ronda[("cobertura.plan", "ronda-2")] == "falla"
    assert por_ronda[("revisor.plan", "ronda-3")] == "pasa"
    assert "HUECO" not in repr(obs.exportador.enviados)


# --- `PLAN-29` E7: las vetadas, con su nivel ---------------------------------------

def _vetadas(obs, catalogo, encontradas):
    from types import SimpleNamespace
    obs.vetadas = catalogo
    observar.del_ciclo(obs, _ciclo(fallo="palabra_vetada", vetadas_comprobadas=True,
                                   vetadas_encontradas=[SimpleNamespace(vetada=f,
                                                                        fragmento=f)
                                                        for f in encontradas]))
    return [s for s in _scores(obs) if s["nombre"] == "INV-21"]


def _v(forma, nivel, id_):
    from app.commons.dominio.enumeraciones import NivelDeVeto
    from app.features.politica.repository import Vetada
    return Vetada(forma, NivelDeVeto(nivel), id_)


def test_una_coincidencia_global_sube_con_su_termino():
    s = _vetadas(_obs(), {"zoquete": _v("zoquete", "global", 3)}, ["zoquete"])
    assert s == [{"traza": s[0]["traza"], "nombre": "INV-21", "categoria": "falla",
                  "nivel": "global", "referencia": "vetada-global-3", "termino": "zoquete"}]


def test_una_coincidencia_de_novela_sube_con_su_nivel_y_su_id_y_sin_el_termino():
    obs = _obs()
    s = _vetadas(obs, {"marisol": _v("marisol", "novela", 41)}, ["marisol"])
    assert s[0]["nivel"] == "novela" and s[0]["referencia"] == "vetada-novela-41"
    assert "termino" not in s[0]
    assert "marisol" not in repr(obs.exportador.enviados)


def test_una_coincidencia_de_franja_no_lleva_el_termino():
    obs = _obs()
    s = _vetadas(obs, {"calavera": _v("calavera", "franja_de_edad", 7)}, ["calavera"])
    assert s[0]["nivel"] == "franja_de_edad" and "termino" not in s[0]
    assert "calavera" not in repr(obs.exportador.enviados)


def test_sin_coincidencias_inv21_pasa_si_se_comprobo():
    obs = _obs()
    observar.del_ciclo(obs, _ciclo(vetadas_comprobadas=True))
    assert _por_nombre(obs)["INV-21"]["categoria"] == "pasa"
    obs = _obs()
    observar.del_ciclo(obs, _ciclo())
    assert "INV-21" not in _por_nombre(obs), "sin lista no se miro: no se dice que pase"
