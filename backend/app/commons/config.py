"""Configuracion y numeros del harness.

Los numeros de aqui no estan medidos, y el fichero lo dice con esas palabras.
`SPEC-05` fija la convencion: una afirmacion que es cierta porque algo no
existe lleva su condicion de caducidad **pegada**, en forma de ruta y no de
frase. `VER-56` recorre estas marcas tambien en el codigo desde `PLAN-01`,
asi que el dia que exista lo que la ruta nombra, el build falla y hay que
volver a mirarlas.

LA REGLA QUE NO SE PUEDE ROMPER AL REFACTORIZAR
-----------------------------------------------
El numero y su marca son **una sola cosa**. Si alguien mueve el valor a una
variable de entorno o a un fichero de configuracion y deja el comentario aqui,
queda un numero sin procedencia y nadie sabra que no esta medido. Un numero
inventado que se presenta como medido es peor que no tener el dato.
"""

# Provisional: elegido por razonamiento, no medido. `O-3` de `SPEC-01` lo hace
# depender de observar la tasa real de fallos transitorios, y todavia no hay
# sistema que observar. Tres intentos con espera creciente: lo que sobrevive a
# eso no es transitorio, es el proveedor caido. Seguir insistiendo cuesta
# llamadas pagadas y, si es el Escritor, bloquea el sistema entero.
# Caduca con: backend/app/features/orquestacion/
TOPE_REINTENTOS_TRANSPORTE = 3

# Provisional: elegido por razonamiento, no medido. Acota `MF-25` -el techo de
# contexto retenido por un trabajo que no vuelve- pero no lo previene: subirlo
# alarga esa parada. Corto cuesta latencia y no correccion, porque el worker
# comprueba su estado antes de escribir.
# Caduca con: backend/app/features/orquestacion/
MARGEN_ABANDONO_SEGUNDOS = 15 * 60

# Provisional: elegido por razonamiento, no medido. `VER-43` lo hace depender
# de observar cuantas veces regenera de verdad una escena problematica, y
# todavia no hay serie que observar. Tres intentos: el primero es el intento,
# el segundo corrige con los problemas del anterior en el prompt, y el tercero
# es la ultima oportunidad antes de rendirse. Un cuarto no cambia de estrategia,
# solo repite, y cada uno es una delegacion pagada.
# Caduca con: harness/evals/
TOPE_INTENTOS_ESCENA = 3

# Provisional: elegido por razonamiento, no medido. Es el freno de mano de una
# obra entera: seis escenas reales costaron tres delegaciones cada una, asi que
# sesenta escenas limpias son ciento ochenta. Se pone al triple para que una
# obra normal no lo roce y una que se ha ido de madre se pare antes de gastarse
# el presupuesto de alguien. **Lo que acota es el gasto, no el error.**
# Caduca con: harness/evals/
TOPE_DELEGACIONES_OBRA = 540

# **No es provisional: es contrato.** Lo decidio el autor en `SPEC-25` `RF-18`
# y coincide con `MaxIntentos = 2` del modelo TLA+ (`specs/tla/`). Cuenta aparte
# de `TOPE_INTENTOS_ESCENA`: una palabra vetada no es un fallo de calidad que
# se arregle insistiendo, y si compartieran contador una escena podria gastar
# sus intentos en vetadas y rendirse con un problema de calidad sin mirar.
TOPE_REESCRITURAS_POR_VETADA = 2

# **Contrato, no estimacion.** `SPEC-26` `O-1`: el autor lo fijo en 3, igual
# que las reescrituras del Editor. Cuenta rondas enteras -Planificador y, si no
# hay huecos, Revisor-, y cualquier rechazo gasta una.
TOPE_REVISIONES_DE_PLAN = 3

# **Contrato, no estimacion.** `SPEC-30` v4 `RF-07`: el autor lo fijo en 2, el mismo
# numero que `TOPE_REESCRITURAS_POR_VETADA`, pero **su propio contador**: no comparte
# las reescrituras del Editor ni las de `INV-21`. Cuenta rondas de la puerta de
# publicacion por un hallazgo de obra del Editor. Un fallo de Lean no gasta ninguna:
# vuelve al Editor y la generacion se detiene (`RF-06`).
TOPE_REINTENTOS_DE_PUBLICACION = 2

# **Elegido con la medida delante** (`specs/lean/medidas.md`, `PLAN-30` E12): una
# ejecucion en caliente tarda 3,8-3,9 s, y 300 s cubren la compilacion en frio -un clon
# sin `.lake`-, que esta **sin medir**. Un Lean que no acaba a tiempo es «sin
# veredicto», que bloquea igual que un fallo (`SPEC-30` `RF-09`), asi que quedarse
# corto cuesta una parada visible, no un verde falso.
TIEMPO_MAXIMO_LEAN_SEGUNDOS = 300

# **Decision de presupuesto, no medida** (`SPEC-31`): la fija el autor para todas las
# ejecuciones reales de la evaluacion, y el enunciado no pone ninguna. No caduca con
# nada porque no estima nada: el coste de una novela con el pipeline actual esta sin
# medir, y por eso el techo se comprueba contra lo gastado (`gasto_de_evaluacion`) y
# nunca contra una prevision. Se puede pasar en lo que cueste el capitulo en curso: la
# generacion se para entre capitulos, no a media delegacion (`PLAN-31` E5).
TECHO_DE_GASTO_EVALUACION_USD = 150

# **Decision de presupuesto, no medida** (`SPEC-33` cuestion 1): el techo de lo que pueden
# gastar las generaciones lanzadas desde la web, separado del de la evaluacion para que el
# uno no se coma el presupuesto del otro. Decision literal del autor: *«50 USD. Una novela
# cuesta unos 17, asi que caben dos demos y margen para un tercero.»* Se compara contra lo
# gastado en la base (`gasto_de_delegacion`), que es un suelo, y nunca contra una prevision.
TECHO_DE_GASTO_GENERACION_WEB_USD = 50

# **Medida, no estimacion**, y de otra base: la novela de ejemplo (`R1`) costo 16,8905 USD
# en 36 delegaciones, todas con coste medido; el libro de gasto y Langfuse coinciden
# (`harness/evals/medidas.md`). La confirmacion de la web la ensena como **referencia con su
# fuente**, no como un coste de la base en la que se lanza (`SPEC-33` `RF-12`).
REFERENCIA_NOVELA_DE_EJEMPLO = {
    "usd": 16.8905, "delegaciones": 36,
    "fuente": "R1, la novela de ejemplo: libro de gasto y Langfuse (harness/evals/medidas.md)"}

# **Contrato, no estimacion.** `SPEC-26` `RF-11`: tres reescrituras despues del
# primer intento. Agotadas, el capitulo se acepta por rendicion con sus
# hallazgos visibles.
TOPE_REESCRITURAS_DEL_EDITOR = 3

# Provisional: elegido por razonamiento, **pendiente de medida** (`SPEC-26`
# `RF-10`). La medida esta definida: comparar las notas del Editor con la
# revision humana de una novela completa con la misma rubrica, y mover el umbral
# a donde las dos coincidan. Hasta entonces, «menos de 3 en cualquier criterio»
# obliga a reescribir.
# Caduca con: harness/evals/revision_humana/
UMBRAL_DEL_EDITOR = 3

# Provisionales: elegidos por razonamiento, **no medidos** (`SPEC-26` `RF-16`).
# Doce apariciones del nombre de pila en 1.000-1.500 palabras es una cada cien,
# que ya se nota; ocho palabras seguidas iguales en dos capitulos ya no es una
# coincidencia de lengua comun. Los dos se ajustan con la primera novela real:
# contar cuantas veces salta `INV-25` en capitulos que el Editor puntua bien en
# ritmo. Si salta en la mayoria, el umbral esta bajo.
# Caduca con: harness/evals/revision_humana/
UMBRAL_REPETICION_NOMBRE = 12
LONGITUD_FRASE_REPETIDA = 8
