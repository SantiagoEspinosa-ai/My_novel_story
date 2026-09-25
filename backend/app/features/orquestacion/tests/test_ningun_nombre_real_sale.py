"""`PLAN-34` E7, `VER-134`: ningun nombre real sale (`SPEC-34` `RF-06`).

De la entrevista a la puerta de publicacion, con dobles: se guarda cada prompt que recibe un
agente, cada salida de las tres tools de la story bible y cada objeto que llega al
exportador de Langfuse, y no aparece ninguna palabra real de la ficha. Los dobles hacen lo
que haria el modelo: trabajan con los nombres que ven.

**Punto ciego** (el de la spec): un nombre que el comprador escribe sin declararlo.
Aqui todos se declaran en su campo.
"""

import json
import re
import sqlite3

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.db import migraciones
from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.commons.observabilidad.observacion import Observacion
from app.commons.politica import pseudonimos
from app.features.entrevista import repository as entrevistas
from app.features.entrevista import service
from app.features.entrevista.schemas import NombresEntrada
from app.features.evaluacion.tests import dobles
from app.features.orquestacion import novela
from app.features.orquestacion import story_bible as tools

REALES = ("Olivia", "Carranza", "Tino", "Ramón", "Marcos", "Ledesma")


class EntrevistadorQueCompleta:
    """Lee la ficha del prompt y la completa en un turno, con los nombres que ve."""

    nombre = "doble-entrevistador"

    def __init__(self, prompts):
        self.prompts = prompts

    def llamar(self, prompt):
        self.prompts.append(prompt)
        bloque = prompt.split("FICHA ACTUAL\n", 1)[1].split("\n\nLO QUE FALTA", 1)[0]
        f = json.loads(bloque)
        # `SPEC-40`: la ficha llega con el `protagonista`, y se devuelve igual.
        p = f["protagonista"]
        pila = p["nombre"].split()[0]
        mascota = next(e["nombre"] for e in p["elementos"] if e.get("nombre"))
        p["edad"] = 9
        p["elementos"] += [
            {"tipo": "rasgo", "descripcion": "colecciona piedras", "imprescindible": True},
            {"tipo": "recuerdo", "descripcion": "la tarde en que {0} aprendio a nadar".format(
                mascota), "imprescindible": True}]
        f.update({"ocasion": "cumpleanos", "genero": "aventura", "tono": "tierno",
                  "extension": "media", "papel": "protagonista",
                  "titulo": "Las piedras de {0}".format(pila),
                  "premisa": "{0} busca una piedra con su perro.".format(pila),
                  "dedicatoria": "Para {0}, de parte de quien la quiere.".format(pila)})
        return {"ficha": f, "pregunta": "¿Algo más sobre {0}?".format(pila)}


def _sin_nombres_reales(textos, donde):
    for texto in textos:
        for real in REALES:
            assert not re.search(r"(?<!\w){0}(?!\w)".format(real), texto), (donde, real,
                                                                          texto[:300])


def test_ningun_nombre_real_sale_hacia_agentes_tools_ni_langfuse(tmp_path):
    con = sqlite3.connect(str(tmp_path / "obra.db"))
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    entrevistas.asegurar_tablas(con)
    exportador = ExportadorEnMemoria()

    def observar(obra, nombre, c=None):
        return Observacion(exportador, con=c, obra=obra, nombre=nombre)

    # La entrevista: los nombres, en su campo; un turno del Entrevistador; cerrar.
    prompts = []
    e = service.crear(con)
    service.declarar_nombres(con, e.id, NombresEntrada.model_validate({
        "destinatario": "Olivia Carranza", "regalado_por": "Ramón",
        "otros": [{"nombre": "Tino", "tipo": "mascota", "relacion": "su perro"}],
        "vetados": ["Marcos Ledesma"]}), ReglasDeContradiccion(), 2026)
    service.turno(con, e.id, "Olivia tiene 9 años y Tino es su perro; nada de Marcos Ledesma",
                  EntrevistadorQueCompleta(prompts), ReglasDeContradiccion(), 2026,
                  observar=observar)
    ficha = service.cerrar(con, e.id)
    assert ficha.destinatario.nombre == "Olivia Carranza"
    assert ficha.nombres_vetados == ["Marcos Ledesma"]

    # La generacion: los dobles trabajan con la ficha como la veria el modelo.
    tabla = pseudonimos.asegurar(con, e.obra, ficha)
    vista = FichaDeEntrevista.model_validate_json(
        tabla.pseudonimizar(ficha.model_dump_json()).replace(
            json.dumps(pseudonimos.MARCA_DE_VETADO), '"X"'))
    r = novela.escribir(con, e.obra, ficha, dobles.agentes_para(vista, prompts),
                        carpeta_de_reglas=str(tmp_path), lean=dobles.LeanFijo(),
                        observacion=Observacion(exportador, con=con, obra=e.obra))
    assert r["generacion"].parada is None, r["generacion"].parada
    assert r["publicacion"] is not None

    # Las tools de la story bible, sobre la obra ya escrita.
    salidas = []
    from app.features.planificacion import repository as planes
    ids = [x.id for x in planes.aprobado(con, e.obra).mundo.personajes]
    for nombre, argumentos in ([("hechos", {}), ("cronologia", {})]
                               + [("ficha", {"id": i}) for i in ids]):
        salida = tools.atender(con, con, e.obra, "escritor", "del-1", nombre, argumentos)
        salidas.extend(c["text"] for c in salida["content"])

    assert len(prompts) > 10 and salidas and exportador.enviados
    _sin_nombres_reales(prompts, "prompt")
    _sin_nombres_reales(salidas, "tool")
    _sin_nombres_reales([json.dumps(o, ensure_ascii=False) for _, o in exportador.enviados],
                        "langfuse")
    # `SPEC-40` `RF-05`: ningun prompt habla del regalo, del destinatario ni del comprador.
    from app.commons.politica.vista_de_agentes import PALABRAS_DEL_REGALO
    for texto in prompts:
        m = PALABRAS_DEL_REGALO.search(texto)
        assert m is None, (m.group(), texto[max(0, m.start() - 150):m.end() + 150])
    # Y la base guarda los reales: la sustitucion es en la frontera, no en el canon.
    textos = " ".join(f[0] for f in con.execute("SELECT texto FROM borrador"))
    assert "Olivia" in textos
