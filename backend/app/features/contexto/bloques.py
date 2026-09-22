"""Los siete bloques del contexto, en el orden de `SPEC-01` 2.4.

La columna que importa es `forma_reducida`. Recortar dejo de ser **elegir que
se pierde** y paso a ser **elegir cuanto se conserva de cada cosa**: entre
"completo" y "ausente" hay "reducido", y un bloque reducido sigue aportando.

`nivel` esta para trazar el origen, **no para recorrerlo**. El nivel
`Recuperado` de `CLAUDE.md` se parte en dos bloques que caen a distinto lado de
la frontera de `RF-26`: las fichas se recortan pronto y el registro de
conocimiento no, porque sin el `INV-03` no es peor, es imposible.

LO QUE NINGUNA FORMA REDUCIDA PUEDE LLEVARSE
---------------------------------------------
Lo que lee una invariante `bloqueante` de nivel escena. Si lo hace, la puerta
sigue en pie y ya no puede decidir. Ata a dos: `INV-02` -que lee
`entidades_vivas`, `ubicaciones` y `Lugar.accesos_y_salidas`- e `INV-03` -que
lee el registro de conocimiento-. Las otras tres bloqueantes de escena miran la
propia escena, su borrador o el delta.
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
           "el grafo de accesos entre lugares y nada mas", eliminable=True,
           lee_una_bloqueante="INV-02 lee Lugar.accesos_y_salidas"),
    Bloque("escena_anterior", "Local",
           "la escena anterior baja a su Resumen", eliminable=True),
    Bloque("estado_y_conocimiento", "Estado actual + Recuperado",
           "el registro de conocimiento entero, entidades_vivas, ubicaciones "
           "y solo los hechos permanentes", eliminable=False,
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
