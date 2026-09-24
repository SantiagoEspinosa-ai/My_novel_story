"""Una ficha y un plan valido de 10 capitulos. Datos **inventados**.

El plan se construye a partir de la ficha para que la prueba de cobertura mida
la relacion entre los dos, no la casualidad de dos fixtures que coinciden.
"""

from app.commons.configuracion.esquemas import PlanDeLaObra
from app.commons.dominio.destinatario import FichaDeEntrevista

FICHA = {
    "destinatario": {
        "nombre": "Irene Valdés", "edad": 34,
        "elementos": [
            {"tipo": "rasgo", "descripcion": "colecciona mapas antiguos",
             "imprescindible": True},
            {"tipo": "recuerdo", "descripcion": "el viaje en tren a Lisboa",
             "momento": {"edad": 20}, "imprescindible": True},
            {"tipo": "mascota", "descripcion": "un galgo muy lento",
             "nombre": "Brisa", "relacion": "su perra", "imprescindible": True},
            {"tipo": "rasgo", "descripcion": "canta mal", "imprescindible": False},
        ]},
    "ocasion": "cumpleanos", "genero": "aventura", "tono": "divertido",
    "extension": "media",
    "papel": "protagonista", "vetadas": ["hospital"],
    "nombres_vetados": ["Tomas Ferrer"],
    "titulo": "El mapa de Irene",
    "premisa": "Un mapa heredado lleva a Irene de vuelta a Lisboa.",
}


def ficha(**cambios):
    return FichaDeEntrevista.model_validate(dict(FICHA, **cambios))


def plan_dict():
    capitulos = [{"id": "cap-{0:02d}".format(n), "titulo": "Capitulo {0}".format(n),
                  "escenas": [{"eje": "vinculo", "signo": "positivo",
                               "lugar": "lug-casa", "pov": "per-irene",
                               "sinopsis": "Irene sigue un mapa.",
                               "t_fabula": "2026-06-{0:02d}".format(n)}]}
                 for n in range(1, 11)]
    return {
        "mundo": {
            "lugares": [{"id": "lug-casa", "nombre": "Casa", "accesos": []}],
            "personajes": [
                {"id": "per-irene", "nombre": "Irene Valdés", "empieza_en": "lug-casa",
                 "fecha_de_nacimiento": "1992-03-14"},
                {"id": "per-brisa", "nombre": "Brisa", "empieza_en": "lug-casa"}]},
        "capitulos": capitulos,
        "imprescindibles": [
            {"elemento": "colecciona mapas antiguos", "capitulo": "cap-01",
             "palabras_clave": ["mapa"]},
            {"elemento": "el viaje en tren a Lisboa", "capitulo": "cap-04",
             "palabras_clave": ["tren", "Lisboa"]},
            {"elemento": "un galgo muy lento", "capitulo": "cap-02",
             "palabras_clave": ["Brisa"]}],
    }


def plan(**cambios):
    return PlanDeLaObra.model_validate(dict(plan_dict(), **cambios))
