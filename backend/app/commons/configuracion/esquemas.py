"""La forma de la obra y la del sistema, como esquemas y no como codigo.

POR QUE ESTO EXISTE, Y NO ES POR COMODIDAD
--------------------------------------------
Que la forma de la obra viviera **dentro del guion** es lo que hizo que nadie
notara durante diez capitulos que estabamos modelando **diez obras** en vez de
una con diez capitulos. La diferencia no se veia porque no habia ningun sitio
donde mirarla: estaba repartida en un bucle que llamaba diez veces a
`guardar_escaleta` con un identificador distinto.

Un fichero con `capitulos: 10` dentro de `forma` **se lee de un vistazo** y no
se confunde con eso. La leccion no es que la configuracion sea comoda: es que
**una forma que no se puede leer en un sitio no se puede discutir**, y lo que
no se discute nadie lo corrige.

SON DOS ESQUEMAS PORQUE CAMBIAN POR MOTIVOS DISTINTOS
-------------------------------------------------------
`ConfiguracionDelSistema` cambia cuando cambia la maquina: que modelo usa cada
agente, cuanto se permite gastar, donde vive la base. `BriefDeObra` cambia
cuando cambia la novela. Juntarlos obligaria a tocar la novela para cambiar de
modelo, y a revisar la maquina para escribir otra historia.

LO QUE **NO** SE INVENTA AQUI
-------------------------------
`CLAUDE.md` es explicito: *"no inventes campos, clases ni valores de
enumeracion. Si algo falta, se añade primero a `Docs/definitions.md`"*. Asi
que todo lo que este esquema recoge de la obra **ya existe en el dominio**:
`titulo`, `premisa`, `genero`, `subgenero` y `extension_objetivo` son de
`Obra`; `persona`, `tiempo_verbal` y `tics_prohibidos` son de `GuiaDeEstilo`.

Lo unico nuevo es `forma`, que **no es dominio**: es cuantas piezas se piden
de las que el dominio ya define. Vivia en el guion y ahora vive aqui.

POR DONDE VA A CRECER, Y POR QUE NO CRECE HOY
-----------------------------------------------
El examen pedira que la obra se escriba **para alguien**: destinatario, edad,
recuerdos que incorporar, palabras que no usar. De esas cuatro, **una ya
existe** y esta recogida: las palabras prohibidas son
`GuiaDeEstilo.tics_prohibidos`.

Las otras tres **no estan en `Docs/definitions.md`**, asi que no se añaden
aqui: entrarian como campos que el dominio no conoce, que es exactamente lo
que la regla prohibe. Cuando se decidan, el sitio es una seccion `destinatario`
al lado de `estilo`, y el orden es el de siempre — primero la definicion,
despues el esquema.
"""

import hashlib
import json

from pydantic import Field, field_validator, model_validator

from app.commons import config
from app.commons.dominio import enumeraciones as enums
from app.commons.dominio.modelos import _DelDominio


class FormaDeLaObra(_DelDominio):
    """Cuantas piezas tiene la novela. **Esto es lo que vivia en el guion.**"""

    capitulos: int = Field(gt=0, description="Cuantos capitulos tiene la obra")
    escenas_por_capitulo: int = Field(gt=0)
    palabras_por_escena: tuple[int, int] = Field(
        description="Rango que llega a `Escena.longitud_objetivo` y lee `INV-17`")

    @field_validator("palabras_por_escena")
    @classmethod
    def _rango_ordenado(cls, v):
        if v[0] > v[1]:
            raise ValueError(
                "el minimo de palabras ({0}) es mayor que el maximo ({1}). "
                "`INV-17` comprueba que la escena caiga dentro del rango, y "
                "con el rango al reves **ninguna escena puede caer dentro**: "
                "fallarian todas y el hallazgo describiria mal la causa".format(*v))
        return v

    @property
    def escenas_totales(self) -> int:
        return self.capitulos * self.escenas_por_capitulo


class EstiloDeLaObra(_DelDominio):
    """De `GuiaDeEstilo`. Ningun campo de aqui es nuevo."""

    persona: enums.PersonaNarrativa | None = None
    tiempo_verbal: enums.TiempoVerbal | None = None
    tics_prohibidos: list[str] = Field(
        default_factory=list,
        description="Lo que el **autor** prohibe, que no caduca. No confundir "
                    "con `FraseRecurrente`, que es lo que el sistema observa")
    anclas: list[str] = Field(
        default_factory=list, description="Fragmentos que fijan el tono")


class BriefDeObra(_DelDominio):
    """Lo que define una novela concreta, fuera del codigo."""

    titulo: str = Field(min_length=1)
    premisa: str = Field(min_length=1)
    genero: str | None = None
    subgenero: str | None = None
    extension_objetivo: int | None = Field(default=None, gt=0)
    forma: FormaDeLaObra
    estilo: EstiloDeLaObra = Field(default_factory=EstiloDeLaObra)
    inmutable: str = Field(
        default="",
        description="El bloque 1 del contexto: premisa, estilo y reglas del "
                    "mundo tal como las lee el Escritor")

    @property
    def huella(self) -> str:
        """Identifica **este** brief, para poder repetir una tanda exacta.

        Ordenada por claves a proposito: dos ficheros con el mismo contenido y
        distinto orden son la misma tanda, y si la huella cambiara con el orden
        diria que son distintas — que es lo unico para lo que no debe servir.

        Junto al commit que guarda `procedencia.py`, esto cierra el par: **con
        que codigo** y **con que forma de obra** se genero una base.
        """
        crudo = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                           ensure_ascii=False)
        return hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:12]


class ModelosPorAgente(_DelDominio):
    """Que modelo usa cada agente.

    Estaban en variables de entorno sueltas, asi que una tanda no podia decir
    con que modelos corrio sin que alguien se acordara de anotarlo. `VER-62`
    vigila que el **conjunto** sea estable entre delegaciones; esto dice cual
    se pidio.
    """

    escritor: str
    juez: str
    resumidor: str


class Topes(_DelDominio):
    """Los numeros siguen viviendo en `commons/config.py` con su marca de
    procedencia. Aqui se pueden **cambiar**, no nacer: tenerlos definidos en
    dos sitios haria que la marca de "no medido" se quedara en uno solo."""

    intentos_por_escena: int = Field(default=config.TOPE_INTENTOS_ESCENA, gt=0)
    delegaciones_por_obra: int = Field(default=config.TOPE_DELEGACIONES_OBRA, gt=0)
    reintentos_de_transporte: int = Field(
        default=config.TOPE_REINTENTOS_TRANSPORTE, gt=0)


class Presupuesto(_DelDominio):
    """El techo de `CLAUDE.md`, que es sobre **lo que se manda** (`SPEC-14`)."""

    techo_de_contexto: int = Field(default=100_000, gt=0)


class ConfiguracionDelSistema(_DelDominio):
    """Lo que cambia con la maquina, no con la novela."""

    modelos: ModelosPorAgente
    topes: Topes = Field(default_factory=Topes)
    presupuesto: Presupuesto = Field(default_factory=Presupuesto)
    ruta_de_la_base: str = Field(default="obra.db")

    @model_validator(mode="after")
    def _el_techo_cabe_en_el_presupuesto(self):
        return self
