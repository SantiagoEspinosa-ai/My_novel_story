"""`PLAN-28` E2 y E3: las tres lecturas de la story bible, y atender una llamada.

Dos novelas en la misma base, montadas desde el mismo plan acotado a cada una
(`F-64`): es donde se ve si una lectura se queda en su obra (`SPEC-28` `RF-06`).
"""

import json
import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio import story_bible as sb
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.features.cronologia import repository as cronologia
from app.features.orquestacion import novela
from app.features.orquestacion import story_bible as tools
from app.features.planificacion import repository as planes
from app.features.planificacion.ids import acotar_a_la_obra
from app.features.planificacion.service import PlanAprobado
from app.features.planificacion.tests.conftest import ficha, plan

MARCADOR = "MARCADOR-DEL-TEXTO-DE-LA-ESCENA"


def _montar(con, obra):
    p = acotar_a_la_obra(plan(), obra)
    novela.montar(con, obra, ficha(), PlanAprobado(p, 1, "T", "P"))
    planes.asegurar_tablas(con)
    planes.guardar(con, obra, 1, p, True, "revisor", [])
    escena = "{0}-cap-01-e1".format(obra)
    cronologia.registrar_usos(con, [{"hecho": "imp-01", "escena": escena,
                                     "capitulo": "{0}-cap-01".format(obra),
                                     "tipo": TipoDeUsoDeHecho.ESTABLECE,
                                     "origen": OrigenDeUso.DELTA}])
    with con:
        con.execute("INSERT INTO borrador (escena, version, texto) VALUES (?, 1, ?)",
                    (escena, MARCADOR))
        for n, t in ((2, "2026-06-02T10:00"), (1, "2026-06-01T10:00")):
            ev = "evt-{0}-cap-{1:02d}-e1".format(obra, n)
            con.execute("INSERT INTO evento_cronologico (id, obra, t_fabula, duracion_min, "
                        "lugar, escena, capitulo) VALUES (?, ?, ?, 60, ?, ?, ?)",
                        (ev, obra, t, "{0}-lug-casa".format(obra),
                         "{0}-cap-{1:02d}-e1".format(obra, n), "{0}-cap-{1:02d}".format(obra, n)))
            con.execute("INSERT INTO participacion_en_evento (evento, personaje, presencia) "
                        "VALUES (?, ?, 'presente')", (ev, "{0}-per-irene".format(obra)))


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    _montar(c, "obra-a")
    _montar(c, "obra-b")
    return c


def test_hechos_trae_cada_uso_con_su_capitulo_y_su_tipo(con):
    s = tools.leer_hechos(con, "obra-a", sb.EntradaHechos(hecho="imp-01"))
    [h] = s.hechos
    assert [(u.capitulo, u.tipo.value) for u in h.usos] == [("obra-a-cap-01", "establece")]


def test_hechos_no_cuenta_usos_de_escenas_de_otra_obra(con):
    """`imp-01` existe en las dos novelas: sin filtrar por las escenas de la obra, sus
    usos se mezclarian, que es lo que paso con `INV-24` (`F-65`)."""
    [h] = tools.leer_hechos(con, "obra-a", sb.EntradaHechos(hecho="imp-01")).hechos
    assert all(u.capitulo.startswith("obra-a") for u in h.usos) and len(h.usos) == 1


def test_la_ficha_de_personaje_sale_del_plan_aprobado_y_del_estado_vigente(con):
    s = tools.leer_ficha(con, "obra-a", sb.EntradaFicha(id="obra-a-per-irene"))
    assert s.personaje.nombre_canonico == "Irene Valdés"
    assert s.personaje.estado_vital.value == "vivo"


def test_la_ficha_de_un_lugar(con):
    s = tools.leer_ficha(con, "obra-a", sb.EntradaFicha(id="obra-a-lug-casa"))
    assert (s.lugar.nombre, s.lugar.atmosfera) == ("Casa", None)


def test_la_ficha_de_una_entidad_de_otra_obra_no_existe(con):
    with pytest.raises(tools.NoExisteEnLaObra):
        tools.leer_ficha(con, "obra-a", sb.EntradaFicha(id="obra-b-per-irene"))


def test_alias_rol_y_atmosfera_salen_vacios_porque_no_tienen_fuente(con):
    p = tools.leer_ficha(con, "obra-a", sb.EntradaFicha(id="obra-a-per-irene")).personaje
    assert (p.alias, p.rol_dramatico) == ([], None)


def test_la_cronologia_va_en_orden_de_fabula_con_presentes_y_lugar(con):
    s = tools.leer_cronologia(con, "obra-a", sb.EntradaCronologia())
    assert [e.capitulo for e in s.eventos] == ["obra-a-cap-01", "obra-a-cap-02"]
    assert s.eventos[0].personajes_presentes == ["obra-a-per-irene"]
    assert s.eventos[0].lugar == "obra-a-lug-casa"


def test_la_cronologia_no_trae_eventos_de_otra_obra(con):
    s = tools.leer_cronologia(con, "obra-a", sb.EntradaCronologia())
    assert all(e.id.startswith("evt-obra-a") for e in s.eventos)


def test_la_cronologia_de_un_capitulo(con):
    s = tools.leer_cronologia(con, "obra-a", sb.EntradaCronologia(capitulo="obra-a-cap-02"))
    assert [e.capitulo for e in s.eventos] == ["obra-a-cap-02"]


def test_ninguna_lectura_devuelve_el_texto_de_una_escena(con):
    """`RF-05`, por contenido y no solo por esquema: el texto de la escena lleva un
    marcador y no aparece en nada de lo que devuelven las tres."""
    salidas = [tools.leer_hechos(con, "obra-a", sb.EntradaHechos()),
               tools.leer_ficha(con, "obra-a", sb.EntradaFicha(id="obra-a-per-irene")),
               tools.leer_cronologia(con, "obra-a", sb.EntradaCronologia())]
    assert all(MARCADOR not in s.model_dump_json() for s in salidas)


def test_las_lecturas_funcionan_con_una_conexion_de_solo_lectura(tmp_path):
    ruta = tmp_path / "obra.db"
    c = sqlite3.connect(str(ruta))
    migraciones.migrar(c)
    _montar(c, "obra-a")
    c.close()
    ro = sqlite3.connect("file:{0}?mode=ro".format(ruta.as_posix()), uri=True)
    assert tools.leer_hechos(ro, "obra-a", sb.EntradaHechos()).hechos
    assert tools.leer_ficha(ro, "obra-a", sb.EntradaFicha(id="obra-a-per-irene")).personaje
    assert tools.leer_cronologia(ro, "obra-a", sb.EntradaCronologia()).eventos
