"""La interfaz de un exportador a Langfuse, el nulo y el doble (`PLAN-29` E3).

Un exportador recibe los tipos de `envio.py` ya validados y no sabe nada del pipeline.
El real (`langfuse.py`) es el unico que habla con la red; estos dos no salen de la maquina.
"""


class ExportadorNulo:
    """Sin claves no se envia nada, y se dice por que: un apagado callado se leeria como
    un envio que salio bien."""

    def __init__(self, motivo):
        self.motivo = motivo

    def enviar(self, tipo, objeto):
        pass

    def vaciar(self, timeout=None):
        return True


class ExportadorEnMemoria:
    """El doble. Guarda lo que se enviaria ya serializado, que es lo que miran las pruebas
    del limite; con `falla=True` revienta en cada envio, para probar `RF-09`."""

    motivo = None

    def __init__(self, falla=False, mensaje="conexion rechazada"):
        self.enviados = []
        self._falla, self._mensaje = falla, mensaje

    def enviar(self, tipo, objeto):
        if self._falla:
            raise ConnectionError(self._mensaje)
        self.enviados.append((tipo, objeto.a_enviar()))

    def vaciar(self, timeout=None):
        return not self._falla
