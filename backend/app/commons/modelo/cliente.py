"""Cliente del modelo: quien decide reintentar y quien no.

`O-3` de `SPEC-01` y `docs/architecture.md`: se reintentan los fallos **de
transporte** -timeout, corte, limite de tasa- porque se resuelven repitiendo.
Los **de contrato** -delta fuera de esquema, respuesta sin texto, valor fuera de
enumeracion- no: repetirlos repite el error y gasta presupuesto en volver a
fallar igual. Esos se marcan fallidos y los ve una persona.

Se reintenta **el trabajo entero desde el ensamblado del contexto**, no solo la
llamada: entre un intento y el siguiente el estado del mundo pudo cambiar, y
reutilizar el contexto viejo es generar contra un mundo que ya no existe.
"""

from app.commons.config import TOPE_REINTENTOS_TRANSPORTE

CLASES_DE_FALLO = ("transporte", "contrato")


class FalloDeTransporte(Exception):
    """El proceso no arranco, no respondio o murio. Por `O-3` **si** se reintenta.

    `F-74`: vive aqui, una sola vez. Habia una en `doble.py` y otra en `proveedor.py`,
    y el bucle capturaba la del doble: un timeout real no lo capturaba nadie."""


def se_reintenta(clase_de_fallo: str) -> bool:
    if clase_de_fallo not in CLASES_DE_FALLO:
        raise ValueError("clase de fallo desconocida: {0!r}".format(clase_de_fallo))
    return clase_de_fallo == "transporte"


def quedan_intentos(intentos_consumidos: int) -> bool:
    return intentos_consumidos < TOPE_REINTENTOS_TRANSPORTE


class ConReintentos:
    """`F-72`: reintenta la llamada de un agente que **no monta contexto** -Planificador,
    Revisor, Editor, Resumidor-, hasta `tope` veces tras la primera. Su entrada es texto
    ya fijado, asi que repetir la llamada es repetir el trabajo entero. El Escritor no
    pasa por aqui: el suyo se reintenta desde el ciclo, con el contexto montado de nuevo.
    Pasado el tope, el fallo sube: quien lanzo la generacion lo informa."""

    def __init__(self, agente, tope):
        object.__setattr__(self, "agente", agente)
        object.__setattr__(self, "tope", tope)

    def __getattr__(self, nombre):
        return getattr(self.agente, nombre)

    def __setattr__(self, nombre, valor):
        # Lo que se configura sobre el agente -sus tools, su entorno- es del agente.
        setattr(self.agente, nombre, valor)

    def llamar(self, prompt):
        for intento in range(self.tope + 1):
            try:
                return self.agente.llamar(prompt)
            except FalloDeTransporte:
                if intento == self.tope:
                    raise
