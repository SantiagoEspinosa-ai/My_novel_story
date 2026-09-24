"""`F-64`: los identificadores de un plan aprobado son de su obra.

El Planificador pone los mismos identificadores en todas las novelas (`cap-01`,
`per-irene`, `lug-casa`), y las tablas que los reciben tienen clave global. Acotarlos
a la obra en un solo punto, al leer el plan, hace que todo lo de abajo —montar,
escribir, el contexto del Escritor— use los mismos sin tener que traducir nada.
"""

from app.features.planificacion.ids import acotar_a_la_obra
from app.features.planificacion.tests.conftest import plan


def test_capitulos_personajes_y_lugares_quedan_acotados_a_la_obra():
    p = acotar_a_la_obra(plan(), "obra-a")
    assert [c.id for c in p.capitulos][:2] == ["obra-a-cap-01", "obra-a-cap-02"]
    assert {x.id for x in p.mundo.personajes} == {"obra-a-per-irene", "obra-a-per-brisa"}
    assert [l.id for l in p.mundo.lugares] == ["obra-a-lug-casa"]


def test_las_referencias_siguen_a_lo_que_citan():
    """Si solo se acotara la declaracion, el plan dejaria de validar: cada cita
    tiene que apuntar al identificador nuevo."""
    p = acotar_a_la_obra(plan(), "obra-a")
    e = p.capitulos[0].escenas[0]
    assert (e.lugar, e.pov) == ("obra-a-lug-casa", "obra-a-per-irene")
    assert {x.empieza_en for x in p.mundo.personajes} == {"obra-a-lug-casa"}
    assert {i.capitulo for i in p.imprescindibles} == {
        "obra-a-cap-01", "obra-a-cap-02", "obra-a-cap-04"}


def test_dos_obras_con_el_mismo_plan_no_comparten_ningun_identificador():
    a, b = acotar_a_la_obra(plan(), "obra-a"), acotar_a_la_obra(plan(), "obra-b")

    def ids(p):
        return ({c.id for c in p.capitulos} | {x.id for x in p.mundo.personajes}
                | {l.id for l in p.mundo.lugares})

    assert not ids(a) & ids(b)


def test_acotar_dos_veces_no_acota_dos_veces():
    """Un plan que ya viene acotado —el de la base, al relanzar— se queda igual."""
    una = acotar_a_la_obra(plan(), "obra-a")
    assert acotar_a_la_obra(una, "obra-a") == una


def test_los_hechos_no_se_acotan():
    """`hecho_canonico` ya tiene clave `(obra, id)` desde `F-39`: acotarlos
    cambiaria lo que el Escritor tiene que citar sin arreglar nada."""
    p = acotar_a_la_obra(plan(hechos=[{"id": "hec-mapa", "enunciado": "hay un mapa"}]), "obra-a")
    assert [h.id for h in p.hechos] == ["hec-mapa"]
