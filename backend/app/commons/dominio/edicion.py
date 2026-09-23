"""`ValoracionDelEditor` de `docs/definitions.md` (`SPEC-26` `RF-09`)."""

from pydantic import Field, model_validator

from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class ValoracionDelEditor(_DelDominio):
    criterio: enums.CriterioDeEdicion
    nota: int = Field(ge=1, le=5)
    justificacion: str = Field(min_length=1)
    instruccion: str = ""


class ValoracionesDelEditor(_DelDominio):
    """Las seis, una por criterio. Una valoracion que se salta un criterio no
    dice que ese criterio este bien: no lo miro, y eso no puede pasar por un
    aprobado."""

    valoraciones: list[ValoracionDelEditor]

    @model_validator(mode="after")
    def _los_seis_criterios_una_vez(self):
        vistos = [v.criterio for v in self.valoraciones]
        if sorted(vistos) != sorted(enums.CriterioDeEdicion):
            raise ValueError("hacen falta los seis criterios una vez cada uno; "
                             "llegaron: {0}".format([v.value for v in vistos]))
        return self
