"""El bucle de generacion de una escena, de principio a fin.

VIVE EN `orquestacion/` Y NO EN `generacion/`, Y NO POR GUSTO
--------------------------------------------------------------
Compone `contexto/`, `escaleta/`, `generacion/` y `verificacion/`, y `A-02`
dice que una feature **nunca** importa de otra salvo `orquestacion/`, que es la
unica autorizada a componer. Se escribio primero en `generacion/agente.py` y lo
cazo la prueba de `A-02` del alta de obra, que recorre `features/` buscando
importaciones cruzadas: el comprobador mas barato del proyecto encontrando la
primera violacion real de una decision de arquitectura.

Es tambien la unica pieza que compone otras, y por eso se prueba entera contra
un doble antes de que exista un cliente real: **un bucle roto descubierto
pagandolo es la forma mas cara de descubrirlo.**

EL ORDEN DE LOS PASOS, Y POR QUE CADA UNO VA DONDE VA
------------------------------------------------------
    1. Ensamblar el contexto dentro del presupuesto. Si no cabe tras agotar
       las formas reducidas y eliminar los tres primeros bloques, `RF-26`:
       **falla en vez de generar**. No se genera con un contexto mutilado.
    2. Comprobar el techo sobre lo que se manda y delegar. **No se reserva**:
       `SPEC-14` C-1 retiro la reserva, porque el harness no administra la
       ventana del subagente.
    3. Leer el contrato. Texto y delta en la misma respuesta. Lo que falle aqui
       es fallo **de contrato**, no hallazgo: no produce `Hallazgo`, no pasa por
       las puertas, y por `O-3` **no se reintenta**.
    4. Guardar el borrador. La escena pasa a `generada`.
    5. Pasar las puertas deterministas. Lo que salga son `Hallazgo`, con su
       invariante y su verificador.

QUE NO HACE ESTE MODULO
-----------------------
No decide que pasa con un hallazgo. Que una `bloqueante` detenga la escena lo
decide `commons/invariantes/severidad.py`, una vez (`D-4`). Aqui solo se
produce el material.

Y no relanza nada por su cuenta: el reintento de un fallo de transporte lo
decide quien llama, con el tope de `commons/config.py`.
"""

import hashlib
import json
from dataclasses import dataclass, field

from app.commons.modelo import presupuesto, traza as modulo_traza
from app.features.contexto import ensamblado, repository as lecturas_repo
from app.commons.modelo.doble import FalloDeTransporte
from app.features.contexto import recorte
from app.features.escaleta import repository as repo
from app.features.generacion import contrato, prompt
from app.features.verificacion import puertas


@dataclass
class Resultado:
    medidas: dict | None = field(default=None, init=False)
    leida_delta: dict | None = field(default=None, init=False)
    escena: str = ""
    version: int | None = None
    hallazgos: list = field(default_factory=list)
    traza: object = None
    fallo: str | None = None


def _prompt(escena, contexto, mundo=None, problemas=None, hechos=None,
            instrucciones=None):
    """Usa la plantilla real, con los identificadores disponibles dentro.

    Sin ellos el modelo no puede citarlos y se le esta pidiendo lo imposible:
    es la mitad del arreglo de `F-21`. La otra la hace el contrato, porque un
    prompt bien construido no garantiza una respuesta bien formada.
    """
    mundo = mundo or {}
    return prompt.construir(
        parametros={"escena": escena["id"],
                    "longitud_objetivo": escena.get("longitud_objetivo"),
                    # `SPEC-18` C-2: el POV es del plan, no del modelo.
                    "pov": escena.get("pov")},
        estado={"contexto": sorted(contexto.items())},
        objetivo=json.dumps(escena.get("cambio_de_valor"), sort_keys=True),
        problemas=problemas,
        personajes=sorted(mundo.get("entidades_vivas") or {}),
        # Los hechos que el plan declaro, **no** los del registro de
        # conocimiento. Derivarlos del registro creo el punto muerto de `F-29`:
        # la lista salia de las revelaciones y las revelaciones necesitaban la
        # lista, asi que nunca habia ninguna.
        hechos=sorted(hechos or []),
        instrucciones=instrucciones,
        # `SPEC-19` P-5: lo que el plan prometio que esta escena establece.
        # Sale de los `beats`, que desde `SPEC-19` pueden llevar referencias
        # ademas de prosa.
        establece=_prometidos(escena),
    )


def _prometidos(escena):
    """Los hechos que los `beats` de esta escena prometen establecer.

    Los `beats` siguen siendo prosa **y ademas** pueden llevar referencias, asi
    que una escaleta antigua trae cadenas donde esto espera diccionarios y hay
    que tolerarlo sin romper.
    """
    salida = set()
    for b in escena.get("beats") or []:
        if isinstance(b, dict):
            salida.update(b.get("establece") or [])
    return sorted(salida)


def generar(con, escena_id, contexto, modelo, techo=100_000, estado_del_techo=None,
            mundo=None, trabajo="sin-trabajo", hechos=None, problemas=None,
            instrucciones=None):
    escena = repo.escena(con, escena_id)
    t = modulo_traza.nueva(agente="escritor", escena=escena_id, trabajo=trabajo,
                           modelo=modelo.nombre)
    estado_del_techo = estado_del_techo if estado_del_techo is not None else {}

    # 1. Ensamblar. `RF-26` falla antes que generar con el contexto mutilado.
    try:
        plan = recorte.planificar(contexto, techo=techo)
    except recorte.NoCabe as e:
        for paso in e.plan:
            modulo_traza.registrar_recorte(t, paso.bloque, paso.clase.value)
        return Resultado(escena=escena_id, traza=t, fallo="no_cabe")
    for paso in plan:
        modulo_traza.registrar_recorte(t, paso.bloque, paso.clase.value)

    t.tokens_para_recortar = sum(contexto.values())
    texto_prompt = _prompt(escena, contexto, mundo, problemas=problemas,
                           hechos=hechos, instrucciones=instrucciones)
    modulo_traza.registrar_entrada(t, prompt_hash=hashlib.sha256(
        texto_prompt.encode("utf-8")).hexdigest()[:12])
    # Lo que esta llamada tuvo delante del canon, registrado **antes** de
    # delegar: una llamada que falla tambien leyo algo, y es la que hay que
    # diagnosticar. Va atado al `prompt_hash`, que es lo que comparte con el
    # `Borrador` que salga de aqui (`RF-11`).
    lecturas_repo.guardar_lecturas(
        con, escena_id, ensamblado.lecturas({"hechos": hechos, "mundo": mundo}),
        prompt_hash=t.prompt_hash)

    # 2. Comprobar el techo y delegar.
    #
    # Ya no se reserva: `SPEC-14` C-1 retiro la reserva porque el harness no
    # administra la ventana del subagente. Lo que queda es el limite sobre lo
    # que **mandamos**, que sigue siendo real y sigue haciendo fallar antes de
    # generar con un contexto mutilado.
    if t.tokens_para_recortar > techo:
        return Resultado(escena=escena_id, traza=t, fallo="no_cabe")
    try:
        respuesta = modelo.llamar(texto_prompt)
    except FalloDeTransporte:
        modulo_traza.registrar_fallo(t, clase="transporte", salida=None)
        return Resultado(escena=escena_id, traza=t, fallo="transporte")

    # 3. El contrato. Lo que falle aqui no es un hallazgo.
    try:
        leida = contrato.leer(respuesta)
    except contrato.FalloDeContrato as e:
        modulo_traza.registrar_fallo(t, clase="contrato", salida=repr(respuesta))
        return Resultado(escena=escena_id, traza=t, fallo="contrato")
    modulo_traza.registrar_respuesta(t, respuesta)
    # `SPEC-14` C-3 supuso que los tokens los reportaria a mano la sesion y
    # serian un suelo. El transporte los devuelve medidos, asi que se guardan.
    medidas = respuesta.get("medidas")
    if medidas:
        t.tokens_estimados = ((medidas.get("tokens_entrada") or 0)
                              + (medidas.get("tokens_salida") or 0))
        # Sin esto la traza del Escritor sale "sin registrar" y `VER-62` no
        # puede comprobar la estabilidad del conjunto justo en el agente que
        # mas delegaciones hace.
        t.modelos = medidas.get("modelos") or []
        t.medidas = medidas

    # 4. Guardar el borrador.
    version = repo.guardar_borrador(con, escena_id, texto=leida.texto,
                                    modelo=modelo.nombre, prompt_hash=t.prompt_hash)

    # 5. Las puertas.
    vista = dict(escena)
    vista["palabras"] = len(leida.texto.split())
    # `SPEC-18` C-1: lo declara el agente, y por eso `INV-04` puede compararlo
    # con el `pov` del plan. Derivarlo del texto seria un eco de `VER-48`.
    vista["pov_usado"] = leida.pov_usado
    vista["longitud_objetivo"] = tuple(escena["longitud_objetivo"] or ()) or None
    vista["personajes_presentes"] = escena.get("personajes_presentes") or []
    hallazgos = puertas.verificar(vista, leida.delta, mundo or _mundo_vacio())
    for h in hallazgos:
        repo.guardar_hallazgo(con, invariante=h.invariante, verificador=h.verificador,
                              escena=h.escena, severidad=h.severidad, estado=h.estado,
                              descripcion=h.descripcion)
    res = Resultado(escena=escena_id, version=version, hallazgos=hallazgos, traza=t)
    res.medidas = respuesta.get("medidas")
    res.leida_delta = leida.delta
    return res


def _mundo_vacio():
    return {"entidades_vivas": {}, "ubicaciones": {}, "accesos": {}, "conocimiento": {}}
