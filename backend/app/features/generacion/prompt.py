"""El prompt del Escritor.

QUE PIDE, Y POR QUE PIDE LAS DOS COSAS A LA VEZ
------------------------------------------------
Texto **y** delta en la misma respuesta (`RF-15`, `A-03`). Extraer el delta
despues, releyendo la escena, es mas caro y menos fiel: el modelo tendria que
deducir lo que el mismo acaba de decidir.

QUE NO LLEVA, Y ESO IMPORTA MAS
--------------------------------
No lleva las reglas del proyecto ni los enunciados de las invariantes. El
Escritor escribe; quien comprueba es otro. Si el prompt le dijera que se va a
comprobar, aprenderia a pasar la comprobacion en vez de a escribir bien, que es
una forma cara de no verificar nada.

Para el Juez la misma regla es aun mas dura y esta decidida en `SPEC-11` C-4:
**no ve las reglas del proyecto**. Desde `SPEC-04` es el desempate de `INV-03`,
`INV-11` e `INV-14`, y un desempate que ve lo mismo que la regla no desempata:
confirma.

EL PROMPT ES DETERMINISTA DADA LA ENTRADA
------------------------------------------
Mismo contexto, mismo prompt, mismo `prompt_hash`. Sin eso el hash no sirve
para detectar si una reconstruccion es fiel, que es lo unico para lo que sirve:
**detecta, no reconstruye**.
"""

import hashlib
import json

PLANTILLA = """Escribe una escena de la novela.

PARAMETROS
{parametros}

LO QUE YA ES VERDAD EN LA FICCION
{estado}

LO QUE ESTA ESCENA TIENE QUE HACER
{objetivo}

{problemas}
FORMATO DE LA RESPUESTA
Devuelve un unico objeto JSON con dos claves:
  "texto": la escena, en prosa.
  "delta": lo que cambia en el mundo, con esta forma:
      cambio_de_valor        {{"eje": ..., "signo": ...}}
      movimientos            [{{"personaje": ..., "a": ...}}]
      revelaciones           [{{"sujeto": ..., "hecho": ...}}]
      cambios_de_estado_vital [{{"personaje": ..., "de": ..., "a": ...}}]
No expliques el JSON ni lo envuelvas en vallas de bloque de codigo.
"""

SIN_PROBLEMAS = ""
CON_PROBLEMAS = """PROBLEMAS DEL INTENTO ANTERIOR QUE HAY QUE CORREGIR
{lista}

"""


def construir(parametros: dict, estado: dict, objetivo: str, problemas=None) -> str:
    """Los problemas del intento anterior entran en el prompt, no en un aviso.

    En la otra rama el aviso de longitud lo leia la sesion orquestadora y no el
    escritor, asi que en la reescritura siguiente el escritor no sabia nada de
    el y volvia a fallar igual. Por eso son un bloque del contexto y por eso
    llegan hasta aqui.
    """
    bloque = SIN_PROBLEMAS
    if problemas:
        bloque = CON_PROBLEMAS.format(
            lista="\n".join("- [{0}] {1}".format(p["invariante"], p["descripcion"])
                            for p in problemas))
    return PLANTILLA.format(
        parametros=json.dumps(parametros, ensure_ascii=False, sort_keys=True),
        estado=json.dumps(estado, ensure_ascii=False, sort_keys=True),
        objetivo=objetivo,
        problemas=bloque,
    )


def hash_de(prompt: str) -> str:
    """`prompt_hash`. Detecta si una reconstruccion es fiel; no la reconstruye."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
