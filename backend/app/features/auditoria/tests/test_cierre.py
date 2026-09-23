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


def test_un_mayor_leido_de_la_base_tambien_bloquea():
    """La prueba que faltaba, y que dejo la puerta abierta en silencio.

    Las de arriba pasan `Severidad.MAYOR` directamente. El repositorio devolvia
    la cadena `"mayor"`, y `"mayor" is Severidad.MAYOR` es falso: el cierre
    pasaba con un `mayor` abierto y nada avisaba. Ahora el repositorio
    deserializa al tipo del dominio, y esta prueba recorre ese camino.
    """
    import sqlite3

    from app.features.escaleta import repository as repo

    con = sqlite3.connect(":memory:")
    repo.asegurar_tablas(con)
    repo.guardar_escaleta(con, "cap-1", [{"id": "e1", "orden": 1,
                                         "pov": "per-marta", "lugar": "lug-salon", 
        "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"}, "beats": ["b1"]}])
    repo.guardar_hallazgo(con, invariante="INV-07", verificador="verificador_de_reglas",
                          escena="e1", severidad=S.MAYOR, estado=EH.ABIERTO,
                          descripcion="sin beat")

    leidos = repo.hallazgos_abiertos(con, "e1")
    assert leidos[0]["severidad"] is S.MAYOR, "el repositorio devuelve el tipo del dominio"
    with pytest.raises(capitulo.NoSePuedeCerrar):
        capitulo.cerrar([EE.CONSOLIDADA], leidos)


def test_un_sin_veredicto_menor_tambien_impide_cerrar():
    """`SPEC-18` C-3: quien no se dejo auditar no gana por defecto, y eso no
    depende de la severidad que habria tenido la violacion. Mirar solo la
    severidad dejaba pasar un `menor` sin veredicto, que es precisamente un
    hueco en la auditoria."""
    with pytest.raises(capitulo.NoSePuedeCerrar):
        capitulo.cerrar(
            [EE.CONSOLIDADA],
            [{"invariante": "INV-16", "severidad": S.MENOR,
              "estado": EH.SIN_VEREDICTO}])


# --- F-47: INV-08 deja de estar declarada y sin ejecutar ------------------

def test_inv08_una_inversion_de_tiempo_impide_cerrar_el_capitulo():
    """`F-47`: la invariante estaba declarada, su consulta escrita y sus
    pruebas en verde, y **no la llamaba nadie en el pipeline**. Desde fuera
    -documento, codigo, pruebas- no se distinguia de una que si se ejecuta."""
    with pytest.raises(capitulo.NoSePuedeCerrar, match="INV-08"):
        capitulo.cerrar([EE.CONSOLIDADA], [],
                        orden_temporal={"inversiones": [("ev-1", "ev-2")],
                                        "sin_fecha_legible": []})


def test_inv08_sin_inversiones_no_impide_nada():
    c = capitulo.cerrar([EE.CONSOLIDADA], [],
                        orden_temporal={"inversiones": [], "sin_fecha_legible": []})
    assert c.estado == "cerrado"


def test_inv08_sin_fechas_legibles_no_es_un_verde():
    """Regla 8: no se pudo comprobar **no es** se comprobo y esta bien. Una
    obra sin `t_fabula` no tiene orden temporal que verificar, y eso tiene que
    verse distinto de una que lo tiene y esta en orden."""
    with pytest.raises(capitulo.NoSePuedeCerrar, match="INV-08"):
        capitulo.cerrar([EE.CONSOLIDADA], [],
                        orden_temporal={"inversiones": [],
                                        "sin_fecha_legible": ["ev-1", "ev-2"]})


def test_sin_el_dato_de_cronologia_el_cierre_sigue_funcionando():
    """Compatibilidad: quien no lo pase cierra como antes. El parametro se
    añade, no se exige."""
    assert capitulo.cerrar([EE.CONSOLIDADA], []).estado == "cerrado"
