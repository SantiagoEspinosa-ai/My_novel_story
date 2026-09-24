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
