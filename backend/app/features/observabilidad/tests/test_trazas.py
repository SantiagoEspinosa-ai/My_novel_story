"""`F-49`: la traza moria con el proceso.

POR QUE IMPORTA, Y NO ES POR TENER REGISTROS
----------------------------------------------
`PC-9` dice que lo que acota el dano de que un agente rellene con invencion lo
que el recorte dejo fuera es justamente que *"la traza de `VER-24` registra que
fichas quedaron fuera, asi que el fallo pasa de invisible a atribuible"*.

Si la traza no sobrevive al proceso, **esa contencion solo vale dentro de la
misma ejecucion** — y el diagnostico siempre se hace despues. Lo destapo la
sesion de verificacion formal preguntandose que mas se estaba aplicando y
tirando, despues de que `deltas.py` cerrara el caso del delta.

LA LLAVE ES `prompt_hash`, COMO EN LAS LECTURAS
-------------------------------------------------
Misma llave y misma forma que `lectura_de_contexto`, que registra **lo que
entra**. Esto registra **lo que sale**. Con las dos, una delegacion pasada se
puede reconstruir por los dos lados sin releer ningun texto.
"""

import sqlite3

import pytest

from app.commons.modelo import traza as modulo_traza
from app.features.observabilidad import repository as repo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    return c


def _traza():
    t = modulo_traza.nueva(agente="escritor", escena="e1", trabajo="obra-1",
                           modelo="fable")
    modulo_traza.registrar_entrada(t, fichas=[("per-marta", 3)], prompt_hash="abc123")
    modulo_traza.registrar_recorte(t, "condensaciones", "eliminacion")
    modulo_traza.registrar_recorte(t, "escena_anterior", "reduccion")
    t.tokens_estimados = 2100
    t.resultado = "ok"
    return t


def test_una_traza_guardada_se_relee_entera(con):
    repo.guardar_traza(con, _traza())
    leidas = repo.trazas_de(con, "e1")
    assert len(leidas) == 1
    assert leidas[0]["agente"] == "escritor"
    assert leidas[0]["modelo"] == "fable"
    assert leidas[0]["tokens_estimados"] == 2100


def test_los_recortes_sobreviven_al_proceso(con):
    """Es el dato de `PC-9`: **que bloques quedaron fuera**. Sin el, saber que
    un agente invento algo no dice si el contexto se lo habia quitado."""
    repo.guardar_traza(con, _traza())
    recortes = repo.trazas_de(con, "e1")[0]["recortes"]
    assert ("condensaciones", "eliminacion") in [tuple(r) for r in recortes]
    assert ("escena_anterior", "reduccion") in [tuple(r) for r in recortes]


def test_una_delegacion_fallida_tambien_deja_traza(con):
    """La llave es `prompt_hash` y no la respuesta, **precisamente** para que
    las llamadas que fallaron consten: son las que mas dicen."""
    t = modulo_traza.nueva(agente="juez", escena="e1", trabajo="obra-1")
    modulo_traza.registrar_entrada(t, prompt_hash="def456")
    modulo_traza.registrar_fallo(t, clase="contrato", salida="{{roto")
    repo.guardar_traza(con, t)
    leida = repo.trazas_de(con, "e1")[0]
    assert leida["clase_de_fallo"] == "contrato"
    assert leida["resultado"] != "ok"


def test_dos_agentes_sobre_la_misma_escena_no_se_pisan(con):
    """Regla 7: la llave tiene que distinguir las filas que no significan lo
    mismo. Escritor y Juez trabajan sobre la misma escena y son dos trazas."""
    repo.guardar_traza(con, _traza())
    t = modulo_traza.nueva(agente="juez", escena="e1", trabajo="obra-1")
    modulo_traza.registrar_entrada(t, prompt_hash="otro-hash")
    repo.guardar_traza(con, t)
    assert {x["agente"] for x in repo.trazas_de(con, "e1")} == {"escritor", "juez"}


def test_guardar_dos_veces_el_mismo_prompt_no_duplica(con):
    """Un reintento del registro no es una delegacion mas: contarlo como tal
    haria que `VER-61` viera trabajo que no existio."""
    repo.guardar_traza(con, _traza())
    repo.guardar_traza(con, _traza())
    assert len(repo.trazas_de(con, "e1")) == 1


def test_una_traza_sin_prompt_hash_se_guarda_igual(con):
    """Una delegacion que fallo antes de construir el prompt no tiene hash, y
    perderla seria perder justo el caso que hay que diagnosticar."""
    t = modulo_traza.nueva(agente="escritor", escena="e2", trabajo="obra-1")
    modulo_traza.registrar_fallo(t, clase="transporte")
    repo.guardar_traza(con, t)
    assert len(repo.trazas_de(con, "e2")) == 1
