"""C3 — El contrato del Escritor: texto y delta en la misma llamada.

`RF-15` y `A-03`. Pedir el delta despues, releyendo la escena, es mas caro y
menos fiel: el modelo tendria que deducir lo que el mismo acaba de decidir.

Y `VER-20`: una respuesta sin delta se rechaza **antes de las puertas**. No es
un hallazgo, es un fallo de contrato -y por `O-3` no se reintenta-.
"""

import pytest

from app.features.generacion import contrato


def test_una_respuesta_sin_delta_se_rechaza_antes_de_las_puertas():
    """El caso negativo de `VER-20`."""
    with pytest.raises(contrato.FalloDeContrato, match="delta"):
        contrato.leer({"texto": "La puerta estaba abierta."})


def test_una_respuesta_sin_texto_tambien():
    with pytest.raises(contrato.FalloDeContrato):
        contrato.leer({"delta": {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"}}})


def test_un_delta_fuera_de_esquema_es_fallo_de_contrato_y_no_se_reintenta():
    from app.commons.modelo import cliente
    with pytest.raises(contrato.FalloDeContrato):
        contrato.leer({"texto": "x", "delta": {"cambio_de_valor": {"eje": "dinero", "signo": "negativo"}}})
    assert cliente.se_reintenta("contrato") is False


def test_una_respuesta_completa_se_lee():
    r = contrato.leer({
        "texto": "La puerta estaba abierta.",
        "delta": {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"}},
    })
    assert r.texto.startswith("La puerta")
    assert r.delta["cambio_de_valor"]["eje"] == "seguridad"


def test_una_respuesta_vacia_es_fallo_y_no_un_texto_vacio():
    """`MF` del agente que devuelve vacio: un vacio que pasa es peor que un fallo."""
    with pytest.raises(contrato.FalloDeContrato):
        contrato.leer({"texto": "   ", "delta": {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"}}})


def test_una_revelacion_en_prosa_es_fallo_de_contrato_no_de_continuidad():
    """`F-21` y la Regla 4. Se detecta en la frontera, no en la puerta.

    Es el caso real de la primera generacion: el modelo devolvio frases donde
    el dominio quiere identificadores, e `INV-03` lo denuncio como "actua sobre
    un hecho que no conoce" con severidad `bloqueante`.
    """
    with pytest.raises(contrato.FalloDeContrato, match="identificador"):
        contrato.leer({
            "texto": "x",
            "delta": {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
                      "revelaciones": [{"sujeto": "casa familiar",
                                        "hecho": "el reloj funciona sin cuerda"}]},
        })


def test_una_revelacion_con_identificadores_pasa():
    r = contrato.leer({
        "texto": "x",
        "delta": {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
                  "revelaciones": [{"sujeto": "per-marta", "hecho": "hec-reloj"}]},
    })
    assert r.delta["revelaciones"][0]["sujeto"] == "per-marta"
