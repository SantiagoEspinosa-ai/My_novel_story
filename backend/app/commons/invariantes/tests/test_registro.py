"""A2 — El registro de invariantes y el comportamiento de la severidad.

Dos cosas distintas y las dos viven aqui, porque `D-4` de `SPEC-01` dice que
la diferencia entre severidades **se implementa una vez** y no caso por caso.

La primera prueba es el caso negativo de `VER-38`: un registro cuya severidad
no coincida con la tabla de `docs/definitions.md` tiene que fallar. `VER-38`
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
    # `INV-19` e `INV-20` no son un hueco: `SPEC-21` los reserva para la edad y
    # la ubicuidad sin decidirlos todavia. Por eso `SPEC-25` tomo `INV-21` y no
    # reutilizo un numero apartado. Cualquier otro hueco sigue fallando aqui.
    reservadas = {19, 20}
    assert ids == ["INV-{0:02d}".format(i) for i in range(1, 30)
                   if i not in reservadas]


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


def test_las_invariantes_de_juez_son_las_decididas():
    """`SPEC-04` dejo quince reglas y una de juez, `INV-10`. `SPEC-26` añadio las
    dos del Editor, `INV-26` y `INV-27`, numeradas en `PLAN-26`. Una cuarta que
    aparezca sin spec que la decida hace fallar esto: lo que se puede comprobar
    con codigo no se delega en un modelo."""
    de_juez = [i for i in registro.TODAS.values()
               if i.tipo is enums.TipoDeVerificador.JUEZ_LLM]
    assert sorted(i.id for i in de_juez) == ["INV-10", "INV-26", "INV-27"]


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
# severidad siguen siendo decision abierta en `docs/definitions.md`. "Lo maximo
# posible" admite dos implementaciones que no son equivalentes -el mayor peso
# de la escala, o un peso que gana a cualquiera- y elegir aqui seria decidir
# por el documento. Queda anotado y sin codigo.


# --- `SPEC-26`: las invariantes nuevas y el plano Terror --------------------


def test_las_de_la_novela_regalo_tienen_su_severidad():
    s = {i: registro.TODAS[i].severidad.value for i in
         ("INV-22", "INV-23", "INV-24", "INV-25", "INV-26", "INV-27")}
    assert s == {"INV-22": "bloqueante", "INV-23": "mayor", "INV-24": "bloqueante",
                 "INV-25": "menor", "INV-26": "mayor", "INV-27": "mayor"}
    assert registro.TODAS["INV-26"].tipo is enums.TipoDeVerificador.JUEZ_LLM
    assert registro.TODAS["INV-24"].nivel is enums.NivelDeEvaluacion.OBRA


def test_las_de_terror_estan_obsoletas_y_no_se_aplican_a_ninguna_obra():
    """`SPEC-26` v3 `RF-20`, `RF-21`: se retiran sin renumerar, y siguen en el
    registro para que ningun identificador publicado desaparezca."""
    assert registro.obsoletas() == ["INV-10", "INV-11", "INV-12", "INV-16"]
    for genero in ("terror", "aventura"):
        assert not registro.aplica("INV-12", genero)


def test_inv14_es_general():
    """`SPEC-26` v3: si `Deterioro` se queda, su invariante tambien."""
    for genero in ("terror", "aventura", "romance"):
        assert registro.aplica("INV-14", genero)
        assert registro.aplica("INV-13", genero) and registro.aplica("INV-15", genero)


def test_las_de_la_puerta_de_publicacion_son_de_obra_y_bloqueantes():
    """`SPEC-30` v4, numeradas en `PLAN-30`: `INV-28` (Lean devuelve `0`) e `INV-29`
    (ningun capitulo publicado esta rendido). Las dos son reglas: Lean es
    determinista, aunque sea un demostrador y no una consulta."""
    for i in ("INV-28", "INV-29"):
        inv = registro.TODAS[i]
        assert inv.nivel is enums.NivelDeEvaluacion.OBRA
        assert inv.severidad is enums.Severidad.BLOQUEANTE
        assert inv.tipo is enums.TipoDeVerificador.REGLA
