"""`SPEC-25` `RF-15`, `RF-16` y `RF-20`: tres niveles en SQLite y el audit log.

El enunciado pide **un caso por nivel y uno de variante**, y son las cuatro
primeras pruebas. Las listas de prueba son inventadas a proposito y distintas
de las de `config/vetadas.json`: si coincidieran, una prueba podria pasar por
leer el fichero real en vez del dato que se le da.
"""

import json
import sqlite3

import pytest

from app.commons.configuracion import carga
from app.commons.configuracion.esquemas import FranjaDeEdad
from app.commons.dominio.enumeraciones import NivelDeVeto as NV
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.politica import auditoria
from app.features.politica import repository as repo
from app.commons.politica.vetadas import coincidencias

FRANJAS = [FranjaDeEdad(nombre="infantil", desde=0, hasta=11),
           FranjaDeEdad(nombre="juvenil", desde=12, hasta=17)]
LISTAS = {"global": ["zoquete"],
          "franjas": {"infantil": ["calavera"], "juvenil": ["resaca"]}}


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    repo.asegurar_tablas(c)
    repo.cargar_listas(c, LISTAS)
    return c


def _formas(con, obra, edad, franjas=FRANJAS):
    return [v.forma for v in repo.vetadas_para(con, obra, edad, franjas)]


def test_nivel_global_se_aplica_a_cualquier_obra(con):
    assert "zoquete" in _formas(con, "obra-a", 40)
    assert "zoquete" in _formas(con, "obra-b", 8)


def test_nivel_franja_de_edad_depende_del_destinatario(con):
    assert "calavera" in _formas(con, "obra-a", 8)
    assert "calavera" not in _formas(con, "obra-a", 40)
    assert "resaca" in _formas(con, "obra-a", 15)


def test_nivel_novela_solo_en_su_obra(con):
    repo.vetar_en_novela(con, "obra-a", nombres=["Luis Pérez"])
    assert "Luis Pérez" in _formas(con, "obra-a", 40)
    assert "Luis" in _formas(con, "obra-a", 40)
    assert "Luis" not in _formas(con, "obra-b", 40)


def test_variante_con_acento_y_plural_contra_la_lista_guardada(con):
    formas = _formas(con, "obra-a", 8)
    assert [c.vetada for c in coincidencias("Vio dos calaveras.", formas)] == [
        "calavera"]


def test_cada_vetada_dice_su_nivel(con):
    repo.vetar_en_novela(con, "obra-a", nombres=["Nala"])
    niveles = {v.forma: v.nivel for v in repo.vetadas_para(con, "obra-a", 8, FRANJAS)}
    assert niveles == {"zoquete": NV.GLOBAL, "calavera": NV.FRANJA_DE_EDAD,
                       "Nala": NV.NOVELA}


def test_una_expresion_vetada_no_se_parte_como_un_nombre(con):
    repo.vetar_en_novela(con, "obra-a", palabras=["tema de familia"])
    assert _formas(con, "obra-a", 40) == ["zoquete", "tema de familia"]


def test_cargar_dos_veces_no_duplica(con):
    repo.cargar_listas(con, LISTAS)
    repo.vetar_en_novela(con, "obra-a", nombres=["Nala"])
    repo.vetar_en_novela(con, "obra-a", nombres=["Nala"])
    assert len(repo.vetadas_para(con, "obra-a", 8, FRANJAS)) == 3


def test_cambiar_la_franja_cambia_el_resultado_sin_tocar_codigo(con):
    """`RF-16`: las franjas son configuracion."""
    solo_bebes = [FranjaDeEdad(nombre="infantil", desde=0, hasta=5)]
    assert "calavera" not in _formas(con, "obra-a", 8, solo_bebes)


def test_una_edad_sin_franja_solo_recibe_global_y_novela(con):
    assert _formas(con, "obra-a", 40) == ["zoquete"]


def test_el_audit_log_guarda_tipo_obra_y_detalle(con):
    auditoria.registrar_decision(con, TD.COINCIDENCIA_VETADA, "obra-a",
                            {"vetada": "zoquete", "escena": "e1", "intento": 1})
    [d] = auditoria.decisiones(con, "obra-a")
    assert d["tipo"] == TD.COINCIDENCIA_VETADA
    assert d["detalle"]["vetada"] == "zoquete"
    assert d["momento"]


def test_las_listas_reales_cargan_con_su_schema():
    """El fichero del repositorio es valido y trae los tres bloques."""
    listas = carga.cargar_vetadas()
    assert listas.global_ and set(listas.franjas) == {"infantil", "juvenil"}
    assert "cadaver" in listas.franjas["infantil"]


def test_un_fichero_de_listas_con_un_campo_de_mas_es_error(tmp_path):
    ruta = tmp_path / "vetadas.json"
    ruta.write_text(json.dumps({"global": [], "franjas": {}, "extra": 1}),
                    encoding="utf-8")
    with pytest.raises(carga.ConfiguracionInvalida):
        carga.cargar_vetadas(ruta)


def test_vetadas_para_devuelve_el_id_de_cada_forma(con):
    """`PLAN-29` E7: una vetada de novela sube a Langfuse por su id, nunca por su forma."""
    repo.vetar_en_novela(con, "obra-a", palabras=["marisol"], nombres=[])
    vetadas = repo.vetadas_para(con, "obra-a", 8, FRANJAS)
    ids = [v.id for v in vetadas]
    assert all(isinstance(i, int) for i in ids) and len(set(ids)) == len(ids)
    marisol = [v for v in vetadas if v.forma == "marisol"][0]
    fila = con.execute("SELECT forma FROM palabra_vetada WHERE rowid = ?",
                       (marisol.id,)).fetchone()
    assert fila[0] == "marisol"
