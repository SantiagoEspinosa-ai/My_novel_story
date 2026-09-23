"""Las contradicciones de la ficha (`SPEC-25` `RF-08`, `RF-08b`, `RF-09`).

Las tres son deterministas porque comparan categorias y numeros. Las parejas
incompatibles son configuracion (`ReglasDeContradiccion` en `sistema.json`).

CUANDO EL CODIGO NO SABE, LO DICE
---------------------------------
Si un campo comparado es `otro`, no hay categoria que comparar. La salida no es
"sin contradiccion" sino `requiere_juicio`, y quien pregunta es el
Entrevistador. Callarse aqui convertiria un "no lo se" en un verde.

LA DESCRIPCION ES LA IDENTIDAD
------------------------------
Una contradiccion resuelta se reconoce por `(tipo, descripcion)`. Por eso la
descripcion se construye siempre igual a partir de los datos: si el comprador
cambia la edad, la descripcion cambia y la resolucion vieja deja de valer, que
es lo correcto — resolvio otra contradiccion.
"""

from dataclasses import dataclass, field

from app.commons.dominio.enumeraciones import TipoDeContradiccion as TC
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal as TE


@dataclass(frozen=True)
class Contradiccion:
    tipo: TC
    descripcion: str


@dataclass
class Resultado:
    abiertas: list = field(default_factory=list)
    requiere_juicio: list = field(default_factory=list)


def _es_otro(valor):
    return valor is not None and valor.value == "otro"


def contradicciones(ficha, reglas, anio_actual) -> Resultado:
    r = Resultado()
    d = ficha.destinatario
    halladas = []
    if d.edad is not None:
        for campo, limites, tipo in (
                ("genero", reglas.edad_minima_por_genero, TC.EDAD_FRENTE_A_GENERO),
                ("ocasion", reglas.edad_minima_por_ocasion, TC.EDAD_FRENTE_A_OCASION)):
            valor = getattr(ficha, campo)
            if valor is None or _es_otro(valor):
                continue
            minima = limites.get(valor)
            if minima is not None and d.edad < minima:
                halladas.append(Contradiccion(tipo, "{0} «{1}» pide al menos {2} "
                                              "años y el destinatario tiene {3}".format(
                                                  campo, valor.value, minima, d.edad)))
        nacimiento = anio_actual - d.edad
        for e in d.elementos:
            if e.tipo is not TE.RECUERDO or e.momento is None:
                continue
            m = e.momento
            if m.edad is not None and m.edad > d.edad:
                halladas.append(Contradiccion(
                    TC.RECUERDO_FRENTE_A_EDAD,
                    "el recuerdo «{0}» es a los {1} años y el destinatario tiene "
                    "{2}".format(e.descripcion, m.edad, d.edad)))
            # Un año de margen: sin fecha de nacimiento, quien tiene 10 años
            # pudo nacer en `anio_actual - 10` o en el anterior.
            if m.anio is not None and (m.anio < nacimiento - 1 or m.anio > anio_actual):
                halladas.append(Contradiccion(
                    TC.RECUERDO_FRENTE_A_EDAD,
                    "el recuerdo «{0}» es de {1} y el destinatario nacio hacia "
                    "{2}".format(e.descripcion, m.anio, nacimiento)))
        r.requiere_juicio = [c for c in ("genero", "ocasion", "tono")
                             if _es_otro(getattr(ficha, c))]
    resueltas = {(c.tipo, c.descripcion) for c in ficha.contradicciones_resueltas}
    r.abiertas = [c for c in halladas if (c.tipo, c.descripcion) not in resueltas]
    return r
