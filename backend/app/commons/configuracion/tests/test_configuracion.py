"""La forma de la obra sale del guion y pasa a ser un fichero.

POR QUE ESTO NO ES COMODIDAD
------------------------------
Que la forma de la obra viviera dentro del guion es lo que hizo que **nadie
notara durante diez capitulos que estabamos modelando diez obras** en vez de
una con diez capitulos. Un fichero de configuracion lo habria hecho visible el
primer dia: `capitulos: 10` en un sitio que se lee de un vistazo no se
confunde con diez llamadas a `guardar_escaleta`.

SON DOS FICHEROS Y NO UNO
---------------------------
El del **sistema** cambia cuando cambia la maquina -que modelo, cuanto se
gasta, donde esta la base- y el **brief** cambia cuando cambia la novela.
Juntarlos obligaria a tocar la novela para cambiar de modelo, y a revisar la
configuracion de la maquina para escribir otra historia.
"""

import json

import pytest

from app.commons.configuracion import carga
from app.commons.configuracion.esquemas import BriefDeObra, ConfiguracionDelSistema


def _escribir(tmp_path, nombre, datos):
    ruta = tmp_path / nombre
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")
    return str(ruta)


SISTEMA_MINIMO = {"modelos": {"escritor": "fable", "juez": "opus",
                              "resumidor": "haiku"}}
BRIEF_MINIMO = {"titulo": "La casa exacta", "premisa": "Marta hereda una casa.",
                "forma": {"capitulos": 3, "escenas_por_capitulo": 4,
                          "palabras_por_escena": [250, 800]}}


def test_el_brief_dice_la_forma_de_la_obra(tmp_path):
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", BRIEF_MINIMO))
    assert b.forma.capitulos == 3
    assert b.forma.escenas_por_capitulo == 4
    assert b.forma.palabras_por_escena == (250, 800)


def test_un_campo_inventado_en_el_brief_no_entra_en_silencio(tmp_path):
    """`CLAUDE.md`: los modelos Pydantic son la frontera de validacion y un
    campo que no esta definido no entra en un esquema. Con `extra=forbid`, un
    nombre mal escrito sale por un error y no por un valor por defecto."""
    datos = dict(BRIEF_MINIMO, capitulosss=10)
    with pytest.raises(carga.ConfiguracionInvalida, match="capitulosss"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", datos))


def test_una_forma_imposible_se_rechaza_al_cargar(tmp_path):
    """Cero capitulos no es una obra corta: es un error de quien lo escribio,
    y descubrirlo al generar cuesta una tanda."""
    datos = dict(BRIEF_MINIMO, forma=dict(BRIEF_MINIMO["forma"], capitulos=0))
    with pytest.raises(carga.ConfiguracionInvalida):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", datos))


def test_el_rango_de_palabras_tiene_que_estar_ordenado(tmp_path):
    datos = dict(BRIEF_MINIMO,
                 forma=dict(BRIEF_MINIMO["forma"], palabras_por_escena=[900, 300]))
    with pytest.raises(carga.ConfiguracionInvalida, match="minimo"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", datos))


def test_el_sistema_trae_los_modelos_por_agente(tmp_path):
    s = carga.cargar_sistema(_escribir(tmp_path, "sistema.json", SISTEMA_MINIMO))
    assert s.modelos.escritor == "fable"
    assert s.modelos.juez == "opus"


def test_los_topes_tienen_los_valores_de_config_si_no_se_dicen(tmp_path):
    """Los numeros no medidos siguen viviendo en `commons/config.py` con su
    marca de procedencia. El fichero puede cambiarlos; **no los inventa de
    nuevo**, porque entonces habria dos sitios que dicen cuanto vale un tope."""
    from app.commons import config

    s = carga.cargar_sistema(_escribir(tmp_path, "sistema.json", SISTEMA_MINIMO))
    assert s.topes.intentos_por_escena == config.TOPE_INTENTOS_ESCENA
    assert s.topes.delegaciones_por_obra == config.TOPE_DELEGACIONES_OBRA


def test_un_fichero_que_no_existe_lo_dice_con_su_ruta(tmp_path):
    """Un `FileNotFoundError` pelado obliga a adivinar cual de los dos falta."""
    with pytest.raises(carga.ConfiguracionInvalida, match="no existe"):
        carga.cargar_brief(str(tmp_path / "no-esta.json"))


def test_un_json_roto_lo_dice_sin_reventar(tmp_path):
    ruta = tmp_path / "brief.json"
    ruta.write_text("{esto no es json", encoding="utf-8")
    with pytest.raises(carga.ConfiguracionInvalida, match="JSON"):
        carga.cargar_brief(str(ruta))


def test_el_brief_tiene_huella_para_poder_repetir_la_tanda(tmp_path):
    """`procedencia.py` guarda con que codigo se escribio una base. Con la
    huella del brief, una tanda se puede repetir **exactamente**: mismo codigo
    y misma forma de obra."""
    ruta = _escribir(tmp_path, "brief.json", BRIEF_MINIMO)
    a = carga.cargar_brief(ruta)
    b = carga.cargar_brief(ruta)
    assert a.huella == b.huella and len(a.huella) == 12


def test_dos_briefs_distintos_tienen_huellas_distintas(tmp_path):
    otro = dict(BRIEF_MINIMO, forma=dict(BRIEF_MINIMO["forma"], capitulos=4))
    a = carga.cargar_brief(_escribir(tmp_path, "a.json", BRIEF_MINIMO))
    b = carga.cargar_brief(_escribir(tmp_path, "b.json", otro))
    assert a.huella != b.huella


def test_la_huella_no_cambia_por_el_orden_de_las_claves(tmp_path):
    """Si cambiara, dos ficheros identicos en contenido dirian que son tandas
    distintas, y la huella dejaria de servir para lo unico que sirve."""
    al_reves = {"premisa": BRIEF_MINIMO["premisa"], "forma": BRIEF_MINIMO["forma"],
                "titulo": BRIEF_MINIMO["titulo"]}
    a = carga.cargar_brief(_escribir(tmp_path, "a.json", BRIEF_MINIMO))
    b = carga.cargar_brief(_escribir(tmp_path, "b.json", al_reves))
    assert a.huella == b.huella


def test_las_palabras_prohibidas_son_las_de_la_guia_de_estilo(tmp_path):
    """No es un campo nuevo: `GuiaDeEstilo.tics_prohibidos` existe en
    `docs/definitions.md`. El brief lo rellena, no lo inventa."""
    datos = dict(BRIEF_MINIMO, estilo={"tics_prohibidos": ["de repente", "sintio que"]})
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", datos))
    assert "de repente" in b.estilo.tics_prohibidos


def test_los_ficheros_del_repositorio_son_validos():
    """El caso que evita que esto se rompa en silencio: los dos ficheros que
    el proyecto trae se cargan con el mismo codigo que los valida."""
    s = carga.cargar_sistema()
    b = carga.cargar_brief()
    assert s.modelos.escritor
    assert b.forma.capitulos > 0


# --- Que la configuracion y el plan no puedan divergir -------------------

def test_una_escaleta_que_no_cuadra_con_la_forma_se_detecta(tmp_path):
    """El brief dice **cuantas** piezas y el guion trae **cuales**. Si los dos
    pueden decir cosas distintas, volvemos a tener la forma en dos sitios — que
    es exactamente lo que `F-53` costo descubrir.

    Se comprueba al arrancar y no al generar: descubrirlo en la escena 37
    cuesta una tanda entera.
    """
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", BRIEF_MINIMO))
    with pytest.raises(carga.ConfiguracionInvalida, match="capitulos"):
        carga.comprobar_forma(b, capitulos=5, escenas_por_capitulo=4)


def test_escenas_por_capitulo_tambien_se_comprueba(tmp_path):
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", BRIEF_MINIMO))
    with pytest.raises(carga.ConfiguracionInvalida, match="escenas"):
        carga.comprobar_forma(b, capitulos=3, escenas_por_capitulo=9)


def test_si_cuadra_no_dice_nada(tmp_path):
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", BRIEF_MINIMO))
    assert carga.comprobar_forma(b, capitulos=3, escenas_por_capitulo=4) is None


# --- El plan entero en el fichero: editar y que cambie la obra ------------

PLAN_MINIMO = {
    "mundo": {
        "lugares": [{"id": "lug-salon", "nombre": "El salon",
                     "accesos": ["lug-cocina"]},
                    {"id": "lug-cocina", "nombre": "La cocina",
                     "accesos": ["lug-salon"]}],
        "personajes": [{"id": "per-marta", "nombre": "Marta",
                        "empieza_en": "lug-salon"}],
        "conocimiento_inicial": [{"sujeto": "per-marta", "hecho": "hec-uno",
                                  "grado": "sabe"}],
    },
    "hechos": [{"id": "hec-uno", "enunciado": "Marta heredo la casa"}],
    "capitulos": [
        {"id": "cap-01", "titulo": "Llegar", "escenas": [
            {"eje": "cordura", "lugar": "lug-salon", "pov": "per-marta",
             "sinopsis": "Marta cuenta los peldanos.", "establece": ["hec-uno"]},
            {"eje": "seguridad", "lugar": "lug-cocina", "pov": "per-marta",
             "sinopsis": "La puerta no cede."},
        ]},
        {"id": "cap-02", "titulo": "Ana", "escenas": [
            {"eje": "vinculo", "lugar": "lug-salon", "pov": "per-marta",
             "sinopsis": "Ana llega."},
            {"eje": "control", "lugar": "lug-cocina", "pov": "per-marta",
             "sinopsis": "Ana propone vender."},
        ]},
    ],
}
BRIEF_CON_PLAN = dict(BRIEF_MINIMO,
                      forma={"capitulos": 2, "escenas_por_capitulo": 2,
                             "palabras_por_escena": [250, 800]},
                      plan=PLAN_MINIMO)


def test_el_brief_trae_la_obra_entera(tmp_path):
    b = carga.cargar_brief(_escribir(tmp_path, "brief.json", BRIEF_CON_PLAN))
    assert [c.id for c in b.plan.capitulos] == ["cap-01", "cap-02"]
    assert b.plan.capitulos[0].escenas[0].establece == ["hec-uno"]
    assert [h.id for h in b.plan.hechos] == ["hec-uno"]


def test_la_forma_y_el_plan_no_pueden_divergir(tmp_path):
    """Se valida **dentro del esquema**, asi que el fichero no puede estar mal:
    antes se comprobaba al arrancar el guion, y eso dejaba una ventana en la
    que el fichero decia una cosa y el codigo otra."""
    malo = dict(BRIEF_CON_PLAN, forma={"capitulos": 5, "escenas_por_capitulo": 2,
                                       "palabras_por_escena": [250, 800]})
    with pytest.raises(carga.ConfiguracionInvalida, match="capitulos"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", malo))


def test_capitulos_con_distinto_numero_de_escenas_se_rechazan(tmp_path):
    """`escenas_por_capitulo` es **un** numero, asi que todos los capitulos
    tienen que traer esa cantidad. Si no, la forma miente sobre la mitad."""
    plan = json.loads(json.dumps(PLAN_MINIMO))
    plan["capitulos"][1]["escenas"].pop()
    malo = dict(BRIEF_CON_PLAN, plan=plan)
    with pytest.raises(carga.ConfiguracionInvalida, match="escenas"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", malo))


def test_un_hecho_que_un_beat_promete_tiene_que_existir(tmp_path):
    """`SPEC-19`: un beat **no inventa hechos, los situa**. Un identificador
    que no este declarado llegaria al prompt y el modelo no podria citarlo."""
    plan = json.loads(json.dumps(PLAN_MINIMO))
    plan["capitulos"][0]["escenas"][0]["establece"] = ["hec-que-no-existe"]
    malo = dict(BRIEF_CON_PLAN, plan=plan)
    with pytest.raises(carga.ConfiguracionInvalida, match="hec-que-no-existe"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", malo))


def test_una_escena_en_un_lugar_que_no_existe_se_rechaza(tmp_path):
    """`INV-02` llega al grafo de accesos por el `id`. Un lugar que no case con
    ninguna fila **no se comprueba contra nada**: es la asimetria que la
    sesion de specs describio, cazada aqui en la frontera."""
    plan = json.loads(json.dumps(PLAN_MINIMO))
    plan["capitulos"][0]["escenas"][0]["lugar"] = "lug-inventado"
    malo = dict(BRIEF_CON_PLAN, plan=plan)
    with pytest.raises(carga.ConfiguracionInvalida, match="lug-inventado"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", malo))


def test_un_acceso_a_un_lugar_que_no_existe_tambien(tmp_path):
    plan = json.loads(json.dumps(PLAN_MINIMO))
    plan["mundo"]["lugares"][0]["accesos"] = ["lug-fantasma"]
    malo = dict(BRIEF_CON_PLAN, plan=plan)
    with pytest.raises(carga.ConfiguracionInvalida, match="lug-fantasma"):
        carga.cargar_brief(_escribir(tmp_path, "brief.json", malo))


def test_el_brief_del_repositorio_trae_su_plan_completo():
    b = carga.cargar_brief()
    assert b.plan is not None, "el brief del proyecto trae la obra entera"
    assert len(b.plan.capitulos) == b.forma.capitulos


# --- `SPEC-32` `RF-07`: las opciones de extension, dentro de 1.000-1.500 ---------

def _con_extensiones(tmp_path, extensiones):
    return _escribir(tmp_path, "sistema.json", dict(SISTEMA_MINIMO, extensiones=extensiones))


def test_los_rangos_por_defecto_cargan(tmp_path):
    s = carga.cargar_sistema(_escribir(tmp_path, "sistema.json", SISTEMA_MINIMO))
    assert {e.value: tuple(r) for e, r in s.extensiones.items()} == {
        "corta": (1000, 1150), "media": (1150, 1350), "larga": (1350, 1500)}


def test_una_opcion_de_extension_fuera_de_1000_1500_es_error(tmp_path):
    """El rango es decision nuestra (`SPEC-32`), pero es obligatorio: una opcion
    fuera es un error de configuracion, no un aviso."""
    with pytest.raises(carga.ConfiguracionInvalida, match="1000"):
        carga.cargar_sistema(_con_extensiones(tmp_path, {
            "corta": [900, 1150], "media": [1150, 1350], "larga": [1350, 1500]}))


def test_un_rango_con_el_minimo_mayor_que_el_maximo_es_error(tmp_path):
    """Con `match`: sin el, pasaba antes de existir el campo, porque un campo
    desconocido tambien es `ConfiguracionInvalida` (Regla 11)."""
    with pytest.raises(carga.ConfiguracionInvalida, match="minimo"):
        carga.cargar_sistema(_con_extensiones(tmp_path, {
            "corta": [1150, 1000], "media": [1150, 1350], "larga": [1350, 1500]}))


def test_falta_el_rango_de_una_opcion_es_error(tmp_path):
    with pytest.raises(carga.ConfiguracionInvalida, match="larga"):
        carga.cargar_sistema(_con_extensiones(tmp_path, {
            "corta": [1000, 1150], "media": [1150, 1350]}))


# --- `SPEC-30` `RF-07`: el tope de la puerta de publicacion ----------------------

def test_el_tope_de_publicacion_es_2_y_cuenta_aparte(tmp_path):
    """El mismo numero que las vetadas, pero su propio contador: no comparte las
    reescrituras del Editor ni las de `INV-21`."""
    from app.commons import config
    s = carga.cargar_sistema(_escribir(tmp_path, "sistema.json", SISTEMA_MINIMO))
    assert s.topes.reintentos_de_publicacion == config.TOPE_REINTENTOS_DE_PUBLICACION == 2
    assert s.lean.tiempo_maximo_segundos == config.TIEMPO_MAXIMO_LEAN_SEGUNDOS


def test_un_tope_de_publicacion_negativo_no_carga(tmp_path):
    """Con el motivo en el `match`: el nombre del campo solo tambien lo daria un
    campo desconocido, y la prueba pasaria antes de existir el tope (Regla 11)."""
    with pytest.raises(carga.ConfiguracionInvalida, match="greater than or equal"):
        carga.cargar_sistema(_escribir(tmp_path, "sistema.json", dict(
            SISTEMA_MINIMO, topes={"reintentos_de_publicacion": -1})))
