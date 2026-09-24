"""La novela regalo en la web (`SPEC-33`): lo que se ensena, resuelto aqui y no en la
interfaz (`CLAUDE.md`: la interfaz muestra estado, no lo calcula)."""

from app.commons import config
from app.features.regalo import repository as repo

POR_QUE_ES_SUELO = ("lo gastado antes de la migracion 18 no tiene coste guardado en la base, "
                    "y una delegacion sin coste medido no suma")


def coste(usd, delegaciones, sin_coste, generacion):
    return {"generacion": generacion, "usd": usd, "delegaciones": delegaciones,
            "sin_coste": sin_coste, "es_suelo": sin_coste > 0}


def estanteria(con):
    """`RF-01`, `RF-02`: el estado de cada obra es su ultima fase, o ninguna."""
    obras = repo.obras_de_la_estanteria(con)
    for o in obras:
        o["fase"] = repo.ultima_fase(con, o["id"])
    return {"obras": obras}


def confirmacion(con, techo):
    """`RF-12`, `RF-19`: lo gastado frente al techo, la ultima generacion y la referencia."""
    usd, n, nulos = repo.gasto_de(con)
    ultima = repo.ultima_generacion(con)
    return {
        "gastado": {"usd": usd, "delegaciones": n, "sin_coste": nulos, "es_suelo": True,
                    "por_que_es_suelo": POR_QUE_ES_SUELO},
        "techo_usd": techo,
        "alcanzado": usd is not None and usd >= techo,
        "ultima": None if ultima is None else coste(*repo.gasto_de(con, generacion=ultima),
                                                     ultima),
        "referencia": config.REFERENCIA_NOVELA_DE_EJEMPLO,
    }


def generacion(con, obra, umbral):
    """`RF-14`..`RF-17`, `RF-20`. `None` si la obra no existe."""
    if not repo.existe_la_obra(con, obra):
        return None
    total = repo.numero_de_capitulos(con, obra)
    fases = repo.ultima_fase_por_capitulo(con, obra)
    capitulos = []
    for numero in range(1, total + 1):
        f = fases.get(numero, {})
        id_capitulo = repo.capitulo_vigente(con, obra, numero)
        notas = repo.notas_aceptadas(con, obra, id_capitulo) if id_capitulo else []
        capitulos.append({
            "numero": numero, "fase": f.get("fase"), "motivo": f.get("motivo"),
            "desde": f.get("desde"),
            "notas": [dict(n, instruccion=n["instruccion"] or None,
                           bajo_el_umbral=n["nota"] < umbral) for n in notas]})
    ultima = repo.ultima_generacion(con, obra)
    return {"obra": obra, "total_de_capitulos": total, "capitulos": capitulos,
            "coste": None if ultima is None
            else coste(*repo.gasto_de(con, obra, ultima), ultima)}
