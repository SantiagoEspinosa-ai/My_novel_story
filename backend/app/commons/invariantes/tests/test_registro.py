"""A2 — El registro de invariantes y el comportamiento de la severidad.

Dos cosas distintas y las dos viven aqui, porque `D-4` de `SPEC-01` dice que
la diferencia entre severidades **se implementa una vez** y no caso por caso.

La primera prueba es el caso negativo de `VER-38`: un registro cuya severidad
no coincida con la tabla de `Docs/definitions.md` tiene que fallar. `VER-38`
es el puesto 1 de la orden de implantacion porque valida a otros tres:
`VER-11`, `VER-12` y `VER-22` pueden estar los tres en verde con una severidad
mal puesta, que es el anti-patron de bajar una bloqueante para desatascar.
"""

import pytest

from app.commons.dominio import enumeraciones as enums
from app.commons.invariantes import registro
from app.commons.invariantes.severidad import (
    detiene_la_escena,
    impide_cerrar_el_capitulo,
    se_lista_al_firmar,
)


def test_estan_las_dieciocho_y_sin_huecos():
    """Un hueco significa que se borro una invariante publicada, y en este
    proyecto lo que deja de aplicar se marca obsoleto pero no se quita."""
    ids = sorted(registro.TODAS)
    assert ids == ["INV-{0:02d}".format(i) for i in range(1, 19)]


def test_la_clasificacion_es_la_de_definitions():
    """Muestreo de las filas que mas han cambiado, con su valor de hoy."""
    assert registro.TODAS["INV-03"].severidad is enums.Severidad.BLOQUEANTE
    assert registro.TODAS["INV-03"].tipo is enums.TipoDeVerificador.REGLA
    assert registro.TODAS["INV-10"].tipo is enums.TipoDeVerificador.JUEZ_LLM
    assert registro.TODAS["INV-17"].severidad is enums.Severidad.MAYOR
    assert registro.TODAS["INV-17"].nivel is enums.NivelDeEvaluacion.ESCENA
    # `INV-18` es `mayor` y no `bloqueante`: lo que falta es una declaracion,
    # no una falsedad, asi que no corrompe el canon (`SPEC-19` P-2).
    assert registro.TODAS["INV-18"].severidad is enums.Severidad.MAYOR
    assert registro.TODAS["INV-18"].tipo is enums.TipoDeVerificador.REGLA


def test_solo_una_invariante_es_de_juez():
    """`SPEC-04` dejo quince reglas y una de juez."""
    de_juez = [i for i in registro.TODAS.values()
               if i.tipo is enums.TipoDeVerificador.JUEZ_LLM]
    assert [i.id for i in de_juez] == ["INV-10"]


def test_caso_negativo_una_severidad_que_no_coincide_con_la_tabla():
    """El caso negativo de `VER-38`: el registro no se puede construir mal."""
    with pytest.raises(ValueError, match="INV-01"):
        registro.construir_invariante(
            id="INV-01",
            enunciado="Toda escena tiene cambio_de_valor no nulo",
            nivel="escena",
            severidad="mayor",          # en la tabla es `bloqueante`
            tipo="regla",
            que_lee="Escena.cambio_de_valor",
            severidad_esperada=enums.Severidad.BLOQUEANTE,
        )


def test_bloqueante_detiene_mayor_y_menor_no():
    assert detiene_la_escena(enums.Severidad.BLOQUEANTE) is True
    assert detiene_la_escena(enums.Severidad.MAYOR) is False
    assert detiene_la_escena(enums.Severidad.MENOR) is False


def test_la_diferencia_entre_mayor_y_menor_esta_en_la_puerta_de_capitulo():
    """`SPEC-04` C-2. Sin esto las dos severidades harian lo mismo."""
    assert impide_cerrar_el_capitulo(enums.Severidad.MAYOR) is True
    assert impide_cerrar_el_capitulo(enums.Severidad.MENOR) is False
    assert se_lista_al_firmar(enums.Severidad.MENOR) is True


# NO HAY PRUEBA DEL PESO DE `sin_veredicto`, Y ES DELIBERADO.
# `SPEC-10` C-2 decidio que pesa "lo maximo posible", pero los pesos por
# severidad siguen siendo decision abierta en `Docs/definitions.md`. "Lo maximo
# posible" admite dos implementaciones que no son equivalentes -el mayor peso
# de la escala, o un peso que gana a cualquiera- y elegir aqui seria decidir
# por el documento. Queda anotado y sin codigo.
