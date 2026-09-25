"""La historia de una novela, para la administracion (`SPEC-37`, `PLAN-37` H1).

Todo por SQL y resuelto aqui: la pagina lo pinta (`CLAUDE.md`). Las tablas que no existan en
una base se leen como vacias: una obra sin versiones es una obra con la version 1.

EL COSTE POR CAPITULO SE ATRIBUYE (`RF-04`)
--------------------------------------------
`gasto_de_delegacion` no guarda el capitulo. El pipeline apunta la fase en
`progreso_de_generacion` justo antes de cada llamada (`ConFase`), asi que cada gasto se
atribuye a **la ultima fila de progreso de la obra anterior a el**: su capitulo, o el plan, o la
puerta. La version, por su fecha de creacion. **Punto ciego**: las horas van por segundos, y un
gasto en el mismo segundo que la fase siguiente cae en la siguiente.
"""

import bisect
import json

from app.commons.db import migraciones
from app.commons.dominio import enumeraciones as enums
from app.commons.obra.vigente import version_vigente

ATRIBUCION = ("El coste de cada capitulo es una atribucion: cada delegacion se asigna a la ultima "
              "fase del progreso de la obra anterior a ella, que el pipeline apunta justo antes "
              "de llamar; la version, por su fecha de creacion. Lo anterior al primer progreso "
              "es de la entrevista.")

_FASES_DEL_PLAN = ("planificando", "revisando_plan")
_CRITERIOS = [c.value for c in enums.CriterioDeEdicion]


def _tabla(con, t):
    return migraciones.tiene_tabla(con, t)


def _coste(filas):
    """`CosteDeUnaObra` de unas filas de gasto, o `None` si no hay ninguna."""
    if not filas:
        return None
    medidos = [f["usd"] for f in filas if f["usd"] is not None]
    sin = len(filas) - len(medidos)
    return {"generacion": None, "usd": sum(medidos) if medidos else None,
            "delegaciones": len(filas), "sin_coste": sin, "es_suelo": sin > 0}


def _versiones(con, obra):
    if not _tabla(con, "version_de_obra"):
        return [{"numero": 1, "creada_en": None, "peticion": None, "anterior": None}]
    filas = con.execute("SELECT numero, creada_en, peticion, anterior FROM version_de_obra "
                        "WHERE obra = ? ORDER BY numero", (obra,)).fetchall()
    return ([{"numero": f[0], "creada_en": f[1], "peticion": f[2], "anterior": f[3]} for f in filas]
            or [{"numero": 1, "creada_en": None, "peticion": None, "anterior": None}])


def _capitulos_de(con, obra, numero):
    """`[id por posicion]` de la version, o los de `capitulo` por orden sin versiones."""
    if _tabla(con, "capitulo_de_version"):
        filas = con.execute("SELECT capitulo FROM capitulo_de_version WHERE obra = ? AND "
                            "numero = ? ORDER BY orden", (obra, numero)).fetchall()
        if filas:
            return [f[0] for f in filas]
    return [f[0] for f in con.execute("SELECT id FROM capitulo WHERE obra = ? ORDER BY orden",
                                      (obra,))]


def _version_de(cuando, versiones):
    """La version de una hora: la ultima creada antes de ella (la 1 si no hay fechas)."""
    elegida = versiones[0]["numero"]
    for v in versiones:
        if v["creada_en"] and cuando and v["creada_en"] <= cuando:
            elegida = v["numero"]
    return elegida


def _escenas(con, obra, capitulo):
    return con.execute("SELECT id, estado, borrador_aceptado FROM escena WHERE obra = ? AND "
                       "capitulo = ? ORDER BY orden", (obra, capitulo)).fetchall()


def _intentos(con, escenas):
    if not escenas:
        return 0
    marcas = ",".join("?" * len(escenas))
    return con.execute("SELECT COUNT(*) FROM borrador WHERE escena IN ({0})".format(marcas),
                       [e[0] for e in escenas]).fetchone()[0]


def _notas(con, escenas, umbral):
    notas = []
    if not _tabla(con, "valoracion_del_editor"):
        return notas
    for id_e, _, aceptado in escenas:
        if aceptado is None:
            continue
        filas = {f[0]: f for f in con.execute(
            "SELECT criterio, nota, justificacion, instruccion FROM valoracion_del_editor "
            "WHERE escena = ? AND version = ?", (id_e, aceptado))}
        for c in _CRITERIOS:
            if c in filas:
                _, nota, justificacion, instruccion = filas[c]
                notas.append({"criterio": c, "nota": nota, "justificacion": justificacion,
                              "instruccion": instruccion or None, "bajo_el_umbral": nota < umbral})
    return notas


def _condiciones(texto):
    try:
        condiciones = json.loads(texto or "[]")
    except ValueError:
        return [texto]
    return ["{0} ({1}): {2}".format(c.get("invariante"), c.get("capitulo") or "obra",
                                    c.get("detalle")) if isinstance(c, dict) else str(c)
            for c in condiciones]


def historia(con, obra, umbral):
    """`None` si la obra no existe (ni montada ni con progreso ni con entrevista)."""
    progreso = []
    if _tabla(con, "progreso_de_generacion"):
        progreso = [{"fase": f[0], "capitulo": f[1], "motivo": f[2], "desde": f[3]}
                    for f in con.execute("SELECT fase, capitulo, motivo, desde FROM "
                                         "progreso_de_generacion WHERE obra = ? ORDER BY desde, "
                                         "id", (obra,))]
    montada = con.execute("SELECT titulo FROM obra WHERE id = ?", (obra,)).fetchone()
    entrevista = (_tabla(con, "entrevista") and con.execute(
        "SELECT id, cerrada FROM entrevista WHERE obra = ?", (obra,)).fetchone()) or None
    if montada is None and not progreso and entrevista is None:
        return None
    gastos = []
    if _tabla(con, "gasto_de_delegacion"):
        gastos = [{"agente": f[0], "usd": f[1], "cuando": f[2]} for f in con.execute(
            "SELECT agente, coste_usd, cuando FROM gasto_de_delegacion WHERE obra = ? ORDER BY "
            "cuando, id", (obra,))]
    versiones = _versiones(con, obra)

    # Atribucion: cada gasto a la ultima fila de progreso anterior o igual a el.
    horas = [p["desde"] for p in progreso]
    cubos = {}
    for g in gastos:
        i = bisect.bisect_right(horas, g["cuando"]) - 1
        if i < 0:
            clave = ("entrevista",)
        else:
            p, v = progreso[i], _version_de(g["cuando"], versiones)
            if p["fase"] in _FASES_DEL_PLAN:
                clave = ("plan",)
            elif p["capitulo"] is not None:
                clave = ("capitulo", v, p["capitulo"])
            else:
                clave = ("puerta", v)
            g["clave"] = clave
        g.setdefault("clave", clave)
        cubos.setdefault(clave, []).append(g)

    eventos = []
    if entrevista is not None or ("entrevista",) in cubos:
        cuando = None
        if entrevista is not None and _tabla(con, "turno_de_entrevista"):
            cuando = con.execute("SELECT MAX(cuando) FROM turno_de_entrevista WHERE entrevista "
                                 "= ?", (entrevista[0],)).fetchone()[0]
        eventos.append(_evento("entrevista", cuando=cuando, coste=_coste(cubos.get(("entrevista",))),
                               aprobado=bool(entrevista[1]) if entrevista else None))
    if _tabla(con, "plan_de_obra"):
        rondas = con.execute("SELECT version, aprobado, origen, objeciones FROM plan_de_obra "
                             "WHERE obra = ? ORDER BY version", (obra,)).fetchall()
        for n, (version, aprobado, origen, objeciones) in enumerate(rondas):
            eventos.append(_evento(
                "ronda_del_plan", ronda=version, aprobado=bool(aprobado), origen=origen,
                objeciones=[str(o) for o in json.loads(objeciones or "[]")],
                # Las rondas no tienen hora: el coste del plan entero va en la ultima.
                coste=_coste(cubos.get(("plan",))) if n == len(rondas) - 1 else None))

    for v in versiones:
        numero = v["numero"]
        propios = _capitulos_de(con, obra, numero)
        del_numero = []
        if v["anterior"] is not None:
            anteriores = _capitulos_de(con, obra, v["anterior"])
            cambiados = [n for n, c in enumerate(propios, 1)
                         if n > len(anteriores) or anteriores[n - 1] != c]
            peticion = None
            if v["peticion"] is not None and _tabla(con, "peticion_de_cambio"):
                f = con.execute("SELECT texto FROM peticion_de_cambio WHERE id = ? AND obra = ?",
                                (v["peticion"], obra)).fetchone()
                peticion = f[0] if f else None
            eventos.append(_evento("version", cuando=v["creada_en"], version=numero,
                                   peticion=peticion, capitulos_cambiados=cambiados))
        else:
            cambiados = list(range(1, len(propios) + 1))
        ventana = _ventana(v, versiones)
        for n in cambiados:
            filas = [p for p in progreso if p["capitulo"] == n and _dentro(p["desde"], ventana)]
            escenas = _escenas(con, obra, propios[n - 1]) if n <= len(propios) else []
            coste = _coste(cubos.get(("capitulo", numero, n)))
            if not filas and not any(e[2] is not None for e in escenas):
                continue
            intentos = _intentos(con, escenas)
            eventos_del = [_evento(
                "capitulo", cuando=filas[0]["desde"] if filas else None, version=numero,
                capitulo=n, coste=coste, notas=_notas(con, escenas, umbral), intentos=intentos,
                escenas=[{"id": e[0], "estado": e[1]} for e in escenas])]
            for p in filas:
                if p["fase"] == "parada":
                    eventos_del.append(_evento("parada", cuando=p["desde"], version=numero,
                                               capitulo=n, motivo=p["motivo"], coste=coste,
                                               intentos=intentos))
            del_numero.extend(eventos_del)
        if _tabla(con, "veredicto_de_publicacion"):
            rondas = con.execute("SELECT ronda, publica, condiciones, codigo_lean, cuando FROM "
                                 "veredicto_de_publicacion WHERE obra = ? AND version = ? "
                                 "ORDER BY ronda", (obra, numero)).fetchall()
            puerta = cubos.get(("puerta", numero), [])
            for i, (ronda, publica, condiciones, codigo, cuando) in enumerate(rondas):
                antes = [r[4] for r in rondas[:i]]
                propias = [g for g in puerta if (cuando is None or g["cuando"] <= cuando)
                           and not any(a and g["cuando"] <= a for a in antes)]
                if i == len(rondas) - 1:
                    propias += [g for g in puerta if cuando and g["cuando"] > cuando]
                del_numero.append(_evento("ronda_de_la_puerta", cuando=cuando, version=numero,
                                          ronda=ronda, aprobado=bool(publica), codigo_lean=codigo,
                                          condiciones=_condiciones(condiciones) if not publica
                                          else [], coste=_coste(propias)))
        # Lo que no tiene hora se escribio despues de crear su version: se ordena por ella, y
        # en pantalla sigue diciendo que no tiene hora.
        del_numero.sort(key=lambda e: (e["cuando"] or v["creada_en"] or "",
                                       _ORDEN.index(e["tipo"])))
        eventos.extend(del_numero)

    vigente = version_vigente(con, obra) or 1
    notas_vigentes = []
    for id_c in _capitulos_de(con, obra, vigente):
        notas_vigentes += [n["nota"] for n in _notas(con, _escenas(con, obra, id_c), umbral)]
    por_agente = {}
    for g in gastos:
        por_agente.setdefault(g["agente"], []).append(g)
    return {
        "obra": obra, "titulo": montada[0] if montada else None,
        "totales": {"coste": _coste(gastos),
                    "nota_media": (sum(notas_vigentes) / len(notas_vigentes)
                                   if notas_vigentes else None),
                    "paradas": sum(1 for p in progreso if p["fase"] == "parada"),
                    "version_vigente": vigente if montada else None},
        "por_agente": [dict(_coste(fs), agente=a) for a, fs in sorted(
            por_agente.items(), key=lambda x: -sum(g["usd"] or 0 for g in x[1]))],
        "abiertos": _abiertos(con, obra),
        "eventos": eventos,
        "atribucion": ATRIBUCION,
    }


_ORDEN = ["entrevista", "ronda_del_plan", "version", "capitulo", "parada", "ronda_de_la_puerta"]


def _ventana(v, versiones):
    siguiente = next((w["creada_en"] for w in versiones if w["numero"] > v["numero"]), None)
    return v["creada_en"], siguiente


def _dentro(hora, ventana):
    desde, hasta = ventana
    return (desde is None or hora >= desde) and (hasta is None or hora < hasta)


def _abiertos(con, obra):
    if not _tabla(con, "hallazgo"):
        return []
    filas = con.execute(
        "SELECT h.invariante, h.severidad, c.orden, h.descripcion FROM hallazgo h "
        "JOIN escena e ON e.id = h.escena LEFT JOIN capitulo c ON c.id = e.capitulo "
        "WHERE e.obra = ? AND h.estado IN ('abierto', 'sin_veredicto') ORDER BY c.orden, h.id",
        (obra,)).fetchall()
    return [{"invariante": f[0], "severidad": f[1], "capitulo": f[2], "descripcion": f[3]}
            for f in filas]


def _evento(tipo, **campos):
    base = {"tipo": tipo, "cuando": None, "version": None, "capitulo": None, "coste": None,
            "notas": [], "escenas": [], "intentos": None, "motivo": None, "aprobado": None,
            "origen": None, "objeciones": [], "ronda": None, "codigo_lean": None,
            "condiciones": [], "peticion": None, "capitulos_cambiados": []}
    base.update(campos)
    return base
