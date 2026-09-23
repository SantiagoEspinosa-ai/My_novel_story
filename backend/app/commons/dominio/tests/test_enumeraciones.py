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


# --- `SPEC-21`: los tres vocabularios de los usos y la cronologia -----------


def test_tipo_de_uso_de_hecho_tiene_los_cuatro_valores():
    """`SPEC-21` C-2: no se colapsan en uno.

    Mencionar, depender y contradecir tienen condiciones de verdad distintas y
    consumidores distintos. Si alguien redujera la enumeracion a un solo valor
    "usa", las cuatro capacidades que cuelgan de ella dejarian de poder
    distinguir lo que necesitan distinguir, y esta prueba es lo que lo impide.
    """
    assert [u.value for u in enums.TipoDeUsoDeHecho] == [
        "establece",
        "menciona",
        "depende",
        "contradice",
    ]


def test_origen_de_uso_distingue_lo_medido_de_lo_afirmado():
    """Una fila calculada por codigo no es lo mismo que una declarada por un
    modelo, y un demostrador formal no puede tratarlas igual."""
    assert [o.value for o in enums.OrigenDeUso] == [
        "regla",
        "delta",
        "juez_llm",
        "humano",
    ]


def test_tipo_de_presencia_separa_estar_de_ser_nombrado():
    """`SPEC-21` C-3: un personaje del que se habla no esta en el evento.

    Sin esta separacion, la comprobacion de que nadie esta en dos lugares a la
    vez se convierte en una fabrica de falsos positivos.
    """
    assert [p.value for p in enums.TipoDePresencia] == ["presente", "mencionado"]
