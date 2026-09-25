"""La puerta de publicacion, compuesta (`SPEC-30` v4, `PLAN-30` E8).

`auditoria/publicacion.decidir` decide sobre datos ya resueltos; aqui se resuelven,
porque cruzan features —escaleta, cronologia, politica, auditoria— y componer es solo
de `orquestacion/` (`A-02`).

UNA RONDA
---------
1. `novela.cerrar` vuelve a comprobar el nivel obra: `INV-24`, `INV-25` e `INV-27`.
2. Los capitulos rendidos se leen del estado de sus escenas (`INV-29`), que desde
   `SPEC-30` `RF-11` sobrevive a la consolidacion.
3. `INV-21` se vuelve a mirar sobre el texto elegido de cada capitulo.
4. Lean se ejecuta **siempre**, aunque otra condicion ya haya fallado: `RF-04`
   informa de todas. Un Lean con violaciones deja un hallazgo `INV-28`.
5. `decidir`, y el veredicto se guarda con su numero de ronda.

LO QUE LA RONDA NUEVA YA NO ENCUENTRA
-------------------------------------
Los hallazgos no se cerraban nunca (hallazgo 2 del plan), y sin cerrarlos la puerta
no se abriria jamas despues de un reintento. Pero solo se cierra lo que **se volvio a
comprobar**: si `INV-24` falla, `cerrar` no juzga la obra entera y un `INV-27`
anterior no se ha vuelto a mirar, asi que sigue abierto. Y lo que sigue fallando se
queda con su hallazgo de antes, sin abrir otro igual: ni se marca `resuelto` lo que
no se arreglo, ni se duplica.
"""

from dataclasses import dataclass

from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import EstadoDeHallazgo as EH
from app.commons.dominio.enumeraciones import Severidad as S
from app.commons.invariantes.registro import TODAS
from app.commons.politica.vetadas import coincidencias
from app.features.auditoria import publicacion as puerta
from app.features.auditoria import repository as veredictos
from app.features.cronologia import repository as cronologia
from app.features.escaleta import repository as escaleta
from app.features.orquestacion import novela
from app.features.orquestacion.obra import _texto_elegido

NIVEL_OBRA = ("INV-24", "INV-25", "INV-27", "INV-28")


@dataclass(frozen=True)
class Evaluacion:
    decision: puerta.Decision
    ronda: int
    implicados: puerta.Implicados
    lean: puerta.ResultadoLean
    cierre: dict | None = None


def _abiertos_de_obra(con, escenas):
    capitulo = {e["id"]: e.get("capitulo") for e in escenas}
    return [dict(h, capitulo=capitulo[e["id"]]) for e in escenas
            for h in escaleta.hallazgos_abiertos(con, e["id"])]


def _conciliar(con, antes, despues, comprobadas, ronda):
    """Lo que la ronda nueva no encuentra se cierra; lo que sigue, conserva su hallazgo."""
    clave = lambda h: (h["invariante"], h["descripcion"])
    viejos = {clave(h): h for h in antes if h["invariante"] in comprobadas}
    ids_antes = {h["id"] for h in antes}
    nuevos = [h for h in despues if h["invariante"] in NIVEL_OBRA and h["id"] not in ids_antes]
    siguen = set()
    for h in nuevos:
        if clave(h) in viejos:
            escaleta.borrar_hallazgo_repetido(con, h["id"])
            siguen.add(clave(h))
    for k, h in viejos.items():
        if k not in siguen:
            escaleta.cerrar_hallazgo(con, h["id"], EH.RESUELTO,
                                     "la ronda {0} de la puerta ya no lo encuentra".format(ronda))


def evaluar(con, obra, ficha, lean, juez_de_obra, vetadas=(), umbral_nombre=None,
            longitud_frase=None, version=None) -> Evaluacion:
    """Una ronda de la puerta sobre la version `version` (sin ella, la vigente). Las
    rondas se cuentan **por version** (`PLAN-23` `F-122`, TLC `CE-15`)."""
    veredictos.asegurar_tablas(con)
    version = _numero(con, obra, version)
    ronda = veredictos.rondas(con, obra, version) + 1
    # `PLAN-23` A6: las escenas de la version que se evalua.
    escenas = _de_la_version(con, obra, version)
    antes = [h for h in _abiertos_de_obra(con, escenas) if h["invariante"] in NIVEL_OBRA]

    cierre = novela.cerrar(con, obra, ficha, juez_de_obra, umbral_nombre, longitud_frase,
                           version=version)
    comprobadas = {"INV-24", "INV-25", "INV-28"}
    if cierre["estado"] != "novela_incompleta":
        comprobadas.add("INV-27")

    resultado = lean.verificar(con, obra, version=version)
    if resultado.codigo == 1:
        escaleta.guardar_hallazgo(
            con, invariante="INV-28", verificador="lean", escena=escenas[-1]["id"],
            severidad=TODAS["INV-28"].severidad, estado=EH.ABIERTO.value,
            descripcion="; ".join("{0} {1}: {2}".format(
                v["invariante"], ",".join(v.get("eventos", [])), v.get("detalle", ""))
                for v in resultado.violaciones) or "violaciones sin detalle")

    despues = _abiertos_de_obra(con, escenas)
    _conciliar(con, antes, despues, comprobadas, ronda)
    hallazgos = _abiertos_de_obra(con, escenas)

    for e in escenas:
        for c in coincidencias(_texto_elegido(con, e) or "", list(vetadas)):
            hallazgos.append({"invariante": "INV-21", "severidad": S.BLOQUEANTE,
                              "estado": EH.ABIERTO, "capitulo": e.get("capitulo"),
                              "descripcion": "vetada en el texto elegido: {0}".format(c)})

    rendidos = sorted({e.get("capitulo") for e in escenas
                       if e["estado"] == EE.ACEPTADA_POR_RENDICION.value})
    decision = puerta.decidir(rendidos, hallazgos, resultado)
    implicados = puerta.capitulos_implicados(
        resultado.violaciones, {ev["id"]: ev["capitulo"]
                                for ev in cronologia.eventos_de(con, obra)},
        [h for h in hallazgos if h["invariante"] == "INV-27"])
    veredictos.guardar(con, obra, decision, resultado.codigo, version)
    return Evaluacion(decision, ronda, implicados, resultado, cierre)


PROMPT_FEEDBACK_LEAN = """Eres el editor de una novela personalizada. La verificacion formal de
la cronologia (Lean) ha encontrado incoherencias temporales. No reescribes nada: lo que
Lean mira lo fija el plan antes de escribir, y la generacion se va a detener. Explica en
una o dos frases que falla en el plan, para el informe.

VIOLACIONES (invariante, eventos implicados, detalle)
{violaciones}

CAPITULOS IMPLICADOS
{capitulos}

Devuelve un unico objeto JSON: "diagnostico": una o dos frases.
"""

PROMPT_INSTRUCCIONES = """Eres el editor de una novela personalizada. El juicio de la obra
entera ha encontrado problemas. No reescribes: das una instruccion concreta al escritor
por cada capitulo que haya que tocar, y solo de los capitulos implicados.

PROBLEMAS DE OBRA
{problemas}

CAPITULOS IMPLICADOS
{capitulos}

RESUMENES DE LA NOVELA (no el texto entero)
{resumenes}

Devuelve un unico objeto JSON: "instrucciones": lista de {{"capitulo", "instruccion"}}.
"""


@dataclass
class Publicacion:
    publicada: bool
    rondas: int
    parada: dict | None = None
    ignoradas: list = None
    evaluaciones: list = None


def _lista(filas):
    return "\n".join("- " + f for f in filas) or "(ninguno)"


def publicar(con, obra, ficha, lean, juez_de_obra, editor, reescribir,
             tope=None, vetadas=(), umbral_nombre=None, longitud_frase=None,
             version=None) -> Publicacion:
    """El bucle de la puerta (`SPEC-30` v4 `RF-04`, `RF-06`, `RF-07`).

    - Si se abre, la version se publica.
    - **Si Lean falla, el fallo vuelve al Editor como feedback y la generacion se
      detiene sin reescribir** (`RF-06`, `C-2`): lo que Lean mira lo fija el plan.
    - Si queda un `INV-27`, el Editor da instrucciones para los capitulos implicados,
      que se reescriben a delta fijo (`RF-10`), y se vuelve a evaluar.
    - Si falla algo que no se arregla reescribiendo, o se agota el tope, se detiene.

    **El tope se lee de la base** (`veredicto_de_publicacion`), asi que relanzar no
    lo reinicia: la leccion de `CE-4`. Cada vuelta guarda una ronda, asi que el bucle
    termina siempre, publicando o detenido.
    """
    from app.commons import config
    from app.features.consolidacion import memoria

    tope = config.TOPE_REINTENTOS_DE_PUBLICACION if tope is None else tope
    # `PLAN-23` `F-122`: el tope es de la version, no de la obra.
    version = _numero(con, obra, version)
    ignoradas, evaluaciones = [], []
    while True:
        previas = veredictos.rondas(con, obra, version)
        if previas > tope:
            return Publicacion(False, previas, {"motivo": "tope", "rondas": previas},
                               ignoradas, evaluaciones)
        e = evaluar(con, obra, ficha, lean, juez_de_obra, vetadas, umbral_nombre,
                    longitud_frase, version=version)
        evaluaciones.append(e)
        if e.decision.publica:
            return Publicacion(True, e.ronda, None, ignoradas, evaluaciones)
        condiciones = [c.__dict__ for c in e.decision.condiciones]
        if any(c.invariante == "INV-28" for c in e.decision.condiciones):
            bruto = editor.llamar(PROMPT_FEEDBACK_LEAN.format(
                violaciones=_lista("{0} {1}: {2}".format(
                    v["invariante"], ",".join(v.get("eventos", [])), v.get("detalle", ""))
                    for v in e.lean.violaciones) if e.lean.violaciones
                    else "- " + (e.lean.detalle or "sin detalle"),
                capitulos=_lista("{0}: {1}".format(c, "; ".join(m))
                                 for c, m in e.implicados.por_capitulo.items())))
            diagnostico = bruto.get("diagnostico") if isinstance(bruto, dict) else None
            return Publicacion(False, e.ronda, {
                "motivo": "lean", "condiciones": condiciones,
                "diagnostico": diagnostico or "el editor no devolvio un diagnostico legible",
                "sin_capitulo": e.implicados.sin_capitulo}, ignoradas, evaluaciones)
        if any(not c.reintentable for c in e.decision.condiciones):
            return Publicacion(False, e.ronda, {"motivo": "no_reintentable",
                                                "condiciones": condiciones},
                               ignoradas, evaluaciones)
        if e.ronda > tope:
            return Publicacion(False, e.ronda, {"motivo": "tope", "rondas": e.ronda,
                                                "condiciones": condiciones},
                               ignoradas, evaluaciones)
        implicados = e.implicados.por_capitulo
        bruto = editor.llamar(PROMPT_INSTRUCCIONES.format(
            problemas=_lista(c["detalle"] for c in condiciones),
            capitulos=_lista("{0}: {1}".format(c, "; ".join(m)) for c, m in implicados.items()),
            resumenes=_lista("{0}: {1}".format(r["escena"], r["texto"])
                             for r in memoria.resumenes_hasta(
                                 con, 10 ** 9, obra=obra, escenas=[
                                     e["id"] for e in _de_la_version(con, obra, version)]))))
        instrucciones = (bruto.get("instrucciones") if isinstance(bruto, dict) else None) or []
        for i in instrucciones:
            if not isinstance(i, dict):
                continue
            capitulo, texto = i.get("capitulo"), i.get("instruccion")
            if capitulo not in implicados or not texto:
                ignoradas.append((capitulo, texto))
                continue
            for escena in escaleta.escenas_de_capitulo(con, capitulo, obra):
                reescribir(con, escena["id"], [texto])


def _numero(con, obra, version):
    """La version que pasa por la puerta: la dada o, si no, la vigente. Una obra sin
    versiones (dada de alta antes de `PLAN-23`) cuenta como la 1."""
    from app.features.brief import repository as brief
    if version is not None:
        return version
    vigente = brief.version_vigente(con, obra)
    return vigente if vigente is not None else 1


def _de_la_version(con, obra, version=None):
    from app.features.orquestacion import regeneracion
    return regeneracion.escenas_de_version(con, obra, version)
