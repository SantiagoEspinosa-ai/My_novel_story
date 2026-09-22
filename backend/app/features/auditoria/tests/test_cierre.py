"""D3 — La puerta de cierre de capitulo, y el barrido de obra.

La puerta de capitulo es lo que da consecuencia a un hallazgo `mayor`. Sin
ella, `mayor` y `menor` producirian exactamente el mismo comportamiento, y una
escala cuyos valores no se distinguen en nada es una etiqueta, no un control.
"""

import pytest

from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import Severidad as S
from app.features.auditoria import capitulo


def _h(sev, estado=EH.ABIERTO):
    return {"severidad": sev, "estado": estado}


def test_un_mayor_abierto_impide_cerrar():
    with pytest.raises(capitulo.NoSePuedeCerrar, match="mayor"):
        capitulo.cerrar([EE.CONSOLIDADA], [_h(S.MAYOR)])


def test_un_menor_abierto_no_impide_cerrar_pero_se_lista():
    r = capitulo.cerrar([EE.CONSOLIDADA], [_h(S.MENOR)])
    assert r.estado == "cerrado"
    assert len(r.menores_que_se_dejan_pasar) == 1, (
        "si no se enseñan, mayor y menor vuelven a ser lo mismo")


def test_un_mayor_descartado_no_bloquea():
    """Para eso existe `descartado`: cerrar un falso positivo sin fingir que
    se corrigio."""
    assert capitulo.cerrar([EE.CONSOLIDADA], [_h(S.MAYOR, EH.DESCARTADO)]).estado == "cerrado"


def test_un_sin_veredicto_bloquea_como_el_peor_de_su_severidad():
    """`SPEC-10`: quien no se dejo auditar no gana por defecto."""
    with pytest.raises(capitulo.NoSePuedeCerrar):
        capitulo.cerrar([EE.CONSOLIDADA], [_h(S.MAYOR, EH.SIN_VEREDICTO)])


def test_una_escena_a_medias_impide_cerrar():
    with pytest.raises(capitulo.NoSePuedeCerrar, match="consolidada"):
        capitulo.cerrar([EE.CONSOLIDADA, EE.EN_REVISION], [])


def test_una_escena_rendida_cuenta_como_completa():
    """Su delta entro al canon igual que el de una limpia."""
    assert capitulo.cerrar([EE.ACEPTADA_POR_RENDICION], []).estado == "cerrado"


def test_un_capitulo_cerrado_no_se_reabre():
    r = capitulo.cerrar([EE.CONSOLIDADA], [])
    with pytest.raises(capitulo.NoSePuedeCerrar, match="reabre"):
        capitulo.reabrir(r)
