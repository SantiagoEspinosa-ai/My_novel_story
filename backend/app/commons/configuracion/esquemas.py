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
enumeracion. Si algo falta, se añade primero a `docs/definitions.md`"*. Asi
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

Las otras tres **no estan en `docs/definitions.md`**, asi que no se añaden
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
from app.commons.dominio.destinatario import FichaDeEntrevista
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


class LugarDelPlan(_DelDominio):
    """De `Lugar`. `nombre` es obligatorio en el dominio y aqui tambien."""

    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    accesos: list[str] = Field(
        default_factory=list,
        description="`Lugar.accesos_y_salidas`, que es lo que lee `INV-02`")


class PersonajeDelPlan(_DelDominio):
    """De `Personaje`."""

    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1, description="`nombre_canonico`")
    empieza_en: str = Field(min_length=1)
    estado_vital: enums.EstadoVital = enums.EstadoVital.VIVO
    fecha_de_nacimiento: str | None = Field(
        default=None,
        description="ISO-8601, opcional (`SPEC-21` C-3). La declara el plan "
                    "(`SPEC-26` `RF-04`) y la lee la comprobacion de edad")


class ConocimientoInicial(_DelDominio):
    """`SPEC-17` C-1: quien sabe que **antes de la escena 1**."""

    sujeto: str
    hecho: str
    grado: enums.GradoDeConocimiento = enums.GradoDeConocimiento.SABE


class HechoDelPlan(_DelDominio):
    """`SPEC-15`: los `HechoCanonico` los declara el plan, no el texto."""

    id: str = Field(min_length=1)
    enunciado: str = Field(min_length=1)


class EscenaDelPlan(_DelDominio):
    """Lo que la escaleta declara **antes de que exista texto**."""

    eje: str = Field(min_length=1, description="`cambio_de_valor.eje`")
    signo: str = "negativo"
    lugar: str = Field(min_length=1)
    pov: str = Field(min_length=1)
    sinopsis: str = ""
    establece: list[str] = Field(
        default_factory=list,
        description="`Beat.establece[]` (`SPEC-19`): que hechos promete "
                    "establecer esta escena")
    t_fabula: str | None = Field(
        default=None,
        description="`MomentoNarrativo.t_fabula`: cuando ocurre en la historia. "
                    "Lo declara el plan (`SPEC-26` `RF-04`)")


class ImprescindibleDelPlan(_DelDominio):
    """`Escaleta.imprescindibles` (`SPEC-26` `RF-03`): donde aparece cada
    elemento imprescindible de la ficha y que palabras lo delatan.

    `elemento` es la `descripcion` literal del `ElementoPersonal` de la ficha:
    es como la cobertura empareja el plan con lo que dijo el comprador.
    """

    elemento: str = Field(min_length=1)
    capitulo: str = Field(min_length=1)
    palabras_clave: list[str] = Field(min_length=1)


class ExclusionPrevista(_DelDominio):
    """`Escaleta.exclusiones_previstas` (`SPEC-26` `RF-04`)."""

    personaje: str = Field(min_length=1)
    capitulo: str = Field(min_length=1)
    estado_vital: enums.EstadoVital


class CapituloDelPlan(_DelDominio):
    id: str = Field(min_length=1)
    titulo: str = ""
    escenas: list[EscenaDelPlan] = Field(min_length=1)


class PlanDeLaObra(_DelDominio):
    """La obra entera, fuera del codigo.

    Estaba en el guion, y por eso cambiar `capitulos: 3` en el fichero fallaba:
    el fichero decia una cosa y el codigo traia otra. Ahora **editar el fichero
    cambia la obra**, que es lo unico que hace verdad la frase.
    """

    mundo: "MundoDelPlan"
    hechos: list[HechoDelPlan] = Field(default_factory=list)
    capitulos: list[CapituloDelPlan] = Field(min_length=1)
    imprescindibles: list[ImprescindibleDelPlan] = Field(default_factory=list)
    exclusiones_previstas: list[ExclusionPrevista] = Field(default_factory=list)

    @model_validator(mode="after")
    def _las_referencias_existen(self):
        """Lo que se cita tiene que estar declarado, y se comprueba **aqui**.

        Un identificador que no existe no revienta: **se degrada**. Un lugar
        inventado en una escena llega a `INV-02`, que busca sus accesos, no
        encuentra la fila y no comprueba nada — la asimetria de la que no
        protege ningun esquema si el esquema no mira.
        """
        lugares = {l.id for l in self.mundo.lugares}
        hechos = {h.id for h in self.hechos}
        personajes = {p.id for p in self.mundo.personajes}
        for l in self.mundo.lugares:
            for destino in l.accesos:
                if destino not in lugares:
                    raise ValueError(
                        "`{0}` tiene acceso a `{1}`, que no esta declarado. "
                        "`INV-02` recorre el grafo por el `id`, asi que un "
                        "destino inexistente hace la accesibilidad "
                        "incomprobable".format(l.id, destino))
        for p in self.mundo.personajes:
            if p.empieza_en not in lugares:
                raise ValueError("`{0}` empieza en `{1}`, que no existe".format(
                    p.id, p.empieza_en))
        for k in self.mundo.conocimiento_inicial:
            if k.hecho not in hechos:
                raise ValueError(
                    "el conocimiento inicial cita `{0}`, que no esta "
                    "declarado".format(k.hecho))
            if k.sujeto not in personajes:
                raise ValueError(
                    "el conocimiento inicial cita `{0}`, que no es un "
                    "personaje declarado".format(k.sujeto))
        for c in self.capitulos:
            for i, e in enumerate(c.escenas, 1):
                if e.lugar not in lugares:
                    raise ValueError(
                        "{0} escena {1} ocurre en `{2}`, que no esta "
                        "declarado".format(c.id, i, e.lugar))
                if e.pov not in personajes:
                    raise ValueError(
                        "{0} escena {1} tiene el POV en `{2}`, que no es un "
                        "personaje declarado".format(c.id, i, e.pov))
                for h in e.establece:
                    if h not in hechos:
                        raise ValueError(
                            "{0} escena {1} promete establecer `{2}`, que no "
                            "esta declarado. Un beat **no inventa hechos, los "
                            "situa** (`SPEC-19`)".format(c.id, i, h))
        capitulos = {c.id for c in self.capitulos}
        for imp in self.imprescindibles:
            if imp.capitulo not in capitulos:
                raise ValueError("el imprescindible «{0}» va en `{1}`, que no es un "
                                 "capitulo del plan".format(imp.elemento, imp.capitulo))
        for x in self.exclusiones_previstas:
            if x.personaje not in personajes or x.capitulo not in capitulos:
                raise ValueError("la exclusion prevista de `{0}` en `{1}` cita algo "
                                 "que no esta declarado".format(x.personaje, x.capitulo))
        return self


class MundoDelPlan(_DelDominio):
    lugares: list[LugarDelPlan] = Field(min_length=1)
    personajes: list[PersonajeDelPlan] = Field(min_length=1)
    conocimiento_inicial: list[ConocimientoInicial] = Field(default_factory=list)


class BriefDeObra(_DelDominio):
    """Lo que define una novela concreta, fuera del codigo."""

    obra_id: str = Field(
        default="obra-1", min_length=1,
        description="El identificador de la `Obra`. **Una obra, no una por "
                    "capitulo**: cuando cada capitulo era su propia obra, "
                    "`escena.capitulo` no tenia a que apuntar y los hechos "
                    "colisionaban (`F-53`, `F-56`)")
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
    plan: PlanDeLaObra | None = None
    destinatario: FichaDeEntrevista | None = Field(
        default=None,
        description="Para quien es la novela (`SPEC-25`). Opcional: una obra "
                    "sin destinatario sigue siendo un brief valido, que es lo "
                    "que permite que el de hoy cargue sin cambios")

    @model_validator(mode="after")
    def _la_forma_cuadra_con_el_plan(self):
        """La forma y el plan no pueden decir cosas distintas.

        Se valida **dentro del esquema** y no al arrancar el guion: antes
        quedaba una ventana en la que el fichero decia una cosa y el codigo
        otra, y esa ventana es donde vivio `F-53` durante diez capitulos.
        """
        if self.plan is None:
            return self
        if len(self.plan.capitulos) != self.forma.capitulos:
            raise ValueError(
                "`forma.capitulos` dice {0} y el plan trae {1} capitulos. La "
                "forma se lee de un vistazo y el plan es lo que se genera: si "
                "discrepan, uno de los dos miente".format(
                    self.forma.capitulos, len(self.plan.capitulos)))
        for c in self.plan.capitulos:
            if len(c.escenas) != self.forma.escenas_por_capitulo:
                raise ValueError(
                    "`forma.escenas_por_capitulo` dice {0} y {1} trae {2} "
                    "escenas".format(self.forma.escenas_por_capitulo, c.id,
                                     len(c.escenas)))
        return self

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
    entrevistador: str | None = Field(
        default=None,
        description="`SPEC-25`. Opcional para que una maquina que solo genera "
                    "siga cargando; la entrevista falla de forma visible si "
                    "falta")
    # `SPEC-26`. Opcionales por lo mismo: la obra de terror sigue cargando.
    planificador: str | None = None
    revisor_plan: str | None = None
    editor: str | None = None


class Topes(_DelDominio):
    """Los numeros siguen viviendo en `commons/config.py` con su marca de
    procedencia. Aqui se pueden **cambiar**, no nacer: tenerlos definidos en
    dos sitios haria que la marca de "no medido" se quedara en uno solo."""

    intentos_por_escena: int = Field(default=config.TOPE_INTENTOS_ESCENA, gt=0)
    delegaciones_por_obra: int = Field(default=config.TOPE_DELEGACIONES_OBRA, gt=0)
    reintentos_de_transporte: int = Field(
        default=config.TOPE_REINTENTOS_TRANSPORTE, gt=0)
    reescrituras_por_vetada: int = Field(
        default=config.TOPE_REESCRITURAS_POR_VETADA, ge=0)
    revisiones_de_plan: int = Field(default=config.TOPE_REVISIONES_DE_PLAN, gt=0)
    reescrituras_del_editor: int = Field(
        default=config.TOPE_REESCRITURAS_DEL_EDITOR, ge=0)


class Edicion(_DelDominio):
    """Los umbrales del Editor y de `INV-25`. **Provisionales**: su marca de no
    medido vive con el numero en `commons/config.py` (`SPEC-26` `RF-10`, `RF-16`)."""

    umbral_del_editor: int = Field(default=config.UMBRAL_DEL_EDITOR, ge=1, le=5)
    umbral_repeticion_nombre: int = Field(default=config.UMBRAL_REPETICION_NOMBRE, gt=0)
    longitud_frase_repetida: int = Field(default=config.LONGITUD_FRASE_REPETIDA, gt=1)


class FranjaDeEdad(_DelDominio):
    """Un tramo de edades con su propia lista de vetadas (`SPEC-25` `RF-16`).

    `hasta` es **inclusivo**: la franja infantil de 0 a 11 incluye a quien tiene
    11 años. Es configuracion y no codigo porque el limite lo decide quien vende
    la novela, no quien la programa.
    """

    nombre: str = Field(min_length=1)
    desde: int = Field(ge=0)
    hasta: int = Field(ge=0)

    @model_validator(mode="after")
    def _el_tramo_no_esta_al_reves(self):
        if self.hasta < self.desde:
            raise ValueError("la franja {0} acaba ({1}) antes de empezar ({2})".format(
                self.nombre, self.hasta, self.desde))
        return self


def _franjas_por_defecto():
    return [FranjaDeEdad(nombre="infantil", desde=0, hasta=11),
            FranjaDeEdad(nombre="juvenil", desde=12, hasta=17)]


class ReglasDeContradiccion(_DelDominio):
    """Las parejas incompatibles de `SPEC-25` `RF-08`, como configuracion.

    Una entrada dice: por debajo de esta edad, este valor se contradice con el
    destinatario. Un valor que no esta en el diccionario no tiene limite.
    """

    edad_minima_por_genero: dict[enums.GeneroDeLaHistoria, int] = Field(
        default_factory=lambda: {enums.GeneroDeLaHistoria.ROMANCE: 12})
    edad_minima_por_ocasion: dict[enums.Ocasion, int] = Field(
        default_factory=lambda: {enums.Ocasion.BODA: 18,
                                 enums.Ocasion.JUBILACION: 18})


class ListasVetadas(_DelDominio):
    """El contenido inicial de los niveles global y por franja (`SPEC-25`).

    El nivel por novela no esta aqui: lo decide el comprador en la entrevista.
    """

    global_: list[str] = Field(alias="global")
    franjas: dict[str, list[str]] = Field(default_factory=dict)


class Presupuesto(_DelDominio):
    """El techo de `CLAUDE.md`, que es sobre **lo que se manda** (`SPEC-14`)."""

    techo_de_contexto: int = Field(default=100_000, gt=0)


class ConfiguracionDelSistema(_DelDominio):
    """Lo que cambia con la maquina, no con la novela."""

    modelos: ModelosPorAgente
    topes: Topes = Field(default_factory=Topes)
    presupuesto: Presupuesto = Field(default_factory=Presupuesto)
    ruta_de_la_base: str = Field(default="obra.db")
    franjas_de_edad: list[FranjaDeEdad] = Field(default_factory=_franjas_por_defecto)
    contradicciones: ReglasDeContradiccion = Field(
        default_factory=ReglasDeContradiccion)
    edicion: Edicion = Field(default_factory=Edicion)

    @property
    def huella(self) -> str:
        """Identifica **esta** configuracion de maquina (`MF-28`).

        El commit dice con que **codigo** se escribio una base y la huella del
        brief con que **novela**. Faltaba la tercera: con que **maquina**. Dos
        tandas de la misma novela y el mismo codigo dan numeros distintos si
        cambia el modelo, y sin esto la diferencia no queda registrada en
        ninguna parte — se le atribuiria a la obra lo que hizo la maquina.

        Ordenada por claves por lo mismo que la del brief: el orden del fichero
        no puede hacer que dos configuraciones identicas parezcan distintas.
        """
        crudo = json.dumps(self.model_dump(mode="json"), sort_keys=True,
                           ensure_ascii=False)
        return hashlib.sha256(crudo.encode("utf-8")).hexdigest()[:12]

    @model_validator(mode="after")
    def _el_techo_cabe_en_el_presupuesto(self):
        return self
