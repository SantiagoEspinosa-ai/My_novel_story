"""`PLAN-23` A3: versiones de la obra con identidad propia (`SPEC-23` `D-2`, `CE-5`).

Una version es su **numero**, no el conjunto de sus capitulos: con la version como
conjunto, regenerar y volver a aprobarlo todo daba un valor identico al anterior, y
«se conserva la version anterior» pasaba por no poder distinguir nada (`F-43`).
"""

import sqlite3

import pytest

from app.commons.db import migraciones
from app.features.brief import repository as brief

DATOS = {"titulo": "Titulo de prueba", "premisa": "Premisa de prueba"}
CAPS = ["obra-a-c1", "obra-a-c2", "obra-a-c3"]


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    migraciones.migrar(c)
    brief.alta_de_obra(c, "obra-a", DATOS, CAPS)
    return c


def _filas(con, numero):
    return con.execute("SELECT * FROM capitulo_de_version WHERE obra = 'obra-a' AND "
                       "numero = ? ORDER BY orden", (numero,)).fetchall()


def test_dar_de_alta_una_obra_crea_su_version_1(con):
    assert [v["numero"] for v in brief.versiones_de(con, "obra-a")] == [1]
    assert brief.capitulos_de_version(con, "obra-a", 1) == CAPS
    assert brief.version_vigente(con, "obra-a") == 1
    v = brief.versiones_de(con, "obra-a")[0]
    assert v["anterior"] is None and v["commit"] and v["creada_en"]


def test_dar_de_alta_dos_veces_no_crea_otra_version(con):
    brief.alta_de_obra(con, "obra-a", DATOS, CAPS)
    assert [v["numero"] for v in brief.versiones_de(con, "obra-a")] == [1]


def test_crear_la_version_2_no_cambia_ninguna_fila_de_la_1(con):
    antes = _filas(con, 1)
    version_1 = con.execute("SELECT * FROM version_de_obra WHERE numero = 1").fetchall()
    n = brief.crear_version(con, "obra-a", ["obra-a-c1", "obra-a-c2-v2", "obra-a-c3-v2"],
                            anterior=1, commit="def5678")
    assert n == 2
    assert _filas(con, 1) == antes
    assert con.execute("SELECT * FROM version_de_obra WHERE numero = 1").fetchall() == version_1
    assert brief.version_vigente(con, "obra-a") == 2


def test_dos_versiones_con_los_mismos_capitulos_se_distinguen_por_su_numero(con):
    """`CE-5`: lo que la version como conjunto no podia distinguir."""
    brief.crear_version(con, "obra-a", CAPS, anterior=1, commit="def5678")
    assert brief.capitulos_de_version(con, "obra-a", 1) == brief.capitulos_de_version(
        con, "obra-a", 2)
    assert [v["numero"] for v in brief.versiones_de(con, "obra-a")] == [1, 2]


def test_un_capitulo_compartido_es_la_misma_fila_en_las_dos_versiones(con):
    brief.crear_version(con, "obra-a", ["obra-a-c1", "obra-a-c2-v2", "obra-a-c3-v2"],
                        anterior=1, commit="def5678")
    assert con.execute("SELECT COUNT(*) FROM capitulo WHERE id = 'obra-a-c1'").fetchone()[0] == 1
    assert brief.capitulos_de_version(con, "obra-a", 2)[0] == \
        brief.capitulos_de_version(con, "obra-a", 1)[0]


def test_un_capitulo_nuevo_en_la_posicion_3_no_pisa_al_capitulo_3_anterior(con):
    """Regla 7: con `UNIQUE (obra, orden)` y `INSERT OR REPLACE`, el capitulo 3 de la
    version 1 desaparecia al escribir el capitulo 3 de la version 2."""
    brief.crear_version(con, "obra-a", ["obra-a-c1", "obra-a-c2", "obra-a-c3-v2"],
                        anterior=1, commit="def5678")
    ids = {f[0] for f in con.execute("SELECT id FROM capitulo WHERE obra = 'obra-a'")}
    assert {"obra-a-c3", "obra-a-c3-v2"} <= ids
    brief.alta_de_obra(con, "obra-a", DATOS, CAPS)
    ids = {f[0] for f in con.execute("SELECT id FROM capitulo WHERE obra = 'obra-a'")}
    assert "obra-a-c3-v2" in ids


def test_modificar_una_version_creada_falla(con):
    with pytest.raises(sqlite3.DatabaseError, match="no cambia"):
        with con:
            con.execute("UPDATE capitulo_de_version SET capitulo = 'otro' WHERE numero = 1")
    with pytest.raises(sqlite3.DatabaseError, match="no cambia"):
        with con:
            con.execute("DELETE FROM capitulo_de_version WHERE numero = 1")
    with pytest.raises(sqlite3.DatabaseError, match="no cambia"):
        with con:
            con.execute("UPDATE version_de_obra SET \"commit\" = 'x' WHERE numero = 1")
    assert brief.capitulos_de_version(con, "obra-a", 1) == CAPS


def test_una_version_no_admite_capitulos_de_otra_obra(con):
    brief.alta_de_obra(con, "obra-b", DATOS, ["obra-b-c1"])
    with pytest.raises(brief.CapituloDeOtraObra):
        brief.crear_version(con, "obra-a", ["obra-b-c1"], anterior=1, commit="x")
    assert brief.version_vigente(con, "obra-a") == 1


def test_la_migracion_da_la_version_1_a_cada_obra_sin_perder_capitulos():
    """Una base anterior: `capitulo` con `UNIQUE (obra, orden)` y dos obras."""
    con = sqlite3.connect(":memory:")
    con.executescript("""
        CREATE TABLE esquema_version (version INTEGER PRIMARY KEY, descripcion TEXT NOT NULL,
            aplicada_en TEXT NOT NULL DEFAULT (datetime('now')));
        CREATE TABLE capitulo (id TEXT PRIMARY KEY, obra TEXT NOT NULL REFERENCES obra(id),
            orden INTEGER NOT NULL, estado TEXT NOT NULL DEFAULT 'abierto',
            UNIQUE (obra, orden));
        INSERT INTO capitulo VALUES ('x-c2', 'obra-x', 2, 'cerrado');
        INSERT INTO capitulo VALUES ('x-c1', 'obra-x', 1, 'cerrado');
        INSERT INTO capitulo VALUES ('y-c1', 'obra-y', 1, 'abierto');
        CREATE TABLE procedencia (clave TEXT PRIMARY KEY, valor TEXT NOT NULL,
            cuando TEXT NOT NULL DEFAULT (datetime('now')));
        INSERT INTO procedencia (clave, valor) VALUES ('version_del_harness', 'aaa1111');
    """)
    con.executemany("INSERT INTO esquema_version (version, descripcion) VALUES (?, 'x')",
                    [(n,) for n in range(1, 11)])
    con.commit()
    migraciones.migrar(con)
    assert brief.capitulos_de_version(con, "obra-x", 1) == ["x-c1", "x-c2"]
    assert brief.capitulos_de_version(con, "obra-y", 1) == ["y-c1"]
    assert brief.versiones_de(con, "obra-x")[0]["commit"] == "aaa1111"
    assert con.execute("SELECT estado FROM capitulo WHERE id = 'x-c1'").fetchone()[0] == "cerrado"
    # Sin `UNIQUE (obra, orden)`: un capitulo nuevo en la posicion 1 no pisa a nadie.
    con.execute("INSERT INTO capitulo (id, obra, orden) VALUES ('x-c1-v2', 'obra-x', 1)")
    assert con.execute("SELECT COUNT(*) FROM capitulo WHERE obra = 'obra-x'").fetchone()[0] == 3
