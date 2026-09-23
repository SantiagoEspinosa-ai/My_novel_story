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

# **Contrato, no estimacion.** `SPEC-26` `RF-11`: tres reescrituras despues del
# primer intento. Agotadas, el capitulo se acepta por rendicion con sus
# hallazgos visibles.
TOPE_REESCRITURAS_DEL_EDITOR = 3
