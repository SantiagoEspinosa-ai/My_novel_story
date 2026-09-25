"""`PLAN-34` E1 y E2: la pareja guardada, la sustitucion exacta y la envoltura (`SPEC-34`).

Los nombres de estas pruebas son inventados: no hay ninguna persona real detras.
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio.enumeraciones import TitularDePseudonimo as TP
from app.commons.politica import pseudonimos as ps


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    return c


def _tabla(con, obra="obra-1", evitar=()):
    return ps.asignar(con, obra, [("Olivia Carranza", TP.DESTINATARIO),
                                  ("Tino", TP.MASCOTA), ("Ramón", TP.QUIEN_REGALA)],
                      evitar=evitar)



def _diminutivo(nombre):
    """«Elena» -> «Elenita», «Inés» -> «Inésita»: sin la ultima vocal, si la tiene."""
    return (nombre[:-1] if nombre[-1] in "aeiou" else nombre) + "ita"

# --- E1: la pareja guardada ---------------------------------------------------

def test_cada_palabra_del_nombre_tiene_su_pseudonimo(con):
    """`RF-08`: «Olivia» sola tambien se sustituye, y «Carranza» suelto."""
    t = _tabla(con)
    assert set(t.pares) == {"Olivia", "Carranza", "Tino", "Ramón"}
    texto = t.pseudonimizar("Olivia Carranza paseaba con Tino. Olivia reía; Carranza no.")
    for real in ("Olivia", "Carranza", "Tino"):
        assert real not in texto
    assert t.pares["Olivia"] + " " + t.pares["Carranza"] in texto


def test_las_particulas_en_minuscula_no_se_sustituyen(con):
    t = ps.asignar(con, "obra-2", [("María de la Paz", TP.DESTINATARIO)])
    assert set(t.pares) == {"María", "Paz"}


def test_el_pseudonimo_es_estable_y_se_lee_de_la_base(con):
    """`RF-02`: una pareja guardada, no un calculo que se repite."""
    t = _tabla(con)
    de_nuevo = _tabla(con)
    leida = ps.de_la_obra(con, "obra-1")
    assert t.pares == de_nuevo.pares == leida.pares
    # Y es distinto en otra obra: la eleccion sale de una huella de la obra.
    otra = _tabla(con, obra="obra-otra")
    assert otra.pares != t.pares


def test_el_pseudonimo_no_choca_con_nombres_vetadas_ni_raices(con):
    t = _tabla(con, evitar=["Elena", "Bruno"])
    pseudos = set(t.pares.values())
    assert not pseudos & {"Olivia", "Carranza", "Tino", "Ramón", "Elena", "Bruno"}
    assert len(pseudos) == len(t.pares)
    for p in pseudos:
        for otro in set(t.pares) | pseudos - {p}:
            assert not ps.comparten_raiz(p, otro), (p, otro)


def test_un_nombre_femenino_recibe_un_pseudonimo_femenino(con):
    """Hallazgo 5 de `PLAN-34`: la misma lectura que haria el modelo."""
    t = _tabla(con)
    assert t.pares["Olivia"] in ps.PILA_FEMENINA
    assert t.pares["Ramón"] in ps.PILA_MASCULINA
    assert t.pares["Carranza"] in ps.APELLIDOS
    assert t.pares["Tino"] in ps.MASCOTAS


def test_un_nombre_femenino_que_no_acaba_en_a_sigue_siendo_femenino(con):
    """«Irene» recibia un pseudonimo masculino, y el Escritor habria escrito «el». Lo cazo
    la prueba de la entrega."""
    t = ps.asignar(con, "obra-g", [("Irene", TP.DESTINATARIO), ("Borja", TP.PERSONA)])
    assert t.pares["Irene"] in ps.PILA_FEMENINA
    assert t.pares["Borja"] in ps.PILA_MASCULINA
    assert all(n == ps._plano(n) for n in ps.FEMENINOS_SIN_A | ps.MASCULINOS_CON_A)


def test_una_obra_sin_tabla_no_sustituye_nada(con):
    t = ps.de_la_obra(con, "sin-nombres")
    assert t.pseudonimizar("Olivia") == "Olivia"
    assert t.restituir({"texto": "Olivia"}) == {"texto": "Olivia"}


def test_restituir_devuelve_el_texto_original_en_listas_y_diccionarios(con):
    t = _tabla(con)
    original = {"texto": "Olivia Carranza y Tino.", "delta": {"personajes": [
        {"nombre": "Olivia"}, {"nombre": "Tino"}]}, "lista": ["Carranza"],
        "medidas": {"modelo": "Olivia"}}
    ida = {k: v for k, v in original.items()}
    ida["texto"] = t.pseudonimizar(original["texto"])
    ida["delta"] = {"personajes": [{"nombre": t.pares["Olivia"]},
                                   {"nombre": t.pares["Tino"]}]}
    ida["lista"] = [t.pares["Carranza"]]
    assert t.restituir(ida) == original


def test_la_sustitucion_es_exacta_y_respeta_los_limites_de_palabra(con):
    t = _tabla(con)
    assert t.pseudonimizar("Tinoco y tino") == "Tinoco y tino"


def test_una_forma_derivada_del_pseudonimo_es_un_residuo(con):
    """`RF-04`: «Elenita» por «Elena» no se restituye a medias: se ve."""
    t = _tabla(con)
    p = t.pares["Olivia"]
    derivada = _diminutivo(p)
    assert t.residuos({"texto": "Llego {0} con su perro.".format(derivada)}) == [derivada]
    assert t.residuos({"texto": "Llego Olivia con su perro."}) == []


def test_un_nombre_parecido_que_no_es_diminutivo_no_es_un_residuo(con):
    """«Martín» no es un diminutivo de «Marta»: es otro personaje. Marcarlo haria reescribir
    todas sus escenas. Y un personaje conocido de la obra nunca es un resto."""
    t = ps.Tabla({"Olivia": "Marta"})
    assert t.residuos({"texto": "Martín y Martina llegaron."}) == []
    assert t.residuos({"texto": "Martitas"}, conocidos=["Martitas"]) == []
    assert t.residuos({"texto": "Llegó Martita."}) == ["Martita"]


def test_los_nombres_vetados_se_ocultan(con):
    """`RF-07`: el nombre vetado completo no sale, aunque vaya en una lista de vetadas."""
    t = _tabla(con)
    t.vetados = ["Marcos Ledesma"]
    salida = t.pseudonimizar("Evita: Marcos Ledesma, oscuro")
    assert "Marcos Ledesma" not in salida
    assert ps.MARCA_DE_VETADO in salida


def test_borrar_de_la_obra(con):
    _tabla(con)
    assert ps.borrar_de_la_obra(con, "obra-1") == 4
    assert ps.de_la_obra(con, "obra-1").pares == {}


def test_asegurar_desde_la_ficha_toma_todos_los_nombres_declarados(con):
    from app.commons.dominio.destinatario import FichaDeEntrevista
    ficha = FichaDeEntrevista.model_validate({
        "destinatario": {"nombre": "Olivia Carranza", "edad": 9, "elementos": [
            {"tipo": "mascota", "descripcion": "su perro", "nombre": "Tino"},
            {"tipo": "persona", "descripcion": "su abuela", "nombre": "Aurora"},
            {"tipo": "rasgo", "descripcion": "curiosa"}]},
        "regalado_por": "Ramón", "nombres_vetados": ["Marcos Ledesma"]})
    t = ps.asegurar(con, "obra-3", ficha)
    assert set(t.pares) == {"Olivia", "Carranza", "Tino", "Aurora", "Ramón"}
    assert t.vetados == ["Marcos Ledesma"]
    assert "Marcos" not in t.pares.values()


# --- E2: la envoltura ---------------------------------------------------------

class _Doble:
    def __init__(self, responder):
        self.recibido = []
        self.responder = responder
        self.reglas = None
        self.herramientas = None
        self.nombre = "doble"

    def llamar(self, prompt):
        self.recibido.append(prompt)
        return self.responder(prompt)


def test_el_agente_no_ve_el_nombre_real_y_quien_llama_si(con):
    t = _tabla(con)
    doble = _Doble(lambda p: {"texto": p.replace("Escribe sobre ", ""),
                              "medidas": {"coste_usd": 0.1}})
    s = ps.SesionPseudonimizada(doble, t)
    r = s.llamar("Escribe sobre Olivia Carranza y Tino")
    assert "Olivia" not in doble.recibido[0] and "Tino" not in doble.recibido[0]
    assert r["texto"] == "Olivia Carranza y Tino"
    assert r["medidas"] == {"coste_usd": 0.1}


def test_la_configuracion_llega_a_la_sesion_de_dentro(con):
    doble = _Doble(lambda p: {})
    s = ps.SesionPseudonimizada(doble, _tabla(con))
    s.reglas = "/tmp/reglas.json"
    s.herramientas = {"db": "x"}
    assert doble.reglas == "/tmp/reglas.json" and doble.herramientas == {"db": "x"}
    assert s.nombre == "doble"


def test_un_resto_en_la_respuesta_queda_en_residuos(con):
    t = _tabla(con)
    derivada = _diminutivo(t.pares["Olivia"])
    s = ps.SesionPseudonimizada(_Doble(lambda p: {"texto": derivada + " corre"}), t)
    s.llamar("hola")
    assert s.residuos == [derivada]
