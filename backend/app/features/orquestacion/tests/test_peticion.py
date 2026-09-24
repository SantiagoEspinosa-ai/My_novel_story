"""`PLAN-23` A7: la peticion, el hecho y el nombre de la version, la propuesta y la
puerta cerrada.

Dos clases de peticion (`C-4`): un **hecho** -el enunciado nuevo, con las palabras
del lector- y un **nombre** -el `nombre_canonico` de un personaje pasa a otro, y su
identidad no cambia-. `SALIDA` es `None` hasta la medida (Parte B), asi que
`POST /obras/{id}/cambios` responde `409` y no encola nada. Datos inventados.
"""

import sqlite3

import pytest
from fastapi.testclient import TestClient

from app.commons.dominio.enumeraciones import ClaseDePeticion as CP
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.commons.dominio.story_bible import EntradaFicha
from app.commons.politica.vetadas import coincidencias
from app.commons.trabajos import cola
from app.features.brief import repository as brief
from app.features.consolidacion import memoria
from app.features.cronologia import repository as usos
from app.features.edicion import permisos
from app.features.entrevista import repository as entrevistas
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela, regeneracion, story_bible
from app.features.orquestacion import obra as modulo_obra
from app.features.orquestacion.tests import obra_regenerable as o
from app.features.planificacion import repository as planes
from app.features.planificacion.service import PlanAprobado
from app.features.planificacion.tests.conftest import ficha, plan_dict
from app.features.revision import repository as peticiones
from app.main import app, preparar_base

OBRA = "obra-x"
PROMESA = "reescribimos lo que dependía de esto"
PUNTO_CIEGO = "si la prosa contradice sin que el delta lo declare, no se toca"


def _plan():
    from app.commons.configuracion.esquemas import PlanDeLaObra
    d = plan_dict()
    d["capitulos"][1]["escenas"][0]["sinopsis"] = "Irene pasea con Brisa por el puerto."
    d["hechos"] = [{"id": "h-cocina", "enunciado": "Brisa duerme en la cocina"}]
    return PlanDeLaObra.model_validate(d)


TEXTOS = {2: "Irene y Brisa corren por la playa.", 7: "El Brisamar zarpa al alba."}


def _novela(con, con_ficha=True):
    planes.asegurar_tablas(con)
    novela.montar(con, OBRA, ficha(), PlanAprobado(_plan(), 1, "El mapa", "Un mapa."))
    planes.guardar(con, OBRA, 1, _plan(), True, "revisor", [])
    o.procedencia.registrar(con, version=o.COMMIT)
    escaleta.asignar_t_discurso(con, OBRA, {"cap-{0:02d}".format(n): n for n in range(1, 11)})
    with con:
        con.execute("UPDATE escena SET personajes_presentes = ? WHERE id = 'cap-05-e1'",
                    ('["per-brisa"]',))
    for n in range(1, 11):
        delta = ({"revelaciones": [{"sujeto": "per-brisa", "hecho": "h-cocina"}]}
                 if n == 6 else {})
        o.escribir(con, "cap-{0:02d}-e1".format(n),
                   TEXTOS.get(n, "Texto del capitulo {0}.".format(n)), delta)
    usos.registrar_usos(con, [
        {"hecho": "h-cocina", "escena": "cap-03-e1", "capitulo": "cap-03",
         "tipo": TipoDeUsoDeHecho.DEPENDE, "origen": OrigenDeUso.DELTA},
        {"hecho": "h-cocina", "escena": "cap-06-e1", "capitulo": "cap-06",
         "tipo": TipoDeUsoDeHecho.ESTABLECE, "origen": OrigenDeUso.DELTA}])
    if con_ficha:
        entrevistas.asegurar_tablas(con)
        e = entrevistas.crear(con, obra=OBRA)
        e.ficha, e.cerrada = ficha(), True
        entrevistas.guardar(con, e)


@pytest.fixture
def con():
    c = o.conexion()
    _novela(c)
    return c


def _hecho(**kw):
    return dict({"clase": CP.HECHO, "hecho": "h-cocina",
                 "enunciado_nuevo": "Brisa duerme en el jardin",
                 "texto": "que duerma fuera"}, **kw)


def _nombre(**kw):
    return dict({"clase": CP.NOMBRE, "personaje": "per-brisa", "nombre_nuevo": "Nala",
                 "texto": "el perro se llama Nala"}, **kw)


def _cuantos(con, tabla):
    try:
        return con.execute("SELECT COUNT(*) FROM {0}".format(tabla)).fetchone()[0]
    except sqlite3.OperationalError:
        return 0


def _v2(con, peticion, posiciones):
    """La version 2 de una peticion guardada, con los capitulos de `posiciones` nuevos."""
    id_p = peticiones.guardar(con, OBRA, dict(peticion, version_de_partida=1,
                                              capitulos_propuestos=[]))
    capitulos = brief.capitulos_de_version(con, OBRA, 1)
    for k in posiciones:
        capitulos[k - 1] = "{0}-v2".format(capitulos[k - 1])
    brief.crear_version(con, OBRA, capitulos, anterior=1, peticion=id_p, commit="def5678")
    return id_p


# --- La propuesta -------------------------------------------------------------------

def test_la_propuesta_lista_los_capitulos_antes_de_tocarlos_y_no_encola_nada(con):
    antes = {t: _cuantos(con, t) for t in ("trabajo", "peticion_de_cambio", "borrador")}
    p = regeneracion.proponer(con, OBRA, _hecho())
    assert p["capitulos"]["selectiva"] == ["cap-03", "cap-06"]
    assert p["capitulos"]["cascada"] == ["cap-{0:02d}".format(n) for n in range(3, 11)]
    assert p["salida"] is None and p["capitulos_propuestos"] is None
    assert "falta la medida" in p["motivo"]
    assert p["version_de_partida"] == 1
    assert {t: _cuantos(con, t) for t in antes} == antes
    assert brief.version_vigente(con, OBRA) == 1


def test_la_propuesta_lleva_la_promesa_y_su_punto_ciego_literales(con):
    p = regeneracion.proponer(con, OBRA, _hecho())
    assert p["promesa"] == PROMESA and p["punto_ciego"] == PUNTO_CIEGO


def test_con_una_salida_elegida_la_propuesta_da_su_lista(con, monkeypatch):
    monkeypatch.setattr(regeneracion, "SALIDA", "selectiva")
    p = regeneracion.proponer(con, OBRA, _hecho())
    assert p["salida"] == "selectiva" and p["capitulos_propuestos"] == ["cap-03", "cap-06"]


def test_una_peticion_sobre_un_hecho_de_otra_obra_se_rechaza(con):
    o.obra(con, id_obra="obra-otra", hechos=[("h-ajeno", "algo de otra obra")], commit=None)
    with pytest.raises(regeneracion.PeticionNoAdmitida, match="no es un hecho de esta obra"):
        regeneracion.proponer(con, OBRA, _hecho(hecho="h-ajeno"))


def test_un_hecho_que_ninguna_escena_de_la_version_usa_se_rechaza(con):
    escaleta.declarar_hechos(con, OBRA, [{"id": "h-suelto", "enunciado": "nadie lo usa"}])
    with pytest.raises(regeneracion.PeticionNoAdmitida, match="ninguna escena"):
        regeneracion.proponer(con, OBRA, _hecho(hecho="h-suelto"))


# --- El hecho de una version --------------------------------------------------------

def test_el_enunciado_nuevo_vale_en_la_version_nueva_y_no_en_la_anterior(con):
    _v2(con, _hecho(), [3, 6])
    nuevo = {h["id"]: h["enunciado"] for h in regeneracion.hechos_de_version(con, OBRA, 2)}
    viejo = {h["id"]: h["enunciado"] for h in regeneracion.hechos_de_version(con, OBRA, 1)}
    assert nuevo["h-cocina"] == "Brisa duerme en el jardin"
    assert viejo["h-cocina"] == "Brisa duerme en la cocina"
    # `HechoCanonico` no se edita: la tabla sigue diciendo lo del plan.
    assert {h["id"]: h["enunciado"] for h in escaleta.hechos_declarados(con, OBRA)}[
        "h-cocina"] == "Brisa duerme en la cocina"
    # Y lo que recibe el Escritor de la version nueva (y el acta, para `menciona`).
    escaleta.guardar_escaleta(con, OBRA, [regeneracion.escena_para_regenerar(con, OBRA, 2, 3)])
    material = modulo_obra.reunir_material(con, escaleta.escena(con, "cap-03-v2-e1"), OBRA)
    assert {h["id"]: h["enunciado"] for h in material["hechos"]}["h-cocina"] == \
        "Brisa duerme en el jardin"


def test_editar_el_hecho_a_mano_sigue_prohibido(con):
    _v2(con, _hecho(), [3, 6])
    usado = modulo_obra.escenas_que_usan(con, "hecho", "h-cocina")
    assert usado == ["cap-06-e1"]
    assert permisos.se_puede_editar("hecho", "h-cocina", usado_por=usado).permitido is False


# --- El nombre de una version -------------------------------------------------------

def test_un_renombrado_toca_los_capitulos_que_contienen_el_nombre_viejo_y_los_de_su_presencia(con):
    p = regeneracion.proponer(con, OBRA, _nombre())
    # cap-02 lo nombra; cap-05 la tiene presente; cap-07 dice «Brisamar», que no es ella.
    assert p["capitulos"]["selectiva"] == ["cap-02", "cap-05"]
    assert p["capitulos"]["cascada"] == ["cap-{0:02d}".format(n) for n in range(2, 11)]


def test_la_version_anterior_conserva_el_nombre_viejo_en_sus_fichas_y_en_inv22(con):
    _v2(con, _nombre(), [2, 5])
    assert regeneracion.nombres_de_version(con, OBRA, 1)["per-brisa"] == "Brisa"
    assert regeneracion.nombres_de_version(con, OBRA, 2)["per-brisa"] == "Nala"
    # Los nombres que `INV-22` compara, por version.
    assert "Brisa" in novela.nombres_para_inv22(con, OBRA, ficha(), _plan(), 1)
    assert "Nala" in novela.nombres_para_inv22(con, OBRA, ficha(), _plan(), 2)
    assert "Brisa" not in novela.nombres_para_inv22(con, OBRA, ficha(), _plan(), 2)
    # La story bible sirve la version que se escribe, la vigente.
    f = story_bible.leer_ficha(con, OBRA, EntradaFicha(id="per-brisa")).personaje
    assert f.nombre_canonico == "Nala" and f.id == "per-brisa"


def test_en_la_version_nueva_el_nombre_viejo_es_una_vetada(con):
    _v2(con, _nombre(), [2, 5])
    v2 = regeneracion.vetadas_de_version(con, OBRA, 2, base=["hospital"])
    assert "Brisa" in v2 and "hospital" in v2
    assert regeneracion.vetadas_de_version(con, OBRA, 1, base=["hospital"]) == ["hospital"]
    assert coincidencias("Nala y Brisa corren.", v2)
    # Y la puerta de la version anterior no se entera: sus capitulos no se tocan.
    assert modulo_obra.evaluar_cierre(con, OBRA, "cap-02",
                                      vetadas=["hospital"])["puede_cerrarse"] is True


def test_el_material_del_escritor_lleva_el_nombre_nuevo(con):
    _v2(con, _nombre(), [2, 5])
    e = regeneracion.escena_para_regenerar(con, OBRA, 2, 2)
    assert e["id"] == "cap-02-v2-e1" and e["capitulo"] == "cap-02-v2"
    assert e["t_discurso"] == 2, "`C-6`: hereda el `t_discurso` de la que sustituye"
    assert e["beats"][0]["texto"] == "Irene pasea con Nala por el puerto."
    assert {h["id"]: h["enunciado"] for h in regeneracion.hechos_de_version(con, OBRA, 2)}[
        "h-cocina"] == "Nala duerme en la cocina"


def test_renombrar_al_destinatario_o_a_un_nombre_ya_usado_es_409(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta).close()
    mem = o.conexion()
    _novela(mem)
    destino = sqlite3.connect(ruta)
    mem.backup(destino)
    destino.close()
    app.state.ruta_db = ruta
    c = TestClient(app)
    url = "/obras/{0}/cambios/propuesta".format(OBRA)
    r = c.post(url, json=_nombre(personaje="per-irene", nombre_nuevo="Ines"))
    assert r.status_code == 409 and "destinatario" in r.json()["detail"]
    r = c.post(url, json=_nombre(nombre_nuevo="Irene Valdés"))
    assert r.status_code == 409 and "ya es" in r.json()["detail"]
    r = c.post(url, json=_hecho(hecho="h-que-no-existe"))
    assert r.status_code == 409
    r = c.post(url, json=_nombre())
    assert r.status_code == 200 and r.json()["capitulos"]["selectiva"] == ["cap-02", "cap-05"]


def test_sin_ficha_no_consta_el_destinatario_y_el_renombrado_se_niega(tmp_path):
    c = o.conexion()
    _novela(c, con_ficha=False)
    with pytest.raises(regeneracion.PeticionNoAdmitida, match="destinatario"):
        regeneracion.proponer(c, OBRA, _nombre())


# --- La puerta cerrada ----------------------------------------------------------------

@pytest.fixture
def cliente(tmp_path):
    ruta = str(tmp_path / "obra.db")
    preparar_base(ruta).close()
    mem = o.conexion()
    _novela(mem)
    destino = sqlite3.connect(ruta)
    mem.backup(destino)
    destino.close()
    app.state.ruta_db = ruta
    return TestClient(app), ruta


def test_pedir_el_cambio_sin_salida_elegida_es_409_y_no_gasta(cliente):
    c, ruta = cliente
    p = c.post("/obras/{0}/cambios/propuesta".format(OBRA), json=_hecho()).json()
    r = c.post("/obras/{0}/cambios".format(OBRA),
               json=dict(_hecho(), capitulos_propuestos=p["capitulos"]["selectiva"]))
    assert r.status_code == 409
    assert "salida sin elegir: falta la medida" in r.json()["detail"]
    con = sqlite3.connect(ruta)
    assert _cuantos(con, "trabajo") == 0 and _cuantos(con, "peticion_de_cambio") == 0
    assert brief.version_vigente(con, OBRA) == 1


def test_pedir_con_una_lista_distinta_de_la_propuesta_es_409(cliente, monkeypatch):
    monkeypatch.setattr(regeneracion, "SALIDA", "selectiva")
    c, ruta = cliente
    r = c.post("/obras/{0}/cambios".format(OBRA),
               json=dict(_hecho(), capitulos_propuestos=["cap-03"]))
    assert r.status_code == 409 and "cambio" in r.json()["detail"]
    con = sqlite3.connect(ruta)
    assert _cuantos(con, "trabajo") == 0


def test_con_la_lista_propuesta_se_encola_y_el_worker_dice_que_la_rama_falta(cliente,
                                                                            monkeypatch):
    """El camino de la Parte B, con `SALIDA` fijada a mano: se guarda la peticion, se
    encola y el worker **no escribe nada**, porque la rama todavia no existe."""
    monkeypatch.setattr(regeneracion, "SALIDA", "selectiva")
    c, ruta = cliente
    r = c.post("/obras/{0}/cambios".format(OBRA),
               json=dict(_hecho(), capitulos_propuestos=["cap-03", "cap-06"]))
    assert r.status_code == 202
    con = sqlite3.connect(ruta)
    t = cola.leer(con, r.json()["id_trabajo"])
    assert t.tipo == regeneracion.TIPO_DE_TRABAJO
    assert t.estado.value == "fallido" and "Parte B" in t.motivo_ultimo_fallo
    p = peticiones.leer(con, t.carga["peticion"])
    assert p["salida"] == "selectiva" and p["capitulos_propuestos"] == ["cap-03", "cap-06"]
    assert p["version_de_partida"] == 1 and p["clase"] == CP.HECHO
    assert brief.version_vigente(con, OBRA) == 1
