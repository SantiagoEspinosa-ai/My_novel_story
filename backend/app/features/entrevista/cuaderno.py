"""El cuaderno de la entrevista (`SPEC-35` `RF-05`, `RF-07`, `PLAN-35` F1).

Lo que la ficha ya sabe, lo que falta y cuanto, **resuelto aqui**: la web no cuenta campos ni
traduce valores (`CLAUDE.md`: la interfaz muestra estado, no lo calcula). Y con palabras de
persona, porque quien encarga un regalo no tiene por que leer `cumpleanos` ni
`drama_cotidiano` (`RF-02`).

Los campos y su orden son los de `ficha.que_falta`: si alli se anade uno, aqui falta su
etiqueta y `etiqueta()` lo dice en vez de inventarla.
"""

from app.commons.configuracion.esquemas import extensiones_por_defecto
from app.commons.dominio.enumeraciones import TipoDeElementoPersonal as TE
from app.features.entrevista import ficha as modulo_ficha

ETIQUETAS = {
    "nombre": "Nombre", "edad": "Edad", "ocasion": "Ocasión", "genero": "Género",
    "tono": "Tono", "extension": "Extensión de cada capítulo",
    "papel": "Papel en la historia", "rasgo": "Rasgos", "recuerdo": "Recuerdos",
    "premisa": "Premisa", "titulo": "Título",
}

# Los valores de los vocabularios que no se leen tal cual. Lo que no esta aqui ya es una
# palabra de persona («boda», «tierno»).
PALABRAS = {
    "cumpleanos": "cumpleaños", "jubilacion": "jubilación", "fantasia": "fantasía",
    "drama_cotidiano": "drama cotidiano", "epico": "épico", "nostalgico": "nostálgico",
    "personaje_secundario": "personaje secundario",
}

# Todos los campos que el cuaderno puede enseñar: los obligatorios de `que_falta`.
CAMPOS = tuple(ETIQUETAS)


def etiqueta(campo):
    if campo not in ETIQUETAS:
        raise KeyError("el campo `{0}` de `que_falta` no tiene etiqueta en el "
                       "cuaderno".format(campo))
    return ETIQUETAS[campo]


def _vocabulario(ficha, campo):
    v = getattr(ficha, campo)
    if v is None:
        return []
    if v.value == "otro":
        return [ficha.literales_de_otro.get(campo) or "otro"]
    return [PALABRAS.get(v.value, v.value)]


def _momento(e):
    m = e.momento
    if m is None:
        return ""
    if m.edad is not None and m.anio is not None:
        return " (a los {0} años, en {1})".format(m.edad, m.anio)
    if m.edad is not None:
        return " (a los {0} años)".format(m.edad)
    if m.anio is not None:
        return " (en {0})".format(m.anio)
    return ""


def _elementos(ficha, tipo):
    return ["{0}{1}{2}".format(e.descripcion, _momento(e),
                               " (imprescindible)" if e.imprescindible else "")
            for e in ficha.destinatario.elementos if e.tipo is tipo]


def _valores(ficha, campo, extensiones):
    d = ficha.destinatario
    if campo == "nombre":
        return [d.nombre] if d.nombre else []
    if campo == "edad":
        return ["{0} años".format(d.edad)] if d.edad is not None else []
    if campo in ("ocasion", "genero", "tono", "papel"):
        return _vocabulario(ficha, campo)
    if campo == "extension":
        if ficha.extension is None:
            return []
        minimo, maximo = (extensiones or extensiones_por_defecto())[ficha.extension]
        return ["{0}: de {1} a {2} palabras por capítulo".format(
            ficha.extension.value, minimo, maximo)]
    if campo == "rasgo":
        return _elementos(ficha, TE.RASGO)
    if campo == "recuerdo":
        return _elementos(ficha, TE.RECUERDO)
    if campo in ("premisa", "titulo"):
        v = (getattr(ficha, campo) or "").strip()
        return [v] if v else []
    raise KeyError(campo)


def cuaderno(ficha, extensiones=None) -> dict:
    """`sabido`, `falta`, `total`, `faltan` y la `propuesta` del cuaderno completo."""
    falta = modulo_ficha.que_falta(ficha)
    sabido = [{"campo": c, "etiqueta": etiqueta(c), "valores": _valores(ficha, c, extensiones)}
              for c in CAMPOS if c not in falta]
    return {"sabido": sabido, "falta": [etiqueta(c) for c in falta],
            "total": len(CAMPOS), "faltan": len(falta),
            "propuesta": {"titulo": ficha.titulo or None, "premisa": ficha.premisa or None,
                          "dedicatoria": ficha.dedicatoria or None}}
