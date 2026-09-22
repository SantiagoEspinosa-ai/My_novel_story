"""C1 — El ensamblado y el recorte de 2.4, estrenandose.

Lo que estas pruebas sostienen:

    1. Dos vueltas: primero se reduce todo lo reducible, y solo despues se
       eliminan bloques. Un bloque con reduccion pendiente no se elimina.
    2. `RF-26`: agotadas las formas reducidas y eliminados los tres primeros
       bloques, el trabajo **falla en vez de generar**.
    3. El caso negativo que `VER-06` pide: un recortador que itere por los
       seis niveles de `CLAUDE.md` en vez de por los bloques de 2.4 se lleva el
       registro de conocimiento y deja `INV-03` sin datos.
"""

import pytest

from app.features.contexto import recorte
from app.features.contexto.bloques import BLOQUES, Clase


def _contexto(tam):
    """Un contexto de juguete: cada bloque con el tamano que se le pida."""
    return {b.nombre: tam.get(b.nombre, 0) for b in BLOQUES}


def test_los_siete_bloques_en_el_orden_de_2_4():
    assert [b.nombre for b in BLOQUES] == [
        "condensaciones",
        "fichas_y_setups",
        "escena_anterior",
        "estado_y_conocimiento",
        "problemas_del_intento_anterior",
        "reserva_de_salida",
        "inmutable",
    ]


def test_dos_bloques_son_irreducibles_y_lo_dicen():
    irreducibles = [b.nombre for b in BLOQUES if b.forma_reducida is None]
    assert irreducibles == ["reserva_de_salida", "inmutable"]


def test_primero_reduce_todo_y_solo_despues_elimina():
    """La regla de las dos vueltas. Si cabe reduciendo, no se elimina nada."""
    plan = recorte.planificar(_contexto({"condensaciones": 40, "fichas_y_setups": 40}),
                              techo=50)
    assert all(p.clase is Clase.REDUCCION for p in plan)
    assert plan, "algo tenia que recortarse"


def test_no_se_elimina_un_bloque_con_reduccion_pendiente():
    plan = recorte.planificar(_contexto({"condensaciones": 90, "fichas_y_setups": 90}),
                              techo=20)
    nombres_reducidos = {p.bloque for p in plan if p.clase is Clase.REDUCCION}
    for p in plan:
        if p.clase is Clase.ELIMINACION:
            assert p.bloque in nombres_reducidos, (
                "{0} se eliminó sin haberse reducido antes".format(p.bloque)
            )


def test_rf26_falla_en_vez_de_generar():
    """Agotado todo y eliminados los tres primeros, se falla."""
    with pytest.raises(recorte.NoCabe):
        recorte.planificar(_contexto({"inmutable": 500}), techo=10)


def test_rf26_no_toca_los_bloques_cuarto_al_septimo():
    try:
        plan = recorte.planificar(_contexto({b.nombre: 100 for b in BLOQUES}), techo=1)
    except recorte.NoCabe as e:
        plan = e.plan
    eliminados = {p.bloque for p in plan if p.clase is Clase.ELIMINACION}
    assert eliminados <= {"condensaciones", "fichas_y_setups", "escena_anterior"}


def test_caso_negativo_iterar_por_niveles_en_vez_de_por_bloques():
    """`VER-06`. El nivel `Recuperado` se parte en dos bloques que caen a
    distinto lado de la frontera: si se itera por niveles, el registro de
    conocimiento se va con las fichas."""
    por_nivel = recorte.simular_recorte_por_niveles(
        _contexto({b.nombre: 100 for b in BLOQUES}), techo=1)
    assert "estado_y_conocimiento" in por_nivel, (
        "iterar por niveles se lleva el registro de conocimiento e `INV-03` "
        "deja de poder decidir"
    )


def test_los_problemas_del_intento_anterior_se_recortan_de_los_ultimos():
    """Si se van, la reescritura repite el error que la motivo."""
    posiciones = {b.nombre: i for i, b in enumerate(BLOQUES)}
    assert posiciones["problemas_del_intento_anterior"] > posiciones["escena_anterior"]
    assert posiciones["problemas_del_intento_anterior"] > posiciones["estado_y_conocimiento"]


@pytest.mark.xfail(
    strict=True,
    reason="CONTRADICCION EN 2.4, NO FALLO DE ESTE CODIGO. La regla C-3 bis "
           "dice que ninguna forma REDUCIDA se lleva lo que lee una bloqueante "
           "de escena, y no dice nada de la ELIMINACION, que quita mas. El "
           "bloque 2 se reduce al grafo de accesos precisamente porque INV-02 "
           "lo lee, y despues se elimina entero porque esta entre los tres "
           "primeros. Se parte `Lugar` para proteger el grafo y luego se tira. "
           "Hace falta decidir: o el bloque 2 deja de ser eliminable, o el "
           "grafo se muda al bloque 4, que nunca se elimina.",
)
def test_la_eliminacion_respeta_la_misma_regla_que_la_reduccion():
    """Lo que la regla protege al reducir, lo pierde al eliminar."""
    try:
        plan = recorte.planificar(_contexto({b.nombre: 100 for b in BLOQUES}), techo=1)
    except recorte.NoCabe as e:
        plan = e.plan
    eliminados = {p.bloque for p in plan if p.clase is Clase.ELIMINACION}
    con_bloqueante = {b.nombre for b in BLOQUES if b.lee_una_bloqueante}
    assert not (eliminados & con_bloqueante), (
        "se eliminaron bloques que leen una invariante bloqueante de escena: "
        "{0}".format(sorted(eliminados & con_bloqueante))
    )
