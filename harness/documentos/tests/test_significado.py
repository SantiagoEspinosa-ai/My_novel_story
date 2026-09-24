"""`PLAN-22` E2 — lo que el contrato significa (`SPEC-22` `RF-34`, `RF-35`, `RF-57`, `VER-103`).

Que el congelado coincida con el backend (`VER-102`) no dice nada de si el contrato dice
algo: un `estado: str` coincide consigo mismo. Estas son las tres cosas que el contrato
tiene que decir para ser un contrato (Regla 5).
"""

from enum import Enum

from fastapi import FastAPI
from pydantic import BaseModel

import contrato


def _esquema(anotaciones):
    Respuesta = type("Respuesta", (BaseModel,), {"__annotations__": anotaciones})
    app = FastAPI(title="prueba", version="0")

    @app.get("/escenas/{id_escena}", response_model=Respuesta)
    def leer(id_escena: str):  # pragma: no cover
        return {}

    return app.openapi()


def test_un_estado_como_cadena_libre_en_el_congelado_es_un_fallo():
    fallos = contrato.comprobar_significado(_esquema({"id": str, "estado": str}))
    assert any("estado" in f and "enumeracion" in f for f in fallos), fallos


def test_un_campo_que_admite_numero_o_cadena_es_un_fallo():
    fallos = contrato.comprobar_significado(_esquema({"tokens": int | str}))
    assert any("tokens" in f and "dos lecturas" in f for f in fallos), fallos


def test_ningun_campo_del_congelado_se_llama_como_la_configuracion_del_sistema():
    fallos = contrato.comprobar_significado(_esquema({"techo_de_contexto": int}))
    assert any("techo_de_contexto" in f and "sistema.json" in f for f in fallos), fallos
    # Y el congelado de hoy no expone ninguno (`RF-57`).
    assert [f for f in contrato.comprobar_significado(contrato.leer_congelado())
            if "sistema.json" in f] == []


def test_los_literales_de_cada_enum_son_los_de_definitions():
    class EstadoDeEscena(str, Enum):
        PLANIFICADA = "planificada"
        TERMINADA = "terminada"      # inventado: no esta en definitions

    fallos = contrato.comprobar_significado(_esquema({"estado": EstadoDeEscena}))
    assert any("EstadoDeEscena" in f and "terminada" in f for f in fallos), fallos

    # El buen caso: los literales exactos de la tabla no dan fallo.
    from app.commons.dominio.enumeraciones import EstadoDeEscena as Real
    assert contrato.comprobar_significado(_esquema({"estado": Real})) == []


def test_el_congelado_de_hoy_significa_lo_que_dice():
    assert contrato.comprobar_significado(contrato.leer_congelado()) == []
