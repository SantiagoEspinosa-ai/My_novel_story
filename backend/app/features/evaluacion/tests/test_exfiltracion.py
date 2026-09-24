"""`PLAN-31` E7: exfiltracion entre dos novelas de la misma base, con dobles (`SPEC-31` `RF-12`).

Dos fichas con nombres y palabras clave disjuntos (`harness/adversarial/`). Se escriben las
dos en la misma base, la A primero, con dobles que **guardan cada prompt que reciben**, y en
ningun prompt de la B puede aparecer nada de la A. El rastro normaliza como las vetadas
(`commons/politica/`): una tilde o una mayuscula no esconden un nombre.
"""

import pathlib
import re
import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.modelo.doble import DELTA_OK
from app.features.evaluacion import briefs, exfiltracion

ADVERSARIAL = pathlib.Path(__file__).resolve().parents[5] / "harness" / "adversarial"
CRITERIOS = ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")


def _brief(letra):
    return briefs.cargar(ADVERSARIAL / "brief-exfiltracion-{0}.json".format(letra))


def test_el_rastro_encuentra_un_nombre_de_la_otra_novela_aunque_cambie_la_tilde():
    textos = ["Marisol se asomo a la borda.", "La verbena de RODRIGO empezaba tarde.",
              "En el ferry a MENÓRCA no habia sitio."]
    huellas = exfiltracion.rastro(textos, ["Rodrigo Peñalver", "Menorca", "acordeon"])
    assert [(h.clave, h.texto) for h in huellas] == [("Rodrigo Peñalver", 1), ("Menorca", 2)]
    assert huellas[0].fragmento == "RODRIGO"


def test_las_claves_de_un_brief_sin_claves_declaradas_son_sus_nombres():
    b = _brief("a").model_copy(update={"claves_de_rastro": None})
    assert exfiltracion.claves_de(b) == ["Rodrigo Peñalver", "Canela", "El acordeon de Albacete"]


def test_las_dos_fichas_del_red_team_son_disjuntas():
    """Si compartieran una clave, un rastro limpio no diria nada."""
    a, b = _brief("a"), _brief("b")
    assert not exfiltracion.rastro([b.ficha.model_dump_json()], exfiltracion.claves_de(a))
    assert not exfiltracion.rastro([a.ficha.model_dump_json()], exfiltracion.claves_de(b))


# --- Dos novelas en la misma base -------------------------------------------------

class _Captura:
    def __init__(self, respuesta, prompts):
        self.r, self.prompts, self.nombre = respuesta, prompts, "doble"
        self.reglas, self.entorno = None, {}

    def llamar(self, prompt):
        self.prompts.append(prompt)
        return self.r(prompt) if callable(self.r) else self.r


def _plan_de(ficha):
    d = ficha.destinatario
    pila = d.nombre.split()[0].lower()
    mascota = next(e for e in d.elementos if e.tipo.value == "mascota")
    imprescindibles = [e for e in d.elementos if e.imprescindible]
    return {
        "mundo": {"lugares": [{"id": "lug-casa", "nombre": "Casa", "accesos": []}],
                  "personajes": [
                      {"id": "per-" + pila, "nombre": d.nombre, "empieza_en": "lug-casa",
                       "fecha_de_nacimiento": "1980-01-01"},
                      {"id": "per-" + mascota.nombre.lower(), "nombre": mascota.nombre,
                       "empieza_en": "lug-casa"}]},
        "capitulos": [{"id": "cap-{0:02d}".format(n), "titulo": "Capitulo {0}".format(n),
                       "escenas": [{"eje": "vinculo", "signo": "positivo", "lugar": "lug-casa",
                                    "pov": "per-" + pila,
                                    "sinopsis": "{0} sigue su dia.".format(d.nombre.split()[0]),
                                    "t_fabula": "2026-06-{0:02d}".format(n)}]}
                      for n in range(1, 11)],
        "imprescindibles": [{"elemento": e.descripcion, "capitulo": "cap-01",
                             "palabras_clave": [e.nombre or e.descripcion.split()[-1]]}
                            for e in imprescindibles],
    }


def _agentes(b, prompts):
    f = b.ficha
    pila = f.destinatario.nombre.split()[0]
    plan = _plan_de(f)
    claves = [i["palabras_clave"][0] for i in plan["imprescindibles"]]
    texto = " ".join(["palabra"] * (1200 - len(claves) - 1) + [pila] + claves)

    def escritor(prompt):
        m = re.search(r"[\w-]*per-" + pila.lower(), prompt)
        return {"texto": texto, "pov_usado": m.group(0) if m else "per-" + pila.lower(),
                "delta": DELTA_OK}
    return {
        "planificador": _Captura({"titulo": f.titulo, "premisa": f.premisa, "plan": plan},
                                 prompts),
        "revisor": _Captura({"aprobado": True, "objeciones": []}, prompts),
        "escritor": _Captura(escritor, prompts),
        "editor": _Captura({"valoraciones": [
            {"criterio": c, "nota": 4, "justificacion": "bien"} for c in CRITERIOS]}, prompts),
        "resumidor": _Captura({"texto": "{0} avanza.".format(pila), "hechos_clave": []},
                              prompts),
    }


def _dos_novelas(tmp_path):
    from app.features.orquestacion import novela
    c = sqlite3.connect(str(tmp_path / "evaluacion.db"))
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    a, b = _brief("a"), _brief("b")
    prompts_a, prompts_b = [], []
    novela.escribir(c, "obra-a", a.ficha, _agentes(a, prompts_a), hasta_capitulo=3,
                    carpeta_de_reglas=str(tmp_path))
    novela.escribir(c, "obra-b", b.ficha, _agentes(b, prompts_b), hasta_capitulo=3,
                    carpeta_de_reglas=str(tmp_path))
    return a, b, prompts_a, prompts_b


@pytest.mark.xfail(strict=True, reason=(
    "F-100: `consolidacion/mundo.leer(con)` no filtra por obra y `obra.reunir_material` lo "
    "manda entero al Escritor: el prompt de la B lleva los personajes, los lugares y el "
    "conocimiento de la A (`obra-a-per-rodrigo`, `obra-a-per-canela`). `entidad`, `lugar` y "
    "`conocimiento` no tienen columna de obra: el arreglo decide algo y no es de este plan"))
def test_la_segunda_novela_no_recibe_nada_de_la_primera(tmp_path):
    a, b, prompts_a, prompts_b = _dos_novelas(tmp_path)
    assert prompts_b, "la novela B tiene que haber llamado a algun agente"
    assert exfiltracion.rastro(prompts_a, exfiltracion.claves_de(a)), \
        "sus propias claves si llegan a la A: si no, el rastro no mira nada"
    huellas = exfiltracion.rastro(prompts_b, exfiltracion.claves_de(a))
    assert huellas == [], "a la novela B le llega {0}".format(
        sorted({(h.clave, h.fragmento) for h in huellas}))


def _respuestas_de_las_tools(con, obra, ids):
    from app.commons.dominio import story_bible as sb
    from app.features.orquestacion import story_bible
    salida = [story_bible.leer_hechos(con, obra, sb.EntradaHechos()).model_dump_json(),
              story_bible.leer_cronologia(con, obra, sb.EntradaCronologia()).model_dump_json()]
    for i in ids:
        salida.append(story_bible.leer_ficha(con, obra, sb.EntradaFicha(id=i))
                      .model_dump_json())
    return salida


def _ids_del_plan(con, obra):
    from app.features.planificacion import repository as planes
    plan = planes.aprobado(con, obra)
    return [p.id for p in plan.mundo.personajes] + [l.id for l in plan.mundo.lugares]


def test_las_tools_de_la_story_bible_de_la_b_no_devuelven_nada_de_la_a(tmp_path):
    """`SPEC-28` `RF-06`: las tres lecturas estan acotadas a la obra de la delegacion. Se
    le piden a la B todos sus ids y tambien los de la A: los de la A no existen para ella."""
    from app.commons.dominio import story_bible as sb
    from app.features.orquestacion import story_bible
    a, _, _, _ = _dos_novelas(tmp_path)
    con = sqlite3.connect(str(tmp_path / "evaluacion.db"))
    respuestas = _respuestas_de_las_tools(con, "obra-b", _ids_del_plan(con, "obra-b"))
    for ajeno in _ids_del_plan(con, "obra-a"):
        with pytest.raises(story_bible.NoExisteEnLaObra):
            story_bible.leer_ficha(con, "obra-b", sb.EntradaFicha(id=ajeno))
    assert exfiltracion.rastro(_respuestas_de_las_tools(con, "obra-a", _ids_del_plan(
        con, "obra-a")), exfiltracion.claves_de(a)), "a la A si le llegan sus claves"
    assert exfiltracion.rastro(respuestas, exfiltracion.claves_de(a)) == []


def test_sin_el_filtro_de_obra_la_prueba_de_las_tools_lo_caza(tmp_path, monkeypatch):
    """Antes de fiarse de un verde, se quita el filtro de obra de una lectura a proposito
    (`PLAN-31` E7) y la misma comprobacion tiene que encontrar la fuga. `F-40` es la
    version accidental de este caso."""
    from app.features.escaleta import repository as escaleta
    a, _, _, _ = _dos_novelas(tmp_path)
    original = escaleta.hechos_declarados
    monkeypatch.setattr(escaleta, "hechos_declarados", lambda con, obra: (
        original(con, "obra-a") + original(con, obra)))
    con = sqlite3.connect(str(tmp_path / "evaluacion.db"))
    respuestas = _respuestas_de_las_tools(con, "obra-b", _ids_del_plan(con, "obra-b"))
    assert exfiltracion.rastro(respuestas, exfiltracion.claves_de(a)),         "sin el filtro, los imprescindibles de la A llegan a la B y el rastro lo ve"
