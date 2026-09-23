"""El bucle de escenas: la unica pieza que las encadena.

Reune el material de cada escena, lo monta, ejecuta su ciclo y pasa a la
siguiente. **Solo si la anterior esta consolidada** (`INV-05`): hasta que el
delta no esta aplicado, el estado del mundo no ha cambiado y la escena
siguiente generaria contra un mundo que ya no es.

POR QUE EL MATERIAL LO REUNE ESTE MODULO
------------------------------------------
Porque es el unico autorizado a componer (`A-02`). `features/contexto/` monta
los bloques pero **no va a buscarlos**: no importa `consolidacion/` ni
`escaleta/`. Reunir es acoplar, y acoplar es cosa de `orquestacion/`.

En `F3` se aprendio que el acoplamiento tambien viaja por SQL sin que ningun
`import` lo delate (`F-28`), asi que aqui se hace explicito: este modulo lee de
las dos features y les pasa el resultado a la tercera.

QUE PASA CUANDO UNA `bloqueante` DETIENE LA OBRA
--------------------------------------------------
Se para. No se rinde y no se salta: rendirse ante `INV-03` meteria un hecho
falso en el registro de conocimiento y **todas las escenas siguientes se
generarian encima**. Con sesenta escenas eso es peor, no mejor.

Lo que si se hace es **dejar el dato**: en que escena paro, que invariante y
con que descripcion. Con que frecuencia `INV-03` bloquea una generacion larga
no se sabe (`VER-64`), y una parada en la tercera escena **no es un fracaso: es
la medida**.
"""

import json
from dataclasses import dataclass, field

from app.commons import config
from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.features.auditoria import capitulo
from app.features.consolidacion import memoria, mundo as modulo_mundo
from app.features.contexto import ensamblado, recorte
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, rendicion


@dataclass
class Generacion:
    escenas_hechas: list = field(default_factory=list)
    parada: dict | None = None
    medidas: list = field(default_factory=list)
    rendidas: list = field(default_factory=list)
    delegaciones: int = 0
    cierre: dict | None = None

    @property
    def llego_al_final(self):
        return self.parada is None


def reunir_material(con, escena, obra_id, inmutable=""):
    """Lo que hay disponible para montar el contexto de esta escena."""
    orden = escena["orden"]
    anterior = con.execute(
        "SELECT b.texto FROM borrador b JOIN escena e ON e.id = b.escena "
        "WHERE e.orden = ? ORDER BY b.version DESC LIMIT 1", (orden - 1,)).fetchone()
    return {
        "resumenes": memoria.resumenes_hasta(con, orden),
        "fichas": memoria.fichas_en(con, orden),
        "escena_anterior": anterior[0] if anterior else "",
        "mundo": modulo_mundo.leer(con),
        "problemas": repo.hallazgos_abiertos(con, escena["id"]),
        "hechos": repo.hechos_declarados(con, obra_id),
        "inmutable": inmutable,
    }


def generar_obra(con, obra, escritor, juez, resumidor, inmutable="",
                 techo=100_000, hasta=None, tope_intentos=None,
                 tope_delegaciones=None):
    """Genera las escenas en orden. Se detiene en la primera `bloqueante`.

    Cada escena tiene hasta `tope_intentos` (`TOPE_INTENTOS_ESCENA`), y los
    problemas de un intento entran en el prompt del siguiente: si no, el
    escritor no sabe nada del fallo y vuelve a cometerlo, que es lo que le pasó
    a la otra rama con el aviso de longitud.

    Y la obra entera tiene `tope_delegaciones` (`TOPE_DELEGACIONES_OBRA`), que
    **acota el gasto y no el error**.
    """
    tope_intentos = tope_intentos or config.TOPE_INTENTOS_ESCENA
    tope_delegaciones = tope_delegaciones or config.TOPE_DELEGACIONES_OBRA
    g = Generacion()
    for escena in repo.escenas_de(con, obra):
        if hasta is not None and escena["orden"] > hasta:
            break

        if not rendicion.queda_presupuesto(g.delegaciones, tope_delegaciones):
            g.parada = {"escena": escena["id"], "motivo": "tope_delegaciones",
                        "delegaciones": g.delegaciones,
                        "detalle": "acota el gasto, no el error: lo decide una "
                                   "persona y no un bucle"}
            return g

        material = reunir_material(con, escena, obra, inmutable)
        bloques = ensamblado.montar(material)
        tamanos = ensamblado.tamanos(bloques)

        try:
            plan = recorte.planificar(tamanos, techo=techo)
        except recorte.NoCabe as e:
            g.parada = {"escena": escena["id"], "motivo": "no_cabe",
                        "detalle": "RF-26: agotadas las formas reducidas"}
            g.medidas.append(_medida(escena, tamanos, e.plan))
            return g
        g.medidas.append(_medida(escena, tamanos, plan))

        c, intentos = _intentar(con, escena, tamanos, escritor, juez, resumidor,
                                material, techo, tope_intentos, g)

        if c.fallo:
            g.parada = {"escena": escena["id"], "motivo": c.fallo,
                        "intentos": len(intentos),
                        "hallazgos": [(h.invariante, h.descripcion)
                                      for h in (c.generacion.hallazgos
                                                if c.generacion else [])]}
            return g

        if c.generacion.hallazgos:
            # Se agotaron los intentos y lo que queda no corrompe el canon:
            # `RF-24`. La escena pasa a `aceptada_por_rendicion` y **no** a
            # `aceptada`, para que quien lea el manuscrito pueda distinguirlas.
            version = rendicion.menos_malo([(v, h) for v, h, _ in intentos])
            elegido = next(c2 for v, _, c2 in intentos if v == version)
            repo.rendir_escena(con, escena["id"], version)
            c = ciclo.consolidar_y_resumir(
                elegido, con, escena["id"],
                ciclo.texto_de(con, escena["id"], version), resumidor,
                "obra-{0}-rendicion".format(escena["orden"]))
            g.rendidas.append((escena["id"], version, len(intentos)))
            if c.fallo:
                g.parada = {"escena": escena["id"], "motivo": c.fallo,
                            "intentos": len(intentos), "hallazgos": []}
                return g

        if c.resumen:
            memoria.guardar_resumen(
                con, escena["id"], escena["orden"],
                str(c.resumen.get("texto") or ""),
                [h for h in (c.resumen.get("hechos_clave") or [])
                 if memoria.IDENTIFICADOR.match(str(h))])
        _marcar_establecidos(con, escena, c)
        _actualizar_fichas(con, escena, c)
        g.escenas_hechas.append(escena["id"])

    g.cierre = evaluar_cierre(con, obra)
    return g


def evaluar_cierre(con, obra):
    """Dice si el capitulo **podria** cerrarse. No lo cierra.

    La firma es humana y la dispara el cliente de la API, nunca el worker
    (`Docs/architecture.md`): al decidir que un `mayor` no detiene la escena, el
    control no desaparecio, **se movio aqui**, que es donde una persona puede
    juzgar si el conjunto se sostiene. Un bucle que firmara solo devolveria ese
    control a la maquina y dejaria la puerta de adorno.

    Lo que si hace el bucle es dejar el veredicto preparado, porque tener que
    ir a buscarlo a mano es la forma mas facil de no mirarlo nunca.
    """
    escenas = repo.escenas_de(con, obra)
    estados = [EE(e["estado"]) for e in escenas]
    hallazgos = [dict(h, severidad=h["severidad"], estado=h["estado"])
                 for e in escenas for h in repo.hallazgos_abiertos(con, e["id"])]
    try:
        cierre = capitulo.cerrar(estados, hallazgos)
    except capitulo.NoSePuedeCerrar as e:
        detalle = "; ".join(sorted({h["invariante"] for h in hallazgos})) or ""
        return {"puede_cerrarse": False, "firmado": False,
                "motivo": "{0} [{1}]".format(e, detalle)}
    return {"puede_cerrarse": True, "firmado": False,
            "menores_que_se_dejan_pasar": cierre.menores_que_se_dejan_pasar}


def _intentar(con, escena, tamanos, escritor, juez, resumidor, material,
              techo, tope, g):
    """Hasta `tope` intentos, y los problemas de uno entran en el siguiente.

    Se para en cuanto sale limpia, y **tambien en cuanto una `bloqueante`
    aparece**: reintentar ante una `bloqueante` no es mas seguro, es mas caro.
    Lo que no se puede rendir tampoco se puede arreglar insistiendo, porque el
    modelo no sabe cual de las quince reglas ha roto — solo lo que le digamos.
    """
    intentos = []
    c = None
    for numero in range(tope):
        c = ciclo.ejecutar(con, escena["id"], tamanos, escritor, juez, resumidor,
                           material["mundo"], techo=techo,
                           trabajo="obra-{0}-i{1}".format(escena["orden"], numero + 1),
                           hechos=[h["id"] for h in material["hechos"]],
                           problemas=_problemas_de(intentos))
        g.delegaciones += ciclo.coste_total(c.trazas)["delegaciones"]
        if c.generacion is not None and c.generacion.version is not None:
            intentos.append((c.generacion.version, c.generacion.hallazgos, c))
        if c.fallo or not c.generacion.hallazgos:
            break
    return c, intentos


def _problemas_de(intentos):
    """Lo que fallo en el ultimo intento, en la forma que espera el prompt."""
    if not intentos:
        return None
    return [{"invariante": h.invariante, "descripcion": h.descripcion}
            for h in intentos[-1][1]]


def _marcar_establecidos(con, escena, c):
    """`SPEC-15`: `escena_de_establecimiento` dice donde lo establece el TEXTO.

    Un hecho que el plan no previo puede establecerse igual, y **se marca**:
    prohibirlo obligaria a replanificar por cada hallazgo del texto, y no
    marcarlo perderia la diferencia entre lo planificado y lo improvisado.
    """
    delta = (c.generacion.leida_delta if c.generacion else None) or {}
    for rev in delta.get("revelaciones", []):
        repo.establecer_hecho(con, rev["hecho"], escena["id"])


def _actualizar_fichas(con, escena, c):
    """Una ficha por entidad que el delta toco. Sin modelo: es un extracto."""
    delta = (c.generacion.leida_delta if c.generacion else None) or {}
    tocadas = {m["personaje"] for m in delta.get("movimientos", [])}
    tocadas |= {r["sujeto"] for r in delta.get("revelaciones", [])}
    if not tocadas:
        return
    m = modulo_mundo.leer(con)
    memoria.actualizar_fichas(con, escena["id"], escena["orden"], {
        e: "en {0}, {1}".format(m["ubicaciones"].get(e, "?"),
                                m["entidades_vivas"].get(e, "?"))
        for e in sorted(tocadas)})


def _medida(escena, tamanos, plan):
    """Lo que la Fase F existe para medir: cuanto ocupa cada bloque y si se
    recorto. El criterio de terminacion no es una prueba verde: es que esto
    crezca."""
    return {"escena": escena["id"], "orden": escena["orden"],
            "total": sum(tamanos.values()), "bloques": dict(tamanos),
            "recortes": [(p.bloque, p.clase.value) for p in plan]}


def informe(g: Generacion) -> str:
    lineas = ["escena  total   recortes"]
    for m in g.medidas:
        lineas.append("{0:6}  {1:6}  {2}".format(
            m["escena"], m["total"], m["recortes"] or "-"))
    if g.medidas:
        crecio = g.medidas[-1]["total"] > g.medidas[0]["total"]
        lineas.append("el contexto {0}".format("CRECE" if crecio else "NO crece"))
    if g.parada:
        lineas.append("PARADA en {0}: {1}".format(
            g.parada["escena"], g.parada["motivo"]))
        for inv, desc in g.parada.get("hallazgos", []):
            lineas.append("   [{0}] {1}".format(inv, desc))
    return "\n".join(lineas)
