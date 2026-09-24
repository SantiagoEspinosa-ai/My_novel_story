"""`PLAN-29` E9: el limite de `SPEC-29`, comprobado (`RF-07`).

Una entrevista con datos de destinatario **inventados y unicos**, dos turnos, un texto
libre, y una novela entera con dobles que **meten esos datos** en el plan, en el texto, en
el resumen, en la justificacion del Editor y en el juicio de la obra; todo contra
`ExportadorEnMemoria`. Despues se busca cada dato en lo que se habria enviado: tal cual,
en minusculas, sin acentos y por nombre de pila.

**Punto ciego**, el de `VER-69`: busca cadenas concretas. No ve un dato transformado
—resumido, traducido, parafraseado— ni lo que el SDK real añada por su cuenta; eso lo mira
`PLAN-29` E13 en la interfaz de Langfuse. Y no busca la edad: es un numero, y los numeros
coinciden legitimamente con tokens y latencias. Que no suba lo garantizan los tipos, que
no tienen ningun campo donde ponerla.
"""

import json
import re
import sqlite3
import unicodedata

import pytest

from app.commons.configuracion.esquemas import ReglasDeContradiccion
from app.commons.db import migraciones
from app.commons.dominio.destinatario import FichaDeEntrevista
from app.commons.modelo.doble import DELTA_OK
from app.commons.observabilidad import envio
from app.commons.observabilidad.exportador import ExportadorEnMemoria
from app.commons.observabilidad.observacion import Observacion
from app.features.auditoria.publicacion import ResultadoLean
from app.commons.politica import auditoria
from app.features.entrevista import repository as repo_entrevista
from app.features.entrevista import service as entrevista
from app.features.orquestacion import novela
from app.features.planificacion.tests.conftest import FICHA, plan_dict

# De lo que hay en los fixtures a lo que se busca. Cada dato, distinto de todo lo demas.
SUSTITUCIONES = [
    ("Irene Valdés", "Zenobia Quiñónez"), ("Irene", "Zenobia"), ("irene", "zenobia"),
    ("colecciona mapas antiguos", "colecciona dedales de ámbar"), ("mapa", "dedal"),
    ("el viaje en tren a Lisboa", "el globo sobre Tordesillas"), ("tren", "globo"),
    ("Lisboa", "Tordesillas"), ("un galgo muy lento", "un ajolote tuerto"),
    ("Brisa", "Pimpollo"), ("canta mal", "silba valses"), ("hospital", "berenjenal"),
    ("Tomas Ferrer", "Casimiro Olabarrieta"),
]
DEDICATORIA = "Para Zenobia, que nunca duerme la siesta."
TEXTO_LIBRE = "Vivió dos años en Ushuaia con su tía Remedios."
HECHO_PROPUESTO = "vivió en Ushuaia con su tía Remedios"

DATOS = ["Zenobia Quiñónez", "dedales de ámbar", "globo sobre Tordesillas", "Tordesillas",
         "ajolote tuerto", "Pimpollo", "silba valses", "berenjenal", "Casimiro Olabarrieta",
         DEDICATORIA, "Ushuaia", "Remedios",
         # Por nombre de pila, que es como un texto nombra a alguien.
         "Zenobia", "Casimiro"]


def _sustituir(obj):
    texto = json.dumps(obj, ensure_ascii=False)
    for viejo, nuevo in SUSTITUCIONES:
        texto = texto.replace(viejo, nuevo)
    return json.loads(texto)


def _ficha():
    return FichaDeEntrevista.model_validate(_sustituir(dict(FICHA, dedicatoria=DEDICATORIA)))


def _sin_acentos(t):
    return "".join(c for c in unicodedata.normalize("NFD", t)
                   if unicodedata.category(c) != "Mn").lower()


class _Fijo:
    def __init__(self, r):
        self.r, self.nombre = r, "doble"
        self.reglas, self.entorno, self.herramientas = None, {}, None

    def llamar(self, prompt):
        return self.r


class _Escritor(_Fijo):
    """El primer intento lleva la vetada y el nombre vetado, para que `INV-21` dispare;
    los siguientes, todos los datos del destinatario."""

    def __init__(self):
        super().__init__(None)
        self.llamadas = 0

    def llamar(self, prompt):
        self.llamadas += 1
        pov = re.search(r"[\w-]*per-zenobia", prompt)
        extra = (["berenjenal", "Casimiro", "Olabarrieta"] if self.llamadas == 1 else
                 ["Zenobia", "Quiñónez", "dedal", "globo", "Tordesillas", "Pimpollo",
                  "Ushuaia", "Remedios"] + DEDICATORIA.split())
        return {"texto": " ".join(["palabra"] * (1200 - len(extra)) + extra),
                "pov_usado": pov.group(0) if pov else "per-zenobia", "delta": DELTA_OK}


class _Editor(_Fijo):
    def __init__(self):
        super().__init__(None)

    def llamar(self, prompt):
        justificacion = "Zenobia Quiñónez y Pimpollo en Tordesillas: bien."
        if "RESUMENES DE LOS CAPITULOS" in prompt:
            return {"arco_cerrado": True, "final_abrupto": False,
                    "justificacion": justificacion}
        return {"valoraciones": [
            {"criterio": c, "nota": 4, "justificacion": justificacion} for c in
            ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")]}


class _Lean:
    def verificar(self, con, obra):
        return ResultadoLean(0)


@pytest.fixture
def enviado(tmp_path):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    repo_entrevista.asegurar_tablas(con)
    auditoria.asegurar_tabla(con)
    exportador = ExportadorEnMemoria()

    def observar(obra, nombre, con_=None):
        return Observacion(exportador, con=con, obra=obra, nombre=nombre)

    ficha = _ficha()
    t = entrevista.crear(con)
    respuesta = {"ficha": ficha.model_dump(mode="json"),
                 "pregunta": "¿Zenobia prefiere Tordesillas o Ushuaia?"}
    for frase in ("Se llama Zenobia Quiñónez y tiene un ajolote tuerto.",
                  DEDICATORIA):
        entrevista.turno(con, t.id, frase, _Fijo(respuesta), ReglasDeContradiccion(),
                         anio_actual=2026, observar=observar)
    entrevista.pegar_texto(con, t.id, TEXTO_LIBRE, _Fijo({"hechos": [HECHO_PROPUESTO]}),
                           observar=observar)

    plan = _sustituir(plan_dict())
    agentes = {"planificador": _Fijo({"titulo": ficha.titulo, "premisa": ficha.premisa,
                                      "plan": plan}),
               "revisor": _Fijo({"aprobado": True, "objeciones": []}),
               "escritor": _Escritor(), "editor": _Editor(),
               "resumidor": _Fijo({"texto": "Zenobia Quiñónez vuelve a Tordesillas con "
                                            "Pimpollo. " * 3, "hechos_clave": []})}
    r = novela.escribir(con, t.obra, ficha, agentes, carpeta_de_reglas=str(tmp_path),
                        lean=_Lean(), observacion=observar(t.obra, "generacion"))
    assert r["generacion"].parada is None, r["generacion"].parada
    assert r["publicacion"] is not None
    return exportador.enviados


def test_la_prueba_ejercita_lo_que_dice(enviado):
    """Sin esto, una prueba del limite que no enviara nada pasaria sola."""
    tipos = {t for t, _ in enviado}
    assert tipos == {"traza", "span", "score", "prompt"}
    nombres = {e["nombre"] for t, e in enviado if t == "score"}
    assert {"INV-21", "INV-22", "INV-23", "INV-24", "INV-27", "schema"} <= nombres
    vetadas = [e for t, e in enviado if t == "score" and e["nombre"] == "INV-21"
               and e["categoria"] == "falla"]
    assert vetadas, "la vetada de novela tiene que haber disparado"
    trazas = [e["nombre"] for t, e in enviado if t == "traza"]
    assert trazas.count("turno_de_entrevista") == 2 and "generacion" in trazas


def test_nada_del_destinatario_sube_a_langfuse(enviado):
    todo = json.dumps(enviado, ensure_ascii=False)
    normalizado = _sin_acentos(todo)
    for dato in DATOS:
        assert dato not in todo, dato
        assert dato.lower() not in todo.lower(), dato
        assert _sin_acentos(dato) not in normalizado, dato


MODELOS = {"traza": envio.TrazaEnviada, "span": envio.SpanEnviado,
           "score": envio.ScoreEnviado, "prompt": envio.VersionDePrompt}


def test_todo_lo_que_sube_tiene_solo_campos_de_la_lista(enviado):
    """Para que un campo añadido en el futuro no se cuele sin pasar por `envio.py`."""
    for tipo, e in enviado:
        modelo = MODELOS[tipo]
        assert set(e) <= set(modelo.model_fields), (tipo, set(e) - set(modelo.model_fields))
        modelo.model_validate(e)
