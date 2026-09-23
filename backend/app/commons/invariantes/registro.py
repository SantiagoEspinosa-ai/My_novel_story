"""El registro de las invariantes `INV-01`..`INV-27` (`INV-19` e `INV-20` reservadas).

Es la copia en codigo de la tabla de `docs/definitions.md`, y `VER-38` existe
para comprobar que las dos digan lo mismo. Por eso se escribe a mano: si se
generara leyendo el documento, `VER-38` compararia el documento consigo mismo
y estaria en verde por construccion (Regla 3 de `docs/verification.md`).

`VER-38` es el puesto 1 de la orden de implantacion porque **valida a otros
tres**: `VER-11`, `VER-12` y `VER-22` pueden estar los tres en verde con una
severidad mal puesta, que es justo el anti-patron de bajar una `bloqueante` a
`mayor` para desatascar una generacion.

LA COLUMNA `que_lee`
--------------------
`SPEC-13` la anadio a la tabla del documento y aqui se replica. Sirve para una
regla concreta de `SPEC-01` 2.4: la forma reducida de un bloque de contexto
nunca puede llevarse lo que lee una invariante `bloqueante` de nivel escena. Sin
esta columna esa regla no se puede comprobar.

Es **una afirmacion, no un hecho**, hasta que exista la implementacion de cada
comprobacion que pueda contradecirla. Es el mismo punto ciego que `VER-38` con
la severidad, y esta declarado en `VER-59`.
"""

from dataclasses import dataclass

from app.commons.dominio.enumeraciones import (
    NivelDeEvaluacion,
    Severidad,
    TipoDeVerificador,
)


@dataclass(frozen=True)
class Invariante:
    id: str
    enunciado: str
    nivel: NivelDeEvaluacion
    severidad: Severidad
    tipo: TipoDeVerificador
    que_lee: str
    obsoleta: bool = False
    """`SPEC-26` v3 `RF-21`: retirada sin renumerar. Sigue en el registro para
    que ningun identificador publicado desaparezca, y no se aplica a ninguna obra."""


def construir_invariante(id, enunciado, nivel, severidad, tipo, que_lee,
                         severidad_esperada=None, obsoleta=False):
    """Construye una invariante y, si se le da, comprueba su severidad.

    `severidad_esperada` es el gancho de `VER-38`: quien parsea la tabla del
    documento le pasa lo que alli pone, y una discrepancia revienta aqui en vez
    de colarse. Sin ese parametro no comprueba nada: el registro de abajo se
    escribe a mano y su contraste con el documento es trabajo de `VER-38`, no
    de este constructor.
    """
    inv = Invariante(
        id=id,
        enunciado=enunciado,
        nivel=NivelDeEvaluacion(nivel),
        severidad=Severidad(severidad),
        tipo=TipoDeVerificador(tipo),
        que_lee=que_lee,
        obsoleta=obsoleta,
    )
    if severidad_esperada is not None and inv.severidad is not severidad_esperada:
        raise ValueError(
            "{0}: la severidad del registro es `{1}` y la de la tabla es `{2}`. "
            "Una invariante mal clasificada deja tres validadores en verde "
            "sobre una puerta que ya no detiene nada.".format(
                inv.id, inv.severidad.value, severidad_esperada.value
            )
        )
    return inv


def _r(id, enunciado, nivel, severidad, tipo, que_lee, obsoleta=False):
    return construir_invariante(id, enunciado, nivel, severidad, tipo, que_lee,
                                obsoleta=obsoleta)


_LISTA = [
    _r("INV-01", "Toda escena tiene `cambio_de_valor` no nulo",
       "escena", "bloqueante", "regla", "Escena.cambio_de_valor"),
    _r("INV-02", "Todo personaje presente tiene `estado_vital = vivo` y es accesible en `EstadoDelMundo(t)`",
       "escena", "bloqueante", "regla",
       "Escena.personajes_presentes, EstadoDelMundo.entidades_vivas, EstadoDelMundo.ubicaciones, Lugar.accesos_y_salidas"),
    _r("INV-03", "Ningun personaje actua sobre un hecho que no conoce en `t`",
       "escena", "bloqueante", "regla",
       "RegistroDeConocimiento, HechoCanonico.escena_de_establecimiento, MomentoNarrativo.t_fabula, revelaciones del delta"),
    _r("INV-04", "El POV no cambia dentro de una escena",
       "escena", "bloqueante", "regla", "Escena.pov, Borrador.pov_usado"),
    _r("INV-05", "Toda escena aceptada tiene su delta aplicado antes de la siguiente",
       "escena", "bloqueante", "regla", "DeltaDeEscena, EstadoDelMundo"),
    _r("INV-06", "Ningun `HechoCanonico` vigente contradice a otro",
       "obra", "bloqueante", "regla", "HechoCanonico.contradice, EstadoDelMundo.hechos_vigentes"),
    _r("INV-07", "Toda escena realiza al menos un beat que sirve a un arco",
       "escena", "mayor", "regla", "Beat.sirve_a, ArcoNarrativo"),
    _r("INV-08", "`t_fabula` es monotono dentro de una linea argumental salvo analepsis declarada",
       "capitulo", "mayor", "regla", "MomentoNarrativo.t_fabula, LineaArgumental"),
    _r("INV-09", "Todo setup plantado se paga antes del final",
       "obra", "mayor", "regla", "SetupYPago.estado"),
    _r("INV-10", "La amenaza no viola sus propias reglas sin pagar el coste declarado",
       "escena", "mayor", "juez_llm", "ReglaDelMundo, Amenaza, deterioros del delta",
       obsoleta=True),
    _r("INV-11", "El grado de explicacion acumulado no supera el fijado en el brief",
       "obra", "mayor", "regla", "HechoCanonico revelados, Amenaza.grado_de_explicacion_permitido",
       obsoleta=True),
    _r("INV-12", "La presion maxima de la curva de dread cae en el climax mas o menos una escena",
       "obra", "mayor", "regla", "CurvaDeDread.serie", obsoleta=True),
    _r("INV-13", "Ningun hecho se revela dos veces al lector como si fuera nuevo",
       "obra", "mayor", "regla", "revelaciones del delta acumuladas"),
    _r("INV-14", "Cada deterioro es monotono, o su reversion esta justificada en el texto",
       "obra", "menor", "regla", "Deterioro.serie_por_escena"),
    _r("INV-15", "La distancia estilometrica a las anclas se mantiene bajo umbral",
       "capitulo", "menor", "regla", "Borrador.texto, AnclaDeEstilo.texto"),
    _r("INV-16", "La varianza de la curva de dread supera el minimo fijado",
       "obra", "menor", "regla", "CurvaDeDread.serie", obsoleta=True),
    _r("INV-18", "Todo hecho que los `beats` de una escena prometian establecer "
       "aparece en su delta",
       "escena", "mayor", "regla",
       "Beat.establece[], revelaciones del delta, "
       "HechoCanonico.escena_de_establecimiento"),
    _r("INV-17", "La longitud de la escena cae dentro de su `longitud_objetivo`",
       "escena", "mayor", "regla", "Borrador.texto, Escena.longitud_objetivo"),
    # `SPEC-25`: de nivel capitulo porque es el capitulo el que no puede
    # aceptarse con una vetada. Se comprueba **tambien** en cada escena, antes
    # de consolidarla, porque esperar al cierre obligaria a reescribir escenas
    # cuyo delta ya se aplico (`PLAN-25` E4).
    _r("INV-21", "Ningun capitulo aceptado contiene una palabra vetada de ninguno "
       "de los tres niveles, tras normalizar",
       "capitulo", "bloqueante", "regla",
       "Borrador.texto, PalabraVetada.forma, Destinatario.edad"),
    # `SPEC-26`: la novela regalo. `INV-26` e `INV-27` los numero `PLAN-26`
    # porque `CLAUDE.md` exige que toda comprobacion cite su identificador.
    _r("INV-22", "Los nombres del destinatario y de los personajes aparecen escritos "
       "exactamente como en la story bible",
       "escena", "bloqueante", "regla",
       "Borrador.texto, Personaje.nombre_canonico, Destinatario.nombre"),
    _r("INV-23", "Las palabras clave de cada imprescindible aparecen en su capitulo "
       "previsto", "escena", "mayor", "regla",
       "Borrador.texto, Escaleta.imprescindibles"),
    _r("INV-24", "Cada imprescindible aparece en al menos un capitulo de la novela",
       "obra", "bloqueante", "regla", "Escaleta.imprescindibles, relacion usa"),
    _r("INV-25", "La prosa no se repite: el nombre del destinatario no supera su "
       "umbral por capitulo y ninguna frase larga se repite entre capitulos",
       "obra", "menor", "regla", "Borrador.texto, FraseRecurrente"),
    _r("INV-26", "El Editor da a cada criterio de un capitulo al menos la nota umbral",
       "escena", "mayor", "juez_llm", "Borrador.texto, ValoracionDelEditor"),
    _r("INV-27", "El juicio de obra no encuentra un arco roto ni un final abrupto",
       "obra", "mayor", "juez_llm",
       "resumenes de capitulo, Borrador.texto del ultimo capitulo"),
]

TODAS = {i.id: i for i in _LISTA}

def aplica(id_inv, genero) -> bool:
    """Si una invariante se aplica a una obra de este genero.

    `SPEC-26` v3: las de terror (`INV-10`, `INV-11`, `INV-12`, `INV-16`) estan
    obsoletas y no se aplican a ninguna obra, tampoco a una de terror. `INV-13`,
    `INV-14` e `INV-15` son narrativa general. El genero se conserva en la firma
    porque es la pregunta que se hace, aunque hoy no cambie la respuesta.
    """
    return not TODAS[id_inv].obsoleta


def obsoletas() -> list:
    return sorted(i.id for i in _LISTA if i.obsoleta)


def de_nivel(nivel: NivelDeEvaluacion):
    return [i for i in _LISTA if i.nivel is nivel]


def bloqueantes_de_escena():
    """Las que atan la regla de las formas reducidas de `SPEC-01` 2.4.

    Son cinco, y solo dos leen bloques del contexto: `INV-02` e `INV-03`. Las
    otras tres miran la propia escena, su borrador o el delta. Esta funcion la
    usara `VER-59` para cruzar lo que leen contra lo que el recorte se lleva.
    """
    return [i for i in _LISTA
            if i.nivel is NivelDeEvaluacion.ESCENA
            and i.severidad is Severidad.BLOQUEANTE]
