"""`SPEC-33` `RF-18`, `PLAN-33` E5: cada turno de la entrevista deja su coste en la base.

El Entrevistador y el extractor del texto libre no pasan por el ciclo de escena, asi que su
coste no quedaba en ningun sitio de la base. Lo que la web ensena como gastado sale de
`gasto_de_delegacion`, y una entrevista tambien gasta.
"""

import json
import sqlite3

import pytest

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.db import migraciones
from app.commons.modelo import proveedor
from app.features.entrevista import repository as repo
from app.features.entrevista import service
from app.features.entrevista.tests.conftest import ficha_completa


@pytest.fixture
def con(monkeypatch):
    monkeypatch.setenv(proveedor.VARIABLES["ejecutable"], "claude-de-mentira")
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    repo.asegurar_tablas(c)
    return c


def _entrevistador(coste):
    respuesta = {"ficha": ficha_completa().model_dump(mode="json"), "pregunta": "¿Algo mas?"}
    sobre = {"type": "result", "result": json.dumps(respuesta), "usage": {}}
    if coste is not None:
        sobre["total_cost_usd"] = coste
    return proveedor.SesionDelegada(modelo="m", agente="entrevistador",
                                    ejecutar=lambda *a, **k: json.dumps(sobre))


def test_cada_turno_anota_el_coste_del_entrevistador_en_su_obra(con):
    e = service.crear(con)
    service.turno(con, e.id, "Irene", _entrevistador(0.0375), ReglasDeContradiccion(), 2026)
    assert con.execute("SELECT obra, agente, generacion, coste_usd FROM gasto_de_delegacion"
                       ).fetchall() == [(e.obra, "entrevistador", None, 0.0375)]


def test_un_turno_sin_coste_medido_anota_ausente(con):
    e = service.crear(con)
    service.turno(con, e.id, "Irene", _entrevistador(None), ReglasDeContradiccion(), 2026)
    assert con.execute("SELECT coste_usd FROM gasto_de_delegacion").fetchall() == [(None,)]


def test_un_doble_sin_anotador_sigue_funcionando(con):
    """Los dobles de las pruebas no son `SesionDelegada`: no se les exige nada."""

    class Doble:
        nombre = "doble"

        def llamar(self, prompt):
            return {"ficha": ficha_completa().model_dump(mode="json"), "pregunta": "¿Y?"}

    e = service.crear(con)
    service.turno(con, e.id, "Irene", Doble(), ReglasDeContradiccion(), 2026)
    assert con.execute("SELECT COUNT(*) FROM gasto_de_delegacion").fetchone()[0] == 0
