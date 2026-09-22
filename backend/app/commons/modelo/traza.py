"""La traza de una llamada al modelo.

`T-1` y `T-2` de `SPEC-01` piden traza de cada llamada, incluidas las que
fallan. `SPEC-08` y `SPEC-11` dicen que registra.

POR QUE LOS TOKENS VAN EN CAMPOS SEPARADOS
-------------------------------------------
`VER-41` reconcilia lo que registra la traza contra lo que declara el modelo, y
es **la segunda fuente independiente** que exige la Regla 3 de
`Docs/verification.md`. Si los numeros salieran del mismo sitio, `VER-41`
compararia un numero consigo mismo: pasaria siempre y seria un eco.

Son **tres numeros, no dos** (`SPEC-12` C-3):

    tokens_para_recortar  el ensamblador, en cada vuelta del bucle. Estimacion
                          conservadora: decide "me paso o no", no "por cuanto".
    tokens_reservados     el control de presupuesto, una vez, antes de salir.
    tokens_estimados      el contador propio, al registrar la traza.
    tokens_declarados     el `usage` del proveedor, COPIADO, nunca calculado.

Mezclar dos cualesquiera rompe la Regla 3, y es justo lo que alguien unifica
al refactorizar creyendo que simplifica.

POR QUE SE GUARDAN IDS Y NO TEXTO
----------------------------------
El contexto puede acercarse a 80.000 tokens y se reconstruye desde el estado en
`t`. Lo que **no** se reconstruye es **cual** se recupero: el indice vectorial
crece al consolidar y los empates de una consulta KNN no tienen orden definido.
Por eso se guardan los identificadores, con su `version_en_t`, que ocupan nada.

El `prompt_hash` **detecta, no reconstruye**: sirve para saber si una
reconstruccion es fiel, no para recuperar lo que se mando. Vive tambien aqui y
no solo en `Borrador` porque una llamada fallida no produce ningun `Borrador`, y
es justo la que hay que diagnosticar.
"""

from dataclasses import dataclass, field

CLASES_DE_RECORTE = ("reduccion", "eliminacion")


@dataclass(frozen=True)
class Recorte:
    bloque: str
    clase: str


@dataclass
class Traza:
    agente: str
    escena: str
    trabajo: str
    modelo: str | None = None
    prompt_hash: str | None = None
    fichas: list = field(default_factory=list)
    presagios: list = field(default_factory=list)
    resumenes: list = field(default_factory=list)
    recortes: list = field(default_factory=list)
    tokens_para_recortar: int | None = None
    tokens_reservados: int | None = None
    tokens_estimados: int | None = None
    tokens_declarados: int | None = None
    resultado: str | None = None
    clase_de_fallo: str | None = None
    salida_fallida: str | None = None


def nueva(agente, escena, trabajo, modelo=None):
    return Traza(agente=agente, escena=escena, trabajo=trabajo, modelo=modelo)


def registrar_entrada(t, fichas=None, presagios=None, resumenes=None, prompt_hash=None):
    """Los identificadores que entraron, no su texto."""
    t.fichas = list(fichas or [])
    t.presagios = list(presagios or [])
    t.resumenes = list(resumenes or [])
    t.prompt_hash = prompt_hash


def registrar_recorte(t, bloque, clase):
    if clase not in CLASES_DE_RECORTE:
        raise ValueError(
            "clase de recorte desconocida: {0!r}. Desde `SPEC-12` reducir y "
            "eliminar no son lo mismo, y la serie por obra solo sirve si se "
            "distinguen".format(clase)
        )
    t.recortes.append(Recorte(bloque=bloque, clase=clase))


def registrar_respuesta(t, respuesta):
    """Copia el `usage` del proveedor. **No lo calcula.**

    Si no viene, queda **ausente**, no en cero: un cero se lee como un dato y un
    hueco no (`RF-25`).
    """
    t.resultado = "ok"
    usage = (respuesta or {}).get("usage")
    t.tokens_declarados = usage.get("total_tokens") if usage else None


def registrar_fallo(t, clase, salida=None):
    """`T-2`: una llamada que falla tambien deja traza.

    La salida entera solo en el fallo **de contrato**: es pequena, no se
    reconstruye, y sin verla no se puede diagnosticar un delta fuera de esquema.
    """
    t.resultado = "fallo"
    t.clase_de_fallo = clase
    t.salida_fallida = salida if clase == "contrato" else None
