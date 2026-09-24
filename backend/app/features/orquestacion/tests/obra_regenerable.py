"""Una obra de prueba para `PLAN-23`: capitulos de una escena, consolidados o no.

Datos inventados. Los identificadores de obra, capitulo y escena son distintos a
proposito entre si (`una prueba que pasa por coincidencia`): el capitulo `obra-a-c2`
no se llama como su escena `obra-a-c2-e1`, y dos obras no comparten capitulos.
"""

import sqlite3

from app.commons.db import migraciones, procedencia
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.features.brief import repository as brief
from app.features.consolidacion import aplicar, deltas, memoria, mundo
from app.features.cronologia import repository as cronologia
from app.features.escaleta import repository as escaleta

COMMIT = "abc1234"


def conexion():
    con = sqlite3.connect(":memory:")
    migraciones.migrar(con)
    for m in (escaleta, aplicar, deltas, cronologia, memoria, mundo, brief):
        m.asegurar_tablas(con)
    return con


def obra(con, id_obra="obra-a", capitulos=3, commit=COMMIT, hechos=(),
         presentes=None):
    """Da de alta la obra con `capitulos` capitulos de una escena, sin escribir.

    `hechos` son pares `(id, enunciado)`. `presentes` es `{n: [personajes]}`."""
    ids = ["{0}-c{1}".format(id_obra, n) for n in range(1, capitulos + 1)]
    brief.alta_de_obra(con, id_obra, {"titulo": "Titulo de prueba",
                                      "premisa": "Premisa de prueba"}, ids)
    escaleta.guardar_escaleta(con, id_obra, [{
        "id": "{0}-e1".format(c), "orden": 1, "capitulo": c,
        "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
        "beats": [{"id": "{0}-b1".format(c), "texto": "sinopsis de {0}".format(c)}],
        "pov": "per-ana", "lugar": "lug-casa", "t_discurso": n,
        "personajes_presentes": (presentes or {}).get(n)}
        for n, c in enumerate(ids, 1)])
    if hechos:
        escaleta.declarar_hechos(con, id_obra, [{"id": h, "enunciado": e} for h, e in hechos])
    if commit is not None:
        procedencia.registrar(con, version=commit)
    return ids


def escena_de(capitulo):
    return "{0}-e1".format(capitulo)


def escribir(con, escena, texto, delta=None):
    """Un borrador consolidado: su delta aplicado y guardado **con su version**."""
    version = escaleta.guardar_borrador(con, escena, texto, "doble", "hash")
    aplicar.consolidar(con, escena, delta or {}, version=version)
    escaleta.marcar_consolidada(con, escena)
    return version


def usar(con, hecho, capitulo, tipo=TipoDeUsoDeHecho.MENCIONA, origen=OrigenDeUso.REGLA,
         escena=None):
    cronologia.registrar_usos(con, [{
        "hecho": hecho, "escena": escena or escena_de(capitulo), "capitulo": capitulo,
        "tipo": tipo, "origen": origen}])
