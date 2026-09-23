"""El ciclo completo de una escena: generar, juzgar, consolidar y resumir.

Es la pieza que `PLAN-01` no tenia: el bucle de `bucle.py` genera y verifica,
y aqui se le enganchan el Juez, el Consolidador y el Resumidor.

TRES AGENTES Y UNO QUE NO LO ES
--------------------------------
    Escritor      llama al modelo. Escribe la escena y devuelve el delta.
    Juez          llama al modelo. Puntua con la rubrica.
    Resumidor     llama al modelo. Condensa la escena consolidada.
    Consolidador  **no** llama al modelo: aplica el delta al estado. Por eso
                  no tiene definicion de agente y vive en su feature.

EL JUEZ SE LANZA AISLADO, Y NO POR `omitClaudeMd`
--------------------------------------------------
`SPEC-11` C-4 dice que el Juez no ve las reglas del proyecto: desde `SPEC-04`
es el **desempate** de `INV-03`, `INV-11` e `INV-14`, y un desempate que ve lo
mismo que la regla no desempata, confirma.

El mecanismo declarado era `omitClaudeMd: true`, y **se midio que se ignora en
silencio** (`F-20`). Lo que si aisla es el **directorio de trabajo**, porque
`claude` carga `CLAUDE.md` desde el arbol del `cwd`.

**Pero un directorio vacio de verdad tampoco sirve**, y eso costo una ejecucion
fallida: `.claude/agents/` tambien es del proyecto, asi que al mover el `cwd` el
agente desaparece con el —*"--agent 'juez' not found"*—. Los dos mecanismos
chocan: lo que esconde las reglas esconde tambien la definicion.

El aislamiento es entonces **un directorio que tiene el agente y nada mas**: se
copia alli `.claude/agents/juez.md` y no se copia nada de `CLAUDE.md`. Y sigue
haciendo falta que el agente no tenga herramientas de lectura: el directorio
solo no basta, uno con lectura puede ir a buscar el fichero.

EL ORDEN, Y POR QUE NO SE PUEDE CAMBIAR
----------------------------------------
Consolidar va **despues** de las puertas y **antes** de resumir. Antes de las
puertas seria meter en el canon algo que no ha pasado ninguna; despues de
resumir seria resumir una escena cuyo delta todavia no esta aplicado, y el
resumen describiria un mundo que no existe.
"""

import json
import os
import pathlib
import tempfile
from dataclasses import dataclass, field

from app.commons.invariantes import severidad
from app.commons.modelo import proveedor, traza as modulo_traza
from app.features.consolidacion import aplicar
from app.features.escaleta import repository as repo
from app.features.orquestacion import bucle
from app.commons.dominio.enumeraciones import EstadoDeHallazgo
from app.commons.dominio.modelos import Hallazgo
from app.commons import config
from app.commons.dominio.edicion import ValoracionesDelEditor
from app.commons.invariantes.registro import TODAS
from app.commons.politica.personalizacion import claves_ausentes, nombres_mal_escritos
from app.commons.politica.vetadas import coincidencias

RUBRICA = """Puntua esta escena de terror. Devuelve PASA o FALLO y los problemas
que encuentres, cada uno con su gravedad y su fragmento literal de evidencia.

Mira: si la escena mueve un valor dramatico, si la tension escala, si el punto
de vista se sostiene, y si la prosa evita la explicacion de lo que ya se ve.
"""


RUBRICA_DEL_EDITOR = """Juzga este capitulo de una novela para regalar con tu rubrica.
Una nota de 1 a 5 por criterio -continuidad, tono, arco,
coherencia_de_personajes, ritmo, personalizacion-, cada una con su justificacion
y, si es baja, una instruccion concreta para el escritor.
"""


@dataclass
class Ciclo:
    escena: str
    generacion: object = None
    veredicto: dict | None = None
    consolidada: bool = False
    resumen: dict | None = None
    fallo: str | None = None
    trazas: list = field(default_factory=list)
    vetadas_encontradas: list = field(default_factory=list)
    nombres_encontrados: list = field(default_factory=list)


def preparar_directorio_aislado(definicion, nombre="juez"):
    """Un directorio con el agente y **nada mas**. Devuelve su ruta.

    No se copia `CLAUDE.md` ni ningun documento del proyecto: esa ausencia es
    el aislamiento. Y se copia el agente porque sin el la delegacion falla con
    `--agent 'juez' not found`.
    """
    base = tempfile.mkdtemp(prefix="juez-aislado-")
    destino = pathlib.Path(base) / ".claude" / "agents"
    destino.mkdir(parents=True)
    (destino / (nombre + ".md")).write_text(
        pathlib.Path(definicion).read_text(encoding="utf-8"), encoding="utf-8")
    return base


def juez_aislado(modelo=None, definicion=None):
    """Directorio con el agente y sin las reglas, **y** sin herramientas."""
    # parents[4] es la raiz del repositorio: `.claude/` vive alli y no en
    # `backend/`, porque lo lee la herramienta y no el paquete.
    definicion = definicion or (pathlib.Path(__file__).resolve().parents[4]
                                / ".claude" / "agents" / "juez.md")
    return proveedor.SesionDelegada(
        modelo=modelo or os.environ.get(proveedor.VARIABLES["modelo_juez"]),
        agente="juez", cwd=preparar_directorio_aislado(definicion))


def editor_aislado(modelo=None, definicion=None):
    """El Editor, aislado como el Juez (`A-06`): un directorio con su agente y
    sin `CLAUDE.md`, y sin herramientas."""
    definicion = definicion or (pathlib.Path(__file__).resolve().parents[4]
                                / ".claude" / "agents" / "editor.md")
    return proveedor.SesionDelegada(
        modelo=modelo, agente="editor",
        cwd=preparar_directorio_aislado(definicion, nombre="editor"))


def _hallazgo_del_editor(con, escena_id, estado, descripcion):
    h = Hallazgo(invariante="INV-26", verificador="editor", escena=escena_id,
                 severidad=TODAS["INV-26"].severidad, estado=EstadoDeHallazgo(estado),
                 descripcion=descripcion)
    repo.guardar_hallazgo(con, invariante=h.invariante, verificador=h.verificador,
                          escena=h.escena, severidad=h.severidad, estado=h.estado,
                          descripcion=h.descripcion)
    return h


def _editar(con, c, editor, escena_id, texto, trabajo, umbral):
    """`INV-26`. Una nota bajo el umbral es un hallazgo `mayor` que entra en el
    siguiente intento con la instruccion del Editor. Una respuesta ilegible es
    `sin_veredicto`: se guarda, pero **no** entra en los hallazgos del intento,
    porque un juicio que no llego no es una violacion (`SPEC-18` C-3)."""
    bruto, _ = _delegar(editor, RUBRICA_DEL_EDITOR + "\n\nCAPITULO\n" + texto,
                        "editor", escena_id, trabajo, c.trazas)
    try:
        leidas = ValoracionesDelEditor.model_validate(bruto or {})
    except Exception as e:
        _hallazgo_del_editor(con, escena_id, "sin_veredicto",
                             "el Editor no devolvio una valoracion legible: {0}".format(
                                 str(e)[:300]))
        c.veredicto = {"veredicto": "SIN_VEREDICTO"}
        return
    c.veredicto = leidas.model_dump(mode="json")
    for v in leidas.valoraciones:
        if v.nota < umbral:
            c.generacion.hallazgos.append(_hallazgo_del_editor(
                con, escena_id, "abierto",
                "{0}: nota {1} (umbral {2}). {3} Instruccion: {4}".format(
                    v.criterio.value, v.nota, umbral, v.justificacion,
                    v.instruccion or "(ninguna)")))


def _delegar(modelo, prompt, agente, escena, trabajo, trazas):
    t = modulo_traza.nueva(agente=agente, escena=escena, trabajo=trabajo,
                           modelo=modelo.nombre)
    try:
        r = modelo.llamar(prompt)
    except proveedor.RespuestaIlegible:
        # No es un fallo de transporte: el verificador **no llego a emitir
        # juicio**. Se registra como tal y pesa lo maximo de su escala, porque
        # quien no se dejo auditar no gana por defecto.
        modulo_traza.registrar_fallo(t, clase="contrato", salida="ilegible")
        trazas.append(t)
        return None, t
    if r is None:
        # Una respuesta nula es lo mismo que una ilegible: **no hay juicio**.
        # El transporte puede devolverla si el JSON de la sesion trae `null`,
        # y sin esto reventaba con `AttributeError` en vez de registrarse.
        modulo_traza.registrar_fallo(t, clase="contrato", salida="nula")
        trazas.append(t)
        return None, t
    medidas = r.get("medidas") or {}
    t.modelos = medidas.get("modelos") or []
    t.medidas = medidas
    t.tokens_estimados = ((medidas.get("tokens_entrada") or 0)
                          + (medidas.get("tokens_salida") or 0))
    t.resultado = "ok"
    trazas.append(t)
    return r, t


def _acta_de(acta, texto, c):
    """Cierra el acta sobre el texto y el delta de esta escena.

    `aplicar.consolidar` solo sabe pasar la conexion, y el acta necesita ademas
    el texto -para calcular las menciones- y el delta -para `establece` y
    `depende`-. Aqui se atan, que es el unico sitio donde los tres estan a la
    vez, y lo que viaja hacia abajo es ya una funcion de un solo argumento.
    """
    if acta is None:
        return None
    return lambda conexion: acta(conexion, texto,
                                 (c.generacion.leida_delta or {}) if c.generacion else {})


def ejecutar(con, escena_id, contexto, escritor, juez, resumidor, mundo,
             techo=100_000, trabajo="ciclo", hechos=None, problemas=None,
             instrucciones=None, acta=None, vetadas=None, nombres=None,
             imprescindibles=None, es_editor=False, umbral=None):
    c = Ciclo(escena=escena_id)

    # 1. Generar y pasar las puertas deterministas.
    c.generacion = bucle.generar(con, escena_id, contexto, escritor, techo=techo,
                                 mundo=mundo, trabajo=trabajo, hechos=hechos,
                                 problemas=problemas,
                                 instrucciones=instrucciones, vetadas=vetadas,
                                 nombres=nombres, imprescindibles=imprescindibles)
    c.trazas.append(c.generacion.traza)
    if c.generacion.fallo:
        c.fallo = c.generacion.fallo
        return c

    texto = con.execute("SELECT texto FROM borrador WHERE escena=? AND version=?",
                        (escena_id, c.generacion.version)).fetchone()[0]

    # `INV-21` antes que el Juez: es una regla de codigo, no cuesta nada, y un
    # texto con una vetada no se va a aceptar diga lo que diga la rubrica. Pagar
    # la delegacion del Juez sobre el seria pagar por un veredicto que no cuenta.
    if vetadas:
        c.vetadas_encontradas = coincidencias(texto, vetadas)
        if c.vetadas_encontradas:
            c.fallo = "palabra_vetada"
            return c
    # `INV-22` (`SPEC-26` `RF-13`): igual que `INV-21`, antes del Juez y con el
    # fragmento exacto, porque es el mismo tipo de error.
    if nombres:
        c.nombres_encontrados = nombres_mal_escritos(texto, nombres)
        if c.nombres_encontrados:
            c.fallo = "nombre_mal_escrito"
            return c
    # `INV-23` (`RF-14`): `mayor`, asi que no para: entra en los hallazgos de
    # este intento, se guarda como los de la puerta y provoca otro intento.
    for elemento, clave in claves_ausentes(texto, imprescindibles or []):
        h = Hallazgo(invariante="INV-23", verificador="verificador_de_reglas",
                     escena=escena_id, severidad=TODAS["INV-23"].severidad,
                     estado=EstadoDeHallazgo.ABIERTO,
                     descripcion="falta «{0}»: el capitulo tiene que contar «{1}»".format(
                         clave, elemento))
        repo.guardar_hallazgo(con, invariante=h.invariante, verificador=h.verificador,
                              escena=h.escena, severidad=h.severidad, estado=h.estado,
                              descripcion=h.descripcion)
        c.generacion.hallazgos.append(h)

    # 2. El Juez, aislado.
    if es_editor:
        # `SPEC-26`: con un fallo determinista (`INV-23`) el intento ya se va a
        # repetir; pagar al Editor sobre el seria pagar un juicio que no cuenta.
        if not c.generacion.hallazgos:
            _editar(con, c, juez, escena_id, texto, trabajo,
                    config.UMBRAL_DEL_EDITOR if umbral is None else umbral)
    else:
        bruto, _ = _delegar(juez, RUBRICA + "\n\nESCENA\n" + texto, "juez",
                            escena_id, trabajo, c.trazas)
        c.veredicto = bruto if bruto else {"veredicto": "SIN_VEREDICTO"}
        if bruto is None:
            # `SPEC-10` C-2: la ausencia de juicio no es un pase.
            c.veredicto = {"veredicto": "SIN_VEREDICTO", "problemas": []}

    # 3. Consolidar: despues de las puertas, antes de resumir.
    # Quien decide es `severidad.py`, una vez (`D-4`), y desde `SPEC-18` C-3
    # mira el hallazgo entero y no solo su severidad: un `sin_veredicto` no
    # afirma que nada se haya roto, asi que no detiene la escena.
    bloqueantes = [h for h in c.generacion.hallazgos
                   if severidad.detiene_la_escena_por(h)]
    if bloqueantes:
        c.fallo = "bloqueante"
        return c

    # Un `mayor` o un `menor` abierto dejan la escena en `en_revision`, y
    # `Docs/architecture.md` solo consolida desde `aceptada` o desde
    # `aceptada_por_rendicion`. Consolidar aqui meteria en el canon el delta de
    # un intento que todavia puede descartarse **y el canon no se deshace**.
    # Se descubrio al conectar los reintentos: el segundo intento moria con
    # `YaConsolidada` porque el primero ya habia escrito.
    if c.generacion.hallazgos:
        return c
    return consolidar_y_resumir(c, con, escena_id, texto, resumidor, trabajo,
                                al_consolidar=_acta_de(acta, texto, c))


def consolidar_y_resumir(c, con, escena_id, texto, resumidor, trabajo="ciclo",
                         al_consolidar=None):
    """Aplica el delta y resume. Se llama cuando la escena **ya esta aceptada**:
    o porque salio limpia, o porque se rindio y se eligio su mejor intento.

    `al_consolidar` viaja hasta `aplicar.consolidar` sin abrirse: es lo que
    `orquestacion/obra.py` quiere escribir dentro de la misma transaccion que
    el delta (`SPEC-21` C-4). Este modulo no mira que hay dentro.
    """
    try:
        aplicar.consolidar(con, escena_id, c.generacion.leida_delta or {},
                           al_consolidar=al_consolidar)
        repo.marcar_consolidada(con, escena_id)
        c.consolidada = True
    except (aplicar.DeltaIncompatible, aplicar.YaConsolidada) as e:
        c.fallo = "delta:" + type(e).__name__
        return c

    bruto, _ = _delegar(resumidor, "Condensa esta escena.\n\nESCENA\n" + texto,
                        "resumidor", escena_id, trabajo, c.trazas)
    c.resumen = bruto
    return c


def texto_de(con, escena_id, version):
    return con.execute("SELECT texto FROM borrador WHERE escena=? AND version=?",
                       (escena_id, version)).fetchone()[0]


def guardar_trazas(con, c):
    """Escribe las trazas del ciclo, que hasta `F-49` morian con el proceso.

    Va aqui y no en `bucle.py` porque el ciclo es quien las tiene todas: la
    del Escritor, la del Juez y la del Resumidor. Guardarlas por separado
    dejaria fuera las de los agentes que `bucle.py` no ve.

    No revienta el ciclo si falla: perder una traza es malo y **perder la
    escena por no poder anotarla es peor**. Lo que no hace es callarse: el
    fallo sube como aviso en el resultado.
    """
    from app.features.observabilidad import repository as obs

    fallos = []
    for t in c.trazas:
        if t is None:
            continue
        try:
            obs.guardar_traza(con, t)
        except Exception as e:  # noqa: BLE001 - se reporta, no se traga
            fallos.append("{0}: {1}".format(getattr(t, "agente", "?"), e))
    return fallos


def coste_total(trazas):
    """Lo que costo el ciclo, sumando lo medido y **diciendo qué falta**."""
    medidos = [t for t in trazas if getattr(t, "tokens_estimados", None)]
    return {
        "delegaciones": len(trazas),
        "con_medida": len(medidos),
        "sin_medida": len(trazas) - len(medidos),
        "tokens": sum(t.tokens_estimados for t in medidos),
    }
