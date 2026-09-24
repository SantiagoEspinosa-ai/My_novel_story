"""El PDF de la novela (`SPEC-27`, `PLAN-27` E5), a partir del `Libro`.

Portada con la dedicatoria, indice con un enlace interno a cada capitulo, un capitulo
por pagina (o las que ocupe) y las fichas de personajes y lugares con enlaces a los
capitulos donde aparece cada uno. **El texto va tal cual**: la fuente es una TrueType
Unicode del repositorio (DejaVu Sans), porque las basicas de PDF solo cubren latin-1 y
sustituirian las rayas y las comillas, y sustituir es tocar el texto (`RF-02`).

La fecha de creacion se fija desde fuera, para que dos exportaciones del mismo libro se
puedan comparar byte a byte.
"""

import datetime
from pathlib import Path

from fpdf import FPDF

FUENTES = Path(__file__).parent / "fuentes"
LETRA = "DejaVu"


def _documento(creado):
    doc = FPDF(format="A5")
    doc.set_margins(18, 18, 18)
    doc.set_auto_page_break(True, margin=18)
    doc.add_font(LETRA, "", str(FUENTES / "DejaVuSans.ttf"))
    doc.add_font(LETRA, "B", str(FUENTES / "DejaVuSans-Bold.ttf"))
    doc.set_creation_date(creado)
    return doc


def _titulo(doc, texto, tamano=16):
    doc.set_font(LETRA, "B", tamano)
    doc.multi_cell(0, tamano * 0.6, texto, new_x="LMARGIN", new_y="NEXT")
    doc.ln(4)


def _enlaces_a_capitulos(doc, capitulos, enlace_de):
    doc.set_font(LETRA, "", 10)
    if capitulos is None:
        doc.cell(0, 6, "   Aparece en: no declarado", new_x="LMARGIN", new_y="NEXT")
        return
    if not capitulos:
        doc.cell(0, 6, "   Aparece en: ningún capítulo", new_x="LMARGIN", new_y="NEXT")
        return
    doc.cell(doc.get_string_width("   Aparece en: ") + 1, 6, "   Aparece en: ")
    for i, n in enumerate(capitulos):
        texto = "capítulo {0}{1}".format(n, "," if i < len(capitulos) - 1 else "")
        doc.cell(doc.get_string_width(texto) + 2, 6, texto, link=enlace_de(n))
    doc.ln(6)


def _fichas(doc, titulo, fichas, enlace_de):
    doc.set_font(LETRA, "B", 12)
    doc.cell(0, 8, titulo, new_x="LMARGIN", new_y="NEXT")
    for f in fichas:
        doc.set_font(LETRA, "", 11)
        nombre = f.nombre + (" (sin nombre guardado)" if f.nombre_es_el_id else "")
        doc.multi_cell(0, 6, nombre, new_x="LMARGIN", new_y="NEXT")
        _enlaces_a_capitulos(doc, f.capitulos, enlace_de)
    doc.ln(4)


def _maquetar(libro, creado, paginas):
    """Una pasada. Con `paginas=None` no pone enlaces y apunta donde empieza cada
    capitulo y las fichas: fpdf2 exige conocer la pagina de un enlace al insertarlo, y
    esa pagina depende de lo que ocupe el texto. Un enlace no cambia la maquetacion, asi
    que la segunda pasada, con las paginas ya sabidas, queda igual."""
    doc = _documento(creado)
    vistas = {}

    def enlace(clave):
        return doc.add_link(page=paginas[clave]) if paginas else None

    doc.add_page()
    doc.ln(40)
    _titulo(doc, libro.titulo, 22)
    if libro.dedicatoria:
        doc.set_font(LETRA, "", 12)
        doc.multi_cell(0, 7, libro.dedicatoria, new_x="LMARGIN", new_y="NEXT")

    doc.add_page()
    _titulo(doc, "Índice")
    doc.set_font(LETRA, "", 12)
    for c in libro.capitulos:
        doc.cell(0, 8, "Capítulo {0}".format(c.numero), link=enlace(c.numero),
                 new_x="LMARGIN", new_y="NEXT")
    doc.cell(0, 8, "Personajes y lugares", link=enlace("fichas"),
             new_x="LMARGIN", new_y="NEXT")

    for c in libro.capitulos:
        doc.add_page()
        vistas[c.numero] = doc.page
        _titulo(doc, "Capítulo {0}".format(c.numero))
        doc.set_font(LETRA, "", 11)
        doc.multi_cell(0, 6, c.texto, new_x="LMARGIN", new_y="NEXT")

    doc.add_page()
    vistas["fichas"] = doc.page
    _titulo(doc, "Personajes y lugares")
    if libro.presentes_sin_declarar:
        doc.set_font(LETRA, "", 10)
        doc.multi_cell(0, 6, "Quién está en cada escena no se declaró en todas: donde falta, "
                             "se dice «no declarado».", new_x="LMARGIN", new_y="NEXT")
        doc.ln(2)
    _fichas(doc, "Personajes", libro.personajes, enlace)
    _fichas(doc, "Lugares", libro.lugares, enlace)
    return doc, vistas


def a_pdf(libro, ruta, creado=None):
    creado = creado or datetime.datetime.now(datetime.timezone.utc)
    _, paginas = _maquetar(libro, creado, None)
    doc, vistas = _maquetar(libro, creado, paginas)
    if vistas != paginas:
        raise RuntimeError("la segunda pasada no maqueto igual que la primera")
    doc.output(str(ruta))
    return Path(ruta)
