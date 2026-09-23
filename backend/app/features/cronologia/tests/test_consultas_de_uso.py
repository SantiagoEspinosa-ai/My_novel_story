"""`SPEC-21` C-2 — Cada consumidor cuenta los tipos que le sirven, y solo esos.

Estas son las pruebas que sostienen la parte parametrizable: no fijan que
significa "usar un hecho", fijan que **cada capacidad puede decidirlo por su
cuenta** y que cambiar de opinion es editar una constante, no migrar la base.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.cronologia import consultas, repository as repo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    # Un hecho con las cuatro relaciones repartidas en cuatro capitulos. Es el
    # caso que distingue a los cuatro consumidores: cada uno ve un subconjunto
    # distinto, y si alguno viera los cuatro capitulos estaria contando de mas.
    repo.registrar_usos(c, [
        {"hecho": "h-llave", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA},
        {"hecho": "h-llave", "escena": "e2", "capitulo": "cap-2",
         "tipo": U.MENCIONA, "origen": O.REGLA},
        {"hecho": "h-llave", "escena": "e3", "capitulo": "cap-3",
         "tipo": U.DEPENDE, "origen": O.DELTA},
        {"hecho": "h-llave", "escena": "e4", "capitulo": "cap-4",
         "tipo": U.CONTRADICE, "origen": O.HUMANO},
    ])
    return c


def test_aparecer_en_un_capitulo_se_satisface_con_mencionarlo(con):
    """Si el lector pidio que salga un gato negro, lo pedido es que **salga**.

    Exigir que la trama dependa de el daria por incumplido un encargo que el
    texto cumplio.
    """
    r = consultas.aparece_en_algun_capitulo(con, "h-llave")
    assert r["aparece"] is True
    assert r["capitulos"] == ["cap-2"]


def test_un_hecho_que_solo_se_establece_no_cuenta_como_aparicion(con):
    """El caso negativo, y el que obliga a que los tipos sean cuatro.

    Un hecho que el delta declara establecido pero que el texto no llega a
    nombrar es exactamente el fallo que un validador de elementos
    personalizados existe para cazar: lo prometido en la estructura y ausente
    en la pagina.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-gato", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA}])
    assert consultas.aparece_en_algun_capitulo(con, "h-gato")["aparece"] is False


def test_la_regeneracion_selectiva_ignora_la_mencion_de_paso(con):
    """`cap-2` solo lo nombra: reescribirlo seria reescribir por una alusion."""
    assert consultas.capitulos_a_regenerar(con, "h-llave") == ["cap-1", "cap-3"]


def test_la_ficha_de_personaje_enlaza_a_los_tres_tipos_de_uso(con):
    """La ficha enlaza a donde el lector encontrara algo. `contradice` no es
    un sitio donde encontrar el hecho: es donde encontrarlo roto."""
    assert consultas.capitulos_de_la_ficha(con, "h-llave") == [
        "cap-1", "cap-2", "cap-3"]


def test_lean_recibe_el_grafo_entero_incluida_la_arista_negativa(con):
    """Un demostrador necesita las cuatro: sin `contradice` no puede probar
    que el canon es consistente, solo que se usa mucho."""
    assert consultas.capitulos_donde_se_usa(con, "h-llave", consultas.PARA_LEAN) == [
        "cap-1", "cap-2", "cap-3", "cap-4"]


def test_cambiar_de_opinion_es_pasar_otros_tipos_sin_migrar_nada(con):
    """La prueba de que la decision quedo parametrizada y no fijada.

    Si mañana se decide que la regeneracion selectiva tambien debe arrastrar
    las menciones, es pasar otro conjunto: las cuatro filas ya estan escritas.
    """
    assert consultas.capitulos_donde_se_usa(
        con, "h-llave", (U.ESTABLECE, U.DEPENDE, U.MENCIONA)) == [
        "cap-1", "cap-2", "cap-3"]


def test_un_uso_sin_capitulo_se_dice_y_no_se_cuela_como_capitulo(con):
    """Las escenas anteriores a `SPEC-21` no tienen capitulo. Devolver `None`
    dentro de la lista de capitulos lo convertiria en un capitulo llamado
    `None` en cuanto alguien lo pintara."""
    repo.registrar_usos(con, [
        {"hecho": "h-pozo", "escena": "e9", "capitulo": None,
         "tipo": U.MENCIONA, "origen": O.REGLA}])
    r = consultas.aparece_en_algun_capitulo(con, "h-pozo")
    assert r["capitulos"] == []
    assert r["usos_sin_capitulo"] == 1


def test_contradice_declara_que_nadie_lo_deduce(con):
    """`SPEC-21`: el tipo existe, la tabla lo admite y no lo rellena nadie.

    Quien pregunte tiene que poder distinguir "no hay contradicciones" de
    "nadie ha buscado contradicciones".
    """
    assert consultas.cobertura_de_tipos()[U.CONTRADICE] == "no_se_deduce"
    assert consultas.cobertura_de_tipos()[U.MENCIONA] == "regla"


def test_la_regeneracion_puede_pedir_solo_lo_observado_o_solo_lo_declarado(con):
    """Los dos conjuntos por separado, que es lo que hace falta para medirlos.

    `SPEC-23` `S-5` compara **observado** -lo que el ensamblador metio en el
    prompt: sobre-aproxima y falla ruidoso- con **declarado** -lo que el modelo
    dice que uso: se ajusta mas y falla en silencio-. Elegir entre los dos sin
    haber medido cuanto se separan seria elegir a ciegas, y para medirlo hay que
    poder pedir cada uno.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e9", "capitulo": "cap-9",
         "tipo": U.DEPENDE, "origen": O.REGLA}])
    assert consultas.capitulos_a_regenerar(con, "h-llave", (O.DELTA,)) == [
        "cap-1", "cap-3"]
    assert consultas.capitulos_a_regenerar(con, "h-llave", (O.REGLA,)) == ["cap-9"]


def test_una_fila_observada_entra_en_la_regeneracion_sin_tocar_constantes(con):
    """El filtro por defecto es **por tipo**, no por origen.

    Es lo que mantiene barata la decision que `SPEC-23` tiene pendiente: el dia
    que exista la fuente observada, sus filas `depende` las cuenta esta consulta
    solas. Si el filtro fuera tambien por origen, incorporarlas seria volver a
    decidir en vez de empezar a escribir.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e9", "capitulo": "cap-9",
         "tipo": U.DEPENDE, "origen": O.REGLA}])
    assert consultas.capitulos_a_regenerar(con, "h-llave") == [
        "cap-1", "cap-3", "cap-9"]


# --- La medida que decide si `menciona` entra en la regeneracion ------------


def test_el_arrastre_de_incluir_mencion_se_mide_por_hecho(con):
    """`SPEC-21` C-2: `menciona` entra, **pero medido antes de decidirlo**.

    Excluirlo era elegir el fallo silencioso en el unico eje medido por codigo,
    y el argumento para excluirlo era una intuicion de coste -"arrastraria media
    novela"- que nunca se comprobo. El coste se puede medir gratis, asi que esta
    es la medida y no una estimacion.
    """
    r = consultas.arrastre_de_incluir_mencion(con, ["h-llave"])
    assert r["declarado"] == 2          # cap-1 y cap-3
    assert r["con_mencion"] == 3        # + cap-2
    assert r["crecimiento"] == 1
    assert r["por_hecho"]["h-llave"]["capitulos_que_se_añaden"] == ["cap-2"]


def test_un_hecho_sin_menciones_no_arrastra_nada(con):
    """El caso negativo: si `menciona` no aportara nunca capitulos nuevos, la
    medida tiene que decir cero y no un numero pequeño cualquiera."""
    repo.registrar_usos(con, [
        {"hecho": "h-gato", "escena": "e1", "capitulo": "cap-1",
         "tipo": U.ESTABLECE, "origen": O.DELTA}])
    r = consultas.arrastre_de_incluir_mencion(con, ["h-gato"])
    assert r["crecimiento"] == 0


def test_la_mencion_en_un_capitulo_ya_arrastrado_no_cuenta_como_crecimiento(con):
    """Lo que encarece no es mencionar: es mencionar **donde no se dependia**.

    Un capitulo que ya entraba por `depende` y ademas nombra el hecho no añade
    trabajo. Contarlo inflaria la medida y haria parecer caro justo lo que no
    lo es.
    """
    repo.registrar_usos(con, [
        {"hecho": "h-llave", "escena": "e3", "capitulo": "cap-3",
         "tipo": U.MENCIONA, "origen": O.REGLA}])
    r = consultas.arrastre_de_incluir_mencion(con, ["h-llave"])
    assert r["crecimiento"] == 1, "cap-3 ya entraba: no es trabajo nuevo"
