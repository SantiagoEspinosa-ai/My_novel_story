"""Lo que costo un agente que no pasa por las trazas del ciclo (`PLAN-31` E5).

Vivia en `novela_regalo.py` sin prueba. Lo usan el Planificador y el Revisor, el juicio
de obra y la puerta de publicacion, y la entrevista de `evaluar.py`: todo lo que se paga
fuera de `ciclo._delegar`, que es lo unico que deja traza.

LO AUSENTE NO SUMA CERO
-----------------------
Una delegacion sin `coste_usd` se cuenta en `sin_coste` y no suma: un cero se lee como un
dato y un hueco no. Con alguna sin coste, `usd` es un suelo; sin ninguna con coste,
`medido` es `None`: no se sabe, que no es lo mismo que gratis.

Una respuesta ilegible **se pago igual** (`PLAN-29` E1): su coste viaja en la excepcion y
se cuenta. Un fallo de transporte no trae sobre, asi que cuenta como sin coste.
"""

_DE_LA_SESION = ("entorno", "herramientas", "reglas")


class Contador:
    def __init__(self, sesion):
        object.__setattr__(self, "sesion", sesion)
        object.__setattr__(self, "usd", 0.0)
        object.__setattr__(self, "delegaciones", 0)
        object.__setattr__(self, "sin_coste", 0)

    def __getattr__(self, nombre):
        return getattr(self.sesion, nombre)

    def __setattr__(self, nombre, valor):
        # Lo que se configura sobre el agente -sus tools, su entorno- es de la sesion.
        if nombre in _DE_LA_SESION:
            setattr(self.sesion, nombre, valor)
        else:
            object.__setattr__(self, nombre, valor)

    @property
    def nombre(self):
        return self.sesion.nombre

    @property
    def medido(self):
        """El total, o `None` si ninguna delegacion trajo coste."""
        return self.usd if self.delegaciones > self.sin_coste else None

    def _sumar(self, medidas):
        object.__setattr__(self, "delegaciones", self.delegaciones + 1)
        usd = (medidas or {}).get("coste_usd")
        if usd is None:
            object.__setattr__(self, "sin_coste", self.sin_coste + 1)
        else:
            object.__setattr__(self, "usd", self.usd + usd)

    def llamar(self, prompt):
        try:
            r = self.sesion.llamar(prompt)
        except Exception as e:
            self._sumar(getattr(e, "medidas", None))
            raise
        self._sumar((r or {}).get("medidas") if isinstance(r, dict) else None)
        return r

    def resumen(self) -> dict:
        return {"usd": self.usd, "delegaciones": self.delegaciones,
                "sin_coste": self.sin_coste}
