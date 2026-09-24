"""`PLAN-28` E1: los esquemas de las tres tools de lectura de la story bible.

`SPEC-28` `RF-02`: cada tool tiene un esquema de entrada y otro de salida, y replican
las clases de `docs/definitions.md`. `RF-05`: ninguna devuelve el texto de una escena.
`RF-06`: la obra no es argumento de ninguna.
"""

import pytest
from pydantic import BaseModel, ValidationError

from app.commons.dominio import story_bible as sb

ENTRADAS = (sb.EntradaHechos, sb.EntradaFicha, sb.EntradaCronologia)
SALIDAS = (sb.SalidaHechos, sb.SalidaFicha, sb.SalidaCronologia)


def test_pedir_otra_obra_por_argumento_se_rechaza():
    """`D-4`: la obra la fija el harness en el servidor, nunca el agente."""
    for entrada, datos in ((sb.EntradaHechos, {}), (sb.EntradaFicha, {"id": "per-a"}),
                           (sb.EntradaCronologia, {})):
        with pytest.raises(ValidationError):
            entrada.model_validate(dict(datos, obra="otra-obra"))


def _campos(modelo, vistos=None):
    vistos = vistos if vistos is not None else set()
    if modelo in vistos:
        return set()
    vistos.add(modelo)
    nombres = set(modelo.model_fields)
    for f in modelo.model_fields.values():
        for tipo in getattr(f.annotation, "__args__", ()) + (f.annotation,):
            if isinstance(tipo, type) and issubclass(tipo, BaseModel):
                nombres |= _campos(tipo, vistos)
    return nombres


def test_ningun_esquema_de_salida_tiene_campo_de_texto_de_escena():
    """`RF-05`: una tool es otra forma de mandar texto al modelo, y el texto de las
    escenas no se manda (`CLAUDE.md`)."""
    for salida in SALIDAS:
        assert not _campos(salida) & {"texto", "borrador", "prosa"}, salida.__name__


def test_la_ficha_de_personaje_tiene_los_campos_de_rf43():
    assert set(sb.FichaDePersonaje.model_fields) == {
        "id", "nombre_canonico", "alias", "rol_dramatico", "estado_vital"}
    assert set(sb.FichaDeLugar.model_fields) == {"id", "nombre", "atmosfera"}


def test_una_ficha_es_de_personaje_o_de_lugar_nunca_de_los_dos():
    with pytest.raises(ValidationError):
        sb.SalidaFicha.model_validate({})
    with pytest.raises(ValidationError):
        sb.SalidaFicha.model_validate({
            "personaje": {"id": "p", "nombre_canonico": "P", "estado_vital": "vivo"},
            "lugar": {"id": "l", "nombre": "L"}})


def test_un_rol_dramatico_fuera_del_vocabulario_es_error():
    with pytest.raises(ValidationError):
        sb.FichaDePersonaje.model_validate({"id": "p", "nombre_canonico": "P",
                                            "estado_vital": "vivo", "rol_dramatico": "heroe"})


def test_un_tipo_de_uso_fuera_del_vocabulario_es_error():
    with pytest.raises(ValidationError):
        sb.UsoDeHecho.model_validate({"capitulo": "cap-01", "tipo": "aparece"})
