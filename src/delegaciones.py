"""Registro local de delegaciones a subagentes, con sus tokens.

QUE PROBLEMA RESUELVE
---------------------
El orquestador (la sesion de Claude Code) recibe, cada vez que delega en un
subagente, cuantos tokens entraron y cuantos salieron. Ese dato vive en la
conversacion y se pierde en cuanto la sesion se cierra o se compacta. Este
modulo lo baja a disco, dentro de `salida/estado.json`, junto al resto del
estado.

La consecuencia practica es la misma que la del resto del proyecto: el informe
final se puede sacar sin la sesion que genero la novela. Una sesion nueva, o
directamente `python -m src.orquestacion informe`, puede contestar "esta novela
costo N delegaciones y X tokens, y de esos X, Y acabaron en el manuscrito y el
resto se gastaron en intentos descartados".

POR QUE EL CONTADOR VIVE AQUI Y NO EN EL COMANDO QUE REGISTRA EL RESULTADO
--------------------------------------------------------------------------
Antes, el contador solo subia cuando un resultado se registraba con exito. Una
delegacion cuya respuesta no era JSON interpretable hacia fallar el comando
antes de sumar, asi que el reintento se contaba una sola vez aunque se hubieran
gastado dos delegaciones de verdad. El contador decia 59 donde habian sido 61.

La regla ahora es una sola y no admite excepciones: **se anota toda delegacion
emitida**, en cuanto se tiene la prueba de que se emitio (su respuesta en un
archivo), y antes de intentar interpretarla. Que la respuesta sirva o no es una
pregunta posterior e independiente.

Este modulo no hace llamadas de red y no escribe en disco: recibe el
diccionario de estado, lo modifica y deja que `src/estado.py` lo guarde.
"""

from __future__ import annotations

from datetime import datetime, timezone

# Clave de estado.json donde vive la lista de delegaciones, una por entrada.
CLAVE = "delegaciones_detalle"

# Clave del contador agregado que ya existia. Se mantiene por compatibilidad
# con estados antiguos y porque es lo que mira el freno de mano de la regla 6.
CLAVE_CONTADOR = "delegaciones"

# Clave donde se deja constancia de que el contador de esta generacion no es
# fiable. Existe porque hay un caso que no se puede arreglar hacia atras: una
# delegacion que se emitio, no dejo ningun archivo y no se anoto es
# indistinguible de una que nunca ocurrio. Cuando eso pasa, el numero no se
# inventa: se marca como suelo y se dice por que.
CLAVE_NOTA = "delegaciones_nota"

# Clave donde se anota la delegacion que esta EN MARCHA ahora mismo.
#
# Por que hace falta. El resto de este modulo solo sabe de delegaciones
# terminadas: una entrada aparece en `delegaciones_detalle` cuando ya hay una
# respuesta que registrar. Mientras un subagente piensa —y el escritor con
# `opus` piensa dos o tres minutos— no hay ni una sola senal en disco de que
# este pasando algo. Para quien mira `estado.json` desde fuera, una generacion
# trabajando y una generacion abandonada a medias se ven exactamente igual.
#
# Esta clave es esa senal. La escribe la sesion ANTES de delegar y desaparece
# en cuanto el resultado se registra. Su valor:
#
#     {"rol": "escritor", "modelo": "opus", "capitulo": 4,
#      "intento": 2, "inicio": "2026-09-18T16:20:31Z"}
#
# `inicio` permite calcular cuanto lleva la delegacion en curso sin guardar un
# cronometro en ninguna parte: basta con restar esa hora de la actual cada vez
# que alguien mira.
#
# Ojo con lo que NO garantiza: si la sesion muere entre el marcado y el
# registro, la clave se queda ahi, y entonces dice "esto se lanzo y nunca se
# supo mas", que sigue siendo informacion cierta y util. No es un candado ni un
# bloqueo; es una nota de "estoy aqui".
CLAVE_EN_CURSO = "delegacion_en_curso"

# Orden en que se muestran los roles en los informes. No es alfabetico: es el
# orden en que actuan durante la generacion, que es como mejor se lee.
ORDEN_ROLES = ("arquitecto", "escritor", "continuidad", "genero", "estilo", "resumidor")


def _ahora_iso():
    """Marca de tiempo UTC, en el mismo formato que usa `src/estado.py`.

    Sirve para cruzar una delegacion de este registro con su traza en Langfuse:
    ambas cosas quedan ordenadas en el tiempo y con el mismo huso horario.
    """
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _entero_o_none(valor):
    """Convierte a entero lo que se pueda, y devuelve None si no se puede.

    Los tokens son opcionales a proposito: si una delegacion se anota sin ellos
    (porque la sesion no los tenia a mano), la delegacion sigue contando. Es
    peor perder el recuento de delegaciones que perder el de tokens.
    """
    if valor is None or valor == "":
        return None
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Escribir en el registro
# ---------------------------------------------------------------------------


def listar(estado):
    """Todas las delegaciones anotadas, en orden de emision."""
    entradas = estado.get(CLAVE)
    return entradas if isinstance(entradas, list) else []


def anotar(estado, rol, modelo=None, capitulo=None, intento=None,
           tokens_in=None, tokens_out=None, nota=None):
    """Anota una delegacion emitida y suma uno al contador.

    Devuelve la entrada creada. No guarda nada en disco: de eso se encarga
    quien llame, para que una sola escritura atomica recoja a la vez el
    contador, el detalle y cualquier otro cambio del estado.

    `capitulo` e `intento` van a None cuando no aplican: el arquitecto no tiene
    capitulo, y el resumidor tiene capitulo pero no intento. `en_manuscrito`
    nace como None porque en el momento de delegar todavia no se sabe: lo
    decide `resolver` mas tarde, cuando elige el intento ganador.
    """
    entradas = estado.setdefault(CLAVE, [])
    entrada = {
        "n": len(entradas) + 1,
        "momento": _ahora_iso(),
        "rol": rol,
        "modelo": modelo,
        "capitulo": capitulo,
        "intento": intento,
        "tokens_in": _entero_o_none(tokens_in),
        "tokens_out": _entero_o_none(tokens_out),
        "en_manuscrito": None,
    }
    if nota:
        entrada["nota"] = nota
    entradas.append(entrada)
    estado[CLAVE_CONTADOR] = estado.get(CLAVE_CONTADOR, 0) + 1
    return entrada


def marcar_en_curso(estado, rol, modelo=None, capitulo=None, intento=None):
    """Deja constancia de que se va a delegar AHORA, antes de hacerlo.

    Se llama justo antes de la delegacion, nunca despues: el valor de esta
    marca es precisamente cubrir el hueco de tiempo en el que el subagente esta
    trabajando y no hay nada escrito en disco.

    Solo puede haber una marca a la vez, y la nueva pisa a la anterior. Eso es
    deliberado y tiene una consecuencia que conviene conocer: los tres
    validadores se lanzan en paralelo, asi que marcar los tres dejaria ver solo
    el ultimo. Para ese caso se marca el rol `validadores`, que es lo que de
    verdad esta pasando (los tres a la vez), en vez de fingir que hay uno solo.

    No guarda nada en disco: de eso se encarga quien llame, igual que en
    `anotar`.
    """
    estado[CLAVE_EN_CURSO] = {
        "rol": rol,
        "modelo": modelo,
        "capitulo": capitulo,
        "intento": intento,
        "inicio": _ahora_iso(),
    }
    return estado[CLAVE_EN_CURSO]


def limpiar_en_curso(estado):
    """Quita la marca de delegacion en curso y devuelve la que hubiera.

    Devolver la marca sirve para saber que se estaba haciendo, por ejemplo para
    decir cuanto tardo. Si no habia ninguna, devuelve None y no pasa nada: que
    se registre un resultado sin marca previa es normal en una sesion que no
    marque, y esto no puede ser un error que corte la generacion.
    """
    return estado.pop(CLAVE_EN_CURSO, None)


def en_curso(estado):
    """La delegacion en marcha ahora mismo, o None si no hay ninguna."""
    marca = estado.get(CLAVE_EN_CURSO)
    return marca if isinstance(marca, dict) else None


def segundos_en_curso(estado, ahora=None):
    """Cuanto lleva trabajando la delegacion en curso, en segundos.

    Devuelve None si no hay ninguna marca o si su `inicio` no se puede leer: es
    preferible no decir nada a dar un numero inventado. `ahora` se puede pasar
    para que los tests no dependan del reloj.
    """
    marca = en_curso(estado)
    if not marca:
        return None
    try:
        inicio = datetime.strptime(marca.get("inicio", ""), "%Y-%m-%dT%H:%M:%SZ")
    except (TypeError, ValueError):
        return None
    inicio = inicio.replace(tzinfo=timezone.utc)
    ahora = ahora or datetime.now(timezone.utc)
    return max(0, int((ahora - inicio).total_seconds()))


def marcar_en_manuscrito(estado, capitulo, intento_ganador):
    """Dice, de cada delegacion de un capitulo, si su trabajo acabo publicado.

    Se llama al cerrar un capitulo, cuando ya se sabe que intento gana. Todas
    las delegaciones atadas a ese intento (el escritor que lo redacto y los tres
    validadores que lo auditaron) quedan a True; las de los intentos
    descartados, a False.

    Las delegaciones sin numero de intento (arquitecto, resumidor) se quedan en
    None: no es que su trabajo se tirara, es que la pregunta no les aplica. Con
    esto el informe puede separar los tokens que produjeron manuscrito de los
    que se gastaron en versiones que nadie leera.
    """
    tocadas = 0
    for entrada in listar(estado):
        if entrada.get("capitulo") != capitulo:
            continue
        if entrada.get("intento") is None:
            continue
        entrada["en_manuscrito"] = entrada.get("intento") == intento_ganador
        tocadas += 1
    return tocadas


# ---------------------------------------------------------------------------
# Leer el registro: agregados para el informe
# ---------------------------------------------------------------------------


def _vacio():
    return {"delegaciones": 0, "tokens_in": 0, "tokens_out": 0, "sin_tokens": 0}


def _sumar(acumulador, entrada):
    """Acumula una entrada en un cubo de totales."""
    acumulador["delegaciones"] += 1
    entrada_in = entrada.get("tokens_in")
    entrada_out = entrada.get("tokens_out")
    if entrada_in is None and entrada_out is None:
        # Delegacion anotada sin cifras. Cuenta como delegacion, pero deja
        # constancia de que los totales de tokens se quedan cortos.
        acumulador["sin_tokens"] += 1
    acumulador["tokens_in"] += entrada_in or 0
    acumulador["tokens_out"] += entrada_out or 0
    return acumulador


def totales(estado):
    """Totales de toda la generacion.

    `sin_tokens` cuenta las delegaciones anotadas sin cifra alguna de tokens. Si
    ese numero no es cero, los totales de tokens son un suelo y no una medida:
    hay que leerlos como "al menos tantos".
    """
    acumulador = _vacio()
    for entrada in listar(estado):
        _sumar(acumulador, entrada)
    return acumulador


def por_rol(estado):
    """Agregado por rol de subagente, en el orden en que actuan."""
    grupos = {}
    for entrada in listar(estado):
        rol = entrada.get("rol") or "?"
        _sumar(grupos.setdefault(rol, _vacio()), entrada)

    ordenados = [(rol, grupos[rol]) for rol in ORDEN_ROLES if rol in grupos]
    ordenados += [
        (rol, datos) for rol, datos in sorted(grupos.items())
        if rol not in ORDEN_ROLES
    ]
    return ordenados


def por_capitulo(estado):
    """Agregado por capitulo. Las delegaciones sin capitulo se quedan fuera."""
    grupos = {}
    for entrada in listar(estado):
        capitulo = entrada.get("capitulo")
        if capitulo is None:
            continue
        _sumar(grupos.setdefault(int(capitulo), _vacio()), entrada)
    return [(numero, grupos[numero]) for numero in sorted(grupos)]


def reparto_manuscrito(estado):
    """Separa los tokens segun su trabajo acabara o no en el manuscrito.

    Devuelve tres cubos: `en_manuscrito`, `descartado` y `no_aplica`. El
    segundo es el interesante: es lo que costo la validacion en trabajo tirado,
    y es el numero que dice si conviene subir el escalon inicial de la escalera
    o bajar el numero de intentos por modelo.
    """
    cubos = {"en_manuscrito": _vacio(), "descartado": _vacio(), "no_aplica": _vacio()}
    for entrada in listar(estado):
        marca = entrada.get("en_manuscrito")
        if marca is True:
            _sumar(cubos["en_manuscrito"], entrada)
        elif marca is False:
            _sumar(cubos["descartado"], entrada)
        else:
            _sumar(cubos["no_aplica"], entrada)
    return cubos


def marcar_incompleto(estado, motivo):
    """Deja constancia de que el contador de esta generacion es un suelo.

    Se usa cuando se sabe que faltan delegaciones pero no cuantas: corregir el
    numero a ojo seria peor que dejarlo bajo, porque un numero inventado no se
    distingue despues de uno medido. Un suelo declarado si se distingue.
    """
    estado[CLAVE_NOTA] = {
        "contador_es_suelo": True,
        "motivo": motivo,
        "anotado": _ahora_iso(),
    }
    return estado[CLAVE_NOTA]


def nota(estado):
    """La anotacion de contador incompleto, o None si el contador es fiable."""
    valor = estado.get(CLAVE_NOTA)
    return valor if isinstance(valor, dict) and valor.get("contador_es_suelo") else None


def coherente(estado):
    """True si el contador agregado y el detalle dicen lo mismo.

    Un estado que venga de una generacion anterior a este registro tendra
    contador pero no lista, y aqui dara False. No es un error: significa que de
    esa generacion no hay desglose de tokens, y el informe lo tiene que decir en
    vez de fingir un cero.
    """
    return len(listar(estado)) == estado.get(CLAVE_CONTADOR, 0)
