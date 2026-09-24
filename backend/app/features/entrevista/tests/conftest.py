"""Fichas de prueba. Datos **inventados** (`SPEC-25` `RF-22`).

Los nombres son distintos entre si a proposito: si el destinatario y la mascota
se llamaran igual, una prueba que confundiera los dos campos pasaria igual.
"""

import pytest

from app.commons.dominio.destinatario import FichaDeEntrevista


def ficha_completa(**cambios):
    datos = {
        "destinatario": {
            "nombre": "Irene Valdés", "edad": 34,
            "elementos": [
                {"tipo": "rasgo", "descripcion": "colecciona mapas antiguos",
                 "imprescindible": True},
                {"tipo": "recuerdo", "descripcion": "el viaje en tren a Lisboa",
                 "momento": {"edad": 20}, "imprescindible": True},
                {"tipo": "mascota", "descripcion": "un galgo muy lento",
                 "nombre": "Brisa", "relacion": "su perra"},
            ]},
        "ocasion": "cumpleanos", "genero": "aventura", "tono": "divertido",
        "extension": "media",
        "papel": "protagonista", "dedicatoria": "Para Irene, que siempre llega.",
        "titulo": "El mapa de Irene",
        "premisa": "Un mapa antiguo devuelve a Irene al tren de Lisboa.",
    }
    datos.update(cambios)
    return FichaDeEntrevista.model_validate(datos)


@pytest.fixture
def completa():
    return ficha_completa()
