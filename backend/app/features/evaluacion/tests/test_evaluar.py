"""`PLAN-31` E10: el guion de ejecucion real de un brief, con dobles.

`evaluar.py` gasta dinero de verdad, asi que antes de empezar enseña lo gastado, lo que
queda hasta el techo y el mayor coste medido de una novela completa, y no empieza sin
`--confirmo-el-gasto`. Aqui todo corre con dobles: `main` recibe los agentes, Lean, el
exportador y el Entrevistador por parametro, y la ejecucion real usa los de verdad.
"""

import pathlib
import sqlite3

import pytest

import evaluar
from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.features.evaluacion import briefs
from app.features.evaluacion import repository as libro
from app.features.evaluacion.tests import dobles

RAIZ = pathlib.Path(__file__).resolve().parents[5]
EVALS = RAIZ / "harness" / "evals"


class _Llamados:
    """Cuenta si alguien pidio los agentes: sin confirmar, nadie tiene que pedirlos."""

    def __init__(self, ficha=None):
        self.veces, self.ficha, self.agentes = 0, ficha, None

    def __call__(self, sistema, entorno, ficha):
        self.veces += 1
        self.ficha = ficha
        self.agentes = dobles.agentes_para(ficha, coste=0.01)
        return self.agentes


def _dobles(llamados, lean=None, guion=None):
    d = {"agentes": llamados, "lean": lean or dobles.LeanFijo(),
         "exportador": lambda: ExportadorEnMemoria()}
    if guion is not None:
        e, x = dobles.EntrevistadorDelGuion(guion), dobles.ExtractorDelGuion(guion)
        d["entrevistador"] = lambda: e
        d["extractor"] = lambda: x
    return d


def _argv(tmp_path, brief="brief-base", *extra):
    return [str(EVALS / (brief + ".json")), "--pasada", "antes",
            "--libro", str(tmp_path / "evaluacion.db"),
            "--base", str(tmp_path / "novela.db"),
            "--tabla", str(tmp_path / "resultados.md")] + list(extra)


def test_evaluar_no_empieza_sin_confirmar_el_gasto(tmp_path, capsys):
    llamados = _Llamados()
    codigo = evaluar.main(_argv(tmp_path), dobles=_dobles(llamados))
    salida = capsys.readouterr().out
    assert codigo == 2
    assert llamados.veces == 0, "sin confirmar no se pide ningun agente"
    for cifra in ("gastado:", "queda hasta el techo", "mayor coste medido de una novela"):
        assert cifra in salida, cifra
    assert "sin medir" in salida and "--confirmo-el-gasto" in salida
    assert libro.filas(sqlite3.connect(str(tmp_path / "evaluacion.db"))) == []


def test_evaluar_no_empieza_con_el_techo_alcanzado(tmp_path, capsys):
    con = sqlite3.connect(str(tmp_path / "evaluacion.db"))
    libro.anotar(con, ejecucion="brief-base-antes-1", brief="brief-base", pasada="antes",
                 capitulo="1", usd=150.0, delegaciones=3, sin_coste=0)
    con.close()
    llamados = _Llamados()
    codigo = evaluar.main(_argv(tmp_path, "brief-base", "--confirmo-el-gasto"),
                          dobles=_dobles(llamados))
    salida = capsys.readouterr().out
    assert codigo == 3 and llamados.veces == 0
    assert "techo" in salida and "150.0000 USD" in salida


def test_evaluar_con_dobles_deja_fila_en_el_libro_de_gasto_y_en_la_tabla(tmp_path, capsys):
    llamados = _Llamados()
    codigo = evaluar.main(_argv(tmp_path, "brief-base", "--confirmo-el-gasto"),
                          dobles=_dobles(llamados))
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    filas = libro.filas(sqlite3.connect(str(tmp_path / "evaluacion.db")))
    assert [f["capitulo"] for f in filas] == ["plan"] + [str(n) for n in range(1, 11)] + [
        "cierre"]
    assert {f["ejecucion"] for f in filas} == {"brief-base-antes-1"}
    assert sum(f["delegaciones"] for f in filas) == 33
    tabla = (tmp_path / "resultados.md").read_text(encoding="utf-8")
    fila = next(l for l in tabla.splitlines() if l.startswith("| brief-base |"))
    assert "pasó" in fila and "sin ejecutar" not in fila
    otra = next(l for l in tabla.splitlines() if l.startswith("| brief-injection |"))
    assert "sin ejecutar" in otra


def _en_base(argv, ruta):
    argv = list(argv)
    argv[argv.index("--base") + 1] = str(ruta)
    return argv


def test_una_segunda_ejecucion_del_mismo_brief_es_otra_ejecucion(tmp_path, capsys):
    for n in range(2):
        evaluar.main(_en_base(_argv(tmp_path, "brief-base", "--confirmo-el-gasto",
                                    "--capitulos", "1"), tmp_path / "novela-{0}.db".format(n)),
                     dobles=_dobles(_Llamados()))
    filas = libro.filas(sqlite3.connect(str(tmp_path / "evaluacion.db")))
    assert {f["ejecucion"] for f in filas} == {"brief-base-antes-1", "brief-base-antes-2"}


def test_evaluar_se_niega_a_escribir_en_una_base_con_otra_novela(tmp_path, capsys):
    """`F-100`: la segunda novela de una base recibe el mundo de la primera. Hasta que se
    arregle, cada ejecucion en su base; el libro de gasto si se comparte."""
    evaluar.main(_argv(tmp_path, "brief-base", "--confirmo-el-gasto", "--capitulos", "1"),
                 dobles=_dobles(_Llamados()))
    capsys.readouterr()
    llamados = _Llamados()
    codigo = evaluar.main(_argv(tmp_path, "brief-vetadas-por-variantes", "--confirmo-el-gasto",
                                "--capitulos", "1"), dobles=_dobles(llamados))
    salida = capsys.readouterr().out
    assert codigo == 4 and llamados.veces == 0
    assert "F-100" in salida


def test_evaluar_un_guion_hace_la_entrevista_contra_la_api_y_anota_su_coste(tmp_path, capsys):
    b = briefs.cargar(EVALS / "brief-injection.json")
    llamados = _Llamados()
    codigo = evaluar.main(_argv(tmp_path, "brief-injection", "--confirmo-el-gasto",
                                "--capitulos", "1"), dobles=_dobles(llamados, guion=b.guion))
    salida = capsys.readouterr().out
    assert codigo == 0, salida
    filas = libro.filas(sqlite3.connect(str(tmp_path / "evaluacion.db")))
    assert [f["capitulo"] for f in filas][:3] == ["entrevista", "plan", "1"]
    assert filas[0]["delegaciones"] == sum(1 for t in b.guion.turnos if not t.cerrar)
    assert filas[0]["ejecucion"] != filas[0]["obra"], "la obra la pone la entrevista"
    assert FichaDeEntrevista.model_validate(llamados.ficha.model_dump()).hechos_propuestos == []


def test_evaluar_pasa_el_rastro_contra_las_obras_anteriores(tmp_path, capsys):
    evaluar.main(_argv(tmp_path, "brief-base", "--confirmo-el-gasto", "--capitulos", "1"),
                 dobles=_dobles(_Llamados()))
    capsys.readouterr()
    evaluar.main(_en_base(_argv(tmp_path, "brief-vetadas-por-variantes", "--confirmo-el-gasto",
                                "--capitulos", "1"), tmp_path / "otra.db"),
                 dobles=_dobles(_Llamados()))
    salida = capsys.readouterr().out
    assert "=== RASTRO DE OTRAS NOVELAS ===" in salida
    assert "brief-base-antes-1: limpio" in salida
