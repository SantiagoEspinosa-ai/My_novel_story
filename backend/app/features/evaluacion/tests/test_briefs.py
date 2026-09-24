"""`PLAN-31` E1: el formato de los briefs de evaluacion (`SPEC-31` `RF-01`).

Cada brief lleva `_meta`, una ficha **o** un guion de entrevista —nunca las dos— y
`que_deberia_pasar`. Punto ciego declarado: «inventados» es una declaracion del fichero,
no algo que esta prueba pueda comprobar.
"""

import json
import pathlib

import pytest

from app.features.evaluacion import briefs

EVALS = pathlib.Path(__file__).resolve().parents[5] / "harness" / "evals"


def _ficheros():
    return sorted(EVALS.glob("brief-*.json"))


def _datos_de(nombre):
    return json.loads((EVALS / nombre).read_text(encoding="utf-8"))


def test_cada_brief_de_harness_evals_carga_con_su_esquema():
    assert _ficheros(), "no hay ningun brief en harness/evals"
    for ruta in _ficheros():
        b = briefs.cargar(ruta)
        assert b.meta.id == ruta.stem, ruta.name
        assert (b.ficha is None) != (b.guion is None), ruta.name
        assert b.que_deberia_pasar, ruta.name


def test_un_brief_sin_datos_inventados_declarados_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    del datos["_meta"]["datos"]
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)
    datos["_meta"]["datos"] = "reales"
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_un_brief_con_ficha_y_guion_a_la_vez_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    datos["guion"] = {"turnos": [{"respuesta": "se llama Ana"}, {"cerrar": True}]}
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_un_brief_sin_ficha_ni_guion_no_carga():
    datos = _datos_de("brief-incoherencia-temporal.json")
    del datos["ficha"]
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)


def test_el_brief_temporal_es_una_ficha_de_misterio_y_conserva_sus_ganchos():
    b = briefs.cargar(EVALS / "brief-incoherencia-temporal.json")
    assert b.ficha.genero.value == "misterio"
    assert set(b.por_que_provoca_cada_incoherencia) == {"L-1", "L-2", "L-3", "L-4"}


# --- `PLAN-31` E2: los cuatro briefs que faltan ---------------------------------

LOS_CINCO = {"brief-base", "brief-injection", "brief-incoherencia-temporal",
             "brief-contradicciones", "brief-vetadas-por-variantes"}


def _brief(nombre):
    return briefs.cargar(EVALS / (nombre + ".json"))


def test_hay_cinco_briefs_y_cubren_los_propositos_de_la_spec():
    """`SPEC-31` `RF-01` y `RF-10`: base, injection, temporal, contradicciones y
    vetadas por variantes. La injection va por el texto libre, asi que es un guion."""
    todos = {ruta.stem: briefs.cargar(ruta) for ruta in _ficheros()}
    assert set(todos) == LOS_CINCO
    injection = todos["brief-injection"]
    assert injection.guion is not None
    assert any(t.texto_libre for t in injection.guion.turnos)
    assert todos["brief-contradicciones"].guion is not None
    for b in todos.values():
        assert b.meta.datos == "inventados"


def test_el_brief_base_es_la_ficha_de_ejemplo_del_repositorio():
    """`RF-10`: el base es tambien el brief de ejemplo del README. Se referencia, no se
    copia: dos copias de la misma ficha acaban divergiendo."""
    base = _brief("brief-base")
    ejemplo = json.loads((EVALS.parents[1] / "ejemplos" / "brief-ejemplo.json")
                         .read_text(encoding="utf-8"))
    assert base.ficha.model_dump(mode="json", exclude_defaults=True) == \
        briefs.FichaDeEntrevista.model_validate(ejemplo).model_dump(
            mode="json", exclude_defaults=True)
    assert _datos_de("brief-base.json").get("ficha_en") == "ejemplos/brief-ejemplo.json"


def test_el_brief_de_injection_trae_una_instruccion_que_el_detector_ve_y_otra_que_no():
    """La segunda esta puesta a proposito: el detector es una lista de patrones y tiene
    falsos negativos (`SPEC-25` `RF-14`). El brief mide que defensa la para entonces."""
    from app.features.entrevista.texto_libre import detectar_instrucciones
    b = _brief("brief-injection")
    textos = [t.texto_libre for t in b.guion.turnos if t.texto_libre]
    assert sorted(i.el_detector_la_ve for i in b.instrucciones_inyectadas) == [False, True]
    for i in b.instrucciones_inyectadas:
        assert bool(detectar_instrucciones(i.texto)) is i.el_detector_la_ve, i.texto
        assert any(i.texto in t for t in textos), "la instruccion va dentro de un texto libre"


def _ficha_antes_del_primer_cierre(b):
    ultima = None
    for t in b.guion.turnos:
        if t.cerrar:
            return ultima
        ultima = t.ficha_esperada or ultima
    return ultima


def test_la_ficha_esperada_del_brief_de_contradicciones_dispara_las_tres_reglas():
    """Las tres deterministas de `SPEC-25` `RF-08`, con las reglas de `sistema.json`.
    `juicio_del_modelo` no cuenta: la emite el Entrevistador, no el codigo."""
    from datetime import date
    from app.commons.configuracion import carga
    from app.features.entrevista.contradicciones import contradicciones
    b = _brief("brief-contradicciones")
    ficha = _ficha_antes_del_primer_cierre(b)
    assert ficha is not None, "el guion intenta cerrar con la ficha contradictoria"
    r = contradicciones(ficha, carga.cargar_sistema().contradicciones, date.today().year)
    tipos = {c.tipo.value for c in r.abiertas}
    assert tipos == {"edad_frente_a_genero", "edad_frente_a_ocasion", "recuerdo_frente_a_edad"}
    assert tipos == {t.value for t in b.contradicciones_que_provoca}
    final = [t.ficha_esperada for t in b.guion.turnos if t.ficha_esperada][-1]
    assert not contradicciones(final, carga.cargar_sistema().contradicciones,
                               date.today().year).abiertas, "el guion las resuelve"


def test_el_brief_de_vetadas_invita_a_una_variante_de_cada_vetada():
    """`RF-12`: evadir las vetadas con variantes (acentos, plurales). Cada vetada de la
    ficha tiene al menos una variante, distinta de la forma vetada, que la normalizacion
    de `commons/politica/` caza. Lo que no caza va en `que_deberia_pasar`."""
    from app.commons.politica.vetadas import coincidencias, formas_de_nombre
    b = _brief("brief-vetadas-por-variantes")
    vetadas = list(b.ficha.vetadas) + list(b.ficha.nombres_vetados)
    assert vetadas and set(b.variantes_que_intenta) == set(vetadas)
    for vetada in vetadas:
        formas = formas_de_nombre(vetada) if vetada in b.ficha.nombres_vetados else [vetada]
        assert b.variantes_que_intenta[vetada], vetada
        for variante in b.variantes_que_intenta[vetada]:
            assert variante != vetada
            assert coincidencias(variante, formas), (vetada, variante)


# --- `PLAN-31` E12: la extension en los briefs (`SPEC-32`) --------------------------

def test_un_brief_sin_extension_no_carga():
    """`SPEC-32`: la extension se pregunta, y un brief que no la fija se ejecutaria con el
    rango entero de 1.000-1.500 palabras, que no es ninguna de las tres opciones."""
    datos = _datos_de("brief-incoherencia-temporal.json")
    del datos["ficha"]["extension"]
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(datos)
    guion = _datos_de("brief-contradicciones.json")
    for t in guion["guion"]["turnos"]:
        (t.get("ficha_esperada") or {}).pop("extension", None)
    with pytest.raises(briefs.BriefInvalido):
        briefs.validar(guion)


def test_cada_brief_fija_una_de_las_extensiones_de_spec_32():
    from app.commons.dominio.enumeraciones import ExtensionDeCapitulo
    for ruta in _ficheros():
        b = briefs.cargar(ruta)
        ficha = b.ficha or [t.ficha_esperada for t in b.guion.turnos if t.ficha_esperada][-1]
        assert ficha.extension in set(ExtensionDeCapitulo), ruta.name
