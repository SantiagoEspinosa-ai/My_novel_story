"""Comprueba que el modelo no cambie dentro de una obra.

POR QUE DEJO DE SER OPCIONAL
-----------------------------
`SPEC-11` C-3 fijo que el modelo es fijo dentro de una obra, porque desde
`SPEC-10` la comparabilidad entre puntuaciones decide que borrador se queda en
`Escena.borrador_aceptado`. Si el modelo cambia a mitad, dos puntuaciones dejan
de significar lo mismo y la eleccion se vuelve arbitraria.

Hasta aqui eso era una regla que se cumplia sola, porque nadie iba a cambiarla
a proposito. **Ya no.** Un modelo puede **enrutar a otro por sus propias
salvaguardas**, asi que el cambio puede ocurrir dentro de una obra sin que nadie
lo pida y sin que nadie se entere. Una regla que depende de que nadie la
incumpla adrede no vale cuando el incumplimiento puede ser automatico.

Por eso la comprobacion no mira la configuracion -que dira siempre lo que se
pidio- sino **la traza de cada delegacion**, que registra lo que se uso.

QUE NO VE
---------
Ve lo que la traza registra. Si el registro del modelo se rellena con lo que se
**pidio** en vez de con lo que **respondio**, esta comprobacion estara en verde
mientras el enrutado ocurre: seria un eco, y es la Regla 3 otra vez. Queda
declarado en `VER-62` y no se tapa aqui.
"""

from dataclasses import dataclass


# El identificador declarado es corto -"fable"- y el reportado es canonico
# -"claude-fable-5-1"-. **El canonico manda**: es el que sale de la respuesta y
# el unico que no depende de como se escribio la configuracion.
def canonico(modelos):
    """El conjunto canonico de una delegacion, ordenado y sin repetidos."""
    return tuple(sorted(set(modelos or ())))


@dataclass(frozen=True)
class Discrepancia:
    trabajo: str
    esperado: tuple
    encontrado: tuple

    def __str__(self):
        return ("el trabajo {0} uso {1} y el resto de la obra {2}"
                .format(self.trabajo, list(self.encontrado), list(self.esperado)))


class ModeloCambiado(Exception):
    def __init__(self, discrepancias):
        self.discrepancias = discrepancias
        super().__init__(
            "el modelo cambio dentro de la obra en {0} delegaciones: {1}. "
            "Dos puntuaciones de modelos distintos no son comparables, y la "
            "eleccion del mejor borrador se vuelve arbitraria".format(
                len(discrepancias), "; ".join(str(d) for d in discrepancias))
        )


def comprobar(trazas):
    """El conjunto de modelos es estable entre delegaciones de la misma obra.

    **No se compara contra lo declarado**: el declarado es corto y el reportado
    canonico, asi que nunca coincidirian. Se compara cada delegacion contra la
    primera que reporto algo, que es la que fija el conjunto de la obra.

    Una traza **sin modelos registrados** no cuenta como discrepancia pero
    tampoco como conformidad: se devuelve aparte, porque decir que todo cuadra
    cuando media muestra esta vacia es lo que `RF-25` prohibe.
    """
    discrepancias, sin_registrar, referencia = [], [], None
    for t in trazas:
        usados = canonico(getattr(t, "modelos", None))
        trabajo = getattr(t, "trabajo", "sin-id")
        if not usados:
            sin_registrar.append(trabajo)
            continue
        if referencia is None:
            referencia = usados
        elif usados != referencia:
            discrepancias.append(Discrepancia(
                trabajo=trabajo, esperado=referencia, encontrado=usados))
    return discrepancias, sin_registrar


def exigir(trazas):
    """Levanta si el conjunto cambio. Para usarlo como puerta, no como informe."""
    discrepancias, _ = comprobar(trazas)
    if discrepancias:
        raise ModeloCambiado(discrepancias)
    return True
