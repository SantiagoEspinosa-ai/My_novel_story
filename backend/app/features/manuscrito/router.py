"""Descargar el PDF de una obra desde la web (`SPEC-35` `RF-12`, `PLAN-35` E1).

Sin logica propia (`A-01`): usa `exportar_pdf`, que ya se niega a exportar lo que la
puerta de publicacion no dejo pasar (`SPEC-27` `RF-01`). La consulta de disponibilidad
dice si hay PDF sin generarlo, para que la portada no ofrezca un boton que falla.
"""

import sqlite3
import tempfile
from pathlib import Path
from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic import BaseModel

from app.features.manuscrito import service

router = APIRouter(tags=["manuscrito"])


class PdfDisponible(BaseModel):
    disponible: bool
    motivo: str | None


def conexion(request: Request):
    con = sqlite3.connect(getattr(request.app.state, "ruta_db", ":memory:"))
    try:
        yield con
    finally:
        con.close()


def _titulo(con, obra):
    try:
        f = con.execute("SELECT titulo FROM obra WHERE id = ?", (obra,)).fetchone()
    except sqlite3.OperationalError:
        f = None
    if f is None:
        raise HTTPException(404, "no existe la obra {0}".format(obra))
    return f[0] or obra


@router.get("/obras/{id_obra}/pdf/disponible", response_model=PdfDisponible)
def disponible(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """Si la obra tiene PDF y, si no, por que. No genera nada."""
    _titulo(con, id_obra)
    motivo = service.motivo_sin_pdf(con, id_obra)
    return {"disponible": motivo is None, "motivo": motivo}


@router.get("/obras/{id_obra}/pdf", response_class=Response,
            responses={200: {"content": {"application/pdf": {}}}})
def descargar(id_obra: str, con: sqlite3.Connection = Depends(conexion)):
    """El PDF de la version vigente. `409` con el motivo de la puerta si no esta publicada."""
    titulo = _titulo(con, id_obra)
    with tempfile.TemporaryDirectory() as carpeta:
        try:
            ruta = service.exportar_pdf(con, id_obra, Path(carpeta) / "libro.pdf")
        except service.VersionNoPublicada as e:
            raise HTTPException(409, str(e))
        contenido = Path(ruta).read_bytes()
    nombre = "{0}.pdf".format(titulo)
    return Response(contenido, media_type="application/pdf", headers={
        "Content-Disposition": "attachment; filename=\"{0}\"; filename*=UTF-8''{1}".format(
            nombre.encode("ascii", "replace").decode("ascii").replace('"', "'"),
            quote(nombre))})
