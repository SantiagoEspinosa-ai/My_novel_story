---
id: SPEC-14
titulo: El harness delega en sesiones, no llama a una API
estado: aprobada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-14 — Delegación en vez de API

## Qué problema resuelve

El proyecto se diseñó sobre una suposición que nunca se escribió porque nadie la vio como
suposición: **que había una clave de API**. No la hay. Hay una suscripción, así que el
camino es el de la rama `main` — el harness delega en sesiones de Claude Code y ningún
código suyo toca la red.

Eso rompe cuatro cosas que están en documentos aprobados, y esta spec las resuelve. No es
un cambio de implementación: **cambia lo que tres afirmaciones del proyecto significan.**

---

## C-1 · El techo de 100.000 es sobre lo que se manda, no sobre la ventana

`CLAUDE.md` lo define como *"límite duro por llamada, incluida la salida"*. Con delegación,
**la ventana del subagente no es nuestra**: el harness puede medir lo que ensambla y no
puede reservar nada sobre un techo que no administra.

**El límite no pasa a ser informativo.** Sigue siendo un límite real sobre algo real: lo
que sale de nuestro lado. Lo que desaparece es la **garantía sobre lo que pasa al otro**.

| Qué | Qué le pasa |
| --- | --- |
| El reparto por niveles | **Intacto.** Repartir lo que mandamos sigue teniendo sentido |
| El orden de recorte de §2.4 | **Intacto.** Mandar menos sigue siendo mejor |
| `RF-26` | **Intacto.** Si lo ensamblado se pasa del techo, el trabajo falla en vez de generar |
| `P-1`…`P-5` | **Pierden la reserva, conservan la estimación** |

**Y la exclusividad de `P-5` ya no se puede hacer cumplir.** Decía que una llamada del
Escritor a tamaño completo agota el techo global y es, de hecho, exclusiva. Eso era una
consecuencia de administrar el techo. Ahora: si dos delegaciones concurrentes saturan algo,
**nos enteramos por fallo y no por control**. Queda escrito porque quien lea `P-5` mañana
tiene que saber que describe una expectativa y no una garantía.

## C-2 · `VER-41` se retira. La reconciliación es un validador nuevo

**No es el mismo validador con otra implementación: cambia lo que afirma.**

- `VER-41` decía: *el contador cuadra con lo que declara el proveedor.*
- El nuevo dice: *el contador no está por debajo del suelo reconstruible desde los
  artefactos.*

Reutilizar el identificador haría que su historial mintiera. **`VER-41` queda quemado**,
como `VER-44`, y la reconciliación entra como **`VER-61`**.

**El `reconciliar` de `main` es mejor que lo que teníamos**, y por un motivo concreto: tres
resultados con significado distinto informan más que una comparación binaria.

| Resultado | Qué significa |
| --- | --- |
| contador **>** suelo | Normal. La diferencia son reintentos que no dejaron artefacto |
| contador **=** suelo | Sospechoso en una obra con reescrituras: ningún reintento se anotó |
| contador **<** suelo | **Error.** Se perdieron delegaciones que sí produjeron trabajo |

**`PC-8` cambia de forma, no desaparece.** Deja de ser *"valida el contador contra el
proveedor, no contra la verdad"* y pasa a ser *"valida el contador contra un suelo, no
contra una medida"*.

**Y se hereda la regla que `main` aprendió corrigiéndola:** se anota **toda delegación
emitida**, en cuanto hay prueba de que se emitió, y **antes** de intentar interpretarla. Su
contador decía 59 donde habían sido 61, porque una respuesta ilegible hacía fallar el
comando antes de sumar. *Que la respuesta sirva o no es una pregunta posterior e
independiente.*

## C-3 · Son dos números, no tres, y el segundo es un suelo

`tokens_reservados` **desaparece**. Un nombre que dice "reservado" cuando no reserva nada es
peor que no tenerlo.

| Número | Quién lo calcula | Qué garantiza |
| --- | --- | --- |
| `tokens_para_recortar` | El ensamblador, en cada vuelta | Estimación conservadora. Decide si hay que recortar |
| `tokens_estimados` | Lo que reporta la sesión que delegó | **Es un suelo, no una medida.** Si una delegación se anota sin cifras, el total se queda corto y hay que decirlo donde se enseñe el número |

La regla de no mezclarlos sobrevive y **vale más que antes**: el riesgo nuevo es que el
número que reporta la sesión y el que estima el harness salgan del mismo sitio, y entonces
`VER-61` compararía uno consigo mismo.

## C-4 · El transporte se adopta de `main`, no se reescribe

Los hallazgos 13 y 14 de `DECISIONES.md` **están pagados**, y son conocimiento de entorno,
no decisiones de diseño:

- **`claude` es un `.CMD` en Windows**, no un ejecutable. `subprocess.run(["claude", ...])`
  da `FileNotFoundError` mientras `claude --version` funciona en la terminal.
- **El prompt va por stdin, nunca como argumento.** Al pasar por `cmd.exe`, el analizador
  de línea de comandos **termina el comando en el primer salto de línea** y el prompt llega
  truncado. *"No era el prompt: era el transporte."*

Y viene con el **parseo defensivo**, que nuestro `_normalizar` no tiene: quitar vallas,
extraer el primer objeto `{...}` equilibrado, redelegar **una vez** incluyendo el error, y
solo entonces rendirse. El hallazgo 7 explica por qué hace falta aunque el prompt lo
prohíba: **las vallas las añadía la sesión intermedia**, no el modelo.

### Lo que esto obliga a mirar en `SPEC-11` C-4

*"El Juez no ve las reglas del proyecto"* es una decisión que en esta arquitectura tiene un
mecanismo concreto: **`omitClaudeMd: true`** en la definición del subagente. Necesita una
versión mínima de la herramienta y **lo que no reconoce lo ignora en silencio** (hallazgo
3). Una decisión de aislamiento que depende de una opción que puede fallar callando merece
saberse: entra en `PC-17`, que ya dice que nadie comprueba esa regla.

## Qué queda explícitamente fuera

- **Las definiciones de los subagentes** y sus prompts. Son del plan.
- **Los hallazgos 5 y 6** —las skills no se precargan con `--agent`, los subagentes no se
  recargan en caliente—: condicionan **cómo se ejecuta** `E5`, no qué dice el diseño.
- **Reabrir el orden de recorte.** `C-1` lo deja intacto a propósito.
- **Los números**: tope de delegaciones, umbrales.

## Qué gobierna esto

`CLAUDE.md` § "Límite de contexto"; `P-1`…`P-5`, `RF-26` y §2.4 de `SPEC-01`; `SPEC-08` C-4;
`SPEC-11` C-1 y C-4; `SPEC-12` C-3; `VER-41`, `PC-8`, `PC-17`. De la rama `main`:
`EJECUCION.md` §2.5 y §4 regla 6, `DECISIONES.md` hallazgos 3, 7, 13 y 14, y
`src/delegaciones.py`.

## Las cuatro preguntas, contestadas al aprobar el 2026-09-23

| # | Pregunta | Respuesta |
| --- | --- | --- |
| 1 | ¿El techo de 100.000 sigue siendo un límite o pasa a ser informativo? | **Límite**, sobre lo que el harness manda. Lo que desaparece es la garantía sobre la ventana del otro lado |
| 2 | ¿`VER-41` se reescribe o se retira? | **Se retira y se quema.** El nuevo afirma otra cosa; reutilizar el id haría mentir a su historial |
| 3 | ¿`tokens_reservados` desaparece? | **Sí.** Un nombre que dice "reservado" sin reservar es peor que no tenerlo |
| 4 | ¿El transporte se adopta o se reescribe? | **Se adopta**, con su parseo defensivo. Los hallazgos 13 y 14 están pagados |
