# Roadmap de reducción de coste por tokens

**Criterio que gobierna todo el documento:** el objetivo no es gastar menos tokens, es **reducir el coste por capítulo de calidad aceptable**. Una medida que abarata la generación y multiplica las reescrituras, o que degrada la continuidad, no ahorra nada.

Cada medida que ponga en riesgo la coherencia va marcada con ⚠️.

---

## Fase 1 · Inventario

### Agentes con modelo

| Agente | Modelo | Cuándo corre |
| --- | --- | --- |
| Entrevistador | — | Una vez por novela |
| Planificador + Revisor | — | Una vez, hasta 3 rondas |
| Escritor | Fable | Por capítulo, más cada reescritura |
| Editor | Opus 5.5 | Por capítulo, seis notas |
| Juez | Opus 5.5, fijo por obra | Desempate de INV-03, INV-11, INV-14 |
| Resumidor | Haiku | Por capítulo aceptado |

Sin modelo por diseño: Orquestador, Ensamblador de contexto, Consolidador, Verificador de reglas. Lo que resuelve una consulta SQL no lleva modelo.

### Flujo

```
entrevista → ficha → plan (con revisor)
  └─ por capítulo: ensamblar contexto → Escritor → puertas deterministas
                   → Editor → reescritura si hace falta → consolidar
                   → Resumidor → puerta de capítulo
```

### Memoria

Story bible en SQLite: hechos con sus usos por capítulo, cronología, fichas versionadas por `t`, resúmenes por capítulo, deltas persistidos y registro de conocimiento. El contexto se monta en siete bloques con orden de recorte y formas reducidas.

### Dónde se van los tokens, medido

| Dato | Valor | De dónde sale |
| --- | --- | --- |
| Creación de caché frente a salida | 9.476 vs 1.188 tokens | Primera escena medida |
| Reparto por agente | Escritor 75%, Juez 17%, Resumidor 7% | Escena con los tres |
| Coste por escena | 0,3951 USD (3 agentes) · 0,47 USD (obra de 10 cap.) | E5b y obra larga |
| Obra completa de 10 capítulos | 26,04 USD, 169 delegaciones, 78 min | Primera obra |
| Capítulo 1 de la novela regalo | 3,77 USD en 7 llamadas, 3 intentos | Primera ejecución del pipeline nuevo |
| Contexto montado, máximo | 4.352 tokens = 4,4% del techo de 100.000 | Obra de 10 capítulos |
| `cache_read` | 1.553 (Escritor), 1.572 (Juez) | Segunda ejecución |

**El hallazgo que gobierna el roadmap:** el coste lo domina **montar el contexto**, no escribir. Y aislar al Juez —cuyo directorio no tiene `CLAUDE.md`— lo hizo **cuatro veces más barato**: 2.562 tokens de caché en vez de 8.434. La decisión se tomó por corrección y resultó ser la partida más rentable del ciclo.

### Supuestos declarados, no medidos

- El coste del pipeline actual **con Editor** está sin medir. Las cifras de obra larga vienen del diseño anterior, sin Editor.
- El **contexto enviado real** está sin medir desde F-58: hasta entonces el número medía lo que se montaba, no lo que se enviaba, y sesgaba a la baja.
- El coste de una novela regalo completa está sin medir: la ejecución no pasó del capítulo 1.
- Los tokens que devuelve una tool se miden pero no se presupuestan (SPEC-28). Punto ciego declarado.

---

## Fase 2 · Categorías

| | Categoría | Qué agrupa |
| --- | --- | --- |
| **A** | Coste de arranque por delegación | Creación de caché, A-03, qué `CLAUDE.md` ve cada agente, aislamiento por directorio |
| **B** | Ensamblado del contexto | Los siete bloques, orden de recorte, qué entra y qué no |
| **C** | Reintentos y reescrituras | Escritor rechazado, rondas del planificador, capítulos fuera de rango |
| **D** | Reparto de modelos por tarea | Qué agente usa qué modelo y si está bien asignado |
| **E** | Validación y juicio | Editor y Juez: cuánto de lo que juzga un modelo lo haría una regla |

Fuera de alcance: código e infraestructura del agente, que no consume tokens de generación. La orquestación cae dentro de **A**, porque aquí el orquestador es código determinista.

---

## Fase 3 · Informe por categoría

### A · Coste de arranque por delegación

**1. Situación.** Es la partida mayor con diferencia: 9.476 tokens de creación de caché frente a 1.188 de salida. Cada agente paga su propio arranque por A-03 (un agente, una llamada, contexto propio). Con seis agentes y diez capítulos, eso son decenas de arranques por novela.

Hay una medida que lo demuestra: el Juez, aislado en un directorio sin `CLAUDE.md`, crea 2.562 tokens de caché en vez de 8.434. **Cuatro veces más barato, por no leer un fichero que no necesitaba.**

**2. Estrategias.**

| Medida | Qué hace |
| --- | --- |
| **Auditar qué `CLAUDE.md` ve cada agente** | El Juez ya está aislado por corrección. Aplicar lo mismo al Resumidor y al Revisor, que tampoco necesitan las reglas del proyecto |
| **Partir `CLAUDE.md` por audiencia** | Un núcleo mínimo para los agentes de generación y el resto en ficheros que solo lee quien los necesita |
| **Aprovechar el caché entre capítulos** | El bloque inmutable —premisa, guía de estilo, anclas— es idéntico en los diez capítulos. Que sea el prefijo estable de cada prompt maximiza `cache_read` |
| **⚠️ Agrupar escenas por delegación** | Menos arranques, pero contradice A-03 y pierde la atribución de fallos por escena, que es por lo que A-03 se eligió |

**3. Ahorro / esfuerzo.** Auditar el `CLAUDE.md` de cada agente: **ahorro alto, esfuerzo bajo** — hay evidencia medida de 4× en un caso. Prefijo estable: **alto / medio**. Agrupar escenas: alto y **no recomendado**.

**4. Riesgos.** El aislamiento tiene un límite conocido: `omitClaudeMd` depende de una versión concreta de Claude Code y **falla en silencio** si no la reconoce. Si deja de aplicarse, el Juez vuelve a ver las reglas del proyecto y su desempate pasa a ser confirmación en vez de desempate. Mitigación: el validador que ya está previsto para comprobar que el aislamiento se aplica de verdad, no solo que está configurado.

**5. Prioridad. La primera.** Es donde está el dinero, hay evidencia medida y no toca la calidad.

---

### B · Ensamblado del contexto

**1. Situación.** El contexto montado llega a 4.352 tokens sobre un techo de 100.000: **el 4,4%**. En una obra de diez capítulos **no se ejerció ni un solo recorte**.

Eso significa que todo el mecanismo de SPEC-12 —formas reducidas, la regla de que lo que lee una bloqueante no se reduce ni se elimina, la partición de `Lugar`— se diseñó para un régimen que el sistema no alcanza. No está mal: está sin ejercer, que es distinto.

Y hay un dato que lo relativiza: el número de 1.339 tokens que sostenía esa conclusión **medía lo que se montaba, no lo que se enviaba** (F-58). El contexto enviado real está sin medir.

**2. Estrategias.**

| Medida | Qué hace |
| --- | --- |
| **Medir primero el contexto enviado** | Nada de esto se decide sin ese número. Es gratis: viaja en la siguiente generación |
| **Ajustar el reparto a lo que se mide** | 15.000 para el inmutable y 25.000 para el local describen otro sistema |
| **Recuperación por similitud en lugar de «todas las fichas»** | `sqlite-vec` ya está enganchado y hoy no se usa para acotar |
| **⚠️ Reducir el bloque Local** | Es el que más ocupa. La escena anterior completa es también lo que sostiene la continuidad inmediata |

**3. Ahorro / esfuerzo.** Medir: **esfuerzo nulo, ahorro indirecto**. Ajustar el reparto: **bajo / bajo** — no ahorra por sí solo, quita ruido. Recuperación acotada: **medio / medio**, y crece con la longitud de la obra.

**4. Riesgos.** Alto y documentado. El bloque Local es exactamente lo que se arregló en F-40 y F-45: una novela que olvida el capítulo uno al empezar el dos. Y una escena escrita sin la anterior ni el estado del mundo **va a salir mal y consumirá una regeneración de todas formas**, así que recortar ahí no ahorra, traslada el gasto a la categoría C.

**5. Prioridad. Segunda, y solo la medición por ahora.** Con el contexto al 4,4% del techo, optimizar el ensamblado es optimizar lo que no duele.

---

### C · Reintentos y reescrituras

**1. Situación.** Cada reintento es **una delegación pagada completa**, con su arranque de caché incluido. Los datos:

- Capítulo 1 del regalo: **3 intentos, 7 llamadas, 3,77 USD**, y ni siquiera llegó a aceptarse.
- El plan: **3 rondas**, dos rechazadas por errores de formato del planificador (F-62), a una ronda de agotar el tope.
- Un intento se pasó del máximo de palabras: 1.564 sobre 1.500.
- Una parada fue **un falso positivo** (F-59): la palabra vetada «coño», al normalizar, acabó vetando la preposición «con». El Escritor no podía escribir una frase.

**2. Estrategias.** Todas van en la misma dirección: **que el prompt pida lo que el contrato exige.** Es un patrón que el proyecto ha encontrado cuatro veces.

| Medida | Qué hace |
| --- | --- |
| **Decir en el prompt qué campos admite el esquema** | F-62: el planificador inventó un campo porque nadie le dijo cuáles había. Dos rondas perdidas |
| **Pasar el rango de palabras al Escritor** | Un intento fuera de rango es una delegación entera tirada por un número que se puede decir |
| **Falsos positivos de los guardrails** | F-59 costó dos reescrituras y una parada. La prueba que lo cierra —contrastar la lista de vetadas contra las palabras más frecuentes del español— caza la familia entera |
| **Reescritura parcial en lugar de capítulo completo** | Un hallazgo de una frase no necesita reescribir 1.300 palabras |
| **Devolver los hallazgos del intento anterior** | Ya existe el canal `problemas`. Sin él, la reescritura repite el error |

**3. Ahorro / esfuerzo.** Prompts que piden lo que el contrato exige: **ahorro alto, esfuerzo muy bajo** — es redactar. Falsos positivos: **alto / bajo**. Reescritura parcial: **medio / alto**, y toca la verificación byte a byte del manuscrito.

**4. Riesgos.** Bajos, y en su mayoría **negativos**: menos reintentos por causas espurias mejora la calidad, no la empeora. La excepción es la reescritura parcial ⚠️: un texto cosido de dos generaciones puede perder la voz, y el validador que compara el manuscrito con el borrador auditado exige identidad byte a byte.

**5. Prioridad. La primera junto con A.** Es la que mejor relación ahorro/esfuerzo tiene: casi todo es redactar prompts.

---

### D · Reparto de modelos por tarea

**1. Situación.** Escritor con Fable, Editor y Juez con Opus 5.5, Resumidor con Haiku. El reparto de coste es 75 / 17 / 7.

El dato que lo gobierna: **los tokens no predicen el coste.** El Resumidor gastó más tokens que el Juez y costó menos de la mitad. Cualquier razonamiento por volumen es inválido aquí.

Y hay una restricción que no es de coste: el modelo del Juez **se fija dentro de una obra**, porque si cambia a mitad, dos capítulos dejan de ser comparables y nada lo avisaría. Además Fable enruta, así que una delegación puede tocar dos modelos legítimamente.

**2. Estrategias.**

| Medida | Qué hace |
| --- | --- |
| **Escritor: mantener el modelo capaz** | Es el 75% del coste y es donde se juega la calidad. Abaratar aquí es el clásico ahorro que se paga en reescrituras |
| **Modelo barato para tareas mecánicas** | El Resumidor ya está en Haiku. Revisar si el Revisor del plan y la extracción de hechos del texto libre también pueden bajar |
| **⚠️ Editor a un modelo más barato** | 17% del coste, pero el Editor es lo que sostiene la calidad narrativa que el enunciado exige. No recomendado sin medir el acuerdo con la revisión humana |
| **Modelo barato en el primer intento, capaz en el segundo** | Idea atractiva y peligrosa: si el barato falla más, el coste sube |

**3. Ahorro / esfuerzo.** Bajar las tareas mecánicas: **ahorro bajo-medio, esfuerzo bajo** (una variable de entorno). Tocar Escritor o Editor: **ahorro medio, riesgo alto**.

**4. Riesgos.** Altos donde más tienta. El Editor juzga la calidad narrativa, y ya hay un punto ciego declarado: **el Editor juzga el antes y el después del tuning**, así que la revisión humana es la segunda fuente. Degradarlo sin medir el acuerdo con esa revisión rompe la única referencia externa que hay.

**5. Prioridad. Tercera.** Ahorro modesto y el riesgo está mal repartido: lo barato de cambiar ahorra poco, lo que ahorraría es lo que no conviene tocar.

---

### E · Validación y juicio

**1. Situación.** El proyecto ya ha recorrido este camino tres veces: **INV-03, INV-11 e INV-14 eran comparaciones disfrazadas de juicio.** INV-14 pedía un juez para comprobar si una lista de números decrece. INV-11 es un conteo. INV-03 es en su mayor parte comparar identificadores del registro de conocimiento.

Reclasificarlas hizo dos cosas a la vez: quitó llamadas al modelo y encogió el punto ciego de que la única puerta bloqueante dependiera de un juez cuya fiabilidad no está medida.

**2. Estrategias.**

| Medida | Qué hace |
| --- | --- |
| **Seguir buscando juicio que es comparación** | Ya hay tres casos; el patrón no se ha agotado |
| **Regla primero, juez solo de desempate** | Es la forma de INV-03 hoy: la comparación determinista caza todo lo declarado y el juez solo ve lo que la regla no puede |
| **Puertas deterministas antes del juez** | Un capítulo que falla una puerta de código no necesita gastar un Editor |
| **Aislar a los jueces** | Doble efecto: más barato (4× medido) y mejor juicio, porque un desempate que ve lo mismo que la regla confirma en vez de desempatar |
| **⚠️ Reducir los criterios del Editor** | Seis notas cuestan más que tres. Pero saltarse un criterio no dice que ese criterio esté bien |

**3. Ahorro / esfuerzo.** Reclasificar: **ahorro medio, esfuerzo medio** — cada una necesita spec de dominio. Orden de puertas: **medio / bajo**. Aislamiento: ya contado en A.

**4. Riesgos.** **Bajos, y esta categoría mejora la calidad mientras ahorra.** Una regla determinista es reproducible y un juez no: la decisión 9 del sistema anterior demostró que sin poder fijar la temperatura, la puntuación deja de ser una medida y pasa a ser una comparación dentro de una misma generación.

El riesgo real es el contrario: **reclasificar a regla algo que sí necesitaba criterio**. Mitigación, ya aplicada — la regla no sustituye al juez, lo antepone.

**5. Prioridad. Segunda.** Ahorra y mejora a la vez, que es raro.

---

## Fase 4 · Roadmap

### Dependencias

```
Medir el contexto enviado (F-58) ──┬──► decidir el reparto (B)
                                   └──► decidir qué se recorta

Auditar CLAUDE.md por agente (A) ──────► aislamiento del Resumidor y el Revisor

Prompts que piden lo que el contrato exige (C) ──► menos rondas de plan
                                                └──► menos intentos del Escritor

Reclasificar juicio→regla (E) ──────────► menos llamadas al Juez
```

**Solapamientos resueltos:** el aislamiento de agentes aparecía en A y en E; se cuenta en A y E solo hereda su beneficio. La reducción del bloque Local aparecía en B y arrastra a C; se descarta por eso.

---

### Fase I · Ganancias rápidas (sin tocar la calidad)

| # | Acción | Categoría | Ahorro | Esfuerzo |
| --- | --- | --- | --- | --- |
| 1 | Auditar qué `CLAUDE.md` ve cada agente y aislar a los que no lo necesitan | A | Alto | Bajo |
| 2 | Decir en cada prompt qué campos admite su contrato | C | Alto | Muy bajo |
| 3 | Pasar el rango de palabras al Escritor | C | Medio | Muy bajo |
| 4 | Cerrar los falsos positivos de los guardrails con la prueba de la lista completa | C | Medio | Bajo |
| 5 | Instrumentar la medida del contexto enviado | B | — | Bajo |

Las cinco son redacción o configuración. **Ninguna toca la calidad narrativa**, y las tres de la categoría C la mejoran, porque quitan reintentos por causas espurias.

### Fase II · Mejoras estructurales

| # | Acción | Categoría | Depende de |
| --- | --- | --- | --- |
| 6 | Prefijo estable en el prompt para maximizar `cache_read` entre capítulos | A | 1 |
| 7 | Ajustar el reparto por niveles a lo medido | B | 5 |
| 8 | Seguir reclasificando juicio que es comparación | E | — |
| 9 | Puertas deterministas antes de llamar al Editor | E | — |
| 10 | Recuperación por similitud en vez de todas las fichas | B | 5, 7 |

### Fase III · Optimización continua

| # | Acción | Condición |
| --- | --- | --- |
| 11 | Bajar el modelo de las tareas mecánicas restantes | Medir antes que no sube la tasa de rechazo |
| 12 | ⚠️ Reescritura parcial en vez de capítulo completo | Resolver la verificación byte a byte del manuscrito |
| 13 | ⚠️ Revisar el modelo del Editor | Solo con el acuerdo Editor–humano medido |

---

### KPIs

| Indicador | Cómo se mide | Por qué |
| --- | --- | --- |
| **Coste por capítulo aceptado** | USD por capítulo que pasa todas las puertas | El indicador principal. Un capítulo barato que se rechaza cuesta más que uno caro que pasa |
| Intentos por capítulo | Media de delegaciones del Escritor por capítulo aceptado | Aísla el gasto de la categoría C |
| Rondas de plan | Rondas hasta aprobar | Mide directamente la acción 2 |
| Ratio caché / salida | Tokens de creación de caché entre tokens de salida | Mide A. Hoy es 8:1 |
| `cache_read` entre capítulos | Tokens leídos de caché por capítulo | Mide la acción 6 |
| Coste por agente | Reparto porcentual | Detecta si la auditoría cambia el peso relativo |
| **Incidencias de continuidad** | Hallazgos bloqueantes por novela | **El freno.** Si sube mientras el coste baja, la optimización está pagándose con calidad |
| Nota media del Editor por criterio | Antes y después de cada medida | Segundo freno, con la revisión humana como referencia externa |

**Regla de parada:** cualquier medida que baje el coste y suba las incidencias de continuidad o la nota del Editor se revierte. El ahorro no es el objetivo; el coste por capítulo aceptable sí.

---

## Resumen ejecutivo

El coste de este sistema no está en escribir, está en **montar el contexto**: ocho tokens de creación de caché por cada uno de salida. La evidencia más fuerte ya está medida — aislar al Juez de `CLAUDE.md` lo hizo cuatro veces más barato, y esa decisión se había tomado por corrección, no por coste.

Por eso la primera fase es auditar qué lee cada agente y arreglar los prompts que no piden lo que el contrato exige, que es lo que ha causado reintentos pagados en las dos últimas ejecuciones. Son medidas de redacción y configuración, sin riesgo para la novela, y varias **mejoran la calidad** al eliminar rechazos espurios.

Lo que no se toca todavía: el contexto ocupa el 4,4% del techo, así que optimizar el ensamblado es optimizar lo que no duele, y el número que lo sostiene está sesgado a la baja hasta que se mida el contexto enviado de verdad. Y el Escritor, que es el 75% del gasto, es también donde se juega la calidad que el encargo pone al mismo nivel que la personalización.
