"""La medida del arrastre de `SPEC-23` v2 (`PLAN-23` A1). **No escribe nada.**

QUE SE MIDE
-----------
La media, entre los hechos de la obra con al menos un uso de cualquier tipo en sus
escenas (`C-1`), del numero de **capitulos distintos** que lo usan segun `menciona`
(`SPEC-21`). Un hecho que solo se usa por `depende` entra con 0: es la lectura
literal, decidida antes de ver el numero. La regla la cerro el autor antes de medir:
**≤ 3 capitulos → `S-1` (cascada); > 3 → `S-2` (selectiva).**

CUANDO NO SE MIDE, Y SE DICE
----------------------------
Sin obra completa, sin ningun hecho con usos o sin procedencia (`MF-27`), la medida
**se niega** con lo que falta. Un numero sacado de ahi no es una medida: es la huella
de que algo no llego a ejecutarse, y es justo el que tranquiliza.

EL SESGO, EN EL MISMO OBJETO
----------------------------
`menciona` es lexico: un capitulo que alude al hecho sin sus palabras no cuenta. El
sesgo es **a la baja, hacia `S-1`**, que es la salida barata, y por eso viaja dentro
del resultado y no en una nota al pie.

Y lo que no puede medir lo informa aparte (hallazgo 9): un capitulo reescrito a delta
fijo despues de consolidar tiene el texto nuevo y las filas `menciona` del primero.
"""

import sqlite3

from app.commons.db.procedencia import SIN_DETERMINAR
from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import SalidaDeRegeneracion as S
from app.commons.dominio.enumeraciones import TipoDeUsoDeHecho as U
from app.features.escaleta import repository as escaleta

# `SPEC-23` v2, cerrado por el autor antes de ver el numero.
UMBRAL_DE_CAPITULOS = 3
SESGO = "a la baja, hacia S-1"
HECHAS = {EE.CONSOLIDADA.value, EE.ACEPTADA_POR_RENDICION.value}


def salida_para(arrastre_medio):
    return (S.CASCADA if arrastre_medio <= UMBRAL_DE_CAPITULOS else S.SELECTIVA).value


def _filas(con, sql, args=()):
    """Una tabla que no existe es una tabla vacia: preguntar no es crearla."""
    try:
        return list(con.execute(sql, args))
    except sqlite3.OperationalError:
        return []


def _commit(con):
    filas = _filas(con, "SELECT valor FROM procedencia WHERE clave = 'version_del_harness'")
    return filas[0][0] if filas else None


def _reescritas(con, escenas):
    """Las escenas cuyo texto aceptado no es el que levanto el acta.

    El delta se guarda con la version del borrador que se consolido. Si el texto
    elegido hoy es otra version, es una reescritura a delta fijo (`SPEC-30` `RF-10`) y
    sus `menciona` son del primer texto. Sin version en el delta **no consta**, y va a
    su propia lista: un dato ausente no es un verde."""
    reescritas, sin_version = [], []
    for e in escenas:
        delta = _filas(con, "SELECT version FROM delta_de_escena WHERE escena = ? "
                            "ORDER BY orden DESC LIMIT 1", (e["id"],))
        if not delta:
            continue
        elegida = e["borrador_aceptado"]
        if elegida is None:
            ultima = _filas(con, "SELECT MAX(version) FROM borrador WHERE escena = ?",
                            (e["id"],))
            elegida = ultima[0][0] if ultima else None
        if delta[0][0] is None:
            sin_version.append(e["id"])
        elif elegida != delta[0][0]:
            reescritas.append(e["id"])
    return reescritas, sin_version


def medir(con, obra, escenas=None):
    """El objeto de la medida, o la negativa con lo que falta. Nunca escribe.

    `escenas` son las de la obra que se mide; sin ellas, todas las de la obra."""
    if escenas is None:
        hay = _filas(con, "SELECT 1 FROM sqlite_master WHERE type='table' AND name='escena'")
        escenas = escaleta.escenas_de(con, obra) if hay else []
    capitulos = [f[0] for f in _filas(
        con, "SELECT id FROM capitulo WHERE obra = ? ORDER BY orden", (obra,))]
    con_escena = {e["capitulo"] for e in escenas}
    faltan = {"escenas_sin_hacer": sorted(e["id"] for e in escenas
                                         if e["estado"] not in HECHAS),
              "capitulos_sin_escena": [c for c in capitulos if c not in con_escena]}
    base = {"obra": obra, "umbral": UMBRAL_DE_CAPITULOS, "sesgo": SESGO}
    if not escenas or faltan["escenas_sin_hacer"] or faltan["capitulos_sin_escena"]:
        return dict(base, medido=False, faltan=faltan,
                    motivo="la obra no esta completa: la medida no se toma y la salida "
                           "no se elige")

    propias = {e["id"] for e in escenas}
    hechos = [f[0] for f in _filas(
        con, "SELECT id FROM hecho_canonico WHERE obra = ? ORDER BY id", (obra,))]
    detalle = []
    for h in hechos:
        # Hallazgo 10: `uso_de_hecho` no guarda la obra, y dos obras pueden tener un
        # hecho con el mismo `id`. Solo cuentan los usos de **sus** escenas.
        usos = [u for u in _filas(con, "SELECT escena, capitulo, tipo FROM uso_de_hecho "
                                       "WHERE hecho = ?", (h,)) if u[0] in propias]
        if not usos:
            continue
        menciones = [u for u in usos if u[2] == U.MENCIONA.value]
        capitulos_h = sorted({u[1] for u in menciones if u[1]})
        detalle.append({
            "hecho": h,
            "origen": "imprescindible" if h.startswith("imp-") else "plan",
            "capitulos": capitulos_h,
            "capitulos_por_mencion": len(capitulos_h),
            "usos_sin_capitulo": sum(1 for u in menciones if not u[1]),
        })
    if not detalle:
        return dict(base, medido=False, faltan={},
                    motivo="ningun hecho de la obra tiene usos: la medida no se toma")

    commit = _commit(con)
    if commit in (None, SIN_DETERMINAR):
        return dict(base, medido=False, faltan={},
                    motivo="la base no dice con que codigo se escribio (MF-27): una "
                           "medida sobre ella puede contestar sobre otro codigo")

    numerador = sum(d["capitulos_por_mencion"] for d in detalle)
    denominador = len(detalle)
    media = numerador / denominador
    reescritas, sin_version = _reescritas(con, escenas)
    return dict(base, medido=True, commit=commit, arrastre_medio=media,
                numerador=numerador, denominador=denominador, salida=salida_para(media),
                detalle=detalle, reescritas_tras_consolidar=reescritas,
                acta_sin_version=sin_version)
