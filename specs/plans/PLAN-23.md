---
id: PLAN-23
spec: SPEC-23
titulo: Implementación de la regeneración en una obra acumulativa
estado: aprobada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 1
---

# PLAN-23 — Regenerar en una obra acumulativa

> **Aprobado (2026-09-24)** con `C-1` a `C-6`, **y con el renombrado dentro**: el ejemplo del
> enunciado es *«el perro se llama Nala»*, y un `409` en la demo es el peor sitio donde
> descubrirlo. `C-4` queda reescrita abajo con la vía mínima, que no versiona la story bible.

Cómo se construye `SPEC-23` v2. Cada paso empieza por la prueba que falla, deja las pruebas
actuales en verde y se puede commitear solo. **Ningún paso llama al modelo real**: todo va
contra bases en memoria con dobles, salvo B4, que gasta dinero y necesita un sí explícito. La
medida (B1) no gasta: lee tablas.

## Reparto con `PLAN-22`

Los dos planes se prepararon a la vez. Queda así:

- **Los endpoints de la petición y de las versiones son de este plan** (A5, A7). La petición
  recibe un **hecho**, no un ancla de texto, así que no espera a `SPEC-22` `DA-6`. La página
  (`PLAN-22`) traduce la selección del lector a los hechos que usa esa escena, y consume estos
  endpoints.
- **El contrato congelado es de `PLAN-22` E1**, que va antes que A5. Desde entonces cada endpoint
  de este plan actualiza el congelado en su mismo commit (`RF-33`).
- **Las filas `VER` de este plan son `VER-113`…`VER-118`** (a reservar). `PLAN-22` usa
  `VER-102`…`VER-112`, y `PLAN-29` reservó `VER-94`…`VER-101`.

## Cómo se reparte: Parte A y Parte B

`SPEC-23` v2 se aprobó **antes** de la medida para que lo común a `S-1` y `S-2` se pueda
construir ya. El plan sigue ese corte.

| Parte | Qué | Depende de | Cuándo |
| --- | --- | --- | --- |
| **A** | Lo que necesitan las dos salidas: la herramienta de medida, el delta y la reconstrucción del estado (`G-05`), versiones con identidad (`D-2`), reverificación (`D-1`), «qué cambió», lecturas por versión, la petición y los endpoints | Nada: todo con datos de fixture | Ahora, en orden |
| **B** | La medida sobre la novela de ejemplo, fijar la salida y **la rama que la medida elija**, escrita para `S-1` y para `S-2` | La novela de ejemplo completa y la Parte A | En cuanto exista el número, sin volver a planificar |

**El corte mínimo del día es A0–A5.** No tocan la generación. Si el día no da para más, el
repositorio queda con la medida lista, versiones con identidad, reverificación y lectura de
versiones, y sin ninguna función a medias expuesta. A6 y A7 hacen falta antes de cualquier rama
de B.

**Hoy `uso_de_hecho` tiene 0 filas en todas las bases reales**, porque nunca se consolidó un
capítulo de la novela regalo. Por eso la medida se construye y se prueba en A1 con fixture, y se
ejecuta en B1.

## Lo que se encontró al preparar el plan

1. **`G-05` está cerrado en el código, y `SPEC-23` dice que no.** `SPEC-23` afirma que no hay
   ninguna tabla que guarde el delta y trata guardarlo como trabajo pendiente. Pero existen
   `consolidacion/deltas.py` (la tabla `delta_de_escena`) y su escritura dentro de la transacción
   (`consolidacion/aplicar.py:149`), y `SPEC-22` lo marca **Cerrado**. De `G-05` falta menos: la
   reconstrucción del estado (A2).
2. **El guion de la obra larga lee una columna que no existe.** `backend/obra_diez_capitulos.py:242`
   hace `SELECT delta FROM delta_de_escena`, y la columna se llama `contenido`. En cuanto haya una
   fila, ese informe muere con `OperationalError`. Hoy no se ve porque la tabla está vacía.
3. **`VER-09` describe un aplicador de referencia que no se ha encontrado** en
   `features/consolidacion/tests/`. Reconstruir el estado desde un punto es justo lo que `VER-09`
   prometía comprobar, así que A2 lo escribe.
4. **Un capítulo nuevo en la misma posición borraría al anterior sin avisar.** `capitulo` tiene
   `UNIQUE (obra, orden)` (`brief/repository.py:28`), y `alta_de_obra` escribe con
   `INSERT OR REPLACE` (`:105`). El `REPLACE` resuelve el choque **borrando** la fila que ya ocupaba
   esa posición. Es la **Regla 7**: el capítulo 3 de `v1` desaparecería al escribir el capítulo 3
   de `v2`. A3 recrea la tabla sin esa restricción.
5. **Casi todo lo que lee «las escenas de la obra» mezclaría dos versiones.** Filtran por `obra`:
   `escaleta/repository.py` (`escenas_de`, usada en `orquestacion/obra.py`, `novela.py`,
   `publicacion.py` y `story_bible.py`), `asignar_t_discurso`, la escena previa de
   `reunir_material`, `memoria.resumenes_hasta` y `fichas_en`, y el manuscrito. Con una sola
   versión todo pasa **por coincidencia** (Regla 11). Con dos, el Escritor recibiría el resumen del
   capítulo sustituido y el manuscrito tendría dos capítulos 3. Lo arregla A6.
6. **Los imprescindibles se asignan por un identificador construido.** `novela.py` los indexa por
   `"{capitulo}-e1"`. Una escena nueva de otra versión tiene otro identificador, así que `INV-23`
   **no se comprobaría** en los capítulos regenerados, y nada lo diría. Va en A6.
7. **Un hallazgo no sabe de qué versión es.** `hallazgo` guarda `escena` y nada más. Un fallo de
   reverificación de un capítulo compartido aparecería también en `v1`, y `v1` dejaría de poder
   cerrarse. Por eso la reverificación guarda sus resultados en una tabla propia (A4) y **no
   escribe en `hallazgo`**.
8. **El mundo vivo es uno por base.** `entidad` y `conocimiento` no tienen `obra` ni versión, y
   `mundo.leer` las lee enteras. Dos versiones no caben en esas tablas a la vez → `C-2`.
9. **La medida no cuenta sobre el texto aceptado en todos los capítulos.** `reescribir_capitulo`
   (la reescritura a delta fijo de `PLAN-30`) cambia `borrador_aceptado` sin volver a levantar el
   acta, y solo vuelve a registrar los imprescindibles. En un capítulo reescrito tras consolidar,
   las filas `menciona` son las del **primer** texto. La medida lo informa aparte (A1).
10. **`uso_de_hecho` no guarda la obra, y los hechos se identifican por obra.** Si la medida no
    filtra los usos por las escenas de la obra, mezcla los usos de dos obras con el mismo `id`.
11. **La lista de `menciona` para la regeneración se contradice en tres documentos.**
    `docs/definitions.md` y el docstring de `capitulos_a_regenerar` dicen que contar `menciona`
    *«reescribe media novela por una alusión de paso»*; `SPEC-21` C-2 dice que **entra, pendiente
    de medida**; y la medida de `SPEC-23` v2 se toma sobre `menciona`. `PARA_REGENERACION` sigue
    siendo `(ESTABLECE, DEPENDE)`. Hay **dos medidas de arrastre distintas**: la de `SPEC-21`
    (`arrastre_de_incluir_mencion`) mide cuánto se añade; la de `SPEC-23` es una media de capítulos
    distintos. No se sustituyen la una a la otra.
12. **`SPEC-22` no se actualizó con `SPEC-23` v2**: `DA-1` sigue con el umbral viejo y asume que
    `RF-50`…`RF-55` no se implementan; `docs/cobertura-examen.md` (`EX-14`) y
    `specs/tla/README.md` (`D-2`) dicen que `SPEC-23` está `en_revision`.
13. **`SPEC-23` tiene restos de v1 que contradicen su v2**: *«Nada del reparto»*; fuera de alcance
    *«elegir ya una de las cinco salidas»*; la tabla de preguntas repetida; y la fila 5, que dice
    que hoy no se puede medir cuando el apartado *«Dónde sí está la medida»* dice que sí.
14. **La definición de la medida tiene dos lecturas** → `C-1`.
15. **El ejemplo del enunciado es un cambio de nombre, y un nombre no se puede cambiar por
    versión.** `EXAMEN.md` pone *«el perro se llama Nala»*. `INV-22` compara los nombres con la
    story bible, que sale de `plan_de_obra`, por obra y no por versión; y un hecho ya usado por una
    escena consolidada **no se puede editar** (`edicion/permisos.py`). Cambiar un hecho tiene que
    valer solo en la versión nueva (A7). Renombrar es la cuestión abierta `C-4`.
16. **`D-2` y `S-2` chocan en los capítulos compartidos que estaban cerrados** → `C-5`.
17. **Una escena reverificada tiene dos estados, y ninguno es de `estado_de_escena`.** La
    verificación por versión necesita su propio vocabulario, **sin añadir ninguna transición a la
    máquina de estados**.
18. **La procedencia es una por base, no por versión.** Cada versión guarda su commit (A3). Es
    `MF-27` aplicado a las versiones.
19. **La publicación no sabe de versiones.** `veredicto_de_publicacion` tiene como clave
    `(obra, ronda)`. Este plan no hace la puerta por versión, pero A6 hace que el manuscrito lea la
    versión vigente y no las mezcle.
20. **Numeración.** La última migración es la **10**. Se usa el número libre **en el momento del
    commit**, y `validar_secuencia` caza uno repetido.

## Decisiones que la spec no toma y el plan necesita

Cada una con su propuesta. **Aprobar el plan es aprobar las propuestas**, salvo las que se
rechacen expresamente.

- **`C-1` · Qué hechos entran en la media** (bloquea A1). **Propuesta:** los que tienen al menos
  una fila de uso de cualquier tipo en las escenas de la obra; el numerador cuenta capítulos por
  `menciona`. Es la lectura literal, decidida antes de ver el número. Un hecho que solo se usa por
  `depende` aporta 0, con el sesgo a la baja que la spec ya declara. Los imprescindibles entran,
  con el reparto plan/imprescindible en el detalle. La herramienta imprime la media aprobada y el
  detalle por hecho, nunca dos medias.
- **`C-2` · Qué es el mundo vivo cuando hay dos versiones** (bloquea A6 y B). **Propuesta:** las
  tablas `entidad` y `conocimiento` son las de la versión que se está escribiendo. Antes de
  regenerar se rebobinan a la semilla más los deltas del prefijo (A2). Lo de las demás versiones se
  reconstruye cuando se necesita, porque es derivado. Coste: quien lea el mundo vivo sin pasar por
  la versión lee el de la última.
- **`C-3` · Qué identifica el estado contra el que se verificó** (bloquea A4). **Propuesta:** la
  huella es la lista ordenada de deltas aplicados antes de la escena, más la huella de la semilla.
  Un verde cuya huella no coincide con la de su versión **no cuenta**. Cierra la mitad de la
  decisión abierta de `docs/verification.md`: *qué identifica un estado*.
- **`C-4` · Qué se puede pedir** (bloquea A7). **Decidido por el autor:** dos clases de petición.
  - **Un hecho:** un cambio del `enunciado` de un `HechoCanonico` de la obra, con las palabras del
    lector. No se admite un hecho que ninguna escena de la versión usa.
  - **Un nombre:** el `nombre_canonico` de un `Personaje` de la obra pasa a otro. **La identidad
    del personaje no cambia** (`Personaje.id`), así que no hace falta versionar la story bible
    entera. La vía mínima tiene cuatro piezas:
    1. **Un nombre por versión, no por obra.** El renombrado vive en la petición, como el
       enunciado nuevo de un hecho, y los nombres de una versión son los del plan con los
       renombrados de su cadena de peticiones (`regeneracion.nombres_de_version`). La versión
       anterior conserva el suyo: sus fichas y su `INV-22` siguen leyendo el nombre viejo.
    2. **Lo afectado lo decide el texto, no el modelo.** Los capítulos que se tocan son los que
       contienen el nombre viejo, como palabra entera, en su texto aceptado, más aquellos en los
       que el personaje está presente (`personajes_presentes`, `PLAN-27` E3). Con `S-1`, desde el
       primero de ellos hasta el final; con `S-2`, exactamente esos, y el resto se reverifica.
       Un capítulo compartido no puede contener el nombre viejo, por construcción.
    3. **El nombre viejo, vetado en la versión nueva.** Entra como nombre vetado de nivel novela
       (`SPEC-25`) solo para los capítulos de la versión nueva: si el Escritor lo arrastra, `INV-21`
       lo devuelve, que es la regla que ya sabe hacerlo.
    4. **El material del Escritor, con el nombre nuevo.** La sinopsis y los beats del plan, y los
       enunciados de los hechos, salen con la sustitución hecha para los capítulos regenerados. Si
       no, el prompt le pediría el nombre viejo y el punto 3 lo rechazaría hasta agotar el tope.
  - **No se admite:** renombrar al **destinatario**, cuyo nombre es un dato de la ficha del
    comprador y no del plan; ni un nombre nuevo que ya sea de otro personaje de la obra. Los dos
    responden `409` con su motivo.
- **`C-5` · Un capítulo compartido y `cerrado` que falla la reverificación** (solo `S-2`).
  **Propuesta:** no se reabre (`RF-30`, `VER-29`). En la versión nueva sale como no verificado,
  con sus hallazgos de versión (`RF-54`), y la salida es una petición nueva que lo incluya.
- **`C-6` · Identificadores de lo nuevo.** **Propuesta:** capítulo
  `{capitulo_de_origen}-v{numero}` y escena `{capitulo_nuevo}-e1`, con la comprobación de choque de
  `alta_de_obra`. La escena nueva hereda el `t_discurso` de la que sustituye.

## Lo que hay que añadir antes a `docs/definitions.md`

Ninguno de estos nombres existe hoy. **Son propuestas y entran en A0**, antes de cualquier código.

| Qué | Dónde | Atributos (propuestos) |
| --- | --- | --- |
| Clase `VersionDeObra` | Plano Obra | **obra** → Obra, **numero** (la identidad; la `ronda` de `CE-5`), anterior → VersionDeObra, **capitulos[]** → Capitulo (en orden, compartidos por referencia), peticion → PeticionDeCambio, **commit** (`MF-27`), creada_en |
| Clase `PeticionDeCambio` | Plano Proceso | **obra**, **version_de_partida** → VersionDeObra, **clase** → `clase_de_peticion`, hecho → HechoCanonico, enunciado_nuevo, personaje → Personaje, nombre_nuevo, **texto** (las palabras del lector), salida → `salida_de_regeneracion`, capitulos_propuestos[] → Capitulo. Con `hecho`, lleva `hecho` y `enunciado_nuevo`; con `nombre`, `personaje` y `nombre_nuevo` |
| Enumeración `clase_de_peticion` | Vocabularios | `hecho`, `nombre` (`C-4`) |
| Clase `Reverificacion` | Plano Calidad | **version** → VersionDeObra, **escena** → Escena, **huella_del_estado**, **estado** → `estado_de_verificacion`, hallazgos[] (de esta versión; no son filas de `Hallazgo`) |
| Enumeración `salida_de_regeneracion` | Vocabularios | `cascada` (`S-1`), `selectiva` (`S-2`) |
| Enumeración `estado_de_verificacion` | Vocabularios | `verificada`, `sin_reverificar` (heredada: **no cuenta como verde**, `D-1`), `fallida` |
| Relación `incluye` | Relaciones | VersionDeObra → Capitulo, N:M (+ `orden`). No basta `contiene`: un capítulo compartido está en dos versiones |
| `EstadoDelMundo.huella` | Plano Mundo | La lista de deltas aplicados, en orden, más la semilla (`C-3`) |
| `DeltaDeEscena.version` | Plano Proceso | Ya es columna (`consolidacion/deltas.py`) y la definición no la lleva |
| Corrección del párrafo de `menciona` | `docs/definitions.md` | Que diga lo de `SPEC-21` C-2 (hallazgo 11) |

Los dos vocabularios van también a `commons/dominio/enumeraciones.py`, su único sitio en el código.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `orquestacion/arrastre.py` (nuevo) | `medir(con, obra)`: la medida de `SPEC-23` v2 |
| `backend/medir_arrastre.py` (nuevo) | La medida desde la terminal, con salida JSON y código de salida |
| `consolidacion/mundo.py`, `consolidacion/deltas.py` | `acumular(semilla, deltas)` puro, `rebobinar(con, mundo)`, leer los deltas de una lista de escenas |
| `brief/repository.py` | `version_de_obra`, `capitulo_de_version` y la recreación de `capitulo` |
| `revision/repository.py` (nuevo) | `peticion_de_cambio` |
| `verificacion/repository.py` (nuevo) | `reverificacion` |
| `orquestacion/regeneracion.py` (nuevo) | Semilla, reverificar, comparar versiones, escenas por versión, la propuesta, `SALIDA` y las dos ramas |
| `orquestacion/router.py`, `orquestacion/schemas.py` (nuevo) | Los endpoints de la tabla de abajo |
| `commons/db/migraciones.py` | Una migración por tabla o columna nueva, para que `esquema_version` diga cuándo apareció (`VER-21`) |

## Endpoints

Las rutas son propuesta. `RF-57` vale para todas: ninguna expone modelos, topes ni la ruta de la base.

| Método y ruta | Para qué | Requisito |
| --- | --- | --- |
| `POST /obras/{id}/cambios/propuesta` | Con `{hecho, enunciado_nuevo, texto}` devuelve la salida, **los capítulos que se van a tocar**, la promesa y su punto ciego. Síncrona y **sin modelo** | `RF-51`, `RF-55` |
| `POST /obras/{id}/cambios` | La misma petición más la lista propuesta que el lector acepta. `202` con el identificador de trabajo. `409` si no hay salida elegida, si la lista cambió desde la propuesta o si pide algo que `C-4` excluye | `RF-48`, `RF-50` |
| `GET /obras/{id}/versiones` | Las versiones con `numero`, `anterior`, `commit`, `creada_en` y la petición | `RF-53` |
| `GET /obras/{id}/versiones/{numero}` | Capítulos en orden: si cambió respecto a la anterior o es compartido, `estado_de_capitulo`, y por escena `estado_de_escena` **y** `estado_de_verificacion` | `RF-52`, `RF-53`, `RF-54` |
| `GET /trabajos/{id}` | Seguir la regeneración | Ya existe |

**Nadie consume hoy la cola de trabajos** (hallazgo 10 de `PLAN-22`): el trabajo de regeneración
necesita su worker, y es de este plan (A7).

## Pasos — Parte A (común a las dos salidas)

### A0 · El dominio primero

`docs/definitions.md` con todo lo de la tabla de arriba; `commons/dominio/enumeraciones.py` con
`SalidaDeRegeneracion` y `EstadoDeVerificacion`.

**Prueba que falla primero:** `test_los_valores_de_estado_de_verificacion_son_los_de_definitions`.
Además `test_los_valores_de_salida_de_regeneracion_son_los_de_definitions`.

### A1 · La herramienta de medida, antes que nada

`arrastre.medir(con, obra)`:

1. **Obra completa**: toda escena de la obra ya hecha y todo capítulo con al menos una escena. Si
   no, se niega con la lista de lo que falta.
2. **Hechos y usos**: los hechos declarados de la obra y, por hecho, sus usos `menciona`
   **filtrados por las escenas de la obra** (hallazgo 10).
3. **Capítulos por hecho**: capítulos distintos no nulos, y aparte los usos sin capítulo.
4. **La media**, sobre los hechos de `C-1`. Si ningún hecho tiene usos, se niega.
5. **Procedencia**: el commit de la base. Si falta o es `sin_determinar`, **se niega** (`MF-27`).
6. **La salida**: **≤ 3 → `S-1`; > 3 → `S-2`**.
7. **El resultado**: el número con numerador y denominador, la obra, el commit, la salida, el
   detalle por hecho, las escenas reescritas tras consolidar (hallazgo 9) y, **en el mismo objeto**,
   `"sesgo": "a la baja, hacia S-1"`.

`medir_arrastre.py --base --obra` imprime ese objeto y sale con 0 si midió y con 1 si se negó. No
escribe en la base.

**Ficheros:** `orquestacion/arrastre.py`, `orquestacion/tests/test_arrastre.py`,
`backend/medir_arrastre.py`.

**Prueba que falla primero:** `test_la_media_cuenta_capitulos_distintos_por_mencion`. Además
`test_dos_menciones_en_el_mismo_capitulo_cuentan_uno`,
`test_con_exactamente_3_sale_s1_y_con_algo_mas_sale_s2`,
`test_una_obra_incompleta_no_se_mide_y_dice_que_falta`, `test_sin_ningun_hecho_con_usos_no_se_mide`,
`test_los_usos_de_otra_obra_con_el_mismo_id_de_hecho_no_cuentan`, `test_sin_procedencia_no_se_mide`,
`test_el_resultado_lleva_la_direccion_del_sesgo`,
`test_un_capitulo_reescrito_tras_consolidar_se_informa_aparte` y `test_medir_no_escribe_en_la_base`.

**Abre** `VER-113`.

### A2 · Leer el delta bien y reconstruir el estado desde él

- Se corrige `obra_diez_capitulos.py:242` para leer con `deltas.leer`.
- `mundo.acumular(semilla, deltas)` es **puro**: devuelve el mundo en la forma de `mundo.leer` y,
  si un delta es incompatible, dice en qué escena, sin lanzar excepción.
- La semilla sale del plan aprobado de la obra (personajes, lugares, accesos) y del conocimiento
  inicial. La compone `regeneracion.semilla_de(con, obra)`. Sin plan aprobado **no hay semilla, y
  se dice**.
- `mundo.rebobinar(con, mundo)` escribe un mundo dado en `entidad` y `conocimiento` en una sola
  transacción (`C-2`).

**Prueba que falla primero:** `test_acumular_los_deltas_da_el_mismo_mundo_que_consolidarlos`.
Además la fila negativa de `VER-09` (un movimiento y una muerte en el mismo `t`, contra un
aplicador ingenuo escrito solo para la prueba),
`test_un_delta_incompatible_se_informa_con_su_escena_y_no_revienta`,
`test_sin_plan_aprobado_no_hay_semilla_y_se_dice`,
`test_rebobinar_y_volver_a_acumular_deja_el_mundo_igual` y
`test_el_resumen_de_acciones_del_guion_lee_el_delta_guardado`.

**Cierra** `VER-09`. Sin migración.

### A3 · Versiones con identidad

Tablas `version_de_obra` (clave `(obra, numero)`) y `capitulo_de_version` (clave
`(obra, numero, orden)`), con un disparador que aborta cualquier `UPDATE` o `DELETE` sobre
`capitulo_de_version`: una versión creada no cambia (`VersionesSoloCrecen` en la base).
`alta_de_obra` crea la versión 1. Funciones: `crear_version`, `versiones_de`,
`capitulos_de_version` y `version_vigente`. El `commit` de cada versión sale de la procedencia del
árbol.

**Migración** (el número libre al commitear): crea las dos tablas, da la versión 1 a cada obra
existente con sus capítulos por `orden`, y recrea `capitulo` **sin** `UNIQUE (obra, orden)`,
copiando las filas (hallazgo 4).

**Prueba que falla primero:** `test_crear_la_version_2_no_cambia_ninguna_fila_de_la_1`. Además
`test_dos_versiones_con_los_mismos_capitulos_se_distinguen_por_su_numero` (`CE-5`),
`test_un_capitulo_compartido_es_la_misma_fila_en_las_dos_versiones`,
`test_un_capitulo_nuevo_en_la_posicion_3_no_pisa_al_capitulo_3_anterior` (Regla 7),
`test_modificar_una_version_creada_falla`, `test_dar_de_alta_una_obra_crea_su_version_1` y
`test_la_migracion_da_la_version_1_a_cada_obra_sin_perder_capitulos`.

**Abre** `VER-114`. Deja listos para cerrar `F-43` y `EX-14`.

### A4 · La reverificación: que un verde heredado no cuente

`regeneracion.reverificar(con, obra, numero)` recorre las escenas de la versión en orden de
lectura. Para cada una calcula la huella (`C-3`), monta el mundo previo con
`acumular(semilla, deltas del prefijo)`, pasa las puertas deterministas con el delta guardado y
guarda una fila `verificada` o `fallida`. Si el delta ya no entra en el mundo nuevo, la fila es
`fallida` con motivo, sin lanzar excepción. **No escribe en `hallazgo`** y **no llama a ningún
modelo**. `INV-06` se lista como no ejecutada, como en `SPEC-30` `RF-12`.

`estado_de(con, obra, numero, escena)` devuelve `sin_reverificar` si no hay fila con la huella
vigente. Así, un verde de otra versión **no cuenta** (`D-1`).

**Migración:** la tabla `reverificacion`.

**Prueba que falla primero:**
`test_una_accion_sobre_un_hecho_que_la_version_nueva_ya_no_revela_falla_al_reverificar` (`INV-03`).
Además `test_una_escena_heredada_sin_reverificar_no_cuenta_como_verificada` (`RF-54`),
`test_con_la_misma_huella_el_verde_se_conserva`,
`test_un_delta_posterior_incompatible_queda_fallido_con_motivo`,
`test_la_reverificacion_no_escribe_en_la_tabla_de_hallazgos`,
`test_la_reverificacion_no_llama_a_ningun_modelo`, `test_sin_semilla_no_se_reverifica_y_lo_dice` y
`test_inv06_sale_como_no_ejecutada`.

**Abre** `VER-115`. `MF-26` pasa a citarla.

### A5 · Qué cambió, y los dos endpoints de lectura

`regeneracion.comparar(con, obra, a, b)` responde por **posición**: compartido (mismo capítulo),
cambiado o nuevo, **por identidad y no por texto** (`CE-5`). Endpoints `GET /obras/{id}/versiones`
y `GET /obras/{id}/versiones/{numero}`, con modelos de salida y las enumeraciones como
enumeraciones (`RF-34`), y el congelado de `PLAN-22` al día en el mismo commit.

**Prueba que falla primero:** `test_cambio_es_por_capitulo_y_lo_dice_el_backend_sin_comparar_textos`.
Además `test_un_capitulo_nuevo_con_el_mismo_texto_sigue_contando_como_cambiado`,
`test_get_versiones_lista_la_1_y_la_2_con_su_numero_y_su_commit`,
`test_get_version_da_por_escena_su_estado_y_su_estado_de_verificacion` y
`test_ningun_campo_expone_la_configuracion_del_sistema` (`RF-57`).

**Abre** `VER-116`.

### A6 · Cada lector ve solo su versión

`regeneracion.escenas_de_version(con, obra, numero=None)`; sin `numero`, la vigente. Pasan a usarla
todos los lectores del hallazgo 5 y los imprescindibles (hallazgo 6). La memoria gana un filtro por
escenas, y `asignar_t_discurso` recibe las escenas que tiene que numerar. **Con una sola versión el
comportamiento es el mismo, y la suite actual lo comprueba.**

**Prueba que falla primero:** `test_con_dos_versiones_cada_lector_ve_solo_las_escenas_de_la_suya`.
Además `test_la_memoria_de_una_escena_de_la_v2_no_trae_el_resumen_del_capitulo_sustituido`,
`test_el_manuscrito_con_dos_versiones_es_el_de_la_vigente_y_no_mezcla`,
`test_un_imprescindible_se_comprueba_en_el_capitulo_regenerado` y
`test_con_una_sola_version_la_obra_se_genera_igual_que_antes`.

**Abre** `VER-117`. **Es el paso más grande y el más arriesgado**: si no cabe en el día, la Parte B
no empieza, y el corte A0–A5 sigue siendo coherente.

### A7 · La petición, el hecho de la versión, la propuesta y la puerta cerrada

- **La petición**: la tabla `peticion_de_cambio` y su validación (`C-4`), de las dos clases.
- **Los nombres de una versión** (`regeneracion.nombres_de_version`), la sustitución en el
  material del Escritor y el nombre viejo como vetada de novela para la versión nueva (`C-4`,
  puntos 1, 3 y 4). Los capítulos afectados por un renombrado, por texto y por presencia (punto 2).
- **Los hechos de una versión**: los de la obra con el enunciado nuevo de su petición, compuestos
  por `regeneracion.hechos_de_version`. `menciona` se calcula en la versión nueva contra el
  enunciado nuevo. `HechoCanonico` no se edita.
- **`regeneracion.proponer(con, obra, peticion)`** devuelve, sin modelo, la salida, los capítulos a
  tocar, la promesa (*«reescribimos lo que dependía de esto»*) y el punto ciego (*«si la prosa
  contradice sin que el delta lo declare, no se toca»*).
- **`SALIDA = None`**. Con `None`, `POST /obras/{id}/cambios` responde `409` *«salida sin elegir:
  falta la medida»* y **no encola nada**. La propuesta responde con los capítulos que tocaría
  **cada** salida y dice que no hay ninguna elegida.
- **El worker** que consume el tipo de trabajo nuevo.

**Migración:** la tabla `peticion_de_cambio`.

**Prueba que falla primero:**
`test_la_propuesta_lista_los_capitulos_antes_de_tocarlos_y_no_encola_nada` (`RF-51`). Además
`test_la_propuesta_lleva_la_promesa_y_su_punto_ciego_literales` (`RF-55`),
`test_pedir_el_cambio_sin_salida_elegida_es_409_y_no_gasta`,
`test_pedir_con_una_lista_distinta_de_la_propuesta_es_409`,
`test_el_enunciado_nuevo_vale_en_la_version_nueva_y_no_en_la_anterior`,
`test_una_peticion_sobre_un_hecho_de_otra_obra_se_rechaza`,
`test_un_renombrado_toca_los_capitulos_que_contienen_el_nombre_viejo_y_los_de_su_presencia`,
`test_la_version_anterior_conserva_el_nombre_viejo_en_sus_fichas_y_en_inv22`,
`test_en_la_version_nueva_el_nombre_viejo_es_una_vetada`,
`test_el_material_del_escritor_lleva_el_nombre_nuevo`,
`test_renombrar_al_destinatario_o_a_un_nombre_ya_usado_es_409` y
`test_editar_el_hecho_a_mano_sigue_prohibido`.

**Amplía** `VER-116`.

### A8 · `docs/` y spec al día de la Parte A

`SPEC-23` (hallazgos 1 y 13), `SPEC-22` (`DA-1`, `G-07`, `G-08`, §3.2.2; hallazgo 12),
`docs/verification.md` (filas nuevas, `VER-09`, `MF-26`, `F-43`, la mitad de la decisión abierta de
`C-3`), `docs/architecture.md`, `docs/definitions.md` (hallazgo 11), `docs/cobertura-examen.md`
(`EX-14`) y `specs/tla/README.md` (`D-2`, `CE-5`).

## Pasos — Parte B (la salida que elija la medida)

### B1 · La medida sobre la novela de ejemplo (no gasta)

**Precondición:** la novela de ejemplo completa (`SPEC-27` `RF-03`). Se ejecuta
`medir_arrastre.py`. Si se niega, **se para aquí y se vuelve al autor**: la salida no se elige. Si
mide, su salida se commitea en `harness/evals/arrastre-SPEC-23.json` y se escribe en `SPEC-23` (v3,
con número, obra, commit y **la dirección del sesgo en la misma línea**), en `SPEC-22` `DA-1` y en
el mensaje del commit.

### B2 · Fijar la salida con el número, no con una opinión

`SALIDA` pasa a `cascada` o `selectiva` según la regla aplicada al número guardado.

**Prueba que falla primero:** `test_la_salida_fijada_es_la_que_da_la_regla_con_el_numero_guardado`:
si alguien cambia `SALIDA` sin cambiar la medida, falla. Desde aquí **se ejecuta una sola rama**.

### Rama `S-1` · si el arrastre medio es ≤ 3

**B-S1.1 · La cascada.** `k` es el primer capítulo de la versión de partida que usa el hecho. Se
crea la versión `n+1` con `1..k-1` compartidos y `k..N` nuevos; se rebobina el mundo vivo a la
semilla más los deltas de `1..k-1`; y se escriben los capítulos nuevos con el mismo montaje que
`novela._escribir`. Relanzar tras una parada sigue desde el último consolidado.

**Prueba que falla primero:**
`test_la_cascada_reescribe_desde_el_primer_capitulo_que_usa_el_hecho_hasta_el_final`. Además
`test_la_cascada_comparte_por_referencia_todo_lo_anterior`,
`test_ningun_capitulo_de_la_version_nueva_queda_sin_reverificar`,
`test_un_capitulo_cerrado_posterior_no_se_reabre_se_escribe_otro` (`RF-30`),
`test_una_parada_a_mitad_deja_la_version_nueva_incompleta_y_la_anterior_intacta` y
`test_relanzar_la_cascada_no_repite_lo_consolidado`.

**B-S1.2 · La promesa**: *«reescribimos lo que dependía de esto: el capítulo k y todos los
siguientes»*, antes de aceptar, con el punto ciego.
**Prueba:** `test_con_s1_la_promesa_dice_que_se_reescribe_hasta_el_final`.

### Rama `S-2` · si el arrastre medio es > 3

**B-S2.0 · La medida de `SPEC-21`, sin gastar.** `arrastre_de_incluir_mencion` sobre la misma base:
si `menciona` añade unos pocos capítulos, entra en `PARA_REGENERACION`; si añade decenas, **se para
y decide el autor** con el número delante.

**B-S2.1 · Regenerar solo lo que usa el hecho**, y reverificar los compartidos que hay entre medias.
Si alguno falla, **se para** y decide una persona.

**Prueba que falla primero:** `test_s2_regenera_solo_los_capitulos_que_usan_el_hecho`. Además
`test_los_capitulos_posteriores_no_se_reescriben_se_reverifican`,
`test_una_accion_posterior_que_deja_de_sostenerse_para_y_levanta_hallazgo_de_version`,
`test_el_hallazgo_de_la_v2_no_aparece_en_la_v1` y
`test_la_reverificacion_no_gasta_ninguna_delegacion`.

**B-S2.2 · Reverificar el resto y enseñarlo**, con `C-5`. **Prueba:**
`test_un_capitulo_cerrado_compartido_que_falla_sigue_cerrado_y_sale_no_verificado`, y el punto ciego
escrito como prueba, `test_una_prosa_que_contradice_sin_delta_pasa_la_reverificacion`, que **pasa a
propósito** y cita `PCF-7`.

**B-S2.3 · La promesa**: *«reescribimos lo que dependía de esto: los capítulos X e Y; los demás se
vuelven a comprobar con reglas, no se reescriben»*, con el punto ciego.

### B3 · `docs/` y spec

La rama elegida en `docs/architecture.md` y en `SPEC-23`. `VER-118` con el punto ciego de la rama.
`SPEC-23` pasa a `aplicada` con su commit propio, **y no sin B4**.

### B4 · Un cambio real sobre la novela de ejemplo (gasta dinero; sí explícito)

Desde la web (`PLAN-22` E16–E18), o por la API si la web no está: propuesta, cambio, seguir el
trabajo y leer las dos versiones. **Se registra** en `docs/verification.md` (sección «La primera
regeneración») y en el historial de `SPEC-23`: base, obra, commit de la generación y de la versión
2; la petición; la salida y el número que la eligió; la lista propuesta frente a la tocada, que
tienen que coincidir; por capítulo, compartido o cambiado; hallazgos y rendiciones de las escenas
nuevas; con `S-2`, cada reverificación; delegaciones y USD **leídos**, con las que no traen cifra
aparte; minutos; si la versión 1 quedó **idéntica byte a byte**; y el estado de Langfuse. Lo que no
se pueda medir dice «sin medir». Una parada a mitad **es un resultado**.

## Orden del día

A0 → A1 → A2 → A3 → A4 → A5 es el corte mínimo; después A6 → A7 → A8. **B1 se ejecuta en cuanto la
novela de ejemplo esté completa**, porque solo necesita A1. B2 y la rama, después de A7. B4, al
final.

## Qué filas `VER-xx` abre o cierra

| Fila | Qué | Paso | Punto ciego |
| --- | --- | --- | --- |
| `VER-113` | La medida se calcula como dice `SPEC-23` v2, se niega sin obra completa, sin usos o sin procedencia, y filtra por obra | A1 | Hereda el de `menciona`, que es léxico: sesgo a la baja |
| `VER-114` | Una versión creada no cambia, dos versiones se distinguen por su número, y lo compartido es la misma fila (`RF-53`, `F-43`, `EX-14`) | A3 | No comprueba que la nueva sea mejor, solo que la anterior sigue |
| `VER-115` | Un verde solo cuenta contra la huella de su versión (`D-1`, `RF-54`, `MF-26`) | A4 | Las puertas leen el delta y no la prosa (`PC-5`, `MF-18`, `PCF-7`) |
| `VER-116` | La propuesta enseña los capítulos antes de tocarlos, «cambió» lo decide el backend por identidad, y la promesa lleva su punto ciego (`RF-51`, `RF-52`, `RF-55`) | A5, A7 | Comprueba la API, no la página (`PLAN-22`) |
| `VER-117` | Con dos versiones, cada lector ve solo la suya | A6 | Solo los lectores enumerados |
| `VER-118` | La rama elegida | B | El de la rama, escrito en B3 |
| **`VER-09`** | **Se cierra**: el aplicador de producción contra uno ingenuo | A2 | Que el delta sea cierto no lo comprueba |

`VER-29` tiene que seguir en verde: ninguna ruta reabre un capítulo `cerrado`.

## Cuestiones abiertas para la aprobación

1. **Resuelta por el autor**: el renombrado entra, por la vía mínima de `C-4`.
2. `C-1` a `C-6`, con sus propuestas.
3. Los nombres de la tabla de `docs/definitions.md`: son propuesta y entran en A0.
4. Registrar migración también para las tablas nuevas, que cambia la costumbre de hasta hoy.

## Lo que este plan no hace

- No hace la puerta de publicación **por versión** ni el PDF por versión.
- No hace el contrato congelado ni ninguna página (`PLAN-22`).
- No da versión a la story bible: un renombrado cambia el nombre de una versión, no la story bible (`C-4`). No renombra al destinatario.
- No implementa `S-5`, ni pone `obra` al mundo vivo para varias obras en una base (hallazgo 8).
- No toca `RF-19`, `RF-30`, `INV-05` ni la máquina de `estado_de_escena`.
- No vuelve a levantar el acta de las escenas reescritas a delta fijo (hallazgo 9): lo informa.
