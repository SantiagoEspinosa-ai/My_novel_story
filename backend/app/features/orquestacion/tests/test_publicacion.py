"""`PLAN-30` E8: evaluar la puerta de publicacion una vez, con Lean automatico.

La novela se escribe con dobles (`_escrita`, de `test_novela.py`) y Lean es un doble
que cuenta cuantas veces se le llama: estas pruebas miran lo que compone la puerta,
no lo que dice Lean de verdad (eso es `auditoria/tests/test_lean_real.py`).
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.features.auditoria import repository as veredictos
from app.features.auditoria.publicacion import ResultadoLean
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import publicacion
from app.features.orquestacion.tests.test_novela import BIEN, JuezDeObra, _escrita
from app.features.planificacion.tests.conftest import ficha

ABRUPTO = {"arco_cerrado": True, "final_abrupto": True, "justificacion": "acaba de golpe"}


class LeanFijo:
    def __init__(self, codigo=0, violaciones=()):
        self.resultado = ResultadoLean(codigo, list(violaciones))
        self.llamadas = 0

    def verificar(self, con, obra):
        self.llamadas += 1
        return self.resultado


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    migraciones.migrar(c)
    return c


def _evaluar(con, lean, juez):
    return publicacion.evaluar(con, "obra-x", ficha(), lean, juez)


def _abiertos(con, invariante):
    return [h for e in escaleta.escenas_de(con, "obra-x")
            for h in escaleta.hallazgos_abiertos(con, e["id"])
            if h["invariante"] == invariante]


def test_lean_se_ejecuta_sin_que_nadie_lo_pida(con):
    """`RF-02`: una llamada a Lean por ronda, sin que el llamante lo pida."""
    _escrita(con)
    lean = LeanFijo()
    _evaluar(con, lean, JuezDeObra(BIEN))
    assert lean.llamadas == 1


def test_todo_limpio_guarda_el_veredicto_publicado(con):
    _escrita(con)
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert e.decision.publica and e.ronda == 1
    v = veredictos.ultimo(con, "obra-x")
    assert v["publica"] and v["ronda"] == 1 and v["codigo_lean"] == 0
    assert [n["invariante"] for n in v["no_ejecutadas"]] == ["INV-06"]


def test_con_inv24_fallando_lean_se_ejecuta_igual(con):
    """`RF-04` informa de todas las condiciones, asi que Lean corre aunque ya se
    sepa que la version no se publica."""
    _escrita(con, usados=("imp-01", "imp-02"))
    lean = LeanFijo()
    e = _evaluar(con, lean, JuezDeObra(BIEN))
    assert lean.llamadas == 1
    assert "INV-24" in [c.invariante for c in e.decision.condiciones]


def test_un_capitulo_rendido_no_publica(con):
    _escrita(con)
    with con:
        con.execute("UPDATE escena SET estado='aceptada_por_rendicion' "
                    "WHERE id='obra-x-cap-03-e1' OR id='cap-03-e1'")
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert [(c.invariante, c.capitulo) for c in e.decision.condiciones] == [("INV-29", "cap-03")]


def test_un_fallo_de_lean_deja_hallazgo_inv28_con_sus_eventos(con):
    _escrita(con)
    e = _evaluar(con, LeanFijo(1, [{"invariante": "L-1", "eventos": ["ev-1", "ev-2"],
                                    "detalle": "ev-2 va antes"}]), JuezDeObra(BIEN))
    assert not e.decision.publica
    assert "L-1" in _abiertos(con, "INV-28")[0]["descripcion"]


def test_un_inv27_que_la_ronda_nueva_no_ve_se_cierra_con_motivo(con):
    _escrita(con)
    _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    [viejo] = _abiertos(con, "INV-27")
    e = _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert e.decision.publica and e.ronda == 2
    assert _abiertos(con, "INV-27") == []
    fila = con.execute("SELECT estado, motivo_de_cierre FROM hallazgo WHERE id = ?",
                       (viejo["id"],)).fetchone()
    assert fila[0] == EH.RESUELTO.value and "ronda 2" in fila[1]


def test_un_inv27_que_sigue_no_se_cierra_ni_se_duplica(con):
    """Si sigue, queda el mismo hallazgo: ni se marca resuelto lo que no se arreglo,
    ni se abre otro igual encima (el recuento por invariante es lo que dice si una
    regla sirve)."""
    _escrita(con)
    _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    [viejo] = _abiertos(con, "INV-27")
    e = _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    assert not e.decision.publica
    assert [h["id"] for h in _abiertos(con, "INV-27")] == [viejo["id"]]


# --- E10: el bucle de la puerta ---------------------------------------------------

class Secuencia:
    """Un juez de obra que dice, ronda a ronda, lo que le toca."""

    nombre = "doble-obra"

    def __init__(self, *respuestas):
        self.respuestas, self.llamadas = list(respuestas), []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.respuestas[min(len(self.llamadas) - 1, len(self.respuestas) - 1)]


class Editor:
    nombre = "doble-editor"

    def __init__(self, respuesta):
        self.respuesta, self.llamadas = respuesta, []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return self.respuesta


class Reescritor:
    def __init__(self):
        self.llamadas = []

    def __call__(self, con, escena_id, instrucciones):
        self.llamadas.append((escena_id, instrucciones))
        return {"aceptada": True, "motivo": ""}


INSTRUYE_CAP10 = {"instrucciones": [{"capitulo": "cap-10", "instruccion": "cierra el viaje"}]}


def _publicar(con, lean, juez, editor, reescribir, **kw):
    return publicacion.publicar(con, "obra-x", ficha(), lean, juez, editor, reescribir, **kw)


def test_el_fallo_de_lean_llega_al_editor_con_la_violacion_y_los_eventos(con):
    """`RF-03`: el Editor recibe la violacion concreta y los eventos implicados."""
    _escrita(con)
    editor = Editor({"diagnostico": "el plan pone el capitulo 3 antes del 2"})
    p = _publicar(con, LeanFijo(1, [{"invariante": "L-1", "eventos": ["ev-1", "ev-2"],
                                     "detalle": "ev-2 va antes"}]),
                  Secuencia(BIEN), editor, Reescritor())
    assert "L-1" in editor.llamadas[0] and "ev-1,ev-2" in editor.llamadas[0]
    assert not p.publicada and p.parada["motivo"] == "lean"
    assert "el capitulo 3 antes del 2" in p.parada["diagnostico"]


def test_un_fallo_de_l1_va_al_editor_y_detiene_sin_reescribir(con):
    """`C-2`: lo que Lean mira lo fija el plan; reescribir la prosa seria gasto sin
    efecto. El diagnostico va al informe y la generacion se detiene."""
    _escrita(con)
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(1, [{"invariante": "L-1", "eventos": ["ev-1", "ev-2"],
                                     "detalle": "x"}]),
                  Secuencia(BIEN), Editor({"diagnostico": "d"}), reescribir)
    assert reescribir.llamadas == [] and p.rondas == 1


def test_un_final_abrupto_arreglado_en_la_segunda_ronda_publica(con):
    _escrita(con)
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(), Secuencia(ABRUPTO, BIEN), Editor(INSTRUYE_CAP10),
                  reescribir)
    assert p.publicada and p.rondas == 2
    assert reescribir.llamadas == [("cap-10-e1", ["cierra el viaje"])]


def test_nunca_hay_un_tercer_reintento(con):
    """Tope 2 (`RF-07`): tres evaluaciones como mucho —la primera y dos reintentos—.
    No son las 3 reescrituras del Editor: es otro contador."""
    _escrita(con)
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(), Secuencia(ABRUPTO), Editor(INSTRUYE_CAP10), reescribir)
    assert not p.publicada and p.parada["motivo"] == "tope"
    assert len(reescribir.llamadas) == 2 and p.rondas == 3


def test_relanzar_no_reinicia_el_contador(con):
    """La leccion de `CE-4`: el tope se lee de la base, no de la memoria de un proceso."""
    _escrita(con)
    _publicar(con, LeanFijo(), Secuencia(ABRUPTO), Editor(INSTRUYE_CAP10), Reescritor())
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(), Secuencia(ABRUPTO), Editor(INSTRUYE_CAP10), reescribir)
    assert reescribir.llamadas == [] and p.parada["motivo"] == "tope"


def test_una_instruccion_para_un_capitulo_no_implicado_se_ignora_y_se_informa(con):
    _escrita(con)
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(), Secuencia(ABRUPTO, BIEN), Editor({"instrucciones": [
        {"capitulo": "cap-02", "instruccion": "cambia todo"},
        {"capitulo": "cap-10", "instruccion": "cierra el viaje"}]}), reescribir)
    assert [e for e, _ in reescribir.llamadas] == ["cap-10-e1"]
    assert p.ignoradas == [("cap-02", "cambia todo")]


def test_una_respuesta_ilegible_del_editor_gasta_la_ronda_sin_reescribir(con):
    _escrita(con)
    reescribir = Reescritor()
    p = _publicar(con, LeanFijo(), Secuencia(ABRUPTO), Editor("no es json"), reescribir)
    assert reescribir.llamadas == [] and p.parada["motivo"] == "tope"


def test_toda_secuencia_de_veredictos_termina_publicada_o_detenida(con):
    """La propiedad de terminacion que el enunciado pide a TLA+, sobre el codigo."""
    for juez in (Secuencia(BIEN), Secuencia(ABRUPTO), Secuencia(ABRUPTO, BIEN),
                 Secuencia(ABRUPTO, ABRUPTO, BIEN)):
        c = sqlite3.connect(":memory:")
        c.row_factory = sqlite3.Row
        migraciones.migrar(c)
        _escrita(c)
        p = publicacion.publicar(c, "obra-x", ficha(), LeanFijo(), juez,
                                 Editor(INSTRUYE_CAP10), Reescritor())
        assert p.publicada != (p.parada is not None)


# --- `PLAN-23` B-S1.1, `F-122` (TLC `CE-15`): las rondas de la puerta son de su version --

def _version_2(con):
    """La version 2 de `obra-x`, que comparte todos los capitulos de la 1: basta para
    que la puerta tenga que saber de que version cuenta las rondas."""
    from app.features.brief import repository as brief
    return brief.crear_version(con, "obra-x", brief.capitulos_de_version(con, "obra-x", 1),
                               anterior=1)


def test_las_rondas_de_la_puerta_se_cuentan_por_version(con):
    _escrita(con)
    _evaluar(con, LeanFijo(), JuezDeObra(ABRUPTO))
    _evaluar(con, LeanFijo(), JuezDeObra(BIEN))
    assert _version_2(con) == 2
    assert veredictos.rondas(con, "obra-x", 1) == 2
    assert veredictos.rondas(con, "obra-x", 2) == 0
    e = publicacion.evaluar(con, "obra-x", ficha(), LeanFijo(), JuezDeObra(BIEN), version=2)
    assert e.ronda == 1, "la version 2 empieza su propia cuenta"
    assert veredictos.ultimo(con, "obra-x", 2)["ronda"] == 1
    assert veredictos.ultimo(con, "obra-x", 1)["ronda"] == 2


def test_la_version_2_no_hereda_las_rondas_gastadas_por_la_1(con):
    """La traza de `CE-15`: la 1 se publica en su primera ronda y la 2 se detenia por
    tope habiendo gastado una sola de las suyas."""
    _escrita(con)
    assert _publicar(con, LeanFijo(), Secuencia(BIEN), Editor(INSTRUYE_CAP10),
                     Reescritor()).publicada
    _version_2(con)
    p = publicacion.publicar(con, "obra-x", ficha(), LeanFijo(), Secuencia(ABRUPTO, BIEN),
                             Editor(INSTRUYE_CAP10), Reescritor(), tope=1, version=2)
    assert p.publicada and p.rondas == 2, p.parada


def test_la_migracion_da_la_version_1_a_los_veredictos_de_antes():
    """Una base de antes: `veredicto_de_publicacion` con clave `(obra, ronda)`. Antes de
    esta migracion ninguna regeneracion pudo escribir nada (`RAMAS` estaba vacio), asi
    que todo veredicto guardado es de la version 1."""
    c = sqlite3.connect(":memory:")
    c.executescript("""
        CREATE TABLE esquema_version (version INTEGER PRIMARY KEY, descripcion TEXT NOT NULL,
            aplicada_en TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE veredicto_de_publicacion (obra TEXT NOT NULL, ronda INTEGER NOT NULL,
            publica INTEGER NOT NULL, condiciones TEXT NOT NULL, codigo_lean INTEGER,
            no_ejecutadas TEXT NOT NULL, cuando TEXT NOT NULL DEFAULT (datetime('now')),
            PRIMARY KEY (obra, ronda));
        INSERT INTO veredicto_de_publicacion (obra, ronda, publica, condiciones,
            no_ejecutadas) VALUES ('obra-x', 1, 0, '[]', '[]'), ('obra-x', 2, 1, '[]', '[]');
    """)
    c.executemany("INSERT INTO esquema_version (version, descripcion) VALUES (?, 'x')",
                  [(n,) for n in range(1, 16)])
    c.commit()
    migraciones.migrar(c)
    assert veredictos.rondas(c, "obra-x", 1) == 2
    assert veredictos.ultimo(c, "obra-x", 1)["publica"] is True
    c.execute("INSERT INTO veredicto_de_publicacion (obra, version, ronda, publica, "
              "condiciones, no_ejecutadas) VALUES ('obra-x', 2, 1, 0, '[]', '[]')")
