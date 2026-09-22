"""A1 — La frontera de validacion.

`CLAUDE.md` dice dos cosas sobre los modelos Pydantic, y esta prueba existe
para que las dos dejen de ser una intencion:

    "Los valores de los vocabularios controlados se implementan como `Enum`,
     no como cadenas libres."
    "Un valor fuera de la enumeracion es un error de validacion, no un aviso."

La diferencia entre error y aviso es la que importa: un aviso lo lee alguien
si mira, y un error detiene la peticion. `RF-xx` de la API devuelve 422
precisamente porque esto levanta excepcion aqui abajo.
"""

import pytest
from pydantic import ValidationError

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import Hallazgo


def test_los_valores_del_vocabulario_son_los_de_definitions():
    """Los literales son los de `Docs/definitions.md`, sin traducir ni abreviar."""
    assert [s.value for s in enums.Severidad] == ["bloqueante", "mayor", "menor"]
    assert [e.value for e in enums.EstadoDeHallazgo] == [
        "abierto",
        "resuelto",
        "descartado",
        "sin_veredicto",
    ]
    assert [d.value for d in enums.DurabilidadDelHecho] == ["permanente", "efimero"]


def test_un_valor_fuera_de_la_enumeracion_es_error_no_aviso():
    """El caso negativo: `severidad` no admite una cadena libre."""
    with pytest.raises(ValidationError):
        Hallazgo(
            invariante="INV-01",
            verificador="verificador_de_reglas",
            escena="esc-1",
            severidad="critica",          # no esta en `severidad`
            estado="abierto",
            descripcion="da igual",
        )


def test_un_hallazgo_valido_se_construye():
    h = Hallazgo(
        invariante="INV-01",
        verificador="verificador_de_reglas",
        escena="esc-1",
        severidad="bloqueante",
        estado="abierto",
        descripcion="la escena no cambia ningun valor",
    )
    assert h.severidad is enums.Severidad.BLOQUEANTE
