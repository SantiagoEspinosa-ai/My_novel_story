"""C4 — Las puertas, con el caso negativo de cada invariante que ejecutan.

"Una invariante que nunca ha fallado en las pruebas no esta verificada, solo
declarada." Esta feature ejecuta seis, y aqui esta el fragmento que viola cada
una a proposito.
"""

import pytest

from app.commons.dominio.enumeraciones import EstadoDeHallazgo, Severidad
from app.features.verificacion import puertas


def _mundo():
    return {
        "entidades_vivas": {"marta": "vivo", "ana": "muerto"},
        "ubicaciones": {"marta": "salon", "ana": "sotano"},
        "accesos": {"salon": ["cocina"], "sotano": []},
        "conocimiento": {("marta", "hec-1"): {"desde": 1, "grado": "sabe"}},
    }


def test_inv01_una_escena_sin_cambio_de_valor():
    h = puertas.verificar({"id": "e1", "cambio_de_valor": None}, {}, _mundo())
    assert any(x.invariante == "INV-01" and x.severidad is Severidad.BLOQUEANTE for x in h)


def test_inv02_un_personaje_muerto_presente():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "personajes_presentes": ["ana"], "lugar": "salon"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-02" for x in h)


def test_inv02_un_personaje_en_un_lugar_inaccesible():
    """La mitad que obligo a partir `Lugar`: la accesibilidad."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "sotano"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-02" for x in h)


def _escena_de_conocimiento():
    return {"id": "e1", "cambio_de_valor": {"eje": "conocimiento", "signo": "positivo"},
            "personajes_presentes": ["marta"], "lugar": "salon", "t_fabula": 5}


def test_inv03_actuar_sobre_un_hecho_que_no_se_conoce():
    """`SPEC-16` C-2: lo que `INV-03` comprueba son las **acciones**."""
    delta = {"acciones": [{"personaje": "ana", "hecho": "hec-9"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, _mundo())
    assert any(x.invariante == "INV-03" and x.severidad is Severidad.BLOQUEANTE for x in h)


def test_inv03_actuar_sobre_un_hecho_que_si_se_conoce_no_es_hallazgo():
    """El caso positivo, que no existia: sin el, una invariante que marcara
    siempre pasaria su propio caso negativo y nadie lo notaria."""
    delta = {"acciones": [{"personaje": "marta", "hecho": "hec-1"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, _mundo())
    assert not any(x.invariante == "INV-03" for x in h)


def test_inv03_ya_no_mira_las_revelaciones():
    """`F-31`: mirarlas exigia saber de antes para poder aprender, asi que
    **ningun personaje podia llegar a saber nada nunca**. Revelar es aprender,
    y aprender no se comprueba contra lo ya sabido (`SPEC-16` C-1)."""
    delta = {"revelaciones": [{"sujeto": "ana", "hecho": "hec-9"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, _mundo())
    assert not any(x.invariante == "INV-03" for x in h)


def test_inv03_un_grado_ignora_no_cuenta_como_conocer():
    """Constar en el registro no basta: `ignora` es constar que no lo sabe."""
    mundo = _mundo()
    mundo["conocimiento"][("ana", "hec-1")] = {"desde": 2, "grado": "ignora"}
    delta = {"acciones": [{"personaje": "ana", "hecho": "hec-1"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, mundo)
    assert any(x.invariante == "INV-03" for x in h)


def test_inv04_el_pov_cambia_dentro_de_la_escena():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "control", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "pov": "marta", "pov_usado": "ana"}
    h = puertas.verificar(esc, {}, _mundo())
    assert any(x.invariante == "INV-04" for x in h)


def test_inv17_una_escena_de_944_palabras_con_minimo_de_1200():
    """El caso de `main`, ahora cazado por una regla y no por un juez."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "longitud_objetivo": (1200, 2200), "palabras": 944}
    h = puertas.verificar(esc, {}, _mundo())
    inv17 = [x for x in h if x.invariante == "INV-17"]
    assert inv17 and inv17[0].severidad is Severidad.MAYOR


def test_un_verificador_mudo_produce_sin_veredicto_y_no_un_pase():
    """`SPEC-10` C-2: quien no se dejo auditar no gana por defecto."""
    h = puertas.veredicto_ilegible("INV-10", "e1", salida="{{roto")
    assert h.estado is EstadoDeHallazgo.SIN_VEREDICTO
    assert h.descripcion, "se rellena con que se intento comprobar y donde"


def test_una_escena_limpia_no_produce_hallazgos():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
           "personajes_presentes": ["marta"], "lugar": "salon",
           "pov": "marta", "pov_usado": "marta",
           "longitud_objetivo": (500, 2200), "palabras": 900}
    assert puertas.verificar(esc, {}, _mundo()) == []


# --- F-34: una invariante sin su dato no calla, dice que no pudo ----------
#
# "Una invariante que se salta en silencio cuando le falta un campo esta
# ausente, no en verde, y desde fuera se ven igual." El mecanismo ya existia
# en este modulo para otro caso -`veredicto_ilegible`, con estado
# `sin_veredicto`- y el argumento es identico: un verificador que no contesta
# es un agujero en la validacion.
#
# El criterio de que campo es imprescindible **sale del dominio, no de aqui**:
# `docs/definitions.md` marca en negrita `Escena.pov`, `Escena.lugar` y
# `Borrador.pov_usado`; `personajes_presentes` y `longitud_objetivo` no lo
# estan, asi que su ausencia es legitima y la invariante simplemente no aplica.

def _sin_veredicto(hallazgos, inv):
    return [x for x in hallazgos if x.invariante == inv
            and x.estado is EstadoDeHallazgo.SIN_VEREDICTO]


def test_inv04_sin_pov_usado_no_calla_dice_que_no_pudo():
    """El caso de `F-34`: el modelo escribio la escena sobre otro personaje y
    `INV-04` paso en verde porque el campo no estaba."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "control", "signo": "negativo"},
           "lugar": "salon", "pov": "marta"}
    h = puertas.verificar(esc, {}, _mundo())
    assert _sin_veredicto(h, "INV-04"), "sin pov_usado no se puede comparar"


def test_inv04_sin_pov_planificado_tampoco_calla():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "control", "signo": "negativo"},
           "lugar": "salon", "pov_usado": "ana"}
    h = puertas.verificar(esc, {}, _mundo())
    assert _sin_veredicto(h, "INV-04")


def test_inv04_con_los_dos_campos_y_coincidiendo_no_marca_nada():
    """El caso positivo: tener el dato y que este bien no produce hallazgo."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "control", "signo": "negativo"},
           "lugar": "salon", "pov": "marta", "pov_usado": "marta"}
    h = puertas.verificar(esc, {}, _mundo())
    assert not any(x.invariante == "INV-04" for x in h)


def test_inv02_con_personajes_y_sin_lugar_no_calla():
    """La mitad de accesibilidad se saltaba en silencio: `lugar` es obligatorio
    en el dominio y sin el no se puede comprobar de donde viene nadie."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "personajes_presentes": ["marta"], "pov": "marta", "pov_usado": "marta"}
    h = puertas.verificar(esc, {}, _mundo())
    assert _sin_veredicto(h, "INV-02")


def test_inv17_con_rango_y_sin_palabras_no_calla():
    """Si hay rango, el texto se puede contar. No contarlo es no comprobarlo."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "lugar": "salon", "pov": "marta", "pov_usado": "marta",
           "longitud_objetivo": [1200, 2200]}
    h = puertas.verificar(esc, {}, _mundo())
    assert _sin_veredicto(h, "INV-17")


def test_un_campo_opcional_ausente_no_produce_nada():
    """El reverso, y es lo que evita que esto se vuelva ruido: sin
    `longitud_objetivo` no hay rango que comprobar, y eso es legitimo."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vida", "signo": "negativo"},
           "lugar": "salon", "pov": "marta", "pov_usado": "marta"}
    h = puertas.verificar(esc, {}, _mundo())
    assert not any(x.invariante == "INV-17" for x in h)
    assert not any(x.invariante == "INV-02" for x in h)


# --- SPEC-17 C-4: `t` dentro de una escena es un intervalo ----------------

def test_inv03_lo_que_la_escena_revela_cuenta_para_sus_propias_acciones():
    """`F-33`: aprender y actuar en la misma escena es el caso narrativo mas
    comun que existe -Marta encuentra la llave y abre el sotano- y bloqueaba
    siempre, porque la puerta verifica antes de consolidar."""
    delta = {"revelaciones": [{"sujeto": "marta", "hecho": "hec-9"}],
             "acciones": [{"personaje": "marta", "hecho": "hec-9"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, _mundo())
    assert not any(x.invariante == "INV-03" for x in h)


def test_inv03_la_revelacion_de_otro_no_habilita_mi_accion():
    """El caso negativo que conserva el filo que queda: que Ana se entere no
    hace que Marta lo sepa, y esa distincion es media novela de terror."""
    delta = {"revelaciones": [{"sujeto": "ana", "hecho": "hec-9"}],
             "acciones": [{"personaje": "marta", "hecho": "hec-9"}]}
    h = puertas.verificar(_escena_de_conocimiento(), delta, _mundo())
    assert any(x.invariante == "INV-03" for x in h)


# --- SPEC-19 / INV-18: lo prometido contra lo entregado -------------------

def _escena_que_promete(establece):
    return {"id": "e2", "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
            "pov": "marta", "lugar": "salon", "pov_usado": "marta",
            "beats": [{"id": "b1", "establece": establece}]}


def test_inv18_un_hecho_prometido_y_no_entregado_es_hallazgo():
    """`F-37` tal cual ocurrio: la escaleta decia "Marta encuentra el sotano
    cerrado", el texto paso todas las puertas y el hecho quedo sin establecer.
    Dos escenas despues `INV-03` bloqueo por la consecuencia."""
    h = puertas.verificar(_escena_que_promete(["hec-sotano"]), {}, _mundo())
    inv18 = [x for x in h if x.invariante == "INV-18"]
    assert inv18 and inv18[0].severidad is Severidad.MAYOR
    assert "hec-sotano" in inv18[0].descripcion


def test_inv18_si_el_delta_lo_declara_no_hay_hallazgo():
    delta = {"revelaciones": [{"sujeto": "marta", "hecho": "hec-sotano"}]}
    h = puertas.verificar(_escena_que_promete(["hec-sotano"]), delta, _mundo())
    assert not any(x.invariante == "INV-18" for x in h)


def test_inv18_no_dice_nada_de_lo_entregado_y_no_prometido():
    """`SPEC-15` P-4 ya decidio que un hecho que el plan no previo **se permite
    y se marca**. Convertirlo aqui en defecto contradiria esa decision."""
    delta = {"revelaciones": [{"sujeto": "marta", "hecho": "hec-improvisado"}]}
    h = puertas.verificar(_escena_que_promete([]), delta, _mundo())
    assert not any(x.invariante == "INV-18" for x in h)


def test_inv18_una_escena_sin_promesas_no_produce_nada():
    """`establece[]` es opcional: la mayoria de beats no añaden al canon."""
    assert not any(x.invariante == "INV-18"
                   for x in puertas.verificar(_escena_que_promete([]), {}, _mundo()))


def test_inv18_beats_en_prosa_no_rompen_la_comprobacion():
    """Los `beats` siguen siendo prosa **y ademas** pueden llevar referencias.
    Una escaleta antigua tiene cadenas donde esta espera diccionarios."""
    esc = dict(_escena_que_promete([]), beats=["Marta baja al sotano"])
    assert not any(x.invariante == "INV-18"
                   for x in puertas.verificar(esc, {}, _mundo()))


# --- `INV-02` y el acto que cambia lo que vigila (decision del autor, 2026-09-24) ---

def _mundo_con_gato():
    m = _mundo()
    m["entidades_vivas"]["gato"] = "desaparecido"
    m["ubicaciones"]["gato"] = "salon"
    return m


def test_inv02_un_desaparecido_que_la_escena_devuelve_a_vivo_puede_estar_presente():
    """La novela de ejemplo se paro en un reencuentro: el gato se perdio en el capitulo 8
    y reaparecia en el 9. `INV-02` miraba el mundo **antes** del delta de la propia escena,
    y asi ningun reencuentro era escribible. Es la familia de `SPEC-16`: una invariante no
    puede bloquear el acto que cambia lo que ella vigila."""
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
           "personajes_presentes": ["gato"], "lugar": "salon"}
    delta = {"cambios_de_estado_vital": [{"personaje": "gato", "de": "desaparecido",
                                          "a": "vivo"}]}
    assert not [x for x in puertas.verificar(esc, delta, _mundo_con_gato())
                if x.invariante == "INV-02"]


def test_inv02_un_desaparecido_que_la_escena_no_devuelve_sigue_bloqueando():
    esc = {"id": "e1", "cambio_de_valor": {"eje": "vinculo", "signo": "positivo"},
           "personajes_presentes": ["gato"], "lugar": "salon"}
    assert any(x.invariante == "INV-02"
               for x in puertas.verificar(esc, {}, _mundo_con_gato()))
