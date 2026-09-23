"""La rendicion: que pasa cuando una escena no sale limpia y se agotan los
intentos.

LO QUE NO SE RINDE NUNCA
-------------------------
Una invariante `bloqueante` abierta. `Docs/architecture.md` lo dice sin margen:
*"el delta de una escena rendida entra al canon igual que el de una limpia, y
una falsedad en el canon la heredan todas las escenas siguientes"*. La salida
de ahi es humana, no automatica.

LO QUE SI SE RINDE
------------------
`mayor` y `menor`. Se elige el borrador menos malo, `borrador_aceptado` dice
cual y la escena queda en `aceptada_por_rendicion` — un estado distinto de
`aceptada`, para que quien lea el manuscrito sepa que esa escena paso sin estar
limpia.

POR QUE SE COMPARA SIN PESOS
-----------------------------
`Docs/definitions.md` deja los pesos por severidad como **decision abierta**:
*"no se fijan aqui"*, salen de medir. Asi que aqui **no se inventa ninguno**: se
ordena por cuantos hallazgos hay de cada severidad, de la mas grave a la menos.
Ese orden es el mismo que daria cualquier asignacion de pesos crecientes, asi
que no adelanta la decision — solo deja de necesitarla para este caso.
"""

from app.commons.dominio.enumeraciones import EstadoDeHallazgo, Severidad
from app.commons.dominio.modelos import Hallazgo
from app.features.orquestacion import rendicion


def _h(severidad, estado=EstadoDeHallazgo.ABIERTO, inv="INV-17"):
    return Hallazgo(invariante=inv, verificador="v", escena="e1",
                    severidad=severidad, estado=estado, descripcion="x")


def test_un_bloqueante_abierto_no_se_rinde_nunca():
    """La falsedad entraria al canon y la heredarian todas las siguientes."""
    assert not rendicion.puede_rendirse([_h(Severidad.BLOQUEANTE, inv="INV-03")])


def test_con_mayores_y_menores_si_se_rinde():
    assert rendicion.puede_rendirse([_h(Severidad.MAYOR), _h(Severidad.MENOR)])


def test_sin_hallazgos_se_rinde_trivialmente():
    assert rendicion.puede_rendirse([])


def test_un_sin_veredicto_no_impide_rendirse():
    """`SPEC-18` C-3: no consta que nada se haya roto. Lo que hace es impedir
    cerrar el capitulo, y eso ocurre una puerta mas arriba."""
    assert rendicion.puede_rendirse(
        [_h(Severidad.BLOQUEANTE, EstadoDeHallazgo.SIN_VEREDICTO, "INV-04")])


def test_el_menos_malo_es_el_que_tiene_menos_hallazgos_graves():
    intentos = [(1, [_h(Severidad.MAYOR), _h(Severidad.MENOR)]),
                (2, [_h(Severidad.MENOR), _h(Severidad.MENOR), _h(Severidad.MENOR)])]
    assert rendicion.menos_malo(intentos) == 2, "tres menores pesan menos que un mayor"


def test_a_igualdad_de_graves_gana_el_que_tiene_menos_leves():
    intentos = [(1, [_h(Severidad.MAYOR), _h(Severidad.MENOR)]),
                (2, [_h(Severidad.MAYOR)])]
    assert rendicion.menos_malo(intentos) == 2


def test_a_igualdad_total_gana_el_primero():
    """Determinismo: dos intentos igual de malos no pueden dar resultados
    distintos segun el orden en que se lean."""
    intentos = [(1, [_h(Severidad.MENOR)]), (2, [_h(Severidad.MENOR)])]
    assert rendicion.menos_malo(intentos) == 1


def test_un_sin_veredicto_pesa_el_maximo_de_la_escala_y_no_mas():
    """`Docs/definitions.md`: *"si el mudo ganara siempre, un intento con un
    juez caido seria automaticamente peor que otro con tres fallos reales, y
    eso no es cierto"*. Pesa como un `bloqueante`, no mas."""
    intentos = [(1, [_h(Severidad.BLOQUEANTE, EstadoDeHallazgo.SIN_VEREDICTO)]),
                (2, [_h(Severidad.BLOQUEANTE), _h(Severidad.BLOQUEANTE)])]
    assert rendicion.menos_malo(intentos) == 1


def test_sin_intentos_no_hay_nada_que_elegir():
    assert rendicion.menos_malo([]) is None


# --- El tope global: el freno de mano de la obra entera -------------------

def test_el_tope_global_para_la_obra_y_dice_por_que():
    """Acota el **gasto**, no el error. Una obra que se ha ido de madre se
    detiene antes de gastarse el presupuesto de alguien."""
    assert rendicion.queda_presupuesto(gastadas=10, tope=20)
    assert not rendicion.queda_presupuesto(gastadas=20, tope=20)


def test_el_tope_global_cuenta_todas_las_delegaciones_no_solo_las_del_escritor():
    """El Juez y el Resumidor tambien se pagan. Contar solo al Escritor daria
    un tope que se pasa por tres."""
    assert rendicion.delegaciones_de([{"delegaciones": 3}, {"delegaciones": 2}]) == 5
