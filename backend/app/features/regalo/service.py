"""La novela regalo en la web (`SPEC-33`): lo que se ensena, resuelto aqui y no en la
interfaz (`CLAUDE.md`: la interfaz muestra estado, no lo calcula)."""

from app.features.regalo import repository as repo


def coste(usd, delegaciones, sin_coste, generacion):
    return {"generacion": generacion, "usd": usd, "delegaciones": delegaciones,
            "sin_coste": sin_coste, "es_suelo": sin_coste > 0}


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
