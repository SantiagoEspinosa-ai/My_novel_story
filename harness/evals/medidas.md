# Medidas, y qué mide cada una

De la misma ejecución salen cifras que no valen lo mismo. Este documento las
pone juntas **con la distinción explicada**, porque separar qué mide cada
número de una misma generación es lo único que impide que una cifra válida
preste credibilidad a otra que no lo es.

## Primera obra de diez capítulos

Medido en solo lectura sobre `backend/obra10.db` el 2026-09-23, con la
generación aún en curso.

| Cifra | Valor | ¿Qué mide? |
| --- | --- | --- |
| Escenas consolidadas | 54 de 60 | **Válida.** Producción real |
| Borradores | 54 | **Válida** |
| Coste | **21,6 USD** | **Válida.** Lo que cuesta generar |
| Paradas | 0 | **Válida.** El pipeline no se atascó |
| Hallazgos | **0** | **NO vale como medida de calidad** |

### Por qué el coste sí y el cero de hallazgos no

**21,6 USD es una medida.** Mide lo que cuesta generar una novela de este
tamaño con esta escalera de modelos, se obtuvo sumando el coste real por
delegación, y sirve para decidir. Es un dato del informe.

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

> La primera obra de diez capítulos costó **21,6 USD** y produjo 54 escenas
> consolidadas sin una sola parada. Cerró con **cero hallazgos**, y ese cero
> **no es una medida de calidad**: los hechos del canon quedaron todos bajo el
> último capítulo y la novela solo tiene dos personajes, los dos vivos, así
> que ni `INV-03` ni la mitad de `INV-02` llegaron a tener nada que comprobar.
> La repetición, con una sola obra de diez capítulos, es la primera en la que
> ese cero significará algo.

Presentar el 21,6 USD solo sería quedarse corto; presentar el cero de
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
