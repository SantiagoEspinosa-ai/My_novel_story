"""`PLAN-26` E6: montar la obra a partir del plan aprobado.

Es lo que hacia `preparar` en el guion de la obra de diez capitulos, llevado a
`app/` para poder probarlo y reutilizarlo.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela
from app.features.planificacion.service import PlanAprobado
from app.features.planificacion.tests.conftest import ficha, plan


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _aprobado():
    return PlanAprobado(plan(), 1, "El mapa de Irene", "Irene sigue un mapa antiguo.")


def test_diez_capitulos_de_una_escena_de_mil_a_mil_quinientas(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    escenas = escaleta.escenas_de(con, "obra-x")
    assert len(escenas) == 10
    assert {e["capitulo"] for e in escenas} == {"cap-{0:02d}".format(n) for n in range(1, 11)}
    assert all(list(e["longitud_objetivo"]) == [1000, 1500] for e in escenas)


def test_cada_imprescindible_es_un_hecho_canonico(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    enunciados = {h["enunciado"] for h in escaleta.hechos_declarados(con, "obra-x")}
    assert {"colecciona mapas antiguos", "el viaje en tren a Lisboa",
            "un galgo muy lento"} <= enunciados


def test_fechas_de_nacimiento_y_momento_de_la_fabula_en_la_base(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert con.execute("SELECT fecha_de_nacimiento FROM entidad WHERE id='per-irene'"
                       ).fetchone()[0] == "1992-03-14"
    assert escaleta.escena(con, "cap-04-e1")["t_fabula"] == "2026-06-04"


def test_la_obra_queda_con_su_titulo_y_su_genero(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    fila = con.execute("SELECT titulo, genero FROM obra WHERE id='obra-x'").fetchone()
    assert tuple(fila) == ("El mapa de Irene", "aventura")


def test_montar_dos_veces_no_duplica_ni_reinicia(con):
    """Relanzar tras una caida no puede rehacer lo que ya estaba."""
    novela.montar(con, "obra-x", ficha(), _aprobado())
    with con:
        con.execute("UPDATE escena SET estado='consolidada' WHERE id='cap-01-e1'")
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert len(escaleta.escenas_de(con, "obra-x")) == 10
    assert escaleta.escena(con, "cap-01-e1")["estado"] == "consolidada"


# --- E9: el nivel obra ----------------------------------------------------------

from app.features.consolidacion import memoria
from app.features.cronologia import repository as usos
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho


class JuezDeObra:
    nombre = "doble-obra"

    def __init__(self, respuesta):
        self.respuesta, self.llamadas = respuesta, []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.respuesta


BIEN = {"arco_cerrado": True, "final_abrupto": False, "justificacion": "cierra"}


def _escrita(con, usados=("imp-01", "imp-02", "imp-03"), texto_extra=None):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    for n in range(1, 11):
        e = "cap-{0:02d}-e1".format(n)
        texto = "Texto del capitulo {0}. ".format(n) + (texto_extra or {}).get(n, "")
        with con:
            con.execute("INSERT INTO borrador (escena, version, texto) VALUES (?, 1, ?)",
                        (e, texto))
            con.execute("UPDATE escena SET estado='consolidada', borrador_aceptado=1 "
                        "WHERE id=?", (e,))
        memoria.guardar_resumen(con, e, n, "Resumen del capitulo {0}.".format(n), [],
                                obra="obra-x")
    usos.registrar_usos(con, [{"hecho": h, "escena": "cap-01-e1", "capitulo": "cap-01",
                               "tipo": TipoDeUsoDeHecho.MENCIONA,
                               "origen": OrigenDeUso.REGLA} for h in usados])


def test_un_imprescindible_sin_uso_deja_la_novela_incompleta(con):
    _escrita(con, usados=("imp-01", "imp-02"))
    juez = JuezDeObra(BIEN)
    r = novela.cerrar(con, "obra-x", ficha(), juez)
    assert r["estado"] == "novela_incompleta"
    assert r["faltan"] == ["un galgo muy lento"]
    assert juez.llamadas == [], "una novela incompleta no se juzga entera"


def test_con_todos_los_imprescindibles_la_novela_termina(con):
    _escrita(con)
    r = novela.cerrar(con, "obra-x", ficha(), JuezDeObra(BIEN))
    assert r["estado"] == "terminada" and r["faltan"] == [] and r["juicio"] == []


def test_el_nombre_repetido_da_un_menor_y_no_para_nada(con):
    _escrita(con, texto_extra={3: "Irene " * 20})
    r = novela.cerrar(con, "obra-x", ficha(), JuezDeObra(BIEN))
    assert r["estado"] == "terminada"
    assert r["repeticiones"] == [("cap-03-e1", 20)]
    assert con.execute("SELECT severidad FROM hallazgo WHERE invariante='INV-25'"
                       ).fetchone()[0] == "menor"


def test_el_juicio_de_obra_ve_el_ultimo_capitulo_y_los_resumenes_no_la_obra(con):
    _escrita(con)
    juez = JuezDeObra(BIEN)
    novela.cerrar(con, "obra-x", ficha(), juez)
    prompt = juez.llamadas[0]
    assert "Texto del capitulo 10." in prompt
    assert "Texto del capitulo 1." not in prompt
    assert "Resumen del capitulo 1." in prompt


def test_un_final_abrupto_es_inv27(con):
    _escrita(con)
    r = novela.cerrar(con, "obra-x", ficha(), JuezDeObra(
        {"arco_cerrado": True, "final_abrupto": True, "justificacion": "corta en seco"}))
    assert [h["invariante"] for h in r["juicio"]] == ["INV-27"]
    assert r["estado"] == "terminada", "qué bloquea la publicación es de otra spec"


def test_un_juicio_de_obra_ilegible_queda_sin_veredicto(con):
    _escrita(con)
    r = novela.cerrar(con, "obra-x", ficha(), JuezDeObra({"nada": 1}))
    assert [h["estado"] for h in r["juicio"]] == ["sin_veredicto"]


# --- La novela entera, encadenada (lo que usara `novela_regalo.py`) ------------

import json as _json

from app.commons.modelo.doble import DELTA_OK
from app.features.planificacion.tests.conftest import plan_dict


class _Fijo:
    def __init__(self, r, nombre="doble"):
        self.r, self.nombre, self.llamadas = r, nombre, []
        self.reglas, self.entorno = None, {}

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.r


def _agentes():
    planificador = _Fijo({"titulo": "El mapa de Irene", "premisa": "Irene sigue un mapa.",
                          "plan": plan_dict()})
    revisor = _Fijo({"aprobado": True, "objeciones": []})
    # El POV del plan de prueba es `per-irene`; el doble de serie declara
    # `per-marta` y `INV-04` lo pararia, con razon.
    escritor = _Fijo({"texto": " ".join(["palabra"] * 1198 + ["Irene", "mapa"]),
                      "pov_usado": "per-irene", "delta": DELTA_OK})
    editor = _Fijo({"valoraciones": [
        {"criterio": c, "nota": 4, "justificacion": "bien"} for c in
        ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
         "personalizacion")]})
    resumidor = _Fijo({"texto": "Resumen. " * 10, "hechos_clave": []})
    return {"planificador": planificador, "revisor": revisor, "escritor": escritor,
            "editor": editor, "resumidor": resumidor}


@__import__("pytest").mark.xfail(strict=True, reason=(
    "F-58: el Escritor recibe los tamaños de los bloques de contexto, no su texto, "
    "asi que el genero y el tono del bloque inmutable no llegan al prompt. "
    "Estricto: se pondra en rojo el dia que se arregle."))
def test_escribir_encadena_plan_montaje_y_generacion(con, tmp_path):
    agentes = _agentes()
    r = novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    assert r["plan"].version == 1
    assert r["generacion"].escenas_hechas == ["cap-01-e1"]
    prompt = agentes["escritor"].llamadas[0]
    assert "Irene Valdés" in prompt and "mapa" in prompt and "hospital" in prompt
    assert "aventura" in prompt and "divertido" in prompt


def test_escribir_deja_las_reglas_del_hook_al_escritor(con, tmp_path):
    agentes = _agentes()
    novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    reglas = _json.loads(open(agentes["escritor"].reglas, encoding="utf-8").read())
    assert reglas["longitud"] == [1000, 1500]
    assert "Irene Valdés" in reglas["nombres"] and "hospital" in reglas["vetadas"]
    assert "Tomas" in reglas["vetadas"], "el nombre vetado, tambien por su nombre de pila"


def test_un_plan_no_aprobado_no_escribe_nada(con, tmp_path):
    agentes = _agentes()
    agentes["revisor"] = _Fijo({"aprobado": False, "objeciones": ["sin arco"]})
    import pytest as _pytest
    from app.features.planificacion.service import PlanNoAprobado
    with _pytest.raises(PlanNoAprobado):
        novela.escribir(con, "obra-x", ficha(), agentes, carpeta_de_reglas=str(tmp_path))
    assert agentes["escritor"].llamadas == []


def test_escribir_encadena_plan_montaje_y_primer_capitulo(con, tmp_path):
    """Lo que si funciona hoy, separado de `F-58` para que no quede sin probar."""
    agentes = _agentes()
    r = novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    assert r["plan"].version == 1 and r["cierre"] is None
    assert r["generacion"].escenas_hechas == ["cap-01-e1"]
    prompt = agentes["escritor"].llamadas[0]
    assert "Irene Valdés" in prompt and "mapa" in prompt and "hospital" in prompt
