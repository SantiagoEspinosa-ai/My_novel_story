"""`PLAN-27` E5: el PDF. Se lee el fichero generado con `pypdf`: su texto y sus
enlaces internos, resueltos hasta la pagina a la que llevan.

Punto ciego, dicho: el texto extraido de un PDF no conserva los blancos, asi que aqui
se compara con los blancos normalizados. El byte a byte se comprueba en el `Libro` (E4).
"""

import datetime

import pytest
from pypdf import PdfReader

from app.features.manuscrito import pdf
from app.features.manuscrito.libro import CapituloDelLibro, Ficha, Libro

RAYA = "—¡Canela!— grito Tula desde el tejado. «Ya voy», dijo."


@pytest.fixture
def libro():
    return Libro("La ruta del gato", "Para Tula, que arregla ruedas.",
                 [CapituloDelLibro(1, "o1-cap-01", "Tula arreglaba una rueda.\n\nLlovia."),
                  CapituloDelLibro(2, "o1-cap-02", RAYA)],
                 [Ficha("o1-per-tula", "Tula Brenes", False, [1, 2]),
                  Ficha("o1-per-gato", "Canela", False, [2]),
                  Ficha("o1-per-sin", "o1-per-sin", True, [])],
                 [Ficha("o1-lug-taller", "El taller", False, [1])])


@pytest.fixture
def leido(libro, tmp_path):
    ruta = tmp_path / "novela.pdf"
    pdf.a_pdf(libro, ruta, creado=datetime.datetime(2026, 9, 24))
    return PdfReader(str(ruta))


def _normal(t):
    return " ".join(t.split())


def _pagina_del_capitulo(leido, n):
    for i, p in enumerate(leido.pages):
        if _normal(p.extract_text() or "").startswith("Capítulo {0}".format(n)):
            return i
    raise AssertionError("no hay pagina que empiece por el capitulo {0}".format(n))


def _destinos(leido, i):
    """Las paginas a las que llevan los enlaces internos de la pagina `i`, en orden."""
    referencias = {p.indirect_reference.idnum: n for n, p in enumerate(leido.pages)}
    destinos = []
    for a in leido.pages[i].get("/Annots") or []:
        a = a.get_object()
        if a.get("/Subtype") != "/Link":
            continue
        dest = a.get("/Dest")
        if dest is None and a.get("/A") is not None:
            dest = a["/A"].get("/D")
        destinos.append(referencias[dest[0].idnum])
    return destinos


def test_cada_entrada_del_indice_enlaza_a_la_pagina_de_su_capitulo(leido):
    indice = next(i for i, p in enumerate(leido.pages) if "Índice" in (p.extract_text() or ""))
    esperado = [_pagina_del_capitulo(leido, 1), _pagina_del_capitulo(leido, 2)]
    assert _destinos(leido, indice)[:2] == esperado


def test_cada_ficha_enlaza_a_los_capitulos_donde_aparece(leido):
    fichas = next(i for i, p in enumerate(leido.pages)
                  if "Personajes y lugares" in (p.extract_text() or "")
                  and i > _pagina_del_capitulo(leido, 2))
    c1, c2 = _pagina_del_capitulo(leido, 1), _pagina_del_capitulo(leido, 2)
    # Tula en 1 y 2, Canela en 2, el sin nombre en ninguno, el taller en 1.
    assert _destinos(leido, fichas) == [c1, c2, c2, c1]


def test_la_portada_lleva_titulo_y_dedicatoria(leido):
    portada = _normal(leido.pages[0].extract_text())
    assert "La ruta del gato" in portada and "Para Tula, que arregla ruedas." in portada


def test_un_texto_con_comillas_tipograficas_y_rayas_se_escribe_sin_sustituir(leido):
    assert _normal(RAYA) in _normal(leido.pages[_pagina_del_capitulo(leido, 2)].extract_text())


def test_el_texto_extraido_de_cada_capitulo_coincide_con_el_del_libro(leido, libro):
    for c in libro.capitulos:
        texto = _normal(leido.pages[_pagina_del_capitulo(leido, c.numero)].extract_text())
        assert _normal(c.texto) in texto


def test_una_ficha_sin_nombre_guardado_lo_dice(leido):
    todo = " ".join(_normal(p.extract_text() or "") for p in leido.pages)
    assert "o1-per-sin (sin nombre guardado)" in todo


def test_el_pdf_no_lleva_estados_ni_hallazgos(leido):
    todo = " ".join(_normal(p.extract_text() or "") for p in leido.pages).lower()
    for palabra in ("consolidada", "hallazgo", "sin_veredicto", "rendicion", "inv-"):
        assert palabra not in todo


def test_dos_exportaciones_con_la_misma_fecha_son_identicas(libro, tmp_path):
    a, b = tmp_path / "a.pdf", tmp_path / "b.pdf"
    fecha = datetime.datetime(2026, 9, 24)
    pdf.a_pdf(libro, a, creado=fecha)
    pdf.a_pdf(libro, b, creado=fecha)
    assert a.read_bytes() == b.read_bytes()
