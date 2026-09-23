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

from app.commons.modelo import proveedor, traza as modulo_traza
from app.features.consolidacion import aplicar
from app.features.orquestacion import bucle

RUBRICA = """Puntua esta escena de terror. Devuelve PASA o FALLO y los problemas
que encuentres, cada uno con su gravedad y su fragmento literal de evidencia.

Mira: si la escena mueve un valor dramatico, si la tension escala, si el punto
de vista se sostiene, y si la prosa evita la explicacion de lo que ya se ve.
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
    medidas = r.get("medidas") or {}
    t.modelos = medidas.get("modelos") or []
    t.medidas = medidas
    t.tokens_estimados = ((medidas.get("tokens_entrada") or 0)
                          + (medidas.get("tokens_salida") or 0))
    t.resultado = "ok"
    trazas.append(t)
    return r, t


def ejecutar(con, escena_id, contexto, escritor, juez, resumidor, mundo,
             techo=100_000, trabajo="ciclo"):
    c = Ciclo(escena=escena_id)

    # 1. Generar y pasar las puertas deterministas.
    c.generacion = bucle.generar(con, escena_id, contexto, escritor, techo=techo,
                                 mundo=mundo, trabajo=trabajo)
    c.trazas.append(c.generacion.traza)
    if c.generacion.fallo:
        c.fallo = c.generacion.fallo
        return c

    texto = con.execute("SELECT texto FROM borrador WHERE escena=? AND version=?",
                        (escena_id, c.generacion.version)).fetchone()[0]

    # 2. El Juez, aislado.
    bruto, _ = _delegar(juez, RUBRICA + "\n\nESCENA\n" + texto, "juez",
                        escena_id, trabajo, c.trazas)
    c.veredicto = bruto if bruto else {"veredicto": "SIN_VEREDICTO"}
    if bruto is None:
        # `SPEC-10` C-2: la ausencia de juicio no es un pase.
        c.veredicto = {"veredicto": "SIN_VEREDICTO", "problemas": []}

    # 3. Consolidar: despues de las puertas, antes de resumir.
    bloqueantes = [h for h in c.generacion.hallazgos
                   if str(h.severidad) == "bloqueante"]
    if bloqueantes:
        c.fallo = "bloqueante"
        return c
    try:
        aplicar.consolidar(con, escena_id, c.generacion.leida_delta or {})
        c.consolidada = True
    except (aplicar.DeltaIncompatible, aplicar.YaConsolidada) as e:
        c.fallo = "delta:" + type(e).__name__
        return c

    # 4. Resumir la escena ya consolidada.
    bruto, _ = _delegar(resumidor, "Condensa esta escena.\n\nESCENA\n" + texto,
                        "resumidor", escena_id, trabajo, c.trazas)
    c.resumen = bruto
    return c


def coste_total(trazas):
    """Lo que costo el ciclo, sumando lo medido y **diciendo qué falta**."""
    medidos = [t for t in trazas if getattr(t, "tokens_estimados", None)]
    return {
        "delegaciones": len(trazas),
        "con_medida": len(medidos),
        "sin_medida": len(trazas) - len(medidos),
        "tokens": sum(t.tokens_estimados for t in medidos),
    }
