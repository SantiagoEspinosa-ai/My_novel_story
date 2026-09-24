"""Una base para mirar la novela regalo en la web, con datos **inventados** y sin modelo
(`PLAN-33` E15, `VER-133`).

    cd backend && python -X utf8 semilla_regalo.py regalo-semilla.db

Deja una obra publicada, una a medio escribir (dos capitulos consolidados con sus notas del
Editor, una bajo el umbral, el 3 editando y una delegacion sin coste), una entrevista a
medias con un aviso y una contradiccion en su turno, y una entrevista cerrada lista para
confirmar. Despues, `uvicorn` con `HARNESS_BASE` y `npm run dev`, y el recorrido de
`frontend/scripts/recorrido-regalo.mjs`.

**A diferencia de `semilla_lectura.py`**, la obra, sus capitulos y escenas, el progreso y
las notas se escriben **por SQL**, como las pruebas de `features/regalo/`: esto enseña lo
que la web pinta de unas tablas dadas, no la forma que deja el pipeline. La forma real la
ensena `F-200`, que no salio de ninguna semilla. Ningun dato es de nadie: la ficha es la de
las pruebas de la entrevista. No se usa ninguna base real.
"""
import json
import sqlite3
import sys

sys.path.insert(0, ".")
from app.commons.modelo import gasto  # noqa: E402
from app.features.entrevista import repository as entrevistas  # noqa: E402
from app.features.entrevista.tests.conftest import ficha_completa  # noqa: E402
from app.main import preparar_base  # noqa: E402

CRITERIOS = ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")
ruta = sys.argv[1]
con = preparar_base(ruta)


def obra(id_obra, titulo, dedicatoria):
    with con:
        con.execute("INSERT INTO obra (id, titulo, premisa, dedicatoria) VALUES (?, ?, ?, ?)",
                    (id_obra, titulo, "Premisa inventada.", dedicatoria))
        for n in range(1, 11):
            cap = "{0}-cap-{1:02d}".format(id_obra, n)
            con.execute("INSERT INTO capitulo (id, obra, orden, estado) VALUES (?, ?, ?, "
                        "'abierto')", (cap, id_obra, n))
            con.execute("INSERT INTO escena (id, obra, orden, estado, cambio_de_valor, beats, "
                        "pov, lugar, capitulo) VALUES (?, ?, 1, 'planificada', '{}', '[]', "
                        "'per-x', 'lug-x', ?)", (cap + "-e1", id_obra, cap))


def fase(id_obra, f, capitulo=None, motivo=None):
    with con:
        con.execute("INSERT INTO progreso_de_generacion (obra, fase, capitulo, "
                    "total_de_capitulos, motivo) VALUES (?, ?, ?, 10, ?)",
                    (id_obra, f, capitulo, motivo))


def notas(id_obra, n, valores, instruccion=""):
    esc = "{0}-cap-{1:02d}-e1".format(id_obra, n)
    with con:
        for c, v in zip(CRITERIOS, valores):
            con.execute("INSERT INTO valoracion_del_editor (escena, version, criterio, nota, "
                        "justificacion, instruccion) VALUES (?, 1, ?, ?, ?, ?)",
                        (esc, c, v, "Justificacion inventada sobre " + c.replace("_", " ") + ".",
                         instruccion if v < 3 else ""))
        con.execute("UPDATE escena SET estado='consolidada', borrador_aceptado=1 WHERE id=?", (esc,))


def entrevista(id_obra, cerrada, turnos=()):
    e = entrevistas.crear(con, id_obra)
    e.ficha = ficha_completa()
    e.cerrada = cerrada
    entrevistas.guardar(con, e)
    for respuesta, pregunta, estado in turnos:
        entrevistas.guardar(con, e, respuesta=respuesta, pregunta=pregunta, estado=estado)
    return e


# 1. Publicada.
obra("obra-publicada", "El mapa de Irene", "Para Irene, que siempre llega.")
entrevista("obra-publicada", True)
for n in range(1, 11):
    fase("obra-publicada", "escribiendo", n)
    notas("obra-publicada", n, (4, 5, 4, 4, 4, 5))
fase("obra-publicada", "publicada")
g = gasto.anotador(con, "obra-publicada", "gen-inventada-1")
for _ in range(30):
    g("escritor", 0.41)

# 2. A medio escribir: dos cerrados con notas, el 3 editando.
obra("obra-en-curso", "La casa del faro", "A Tomás, que encendía la luz.")
entrevista("obra-en-curso", True)
fase("obra-en-curso", "planificando")
fase("obra-en-curso", "revisando_plan")
for n in (1, 2):
    fase("obra-en-curso", "escribiendo", n)
    fase("obra-en-curso", "editando", n)
    fase("obra-en-curso", "resumiendo", n)
notas("obra-en-curso", 1, (4, 4, 5, 4, 3, 5))
notas("obra-en-curso", 2, (4, 3, 4, 4, 2, 4), instruccion="Acelera el final del capitulo.")
fase("obra-en-curso", "escribiendo", 3)
fase("obra-en-curso", "editando", 3)
g = gasto.anotador(con, "obra-en-curso", "gen-inventada-2")
for agente, c in (("planificador", 0.52), ("revisor_plan", 0.18), ("escritor", 0.44),
                  ("editor", 0.21), ("resumidor", 0.07), ("escritor", 0.47),
                  ("editor", None), ("resumidor", 0.06), ("escritor", 0.45)):
    g(agente, c)

# 3. Entrevista a medias, con un aviso y una contradiccion en su turno.
entrevista("obra-a-medias", False, turnos=[
    ("Se llama Nerea y cumple 41", "¿Quién es Nora Quintana?", {
        "tema": "el nombre vetado", "falta": ["ocasion"],
        "avisos": ["el nombre vetado «Nora Quintana» comparte nombre de pila con «Nora» (mascota)"],
        "contradicciones_abiertas": [{"tipo": "edad_y_genero",
                                      "descripcion": "el romance pide al menos 12 años"}]}),
    ("Nora es otra persona", "¿Qué ocasión celebra el regalo?", {
        "tema": None, "falta": ["ocasion"], "avisos": [], "contradicciones_abiertas": []}),
])

# 4. Entrevista cerrada y sin generacion: la que ofrece escribir la novela.
entrevista("obra-lista", True)
con.close()
print("sembrada", ruta)
