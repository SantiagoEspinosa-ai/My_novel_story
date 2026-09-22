"""Modelos Pydantic del dominio: la frontera de validacion.

`CLAUDE.md` lo dice en dos frases que gobiernan este fichero:

    "Los modelos Pydantic son la frontera de validacion y replican las clases
     de `Docs/definitions.md`. Un campo que no esta definido alli no entra en
     un esquema."
    "Un valor fuera de la enumeracion es un error de validacion, no un aviso."

La segunda es la que hace que la API devuelva 422 en vez de seguir adelante
con un valor que nadie reconoce. Aqui se consigue sin escribir nada: un campo
tipado como `Severidad` rechaza cualquier cadena que no sea uno de sus tres
valores, y Pydantic levanta `ValidationError`.

QUE HAY AQUI Y QUE NO
---------------------
Solo las clases que el paso A1 necesita para que la frontera exista y se pueda
probar. El resto de las 43 entran con la feature que las usa: un esquema sin
nadie que lo llame es codigo sin prueba que haya fallado antes.
"""

from pydantic import BaseModel, ConfigDict, Field

from app.commons.dominio import enumeraciones as enums


class _DelDominio(BaseModel):
    """Base de los modelos del dominio.

    `extra="forbid"` no es una manía: es "un campo que no esta definido en
    `Docs/definitions.md` no entra en un esquema" hecho cumplir. Sin esto, un
    campo inventado entraria en silencio y el esquema dejaria de replicar la
    ficha sin que nada fallara.
    """

    model_config = ConfigDict(extra="forbid", frozen=True, use_enum_values=False)


class Hallazgo(_DelDominio):
    """Defecto detectado, con localizacion.

    `verificador` es obligatorio y `VER-12` comprueba que lo sea de verdad:
    con `INV-13` comprobada dos veces -incremental en el Verificador, barrido
    en el Auditor- hace falta poder distinguir cual de los dos lo levanto, o el
    recuento por invariante mezcla dos cosas.

    Un hallazgo con `estado = sin_veredicto` significa que el verificador no
    llego a emitir juicio. Sus campos obligatorios **no se relajan**:
    `descripcion` se rellena con que se intento comprobar y donde. Lo que falta
    es el juicio, no el contexto.
    """

    invariante: str = Field(pattern=r"^INV-\d{2}$")
    verificador: str = Field(min_length=1)
    escena: str = Field(min_length=1)
    severidad: enums.Severidad
    estado: enums.EstadoDeHallazgo
    descripcion: str = Field(min_length=1)
