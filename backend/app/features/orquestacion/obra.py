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

from app.features.consolidacion import memoria, mundo as modulo_mundo
from app.features.contexto import ensamblado, recorte
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo


@dataclass
class Generacion:
    escenas_hechas: list = field(default_factory=list)
    parada: dict | None = None
    medidas: list = field(default_factory=list)

    @property
    def llego_al_final(self):
        return self.parada is None


def reunir_material(con, escena, inmutable=""):
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
        "inmutable": inmutable,
    }


def generar_obra(con, obra, escritor, juez, resumidor, inmutable="",
                 techo=100_000, reserva_de_salida=20_000, hasta=None):
    """Genera las escenas en orden. Se detiene en la primera `bloqueante`."""
    g = Generacion()
    for escena in repo.escenas_de(con, obra):
        if hasta is not None and escena["orden"] > hasta:
            break

        material = reunir_material(con, escena, inmutable)
        bloques = ensamblado.montar(material)
        tamanos = ensamblado.tamanos(bloques, reserva_de_salida)

        try:
            plan = recorte.planificar(tamanos, techo=techo)
        except recorte.NoCabe as e:
            g.parada = {"escena": escena["id"], "motivo": "no_cabe",
                        "detalle": "RF-26: agotadas las formas reducidas"}
            g.medidas.append(_medida(escena, tamanos, e.plan))
            return g
        g.medidas.append(_medida(escena, tamanos, plan))

        c = ciclo.ejecutar(con, escena["id"], tamanos, escritor, juez, resumidor,
                           material["mundo"], techo=techo,
                           trabajo="obra-{0}".format(escena["orden"]))

        if c.fallo:
            g.parada = {"escena": escena["id"], "motivo": c.fallo,
                        "hallazgos": [(h.invariante, h.descripcion)
                                      for h in (c.generacion.hallazgos
                                                if c.generacion else [])]}
            return g

        if c.resumen:
            memoria.guardar_resumen(
                con, escena["id"], escena["orden"],
                str(c.resumen.get("texto") or ""),
                [h for h in (c.resumen.get("hechos_clave") or [])
                 if memoria.IDENTIFICADOR.match(str(h))])
        _actualizar_fichas(con, escena, c)
        g.escenas_hechas.append(escena["id"])
    return g


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
