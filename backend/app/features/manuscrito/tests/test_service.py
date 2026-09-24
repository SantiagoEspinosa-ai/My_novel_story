"""`PLAN-27` E6: solo se exporta una version que paso la puerta de publicacion
(`SPEC-27` `RF-01`, `SPEC-30`). La version es **la unica que hay** mientras no existan
versiones de obra (`PLAN-23`)."""

import json

import pytest

from app.features.manuscrito import service
from app.features.manuscrito.tests.test_libro import con  # noqa: F401  (fixture)


def _veredicto(con, publica, condiciones=(), codigo_lean=0):
    con.execute("""CREATE TABLE IF NOT EXISTS veredicto_de_publicacion (
        obra TEXT NOT NULL, ronda INTEGER NOT NULL, publica INTEGER NOT NULL,
        condiciones TEXT NOT NULL, codigo_lean INTEGER, no_ejecutadas TEXT NOT NULL,
        cuando TEXT NOT NULL DEFAULT (datetime('now')))""")
    n = con.execute("SELECT COUNT(*) FROM veredicto_de_publicacion").fetchone()[0]
    con.execute("INSERT INTO veredicto_de_publicacion (obra, ronda, publica, condiciones, "
                "codigo_lean, no_ejecutadas) VALUES ('o1', ?, ?, ?, ?, '[]')",
                (n + 1, int(publica), json.dumps(list(condiciones)), codigo_lean))
    con.commit()


def test_una_version_sin_veredicto_no_se_exporta(con, tmp_path):
    with pytest.raises(service.VersionNoPublicada) as e:
        service.exportar_pdf(con, "o1", tmp_path / "n.pdf")
    assert "puerta" in str(e.value) and not (tmp_path / "n.pdf").exists()


def test_una_version_que_no_paso_la_puerta_no_se_exporta(con, tmp_path):
    _veredicto(con, False, [{"invariante": "INV-29", "capitulo": "o1-cap-02",
                             "detalle": "rendido"}])
    with pytest.raises(service.VersionNoPublicada) as e:
        service.exportar_pdf(con, "o1", tmp_path / "n.pdf")
    assert "INV-29" in str(e.value)


def test_una_version_con_veredicto_negativo_de_lean_no_se_exporta(con, tmp_path):
    _veredicto(con, False, [{"invariante": "INV-28", "capitulo": None, "detalle": "L-1"}],
               codigo_lean=1)
    with pytest.raises(service.VersionNoPublicada) as e:
        service.exportar_pdf(con, "o1", tmp_path / "n.pdf")
    assert "INV-28" in str(e.value)


def test_cuenta_el_ultimo_veredicto(con, tmp_path):
    _veredicto(con, False, [{"invariante": "INV-29", "capitulo": None, "detalle": "x"}])
    _veredicto(con, True)
    assert service.exportar_pdf(con, "o1", tmp_path / "n.pdf").exists()


def test_una_version_publicada_se_exporta_y_el_pdf_existe(con, tmp_path):
    _veredicto(con, True)
    ruta = service.exportar_pdf(con, "o1", tmp_path / "n.pdf")
    assert ruta.exists() and ruta.read_bytes().startswith(b"%PDF")


# --- `PLAN-27` E8: exportar desde la terminal ----------------------------------------

def _guion():
    import importlib.util
    import pathlib
    ruta = pathlib.Path(__file__).resolve().parents[4] / "leer_obra.py"
    spec = importlib.util.spec_from_file_location("leer_obra", ruta)
    guion = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guion)
    return guion


def _a_fichero(con, tmp_path):
    import sqlite3
    ruta = tmp_path / "obra.db"
    destino = sqlite3.connect(str(ruta))
    con.backup(destino)
    destino.close()
    return str(ruta)


def test_leer_obra_con_pdf_se_niega_si_no_esta_publicada_y_sale_con_1(con, tmp_path, capsys):
    base = _a_fichero(con, tmp_path)
    codigo = _guion().main(["--base", base, "--obra", "o1", "--pdf", str(tmp_path / "n.pdf")])
    assert codigo == 1 and not (tmp_path / "n.pdf").exists()
    assert "no se exporta" in capsys.readouterr().out


def test_leer_obra_con_pdf_escribe_el_fichero_de_una_obra_publicada(con, tmp_path, capsys):
    _veredicto(con, True)
    base = _a_fichero(con, tmp_path)
    codigo = _guion().main(["--base", base, "--obra", "o1", "--pdf", str(tmp_path / "n.pdf")])
    assert codigo == 0 and (tmp_path / "n.pdf").read_bytes().startswith(b"%PDF")
