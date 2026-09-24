"""`PLAN-23` Parte B, rama `S-1`: la salida fijada por la medida y la cascada.

Ningun paso llama al modelo real: los agentes son dobles con la misma forma que los de
`novela_regalo.agentes` (un `llamar(prompt)` que devuelve un diccionario). Datos
inventados.
"""

import json
import os
import sqlite3

import pytest

from app.commons.db import migraciones
from app.commons.dominio.enumeraciones import EstadoDeVerificacion as EV
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.commons.modelo.doble import DELTA_OK
from app.commons.trabajos import cola
from app.features.auditoria import publicacion as puerta
from app.features.auditoria import repository as veredictos
from app.features.brief import repository as brief
from app.features.cronologia import repository as usos
from app.features.entrevista import repository as entrevistas
from app.features.escaleta import repository as escaleta
from app.features.manuscrito import exportar
from app.features.orquestacion import arrastre, cascada, novela, regeneracion
from app.features.orquestacion.obra import _texto_elegido
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.orquestacion.tests.test_novela import (
    BIEN, _EditorDeLaPuerta, _EscritorQueCopiaElPov, _LeanFijo,
    _agentes_para_la_novela_entera)
from app.features.planificacion.tests.conftest import ficha
from app.features.revision import repository as peticiones

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


# --- B-S1.1 · la cascada, con una novela entera escrita con dobles ----------------

OBRA = "obra-x"
CAPS = ["obra-x-cap-{0:02d}".format(n) for n in range(1, 11)]
NUEVOS = CAPS[:2] + ["{0}-v2".format(c) for c in CAPS[2:]]
MARCA = "reescrito"


class _EscritorDeLaVersion(_EscritorQueCopiaElPov):
    """Como el de la novela, con una marca en el texto -para saber que capitulo es de la
    version nueva- y el nombre de la perra que el prompt le pida: si el prompt dice
    «Nala», escribe «Nala», como haria el modelo. Desde la llamada `rompe_desde` devuelve
    un delta en el que la perra actua sobre un hecho que no conoce: `INV-03` es
    bloqueante, y la escena se para. Con `con`, apunta la vigente en cada llamada."""

    def __init__(self, rompe_desde=None, con=None):
        super().__init__({"pov_usado": "per-irene", "delta": DELTA_OK})
        self.rompe_desde, self.con, self.vigentes = rompe_desde, con, []

    def llamar(self, prompt):
        r = super().llamar(prompt)
        if self.con is not None:
            self.vigentes.append(brief.version_vigente(self.con, OBRA))
        perra = "Nala" if "Nala" in prompt else "Brisa"
        r = dict(r, texto=" ".join(["palabra"] * 1195 + [
            "Irene", "mapa", "tren", "Lisboa", perra, MARCA]))
        if self.rompe_desde is not None and len(self.llamadas) >= self.rompe_desde:
            r["delta"] = dict(DELTA_OK, acciones=[
                {"personaje": "obra-x-per-brisa", "hecho": "obra-x-h-que-nadie-sabe"}])
        return r


def _agentes(escritor=None):
    """Los de la novela entera, con un Editor que tambien sabe juzgar la obra entera
    (bien a la primera): sin el, la puerta no publica ni la version 1."""
    a = _agentes_para_la_novela_entera()
    a["editor"] = _EditorDeLaPuerta(a["editor"].r, juicios=[BIEN])
    if escritor is not None:
        a["escritor"] = escritor
    return a


def _base(con_ficha=True, tmp=None):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    migraciones.migrar(con)
    r = novela.escribir(con, OBRA, ficha(), _agentes(), carpeta_de_reglas=tmp,
                        lean=_LeanFijo())
    assert r["publicacion"].publicada, r["publicacion"].parada
    # El imprescindible del tren, usado por `depende` en los capitulos 3 y 6: la cascada
    # empieza en el 3.
    usos.registrar_usos(con, [
        {"hecho": "imp-02", "escena": "{0}-e1".format(CAPS[n]), "capitulo": CAPS[n],
         "tipo": TipoDeUsoDeHecho.DEPENDE, "origen": OrigenDeUso.DELTA} for n in (2, 5)])
    if con_ficha:
        entrevistas.asegurar_tablas(con)
        e = entrevistas.crear(con, obra=OBRA)
        e.ficha, e.cerrada = ficha(), True
        entrevistas.guardar(con, e)
    return con


def _hecho():
    return {"clase": "hecho", "hecho": "imp-02",
            "enunciado_nuevo": "el viaje en tren nocturno a Lisboa",
            "texto": "que el tren sea de noche"}


def _nombre():
    return {"clase": "nombre", "personaje": "obra-x-per-brisa", "nombre_nuevo": "Nala",
            "texto": "el perro se llama Nala"}


def _pedida(con, peticion):
    p = regeneracion.proponer(con, OBRA, peticion)
    return regeneracion.pedir(con, OBRA, dict(
        peticion, capitulos_propuestos=p["capitulos_propuestos"]))


def _regenerar(con, peticion, escritor=None, **kw):
    _, id_p = _pedida(con, peticion)
    kw.setdefault("lean", _LeanFijo())
    return cascada.regenerar(con, peticiones.leer(con, id_p),
                             agentes=_agentes(escritor or _EscritorDeLaVersion()), **kw)


def _textos(con, numero):
    return {e["id"]: _texto_elegido(con, e)
            for e in regeneracion.escenas_de_version(con, OBRA, numero)}


def _borradores(con):
    return [tuple(f) for f in con.execute(
        "SELECT escena, version, texto FROM borrador ORDER BY escena, version")]


def test_la_cascada_reescribe_desde_el_primer_capitulo_que_usa_el_hecho_hasta_el_final():
    con = _base()
    escritor = _EscritorDeLaVersion()
    r = _regenerar(con, _hecho(), escritor)
    assert r["version"] == 2 and r["desde_capitulo"] == 3
    assert brief.capitulos_de_version(con, OBRA, 2) == NUEVOS
    assert r["capitulos_cambiados"] == NUEVOS[2:]
    assert len(escritor.llamadas) == 8, "una escena por capitulo, del 3 al 10"
    textos = _textos(con, 2)
    for c in NUEVOS[2:]:
        assert MARCA in textos["{0}-e1".format(c)]
        assert escaleta.escena(con, "{0}-e1".format(c))["estado"] == "consolidada"
    # El Escritor de la version nueva recibe el enunciado nuevo, no el viejo.
    assert "el viaje en tren nocturno a Lisboa" in escritor.llamadas[0]
    assert r["publicacion"]["publicada"] is True, r["publicacion"]
    assert brief.version_vigente(con, OBRA) == 2


def test_la_cascada_comparte_por_referencia_todo_lo_anterior():
    con = _base()
    antes = _borradores(con)
    v1 = _textos(con, 1)
    r = _regenerar(con, _hecho())
    assert r["capitulos_compartidos"] == CAPS[:2]
    assert brief.capitulos_de_version(con, OBRA, 2)[:2] == CAPS[:2]
    assert _textos(con, 1) == v1, "la version 1 queda identica, texto a texto"
    despues = _borradores(con)
    assert [f for f in despues if f in antes] == antes, "ningun borrador viejo cambia"
    nuevos = [f for f in despues if f not in antes]
    assert {f[0] for f in nuevos} == {"{0}-e1".format(c) for c in NUEVOS[2:]}, \
        "solo se escriben escenas de capitulos nuevos: lo compartido no se toca"


def test_ningun_capitulo_de_la_version_nueva_queda_sin_reverificar():
    con = _base()
    r = _regenerar(con, _hecho())
    estados = {e["id"]: regeneracion.estado_de(con, OBRA, 2, e["id"])
               for e in regeneracion.escenas_de_version(con, OBRA, 2)}
    assert len(estados) == 10
    assert EV.SIN_REVERIFICAR not in estados.values(), estados
    assert r["reverificacion"]["sin_reverificar"] == []


def test_un_capitulo_cerrado_posterior_no_se_reabre_se_escribe_otro():
    """`RF-30`: ninguna ruta reabre un capitulo `cerrado`. Hoy nadie escribe
    `capitulo.estado` (`F-92`), asi que el fixture lo cierra a mano."""
    con = _base()
    with con:
        con.execute("UPDATE capitulo SET estado = 'cerrado' WHERE id = ?", (CAPS[4],))
    texto = _textos(con, 1)[CAPS[4] + "-e1"]
    _regenerar(con, _hecho())
    assert brief.estado_de_capitulo(con, CAPS[4]) == "cerrado"
    assert _textos(con, 1)[CAPS[4] + "-e1"] == texto
    assert brief.estado_de_capitulo(con, NUEVOS[4]) == "abierto"
    assert MARCA in _textos(con, 2)[NUEVOS[4] + "-e1"]


def test_una_parada_a_mitad_deja_la_version_nueva_incompleta_y_la_anterior_intacta():
    con = _base()
    v1 = _textos(con, 1)
    escritor = _EscritorDeLaVersion(rompe_desde=3, con=con)
    r = _regenerar(con, _hecho(), escritor)
    assert r["parada"] is not None and r["publicacion"] is None
    hechas = [e["capitulo"] for e in regeneracion.escenas_de_version(con, OBRA, 2)
              if e["estado"] == "consolidada"]
    assert hechas == NUEVOS[:4], "los dos compartidos, el 3 y el 4, y ninguno mas"
    assert _textos(con, 1) == v1
    # `F-121`: mientras se escribia y despues de parar, el lector sigue en la 1.
    assert set(escritor.vigentes) == {1}
    assert brief.version_vigente(con, OBRA) == 1
    assert brief.leer(con, OBRA)["capitulos"] == CAPS


def test_relanzar_la_cascada_no_repite_lo_consolidado():
    con = _base()
    _, id_p = _pedida(con, _hecho())
    peticion = peticiones.leer(con, id_p)
    cascada.regenerar(con, peticion, agentes=_agentes(_EscritorDeLaVersion(rompe_desde=3)),
                      lean=_LeanFijo())
    antes = dict(con.execute("SELECT escena, COUNT(*) FROM borrador GROUP BY escena"))
    escritor = _EscritorDeLaVersion()
    r = cascada.regenerar(con, peticion, agentes=_agentes(escritor), lean=_LeanFijo())
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1, 2], "no crea otra"
    assert len(escritor.llamadas) == 6, "del 5 al 10: el 3 y el 4 ya estaban"
    despues = dict(con.execute("SELECT escena, COUNT(*) FROM borrador GROUP BY escena"))
    for c in NUEVOS[2:4]:
        assert despues["{0}-e1".format(c)] == antes["{0}-e1".format(c)]
    assert r["parada"] is None and r["publicacion"]["publicada"] is True, r


def test_la_version_nueva_se_publica_con_sus_propias_rondas():
    """`F-122` dentro de la cascada: la 1 gasto su ronda; la 2 empieza en la 1."""
    con = _base()
    _regenerar(con, _hecho())
    assert veredictos.ultimo(con, OBRA, 1)["ronda"] == 1
    assert veredictos.ultimo(con, OBRA, 2)["ronda"] == 1
    assert veredictos.ultimo(con, OBRA, 2)["publica"] is True


def test_en_un_renombrado_la_cascada_escribe_con_el_nombre_nuevo_y_veta_el_viejo(tmp_path):
    """El ejemplo del enunciado: «el perro se llama Nala». La perra sale en todos los
    capitulos, asi que la cascada empieza en el 1."""
    con = _base()
    v1 = _textos(con, 1)
    escritor = _EscritorDeLaVersion()
    r = _regenerar(con, _nombre(), escritor, carpeta_de_reglas=str(tmp_path))
    assert r["desde_capitulo"] == 1 and len(escritor.llamadas) == 10
    for texto in _textos(con, 2).values():
        assert "Nala" in texto and "Brisa" not in texto
    assert r["publicacion"]["publicada"] is True, r["publicacion"]
    with open(escritor.reglas, encoding="utf-8") as f:
        reglas = json.load(f)
    assert "Brisa" in reglas["vetadas"] and "Nala" in reglas["nombres"]
    assert _textos(con, 1) == v1 and all("Brisa" in t for t in v1.values())


def test_en_un_renombrado_las_palabras_clave_del_imprescindible_llevan_el_nombre_nuevo():
    """`F-124`: `INV-23` pedia «Brisa» -la palabra clave del plan- y `INV-21` la vetaba en la
    version nueva. El capitulo no podia pasar nunca."""
    con = _base()
    _, id_p = _pedida(con, _nombre())
    brief.crear_version(con, OBRA, ["{0}-v2".format(c) for c in CAPS], anterior=1,
                        peticion=id_p)
    from app.features.planificacion import repository as planes
    plan = planes.aprobado(con, OBRA)

    def claves(numero):
        por_escena = novela.imprescindibles_por_escena(con, OBRA, plan, numero)
        return [p for imps in por_escena.values() for i in imps for p in i["palabras_clave"]]

    assert "Nala" in claves(2) and "Brisa" not in claves(2)
    assert "Brisa" in claves(1)


def test_sin_ficha_la_cascada_no_escribe_nada_y_dice_por_que():
    """`F-91`: la ficha se borra al entregar, y sin ella no hay bloque inmutable. No se
    inventa: se para antes de crear la version."""
    con = _base(con_ficha=False)
    _, id_p = _pedida(con, _hecho())
    antes = _borradores(con)
    with pytest.raises(cascada.NoSePuedeRegenerar, match="F-91"):
        cascada.regenerar(con, peticiones.leer(con, id_p),
                          agentes=_agentes(_EscritorDeLaVersion()), lean=_LeanFijo())
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1]
    assert _borradores(con) == antes


def test_el_worker_ejecuta_la_cascada_de_un_trabajo_regenerar_obra():
    con = _base()
    id_t, _ = _pedida(con, _hecho())
    assert regeneracion.atender(con, id_t, agentes=_agentes(_EscritorDeLaVersion()),
                                lean=_LeanFijo())
    t = cola.leer(con, id_t)
    assert t.estado.value == "terminado", t.motivo_ultimo_fallo
    assert t.resultado["version"] == 2 and t.resultado["publicacion"]["publicada"] is True


def test_sin_agentes_el_worker_no_escribe_nada_y_lo_dice():
    """El worker de la API no tiene agentes: el trabajo falla con su motivo y **no se
    escribe nada**, ni la version."""
    con = _base()
    id_t, _ = _pedida(con, _hecho())
    assert regeneracion.atender(con, id_t) is False
    t = cola.leer(con, id_t)
    assert t.estado.value == "fallido" and "agentes" in t.motivo_ultimo_fallo
    assert [v["numero"] for v in brief.versiones_de(con, OBRA)] == [1]


def test_la_version_que_se_escribe_llega_a_las_tools_de_la_story_bible(tmp_path):
    ruta = str(tmp_path / "obra.db")
    mem = _base()
    destino = sqlite3.connect(ruta)
    mem.backup(destino)
    destino.row_factory = sqlite3.Row
    escritor = _EscritorDeLaVersion()
    agentes = _agentes(escritor)
    _, id_p = _pedida(destino, _hecho())
    cascada.regenerar(destino, peticiones.leer(destino, id_p), agentes=agentes,
                      lean=_LeanFijo())
    assert escritor.herramientas == {"db": ruta, "obra": OBRA, "version": 2}
    assert agentes["editor"].herramientas["version"] == 2
    destino.close()


# --- B-S1.2 · la promesa, antes de aceptar -----------------------------------------

def test_con_s1_la_promesa_dice_que_se_reescribe_hasta_el_final():
    """`SPEC-23` `D-3` con la salida elegida: «reescribimos lo que dependia de esto: el
    capitulo k y todos los siguientes», con su punto ciego, **antes** de aceptar."""
    con = _base()
    p = regeneracion.proponer(con, OBRA, _hecho())
    assert p["salida"] == "cascada"
    assert p["promesa"] == ("reescribimos lo que dependía de esto: el capítulo 3 y todos "
                            "los siguientes")
    assert p["punto_ciego"] == regeneracion.PUNTO_CIEGO
    assert p["capitulos_propuestos"] == CAPS[2:]


def test_con_observacion_la_cascada_es_una_traza_con_sus_capitulos_por_numero():
    """`SPEC-29`: la regeneracion sube como la generacion -un span por llamada a cada rol,
    colgado de su capitulo, que va por su **numero** en la version- y nada mas."""
    from app.features.orquestacion.tests.test_novela import _enviados, _observacion
    con = _base()
    obs = _observacion(con)
    _regenerar(con, _hecho(), observacion=obs)
    spans = _enviados(obs, "span")
    capitulos = sorted(s["capitulo"] for s in spans
                       if s["tipo"] == "grupo" and s["nombre"] == "capitulo")
    assert capitulos == list(range(3, 11))
    assert {s["nombre"] for s in spans if s["tipo"] == "rol"} >= {
        "escritor", "editor", "resumidor"}
    assert [s for s in spans if s["tipo"] == "grupo" and s["nombre"] == "regeneracion"]
