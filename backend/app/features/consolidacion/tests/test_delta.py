"""C5 — La consolidacion, que es donde se corta la propagacion del error.

`INV-05`: hasta que el delta no esta aplicado, el estado del mundo no ha
cambiado y la escena siguiente **no puede generarse**.

La prueba que abre el paso es la del delta a medias, porque es la unica
categoria de fallo de la que no se sale reintentando: los demas detienen el
trabajo y dejan el estado intacto; este lo corrompe, y todo lo que se genere
encima hereda la corrupcion sin que nada avise.
"""

import sqlite3

import pytest

from app.features.consolidacion import aplicar


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"marta": ("vivo", "salon")})
    return c


def test_un_delta_que_falla_a_mitad_no_deja_el_estado_a_medias(con):
    """LA prueba del paso. Atomicidad, no buena intencion."""
    delta = {
        "movimientos": [{"personaje": "marta", "a": "cocina"}],
        "cambios_de_estado_vital": [{"personaje": "nadie", "de": "vivo", "a": "muerto"}],
    }
    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", delta)

    # El primer cambio no puede haber quedado escrito.
    assert aplicar.estado(con)["marta"] == ("vivo", "salon")


def test_un_delta_valido_se_aplica_entero(con):
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "cocina"}]})
    assert aplicar.estado(con)["marta"] == ("vivo", "cocina")


def test_la_escena_siguiente_no_se_genera_sin_el_delta_aplicado(con):
    """`INV-05` e `INV-19` del proceso: la puerta que corta la propagacion."""
    assert aplicar.puede_generarse_la_siguiente(con, "e1") is False
    aplicar.consolidar(con, "e1", {"movimientos": []})
    assert aplicar.puede_generarse_la_siguiente(con, "e1") is True


def test_consolidar_dos_veces_la_misma_escena_no_duplica(con):
    aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "cocina"}]})
    with pytest.raises(aplicar.YaConsolidada):
        aplicar.consolidar(con, "e1", {"movimientos": [{"personaje": "marta", "a": "sotano"}]})
    assert aplicar.estado(con)["marta"] == ("vivo", "cocina")


# --- `SPEC-21` C-4: lo que se escribe al consolidar, se escribe con el delta -


def test_el_acta_de_la_escena_se_escribe_dentro_de_la_transaccion(con):
    """`SPEC-21` C-4. El acta y el estado caen o se salvan juntos.

    Quien quiera escribir algo mas al consolidar -los usos de un hecho, el
    evento de la cronologia- pasa una funcion, y esa funcion corre **dentro**
    de la misma transaccion. Fuera de ella, un delta que falle a medias dejaria
    registrado el uso de un hecho en una escena que no llego a ocurrir: el
    estado a medias que `INV-05` no sabe clasificar, por otra puerta.

    No se importa `cronologia/` aqui: `consolidacion/` no sabe quien escribe ni
    que escribe, solo que ocurre con su delta. Componer es de `orquestacion/`
    (`A-02`).
    """
    escrito = []

    def _acta(conexion):
        conexion.execute("CREATE TABLE IF NOT EXISTS acta (escena TEXT)")
        conexion.execute("INSERT INTO acta VALUES ('e1')")
        escrito.append(True)

    delta = {
        "movimientos": [{"personaje": "marta", "a": "cocina"}],
        "cambios_de_estado_vital": [{"personaje": "nadie", "de": "vivo", "a": "muerto"}],
    }
    with pytest.raises(aplicar.DeltaIncompatible):
        aplicar.consolidar(con, "e1", delta, al_consolidar=_acta)

    con.execute("CREATE TABLE IF NOT EXISTS acta (escena TEXT)")
    assert con.execute("SELECT COUNT(*) FROM acta").fetchone()[0] == 0


def test_el_acta_se_escribe_cuando_el_delta_entra(con):
    def _acta(conexion):
        conexion.execute("CREATE TABLE IF NOT EXISTS acta (escena TEXT)")
        conexion.execute("INSERT INTO acta VALUES ('e1')")

    aplicar.consolidar(
        con, "e1", {"movimientos": [{"personaje": "marta", "a": "cocina"}]},
        al_consolidar=_acta)
    assert con.execute("SELECT COUNT(*) FROM acta").fetchone()[0] == 1


# --- `SPEC-21` C-3: la fecha de nacimiento, que es del personaje ------------


def test_la_fecha_de_nacimiento_se_fija_y_se_lee(con):
    """Vive en `entidad` y no en una tabla nueva de personajes.

    `entidad.id` **ya es** el identificador de personaje: es el que usan los
    movimientos y los cambios de estado vital del delta. Crear una tabla
    `personaje` en paralelo dejaria dos sitios donde consta quien existe, y la
    copia que alguien olvide actualizar seria justo la que lea la comprobacion
    de edad.
    """
    aplicar.fijar_fecha_de_nacimiento(con, "marta", "1862-04-11")
    assert aplicar.fechas_de_nacimiento(con) == {"marta": "1862-04-11"}


def test_un_personaje_sin_fecha_no_aparece_en_el_mapa(con):
    """Y no aparece como `None`: la comprobacion de edad distingue "no cuadra"
    de "no se puede saber", y para eso el que no la tiene tiene que faltar."""
    assert aplicar.fechas_de_nacimiento(con) == {}
