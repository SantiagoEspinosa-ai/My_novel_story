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
