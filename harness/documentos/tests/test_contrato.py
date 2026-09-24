"""`PLAN-22` E1 — el contrato congelado y su validador (`SPEC-22` `RF-31`..`RF-33`, `VER-102`).

El congelado se **deriva** del backend (`DF-3`) y cualquier diferencia es un fallo, no un
aviso, con **operacion**, **campo** y **direccion** (`RF-32`).
"""

from fastapi import FastAPI
from pydantic import BaseModel

import contrato


def _app_con(campos):
    """Una API minima cuya respuesta tiene exactamente `campos`."""
    Respuesta = type("Respuesta", (BaseModel,), {"__annotations__": {c: str for c in campos}})
    app = FastAPI(title="prueba", version="0")

    @app.get("/cosas/{id_cosa}", response_model=Respuesta)
    def leer(id_cosa: str):  # pragma: no cover - solo se genera el esquema
        return {}

    return app


def test_quitar_un_campo_de_una_respuesta_falla_y_dice_operacion_campo_y_direccion():
    congelado = _app_con(["id", "titulo"]).openapi()
    actual = _app_con(["id"]).openapi()
    diferencias = contrato.comparar(congelado, actual)
    assert diferencias, "quitar un campo tiene que ser una diferencia"
    quitado = [d for d in diferencias if d.direccion == contrato.QUITADO
               and d.campo.endswith("/properties/titulo")]
    assert quitado, [str(d) for d in diferencias]
    d = quitado[0]
    assert "GET /cosas/{id_cosa}" in d.operacion
    assert d.campo == "/components/schemas/Respuesta/properties/titulo"
    texto = str(d)
    assert "GET /cosas/{id_cosa}" in texto and "titulo" in texto and "quitado" in texto


def test_anadir_una_ruta_es_una_diferencia_y_no_un_aviso():
    congelado = _app_con(["id"]).openapi()
    app = _app_con(["id"])

    @app.post("/cosas")
    def crear():  # pragma: no cover
        return {}

    diferencias = contrato.comparar(congelado, app.openapi())
    anadidas = [d for d in diferencias if d.direccion == contrato.ANADIDO]
    assert any(d.operacion == "POST /cosas" for d in anadidas), [str(d) for d in diferencias]
    assert contrato.codigo_de_salida(diferencias) == 1


def test_dos_generaciones_seguidas_son_identicas_byte_a_byte():
    assert contrato.serializar(contrato.generar()) == contrato.serializar(contrato.generar())


def test_el_congelado_del_repositorio_coincide_con_el_backend_de_hoy():
    congelado = contrato.leer_congelado()
    diferencias = contrato.comparar(congelado, contrato.generar())
    assert diferencias == [], "\n".join(str(d) for d in diferencias)
    assert contrato.RUTA_CONGELADO.read_bytes().decode("utf-8") == \
        contrato.serializar(contrato.generar())
