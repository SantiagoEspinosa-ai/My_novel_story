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


def test_genera_las_tres_escenas_en_orden(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1", "e2", "e3"]
    assert g.llego_al_final


def test_el_material_de_la_escena_2_incluye_lo_que_dejo_la_1(con):
    """El encadenado: sin esto la 2 genera contra el mundo de la 1."""
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    material = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert material["resumenes"], "el resumen de la 1 esta disponible en la 2"
    assert material["escena_anterior"], "y el texto de la 1 tambien"


def test_el_contexto_crece_escena_a_escena(con):
    """El criterio de terminacion de la Fase F, y el unico que importa."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    totales = [m["total"] for m in g.medidas]
    assert totales == sorted(totales), "no decrece: {0}".format(totales)
    assert totales[-1] > totales[0], "tiene que crecer solo: {0}".format(totales)


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
                "pov_usado": "per-marta",
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


# --- Los intentos, la rendicion y el tope global --------------------------

class SiempreCorto:
    """Produce siempre una escena fuera de rango: `INV-17`, `mayor`.

    Molesta y no corrompe, asi que es exactamente lo que se rinde.
    """

    nombre = "doble-corto"

    def __init__(self):
        self.llamadas = []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return {"texto": " ".join(["palabra"] * 3), "pov_usado": "per-marta",
                "delta": {"cambio_de_valor": {"eje": "cordura", "signo": "negativo"}},
                "usage": {"total_tokens": 100}}


def test_una_escena_con_un_mayor_se_reintenta_y_acaba_rindiendose(con):
    """`RF-24`: los intentos se agotan y la escena pasa a
    `aceptada_por_rendicion`, no a `aceptada`. Quien lea el manuscrito tiene
    que poder distinguirlas."""
    escritor = SiempreCorto()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000, hasta=1, tope_intentos=3)
    assert len(escritor.llamadas) == 3, "se agotan los intentos antes de rendirse"
    assert g.escenas_hechas == ["e1"]
    # Acaba en `consolidada`, no en `aceptada_por_rendicion`: la tabla de
    # transiciones de `Docs/architecture.md` tiene `aceptada_por_rendicion ->
    # consolidada`, asi que ese estado es de paso. Lo que deja constancia de
    # que se rindio es `borrador_aceptado` -que dice cual de los intentos se
    # eligio- y los hallazgos que siguen abiertos.
    assert repo.escena(con, "e1")["estado"] == "consolidada"
    assert repo.escena(con, "e1")["borrador_aceptado"] is not None
    # Los tres intentos empatan -el doble falla siempre igual-, y a igualdad
    # gana el primero: la rendicion tiene que ser reproducible.
    assert g.rendidas == [("e1", 1, 3)]


def test_los_problemas_del_intento_anterior_llegan_al_siguiente(con):
    """Si no, el escritor no sabe nada del fallo y vuelve a cometerlo. Es lo
    que le paso a la otra rama con el aviso de longitud."""
    escritor = SiempreCorto()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1, tope_intentos=2)
    assert "INV-17" in escritor.llamadas[1], "el segundo intento ve el problema"
    assert "INV-17" not in escritor.llamadas[0], "y el primero no, porque no habia"


def test_una_bloqueante_no_se_rinde_por_muchos_intentos_que_queden(con):
    """La falsedad entraria al canon y la heredarian todas las siguientes."""
    from app.commons.modelo.doble import Guion

    escritor = DobleDelModelo(Guion(["actua_sin_saber"]))
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000, tope_intentos=3)
    assert g.parada["escena"] == "e1"
    assert repo.escena(con, "e1")["estado"] != "aceptada_por_rendicion"


def test_el_tope_global_de_delegaciones_detiene_la_obra(con):
    """Acota el gasto, no el error: la parada dice cuantas llevaba."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000,
                          tope_delegaciones=2)
    assert g.parada["motivo"] == "tope_delegaciones"
    assert g.parada["delegaciones"] >= 2
    assert len(g.escenas_hechas) < 3, "no llego al final"


# --- La puerta de capitulo, al terminar la obra ---------------------------

def test_al_terminar_se_evalua_el_cierre_pero_no_se_firma(con):
    """La firma es **humana** y la dispara el cliente de la API, nunca el
    worker (`Docs/architecture.md`). Lo que hace el bucle al terminar es decir
    si el capitulo **podria** cerrarse, que es distinto de cerrarlo."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.llego_al_final
    assert g.cierre["puede_cerrarse"] is True
    assert g.cierre["firmado"] is False, "el bucle no firma"


def test_una_escena_rendida_deja_el_capitulo_sin_poder_cerrarse(con):
    """El control no desaparecio al dejar pasar un `mayor`: se movio aqui."""
    g = obra.generar_obra(con, "cap-1", SiempreCorto(), *_agentes()[1:],
                          techo=1_000_000, tope_intentos=2)
    assert g.rendidas, "las tres escenas se rindieron"
    assert g.cierre["puede_cerrarse"] is False
    assert "INV-17" in g.cierre["motivo"] or "mayor" in g.cierre["motivo"]


def test_si_la_obra_se_detiene_no_se_evalua_el_cierre(con):
    """Un capitulo con escenas a medias no es un capitulo, y preguntarselo a
    la puerta seria pedirle que juzgue algo que no ha terminado."""
    from app.commons.modelo.doble import Guion

    g = obra.generar_obra(con, "cap-1", DobleDelModelo(Guion(["actua_sin_saber"])),
                          *_agentes()[1:], techo=1_000_000)
    assert g.parada is not None
    assert g.cierre is None
