"""`PLAN-23` Parte B, rama `S-1`: la salida fijada por la medida y la cascada.

Ningun paso llama al modelo real: los agentes son dobles con la misma forma que los de
`novela_regalo.agentes` (un `llamar(prompt)` que devuelve un diccionario). Datos
inventados.
"""

import json
import os

from app.features.orquestacion import arrastre, regeneracion

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))))
MEDIDA = os.path.join(RAIZ, "harness", "evals", "arrastre-SPEC-23.json")


# --- B2 · la salida, fijada con el numero y no con una opinion ---------------------

def test_la_salida_fijada_es_la_que_da_la_regla_con_el_numero_guardado():
    """Si alguien cambia `SALIDA` sin cambiar la medida -o la medida sin `SALIDA`-,
    falla. El numero es el de B1, guardado en el repositorio."""
    with open(MEDIDA, encoding="utf-8") as f:
        medida = json.load(f)
    assert medida["medido"] is True, "sin medida no se elige salida (`SPEC-23` v2)"
    assert medida["umbral"] == arrastre.UMBRAL_DE_CAPITULOS
    assert regeneracion.SALIDA == arrastre.salida_para(medida["arrastre_medio"])
    assert regeneracion.SALIDA == medida["salida"]


# --- B-S1.1, `F-121` (TLC `CE-14`): el lector solo ve versiones publicadas ---------

from app.features.auditoria import publicacion as puerta  # noqa: E402
from app.features.auditoria import repository as veredictos  # noqa: E402
from app.features.brief import repository as brief  # noqa: E402
from app.features.manuscrito import exportar  # noqa: E402
from app.features.orquestacion.tests import obra_regenerable as o  # noqa: E402


def _publicar_version(con, obra, numero, publica=True):
    rendidos = [] if publica else ["cualquiera"]
    veredictos.guardar(con, obra, puerta.decidir(rendidos, [], puerta.ResultadoLean(0)), 0,
                       numero)


def _con_version_2():
    con = o.conexion()
    caps = o.obra(con)
    brief.crear_version(con, "obra-a", caps[:2] + ["obra-a-c3-v2"], anterior=1)
    return con, caps


def test_la_version_vigente_es_la_ultima_publicada_y_no_la_ultima_creada():
    """La traza de `CE-14`: publicada la 1, se pide un cambio y se crea la 2 antes de
    escribirla. El lector seguia viendo la 2, con capitulos sin escribir."""
    con, caps = _con_version_2()
    _publicar_version(con, "obra-a", 1)
    assert brief.version_vigente(con, "obra-a") == 1
    assert brief.leer(con, "obra-a")["capitulos"] == caps
    assert [c.id for c in exportar.capitulos_de(con, "obra-a")] == caps
    assert [e["capitulo"] for e in regeneracion.escenas_de_version(con, "obra-a")] == caps
    _publicar_version(con, "obra-a", 2, publica=False)
    assert brief.version_vigente(con, "obra-a") == 1, "una puerta que no abre no publica"
    _publicar_version(con, "obra-a", 2)
    assert brief.version_vigente(con, "obra-a") == 2


def test_sin_ninguna_version_publicada_la_vigente_es_la_1():
    """Antes de la primera publicacion lo que se escribe es la 1, y es la que se lee."""
    con, caps = _con_version_2()
    assert brief.version_vigente(con, "obra-a") == 1
    assert [c.id for c in exportar.capitulos_de(con, "obra-a")] == caps
