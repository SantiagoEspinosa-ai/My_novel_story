"""Cuando una escena no sale limpia y se acaban los intentos.

QUE NO SE RINDE NUNCA, Y POR QUE NO ES NEGOCIABLE
---------------------------------------------------
Una invariante `bloqueante` **abierta**. `docs/architecture.md`: *"el delta de
una escena rendida entra al canon igual que el de una limpia, y una falsedad en
el canon la heredan todas las escenas siguientes"*. Rendirse ante `INV-03`
meteria un hecho falso en el registro de conocimiento y **las cincuenta escenas
siguientes se generarian encima**. La salida de ahi es humana.

Lo que si se rinde es `mayor` y `menor`: molestan, no corrompen.

COMO SE ELIGE EL MENOS MALO SIN INVENTAR UN PESO
--------------------------------------------------
`docs/definitions.md` deja los pesos por severidad como decision abierta —*"no
se fijan aqui"*, salen de medir sobre esta implementacion— y este modulo **no
los adelanta**. Ordena por cuantos hallazgos hay de cada severidad, empezando
por la mas grave: entre dos intentos gana el que tenga menos `bloqueante`; a
igualdad, menos `mayor`; a igualdad, menos `menor`.

Ese orden es el que daria **cualquier** asignacion de pesos crecientes, asi que
no decide nada que la decision abierta tenga que decidir despues. Cuando los
pesos se fijen con datos reales, sustituiran a esto y podran discrepar en casos
que hoy empatan; mientras tanto, esto no miente sobre lo que sabe.

Y la comparacion es **local**: solo vale entre intentos de la misma escena.
Dos obras distintas no son comparables porque el muestreo del modelo no se
puede fijar, y esa advertencia costo descubrirla en la otra rama.
"""

from app.commons.dominio.enumeraciones import Severidad

# De la mas grave a la menos. El orden es el de la escala, no una preferencia
# de este modulo.
ESCALA = (Severidad.BLOQUEANTE, Severidad.MAYOR, Severidad.MENOR)


def _es_sin_veredicto(h) -> bool:
    return str(getattr(h, "estado", "")) == "sin_veredicto"


def puede_rendirse(hallazgos) -> bool:
    """`False` si queda una `bloqueante` **confirmada** abierta.

    Un `sin_veredicto` no lo impide: no consta que nada se haya roto
    (`SPEC-18` C-3). Lo que hace es impedir cerrar el capitulo, y eso se
    decide una puerta mas arriba.
    """
    return not any(str(h.severidad) == "bloqueante" and not _es_sin_veredicto(h)
                   for h in hallazgos)


def _perfil(hallazgos):
    """Cuantos hay de cada severidad, de la mas grave a la menos.

    Un `sin_veredicto` cuenta en el tramo **mas grave de la escala y no por
    encima**: pesa lo maximo porque no auditarse no puede salir barato, pero no
    es *peor* que un fallo confirmado. Uno dice que algo esta mal; el otro, que
    no sabemos. Si el mudo ganara siempre, un intento con un juez caido seria
    automaticamente peor que otro con tres fallos reales, y eso no es cierto.
    """
    cuenta = {s: 0 for s in ESCALA}
    for h in hallazgos:
        if _es_sin_veredicto(h):
            cuenta[ESCALA[0]] += 1
            continue
        for s in ESCALA:
            if str(h.severidad) == str(s):
                cuenta[s] += 1
                break
    return tuple(cuenta[s] for s in ESCALA)


def menos_malo(intentos):
    """De `[(version, hallazgos)]`, la version que menos duele. `None` si no hay.

    El empate lo gana el **primero**, que en la practica es el intento mas
    temprano: dos intentos igual de malos no pueden dar resultados distintos
    segun el orden en que se lean, o la rendicion dejaria de ser reproducible.
    """
    if not intentos:
        return None
    mejor = min(enumerate(intentos), key=lambda par: (_perfil(par[1][1]), par[0]))
    return mejor[1][0]


def queda_presupuesto(gastadas: int, tope: int) -> bool:
    """El freno de mano de la obra entera (`TOPE_DELEGACIONES_OBRA`).

    **Acota el gasto, no el error.** Una obra que se detiene aqui no esta mal
    escrita: esta costando mas de lo previsto, y eso lo decide una persona y no
    un bucle. Por eso la parada dice cuantas llevaba y no se reintenta sola.
    """
    return gastadas < tope


def delegaciones_de(costes) -> int:
    """Todas las delegaciones, no solo las del Escritor.

    El Juez y el Resumidor tambien se pagan, y en `E5b` el Juez costo mas por
    token que el Escritor. Contar solo al Escritor daria un tope que se pasa
    por tres sin que nadie lo note.
    """
    return sum(c.get("delegaciones", 0) for c in costes)
