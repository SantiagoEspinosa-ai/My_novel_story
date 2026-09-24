"""Los prompts del sistema, del repositorio a Langfuse (`SPEC-29` `RF-05`, `RF-13`).

**La fuente es el repositorio.** La version de un rol es la huella de su texto: los 12
primeros caracteres del sha256 de su definicion en `.claude/agents/<rol>.md` mas las
plantillas **sin rellenar** que usa. Nace del repositorio y cambia si cambia una coma, asi
que el codigo no depende de Langfuse para arrancar y la iteracion de tuning (`SPEC-31`)
puede decir que version dio cada resultado.

Lo que sube es la plantilla, nunca el prompt tal como se envio: ese lleva la ficha
rellenada (`SPEC-29` § "El limite").
"""

import hashlib
import sqlite3
from dataclasses import dataclass

from app.commons.modelo.proveedor import RAIZ_DEL_REPOSITORIO

AGENTES = RAIZ_DEL_REPOSITORIO / ".claude" / "agents"

SQL = """
CREATE TABLE IF NOT EXISTS version_de_prompt_enviada (
    rol     TEXT NOT NULL,
    version TEXT NOT NULL,
    PRIMARY KEY (rol, version)
);
"""


@dataclass(frozen=True)
class Version:
    rol: str
    version: str
    plantilla: str


def huella(texto: str) -> str:
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()[:12]


def _plantillas():
    """Que plantillas usa cada rol. Importadas aqui dentro porque `novela` y `publicacion`
    importaran este modulo para envolver sus agentes."""
    from app.features.entrevista import service as entrevista, texto_libre
    from app.features.generacion import prompt as generacion
    from app.features.orquestacion import ciclo, novela, publicacion
    from app.features.planificacion import service as planificacion
    return {
        "entrevistador": [entrevista.PROMPT, texto_libre.PROMPT],
        "planificador": [planificacion.PROMPT_PLANIFICADOR],
        "revisor_plan": [planificacion.PROMPT_REVISOR],
        "escritor": [generacion.PLANTILLA, generacion.CON_NOMBRES, generacion.CON_CLAVES,
                     generacion.CON_VETADAS, generacion.CON_ESTABLECER,
                     generacion.CON_INSTRUCCIONES, generacion.CON_PROBLEMAS],
        "editor": [ciclo.RUBRICA_DEL_EDITOR, novela.PROMPT_JUICIO_DE_OBRA,
                   publicacion.PROMPT_FEEDBACK_LEAN, publicacion.PROMPT_INSTRUCCIONES],
        "juez": [ciclo.RUBRICA],
        "resumidor": [ciclo.PROMPT_RESUMEN],
    }


def registro() -> dict:
    salida = {}
    for rol, plantillas in _plantillas().items():
        definicion = (AGENTES / "{0}.md".format(rol)).read_text(encoding="utf-8")
        texto = "\n\n---\n\n".join([definicion] + plantillas)
        salida[rol] = Version(rol=rol, version=huella(texto), plantilla=texto)
    return salida


def version_de(rol):
    v = registro().get(rol)
    return v.version if v else None


def enviar_nuevas(con: sqlite3.Connection, observacion) -> int:
    """Solo las huellas que no se enviaron nunca. Una que no llego no se marca, y se
    reintenta en la siguiente generacion."""
    with con:
        con.executescript(SQL)
    enviadas = 0
    for v in registro().values():
        if con.execute("SELECT 1 FROM version_de_prompt_enviada WHERE rol = ? AND version = ?",
                       (v.rol, v.version)).fetchone():
            continue
        if observacion.prompt(v.rol, v.version, v.plantilla):
            with con:
                con.execute("INSERT INTO version_de_prompt_enviada (rol, version) VALUES (?, ?)",
                            (v.rol, v.version))
            enviadas += 1
    return enviadas
