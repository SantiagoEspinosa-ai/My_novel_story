---
id: PLAN-26
spec: SPEC-26
titulo: Implementación del pipeline de la novela regalo
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-23
version: 1
---

# PLAN-26 — El pipeline de la novela regalo

Cómo se construye `SPEC-26`. Cada paso empieza por la prueba que falla, deja las
534 pruebas actuales en verde y se puede commitear solo. **Ningún paso llama al
modelo real**: todo va contra dobles, salvo E13, que gasta dinero y necesita un
sí explícito.

## Lo que se encontró al preparar el plan

Tres hechos del código que cambian lo que hay que hacer:

1. **El veredicto del Juez no decide nada hoy.** `ciclo.ejecutar` lo guarda y
   ninguna ruta lo usa para aceptar o rechazar. El Editor es la primera crítica
   que decide de verdad, así que hay que conectarlo, no sustituir algo que ya
   funcionaba.
2. **Las invariantes de terror no están implementadas en la puerta.** La puerta
   de escena aplica `INV-01`..`INV-04`, `INV-17` e `INV-18`; de las de terror solo
   hay `INV-12` e `INV-16` «previstas» en `escaleta/plan.py`. `RF-20` es, en la
   práctica, que el Escritor y la rúbrica dejen de ser de terror, que el
   Escaletador no exija la curva de miedo y que el informe diga «no aplica».
3. **Traducir el plan a escaleta vive en un guion** (`obra_diez_capitulos.py`,
   `preparar`), no en `app/`. Hay que llevarlo a `orquestacion/`, donde se puede
   probar y donde la novela regalo lo pueda usar.

## Dos identificadores que la spec no nombra y el plan necesita

`CLAUDE.md` exige que toda comprobación cite su invariante por identificador. La
spec decide dos comprobaciones de juicio sin darles número:

- **`INV-26`** (`mayor`, capítulo, `juez_llm`): el Editor da a cada criterio al
  menos la nota umbral (`RF-09`..`RF-11`).
- **`INV-27`** (`mayor`, obra, `juez_llm`): el juicio de obra no encuentra un arco
  roto ni un final abrupto (`RF-12`).

Los dos están comprobados libres en todas las ramas. **Aprobar este plan es
aprobar esos dos números.**

## Dónde vive

| Dónde | Qué | Por qué ahí |
| --- | --- | --- |
| `features/planificacion/` (nueva) | Planificador, Revisor del plan, comprobación de cobertura y versiones del plan | Es un caso de uso propio: de ficha a plan aprobado (`A-02`) |
| `features/verificacion/personalizacion.py` | `INV-22`, `INV-23`, `INV-25`: funciones puras sobre texto | Son puertas deterministas, como el resto de `verificacion/` |
| `features/orquestacion/novela.py` (nueva) | Compone: ficha → plan → obra montada → generación → juicio de obra | Componer es solo de `orquestacion/` |
| `features/orquestacion/ciclo.py` y `obra.py` | `INV-22` junto a `INV-21`, `INV-23`, el Editor e `INV-26` | Es donde ya viven las puertas de la escena |
| `commons/invariantes/registro.py` | `INV-22`..`INV-27` y qué invariantes son del plano Terror | El registro es la copia en código de la tabla |
| `backend/hooks/` (nueva) | `validar_capitulo.py` (Stop) y `policy.py` (PreToolUse) | Son scripts que ejecuta Claude Code, no la API |
| `.claude/settings.json` (nuevo en esta rama) | La declaración de los dos hooks | Es donde Claude Code los lee |
| `.claude/agents/` | `planificador.md`, `revisor_plan.md`, `editor.md`; `escritor.md` deja de ser de terror | Un agente por llamada (`A-03`) |
| `backend/novela_regalo.py` | Guion de ejecución real a partir de un brief con destinatario | Como `obra_diez_capitulos.py`: gasta dinero, no es un comando suelto |

**Sin migraciones de tablas existentes.** `entidad.fecha_de_nacimiento` y
`escena.t_fabula` ya existen (`SPEC-21`). La única tabla nueva es la de versiones
del plan, en su feature.

## Pasos

### E1 · El dominio primero

`Docs/definitions.md`: en `PlanDeLaObra`, los imprescindibles del plan
(`{elemento, capitulo, palabras_clave[]}`), el momento de la fábula por capítulo,
la fecha de nacimiento por personaje y las exclusiones previstas
(`{personaje, capitulo, estado_vital}`); la clase `ValoracionDelEditor`
(`{criterio, nota, justificacion, instruccion}`); el vocabulario
`criterio_de_edicion` (continuidad, tono, arco, coherencia\_de\_personajes, ritmo,
personalizacion); e `INV-22`..`INV-27` en la tabla.

**Prueba:** `test_enumeraciones.py` falla hasta que `CriterioDeEdicion` cuadra
literal a literal.

### E2 · Los validadores deterministas, como funciones puras

`verificacion/personalizacion.py`:

- `nombres_mal_escritos(texto, nombres)`: palabras con mayúscula a distancia de
  edición 1 de un nombre conocido (2 si tiene más de 6 letras) que no son ese
  nombre ni otro conocido (`INV-22`).
- `claves_ausentes(texto, imprescindibles)`: las palabras clave que no aparecen,
  con la normalización de `commons/politica/` (`INV-23`).
- `repeticiones(texto, nombre, umbral)` y `frases_repetidas(textos, longitud)`
  (`INV-25`).

**Pruebas:** «Irena» por «Irene» se detecta; «Irene» no; «Luisa» no se toma por
«Luis» si los dos son personajes; una clave con otro plural o acento cuenta como
presente; una clave ausente se nombra; el umbral de repetición cambia el
resultado; una frase de 8 palabras repetida entre dos capítulos se encuentra.

### E3 · El registro y el plano Terror

`INV-22`..`INV-27` en el registro. `registro.aplica(inv, genero)` dice si una
invariante se aplica a una obra: las de terror (`INV-10`, `INV-11`, `INV-12`,
`INV-14`, `INV-16`) solo con `genero = terror`. `escaleta/plan.py` deja de exigir
`INV-12` e `INV-16` en una obra que no es de terror, y el informe de la obra
escribe «no aplica» junto a cada una.

**Pruebas:** `test_registro` pasa a 1..27 menos las reservadas 19 y 20; una obra
de aventura no exige la curva de miedo en su plan y su informe dice «no aplica»
cinco veces; una de terror sigue exigiéndola.

### E4 · El plan y su cobertura

`commons/configuracion/esquemas.py`: el `PlanDeLaObra` gana lo de E1.
`planificacion/cobertura.py`: `huecos(plan, ficha)` devuelve lo que se comprueba
sin juicio (`RF-06`): 10 capítulos, una escena por capítulo, cada imprescindible
con capítulo y al menos una palabra clave, los nombres del plan iguales a los de
la ficha y ninguna vetada en el plan.

**Pruebas:** un plan correcto no tiene huecos; cada condición tiene su plan
roto y su hueco nombrado; un plan con un imprescindible de la ficha sin asignar
lo dice.

### E5 · Planificar con revisión

`planificacion/service.py`: el Planificador produce un plan (JSON validado con el
esquema, reintentos con el tope de transporte). Si `huecos()` no está vacío,
vuelve al Planificador sin pasar por el Revisor. Si está vacío, el Revisor
compara plan y ficha y devuelve `{"aprobado": bool, "objeciones": [...]}`. Con
objeciones, el Planificador rehace el plan, **hasta 3 revisiones**
(`topes.revisiones_de_plan`). Cada versión del plan y su veredicto se guardan en
la tabla `plan_de_obra`. Agotado el tope, se lanza `PlanNoAprobado` y **la
generación no empieza**.

**Pruebas**, con dobles: aprobado a la primera; aprobado en la tercera revisión,
con las objeciones de la segunda dentro del prompt de la tercera; rechazado tres
veces → `PlanNoAprobado` y cero llamadas al Escritor; un plan con huecos no llega
al Revisor.

### E6 · Montar la obra desde el plan

`orquestacion/novela.py:montar(con, obra, brief)` hace en `app/` lo que hoy hace
`preparar` en el guion: alta de la obra, un capítulo por entrada del plan con
**una escena de 1.000 a 1.500 palabras** (`RF-01`), hechos declarados (los
imprescindibles incluidos, uno por elemento), personajes y lugares sembrados,
fechas de nacimiento (`aplicar.fijar_fecha_de_nacimiento`) y `t_fabula` por
escena.

**Pruebas:** tras montar hay 10 capítulos con una escena cada uno y
`longitud_objetivo = [1000, 1500]`; cada imprescindible es un `HechoCanonico`;
las fechas de nacimiento y los `t_fabula` están en la base; montar dos veces no
duplica.

### E7 · Nombres exactos e imprescindibles en la puerta

En `ciclo.ejecutar`, junto a `INV-21` y antes del Juez o Editor, `INV-22`: con un
nombre mal escrito la escena vuelve al Escritor con el fragmento exacto, **con el
mismo contador y el mismo tope de 2 que `INV-21`** (`O-2`). `INV-23` entra como
hallazgo `mayor` dentro de los intentos de calidad. Cuando las claves de un
imprescindible aparecen, se registra su uso (`menciona`, origen `regla`) en
`uso_de_hecho`, que es de donde leerá `INV-24`. El prompt lleva los nombres
exactos y las palabras clave del capítulo (Regla 4).

**Pruebas:** un doble que escribe «Irena» dos veces y luego «Irene» → aceptada
con 2 reescrituras que cuentan en el mismo contador que las vetadas; tres veces →
parada `nombre_mal_escrito`; una clave ausente produce `INV-23` y un intento más;
la clave presente deja una fila en `uso_de_hecho`; el prompt lleva los nombres y
las claves.

### E8 · El Editor

`ciclo.py`: con un Editor en vez del Juez, su respuesta se valida
(`{"valoraciones": [...seis criterios...]}`, cada una con nota 1–5 y
justificación no vacía). Una nota por debajo de `umbral_del_editor` (inicial 3,
**pendiente de medida**, `RF-10`) produce un hallazgo `INV-26` `mayor` cuyas
instrucciones entran en el siguiente intento. Para la novela regalo el tope es
**1 intento + 3 reescrituras**; agotado, `aceptada_por_rendicion` con los
hallazgos visibles. Una respuesta ilegible es `sin_veredicto`, que no se trata
como violación. El Editor se lanza aislado, como el Juez.

**Pruebas:** seis notas de 4 → aceptada sin reescribir; una nota de 2 → hallazgo
`INV-26` y la instrucción del Editor en el prompt siguiente; cuatro rondas por
debajo → rendida; una valoración sin justificación es ilegible y no bloquea; el
Editor se lanza desde un directorio sin `CLAUDE.md`.

### E9 · El nivel obra

Al terminar el último capítulo: `INV-24` (`bloqueante`) consulta `uso_de_hecho`
por cada imprescindible, y si falta alguno **la novela no se da por terminada**;
`INV-25` (`menor`) cuenta repeticiones por capítulo y frases repetidas entre
capítulos, leyendo el texto de la base sin mandarlo al modelo; el juicio de obra
(`INV-27`) recibe **los resúmenes de los diez capítulos y el texto completo del
último**, nunca la obra entera.

**Pruebas:** con un imprescindible sin uso, la generación termina en
`novela_incompleta` y lo nombra; con todos, termina; el nombre repetido por
encima del umbral da un `menor` y no para nada; el prompt del juicio de obra
contiene el último capítulo entero y no contiene el texto del primero.

### E10 · Los hooks

`backend/hooks/validar_capitulo.py` (evento `Stop`): lee el último mensaje del
agente desde la transcripción, extrae el JSON y comprueba longitud, vetadas y
nombres con las funciones de E2. Si falla, sale con código 2 y el motivo, y
Claude Code se lo devuelve al Escritor en la misma sesión. `policy.py` (evento
`PreToolUse`): niega cualquier herramienta a un agente del pipeline y deja la
negación en el audit log.

**Solo actúan sobre el pipeline** (`RF-19`): `proveedor.SesionDelegada` lanza cada
delegación con `HARNESS_AGENTE` y `HARNESS_REGLAS` (la ruta de un JSON con
vetadas, nombres y longitud), y los dos scripts no hacen nada si falta
`HARNESS_AGENTE`.

**Pruebas**, ejecutando los scripts como proceso con su entrada JSON: sin
`HARNESS_AGENTE` salen con 0 sin mirar nada; con un texto corto o con una vetada,
el de validación sale con 2 y el motivo; con uno correcto, 0; el de policy niega
y deja la fila en el audit log; `SesionDelegada` pone las dos variables.

**Lo que estas pruebas no prueban**, dicho aquí para que no se dé por hecho: que
Claude Code entregue a los hooks esas variables y ese formato de entrada en una
delegación real. Eso lo comprueba E13. Y mientras los agentes tengan
`tools: []`, el hook de policy **no se dispara nunca** en la práctica: es una
guarda contra que alguien les dé herramientas, verificada por su prueba de
script.

### E11 · Los agentes y la configuración

`planificador.md`, `revisor_plan.md` y `editor.md`, todos con `tools: []` y su
contrato JSON. `escritor.md` deja de decir «terror»: el género y el tono llegan
en el prompt. `sistema.json` gana los modelos de los tres agentes y
`topes.revisiones_de_plan = 3`, `topes.reescrituras_del_editor = 3`,
`umbral_del_editor = 3` y los umbrales de repetición, con su marca de
**provisional, no medido** en `commons/config.py`.

**Pruebas:** cada agente del pipeline existe y declara `tools: []`; ninguno
menciona «terror» salvo la rúbrica del Juez de terror; `sistema.json` carga con
los campos nuevos.

### E12 · `Docs/` y spec al día

`architecture.md` (la feature, los tres agentes, los hooks), `domain-knowledge.md`,
`verification.md` (filas nuevas, números comprobados al commitear), `AGENTS.md` y
`CLAUDE.md` (el guion `novela_regalo.py`, que gasta dinero). `SPEC-26` pasa a
`aplicada` con su commit propio.

### E13 · Una ejecución real mínima (gasta dinero; necesita un sí explícito)

Con `novela_regalo.py` y un brief de prueba con datos inventados: **un solo
capítulo**, para comprobar lo que las pruebas no pueden: que los hooks reciben
las variables y la transcripción, que el Planificador y el Revisor devuelven JSON
válido y que un capítulo sale entre 1.000 y 1.500 palabras. El coste se informa
con lo que diga la medida, y si una cifra no llega, se dice «sin medir».

## Qué filas `VER-xx` abre

Nuevas, con número comprobado al commitear (hoy el último publicado es `VER-69`):
nombres exactos (`INV-22`), imprescindibles por capítulo y por obra (`INV-23`,
`INV-24`), repetición (`INV-25`), el Editor (`INV-26`), el juicio de obra
(`INV-27`), el plan aprobado antes de escribir y los hooks limitados al pipeline.

## Lo que este plan no hace

- No envía nada a Langfuse.
- No conecta Lean ni decide qué bloquea la publicación.
- No escribe los cinco briefs de evaluación ni hace la revisión humana.
- No genera una novela completa: E13 es un capítulo.
