"""`PLAN-31` E6: lo que dice cada validador de una obra, reunido (`SPEC-31` `RF-02`).

La regla de lectura: **una columna sin constancia de ejecucion dice «sin veredicto»,
nunca «pasó»**. La tabla `hallazgo` solo registra violaciones (`PLAN-31` hallazgo 4), asi
que «sin hallazgos» no es «pasó»: es el cero vacio de `F-30`.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.invariantes import registro
from app.features.auditoria import publicacion as puerta
from app.features.auditoria import repository as veredictos
from app.features.escaleta import repository as escaleta
from app.features.evaluacion.tabla import Resultado as R
from app.features.orquestacion import evaluacion


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    escaleta.asegurar_tablas(c)
    escaleta.guardar_escaleta(c, "obra-x", [
        {"id": "obra-x-e1", "orden": 1, "capitulo": "obra-x-cap-01",
         "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
         "pov": "per-a", "lugar": "lug-a", "beats": ["b"], "longitud_objetivo": [10, 50]}])
    return c


def _borrador(con, escena="obra-x-e1"):
    return escaleta.guardar_borrador(con, escena, texto="texto", modelo="doble",
                                     prompt_hash="h")


def _hallazgo(con, inv, estado="abierto", escena="obra-x-e1"):
    escaleta.guardar_hallazgo(con, invariante=inv, verificador="prueba", escena=escena,
                              severidad=registro.TODAS[inv].severidad, estado=estado,
                              descripcion="d")


def _puerta(con, codigo_lean=0, hallazgos=()):
    decision = puerta.decidir([], list(hallazgos), puerta.ResultadoLean(codigo_lean))
    veredictos.guardar(con, "obra-x", decision, codigo_lean)


def test_sin_hallazgos_y_sin_constancia_de_ejecucion_no_es_paso(con):
    """La escena esta planificada y no tiene ningun borrador: ninguna puerta llego a
    mirar nada, y sin hallazgos eso no puede salir como «pasó»."""
    celdas = evaluacion.resultados(con, "obra-x")
    for inv in ("INV-01", "INV-04", "INV-17", "INV-26", "INV-28", "publicacion"):
        assert celdas[inv].resultado is R.SIN_VEREDICTO, inv
        assert celdas[inv].motivo, "dice por que no hay veredicto"


def test_con_borrador_y_sin_hallazgos_la_puerta_de_escena_pasa(con):
    """Guardar un borrador y pasarle las puertas es un solo paso (`bucle.generar`): un
    borrador es la constancia de que `INV-01`..`INV-04`, `INV-17` e `INV-18` miraron."""
    _borrador(con)
    escaleta.marcar_consolidada(con, "obra-x-e1")
    celdas = evaluacion.resultados(con, "obra-x")
    assert celdas["INV-01"].resultado is R.PASO and celdas["INV-01"].disparos == 0


def test_un_hallazgo_sin_veredicto_no_se_cuenta_como_pasado(con):
    _borrador(con)
    escaleta.marcar_consolidada(con, "obra-x-e1")
    _hallazgo(con, "INV-04", estado="sin_veredicto")
    assert evaluacion.resultados(con, "obra-x")["INV-04"].resultado is R.SIN_VEREDICTO


def test_una_invariante_obsoleta_sale_como_no_aplica(con):
    celdas = evaluacion.resultados(con, "obra-x")
    for inv in registro.obsoletas():
        assert celdas[inv].resultado is R.NO_APLICA, inv


def test_un_validador_que_disparo_y_se_resolvio_dice_paso_con_sus_disparos(con):
    """El primer intento sale corto (`INV-17`) dos veces y el tercero se acepta: la
    escena termina consolidada, asi que la regla disparo y se arreglo."""
    for _ in range(3):
        _borrador(con)
    _hallazgo(con, "INV-17")
    _hallazgo(con, "INV-17")
    escaleta.marcar_consolidada(con, "obra-x-e1")
    celda = evaluacion.resultados(con, "obra-x")["INV-17"]
    assert celda.resultado is R.PASO and celda.disparos == 2
    assert celda.texto == "pasó (2 disparos)"


def test_un_hallazgo_de_una_escena_rendida_es_fallo(con):
    _borrador(con)
    _hallazgo(con, "INV-17")
    escaleta.rendir_escena(con, "obra-x-e1", 1)
    assert evaluacion.resultados(con, "obra-x")["INV-17"].resultado is R.FALLO


def test_lean_2_es_sin_veredicto(con):
    """`SPEC-30` `RF-09`: el `2` de Lean no es un aprobado."""
    _borrador(con)
    _puerta(con, codigo_lean=2)
    assert evaluacion.resultados(con, "obra-x")["INV-28"].resultado is R.SIN_VEREDICTO
    _puerta(con, codigo_lean=0)
    assert evaluacion.resultados(con, "obra-x")["INV-28"].resultado is R.PASO


def test_inv06_sale_como_no_ejecutado(con):
    """`SPEC-30` `RF-12`: no la ejecuta nadie. No ha pasado: no se ha mirado."""
    _borrador(con)
    _puerta(con)
    celda = evaluacion.resultados(con, "obra-x")["INV-06"]
    assert celda.resultado is R.NO_EJECUTADO and "RF-12" in celda.motivo


def test_una_invariante_nueva_del_registro_sale_sola_como_sin_veredicto(con, monkeypatch):
    """Las columnas salen del registro, no de una lista a mano: una invariante que se
    anada manana aparece sin que nadie toque la tabla, y sin constancia de quien la
    ejecuta dice «sin veredicto» hasta que alguien la conecte."""
    nueva = registro.construir_invariante("INV-99", "prueba", "escena", "menor", "regla", "x")
    monkeypatch.setitem(registro.TODAS, "INV-99", nueva)
    _borrador(con)
    celdas = evaluacion.resultados(con, "obra-x")
    assert celdas["INV-99"].resultado is R.SIN_VEREDICTO


def test_una_obra_que_no_existe_sale_sin_ejecutar(con):
    celdas = evaluacion.resultados(con, "obra-que-no-esta")
    assert celdas["INV-01"].resultado is R.SIN_EJECUTAR
    assert celdas["INV-06"].resultado is R.NO_EJECUTADO


def test_lo_que_la_tabla_da_por_no_ejecutado_es_lo_que_la_puerta_declara():
    """Dos copias de la misma lista, a cada lado de `A-02`: se comparan aqui."""
    from app.features.evaluacion import tabla
    assert set(tabla.NO_EJECUTADAS) == {i for i, _ in puerta.NO_EJECUTADAS}


def test_una_novela_entera_con_dobles_da_pases_con_constancia(tmp_path):
    """De punta a punta: cada columna que dice «pasó» lo dice porque algo lo registro."""
    from app.features.orquestacion import novela
    from app.features.orquestacion.tests import test_novela as tn
    from app.features.planificacion.tests.conftest import ficha
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    agentes = tn._agentes_para_la_novela_entera()
    agentes["editor"] = tn._EditorDeLaPuerta(agentes["editor"].r, juicios=[
        {"arco_cerrado": True, "final_abrupto": False, "justificacion": "bien"}])
    r = novela.escribir(c, "obra-x", ficha(), agentes, carpeta_de_reglas=str(tmp_path),
                        lean=tn._LeanFijo())
    assert r["publicacion"].publicada
    celdas = evaluacion.resultados(c, "obra-x")
    for col in ("INV-01", "INV-02", "INV-03", "INV-04", "INV-17", "INV-18", "INV-21",
                "INV-22", "INV-23", "INV-24", "INV-26", "INV-26.ritmo", "INV-27",
                "INV-28", "INV-29", "schema.plan", "publicacion"):
        assert celdas[col].resultado is R.PASO, (col, celdas[col])
    assert celdas["INV-06"].resultado is R.NO_EJECUTADO
    assert celdas["entrevista.instrucciones"].resultado is R.NO_APLICA
    assert celdas["INV-08"].resultado is R.SIN_VEREDICTO, "se evalua y no deja rastro"
