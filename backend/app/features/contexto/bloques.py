"""Los siete bloques del contexto, en el orden de `SPEC-01` 2.4.

La columna que importa es `forma_reducida`. Recortar dejo de ser **elegir que
se pierde** y paso a ser **elegir cuanto se conserva de cada cosa**: entre
"completo" y "ausente" hay "reducido", y un bloque reducido sigue aportando.

`nivel` esta para trazar el origen, **no para recorrerlo**. El nivel
`Recuperado` de `CLAUDE.md` se parte en dos bloques que caen a distinto lado de
la frontera de `RF-26`: las fichas se recortan pronto y el registro de
conocimiento no, porque sin el `INV-03` no es peor, es imposible.

LO QUE NO SE REDUCE NI SE ELIMINA
----------------------------------
Lo que lee una invariante `bloqueante` de nivel escena, y **si eso obliga a
mover un dato de bloque, se mueve**. Proteger la reduccion y olvidar la
eliminacion seria proteger lo menos.

Por eso el **grafo de accesos** vive en el bloque 4 y no en el 2, aunque venga
de la misma recuperacion que las fichas: `INV-02` lo lee y el 2 se elimina.
Declarar el 2 no eliminable habria sido proteger un bloque entero por culpa de
un campo, y el 2 existe para adelgazar.

Y por eso la reduccion del bloque 4 conserva **cualquier hecho que el delta
referencie**, sea cual sea su durabilidad: `INV-03` necesita su
`escena_de_establecimiento` para comprobar que revelar no precede a establecer,
y un hecho efimero tiene esa fecha igual que uno permanente. La durabilidad
decide que se puede recortar **del estado**, no que necesita una puerta.
"""

from dataclasses import dataclass
from enum import Enum


class Clase(str, Enum):
    REDUCCION = "reduccion"
    ELIMINACION = "eliminacion"


@dataclass(frozen=True)
class Bloque:
    nombre: str
    nivel: str
    forma_reducida: str | None
    eliminable: bool
    lee_una_bloqueante: str | None = None


BLOQUES = [
    Bloque("condensaciones", "Resumenes",
           "solo las de capitulo; se van las de parte", eliminable=True),
    Bloque("fichas_y_setups", "Recuperado",
           "solo las entidades presentes en la escena", eliminable=True),
    Bloque("escena_anterior", "Local",
           "la escena anterior baja a su Resumen", eliminable=True),
    Bloque("estado_y_conocimiento", "Estado actual + Recuperado",
           "el registro entero, el grafo de accesos entero, entidades_vivas, "
           "ubicaciones, los hechos permanentes y cualquier hecho que el delta "
           "referencie", eliminable=False,
           lee_una_bloqueante="INV-02 e INV-03"),
    Bloque("problemas_del_intento_anterior", "Local",
           "solo los de severidad bloqueante y mayor", eliminable=False),
    Bloque("reserva_de_salida", "Salida", None, eliminable=False),
    Bloque("inmutable", "Inmutable", None, eliminable=False),
]

POR_NOMBRE = {b.nombre: b for b in BLOQUES}

# Cuanto conserva una forma reducida, como fraccion del bloque completo. No
# esta medido: es el mismo caso que los topes de `commons/config.py`.
# Caduca con: backend/app/features/orquestacion/
FRACCION_REDUCIDA = 0.4
