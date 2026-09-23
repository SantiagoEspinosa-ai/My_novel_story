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


@dataclass(frozen=True)
class Discrepancia:
    trabajo: str
    esperado: str
    encontrado: str

    def __str__(self):
        return ("el trabajo {0} uso `{1}` y la obra declaro `{2}`"
                .format(self.trabajo, self.encontrado, self.esperado))


class ModeloCambiado(Exception):
    def __init__(self, discrepancias):
        self.discrepancias = discrepancias
        super().__init__(
            "el modelo cambio dentro de la obra en {0} delegaciones: {1}. "
            "Dos puntuaciones de modelos distintos no son comparables, y la "
            "eleccion del mejor borrador se vuelve arbitraria".format(
                len(discrepancias), "; ".join(str(d) for d in discrepancias))
        )


def comprobar(declarado: str, trazas) -> list:
    """Devuelve las discrepancias. Lista vacia es que no hubo ninguna.

    Una traza **sin modelo registrado** no cuenta como discrepancia pero
    tampoco como conformidad: se devuelve aparte, porque decir que todo cuadra
    cuando media muestra esta vacia es exactamente lo que `RF-25` prohibe.
    """
    discrepancias, sin_registrar = [], []
    for t in trazas:
        usado = getattr(t, "modelo", None)
        if usado is None:
            sin_registrar.append(getattr(t, "trabajo", "sin-id"))
            continue
        if usado != declarado:
            discrepancias.append(Discrepancia(
                trabajo=getattr(t, "trabajo", "sin-id"),
                esperado=declarado, encontrado=usado))
    return discrepancias, sin_registrar


def exigir(declarado: str, trazas):
    """Levanta si hubo cambio. Para usarlo como puerta y no como informe."""
    discrepancias, _ = comprobar(declarado, trazas)
    if discrepancias:
        raise ModeloCambiado(discrepancias)
    return True
