"""Una obra para mirar la lectura web, con datos **inventados** y sin modelo (`PLAN-22` E11).

    cd backend && python -X utf8 semilla_lectura.py lectura-semilla.db

Monta la obra como la monta la novela regalo -`novela.montar` con una ficha y un plan
aprobado- y hace avanzar sus escenas **por las funciones del repositorio**, nunca con SQL
a mano: lo que la web enseñe tiene que ser la forma que dejan los que escriben. Deja una
escena de cada estado que la lectura tiene que distinguir: `consolidada`,
`aceptada_por_rendicion` con un hallazgo abierto, `generada` con un `sin_veredicto` y un
`menor`, y `planificada` sin texto.

NINGUN DATO ES DE NADIE
-----------------------
La ficha, los nombres, la dedicatoria y los textos son inventados y lo dicen. No se usan
bases reales (`regalo-real.db`, `regalo-prueba.db`, `obra10.db`): pueden tener los datos
de un destinatario de verdad (`PLAN-22` hallazgo 16).

Si la base ya tiene esta obra, **no escribe nada** y lo dice: volver a sembrar no puede
duplicar borradores ni hallazgos.
"""

import sys

from app.commons.configuracion.esquemas import PlanDeLaObra
from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela
from app.features.planificacion.service import PlanAprobado
from app.main import preparar_base

OBRA = "obra-semilla-inventada"
TITULO = "El faro de papel (obra inventada)"
DEDICATORIA = "Para una persona inventada, que no existe.\nDedicatoria de prueba."

FICHA = {
    "destinatario": {
        "nombre": "Persona Inventada", "edad": 40,
        "elementos": [
            {"tipo": "rasgo", "descripcion": "dibuja faros en servilletas (inventado)",
             "imprescindible": True},
        ]},
    "ocasion": "cumpleanos", "genero": "aventura", "tono": "tierno", "extension": "corta",
    "papel": "protagonista",
    "titulo": TITULO,
    "premisa": "Una persona inventada sigue un faro dibujado (premisa inventada).",
    "dedicatoria": DEDICATORIA,
}

_CAPITULOS = [
    ("cap-01", "lug-faro", "Llega al faro de papel."),
    ("cap-02", "lug-puerto", "Cruza el puerto de noche."),
    ("cap-03", "lug-faro", "Vuelve al faro con una pregunta."),
    ("cap-04", "lug-puerto", "Se despide en el puerto."),
]

PLAN = {
    "mundo": {
        "lugares": [{"id": "lug-faro", "nombre": "Faro inventado", "accesos": ["lug-puerto"]},
                    {"id": "lug-puerto", "nombre": "Puerto inventado", "accesos": ["lug-faro"]}],
        "personajes": [
            {"id": "per-inventada", "nombre": "Persona Inventada", "empieza_en": "lug-faro"},
            {"id": "per-farera", "nombre": "Farera Inventada", "empieza_en": "lug-faro"}]},
    "hechos": [{"id": "hec-faro", "enunciado": "El faro de papel existe (inventado)."}],
    "capitulos": [
        {"id": c, "escenas": [{"eje": "vinculo", "signo": "positivo", "lugar": lugar,
                               "pov": "per-inventada", "sinopsis": sinopsis,
                               "t_fabula": "2026-06-{0:02d}".format(n)}]}
        for n, (c, lugar, sinopsis) in enumerate(_CAPITULOS, 1)],
    "imprescindibles": [{"elemento": "dibuja faros en servilletas (inventado)",
                         "capitulo": "cap-01", "palabras_clave": ["faro"]}],
}

TEXTOS = {
    "cap-01-e1": ("Texto inventado del primer capitulo. La persona inventada llega al faro\n"
                  "de papel y lo dibuja en una servilleta.\n\nSegundo parrafo, tambien inventado."),
    "cap-02-e1": ("Primer intento inventado del segundo capitulo.",
                  "Segundo intento inventado: el puerto de noche, con  dos espacios."),
    "cap-03-e1": "Texto inventado del tercer capitulo, generado y sin revisar.",
}


def sembrar(ruta):
    """Monta la obra inventada en `ruta`. Devuelve `False` si ya estaba y no toca nada."""
    con = preparar_base(ruta)
    try:
        ficha = FichaDeEntrevista.model_validate(FICHA)
        aprobado = PlanAprobado(PlanDeLaObra.model_validate(PLAN), 1, TITULO, FICHA["premisa"])
        if not novela.montar(con, OBRA, ficha, aprobado):
            return False
        # cap-01: generada -> aceptada -> consolidada.
        v = escaleta.guardar_borrador(con, "cap-01-e1", TEXTOS["cap-01-e1"], "semilla", "s1")
        escaleta.aceptar_borrador(con, "cap-01-e1", version=v, rindiendose=False)
        escaleta.marcar_consolidada(con, "cap-01-e1")
        # cap-02: dos intentos, un mayor abierto y rendida en el primero.
        v1 = escaleta.guardar_borrador(con, "cap-02-e1", TEXTOS["cap-02-e1"][0], "semilla", "s2")
        escaleta.guardar_borrador(con, "cap-02-e1", TEXTOS["cap-02-e1"][1], "semilla", "s3")
        escaleta.guardar_hallazgo(con, "INV-17", "regla", "cap-02-e1", Severidad.MAYOR,
                                  EH.ABIERTO, "La longitud queda fuera de rango (inventado).")
        escaleta.rendir_escena(con, "cap-02-e1", v1)
        escaleta.marcar_consolidada(con, "cap-02-e1")
        # cap-03: generada, con un sin_veredicto y un menor abiertos.
        escaleta.guardar_borrador(con, "cap-03-e1", TEXTOS["cap-03-e1"], "semilla", "s4")
        escaleta.guardar_hallazgo(con, "INV-27", "juez_llm", "cap-03-e1", Severidad.MAYOR,
                                  EH.SIN_VEREDICTO, "El juez no contesto (inventado).")
        escaleta.guardar_hallazgo(con, "INV-15", "regla", "cap-03-e1", Severidad.MENOR,
                                  EH.ABIERTO, "La voz se aleja de las anclas (inventado).")
        # cap-04: planificada, sin ningun borrador.
        return True
    finally:
        con.close()


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("uso: python -X utf8 semilla_lectura.py RUTA.db")
        sys.exit(2)
    if sembrar(sys.argv[1]):
        print("obra {0} sembrada en {1} (datos inventados)".format(OBRA, sys.argv[1]))
    else:
        print("la base {0} ya tiene la obra {1}: no se ha escrito nada".format(sys.argv[1], OBRA))
