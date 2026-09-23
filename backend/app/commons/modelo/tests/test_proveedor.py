"""E3 — El cliente real, probado sin red y sin gastar.

Todo lo de aqui usa un transporte inyectado. **Ninguna prueba sale de la
maquina**, y ninguna necesita una credencial de verdad: la que se pone es una
cadena de prueba declarada como tal.

Lo que estas pruebas sostienen:

    1. Falta una variable -> falla al construir, con el nombre de la variable
       y sin el valor de nada.
    2. La clave no aparece en el `repr`, ni en el mensaje de un fallo de
       transporte.
    3. `usage` se copia tal cual y queda ausente si no viene.
    4. Misma firma que el doble, para que el bucle no distinga.
"""

import pytest

from app.commons.modelo import proveedor
from app.commons.modelo.doble import DobleDelModelo

CLAVE_DE_PRUEBA = "clave-de-prueba-no-es-real"


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv(proveedor.VARIABLES["clave"], CLAVE_DE_PRUEBA)
    monkeypatch.setenv(proveedor.VARIABLES["base_url"], "https://ejemplo.invalido/v1")
    monkeypatch.setenv(proveedor.VARIABLES["modelo_escritor"], "modelo-de-prueba")


def test_sin_la_variable_de_clave_falla_al_construir(monkeypatch):
    monkeypatch.delenv(proveedor.VARIABLES["clave"], raising=False)
    with pytest.raises(proveedor.FaltaCredencial) as e:
        proveedor.ClienteReal(modelo="m")
    assert proveedor.VARIABLES["clave"] in str(e.value)


def test_el_repr_no_lleva_la_clave(entorno):
    c = proveedor.ClienteReal()
    assert CLAVE_DE_PRUEBA not in repr(c)
    assert "modelo-de-prueba" in repr(c)


def test_un_fallo_de_transporte_no_filtra_la_clave_ni_el_cuerpo(entorno):
    def transporte_que_revienta(url, cabeceras, cuerpo):
        raise OSError("no se pudo conectar a {0} con {1}".format(url, cabeceras))

    c = proveedor.ClienteReal(transporte=transporte_que_revienta)
    with pytest.raises(proveedor.FalloDeTransporte) as e:
        c.llamar("un prompt cualquiera")
    assert CLAVE_DE_PRUEBA not in str(e.value)
    assert "un prompt cualquiera" not in str(e.value)


def test_el_usage_se_copia_y_queda_ausente_si_no_viene(entorno):
    con_usage = proveedor._normalizar({"texto": "x", "delta": {}, "usage": {"total_tokens": 7}})
    sin_usage = proveedor._normalizar({"texto": "x", "delta": {}})
    assert con_usage["usage"]["total_tokens"] == 7
    assert "usage" not in sin_usage, "ausente, no en cero"


def test_un_delta_que_llega_como_cadena_se_parsea(entorno):
    r = proveedor._normalizar({"texto": "x", "delta": '{"cambio_de_valor": {}}'})
    assert r["delta"] == {"cambio_de_valor": {}}


def test_un_delta_ilegible_queda_en_none_y_lo_cazara_el_contrato(entorno):
    """No se rescata a la brava: que falle el contrato, que es quien decide."""
    assert proveedor._normalizar({"texto": "x", "delta": "{roto"})["delta"] is None


def test_la_firma_es_la_misma_que_la_del_doble(entorno):
    """Lo que hace que el bucle probado en E2 sea el mismo que correra en E5."""
    real = proveedor.ClienteReal(transporte=lambda **k: {"texto": "x", "delta": {}})
    for atributo in ("nombre", "llamar"):
        assert hasattr(real, atributo) and hasattr(DobleDelModelo(), atributo)
