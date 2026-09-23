"""Un doble del modelo con la misma forma que lo real.

    "Un doble de prueba tiene la misma forma que lo real. Si el modelo devuelve
     texto y delta en la misma respuesta, el doble tambien."

Es la tercera regla de pruebas de `Docs/architecture.md`, y la otra rama la
aprendio a golpes: un doble demasiado limpio no caza lo que el real hace mal.
Por eso este doble **puede portarse mal a peticion**: devolver un delta fuera de
esquema, quedarse mudo, o quedarse corto de palabras. Si solo supiera portarse
bien, el bucle pasaria contra el y fallaria contra el proveedor.

NO HABLA CON NADIE
------------------
No importa ningun cliente HTTP y no lee credenciales. Es el unico modelo que
existe hasta `E3`, y existe para que un bucle roto se descubra gratis.
"""

from dataclasses import dataclass


@dataclass
class Guion:
    """Que va a hacer el doble en cada llamada, en orden.

    Cada elemento es una de estas cadenas:

        "bien"          texto y delta correctos
        "sin_delta"     texto y nada mas: fallo de contrato
        "delta_roto"    delta con un eje que no existe: fallo de contrato
        "mudo"          respuesta vacia
        "corto"         texto de 944 palabras, el caso real de la otra rama
        "timeout"       levanta un fallo de transporte
        "vetada"        texto correcto con la palabra vetada «zoquete»
    """

    pasos: list

    def __post_init__(self):
        self._i = 0


class FalloDeTransporte(Exception):
    pass


# El POV que los fixtures planifican. El doble lo respeta salvo que el
# guion pida `pov_cambiado`.
POV = "per-marta"

DELTA_OK = {"cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
            "movimientos": [], "revelaciones": []}


class DobleDelModelo:
    """Misma firma que el cliente real: `llamar(prompt) -> dict`."""

    nombre = "doble"

    def __init__(self, guion=None):
        self.guion = guion or Guion(["bien"])
        self.llamadas = []

    def llamar(self, prompt: str) -> dict:
        paso = self.guion.pasos[min(self.guion._i, len(self.guion.pasos) - 1)]
        self.guion._i += 1
        self.llamadas.append(prompt)

        if paso == "timeout":
            raise FalloDeTransporte("el proveedor no respondio a tiempo")
        if paso == "mudo":
            return {"texto": "", "usage": {"total_tokens": 12}}
        if paso == "sin_delta":
            return {"texto": "La puerta estaba abierta.", "pov_usado": POV,
                    "usage": {"total_tokens": 40}}
        if paso == "delta_roto":
            return {"texto": "La puerta estaba abierta.", "pov_usado": POV,
                    "delta": {"cambio_de_valor": {"eje": "dinero", "signo": "negativo"}},
                    "usage": {"total_tokens": 45}}
        if paso == "pov_cambiado":
            # `F-34` en real: el modelo escribio la escena sobre otro
            # personaje del planificado. Sin este paso, `INV-04` no tiene
            # ningun caso que la ejercite contra el bucle.
            return {"texto": " ".join(["palabra"] * 1500), "pov_usado": "per-ana",
                    "delta": DELTA_OK, "usage": {"total_tokens": 2100}}
        if paso == "actua_sin_saber":
            # El caso de `F-24`, que el modelo real produjo solo: un personaje
            # obra sirviendose de algo que no consta que conozca. Sin este paso
            # el doble no puede ejercitar `INV-03`, y una invariante que nunca
            # falla en las pruebas no esta verificada, solo declarada.
            return {"texto": " ".join(["palabra"] * 1500), "pov_usado": POV,
                    "delta": dict(DELTA_OK, acciones=[
                        {"personaje": "per-ana", "hecho": "hec-llave"}]),
                    "usage": {"total_tokens": 2100}}
        if paso == "vetada":
            # `SPEC-25`: el texto trae una palabra de la lista de prueba. Sin
            # este paso `INV-21` no tendria ningun caso que la ejercite contra
            # el bucle, y una invariante que nunca falla no esta verificada.
            return {"texto": " ".join(["palabra"] * 1499 + ["zoquete"]),
                    "pov_usado": POV, "delta": DELTA_OK,
                    "usage": {"total_tokens": 2100}}
        if paso == "corto":
            return {"texto": " ".join(["palabra"] * 944), "pov_usado": POV,
                    "delta": DELTA_OK, "usage": {"total_tokens": 1300}}
        return {"texto": " ".join(["palabra"] * 1500), "pov_usado": POV,
                "delta": DELTA_OK, "usage": {"total_tokens": 2100}}
