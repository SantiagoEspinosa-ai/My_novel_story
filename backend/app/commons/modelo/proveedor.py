"""El cliente real del modelo. **Nada de este modulo se ejecuta en las pruebas.**

QUE HACE Y QUE NO
-----------------
Traduce entre el harness y un proveedor HTTP: manda un prompt, recibe texto,
delta y `usage`. Tiene **la misma firma que el doble** -`llamar(prompt) -> dict`-
para que el bucle de `features/orquestacion/bucle.py` no sepa cual de los dos
tiene delante. Esa simetria es lo que hace que `E2` valga: el bucle probado
contra el doble es el mismo bucle que correra contra el proveedor.

LAS CREDENCIALES
----------------
Se leen del **entorno** y de ningun otro sitio. No hay fichero de ejemplo, no
hay valor por defecto y no se escriben nunca:

  - no van al repositorio ni a `config.json`;
  - no van a la traza, que registra **que modelo** se uso y no con que clave;
  - no van al log, ni siquiera truncadas;
  - no van al mensaje de una excepcion.

Si falta la variable, el modulo falla al construirse con un mensaje que dice
**que variable falta**, nunca que valor tenia. Un fichero de configuracion
versionado con una clave dentro es el modo de fallo mas caro y mas frecuente
que hay, y no se cataloga como modo de fallo: se impide.

POR QUE EL MODELO SE FIJA AL CONSTRUIR
---------------------------------------
`SPEC-11` C-3: el modelo del Juez es **fijo dentro de una obra**, porque desde
`SPEC-10` la comparabilidad entre puntuaciones decide que borrador se queda en
`Escena.borrador_aceptado`. Si el modelo cambiara a mitad, dos puntuaciones
dejarian de significar lo mismo y la eleccion seria arbitraria sin que nada
avisara. Por eso se pasa en el constructor y no en cada llamada, y por eso la
traza registra cual se uso: sin ese registro la regla no se puede comprobar
despues.
"""

import json
import os

VARIABLES = {
    "clave": "HARNESS_MODELO_API_KEY",
    "base_url": "HARNESS_MODELO_BASE_URL",
    "modelo_escritor": "HARNESS_MODELO_ESCRITOR",
    "modelo_juez": "HARNESS_MODELO_JUEZ",
}


class FaltaCredencial(RuntimeError):
    pass


class FalloDeTransporte(Exception):
    """Timeout, corte, limite de tasa. Por `O-3` **si** se reintenta."""


def _del_entorno(nombre, obligatoria=True):
    valor = os.environ.get(nombre)
    if obligatoria and not valor:
        raise FaltaCredencial(
            "falta la variable de entorno {0}. El harness no lee credenciales "
            "de ningun fichero: ponla en la sesion antes de arrancar".format(nombre)
        )
    return valor


class ClienteReal:
    """Misma firma que `DobleDelModelo`. El bucle no distingue."""

    def __init__(self, modelo=None, transporte=None):
        self._clave = _del_entorno(VARIABLES["clave"])
        self.base_url = _del_entorno(VARIABLES["base_url"], obligatoria=False)
        self.nombre = modelo or _del_entorno(VARIABLES["modelo_escritor"])
        # El transporte se inyecta para poder probar el adaptador sin red.
        self._transporte = transporte

    def __repr__(self):
        """Sin la clave. Un `repr` que la lleve acaba en un log tarde o temprano."""
        return "ClienteReal(modelo={0!r})".format(self.nombre)

    def llamar(self, prompt: str) -> dict:
        cuerpo = {"model": self.nombre, "prompt": prompt}
        try:
            bruto = self._transporte(
                url=self.base_url,
                cabeceras={"Authorization": "Bearer {0}".format(self._clave)},
                cuerpo=cuerpo,
            )
        except Exception as e:
            # El mensaje no incluye ni las cabeceras ni el cuerpo: las primeras
            # llevan la clave y el segundo puede ser el contexto entero.
            raise FalloDeTransporte(
                "la llamada al proveedor no completo: {0}".format(type(e).__name__)
            ) from None
        return _normalizar(bruto)


def _normalizar(bruto: dict) -> dict:
    """Deja la respuesta en la forma que el bucle espera.

    `usage` se **copia tal cual**. No se calcula, no se rellena y no se pone a
    cero si falta: queda ausente. Es la regla 1 de `SPEC-08` C-4, y es la que
    hace que `VER-41` compare dos numeros y no uno consigo mismo.
    """
    texto = bruto.get("texto") or bruto.get("content")
    delta = bruto.get("delta")
    if isinstance(delta, str):
        try:
            delta = json.loads(delta)
        except ValueError:
            delta = None
    salida = {"texto": texto, "delta": delta}
    if "usage" in bruto:
        salida["usage"] = bruto["usage"]
    return salida
