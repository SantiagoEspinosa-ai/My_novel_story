"""De donde sale cada tipo de uso, y por que no todos salen del mismo sitio.

Tres de los cuatro tipos de `tipo_de_uso_de_hecho` se pueblan hoy **sin tocar
ningun prompt ni añadir ninguna delegacion**, porque el material ya existe:

    establece   `revelaciones` del delta  -- lo declara el escritor
    depende     `acciones` del delta      -- lo declara el escritor
    menciona    el texto del borrador     -- lo calcula este modulo

POR QUE `acciones` ES EXACTAMENTE `depende`
--------------------------------------------
`SPEC-16` separo dos campos que parecian uno: revelar es **aprender** y actuar
es **obrar sirviendose de lo ya sabido**. Ese segundo campo es, palabra por
palabra, la definicion de depender: si el hecho fuera falso, lo que el
personaje hizo no se sostiene. La relacion que parecia necesitar un modelo
nuevo llevaba escrita en el delta desde `SPEC-16`.

POR QUE `menciona` LO CALCULA EL CODIGO Y NO UN JUEZ
-----------------------------------------------------
Porque se puede comprobar: es buscar un enunciado en un texto. Lo que se puede
comprobar con codigo no se delega en un modelo, y ademas asi `menciona` es el
unico de los cuatro que es un dato **medido** y no una afirmacion. Esa
diferencia la guarda `origen_de_uso`, y para un demostrador formal no es un
matiz.

EL PUNTO CIEGO DE `menciona`, DECLARADO
----------------------------------------
Es lexico. Un capitulo que dice "la llave seguia donde su madre la dejo" usa el
hecho "La llave del sotano esta en el costurero" y **no lo menciona** para este
modulo. Es un falso negativo conocido, no un descuido: la alternativa -pedirselo
a un juez- cambia un punto ciego medible por uno que no lo es. Se compensa con
que `establece` y `depende` vienen declarados, asi que los tres juntos no
comparten punto ciego, que es lo que `docs/verification.md` Regla 3 pide.
"""

import re
import unicodedata

from app.commons.dominio.enumeraciones import OrigenDeUso as O
from app.commons.dominio.enumeraciones import TipoDePresencia as P
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U

# Cuantas palabras del enunciado tienen que aparecer seguidas para contarlo
# como mencion. Un enunciado entero casi nunca aparece literal en la prosa; una
# sola palabra lo dispara con cualquier "la". Se mide en palabras y no en
# caracteres porque el umbral tiene que significar lo mismo en un enunciado
# corto y en uno largo.
PALABRAS_MINIMAS_PARA_MENCION = 4


def _normalizar(texto):
    """Minusculas, sin tildes y sin puntuacion.

    Sin tildes porque una cadena acentuada admite dos representaciones Unicode
    iguales a la vista y distintas byte a byte (`docs/definitions.md`,
    "Convencion de nombres"): comparar sin normalizar falla en silencio.
    """
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", texto or "")
        if unicodedata.category(c) != "Mn")
    return re.sub(r"[^\w\s]", " ", sin_tildes.lower())


def _palabras(texto):
    return _normalizar(texto).split()


def menciona(texto, enunciado, minimas=PALABRAS_MINIMAS_PARA_MENCION):
    """True si `minimas` palabras consecutivas del enunciado estan en el texto.

    No se exige el enunciado entero: nadie escribe prosa citando su propio
    canon palabra por palabra. Se exige una tirada consecutiva porque las
    palabras sueltas de un enunciado cualquiera aparecen en cualquier texto.
    """
    del_texto = _palabras(texto)
    del_enunciado = _palabras(enunciado)
    if not del_texto or not del_enunciado:
        return False
    n = min(minimas, len(del_enunciado))
    ventanas_texto = {tuple(del_texto[i:i + n])
                      for i in range(len(del_texto) - n + 1)}
    return any(tuple(del_enunciado[i:i + n]) in ventanas_texto
               for i in range(len(del_enunciado) - n + 1))


def usos_de_la_escena(delta, texto, hechos, escena, capitulo):
    """Los usos que esta escena hace de los hechos declarados de la obra.

    `hechos` son los `HechoCanonico` de la obra tal como los devuelve
    `escaleta.hechos_declarados`: hace falta la lista para poder decir que una
    escena usa un hecho **que ya existia**, que es justo lo que ninguna pieza
    del sistema podia decir hasta ahora.

    Nunca devuelve `contradice`: ese tipo existe, se puede escribir a mano y
    **no lo deduce nadie todavia** (`SPEC-21`, "Qué queda fuera").
    """
    delta = delta or {}
    conocidos = {h["id"]: h.get("enunciado", "") for h in (hechos or [])}
    usos = {}

    def _anotar(id_hecho, tipo, origen):
        # Un hecho que el delta nombra y que la obra no declaro se ignora: el
        # plan declara que hechos existen (`SPEC-15`), y aceptar aqui uno
        # inventado por el texto lo colaria en el canon por la puerta de atras.
        if id_hecho not in conocidos:
            return
        usos[(id_hecho, tipo)] = {
            "hecho": id_hecho, "escena": escena, "capitulo": capitulo,
            "tipo": tipo, "origen": origen}

    for rev in delta.get("revelaciones", []):
        _anotar(rev.get("hecho"), U.ESTABLECE, O.DELTA)
    for acc in delta.get("acciones", []):
        _anotar(acc.get("hecho"), U.DEPENDE, O.DELTA)
    for id_hecho, enunciado in conocidos.items():
        if menciona(texto, enunciado):
            _anotar(id_hecho, U.MENCIONA, O.REGLA)

    return [usos[k] for k in sorted(usos, key=lambda k: (k[0], str(k[1])))]


def evento_de_la_escena(escena, obra):
    """El evento que aporta una escena, o `None` si no se puede situar.

    **Una escena sin `t_fabula` no produce evento y no se inventa uno.** Situar
    en el tiempo una escena que no dice cuando ocurre daria una cronologia
    completa y falsa, que es peor que una incompleta: la incompleta se nota.

    Devuelve el par `(evento, participantes)` que espera `registrar_evento`.
    Las escenas aportan un evento cada una; el delta puede declarar mas, y esos
    entran por `registrar_evento` directamente.
    """
    if not escena.get("t_fabula"):
        return None
    evento = {
        "id": "evt-{0}".format(escena["id"]),
        "obra": obra,
        "t_fabula": escena["t_fabula"],
        "duracion_min": escena.get("duracion_ficcional"),
        "lugar": escena.get("lugar"),
        "escena": escena["id"],
        "capitulo": escena.get("capitulo"),
        "descripcion": escena.get("objetivo_dramatico") or "",
    }
    presentes = escena.get("personajes_presentes") or []
    return evento, [(p, P.PRESENTE) for p in presentes]
