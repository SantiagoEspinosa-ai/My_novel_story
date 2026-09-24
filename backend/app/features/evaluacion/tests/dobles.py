"""Dobles de la evaluacion: reproducen lo que un brief declara que deberia pasar.

Tienen la forma de lo real (`llamar(prompt) -> dict`), y lo que devuelven sale del propio
brief —`ficha_esperada`, `hechos_esperados`—, no de la prueba: si el brief cambia, el
doble cambia con el.
"""


class EntrevistadorDelGuion:
    """Devuelve, turno a turno, la `ficha_esperada` de cada respuesta del guion."""

    nombre = "doble-entrevistador"

    def __init__(self, guion):
        self.fichas = [t.ficha_esperada.model_dump(mode="json")
                       for t in guion.turnos if t.respuesta is not None]
        self.i = 0

    def llamar(self, prompt):
        f = self.fichas[min(self.i, len(self.fichas) - 1)]
        self.i += 1
        return {"ficha": f, "pregunta": "pregunta {0}".format(self.i)}


class ExtractorDelGuion:
    """Devuelve los `hechos_esperados` de cada texto libre del guion, en orden."""

    nombre = "doble-extractor"

    def __init__(self, guion):
        self.hechos = [list(t.hechos_esperados) for t in guion.turnos if t.texto_libre]
        self.i = 0

    def llamar(self, prompt):
        h = self.hechos[min(self.i, len(self.hechos) - 1)] if self.hechos else []
        self.i += 1
        return {"hechos": h}


# --- Los agentes de una novela entera, a partir de su ficha ---------------------------

CRITERIOS = ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo",
             "personalizacion")


class Captura:
    """Un agente doble que guarda cada prompt y, con `coste`, devuelve las medidas del
    sobre como la `SesionDelegada` real."""

    def __init__(self, respuesta, prompts=None, coste=None):
        self.r, self.prompts, self.coste = respuesta, prompts if prompts is not None else [], coste
        self.nombre, self.reglas, self.entorno, self.herramientas = "doble", None, {}, None

    def llamar(self, prompt):
        self.prompts.append(prompt)
        r = self.r(prompt) if callable(self.r) else self.r
        if self.coste is not None:
            r = dict(r, medidas={"coste_usd": self.coste, "tokens_entrada": 10,
                                 "tokens_salida": 5, "modelos": ["m-1"], "duracion_ms": 7})
        return r


def plan_de(ficha):
    """Un plan de diez capitulos que cubre los imprescindibles de la ficha, con los
    nombres de la ficha: un plan ajeno no pasaria la cobertura (`SPEC-26` `RF-06`)."""
    import re
    d = ficha.destinatario
    pila = re.sub(r"\W", "", d.nombre.split()[0].lower())
    personajes = [{"id": "per-" + pila, "nombre": d.nombre, "empieza_en": "lug-casa",
                   "fecha_de_nacimiento": "1980-01-01"}]
    for e in d.elementos:
        if e.nombre:
            personajes.append({"id": "per-" + re.sub(r"\W", "", e.nombre.split()[0].lower()),
                               "nombre": e.nombre, "empieza_en": "lug-casa"})
    return {
        "mundo": {"lugares": [{"id": "lug-casa", "nombre": "Casa", "accesos": []}],
                  "personajes": personajes},
        "capitulos": [{"id": "cap-{0:02d}".format(n), "titulo": "Capitulo {0}".format(n),
                       "escenas": [{"eje": "vinculo", "signo": "positivo", "lugar": "lug-casa",
                                    "pov": "per-" + pila,
                                    "sinopsis": "{0} sigue su dia.".format(d.nombre.split()[0]),
                                    "t_fabula": "2026-06-{0:02d}".format(n)}]}
                      for n in range(1, 11)],
        "imprescindibles": [{"elemento": e.descripcion, "capitulo": "cap-01",
                             "palabras_clave": [e.nombre or e.descripcion.split()[-1]]}
                            for e in d.elementos if e.imprescindible],
    }


def agentes_para(ficha, prompts=None, coste=None):
    """Planificador, Revisor, Escritor, Editor y Resumidor de una novela que pasa todas
    sus puertas: el Escritor copia el POV del prompt y escribe las palabras clave, y el
    Editor contesta a la rubrica y al juicio de obra por separado."""
    import re
    from app.commons.modelo.doble import DELTA_OK
    from app.commons.configuracion.esquemas import rango_de_palabras
    prompts = prompts if prompts is not None else []
    plan = plan_de(ficha)
    pila = ficha.destinatario.nombre.split()[0]
    pov = plan["capitulos"][0]["escenas"][0]["pov"]
    claves = [i["palabras_clave"][0] for i in plan["imprescindibles"]]
    minimo, maximo = rango_de_palabras(ficha.extension)
    largo = (minimo + maximo) // 2
    texto = " ".join(["palabra"] * (largo - len(claves) - 1) + [pila] + claves)

    def escritor(prompt):
        m = re.search(r"[\w-]*" + re.escape(pov), prompt)
        return {"texto": texto, "pov_usado": m.group(0) if m else pov, "delta": DELTA_OK}

    def editor(prompt):
        if "Juzga una novela para regalar entera" in prompt:
            return {"arco_cerrado": True, "final_abrupto": False, "justificacion": "bien"}
        return {"valoraciones": [{"criterio": c, "nota": 4, "justificacion": "bien"}
                                 for c in CRITERIOS]}
    return {
        "planificador": Captura({"titulo": ficha.titulo, "premisa": ficha.premisa,
                                 "plan": plan}, prompts, coste),
        "revisor": Captura({"aprobado": True, "objeciones": []}, prompts, coste),
        "escritor": Captura(escritor, prompts, coste),
        "editor": Captura(editor, prompts, coste),
        "resumidor": Captura({"texto": "{0} avanza.".format(pila), "hechos_clave": []},
                             prompts, coste),
    }


class LeanFijo:
    def __init__(self, codigo=0):
        self.codigo, self.llamadas = codigo, 0

    def verificar(self, con, obra):
        from app.features.auditoria.publicacion import ResultadoLean
        self.llamadas += 1
        return ResultadoLean(self.codigo)
