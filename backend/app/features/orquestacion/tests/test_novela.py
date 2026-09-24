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
    assert all(list(e["longitud_objetivo"]) == [1150, 1350] for e in escenas), "la de `media`, la de la ficha"


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


class _EscritorQueCopiaElPov(_Fijo):
    """Copia del prompt el identificador del POV, como haria el modelo: con los
    identificadores de la obra acotados (`F-64`), `per-irene` a secas ya no es el
    POV de nadie, y un doble que lo tuviera escrito a fuego pasaria por otra cosa."""

    def llamar(self, prompt):
        import re
        self.llamadas.append(prompt)
        m = re.search(r"[\w-]*per-irene", prompt)
        return dict(self.r, pov_usado=m.group(0) if m else "per-irene")


def _agentes(obra=None):
    # La premisa, distinta de la sinopsis del capitulo 1 a proposito: si fueran
    # la misma frase, una prueba de que llega la premisa pasaria por la sinopsis.
    planificador = _Fijo({"titulo": "El mapa de Irene",
                          "premisa": "una premisa del planificador que se ignora",
                          "plan": plan_dict()})
    revisor = _Fijo({"aprobado": True, "objeciones": []})
    # El POV del plan de prueba es `per-irene`; el doble de serie declara
    # `per-marta` y `INV-04` lo pararia, con razon.
    escritor = _EscritorQueCopiaElPov({"texto": " ".join(["palabra"] * 1198 + ["Irene", "mapa"]),
                                       "pov_usado": "per-irene", "delta": DELTA_OK})
    editor = _Fijo({"valoraciones": [
        {"criterio": c, "nota": 4, "justificacion": "bien"} for c in
        ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
         "personalizacion")]})
    resumidor = _Fijo({"texto": "Resumen. " * 10, "hechos_clave": []})
    return {"planificador": planificador, "revisor": revisor, "escritor": escritor,
            "editor": editor, "resumidor": resumidor}


def test_escribir_encadena_plan_montaje_y_generacion(con, tmp_path):
    """Fue un xfail estricto mientras existio `F-58`: el genero y el tono del
    bloque inmutable no llegaban porque el Escritor recibia tamaños."""
    agentes = _agentes()
    r = novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    assert r["plan"].version == 1
    assert r["generacion"].escenas_hechas == ["obra-x-cap-01-e1"], "acotada a su obra (`F-64`)"
    prompt = agentes["escritor"].llamadas[0]
    assert "Irene Valdés" in prompt and "mapa" in prompt and "hospital" in prompt
    assert "aventura" in prompt and "divertido" in prompt
    assert "Irene sigue un mapa." in prompt, "la sinopsis del plan llega"


def test_escribir_deja_las_reglas_del_hook_al_escritor(con, tmp_path):
    agentes = _agentes()
    novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    reglas = _json.loads(open(agentes["escritor"].reglas, encoding="utf-8").read())
    assert reglas["longitud"] == [1150, 1350], "la extension de la ficha (`SPEC-32`)"
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
    assert r["generacion"].escenas_hechas == ["obra-x-cap-01-e1"], "acotada a su obra (`F-64`)"
    prompt = agentes["escritor"].llamadas[0]
    assert "Irene Valdés" in prompt and "mapa" in prompt and "hospital" in prompt


def test_la_premisa_decidida_llega_al_escritor_como_texto(con, tmp_path):
    agentes = _agentes()
    novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    assert "Un mapa heredado lleva a Irene de vuelta a Lisboa." in agentes["escritor"].llamadas[0]


# --- `F-60`: el destinatario conoce sus propios recuerdos ------------------------

def _sabe(con):
    return {(f[0], f[1]) for f in con.execute(
        "SELECT sujeto, hecho FROM conocimiento WHERE desde_escena IS NULL")}


def test_el_destinatario_conoce_de_entrada_todos_los_imprescindibles(con):
    """`F-60`: sin esto `INV-03` bloqueaba a Tomas por actuar sobre su propio
    recuerdo, en los tres intentos del capitulo 1 real."""
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert {("per-irene", "imp-01"), ("per-irene", "imp-02"),
            ("per-irene", "imp-03")} <= _sabe(con)


def test_una_persona_o_mascota_imprescindible_conoce_lo_que_la_nombra(con):
    novela.montar(con, "obra-x", ficha(), _aprobado())
    assert ("per-brisa", "imp-03") in _sabe(con)
    assert ("per-brisa", "imp-01") not in _sabe(con)


def test_el_conocimiento_inicial_del_plan_tambien_se_siembra(con):
    """`montar` lo ignoraba: el plan podia declararlo y no llegaba al registro."""
    d = plan_dict()
    d["hechos"] = [{"id": "hec-carta", "enunciado": "hay una carta en el mapa"}]
    d["mundo"]["conocimiento_inicial"] = [{"sujeto": "per-brisa", "hecho": "hec-carta"}]
    novela.montar(con, "obra-x", ficha(), PlanAprobado(plan(**d), 1, "t", "p"))
    assert ("per-brisa", "hec-carta") in _sabe(con)


def test_el_destinatario_actua_sobre_su_recuerdo_sin_disparar_inv03(con, tmp_path):
    agentes = _agentes()
    agentes["escritor"] = _Fijo({
        "texto": " ".join(["palabra"] * 1198 + ["Irene", "mapa"]),
        "pov_usado": "obra-x-per-irene",
        "delta": dict(DELTA_OK, acciones=[{"personaje": "obra-x-per-irene", "hecho": "imp-01"}])})
    r = novela.escribir(con, "obra-x", ficha(), agentes, hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    assert r["generacion"].parada is None
    assert not con.execute("SELECT 1 FROM hallazgo WHERE invariante='INV-03'").fetchone()


# --- `F-64`: dos novelas en la misma base no se pisan ----------------------------

def test_dos_novelas_con_el_mismo_plan_en_la_misma_base_no_se_pisan(con, tmp_path):
    """El Planificador pone los mismos identificadores en todas las novelas
    (`cap-01`, `per-irene`, `lug-casa`), y `escena`, `capitulo`, `entidad` y `lugar`
    tienen clave global. Antes de `F-64`, la segunda novela no fallaba: pisaba."""
    for obra in ("obra-a", "obra-b"):
        novela.escribir(con, obra, ficha(), _agentes(obra), hasta_capitulo=1,
                        carpeta_de_reglas=str(tmp_path))
    for obra in ("obra-a", "obra-b"):
        escenas = escaleta.escenas_de(con, obra)
        assert len(escenas) == 10, obra
    ids_a = {e["id"] for e in escaleta.escenas_de(con, "obra-a")}
    ids_b = {e["id"] for e in escaleta.escenas_de(con, "obra-b")}
    assert not ids_a & ids_b, "ninguna escena comparte identificador entre novelas"
    capitulos = con.execute("SELECT obra, COUNT(*) FROM capitulo GROUP BY obra").fetchall()
    assert {tuple(f) for f in capitulos} == {("obra-a", 10), ("obra-b", 10)}
    personajes = con.execute("SELECT COUNT(*) FROM entidad WHERE id LIKE '%per-irene'").fetchone()[0]
    assert personajes == 2, "cada novela tiene su propia Irene"


# --- `SPEC-32` `RF-09`: el codigo respeta la extension elegida --------------------

def test_montar_usa_la_longitud_de_la_extension_elegida(con):
    novela.montar(con, "obra-x", ficha(extension="larga"), _aprobado())
    assert all(list(e["longitud_objetivo"]) == [1350, 1500]
               for e in escaleta.escenas_de(con, "obra-x"))


def test_las_reglas_del_hook_llevan_la_longitud_elegida(con, tmp_path):
    agentes = _agentes()
    novela.escribir(con, "obra-x", ficha(extension="corta"), agentes, hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    reglas = _json.loads(open(agentes["escritor"].reglas, encoding="utf-8").read())
    assert reglas["longitud"] == [1000, 1150]


def test_un_capitulo_de_1200_palabras_falla_inv17_si_la_extension_es_larga(con, tmp_path):
    """El caso negativo: el doble escribe 1200 palabras, que caben en `media` y no en
    `larga`. Si el codigo siguiera con 1000-1500, esto pasaria en silencio."""
    novela.escribir(con, "obra-x", ficha(extension="larga"), _agentes(), hasta_capitulo=1,
                    carpeta_de_reglas=str(tmp_path))
    assert con.execute("SELECT 1 FROM hallazgo WHERE invariante='INV-17'").fetchone()
