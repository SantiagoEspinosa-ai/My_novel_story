"""`INV-21` en el bucle de la obra (`SPEC-25` `RF-18`, `PLAN-25` E4).

Una palabra vetada devuelve la escena al Escritor **hasta dos veces**, con un
contador que no gasta los intentos de calidad, y al agotarse **se para**: no hay
rendicion posible, porque el `menos_malo` de tres textos con el nombre de una
expareja sigue llevando el nombre de la expareja.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.commons.invariantes import registro
from app.commons.modelo.doble import DobleDelModelo, Guion
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra
from app.features.politica import repository as politica

VETADAS = ["zoquete"]


class Devuelve:
    def __init__(self, respuesta, nombre="doble"):
        self.nombre, self._r = nombre, respuesta

    def llamar(self, prompt):
        return dict(self._r)


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    politica.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-sotano"], "lug-sotano": ["lug-salon"]})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e{0}".format(i), "orden": i,
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": ["b"], "longitud_objetivo": [10, 5000]} for i in (1, 2)])
    return c


def _generar(con, pasos, **kw):
    escritor = DobleDelModelo(Guion(pasos))
    g = obra.generar_obra(
        con, "cap-1", escritor,
        Devuelve({"veredicto": "PASA", "problemas": []}),
        Devuelve({"texto": "Resumen. " * 10, "hechos_clave": []}),
        techo=1_000_000, vetadas=VETADAS, **kw)
    return g, escritor


def _tipos(con):
    return [d["tipo"] for d in auditoria.decisiones(con, "cap-1")]


def test_dos_reescrituras_y_la_tercera_limpia_se_acepta(con):
    g, escritor = _generar(con, ["vetada", "vetada", "bien"])
    assert g.escenas_hechas == ["e1", "e2"]
    assert len(escritor.llamadas) == 4
    assert _tipos(con) == [TD.COINCIDENCIA_VETADA, TD.REESCRITURA_PEDIDA,
                           TD.COINCIDENCIA_VETADA, TD.REESCRITURA_PEDIDA]


def test_las_reescrituras_no_gastan_los_intentos_de_calidad(con):
    """Con un solo intento de calidad, dos vetadas siguen cabiendo."""
    g, _ = _generar(con, ["vetada", "vetada", "bien"], tope_intentos=1)
    assert g.llego_al_final


def test_la_tercera_vetada_para_la_obra_sin_rendirse(con):
    g, _ = _generar(con, ["vetada"])
    assert g.parada["motivo"] == "palabra_vetada"
    assert g.parada["escena"] == "e1"
    assert g.escenas_hechas == [] and g.rendidas == []
    assert repo.escena(con, "e1")["estado"] != "consolidada"
    assert _tipos(con).count(TD.COINCIDENCIA_VETADA) == 3
    assert _tipos(con).count(TD.REESCRITURA_PEDIDA) == 2
    assert _tipos(con)[-1] == TD.PARADA_POR_VETADA


def test_la_reescritura_le_dice_al_escritor_que_escribio(con):
    _, escritor = _generar(con, ["vetada", "bien"])
    assert "INV-21" in escritor.llamadas[1]
    assert "zoquete" in escritor.llamadas[1]


def test_el_prompt_lleva_las_vetadas_desde_el_primer_intento(con):
    """Regla 4: exigir sin pedir produce un rechazo merecido e inutil."""
    _, escritor = _generar(con, ["bien"])
    assert "zoquete" in escritor.llamadas[0]


def test_la_coincidencia_queda_con_su_fragmento_escena_e_intento(con):
    _generar(con, ["vetada", "bien"])
    [d] = [d for d in auditoria.decisiones(con, "cap-1")
           if d["tipo"] == TD.COINCIDENCIA_VETADA]
    assert d["detalle"] == {"vetada": "zoquete", "fragmento": "zoquete",
                            "escena": "e1", "reescritura": 0}


def test_el_cierre_no_deja_pasar_una_vetada_que_entro_por_otro_camino(con):
    """Segunda linea: un texto editado a mano no paso por la puerta."""
    _generar(con, ["bien"])
    with con:
        con.execute("UPDATE borrador SET texto = texto || ' zoquete' "
                    "WHERE escena = 'e2'")
    cierre = obra.evaluar_cierre(con, "cap-1", vetadas=VETADAS)
    assert cierre["puede_cerrarse"] is False
    assert "INV-21" in cierre["motivo"]


def test_sin_vetadas_el_informe_dice_que_no_se_comprobo(con):
    """Un dato ausente no es un verde."""
    g = obra.generar_obra(con, "cap-1", DobleDelModelo(),
                          Devuelve({"veredicto": "PASA", "problemas": []}),
                          Devuelve({"texto": "Resumen. " * 10, "hechos_clave": []}),
                          techo=1_000_000)
    assert "INV-21 no se comprobo" in obra.informe(g)


def test_inv21_esta_en_el_registro_como_bloqueante_de_capitulo():
    inv = registro.TODAS["INV-21"]
    assert inv.severidad.value == "bloqueante"
    assert inv.nivel.value == "capitulo"
