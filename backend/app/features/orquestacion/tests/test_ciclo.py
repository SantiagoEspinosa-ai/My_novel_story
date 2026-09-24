"""El ciclo completo contra dobles: generar, juzgar, consolidar y resumir.

Ningun proceso se arranca. Lo que se prueba es el **orden** y lo que pasa
cuando cada pieza falla, que es donde el ciclo se puede romper en silencio.
"""

import sqlite3

import pytest

from app.commons.invariantes import severidad
from app.commons.modelo.doble import DobleDelModelo, Guion
from app.features.consolidacion import aplicar
from app.features.contexto.bloques import BLOQUES
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo
from app.features.verificacion import puertas


class DobleQueDevuelve:
    """Un juez o resumidor de mentira, con la firma del real."""

    def __init__(self, respuesta, nombre="doble"):
        self.nombre = nombre
        self._r = respuesta

    def llamar(self, prompt):
        if self._r is None:
            from app.commons.modelo.proveedor import RespuestaIlegible
            raise RespuestaIlegible("no parsea")
        return dict(self._r, medidas={"modelos": ["doble-1"], "tokens_entrada": 10,
                                      "tokens_salida": 20})


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    aplicar.sembrar(c, {"marta": ("vivo", "salon")})
    repo.guardar_escaleta(c, "cap-1", [{"id": "e1", "orden": 1,
                                       "pov": "per-marta", "lugar": "lug-salon", 
        "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
        "beats": ["b1"], "longitud_objetivo": [100, 3000]}])
    return c


def _mundo():
    return {"entidades_vivas": {"marta": "vivo"}, "ubicaciones": {"marta": "salon"},
            "accesos": {"salon": []}, "conocimiento": {}}


def _ctx():
    return {b.nombre: 10 for b in BLOQUES}


def test_el_ciclo_completo_deja_escena_consolidada_y_resumida(con):
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                       DobleQueDevuelve({"veredicto": "PASA", "problemas": []}),
                       DobleQueDevuelve({"texto": "Marta baja.", "hechos_clave": []}),
                       _mundo(), techo=10_000)
    assert c.fallo is None
    assert c.veredicto["veredicto"] == "PASA"
    assert c.consolidada is True
    assert c.resumen["texto"] == "Marta baja."


def test_un_juez_ilegible_no_es_un_pase(con):
    """`SPEC-10` C-2: quien no se dejo auditar no gana por defecto."""
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(), DobleQueDevuelve(None),
                       DobleQueDevuelve({"texto": "x", "hechos_clave": []}),
                       _mundo(), techo=10_000)
    assert c.veredicto["veredicto"] == "SIN_VEREDICTO"


def test_se_consolida_despues_de_las_puertas_y_antes_de_resumir(con):
    """El orden no se puede cambiar, y aqui queda como prueba."""
    orden = []

    class Espia(DobleQueDevuelve):
        def llamar(self, prompt):
            orden.append("resumidor" if "Condensa" in prompt else "juez")
            return super().llamar(prompt)

    ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                   Espia({"veredicto": "PASA", "problemas": []}),
                   Espia({"texto": "x", "hechos_clave": []}), _mundo(), techo=10_000)
    assert orden == ["juez", "resumidor"]


def test_una_bloqueante_detiene_antes_de_consolidar(con):
    """Una bloqueante no se rinde: su delta no entra al canon.

    Se usa `INV-01` -escena sin `cambio_de_valor`- y no `INV-07` -sin beats-,
    porque la segunda es `mayor` y no detiene nada. La primera version de esta
    prueba se equivoco justo en eso: pedia un comportamiento de `bloqueante` a
    una invariante que no lo es.
    """
    mundo = _mundo()
    with con:
        con.execute("UPDATE escena SET cambio_de_valor='null' WHERE id='e1'")
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                       DobleQueDevuelve({"veredicto": "PASA"}),
                       DobleQueDevuelve({"texto": "x"}), mundo, techo=10_000)
    assert c.fallo == "bloqueante"
    assert c.consolidada is False


def test_el_coste_dice_cuantas_delegaciones_no_tienen_medida(con):
    """Un total sin decir que le falta es un suelo disfrazado de medida."""
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                       DobleQueDevuelve({"veredicto": "PASA"}),
                       DobleQueDevuelve({"texto": "x"}), _mundo(), techo=10_000)
    coste = ciclo.coste_total(c.trazas)
    assert coste["delegaciones"] == 3
    assert coste["sin_medida"] >= 1, "el Escritor doble no reporta medidas"


def test_un_sin_veredicto_no_detiene_la_escena_pero_queda_abierto(con):
    """`SPEC-18` C-3: "no se pudo comprobar" no es "se violo".

    Antes heredaba la severidad de su invariante, asi que un dato que faltaba
    detenia la obra igual que una violacion confirmada. Y tampoco puede pasar
    como exito: `SPEC-10` C-2 dice que quien no se dejo auditar no gana por
    defecto, y el sitio donde eso es verdad es el cierre de capitulo.
    """
    from app.commons.dominio.enumeraciones import EstadoDeHallazgo
    from app.features.escaleta import repository as repo

    with con:
        con.execute("UPDATE escena SET longitud_objetivo='[300, 900]' WHERE id='e1'")
    h = puertas.dato_ausente("INV-04", "e1", "Borrador.pov_usado", "comparar")
    assert h.estado is EstadoDeHallazgo.SIN_VEREDICTO
    assert not severidad.detiene_la_escena_por(h), "no detiene: no consta violacion"
    assert severidad.impide_cerrar_el_capitulo_por(h), "pero no gana por defecto"


def test_una_delegacion_ilegible_deja_su_coste_en_la_traza(con):
    """`PLAN-29` E1: el Juez devolvio algo que no parsea, pero el sobre se pago."""
    from app.commons.modelo.proveedor import RespuestaIlegible

    class JuezIlegibleConCoste(DobleQueDevuelve):
        def llamar(self, prompt):
            raise RespuestaIlegible("no parsea", medidas={"coste_usd": 0.05,
                                                           "tokens_entrada": 7,
                                                           "tokens_salida": 3,
                                                           "modelos": ["m-1"]})

    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(), JuezIlegibleConCoste(None),
                       DobleQueDevuelve({"texto": "x", "hechos_clave": []}),
                       _mundo(), techo=10_000)
    juez = [t for t in c.trazas if t.agente == "juez"][0]
    assert juez.resultado == "fallo"
    assert juez.medidas["coste_usd"] == 0.05 and juez.modelos == ["m-1"]


# --- `F-76` y `F-77`: lo que vio la primera ejecucion real aceptada -----------------

CRITERIOS = ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")


def test_el_editor_se_lee_aunque_el_transporte_anada_sus_medidas(con):
    """`F-76`: el transporte mete `medidas` en toda respuesta, y el esquema del Editor
    prohibe campos de mas: con datos reales, ninguna valoracion validaba nunca."""
    editor = DobleQueDevuelve({"valoraciones": [
        {"criterio": c, "nota": 4, "justificacion": "bien"} for c in CRITERIOS]})
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(), editor,
                       DobleQueDevuelve({"texto": "Marta baja.", "hechos_clave": []}),
                       _mundo(), techo=10_000, es_editor=True)
    assert "valoraciones" in c.veredicto
    sin = con.execute("SELECT COUNT(*) FROM hallazgo WHERE invariante='INV-26' "
                      "AND estado='sin_veredicto'").fetchone()[0]
    assert sin == 0


class _ResumidorQueMira(DobleQueDevuelve):
    def __init__(self):
        super().__init__({"texto": "Marta baja.", "hechos_clave": []})
        self.prompts = []

    def llamar(self, prompt):
        self.prompts.append(prompt)
        return super().llamar(prompt)


def test_el_resumidor_recibe_la_lista_de_hechos_que_su_contrato_exige(con):
    """`F-77`, Regla 4: la definicion del Resumidor le pide identificadores «de la lista
    que te den», y el prompt no le daba ninguna. En real, el modelo pidio la lista en vez
    de contestar, y la escena se quedo sin resumen."""
    r = _ResumidorQueMira()
    ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                   DobleQueDevuelve({"veredicto": "PASA", "problemas": []}), r, _mundo(),
                   techo=10_000, hechos=[{"id": "hec-llave", "enunciado": "la llave abre"}])
    assert "hec-llave" in r.prompts[0] and "la llave abre" in r.prompts[0]


def test_sin_hechos_el_resumidor_sabe_que_la_lista_va_vacia(con):
    r = _ResumidorQueMira()
    ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                   DobleQueDevuelve({"veredicto": "PASA", "problemas": []}), r, _mundo(),
                   techo=10_000)
    assert "hechos_clave vacia" in r.prompts[0]


def test_el_delta_se_guarda_con_la_version_del_borrador_que_se_consolido(con):
    """`PLAN-23` A1, hallazgo 9: sin la version, una reescritura a delta fijo posterior
    no se distingue del texto que levanto el acta, y la medida no puede avisar."""
    from app.features.consolidacion import deltas
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                       DobleQueDevuelve({"veredicto": "PASA", "problemas": []}),
                       DobleQueDevuelve({"texto": "Marta baja.", "hechos_clave": []}),
                       _mundo(), techo=10_000)
    assert c.consolidada is True
    assert deltas.ultimo(con, "e1")["version"] == c.generacion.version


def test_consolidar_cierra_los_hallazgos_de_puerta_que_la_version_aceptada_ya_no_tiene(con):
    """`F-118`: un intento anterior dejo un `INV-04` `bloqueante` abierto; la escena se
    reescribio y paso la puerta, pero el hallazgo del intento descartado seguia abierto, y la
    puerta de publicacion no publicaba nunca. Es `_conciliar` de la puerta, un nivel abajo."""
    repo.guardar_hallazgo(con, "INV-04", "verificador_de_reglas", "e1", "bloqueante",
                          "abierto", "el POV planificado es per-marta y el usado per-nadie")
    c = ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                       DobleQueDevuelve({"veredicto": "PASA", "problemas": []}),
                       DobleQueDevuelve({"texto": "Marta baja.", "hechos_clave": []}),
                       _mundo(), techo=10_000)
    assert c.consolidada is True
    fila = con.execute("SELECT estado, motivo_de_cierre FROM hallazgo WHERE invariante='INV-04'"
                       ).fetchone()
    assert fila[0] == "resuelto" and "ya no lo tiene" in fila[1]


def test_consolidar_no_cierra_un_hallazgo_que_la_version_aceptada_sigue_teniendo(con):
    """Un `INV-17` que produce la version aceptada -rendida con el- se queda abierto."""
    repo.guardar_hallazgo(con, "INV-26", "editor", "e1", "mayor", "abierto", "ritmo: nota 2")
    ciclo.ejecutar(con, "e1", _ctx(), DobleDelModelo(),
                   DobleQueDevuelve({"veredicto": "PASA", "problemas": []}),
                   DobleQueDevuelve({"texto": "Marta baja.", "hechos_clave": []}),
                   _mundo(), techo=10_000)
    assert con.execute("SELECT estado FROM hallazgo WHERE invariante='INV-26'").fetchone()[0] \
        == "abierto", "solo se concilian las invariantes de la puerta de escena"
