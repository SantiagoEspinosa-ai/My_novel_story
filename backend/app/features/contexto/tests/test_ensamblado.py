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


def test_la_reserva_de_salida_no_ocupa_nada():
    """`SPEC-14` C-1 la retiro: el harness **no administra la ventana** del
    subagente, asi que no puede apartar sitio en ella.

    Esta prueba afirmaba lo contrario y por eso `F-35` sobrevivio: el bloque
    inyectaba 20.000 tokens en el total contra el que se compara el techo, y el
    numero que salia era plausible. Un informe decia 20.225 cuando el contexto
    real eran 225.
    """
    bloques = ensamblado.montar(MATERIAL)
    assert bloques["reserva_de_salida"] == ""
    assert ensamblado.tamanos(bloques)["reserva_de_salida"] == 0


def test_el_total_medido_es_solo_lo_que_se_manda():
    """El numero que se informa como contexto tiene que ser contexto."""
    tam = ensamblado.tamanos(ensamblado.montar(MATERIAL))
    sin_reserva = sum(v for n, v in tam.items() if n != "reserva_de_salida")
    assert sum(tam.values()) == sin_reserva


def test_el_tamano_sale_del_texto_de_verdad():
    tam = ensamblado.tamanos(ensamblado.montar(MATERIAL))
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
    tam = ensamblado.tamanos(bloques)
    plan = recorte.planificar(tam, techo=180)
    tras = ensamblado.aplicar_recorte(bloques, plan)
    assert plan, "con ese techo tenia que recortar"
    assert sum(len(v) for v in tras.values()) < sum(len(v) for v in bloques.values())


def test_lo_irreducible_es_lo_que_hace_fallar_rf26():
    """Con un techo por debajo de lo que no se puede recortar, **no hay recorte
    que valga**: los demas bloques se reducen, tres se eliminan, y sigue sin
    caber. `RF-26` falla en vez de generar, que es lo correcto — generar ahi
    seria mandar un contexto mutilado.

    Esta prueba se apoyaba en la reserva de salida, que `SPEC-14` C-1 retiro
    (`F-35`). El irreducible que la sostiene ahora es el **bloque inmutable**:
    la premisa y la guia de estilo, sin las cuales la escena no es de esta
    obra. `RF-26` no dependia de la reserva; dependia de que **algo** sea
    irreducible.
    """
    import pytest

    tam = ensamblado.tamanos(ensamblado.montar(MATERIAL))
    with pytest.raises(recorte.NoCabe) as e:
        recorte.planificar(tam, techo=10)
    tocados = {p.bloque for p in e.value.plan}
    assert "inmutable" not in tocados, "es irreducible y no se toca"
    assert "reserva_de_salida" not in tocados


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


def test_el_bloque_4_dice_donde_ocurre_la_escena_siguiente():
    """`F-149`: sin esto el Escritor podia dejar a los presentes donde la escena siguiente
    no llega, y `INV-02` solo lo veia un capitulo tarde."""
    texto = ensamblado.montar(dict(MATERIAL, lugar_siguiente="lug-sotano"))[
        "estado_y_conocimiento"]
    assert "escena siguiente: lug-sotano" in texto
    assert "escena siguiente" not in ensamblado.montar(MATERIAL)["estado_y_conocimiento"]
