"""F6 — El bucle de escenas, contra dobles.

Lo que se comprueba aqui es el **encadenado**: que el material de la escena N
incluya lo que dejo la N-1, que el contexto crezca, y que una `bloqueante`
detenga la obra en vez de saltarsela.
"""

import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra


class Devuelve:
    def __init__(self, respuesta, nombre="doble"):
        self.nombre, self._r = nombre, respuesta

    def llamar(self, prompt):
        return dict(self._r, medidas={"modelos": ["doble-1"], "tokens_entrada": 5,
                                      "tokens_salida": 5})


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-sotano"], "lug-sotano": ["lug-salon"]})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e{0}".format(i), "orden": i,
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": ["b"], "longitud_objetivo": [10, 5000]} for i in (1, 2, 3)])
    return c


def _agentes():
    return (DobleDelModelo(),
            Devuelve({"veredicto": "PASA", "problemas": []}),
            Devuelve({"texto": "Resumen de la escena. " * 10,
                      "hechos_clave": ["hec-llave"]}))


PENDIENTE_F36 = pytest.mark.xfail(strict=True, reason=(
    "F-36: `Borrador.pov_usado` es obligatorio en el dominio y **nadie lo "
    "rellena**. Al dejar de callarse (`F-34`), `INV-04` devuelve "
    "`sin_veredicto` en toda escena, y `sin_veredicto` hereda la severidad de "
    "su invariante -`bloqueante`- asi que el bucle se detiene antes de "
    "generar nada. No se ablanda la comprobacion ni se ajusta la prueba: "
    "faltan dos decisiones de dominio -de donde sale `pov_usado` y si un "
    "`sin_veredicto` detiene igual que una violacion confirmada- y las dos "
    "van por spec. `strict` para que estas pruebas avisen en cuanto se "
    "decidan."))


@PENDIENTE_F36
def test_genera_las_tres_escenas_en_orden(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1", "e2", "e3"]
    assert g.llego_al_final


@PENDIENTE_F36
def test_el_material_de_la_escena_2_incluye_lo_que_dejo_la_1(con):
    """El encadenado: sin esto la 2 genera contra el mundo de la 1."""
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    material = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert material["resumenes"], "el resumen de la 1 esta disponible en la 2"
    assert material["escena_anterior"], "y el texto de la 1 tambien"


@PENDIENTE_F36
def test_el_contexto_crece_escena_a_escena(con):
    """El criterio de terminacion de la Fase F, y el unico que importa."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    totales = [m["total"] for m in g.medidas]
    assert totales == sorted(totales), "no decrece: {0}".format(totales)
    assert totales[-1] > totales[0], "tiene que crecer solo: {0}".format(totales)


@PENDIENTE_F36
def test_una_bloqueante_detiene_la_obra_y_deja_el_dato(con):
    """No se rinde y no se salta. Y la parada **es la medida** (`VER-64`)."""
    with con:
        con.execute("UPDATE escena SET cambio_de_valor='null' WHERE id='e2'")
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1"]
    assert g.parada["escena"] == "e2"
    assert any(inv == "INV-01" for inv, _ in g.parada["hallazgos"])
    assert "INV-01" in obra.informe(g)


def test_rf26_detiene_la_obra_sin_llamar_al_modelo(con):
    """Con un techo imposible no se genera: se falla antes."""
    escritor = DobleDelModelo()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1)
    assert g.parada["motivo"] == "no_cabe"
    assert escritor.llamadas == []


@PENDIENTE_F36
def test_el_informe_dice_si_el_contexto_crece(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert "CRECE" in obra.informe(g)


# --- SPEC-15: los hechos los declara el plan, y el prompt los lleva --------

class Revela:
    """Un doble que **revela**, que es lo que el de serie nunca hace.

    Regla 3 aplicada a las pruebas: un doble que solo sabe portarse bien pasa
    contra si mismo. Sin este, el marcado de `escena_de_establecimiento` no
    tendria ningun caso que lo ejercite.
    """

    nombre = "doble-que-revela"

    def __init__(self):
        self.llamadas = []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return {"texto": " ".join(["palabra"] * 1500),
                "delta": {"cambio_de_valor": {"eje": "cordura",
                                              "signo": "negativo"},
                          "movimientos": [],
                          "revelaciones": [{"sujeto": "per-marta",
                                            "hecho": "hec-llave",
                                            "grado": "sabe"}]},
                "usage": {"total_tokens": 2100}}


def test_los_hechos_declarados_llegan_al_prompt(con):
    """El punto muerto de `F-29`: la lista salia del registro de conocimiento,
    que solo crecia con revelaciones, que necesitaban la lista."""
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert "hec-llave" in escritor.llamadas[0]


def test_sin_hechos_declarados_el_prompt_no_inventa_ninguno(con):
    """El caso negativo: que aparezca uno aqui seria el prompt fabricandolo."""
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert "hec-" not in escritor.llamadas[0]


@PENDIENTE_F36
def test_una_revelacion_marca_donde_el_texto_establece_el_hecho(con):
    """`SPEC-15` C-1: `escena_de_establecimiento` es donde lo establece el
    TEXTO, no donde nacio el hecho. Y `SPEC-16` C-4: establecer un hecho **es**
    su primera revelacion.

    Esta prueba estuvo marcada `xfail(strict)` mientras `F-31` estuvo abierto:
    la obra paraba en `e1` y no se llegaba a marcar nada. Se retira la marca
    porque el fallo esta corregido, no porque la prueba se haya ablandado.
    """
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    obra.generar_obra(con, "cap-1", Revela(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    hechos = repo.hechos_declarados(con, "cap-1")
    assert hechos[0]["establecido_en"] == "e1"


def test_el_material_de_una_escena_lleva_los_hechos_de_su_obra(con):
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    material = obra.reunir_material(con, repo.escena(con, "e1"), "cap-1")
    assert [h["id"] for h in material["hechos"]] == ["hec-llave"]


def test_una_accion_sin_conocimiento_detiene_la_obra(con):
    """El circuito entero contra el doble, y el caso que `F-24` cazo en real.

    El doble tiene que poder producirlo: si solo sabe portarse bien, el bucle
    pasa contra el doble y falla contra el proveedor (`F-18`, Regla 3).
    """
    from app.commons.modelo.doble import Guion

    escritor = DobleDelModelo(Guion(["actua_sin_saber"]))
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000)
    assert g.escenas_hechas == []
    assert g.parada["escena"] == "e1"
    assert any(inv == "INV-03" for inv, _ in g.parada["hallazgos"])
