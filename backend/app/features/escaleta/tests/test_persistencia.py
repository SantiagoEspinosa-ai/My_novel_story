"""E1 — Donde vive lo que el modelo devuelva.

Hasta aqui habia tablas de obra, capitulo, entidad y trabajo. Sin `Escena`,
`Borrador` y `Hallazgo` no hay donde poner el resultado de una generacion, y el
bucle de E2 no tendria contra que escribir.
"""

import sqlite3

import pytest

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S
from app.features.escaleta import repository as repo


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    return c


def _sembrar(con):
    repo.guardar_escaleta(con, "obra-1", [
        {"id": "e1", "orden": 1, "pov": "per-marta", "lugar": "lug-salon", 
         "cambio_de_valor": {"eje": "seguridad", "signo": "negativo"},
         "beats": ["b1"], "longitud_objetivo": [1200, 2200]},
    ])


def test_una_escaleta_validada_se_guarda_y_se_relee(con):
    _sembrar(con)
    escenas = repo.escenas_de(con, "obra-1")
    assert len(escenas) == 1
    assert escenas[0]["estado"] == EE.PLANIFICADA.value
    assert escenas[0]["longitud_objetivo"] == [1200, 2200]


def test_la_version_del_borrador_crece_por_escena_y_no_globalmente(con):
    _sembrar(con)
    v1 = repo.guardar_borrador(con, "e1", texto="primero", modelo="doble", prompt_hash="aa")
    v2 = repo.guardar_borrador(con, "e1", texto="segundo", modelo="doble", prompt_hash="bb")
    assert (v1, v2) == (1, 2)
    assert repo.intentos_de(con, "e1") == 2


def test_guardar_un_borrador_deja_la_escena_en_generada(con):
    _sembrar(con)
    repo.guardar_borrador(con, "e1", texto="x", modelo="doble", prompt_hash="aa")
    assert repo.escena(con, "e1")["estado"] == EE.GENERADA.value


def test_un_hallazgo_se_guarda_con_su_verificador(con):
    """`VER-12`: sin `verificador`, el recuento por invariante mezcla dos cosas."""
    _sembrar(con)
    repo.guardar_hallazgo(con, invariante="INV-07", verificador="verificador_de_reglas",
                          escena="e1", severidad=S.MAYOR, estado=EH.ABIERTO,
                          descripcion="sin beat que sirva a un arco")
    abiertos = repo.hallazgos_abiertos(con, "e1")
    assert abiertos[0]["verificador"] == "verificador_de_reglas"


def test_un_sin_veredicto_cuenta_como_abierto(con):
    """Nadie ha dicho que este bien: su verificador no llego a emitir juicio."""
    _sembrar(con)
    repo.guardar_hallazgo(con, invariante="INV-10", verificador="juez_de_rubrica",
                          escena="e1", severidad=S.MAYOR, estado=EH.SIN_VEREDICTO,
                          descripcion="no se pudo interpretar el veredicto")
    assert len(repo.hallazgos_abiertos(con, "e1")) == 1


def test_un_hallazgo_descartado_no_cuenta_como_abierto(con):
    _sembrar(con)
    repo.guardar_hallazgo(con, invariante="INV-07", verificador="verificador_de_reglas",
                          escena="e1", severidad=S.MAYOR, estado=EH.DESCARTADO,
                          descripcion="falso positivo")
    assert repo.hallazgos_abiertos(con, "e1") == []


def test_el_borrador_aceptado_se_marca_y_la_escena_lo_apunta(con):
    _sembrar(con)
    repo.guardar_borrador(con, "e1", texto="primero", modelo="doble", prompt_hash="aa")
    repo.aceptar_borrador(con, "e1", version=1, rindiendose=False)
    e = repo.escena(con, "e1")
    assert e["estado"] == EE.ACEPTADA.value
    assert e["borrador_aceptado"] == 1


def test_aceptar_rindiendose_deja_otro_estado(con):
    """`SPEC-10`: no son el mismo hecho, y quien lea el manuscrito lo necesita."""
    _sembrar(con)
    repo.guardar_borrador(con, "e1", texto="el menos malo", modelo="doble", prompt_hash="aa")
    repo.aceptar_borrador(con, "e1", version=1, rindiendose=True)
    assert repo.escena(con, "e1")["estado"] == EE.ACEPTADA_POR_RENDICION.value


# --- SPEC-15: los hechos los declara el plan -------------------------------

def test_un_hecho_declarado_existe_antes_de_que_nadie_lo_escriba(con):
    """El punto muerto de `F-29`: la lista salia del registro de conocimiento,
    el registro solo crecia con revelaciones, y revelar exigia la lista."""
    repo.declarar_hechos(con, "obra-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    hechos = repo.hechos_declarados(con, "obra-1")
    assert [h["id"] for h in hechos] == ["hec-llave"]
    assert hechos[0]["establecido_en"] is None, "declarado no es establecido"


def test_establecer_un_hecho_dice_donde_lo_establece_el_texto(con):
    repo.declarar_hechos(con, "obra-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    repo.establecer_hecho(con, "hec-llave", "e1")
    assert repo.hechos_declarados(con, "obra-1")[0]["establecido_en"] == "e1"


def test_establecer_dos_veces_conserva_la_primera(con):
    """`escena_de_establecimiento` es donde se establece, no donde se repite."""
    repo.declarar_hechos(con, "obra-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    repo.establecer_hecho(con, "hec-llave", "e1")
    repo.establecer_hecho(con, "hec-llave", "e4")
    assert repo.hechos_declarados(con, "obra-1")[0]["establecido_en"] == "e1"


def test_los_hechos_de_otra_obra_no_se_cuelan(con):
    repo.declarar_hechos(con, "obra-1", [{"id": "hec-a", "enunciado": "a"}])
    repo.declarar_hechos(con, "obra-2", [{"id": "hec-b", "enunciado": "b"}])
    assert [h["id"] for h in repo.hechos_declarados(con, "obra-1")] == ["hec-a"]


# --- F-38: un hallazgo se puede cerrar ------------------------------------
#
# `resuelto` y `descartado` estaban en `estado_de_hallazgo` desde el primer dia
# y **ninguna funcion los escribia**. Un hallazgo nacia abierto y se quedaba
# abierto para siempre, asi que aunque se arreglara la causa el capitulo no
# podia cerrarse nunca.

def test_un_hallazgo_se_resuelve_y_deja_de_contar_como_abierto(con):
    _sembrar(con)
    repo.guardar_hallazgo(con, "INV-17", "v", "e1", S.MAYOR, EH.ABIERTO, "corta")
    ident = repo.hallazgos_abiertos(con, "e1")[0]["id"]
    repo.cerrar_hallazgo(con, ident, EH.RESUELTO, motivo="se reescribio la escena")
    assert repo.hallazgos_abiertos(con, "e1") == []


def test_descartar_no_es_lo_mismo_que_resolver_y_se_distingue(con):
    """Resuelto es *se arreglo*; descartado es *se decidio que no aplica*. Si
    no se distinguieran, el recuento por invariante mezclaria dos cosas y nadie
    podria saber cuantas veces la regla acerto."""
    _sembrar(con)
    repo.guardar_hallazgo(con, "INV-17", "v", "e1", S.MAYOR, EH.ABIERTO, "corta")
    ident = repo.hallazgos_abiertos(con, "e1")[0]["id"]
    repo.cerrar_hallazgo(con, ident, EH.DESCARTADO, motivo="el rango estaba mal")
    fila = con.execute("SELECT estado, motivo_de_cierre FROM hallazgo "
                       "WHERE id = ?", (ident,)).fetchone()
    assert fila[0] == "descartado"
    assert fila[1] == "el rango estaba mal"


def test_cerrar_exige_motivo(con):
    """Un hallazgo cerrado sin motivo es indistinguible de uno que alguien
    cerro para que dejara de molestar."""
    _sembrar(con)
    repo.guardar_hallazgo(con, "INV-17", "v", "e1", S.MAYOR, EH.ABIERTO, "corta")
    ident = repo.hallazgos_abiertos(con, "e1")[0]["id"]
    with pytest.raises(ValueError, match="motivo"):
        repo.cerrar_hallazgo(con, ident, EH.RESUELTO, motivo="")


def test_no_se_puede_cerrar_a_un_estado_que_no_es_de_cierre(con):
    _sembrar(con)
    repo.guardar_hallazgo(con, "INV-17", "v", "e1", S.MAYOR, EH.ABIERTO, "corta")
    ident = repo.hallazgos_abiertos(con, "e1")[0]["id"]
    with pytest.raises(ValueError, match="cierre"):
        repo.cerrar_hallazgo(con, ident, EH.SIN_VEREDICTO, motivo="x")


def test_un_sin_veredicto_tambien_se_puede_cerrar(con):
    """Es lo que permite firmar un capitulo cuando el juez estuvo caido y
    alguien miro la escena a mano."""
    _sembrar(con)
    repo.guardar_hallazgo(con, "INV-04", "v", "e1", S.BLOQUEANTE,
                          EH.SIN_VEREDICTO, "no se pudo comprobar")
    ident = repo.hallazgos_abiertos(con, "e1")[0]["id"]
    repo.cerrar_hallazgo(con, ident, EH.RESUELTO, motivo="revisado a mano")
    assert repo.hallazgos_abiertos(con, "e1") == []
