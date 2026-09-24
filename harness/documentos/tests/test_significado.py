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


# --- `PLAN-22` E14: el trabajo tiene forma (`VER-110`) ------------------------------------

def test_los_estados_de_un_trabajo_se_leen_de_architecture_y_no_de_definitions():
    """`estado_de_trabajo` es infraestructura y se declara en `docs/architecture.md` §
    "Los estados de un trabajo" (`docs/definitions.md` lo avisa). Se lee **del
    documento**, como los del dominio: comparar con el `Enum` del backend seria
    comparar el backend consigo mismo (Regla 3)."""
    vocabularios = contrato.vocabularios_de_definitions()
    assert vocabularios["estado_de_trabajo"] == [
        "en_cola", "esperando_presupuesto", "en_curso", "terminado", "fallido",
        "abandonado", "detenido_por_presupuesto"]

    class EstadoDeTrabajo(str, Enum):
        EN_COLA = "en_cola"
        PERDIDO = "perdido"          # inventado: no esta en architecture

    fallos = contrato.comprobar_significado(_esquema({"estado": EstadoDeTrabajo}))
    assert any("EstadoDeTrabajo" in f and "perdido" in f for f in fallos), fallos


def test_el_trabajo_tiene_forma_en_el_congelado():
    """`GET /trabajos/{id}` gana `response_model` (`PLAN-22` hallazgo 9): sin el, el
    congelado decia «cualquier cosa» y seguir una peticion (`RF-48`) no tenia contrato."""
    congelado = contrato.leer_congelado()
    respuesta = congelado["paths"]["/trabajos/{id_trabajo}"]["get"]["responses"]["200"]
    ref = respuesta["content"]["application/json"]["schema"]["$ref"]
    esquema = congelado["components"]["schemas"][ref.rsplit("/", 1)[1]]
    assert set(esquema["properties"]) == {
        "id", "tipo", "estado", "resultado", "motivo", "volvio_tras_abandono"}
    assert esquema["properties"]["estado"]["$ref"].endswith("/EstadoDeTrabajo")
    assert congelado["components"]["schemas"]["EstadoDeTrabajo"]["enum"] == \
        contrato.vocabularios_de_definitions()["estado_de_trabajo"]
