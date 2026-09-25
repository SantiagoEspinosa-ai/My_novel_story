"""Lo que devuelven publicar y reanudar desde la web (`SPEC-39`)."""

from pydantic import BaseModel


class Publicar(BaseModel):
    posible: bool
    motivo: str | None
    version: int
    lean_disponible: bool
    lean_motivo: str | None
    coste_medio_del_editor: float | None
    delegaciones_medidas_del_editor: int


class Reanudar(BaseModel):
    posible: bool
    motivo: str | None
    desde_capitulo: int | None
    faltan: int
    coste_por_capitulo: float | None
    fuente: str | None
    estimacion_usd: float | None


class AccionesDeObra(BaseModel):
    """`SPEC-39` `RF-07`: que se puede hacer con la novela, y por que no, lo decide el backend."""

    publicar: Publicar
    reanudar: Reanudar
