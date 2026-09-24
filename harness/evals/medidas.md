# Medidas, y qué mide cada una

De la misma ejecución salen cifras que no valen lo mismo. Este documento las
pone juntas **con la distinción explicada**, porque separar qué mide cada
número de una misma generación es lo único que impide que una cifra válida
preste credibilidad a otra que no lo es.

## Primera obra de diez capítulos

Medido en solo lectura sobre `backend/obra10.db` el 2026-09-23, **con la
generación aún en curso**, tras el capítulo 8.

> **Corrección (2026-09-24).** La primera columna se presentaba como la medida de la obra y era una lectura a mitad de generación. La columna *Al terminar* sale de `salida/novela-1/obra10.log` (no versionado) y de `obra10.db`.

| Cifra | Tras el capítulo 8 | Al terminar | ¿Qué mide? |
| --- | --- | --- | --- |
| Escenas | 54 consolidadas | **55 de 60**; se paró en `cap-10-e2` por `INV-03` | **Válida.** Producción real, de una obra **sin terminar** |
| Borradores | 54 | 57 | **Válida** |
| Coste | 21,6 USD | **26,0372 USD, un suelo**: 10 de 169 delegaciones sin coste | **Suelo** de lo que costó llegar hasta ahí |
| Paradas | 0 | 2 por `INV-03`, una desatascada con instrucción | **Válida** |
| Hallazgos | **0** | 2, los dos `INV-03` `bloqueante` | **NO vale como medida de calidad** |

### Por qué el coste sí y el cero de hallazgos no

**El coste es una medida, pero es un suelo y de una obra sin terminar.**
26,0372 USD se obtuvo sumando el coste real por delegación, y a 10 de las 169
no se les leyó coste, así que el real es mayor. Mide lo que costó escribir 55
escenas de 60 con esta escalera de modelos, no lo que cuesta una novela, y
menos la novela regalo, que tiene otros agentes (`SPEC-31`).

**Cero hallazgos no mide la calidad de la obra: mide que las puertas no
tuvieron nada que rechazar.** Son dos afirmaciones distintas y solo la segunda
es cierta aquí. Comprobado, no supuesto:

- Los diez `hecho_canonico` quedaron todos bajo `obra='cap-10'`, así que los
  capítulos 1 a 9 generaron con *«hechos: (ninguno)»* e **`INV-03` no tuvo un
  solo hecho que comprobar**.
- Hay **dos entidades** en toda la novela, las dos `vivo`, así que la mitad de
  `estado_vital` de `INV-02` **no podía fallar**.
- La base tiene **diez obras de seis escenas** —`obra='cap-01'`…`'cap-10'`—
  porque el guion modelaba una obra por capítulo. De ahí que `escena.capitulo`
  esté a `None`: la identidad del capítulo viajaba en la columna `obra`.

Es `F-30` a escala de obra: **un validador que no puede dispararse no está
midiendo cero.** Queda registrado en `F-52`.

### La verificación formal no pudo decir nada, y no por falta de tablas

`evento_cronologico` no existe en esa base, pero **aunque hubiera existido no
habría servido**: se consulta con `WHERE obra = ?`, y con una obra por
capítulo cada capítulo habría sido su propia cronología. No habría habido **un
solo par que comparar** entre capítulos, que es justamente lo que las cuatro
invariantes miran.

No era un problema de tablas ausentes: **era el modelado**.

## Cómo presentar esto

Las dos cifras juntas y con la distinción dicha en una línea. Algo así:

> La primera obra de diez capítulos costó **al menos 26,04 USD** y escribió 55
> escenas de 60 antes de pararse en el último capítulo por `INV-03`. Hasta el
> capítulo 8 llevaba **cero hallazgos**, y ese cero
> **no es una medida de calidad**: los hechos del canon quedaron todos bajo el
> último capítulo y la novela solo tiene dos personajes, los dos vivos, así
> que ni `INV-03` ni la mitad de `INV-02` llegaron a tener nada que comprobar.
> La repetición, con una sola obra de diez capítulos, es la primera en la que
> ese cero significará algo.

Presentar el coste solo sería quedarse corto; presentar el cero de
hallazgos como calidad sería falso. **Presentarlos juntos con la distinción es
lo que los hace creíbles a los dos**, y es el mismo criterio que este
proyecto aplica en `F-30`, `F-52` y la Regla 8.

## Lo que la repetición podrá medir y esta no

| | Primera obra | Repetición |
| --- | --- | --- |
| Acciones declaradas | **Desconocido** (sin `delta_de_escena`) | Contadas, con aviso si salen cero |
| Procedencia de la base | Ausente (ni `esquema_version`) | Commit y huella del brief |
| Tablas | 10 | 18, tras `migrar()` |
| `escena.capitulo` | `None` en todas | Relleno |
| Estructura | Diez obras de seis escenas | **Una obra, diez capítulos** |
| Cronología de fábula | Imposible por construcción | Medible por primera vez |


## R0 · Primera ejecución real aceptada de la novela regalo (2026-09-24)

`novela_regalo.py ejemplos/brief-ejemplo.json --capitulos 1 --base ejemplo.db --obra
obra-ejemplo`, con el código del commit `186c55f` de la rama `examen-cierre`, leído de la
procedencia de la base (`procedencia.version_del_harness`). Datos inventados.

| Cifra | Valor | ¿Qué mide? |
| --- | --- | --- |
| Rondas del plan | **1** | El plan se aprobó a la primera (tras `F-62` y `F-68`) |
| Capítulo 1 | **aceptado**, 1.102 palabras (`corta`: 1.000–1.150) | Primera escena de la novela regalo que llega a consolidarse |
| Delegaciones | 5, **todas con coste medido** | Planificador, Revisor, Escritor, Editor, Resumidor |
| Coste | **2,1650 USD** | Leído del sobre de cada delegación. Langfuse suma lo mismo: 2,165 |
| Tiempo | 426 s | Del plan al resumen del capítulo 1 |
| Contexto enviado | 620 tokens estimados | Primer capítulo: sin capítulo anterior ni resúmenes, **sesga a la baja** |
| Hooks | `validar_capitulo` sobre el Escritor, código 0; `policy` 3 veces sobre el Escritor y 4 sobre el Editor, código 0 | **Primera vez** que los dos hooks actúan sobre un capítulo real |
| Tools | 7 llamadas: el Escritor `ficha` ×3 (`ok`); el Editor `ficha` ×2 (`no_existe`), `hechos` y `cronologia` (`ok`) | Primera ejecución real de las tools (`PLAN-28` E10) |
| Cronología y usos | 1 evento, 2 participaciones; 3 usos de hecho | Primeras filas reales de `evento_cronologico` y `uso_de_hecho` |
| Langfuse | 15 observaciones en la sesión de la obra: 5 de rol con coste, 7 de tool, 3 de grupo | `PLAN-29` E13(b) |

**Lo que no vale como medida de calidad:** `INV-26` salió `sin_veredicto` (`F-76`) y el
Resumidor falló (`F-77`), así que este capítulo **no lo juzgó el Editor** y quedó sin resumen.
Los dos están arreglados después de esta ejecución. Su coste **no se multiplica por diez** para
presentarlo como coste de una novela (`PLAN-31` R0).

### El gasto de diagnóstico después de R0

Tres delegaciones sueltas, sobre el texto del capítulo 1 de `R0`, para comprobar los arreglos
antes de gastar una novela entera. Todas con coste medido:

| Delegación | Para qué | USD |
| --- | --- | --- |
| Resumidor, prompt viejo | Ver qué devolvía (`F-77`) | 0,05233 |
| Resumidor, prompt nuevo | Comprobar el arreglo de `F-77` | 0,05208 |
| Editor | Comprobar el arreglo de `F-76` | 0,1384975 |

**Gastado hasta aquí contra el techo de 150 USD de `SPEC-31`**: 2,1650 de `R0` más 0,2429 de
diagnóstico, **2,4079 USD**. Es la suma de lo leído; no incluye ninguna ejecución de otras
sesiones.

## R1 · La novela de ejemplo, completa y publicada (2026-09-24)

`evaluar.py harness/evals/brief-base.json --pasada antes --confirmo-el-gasto`, y después
`--reanudar brief-base-antes-1`. Datos inventados (`ejemplos/brief-ejemplo.json`). Obra
`brief-base-antes-1`, en su propia base.

| Cifra | Valor | ¿Qué mide? |
| --- | --- | --- |
| Rondas del plan | **1** | Aprobado a la primera |
| Primera ejecución | 8 capítulos, parada en el 9 por `INV-02` (`F-79`) | El reencuentro que la regla no dejaba escribir |
| Reanudación | capítulos 9 y 10 y la puerta | **El checkpoint, ejercido por primera vez con datos reales**: no se volvió a planificar, y el `INV-02` del intento parado quedó `resuelto` (`F-118`) |
| Publicación | **publicada**, ronda 1 de la puerta, Lean `0` | Primera versión de una novela regalo que pasa la puerta |
| Coste de la novela entera | **16,8905 USD en 36 delegaciones, todas con coste medido** | Libro de gasto y Langfuse, iguales. Incluye el plan, los diez capítulos, el intento parado del 9 (1,107342) y el cierre |
| Tiempo | 1.949 s la primera ejecución y 462 s la reanudación | Sin las decisiones y arreglos de en medio |
| Hallazgos abiertos | 2 `INV-17` `mayor` (capítulos 3 y 5, fuera del rango de palabras) y 7 `INV-25` `menor` | No bloquean la publicación |

**Cómo leer el coste.** Es una novela, no una media: con el Editor juzgando de verdad, cada
capítulo puede pedir hasta tres reescrituras, y cuántas pide cambia de brief a brief. Es la cifra
que el libro usa como «mayor coste medido de una novela completa» para decidir cuántos briefs caben.

**Lo que no está limpio, dicho.**
- **Dos códigos.** Los capítulos 1 a 8 se escribieron con `f986cf5`; el 9, el 10 y la puerta, con
  `8ed4680` (con los arreglos de `F-79`, `F-113`, `F-117` y `F-118`). La procedencia de la base
  guarda una sola versión y no pisa, así que dice `f986cf5` para toda la obra: **es una limitación
  conocida** (la procedencia es una por base; `PLAN-23` hallazgo 18).
- **El libro se reparó a mano**, con `anotar`, tras `F-119`. Cuadra con Langfuse, que no se tocó.
- **La traza del intento parado del 9 se perdió** (`F-120`); su coste no.

## Concurrencia: dos ejecuciones a la vez caben en 100.000 tokens (2026-09-24)

Regla del autor: en serie, salvo que la medida diga que dos a la vez caben. Medido sobre las 36
delegaciones de `R1`:

| Cifra | Valor |
| --- | --- |
| Lo que ensambla el harness por delegación (`tokens_para_recortar`), máximo | 3.264 |
| Entrada más salida del sobre por delegación (`tokens_estimados`), máximo | 8.696 (Escritor; Editor 4.552, Resumidor 4.580) |
| Contexto propio de Claude Code en caché, en una delegación medida (`cache_creation_input_tokens`) | 21.231 |
| **Dos ejecuciones a la vez, cota** | 2 × (8.696 + 21.231) = **59.854** |

Cabe con holgura, así que los cuatro briefs van **de dos en dos**. La cota sesga **al alza**: suma
el máximo de cada agente como si coincidieran, y la caché de Claude Code de una sola delegación.

## INV-30 en real, sobre la novela de ejemplo (2026-09-24)

`inspeccion_visual.py ejemplo-web.db brief-base-antes-1 http://127.0.0.1:5173/obras/brief-base-antes-1`,
con la web servida sobre una **copia** de la base de `R1`. **Falla**, y con dos defectos reales:

| Pieza | Veredicto | Motivo |
| --- | --- | --- |
| portada | pasa | Título y dedicatoria enteros |
| índice | pasa | Los diez capítulos en orden, con estado y hallazgos |
| capítulos | **falla** | `F-141`: la frase repetida de `INV-25` sale normalizada |
| fichas | **falla** | `F-142`: Cloe está en el capítulo 10 y su ficha no lo enlaza |
| enlaces | pasa | Cada enlace lleva a su capítulo, y el capítulo contiene a la entidad |

Coste de la delegación: 0,6958668 USD. Es el primer fallo real de `INV-30`: un validador que
no había podido fallar hasta ahora (`F-84`: la primera inspección dio por buena una web con
tres defectos).

## R2 · Inyección, pasada «antes»: la entrevista no cerró (2026-09-24)

El detector cazó la inyección reconocible con el modelo real y descartó ese texto libre. La
entrevista no cerró por `F-140`, así que **no hay novela**. 1,6246488 USD en 14 delegaciones.

## R3 · El brief temporal: el Revisor cazó las incoherencias en el plan (2026-09-24)

El plan no se aprobó en tres rondas de revisión (cinco versiones: una rechazada por la
cobertura, dos por el esquema —que no gastan ronda desde `F-68`— y dos por el Revisor). **Las
objeciones del Revisor son las incoherencias temporales que el brief provoca**: *«Incoherencia
temporal dentro de la línea de 2019, entre cap-02 y cap-04»*, una muerte situada en un año que
choca con capítulos anteriores en la fábula, y la alternancia de líneas rota. **No se escribió
novela**, así que Lean no tuvo eventos que mirar. Para `EX-15` es la justificación que pide el
enunciado: la incoherencia la paró un validador anterior —el semántico del plan— y por eso Lean
no la detectó. 4,9492 USD en 7 delegaciones. El informe se perdió por `F-143`, ya cerrado.

## R5 · Vetadas por variantes: parada en el capítulo 2 por `INV-03` (2026-09-24)

Capítulo 1 consolidado; capítulo 2 parado: *«Luisa actúa sobre `imp-01` y no consta que lo
conozca»*. **Ninguna coincidencia vetada**: el Escritor esquivó las variantes («hospitales»,
«Tórmenta», «Tomás»…) porque su prompt le da la lista, así que el guardrail no tuvo nada que
detectar. 3,8173 USD en 7 delegaciones. Se reanuda con `--reanudar`.
