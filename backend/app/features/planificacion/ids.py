"""`F-64`: los identificadores de un plan son de su obra.

LO QUE PASABA
-------------
El Planificador pone los mismos identificadores en todas las novelas —`cap-01`,
`per-irene`, `lug-casa`—, y `capitulo`, `escena`, `entidad` y `lugar` tienen clave
**global**. Con dos novelas en la misma base, la segunda **no fallaba al empezar:
pisaba**. `capitulo`, `entidad`, `lugar` y `conocimiento` se escriben con
`INSERT OR REPLACE`, asi que se quedaba los capitulos, los personajes y los lugares de
la primera, y solo al insertar la escena reventaba. La primera novela quedaba corrupta
y nadie lo decia.

POR QUE AQUI Y NO EN LAS TABLAS
-------------------------------
Cambiar la clave de todas esas tablas a `(obra, id)` toca mas de treinta consultas y
deja `escena.id` global igualmente, porque la citan media docena de tablas por su id a
secas. Acotar los identificadores **en el unico punto por el que entran**, al leer el
plan, hace que todo lo de abajo —montar, escribir, el contexto del Escritor, la
cronologia, Lean— use los mismos sin traducir nada.

LO QUE CUESTA
-------------
El Escritor ve identificadores mas largos (`obra-3f2a9c1b7e-per-irene`) y tiene que
copiarlos tal cual en su delta. Si eso le cuesta, lo dira la siguiente ejecucion real:
un identificador mal copiado no pasa en silencio, lo rechaza el contrato.

LOS HECHOS NO SE TOCAN
----------------------
`hecho_canonico` ya tiene clave `(obra, id)` desde `F-39`.
"""

from app.commons.configuracion.esquemas import PlanDeLaObra


def acotar_a_la_obra(plan: PlanDeLaObra, obra: str) -> PlanDeLaObra:
    prefijo = "{0}-".format(obra)
    return _cada_id(plan, lambda i: i if i.startswith(prefijo) else prefijo + i)


def reacotar(plan: PlanDeLaObra, de_obra: str, a_obra: str) -> PlanDeLaObra:
    """El plan de `de_obra` con los identificadores de `a_obra`: para reutilizar un plan
    aprobado en otra ejecucion (la pasada «despues» del tuning parte del plan de la
    «antes»). Recorre los mismos campos que `acotar_a_la_obra`: hay un solo recorrido."""
    viejo, nuevo = "{0}-".format(de_obra), "{0}-".format(a_obra)
    return _cada_id(plan, lambda i: nuevo + (i[len(viejo):] if i.startswith(viejo) else i))


def _cada_id(plan: PlanDeLaObra, a) -> PlanDeLaObra:
    """Aplica `a` a cada identificador del plan que es de la obra. Los hechos no, que ya
    tienen clave `(obra, id)` (`F-39`)."""
    d = plan.model_dump(mode="json")
    mundo = d["mundo"]
    for l in mundo["lugares"]:
        l["id"], l["accesos"] = a(l["id"]), [a(x) for x in l["accesos"]]
    for p in mundo["personajes"]:
        p["id"], p["empieza_en"] = a(p["id"]), a(p["empieza_en"])
    for k in mundo.get("conocimiento_inicial", []):
        k["sujeto"] = a(k["sujeto"])
    for c in d["capitulos"]:
        c["id"] = a(c["id"])
        for e in c["escenas"]:
            e["lugar"], e["pov"] = a(e["lugar"]), a(e["pov"])
            e["personajes_presentes"] = [a(x) for x in e.get("personajes_presentes", [])]
    for i in d.get("imprescindibles", []):
        i["capitulo"] = a(i["capitulo"])
    for x in d.get("exclusiones_previstas", []):
        x["personaje"], x["capitulo"] = a(x["personaje"]), a(x["capitulo"])
    return PlanDeLaObra.model_validate(d)
