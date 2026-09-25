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


# --- A6 · cada lector ve solo su version --------------------------------------------

from app.commons.db import procedencia
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.features.consolidacion import memoria
from app.features.cronologia import repository as usos
from app.features.manuscrito import exportar
from app.features.orquestacion import arrastre, novela, story_bible
from app.features.orquestacion import obra as modulo_obra
from app.features.planificacion.service import PlanAprobado
from app.features.planificacion.tests.conftest import ficha
from app.commons.dominio.story_bible import EntradaHechos

OBRA = "obra-x"


def _novela_con_dos_versiones(con):
    """La novela del fixture de `planificacion`, escrita entera, y una version 2 que
    sustituye el capitulo 2 (`cap-02`) por `cap-02-v2`, con su `t_discurso` (`C-6`)."""
    novela.montar(con, OBRA, ficha(), PlanAprobado(plan(), 1, "El mapa", "Un mapa."))
    planes.guardar(con, OBRA, 1, plan(), True, "revisor", [])
    procedencia.registrar(con, version=o.COMMIT)
    escaleta.asignar_t_discurso(con, OBRA, {"cap-{0:02d}".format(n): n for n in range(1, 11)})
    for n in range(1, 11):
        e = "cap-{0:02d}-e1".format(n)
        o.escribir(con, e, "Texto viejo del capitulo {0}.".format(n))
        memoria.guardar_resumen(con, e, n, "Resumen viejo {0}.".format(n), [], obra=OBRA)
    # El galgo (imp-03, previsto en cap-02) solo se uso en el capitulo que se sustituye.
    usos.registrar_usos(con, [{"hecho": h, "escena": "{0}-e1".format(c), "capitulo": c,
                               "tipo": TipoDeUsoDeHecho.MENCIONA, "origen": OrigenDeUso.REGLA}
                              for h, c in (("imp-01", "cap-01"), ("imp-02", "cap-04"),
                                           ("imp-03", "cap-02"))])
    capitulos = brief.capitulos_de_version(con, OBRA, 1)
    capitulos[1] = "cap-02-v2"
    brief.crear_version(con, OBRA, capitulos, anterior=1, commit="def5678")
    escaleta.guardar_escaleta(con, OBRA, [{
        "id": "cap-02-v2-e1", "orden": 1, "capitulo": "cap-02-v2",
        "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"}, "beats": [],
        "pov": "per-irene", "lugar": "lug-casa", "t_discurso": 2,
        "longitud_objetivo": [1, 5000]}])
    o.escribir(con, "cap-02-v2-e1", "Texto nuevo del capitulo 2.")
    memoria.guardar_resumen(con, "cap-02-v2-e1", 2, "Resumen nuevo 2.", [], obra=OBRA)
    # `F-121` (TLC `CE-14`): la vigente es la ultima **publicada**. Estas pruebas miran lo
    # que ve el lector con la 2 ya publicada, asi que la puerta la deja pasar.
    from app.features.auditoria import publicacion as puerta
    from app.features.auditoria import repository as veredictos
    veredictos.guardar(con, OBRA, puerta.decidir([], [], puerta.ResultadoLean(0)), 0, 2)


def test_con_dos_versiones_cada_lector_ve_solo_las_escenas_de_la_suya(con):
    _novela_con_dos_versiones(con)
    v1 = [e["id"] for e in regeneracion.escenas_de_version(con, OBRA, 1)]
    v2 = [e["id"] for e in regeneracion.escenas_de_version(con, OBRA, 2)]
    assert "cap-02-e1" in v1 and "cap-02-v2-e1" not in v1
    assert v2[1] == "cap-02-v2-e1" and "cap-02-e1" not in v2 and len(v2) == 10
    assert [e["id"] for e in regeneracion.escenas_de_version(con, OBRA)] == v2
    assert brief.leer(con, OBRA)["capitulos"][1] == "cap-02-v2"
    # La story bible: el uso del galgo es del capitulo sustituido, no de la version 2.
    hechos = {h.id: h for h in story_bible.leer_hechos(con, OBRA, EntradaHechos()).hechos}
    assert hechos["imp-03"].usos == []
    # `INV-24`: en la version vigente el galgo no aparece en ningun capitulo.
    r = novela.cerrar(con, OBRA, ficha(), None)
    assert r["estado"] == "novela_incompleta" and r["faltan"] == ["un galgo muy lento"]
    # La medida del arrastre: la de la version vigente.
    medida = arrastre.medir(con, OBRA)
    assert medida["medido"] is True
    assert [d["hecho"] for d in medida["detalle"]] == ["imp-01", "imp-02"]
    # El cierre de la obra no mira los hallazgos del capitulo sustituido.
    escaleta.guardar_hallazgo(con, "INV-07", "juez", "cap-02-e1", "mayor", "abierto", "x")
    assert modulo_obra.evaluar_cierre(con, OBRA)["puede_cerrarse"] is True


def test_la_memoria_de_una_escena_de_la_v2_no_trae_el_resumen_del_capitulo_sustituido(con):
    _novela_con_dos_versiones(con)
    material = modulo_obra.reunir_material(con, escaleta.escena(con, "cap-03-e1"), OBRA,
                                           anterior_cruza_capitulo=True)
    assert [r["escena"] for r in material["resumenes"]] == ["cap-01-e1", "cap-02-v2-e1"]
    assert material["escena_anterior"] == "Texto nuevo del capitulo 2."
    en_la_1 = modulo_obra.reunir_material(con, escaleta.escena(con, "cap-03-e1"), OBRA,
                                          anterior_cruza_capitulo=True, version=1)
    assert [r["escena"] for r in en_la_1["resumenes"]] == ["cap-01-e1", "cap-02-e1"]


def test_el_manuscrito_con_dos_versiones_es_el_de_la_vigente_y_no_mezcla(con):
    _novela_con_dos_versiones(con)
    m = exportar.manuscrito(con, OBRA)
    assert "Texto nuevo del capitulo 2." in m.texto
    assert "Texto viejo del capitulo 2." not in m.texto
    assert m.capitulos == 10 and m.escenas == 10
    assert m.texto.index("capitulo 1.") < m.texto.index("nuevo del capitulo 2") \
        < m.texto.index("capitulo 3.")


def test_un_imprescindible_se_comprueba_en_el_capitulo_regenerado(con):
    """Hallazgo 6: se indexaban por `"{capitulo}-e1"`, y la escena nueva tiene otro id."""
    _novela_con_dos_versiones(con)
    por_escena = novela.imprescindibles_por_escena(con, OBRA, plan())
    assert [i["id"] for i in por_escena["cap-02-v2-e1"]] == ["imp-03"]
    assert "cap-02-e1" not in por_escena
    assert [i["id"] for i in por_escena["cap-01-e1"]] == ["imp-01"]
    en_la_1 = novela.imprescindibles_por_escena(con, OBRA, plan(), version=1)
    assert [i["id"] for i in en_la_1["cap-02-e1"]] == ["imp-03"]


def test_con_una_sola_version_la_obra_se_genera_igual_que_antes(con):
    novela.montar(con, OBRA, ficha(), PlanAprobado(plan(), 1, "El mapa", "Un mapa."))
    escaleta.asignar_t_discurso(con, OBRA, {"cap-{0:02d}".format(n): n for n in range(1, 11)})
    assert [e["id"] for e in regeneracion.escenas_de_version(con, OBRA)] == [
        e["id"] for e in escaleta.escenas_de(con, OBRA)]
    viejo = {"cap-{0:02d}-e1".format(n): [] for n in range(1, 11)}
    for n, imp in enumerate(plan().imprescindibles, 1):
        viejo["{0}-e1".format(imp.capitulo)].append(imp.elemento)
    nuevo = novela.imprescindibles_por_escena(con, OBRA, plan())
    assert {k: [i["elemento"] for i in v] for k, v in nuevo.items()} == \
        {k: v for k, v in viejo.items() if v}


def test_el_material_lleva_el_lugar_de_la_escena_siguiente_de_su_version(con):
    """`F-149`: la accesibilidad de `INV-02` compara donde deja a los presentes la escena
    anterior con el `lugar` de la siguiente, y el Escritor no sabia cual era. La demo de
    B4 paro en el capitulo 9 por eso. La siguiente es **la de la version que se escribe**:
    el capitulo 2 sustituido y el nuevo ocurren en sitios distintos a proposito, para que
    la prueba no pase por coincidencia (Regla 11)."""
    _novela_con_dos_versiones(con)
    con.execute("UPDATE escena SET lugar = 'lug-vieja' WHERE id = 'cap-02-e1'")
    con.execute("UPDATE escena SET lugar = 'lug-nueva' WHERE id = 'cap-02-v2-e1'")
    uno = escaleta.escena(con, "cap-01-e1")
    en_la_2 = modulo_obra.reunir_material(con, uno, OBRA, version=2)
    en_la_1 = modulo_obra.reunir_material(con, uno, OBRA, version=1)
    assert en_la_2["lugar_siguiente"] == "lug-nueva"
    assert en_la_1["lugar_siguiente"] == "lug-vieja"
    ultima = modulo_obra.reunir_material(con, escaleta.escena(con, "cap-10-e1"), OBRA,
                                         version=2)
    assert ultima["lugar_siguiente"] is None


def _con_una_version_3_sin_escribir(con):
    """La 2 publicada y una 3 recien creada por una cascada, con su capitulo 5 sin escribir:
    el estado de la demo de B4 a mitad."""
    _novela_con_dos_versiones(con)
    capitulos = brief.capitulos_de_version(con, OBRA, 2)
    capitulos[4] = "cap-05-v3"
    brief.crear_version(con, OBRA, capitulos, anterior=2, commit="abc9999")


def test_la_lectura_web_lee_la_ultima_publicada_y_no_la_ultima_creada(con):
    """`F-150`: `lectura/repository` tenia su propia copia de la regla de la vigente, con
    `MAX(numero)`, y la web ensenaba como vigente la version que la cascada estaba
    escribiendo. Es `CE-14` (`F-121`) otra vez, por una copia que llego de otra rama."""
    from app.features.lectura import repository as lectura
    _con_una_version_3_sin_escribir(con)
    ids = [c["id"] if isinstance(c, dict) else c[0] for c in lectura.capitulos(con, OBRA)]
    assert "cap-02-v2" in ids and "cap-05-v3" not in ids, ids


def test_el_arrastre_se_mide_sobre_la_ultima_publicada(con):
    """`F-150`, la otra copia: `arrastre.medir` tomaba la ultima creada, y con una version
    a medio escribir decia que la obra estaba incompleta."""
    _con_una_version_3_sin_escribir(con)
    assert arrastre.medir(con, OBRA)["medido"] is True
