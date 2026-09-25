"""El prompt del Escritor.

QUE PIDE, Y POR QUE PIDE LAS DOS COSAS A LA VEZ
------------------------------------------------
Texto **y** delta en la misma respuesta (`RF-15`, `A-03`). Extraer el delta
despues, releyendo la escena, es mas caro y menos fiel: el modelo tendria que
deducir lo que el mismo acaba de decidir.

QUE SI LLEVA: LOS IDENTIFICADORES DISPONIBLES
----------------------------------------------
Sin saber que ids existen, el modelo no puede citarlos y se le esta pidiendo lo
imposible: en la primera generacion real devolvio `"sujeto": "casa familiar"`
porque nadie le habia dicho que los sujetos son identificadores ni cuales hay.
El rechazo del contrato habria sido merecido e inutil.

Es la mitad del arreglo. La otra la hace el contrato, que comprueba que la
respuesta los use: **un prompt bien construido no garantiza una respuesta bien
formada.**

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
{extension}
EL PUNTO DE VISTA ES DEL PLAN, NO TUYO
{pov}
Escribe la escena desde ese personaje y desde ningun otro, y **declaralo** en
`pov_usado`. Si lo cambias, la escena no es la planificada.

IDENTIFICADORES QUE PUEDES CITAR EN EL DELTA
Usa SOLO estos. Son identificadores, no descripciones: si lo que quieres decir
no esta en la lista, no lo pongas en el delta y dejalo solo en el texto.
{identificadores}
{establece}
{problemas}{instrucciones}{vetadas}{personalizacion}FORMATO DE LA RESPUESTA
Devuelve un unico objeto JSON con tres claves, las tres obligatorias. Una
respuesta sin `pov_usado` se rechaza entera, aunque el texto este bien:
  "texto": la escena, en prosa.
  "pov_usado": el identificador del personaje desde cuyo punto de vista la
      escribiste. Es lo que se compara con el POV del plan.
  "delta": lo que cambia en el mundo. Cada campo tiene un significado preciso y
  no son intercambiables:

      cambio_de_valor        {{"eje": ..., "signo": ...}}
          En que se mueve la escena y en que direccion.

      movimientos            [{{"personaje": ..., "a": ...}}]
          Donde queda cada personaje al terminar la escena.

      revelaciones           [{{"sujeto": ..., "hecho": ...}}]
          El sujeto PASA A CONOCER ese hecho en esta escena: es el momento en
          que se entera. Si ya lo sabia de antes, NO va aqui.

      acciones               [{{"personaje": ..., "hecho": ...}}]
          El personaje obra SIRVIENDOSE de un hecho que YA conocia. Es lo que
          hace, no lo que aprende. Si se entera en esta escena y ademas obra
          con ello, van las dos cosas, cada una en su lista.

      cambios_de_estado_vital [{{"personaje": ..., "de": ..., "a": ...}}]
          Quien pasa a estar vivo, muerto o desaparecido.

No expliques el JSON ni lo envuelvas en vallas de bloque de codigo.
"""

SIN_PROBLEMAS = ""
# `F-209`: el rango dentro del JSON de parametros no bastaba; el Escritor real se quedaba
# corto siempre. Se apunta cerca del maximo porque el error medido es por abajo.
CON_EXTENSION = """
EXTENSION
La escena tiene entre {minimo} y {maximo} palabras; apunta a unas {apunta}, que son
unos {parrafos} parrafos de unas 100 palabras. Un texto fuera de ese rango vuelve para
reescribirlo, y el error habitual es quedarse corto.
"""
SIN_INSTRUCCIONES = ""
SIN_VETADAS = ""
CON_NOMBRES = """NOMBRES QUE VAN ESCRITOS EXACTAMENTE ASI
Con estas letras y estas tildes. Un nombre parecido que no sea igual devuelve la
escena para reescribirla.
{lista}

"""
CON_CLAVES = """ESTE CAPITULO TIENE QUE CONTAR ESTO
Son recuerdos y rasgos reales de la persona que recibe la novela. Integralos con
naturalidad, sin forzarlos, y usa estas palabras al contarlos, escritas tal cual y
en esa forma exacta: sin cambiar el tiempo del verbo, el numero ni el genero. Si la
narracion va en pasado, ponlas en un dialogo o en una frase en presente.
{lista}

"""
CON_VETADAS = """PALABRAS QUE NO PUEDEN APARECER
Ni estas ni sus plurales, femeninos o variantes con o sin acento. Una sola
aparicion devuelve la escena para reescribirla.
{lista}

"""
SIN_ESTABLECER = ""
CON_ESTABLECER = """
ESTA ESCENA TIENE QUE ESTABLECER ESTOS HECHOS
El plan dice que es aqui donde el lector se entera de esto. Escribelos en el
texto y **declaralos en `revelaciones`**, con el sujeto que se entera.
{lista}
"""
CON_INSTRUCCIONES = """INSTRUCCIONES DE UNA PERSONA SOBRE ESTA ESCENA
Esto no lo levanto ninguna regla: lo escribio quien supervisa la obra. Tiene
prioridad sobre tu criterio.
{lista}

"""
CON_PROBLEMAS = """PROBLEMAS DEL INTENTO ANTERIOR QUE HAY QUE CORREGIR
{lista}

"""


def construir(parametros: dict, estado: dict, objetivo: str, problemas=None,
              personajes=None, ids_de_hechos=None, instrucciones=None,
              establece=None, vetadas=None, nombres=None,
              imprescindibles=None) -> str:
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
    # Las instrucciones humanas van en un bloque **propio** y no mezcladas con
    # los problemas: un hallazgo lo levanto una regla y una instruccion la
    # escribio una persona. Mezclarlos haria que el modelo no supiera cual es
    # cual, y que quien lea la traza no pueda saber de donde salio cada cosa.
    # `SPEC-19` P-5 / Regla 4, por tercera vez: si no le decimos que hechos
    # tiene que establecer, exigirle en el contrato que los declare es pedirle
    # lo imposible, y `INV-18` seria un rechazo merecido e inutil.
    bloque_establece = SIN_ESTABLECER
    if establece:
        bloque_establece = CON_ESTABLECER.format(
            lista="\n".join("- " + str(e) for e in sorted(establece)))
    bloque_humano = SIN_INSTRUCCIONES
    if instrucciones:
        bloque_humano = CON_INSTRUCCIONES.format(
            lista="\n".join("- " + str(i) for i in instrucciones))
    # `SPEC-25` / Regla 4: `INV-21` rechaza una escena con una vetada, asi que
    # el Escritor tiene que saber cuales son antes de escribir, no despues.
    bloque_vetadas = SIN_VETADAS
    if vetadas:
        bloque_vetadas = CON_VETADAS.format(
            lista="\n".join("- " + str(v) for v in vetadas))
    # `SPEC-26` / Regla 4: `INV-22` e `INV-23` exigen nombres exactos y palabras
    # clave, asi que el Escritor tiene que saberlos antes de escribir.
    bloque_personal = ""
    if nombres:
        bloque_personal += CON_NOMBRES.format(
            lista="\n".join("- " + n for n in nombres))
    if imprescindibles:
        bloque_personal += CON_CLAVES.format(lista="\n".join(
            "- {0} (palabras: {1})".format(i["elemento"], ", ".join(i["palabras_clave"]))
            for i in imprescindibles))
    bloque_extension = ""
    rango = parametros.get("longitud_objetivo")
    if rango and len(rango) == 2:
        minimo, maximo = int(rango[0]), int(rango[1])
        apunta = maximo - max(50, (maximo - minimo) // 4)
        bloque_extension = CON_EXTENSION.format(
            minimo=minimo, maximo=maximo, apunta=apunta, parrafos=round(apunta / 100))
    ids = "\n".join([
        "personajes: " + (", ".join(personajes or []) or "(ninguno)"),
        "hechos: " + (", ".join(ids_de_hechos or []) or "(ninguno)"),
    ])
    return PLANTILLA.format(
        identificadores=ids,
        pov=parametros.get("pov") or "(el plan no lo declara)",
        parametros=json.dumps(parametros, ensure_ascii=False, sort_keys=True),
        estado=(estado if isinstance(estado, str)
                else json.dumps(estado, ensure_ascii=False, sort_keys=True)),
        objetivo=objetivo,
        extension=bloque_extension,
        problemas=bloque,
        instrucciones=bloque_humano,
        establece=bloque_establece,
        vetadas=bloque_vetadas,
        personalizacion=bloque_personal,
    )


def hash_de(prompt: str) -> str:
    """`prompt_hash`. Detecta si una reconstruccion es fiel; no la reconstruye."""
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]
