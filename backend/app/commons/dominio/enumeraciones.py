"""Los vocabularios controlados de `Docs/definitions.md`, como `Enum`.

POR QUE ESTAN AQUI Y SOLO AQUI
------------------------------
`VER-15` y la decision `D-3` de `SPEC-01`: los `Enum` de los vocabularios
controlados **del dominio** viven solo en `commons/dominio/`. Los de
infraestructura -hoy los estados de un trabajo- viven con su infraestructura,
en `commons/trabajos/`, porque la tabla de trabajos no existiria si la novela
se escribiera a mano.

POR QUE ESTAN ESCRITOS A MANO Y NO GENERADOS
--------------------------------------------
Seria facil generarlos leyendo la tabla de `Docs/definitions.md`, y seria un
error. `VER-01` comprueba que los esquemas y las fichas de clase digan lo
mismo; si los esquemas salieran de las fichas, `VER-01` compararia el documento
consigo mismo y estaria en verde por construccion. Es la Regla 3 de
`Docs/verification.md`: un validador no comparte implementacion con lo que
valida.

Asi que la copia es deliberada, y `VER-01` existe para cazarla cuando divergen.

LOS LITERALES SON LITERALES
---------------------------
No se traducen, no se abrevian y no se les ponen tildes. Una cadena acentuada
admite dos representaciones Unicode iguales a la vista y distintas byte a byte,
asi que dos valores que se leen igual dejarian de compararse iguales y fallarian
en silencio (`Docs/definitions.md`, "Convencion de nombres").
"""

from enum import Enum


class _Vocabulario(str, Enum):
    """Base de todos: hereda de `str` para que el valor viaje tal cual en JSON."""

    def __str__(self):
        return self.value


# --- Plano Mundo -----------------------------------------------------------

class RolDramatico(_Vocabulario):
    PROTAGONISTA = "protagonista"
    ANTAGONISTA = "antagonista"
    ALIADO = "aliado"
    GUARDIAN_DEL_UMBRAL = "guardian_del_umbral"
    VICTIMA = "victima"
    TESTIGO = "testigo"


class EstadoVital(_Vocabulario):
    VIVO = "vivo"
    MUERTO = "muerto"
    DESAPARECIDO = "desaparecido"


class CertezaCanonica(_Vocabulario):
    ESTABLECIDO = "establecido"
    IMPLICITO = "implicito"
    DISPUTADO = "disputado"


class DurabilidadDelHecho(_Vocabulario):
    """Independiente de `CertezaCanonica`: cuanto dura no es cuanto se sabe."""

    PERMANENTE = "permanente"
    EFIMERO = "efimero"


class TipoDeUsoDeHecho(_Vocabulario):
    """Que relacion tiene una escena con un hecho (`SPEC-21` C-2).

    POR QUE SON CUATRO Y NO UNO
    ----------------------------
    "Usar un hecho" parece una sola cosa y son cuatro, con condiciones de
    verdad distintas y consumidores distintos:

        establece   el texto lo hace verdadero por primera vez;
        menciona    el enunciado aparece en el texto, y nada mas;
        depende     alguien obro sirviendose de el: si fuera falso, la escena
                    no se sostiene;
        contradice  la escena afirma algo incompatible.

    Colapsarlos rompe las dos puntas a la vez. "Este elemento aparece en algun
    capitulo" se satisface con `menciona`; exigir `depende` lo daria por
    incumplido. La regeneracion selectiva necesita `depende`; contar tambien
    los `menciona` reescribe media novela por una alusion de paso.

    Y `contradice` **no es un uso**: no cuenta como aparicion y no arrastra
    regeneracion hacia adelante, sino correccion hacia atras. Vive aqui porque
    es la misma arista del grafo con otro signo, y separarla obligaria a unir
    dos tablas para preguntar que relacion tiene un capitulo con un hecho.
    """

    ESTABLECE = "establece"
    MENCIONA = "menciona"
    DEPENDE = "depende"
    CONTRADICE = "contradice"


class OrigenDeUso(_Vocabulario):
    """Quien afirmo la fila, que no es lo mismo que si es verdad.

    Una fila `regla` la calculo el codigo sobre el texto: es un dato medido.
    Una `delta` o una `juez_llm` la declaro un modelo: es una afirmacion no
    verificada. Un demostrador formal no puede tratarlas igual, y sin esta
    columna no hay forma de distinguirlas despues.
    """

    REGLA = "regla"
    DELTA = "delta"
    JUEZ_LLM = "juez_llm"
    HUMANO = "humano"


class TipoDePresencia(_Vocabulario):
    """Estar en un evento no es que hablen de ti (`SPEC-21` C-3).

    La comprobacion de que nadie esta en dos lugares a la vez solo mira los
    `presente`. Si un personaje nombrado contara como presente, cada vez que
    dos personajes se acordaran del mismo ausente el validador diria que ese
    ausente esta en dos sitios.
    """

    PRESENTE = "presente"
    MENCIONADO = "mencionado"


class TipoDeSujeto(_Vocabulario):
    PERSONAJE = "personaje"
    NARRADOR = "narrador"
    LECTOR = "lector"


class GradoDeConocimiento(_Vocabulario):
    IGNORA = "ignora"
    SOSPECHA = "sospecha"
    CREE = "cree"
    SABE = "sabe"


# --- Plano Obra ------------------------------------------------------------

class PersonaNarrativa(_Vocabulario):
    PRIMERA = "primera"
    SEGUNDA = "segunda"
    TERCERA_LIMITADA = "tercera_limitada"
    TERCERA_OMNISCIENTE = "tercera_omnisciente"


class TiempoVerbal(_Vocabulario):
    PRESENTE = "presente"
    PASADO = "pasado"


class EjeDeValor(_Vocabulario):
    SEGURIDAD = "seguridad"
    CONOCIMIENTO = "conocimiento"
    CONTROL = "control"
    VINCULO = "vinculo"
    CORDURA = "cordura"
    VIDA = "vida"


class SignoDeCambio(_Vocabulario):
    POSITIVO = "positivo"
    NEGATIVO = "negativo"


class EstadoDeEscena(_Vocabulario):
    PLANIFICADA = "planificada"
    GENERADA = "generada"
    EN_VERIFICACION = "en_verificacion"
    RECHAZADA = "rechazada"
    EN_REVISION = "en_revision"
    ACEPTADA = "aceptada"
    ACEPTADA_POR_RENDICION = "aceptada_por_rendicion"
    CONSOLIDADA = "consolidada"


class EstadoDeCapitulo(_Vocabulario):
    ABIERTO = "abierto"
    CERRADO = "cerrado"


# --- Plano Terror ----------------------------------------------------------

class FuenteDelMiedo(_Vocabulario):
    DESCONOCIDO = "desconocido"
    PERDIDA_DE_CONTROL = "perdida_de_control"
    CONTAMINACION = "contaminacion"
    PARANOIA = "paranoia"
    CULPA = "culpa"
    AISLAMIENTO = "aislamiento"


class EstadoDePresagio(_Vocabulario):
    PLANTADO = "plantado"
    PAGADO = "pagado"
    HUERFANO = "huerfano"


class TipoDeValvula(_Vocabulario):
    HUMOR = "humor"
    TERNURA = "ternura"
    INFORMACION = "informacion"
    SEGURIDAD_FALSA = "seguridad_falsa"


class EjeDeDeterioro(_Vocabulario):
    CORDURA = "cordura"
    CUERPO = "cuerpo"
    VINCULOS = "vinculos"
    RECURSOS = "recursos"


# --- Plano Proceso ---------------------------------------------------------

class TipoDePase(_Vocabulario):
    CONTINUIDAD = "continuidad"
    VOZ = "voz"
    RITMO = "ritmo"
    DENSIDAD = "densidad"
    LINEA = "linea"


# --- Plano Calidad ---------------------------------------------------------

class EstadoDeHallazgo(_Vocabulario):
    ABIERTO = "abierto"
    RESUELTO = "resuelto"
    DESCARTADO = "descartado"
    SIN_VEREDICTO = "sin_veredicto"
    """No es un hallazgo mas: el verificador no llego a emitir juicio."""


class TipoDeVerificador(_Vocabulario):
    REGLA = "regla"
    JUEZ_LLM = "juez_llm"
    HUMANO = "humano"


class NivelDeEvaluacion(_Vocabulario):
    ESCENA = "escena"
    CAPITULO = "capitulo"
    OBRA = "obra"


class Severidad(_Vocabulario):
    BLOQUEANTE = "bloqueante"
    MAYOR = "mayor"
    MENOR = "menor"


# --- Plano Destinatario (`SPEC-25`) ----------------------------------------
#
# Las cuatro que elige el comprador terminan en `OTRO`. Elegir `OTRO` obliga a
# guardar sus palabras literales (`FichaDeEntrevista.literales_de_otro`): es lo
# que deja preguntar con naturalidad y seguir comprobando con codigo.

class Ocasion(_Vocabulario):
    CUMPLEANOS = "cumpleanos"
    BODA = "boda"
    ANIVERSARIO = "aniversario"
    JUBILACION = "jubilacion"
    NACIMIENTO = "nacimiento"
    OTRO = "otro"


class GeneroDeLaHistoria(_Vocabulario):
    AVENTURA = "aventura"
    ROMANCE = "romance"
    COMEDIA = "comedia"
    FANTASIA = "fantasia"
    MISTERIO = "misterio"
    DRAMA_COTIDIANO = "drama_cotidiano"
    OTRO = "otro"


class TonoDeLaHistoria(_Vocabulario):
    TIERNO = "tierno"
    DIVERTIDO = "divertido"
    EMOTIVO = "emotivo"
    EPICO = "epico"
    NOSTALGICO = "nostalgico"
    OTRO = "otro"


class PapelDelDestinatario(_Vocabulario):
    PROTAGONISTA = "protagonista"
    PERSONAJE_SECUNDARIO = "personaje_secundario"
    OTRO = "otro"


class TipoDeElementoPersonal(_Vocabulario):
    RASGO = "rasgo"
    RECUERDO = "recuerdo"
    PERSONA = "persona"
    MASCOTA = "mascota"


class EstadoDeHechoPropuesto(_Vocabulario):
    PROPUESTO = "propuesto"
    CONFIRMADO = "confirmado"
    DESCARTADO = "descartado"


class NivelDeVeto(_Vocabulario):
    GLOBAL = "global"
    FRANJA_DE_EDAD = "franja_de_edad"
    NOVELA = "novela"


class TipoDeContradiccion(_Vocabulario):
    EDAD_FRENTE_A_GENERO = "edad_frente_a_genero"
    EDAD_FRENTE_A_OCASION = "edad_frente_a_ocasion"
    RECUERDO_FRENTE_A_EDAD = "recuerdo_frente_a_edad"
    JUICIO_DEL_MODELO = "juicio_del_modelo"
    """No es una comprobacion: la emite el Entrevistador cuando hay un `otro`
    que el codigo no puede comparar (`SPEC-25` `RF-08b`)."""


class TipoDeDecisionDePolitica(_Vocabulario):
    COINCIDENCIA_VETADA = "coincidencia_vetada"
    REESCRITURA_PEDIDA = "reescritura_pedida"
    PARADA_POR_VETADA = "parada_por_vetada"
    INSTRUCCION_EN_TEXTO_LIBRE = "instruccion_en_texto_libre"
    CONTRADICCION_DETECTADA = "contradiccion_detectada"
    CONTRADICCION_RESUELTA = "contradiccion_resuelta"
    BORRADO_AL_ENTREGAR = "borrado_al_entregar"
    HERRAMIENTA_DENEGADA = "herramienta_denegada"
    """`SPEC-26` `RF-18`: el hook de policy nego una herramienta a un agente."""


class CriterioDeEdicion(_Vocabulario):
    """Los criterios del Editor (`SPEC-26` `RF-09`). Ninguno es de terror: la
    rubrica del Juez de terror sigue existiendo para las obras de terror."""

    CONTINUIDAD = "continuidad"
    TONO = "tono"
    ARCO = "arco"
    COHERENCIA_DE_PERSONAJES = "coherencia_de_personajes"
    RITMO = "ritmo"
    PERSONALIZACION = "personalizacion"
