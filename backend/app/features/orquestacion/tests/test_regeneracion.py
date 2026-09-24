"""`PLAN-23`: la regeneracion en una obra acumulativa, contra bases en memoria.

Ningun paso llama al modelo. Los datos son inventados.
"""

import pytest

from app.features.consolidacion import mundo
from app.features.orquestacion import regeneracion
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.planificacion import repository as planes
from app.features.planificacion.tests.conftest import plan


@pytest.fixture
def con():
    c = o.conexion()
    planes.asegurar_tablas(c)
    return c


# --- A2 · la semilla ------------------------------------------------------------

def test_sin_plan_aprobado_no_hay_semilla_y_se_dice(con):
    o.obra(con)
    planes.guardar(con, "obra-a", 1, plan(), False, "revisor", ["no"])
    with pytest.raises(regeneracion.SinSemilla, match="plan aprobado"):
        regeneracion.semilla_de(con, "obra-a")


def test_la_semilla_sale_del_plan_y_del_conocimiento_anterior_al_relato(con):
    o.obra(con)
    planes.guardar(con, "obra-a", 1, plan(), True, "revisor", [])
    mundo.sembrar_conocimiento(con, [{"sujeto": "per-irene", "hecho": "imp-01"}])
    o.escribir(con, "obra-a-c1-e1", "texto", {
        "movimientos": [], "revelaciones": [{"sujeto": "per-brisa", "hecho": "h-x"}]})
    s = regeneracion.semilla_de(con, "obra-a")
    assert s["entidades_vivas"] == {"per-irene": "vivo", "per-brisa": "vivo"}
    assert s["ubicaciones"] == {"per-irene": "lug-casa", "per-brisa": "lug-casa"}
    assert s["accesos"] == {"lug-casa": []}
    # Lo revelado por una escena no es semilla: es de su delta.
    assert s["conocimiento"] == {("per-irene", "imp-01"): {"desde": None, "grado": "sabe"}}


# --- A4 · la reverificacion: que un verde heredado no cuente ------------------------

from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.features.brief import repository as brief
from app.features.escaleta import repository as escaleta


def _con_plan(con, **kw):
    ids = o.obra(con, **kw)
    planes.guardar(con, "obra-a", 1, plan(), True, "revisor", [])
    mundo.sembrar_conocimiento(con, [{"sujeto": "per-irene", "hecho": "h-mapa"}])
    # El mundo vivo arranca en la semilla, como tras `novela.montar`.
    mundo.rebobinar(con, regeneracion.semilla_de(con, "obra-a"))
    return ids


REVELA = {"revelaciones": [{"sujeto": "per-irene", "hecho": "h-llave"}]}
ACTUA = {"acciones": [{"personaje": "per-irene", "hecho": "h-llave"}]}


def _v1(con):
    """c1 revela la llave, c2 no hace nada, c3 actua sobre ella."""
    ids = _con_plan(con)
    o.escribir(con, o.escena_de(ids[0]), "uno", REVELA)
    o.escribir(con, o.escena_de(ids[1]), "dos", {})
    o.escribir(con, o.escena_de(ids[2]), "tres", ACTUA)
    return ids


def _v2(con, ids, delta_nuevo, sustituye=0):
    """La version 2 con el capitulo `sustituye` nuevo y el resto compartido."""
    nuevo = "{0}-v2".format(ids[sustituye])
    capitulos = list(ids)
    capitulos[sustituye] = nuevo
    brief.crear_version(con, "obra-a", capitulos, anterior=1, commit="def5678")
    # `C-2`: antes de escribir, el mundo vivo se rebobina a la semilla mas el prefijo.
    prefijo = o.deltas.de_escenas(con, [o.escena_de(c) for c in capitulos[:sustituye]])
    mundo.rebobinar(con, mundo.acumular(regeneracion.semilla_de(con, "obra-a"), prefijo)[0])
    escaleta.guardar_escaleta(con, "obra-a", [{
        "id": o.escena_de(nuevo), "orden": 1, "capitulo": nuevo,
        "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"}, "beats": [],
        "pov": "per-ana", "lugar": "lug-casa", "t_discurso": sustituye + 1}])
    o.escribir(con, o.escena_de(nuevo), "nuevo", delta_nuevo)
    return capitulos


def test_una_accion_sobre_un_hecho_que_la_version_nueva_ya_no_revela_falla_al_reverificar(con):
    ids = _v1(con)
    _v2(con, ids, {})
    r = regeneracion.reverificar(con, "obra-a", 2)
    por_escena = {e["escena"]: e for e in r["escenas"]}
    c3 = por_escena[o.escena_de(ids[2])]
    assert c3["estado"] == EV.FALLIDA
    assert [h["invariante"] for h in c3["hallazgos"]] == ["INV-03"]
    assert por_escena[o.escena_de(ids[1])]["estado"] == EV.VERIFICADA
    # En la version 1 la accion se sostiene.
    r1 = regeneracion.reverificar(con, "obra-a", 1)
    assert {e["estado"] for e in r1["escenas"]} == {EV.VERIFICADA}


def test_una_escena_heredada_sin_reverificar_no_cuenta_como_verificada(con):
    ids = _v1(con)
    regeneracion.reverificar(con, "obra-a", 1)
    assert regeneracion.estado_de(con, "obra-a", 1, o.escena_de(ids[2])) == EV.VERIFICADA
    _v2(con, ids, REVELA)
    # Compartida, con el verde de la version 1 y sin reverificar en la 2: no es verde.
    assert regeneracion.estado_de(con, "obra-a", 2, o.escena_de(ids[2])) == EV.SIN_REVERIFICAR


def test_con_la_misma_huella_el_verde_se_conserva(con):
    ids = _v1(con)
    regeneracion.reverificar(con, "obra-a", 1)
    e3 = o.escena_de(ids[2])
    assert regeneracion.estado_de(con, "obra-a", 1, e3) == EV.VERIFICADA
    assert regeneracion.estado_de(con, "obra-a", 1, e3) == EV.VERIFICADA
    # Un delta nuevo en el prefijo cambia la huella: el verde deja de contar.
    o.deltas.guardar(con, o.escena_de(ids[1]), {"revelaciones": []}, 2)
    assert regeneracion.estado_de(con, "obra-a", 1, e3) == EV.SIN_REVERIFICAR


def test_un_delta_posterior_incompatible_queda_fallido_con_motivo(con):
    ids = _con_plan(con)
    o.escribir(con, o.escena_de(ids[0]), "uno", {})
    o.escribir(con, o.escena_de(ids[1]), "dos", {})
    o.escribir(con, o.escena_de(ids[2]), "tres", {"cambios_de_estado_vital": [
        {"personaje": "per-brisa", "de": "vivo", "a": "desaparecido"}]})
    _v2(con, ids, {"cambios_de_estado_vital": [
        {"personaje": "per-brisa", "de": "vivo", "a": "muerto"}]})
    r = regeneracion.reverificar(con, "obra-a", 2)
    c3 = {e["escena"]: e for e in r["escenas"]}[o.escena_de(ids[2])]
    assert c3["estado"] == EV.FALLIDA
    assert "per-brisa" in c3["motivo"]


def test_la_reverificacion_no_escribe_en_la_tabla_de_hallazgos(con):
    ids = _v1(con)
    _v2(con, ids, {})
    antes = con.execute("SELECT COUNT(*) FROM hallazgo").fetchone()[0]
    regeneracion.reverificar(con, "obra-a", 2)
    assert con.execute("SELECT COUNT(*) FROM hallazgo").fetchone()[0] == antes


def test_la_reverificacion_no_llama_a_ningun_modelo(con, monkeypatch):
    from app.features.orquestacion import bucle, ciclo

    def prohibido(*a, **k):
        raise AssertionError("la reverificacion llamo al modelo")

    monkeypatch.setattr(bucle, "generar", prohibido)
    monkeypatch.setattr(ciclo, "_delegar", prohibido)
    ids = _v1(con)
    _v2(con, ids, {})
    assert regeneracion.reverificar(con, "obra-a", 2)["reverificada"] is True
    import inspect
    fuente = inspect.getsource(regeneracion.reverificar)
    assert "llamar(" not in fuente and "escritor" not in fuente


def test_sin_semilla_no_se_reverifica_y_lo_dice(con):
    ids = o.obra(con)
    o.escribir(con, o.escena_de(ids[0]), "uno", {})
    r = regeneracion.reverificar(con, "obra-a", 1)
    assert r["reverificada"] is False and "plan aprobado" in r["motivo"]
    assert con.execute("SELECT COUNT(*) FROM reverificacion").fetchone()[0] == 0


def test_inv06_sale_como_no_ejecutada(con):
    _v1(con)
    r = regeneracion.reverificar(con, "obra-a", 1)
    no = {n["invariante"]: n["motivo"] for n in r["no_ejecutadas"]}
    assert "INV-06" in no and "RF-12" in no["INV-06"]
    # `pov_usado` no se guarda con el borrador: `INV-04` no se puede volver a pasar.
    assert "INV-04" in no
