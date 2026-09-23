"""El delta se guarda, no solo se aplica.

`SPEC-01` §3.2.2 declara `delta_de_escena` como **fuente de verdad del estado**
y hasta ahora el delta se aplicaba y se tiraba: lo que quedaba era su *efecto*
-donde esta cada quien, quien sabe que-, no lo que cada escena aporto. Con solo
el efecto no se puede responder que aporto la escena 7, ni comparar el delta
viejo con el nuevo, ni recalcular el estado desde un punto; y `VER-09`, que
reconstruye el estado acumulando deltas en orden, da por hecho que los deltas
estan.

`SPEC-23` lo separa de las decisiones que tiene abiertas: guardar el delta no
elige ninguna de sus cinco salidas, porque **las cinco lo necesitan**.

POR QUE SE GUARDA POR ESCENA Y VERSION
---------------------------------------
El delta y el texto vienen en la misma respuesta del Escritor (`RF-09`), asi
que son dos mitades del mismo intento y se versionan igual. Guardar solo el
ultimo delta de cada escena perderia justo el dato que hace falta para saber
si una regeneracion movio el estado del mundo o solo cambio la prosa.

La version puede faltar -hoy `consolidar` no siempre la conoce- y entonces se
guarda **ausente**, nunca como cero: un cero se lee como "la version 0" y un
hueco se lee como lo que es.
"""

import sqlite3

import pytest

from app.features.consolidacion import aplicar, deltas


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"marta": ("vivo", "salon")})
    return c


DELTA = {
    "cambio_de_valor": {"eje": "conocimiento", "signo": "negativo"},
    "revelaciones": [{"sujeto": "marta", "hecho": "hec-llave"}],
    "acciones": [{"personaje": "marta", "hecho": "hec-herencia"}],
    "movimientos": [{"personaje": "marta", "a": "cocina"}],
}


def test_el_delta_guardado_vuelve_igual(con):
    """Round trip. `acciones` es el campo que hoy se perdia entero."""
    deltas.guardar(con, "e1", DELTA, version=1)

    guardados = deltas.leer(con, "e1")

    assert len(guardados) == 1
    assert guardados[0]["version"] == 1
    assert guardados[0]["delta"] == DELTA


def test_consolidar_guarda_el_delta_que_aplica(con):
    """No es un paso aparte que alguien pueda olvidar: lo hace la consolidacion."""
    aplicar.consolidar(con, "e1", DELTA, version=2)

    guardados = deltas.leer(con, "e1")

    assert [g["version"] for g in guardados] == [2]
    assert guardados[0]["delta"]["acciones"] == DELTA["acciones"]


def test_un_delta_que_falla_a_mitad_no_deja_delta_guardado(con):
    """Dentro de la transaccion, como el conocimiento.

    Fuera de ella quedaria escrito el delta de una escena que no ocurrio, que
    es el estado a medias que `INV-05` no sabe clasificar, por otra puerta.
    """
    roto = {
        "movimientos": [{"personaje": "marta", "a": "cocina"}],
        "cambios_de_estado_vital": [{"personaje": "nadie", "de": "vivo", "a": "muerto"}],
    }

    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", roto, version=1)

    assert deltas.leer(con, "e1") == []


def test_el_delta_viejo_sobrevive_al_nuevo(con):
    """Lo que hace posible comparar antes y despues de una regeneracion.

    Es la pregunta que `SPEC-23` `S-3` tiene que poder responder: si el delta
    nuevo es igual al viejo, el cambio fue de prosa y nada posterior queda
    invalidado.
    """
    deltas.guardar(con, "e1", DELTA, version=1)
    otro = dict(DELTA, movimientos=[{"personaje": "marta", "a": "sotano"}])

    deltas.guardar(con, "e1", otro, version=2)

    guardados = deltas.leer(con, "e1")
    assert [g["version"] for g in guardados] == [1, 2]
    assert guardados[0]["delta"]["movimientos"] != guardados[1]["delta"]["movimientos"]


def test_una_version_que_no_consta_se_guarda_ausente_y_no_como_cero(con):
    """`RF-25` en la base: un dato que no se ha medido no se rellena."""
    deltas.guardar(con, "e1", DELTA)

    assert deltas.leer(con, "e1")[0]["version"] is None


def test_leer_una_escena_sin_delta_devuelve_vacio_y_no_falla(con):
    assert deltas.leer(con, "e9") == []
