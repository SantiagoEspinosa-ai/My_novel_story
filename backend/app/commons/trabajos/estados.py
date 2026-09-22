"""Los estados de un trabajo.

NO SON DOMINIO, Y POR ESO ESTAN AQUI
------------------------------------
`VER-15` y `D-3` dicen que los `Enum` de los vocabularios controlados **del
dominio** viven solo en `commons/dominio/`. Este no lo es: la tabla de trabajos
no existiria si la novela se escribiera a mano, asi que es infraestructura y
vive con su infraestructura. `Docs/architecture.md` los declara, no
`Docs/definitions.md`, y su seccion de vocabularios avisa de que hay uno fuera.

Siguen las mismas reglas de nombres -ASCII, `snake_case`- porque es el mismo
codigo leyendo el mismo tipo de valor, y dos convenciones para lo mismo es como
`juez LLM` acabo divergiendo de `juez_llm`.

`FALLIDO` Y `ABANDONADO` NO SON EL MISMO HECHO
----------------------------------------------
Uno significa que **se sabe que paso**: un fallo de contrato, o el tope de
reintentos agotado. El otro, que **no se sabe si llego a pasar**. La
consecuencia practica esta en el tope: un abandonado no cuenta contra el,
porque no es un intento que fallo sino uno cuyo resultado se desconoce. Con un
campo en vez de un estado, una interfaz que solo mire el estado los confunde y
alguien lo relanza a mano creyendo que fallo, que es pagar dos veces por otra
puerta.
"""

from enum import Enum


class EstadoDeTrabajo(str, Enum):
    EN_COLA = "en_cola"
    ESPERANDO_PRESUPUESTO = "esperando_presupuesto"
    EN_CURSO = "en_curso"
    TERMINADO = "terminado"
    FALLIDO = "fallido"
    ABANDONADO = "abandonado"
    DETENIDO_POR_PRESUPUESTO = "detenido_por_presupuesto"

    def __str__(self):
        return self.value
