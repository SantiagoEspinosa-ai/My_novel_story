"""F5 — Los bloques llevan texto, no numeros.

Hasta aqui el recorte operaba sobre un diccionario de tamaños: nunca se
acercaba al techo y `VER-37` no se podia contestar. Estas pruebas comprueban
que el material entra, que el bloque 4 lleva lo que leen las bloqueantes, y que
el recorte deja rastro de lo que se fue.
"""

from app.features.contexto import ensamblado, recorte
from app.features.contexto.bloques import BLOQUES, Clase

MATERIAL = {
    "resumenes": [{"escena": "e1", "texto": "Marta llega a la casa."},
                  {"escena": "e2", "texto": "Marta encuentra el sotano cerrado."}],
    "fichas": [{"entidad": "per-marta", "version_en_t": "e2",
                "resumen": "Heredera, insomne desde la mudanza."}],
    "escena_anterior": "El pasillo estaba a oscuras. " * 20,
    "mundo": {"entidades_vivas": {"per-marta": "vivo"},
              "ubicaciones": {"per-marta": "lug-salon"},
              "accesos": {"lug-salon": ["lug-sotano"]},
              "conocimiento": {("per-marta", "hec-llave"): {"desde": "e1",
                                                            "grado": "sabe"}}},
    "problemas": [{"invariante": "INV-17", "descripcion": "944 palabras"}],
    "inmutable": "Terror domestico. Tercera limitada. Pasado.",
}


def test_estan_los_siete_bloques_en_el_orden_de_2_4():
    bloques = ensamblado.montar(MATERIAL)
    assert list(bloques) == [b.nombre for b in BLOQUES]


def test_el_bloque_4_lleva_lo_que_leen_las_bloqueantes():
    """`INV-02` lee vivos, donde y accesos; `INV-03` el conocimiento."""
    texto = ensamblado.montar(MATERIAL)["estado_y_conocimiento"]
    for debe in ("vivos", "donde", "accesos", "per-marta sabe hec-llave desde e1"):
        assert debe in texto


def test_los_resumenes_y_las_fichas_entran_con_su_version():
    bloques = ensamblado.montar(MATERIAL)
    assert "[e1]" in bloques["condensaciones"]
    assert "@e2" in bloques["fichas_y_setups"], "la ficha dice de cuando es"


def test_los_problemas_del_intento_anterior_entran():
    assert "944 palabras" in ensamblado.montar(MATERIAL)["problemas_del_intento_anterior"]


def test_la_reserva_de_salida_no_tiene_texto_y_ocupa_igual():
    """Recortarla no es recortar contexto: es truncar la escena."""
    bloques = ensamblado.montar(MATERIAL)
    assert bloques["reserva_de_salida"] == ""
    assert ensamblado.tamanos(bloques, reserva_de_salida=20_000)["reserva_de_salida"] == 20_000


def test_el_tamano_sale_del_texto_de_verdad():
    tam = ensamblado.tamanos(ensamblado.montar(MATERIAL), reserva_de_salida=0)
    assert tam["escena_anterior"] > 0
    assert tam["condensaciones"] > 0


def test_un_bloque_eliminado_queda_vacio_pero_no_desaparece():
    """Quien lea despues tiene que ver que estaba y se fue."""
    bloques = ensamblado.montar(MATERIAL)
    plan = [recorte.Paso("condensaciones", Clase.ELIMINACION)]
    tras = ensamblado.aplicar_recorte(bloques, plan)
    assert tras["condensaciones"] == ""
    assert "condensaciones" in tras


def test_un_bloque_reducido_conserva_parte():
    bloques = ensamblado.montar(MATERIAL)
    plan = [recorte.Paso("escena_anterior", Clase.REDUCCION)]
    tras = ensamblado.aplicar_recorte(bloques, plan)
    assert 0 < len(tras["escena_anterior"]) < len(bloques["escena_anterior"])


def test_el_recorte_de_2_4_opera_sobre_el_texto_montado():
    """El circuito de F5: montar, medir, planificar, aplicar."""
    bloques = ensamblado.montar(MATERIAL)
    tam = ensamblado.tamanos(bloques, reserva_de_salida=100)
    plan = recorte.planificar(tam, techo=180)
    tras = ensamblado.aplicar_recorte(bloques, plan)
    assert plan, "con ese techo tenia que recortar"
    assert sum(len(v) for v in tras.values()) < sum(len(v) for v in bloques.values())


def test_la_reserva_irreducible_es_lo_que_hace_fallar_rf26():
    """El caso que aparecio escribiendo estas pruebas, y vale la pena fijarlo.

    Con un techo por debajo de la propia reserva de salida, **no hay recorte
    que valga**: los otros seis bloques se reducen, tres se eliminan, y sigue
    sin caber porque lo que no cabe es el sitio apartado para la respuesta.
    `RF-26` falla en vez de generar, que es lo correcto — generar ahi seria
    truncar la escena.
    """
    import pytest

    tam = ensamblado.tamanos(ensamblado.montar(MATERIAL), reserva_de_salida=100)
    with pytest.raises(recorte.NoCabe) as e:
        recorte.planificar(tam, techo=50)
    tocados = {p.bloque for p in e.value.plan}
    assert "reserva_de_salida" not in tocados, "es irreducible y no se toca"
    assert "inmutable" not in tocados


# --- SPEC-15: los hechos declarados van en el bloque 4 ---------------------

def test_el_bloque_4_lleva_los_hechos_declarados_con_su_enunciado():
    """Son lo que el modelo puede citar. Sin ellos el prompt decia
    "hechos: (ninguno)" y el modelo, correctamente, no citaba ninguno."""
    material = dict(MATERIAL, hechos=[
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio",
         "establecido_en": None}])
    texto = ensamblado.montar(material)["estado_y_conocimiento"]
    assert "hec-llave" in texto
    assert "La llave del sotano se perdio" in texto


def test_un_hecho_sin_establecer_se_distingue_de_uno_establecido():
    """`INV-03` compara contra esto: revelar no puede preceder a establecer."""
    material = dict(MATERIAL, hechos=[
        {"id": "hec-a", "enunciado": "a", "establecido_en": "e1"},
        {"id": "hec-b", "enunciado": "b", "establecido_en": None}])
    texto = ensamblado.montar(material)["estado_y_conocimiento"]
    linea_a = [l for l in texto.splitlines() if l.startswith("hec-a")][0]
    linea_b = [l for l in texto.splitlines() if l.startswith("hec-b")][0]
    assert "sin establecer" not in linea_a
    assert "sin establecer" in linea_b


def test_sin_hechos_declarados_el_bloque_4_sigue_montando():
    """El caso de la obra que aun no tiene plan: no revienta, sale vacio."""
    assert "hechos declarados" in ensamblado.montar(MATERIAL)["estado_y_conocimiento"]
