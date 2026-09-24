"""`PLAN-22` E5 — las fichas (`SPEC-22` `RF-43`, `RF-44`).

*Aparecer* tiene un significado exacto: `participa_en` para un `Personaje`
(`Escena.personajes_presentes`) y `ocurre_en` para un `Lugar` (`Escena.lugar`). Una mencion
en el texto no cuenta. La lista la calcula el backend, por `capitulo.orden`.

Hasta `PLAN-27` E2 no hay nombres guardados, y hasta E3 la novela regalo no declara
presentes: sale honesta, con el nombre nulo y los capitulos del personaje **desconocidos**
(nulos), nunca vacios. `VER-104` y la fila compartida con `PLAN-27`.
"""

import sqlite3

from app.features.lectura.tests.conftest import OBRA, OTRA


def _fichas(cliente, obra=OBRA):
    r = cliente.get("/obras/{0}/fichas".format(obra))
    assert r.status_code == 200, r.text
    return r.json()


def _por_id(lista):
    return {f["id"]: f for f in lista}


def _ids(capitulos):
    return None if capitulos is None else [c["id"] for c in capitulos]


def test_un_personaje_enlaza_los_capitulos_donde_participa_y_una_mencion_no_cuenta(cliente):
    personajes = _por_id(_fichas(cliente)["personajes"])
    assert _ids(personajes["per-uno"]["capitulos_donde_aparece"]) == ["cap-b", "cap-a"]
    # per-dos esta en esc-b1 y solo se **menciona** en el texto de esc-a1 (cap-a).
    assert _ids(personajes["per-dos"]["capitulos_donde_aparece"]) == ["cap-b"]


def test_un_lugar_enlaza_los_capitulos_donde_ocurre_una_escena(cliente):
    lugares = _por_id(_fichas(cliente)["lugares"])
    assert _ids(lugares["lug-faro"]["capitulos_donde_aparece"]) == ["cap-b", "cap-a"]
    assert _ids(lugares["lug-casa"]["capitulos_donde_aparece"]) == ["cap-b"]
    # El negativo: esc-z1 ocurre en lug-casa, pero es de otra obra.
    assert "cap-z" not in _ids(lugares["lug-casa"]["capitulos_donde_aparece"])
    ajenos = _por_id(_fichas(cliente, OTRA)["lugares"])
    assert _ids(ajenos["lug-casa"]["capitulos_donde_aparece"]) == ["cap-z"]
    assert "lug-faro" not in ajenos


def test_presentes_sin_declarar_viajan_nulos_y_no_como_lista_vacia(cliente):
    """En `OTRA` ninguna escena declara presentes: no se sabe, que no es *nadie*."""
    personajes = _por_id(_fichas(cliente, OTRA)["personajes"])
    assert personajes, "el pov de la escena existe aunque no se sepa donde aparece"
    for f in personajes.values():
        assert f["capitulos_donde_aparece"] is None, f


def test_una_entidad_sin_nombre_guardado_viaja_con_nombre_nulo(cliente):
    fichas = _fichas(cliente)
    for f in fichas["personajes"]:
        assert f["nombre_canonico"] is None
        assert (f["alias"], f["rol_dramatico"]) == (None, None), "sin dato, no ninguno"
    for f in fichas["lugares"]:
        assert (f["nombre"], f["atmosfera"]) == (None, None)
    assert _por_id(fichas["personajes"])["per-dos"]["estado_vital"] == "desaparecido"


def test_con_el_nombre_guardado_la_ficha_lo_trae(cliente):
    """Cuando `PLAN-27` E2 anada las columnas, el nombre viaja sin tocar la lectura."""
    from app.main import app
    con = sqlite3.connect(app.state.ruta_db)
    with con:
        con.execute("ALTER TABLE entidad ADD COLUMN nombre_canonico TEXT")
        con.execute("ALTER TABLE lugar ADD COLUMN nombre TEXT")
        con.execute("UPDATE entidad SET nombre_canonico = 'Nombre inventado' WHERE id = 'per-uno'")
        con.execute("UPDATE lugar SET nombre = 'Faro inventado' WHERE id = 'lug-faro'")
    con.close()
    fichas = _fichas(cliente)
    assert _por_id(fichas["personajes"])["per-uno"]["nombre_canonico"] == "Nombre inventado"
    assert _por_id(fichas["personajes"])["per-dos"]["nombre_canonico"] is None
    assert _por_id(fichas["lugares"])["lug-faro"]["nombre"] == "Faro inventado"


def test_los_capitulos_de_una_ficha_van_en_orden_de_lectura_y_no_de_id(cliente):
    per_uno = _por_id(_fichas(cliente)["personajes"])["per-uno"]
    assert [(c["id"], c["orden"]) for c in per_uno["capitulos_donde_aparece"]] == \
        [("cap-b", 1), ("cap-a", 2)]


def test_las_fichas_de_una_obra_que_no_existe_dan_404(cliente):
    assert cliente.get("/obras/cap-b/fichas").status_code == 404
