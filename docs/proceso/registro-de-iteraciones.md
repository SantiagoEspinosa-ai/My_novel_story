# Registro de iteraciones

Qué cambió tras cada ejecución real, cada contraejemplo de TLC y cada resultado de Lean, y
por qué. Causa y efecto, no diario. El detalle completo de cada hallazgo está en su fila
`F-xx` de `docs/verification.md` § "Lo que se aprendió al implementar", o en su `CE-x` de
`specs/tla/README.md`; aquí va lo que hace falta para seguir la cadena.

Solo entran los hallazgos cuyo origen está comprobado. Los demás `F-xx` salieron de revisar
código y documentos, no de una ejecución, y viven en su tabla.

## Tras ejecuciones reales

### La primera obra de diez capítulos (26,04 USD como suelo, 55 escenas escritas de 60)

Era la novela de terror anterior, con la forma vieja: seis escenas por capítulo. Se paró en `cap-10-e2` por `INV-03`, así que **no llegó a terminarse**. El coste, 26,0372 USD, es un **suelo**: 10 de las 169 delegaciones no dieron coste (`salida/novela-1/obra10.log`, que no se versiona).

> **Corrección (2026-09-24).** Este encabezado decía *21,6 USD, 54 escenas consolidadas*. Era una lectura de `obra10.db` hecha con la generación en curso —21,6247 USD es la suma de los capítulos 1 a 8 del log— y se presentó como el total de la obra.

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-56` | Los diez capítulos se habían modelado como **diez obras**, así que ninguna comprobación entre capítulos tenía sobre qué actuar | Una obra con sus diez capítulos registrados en `capitulo` con su orden | Lo que desbloquea la cronología y Lean: sin esto, cada capítulo era su propia cronología |
| `F-39` | Dos capítulos que declaraban el mismo identificador de hecho: **el segundo pisaba al primero** | La clave pasa a `(obra, id)`, con su migración | Cerrado |
| `F-40` | La memoria **mezclaba obras**, y cada capítulo arrancaba sin memoria del anterior | `resumen` y `ficha` guardan su obra y sus consultas se acotan | Cerrado |
| `F-52` | Cero hallazgos en toda la obra, y **ese cero no podía distinguir una obra limpia de una comprobación que no se ejecutó** | Nada se da por medido con esa base; la repetición irá con los arreglos dentro | Abierto: queda repetir la generación |

**Lo que dejó como regla**: *un número medido sobre un sistema roto no es una medida, y
sesga hacia lo cómodo*. Un arrastre pequeño medido ahí no habría dicho que arrastra poco,
sino que se registró poco.

### La primera ejecución real de la novela regalo (`bf42074`)

No pasó del capítulo 1. Cuatro hallazgos:

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-59` | Una vetada global con «ñ» se normalizaba perdiendo la «ñ» y **vetaba una preposición común**: ningún capítulo podía pasar `INV-21` | La normalización conserva la «ñ», que no es una tilde sino otra letra; y una prueba recorre la lista real buscando vetadas que coincidan con palabras comunes | Cerrado (`b18b286`) |
| `F-60` | `INV-03` bloqueaba al destinatario **por usar sus propios recuerdos**: nadie declaraba lo que ya sabía al empezar | Montar la obra siembra el conocimiento inicial de los imprescindibles | Cerrado (`7b4aff2`) |
| `F-61` | Los hooks **no dejaron constancia** | Diagnóstico (`6c175a5`): Claude Code solo los carga desde la raíz del repositorio. Arreglo: las delegaciones arrancan en la raíz | Cerrado (`1ad5691`) en lo diagnosticado: desde la raíz, Claude Code carga los hooks. **Ninguno ha validado todavía un capítulo ni interceptado una herramienta**: en la segunda ejecución real `validar_capitulo.py` dejó 4 filas en el registro de hooks, las 4 con el Planificador o el Revisor y en la rama que sale sin comprobar nada (solo actúa con el Escritor, `validar_capitulo.py:76`); `policy.py` no dejó ninguna. El Escritor no llegó a ejecutarse (`F-68`) |
| `F-62` | El Planificador devolvió **dos planes fuera de esquema** antes del bueno | Su prompt y su definición dicen que un campo de más hace rechazar el plan entero | Cerrado (`3dbc2d1`) |

### `R0` · el primer capítulo aceptado (2,1650 USD)

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-76` | `INV-26` salió `sin_veredicto`: el esquema del Editor rechazaba toda valoración real porque el transporte le añade `medidas` | La valoración se valida sin `medidas` | Cerrado. **El capítulo de `R0` no lo juzgó el Editor**, y por eso su nota no cuenta |
| `F-77` | El Resumidor falló y el capítulo quedó sin resumen | Su prompt recibe los hechos de la obra y qué hacer si no hay | Cerrado; comprobado con tres delegaciones de diagnóstico (0,2429 USD) antes de gastar una novela |

### `R1` · la novela de ejemplo, publicada (16,8905 USD en 36 delegaciones)

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-79` | Parada en el capítulo 9 por `INV-02`: un reencuentro que la regla no dejaba escribir | El estado vital que cuenta es el que deja la propia escena, con los cambios de su delta (decisión del autor) | Cerrado. La reanudación escribió el 9 y el 10 sin volver a planificar: el checkpoint, ejercido por primera vez con datos reales |
| `F-118` | Un `bloqueante` del intento descartado seguía abierto y la puerta no publicaba nunca | Al consolidar se cierran los hallazgos que la versión aceptada ya no produce | Cerrado. **Primera novela regalo publicada**, ronda 1, Lean `0` |
| `F-117`, `F-119` | El libro de gasto perdía el capítulo parado y, al reanudar, **pisó con ceros 11,9010 USD medidos** | El capítulo parado se anota; anotar otra vez suma | Cerrados. El libro de `R1` se reparó con `anotar` y cuadra con Langfuse |
| `F-120` | La traza del intento parado del 9 se perdió; su coste no | Nada todavía | Abierto: toca la clave de la tabla y su migración |

### `INV-30` en real, sobre la novela de ejemplo (0,6959 USD)

El validador visual **falló por primera vez**, y con dos defectos reales; la primera inspección
había dado por buena una web con tres (`F-84`).

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-141` | La frase repetida de `INV-25` se enseñaba normalizada («gat que ha comid…») | Se enseña el fragmento del texto de su primera aparición | Cerrado |
| `F-142` | La ficha de Cloe no enlaza el capítulo 10, donde habla y actúa: enlaza donde el plan la declaró | Nada todavía | Abierto: decide el autor (presentes en el delta, o que el Editor los contraste) |

### La pasada «antes», briefs de riesgo (`R2` a `R5`)

| Ejecución | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `R2` · inyección (1,6246 USD) | El detector cazó la inyección con el modelo real; la entrevista no cerró porque el guion estaba escrito para el Entrevistador doble (`F-140`) | Los briefs de guion responden a lo que el Entrevistador real pregunta | Cerrado en los briefs. Sin novela en la pasada «antes» |
| `R3` · incoherencia temporal (4,9492 USD) | **El Revisor rechazó el plan por las incoherencias que el brief provoca**, en tres rondas. Sin novela, Lean no tuvo eventos. El informe se perdió porque `evaluar.py` reventaba sin plan (`F-143`) | `evaluar.py` informa sin obra montada | Cerrado. La incoherencia la paró un validador anterior a Lean, y es la justificación que pide el enunciado |
| `R4` · contradicciones (3,1154 USD) | El Entrevistador detectó las tres; el plan se rechazó porque el nombre llegó como `[NOMBRE_ANONIMIZADO]` (`F-146`) | Decisión del autor: pseudonimizar los nombres en el harness (`SPEC-34`, aprobada) | Sin implementar: no hay `PLAN-34` todavía |
| `R5` · vetadas por variantes (20,5556 USD, reanudada) | Parada en el capítulo 2 por `INV-03`; reanudada, **publicada** sin ninguna vetada: el Escritor las esquivó. El rastro dio una huella falsa, «martes» por «Marta» (`F-145`) | Nada para `F-145` todavía | `F-145` abierto; falla hacia el ruido |

### `B4` · la demo de la cascada, publicada (19,5379 USD en 42 delegaciones)

Una petición real de renombrado sobre la novela de ejemplo. En los cuatro tramos, **la versión 1
siguió siendo la vigente en el backend** hasta que se publicó la nueva: `D-2` se sostuvo con
paradas reales a mitad. **La web no**: enseñaba como vigente la versión que se estaba escribiendo
(`F-150`).

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-148` | `INV-02` bloqueaba la escena en la que un personaje desaparece: el arreglo de `F-79` rompió su espejo | Un presente pasa si está vivo antes o después de los cambios de su escena | Cerrado; el capítulo 8 de la versión 2 pasó al relanzar |
| `F-149` | El Escritor no sabía dónde ocurre la escena siguiente, y `INV-02` se lo exigía un capítulo tarde | El material del Escritor lleva el lugar de la escena siguiente de la versión que se escribe | Cerrado; la versión 3 se escribió entera sin paradas |
| `F-151` | La puerta de Lean no podía publicar ninguna versión 2 o posterior: leía los eventos de todas las versiones | Lean recibe la versión y solo sus eventos | Cerrado; publicada en la ronda 2 |
| `F-150` | La web enseñaba como vigente la versión que la cascada estaba escribiendo | El backend lee la última publicada de `commons/obra/vigente.py` | Cerrado en el backend; el frontend recibe `vigente` en la respuesta de versiones (decisión del autor) |

### El tuning (`PLAN-31` `T1`): **no completado**

Decisión del autor (2026-09-25): se cierra como no completado, con sus números reales y su
causa. La pasada «después» **no se lanzó**, y `T1` (el Escritor, sobre el ritmo; `6deefe5`)
está commiteado **sin medir**.

| Paso | Qué pasó | Coste |
| --- | --- | --- |
| `antes-2`: el brief base repetido con el código de `89425c4` y la misma versión del Escritor que `R1` (`8f9a1478e71a`) | Capítulos 1 y 2 consolidados; **el 3 se paró tres veces** por `INV-03`: Tere actúa sobre `imp-02` e `imp-03` sin constar que los conozca. 3 borradores y 5 hallazgos bloqueantes | **8,7712 USD en 14 delegaciones** (6,8424 del primer intento, 1,0935 de la reanudación y 0,8353 del reintento final) |
| La «después» | No se lanzó: con el mismo plan habría chocado con la misma parada | — |

**Por qué hacía falta repetir la «antes».** Desde `R1` cambió lo que recibe el Escritor
(`F-149`: el lugar de la escena siguiente), y la «versión del prompt» de la tabla es solo la
huella de `escritor.md`, que no cambió. Comparar la «después» con `R1` habría mezclado `T1` con
ese cambio sin que la tabla lo dejara ver.

**Lo que sí se midió, y es el resultado de este paso (`F-155`).** Los tres planes de las
generaciones por ficha (`R1`, `R5` y `antes-2`) tienen **`conocimiento_inicial` vacío**: el
Planificador no lo siembra nunca, porque ni su prompt ni el código de planificación lo piden, y
el esquema lo deja vacío por defecto (Regla 4). **Dos de las tres generaciones se pararon por
eso**: un personaje secundario actúa sobre un imprescindible de la destinataria que nadie le
sembró. En `R5` fue Luisa sobre `imp-01`, en el capítulo 2; en `antes-2`, Tere sobre `imp-02` e
`imp-03`, en el capítulo 3. `R1` se libró porque su Escritor no hizo actuar a ningún secundario
sobre un imprescindible. El libro de gasto pasa de 47,1354 a 55,9066 USD.

## Tras Lean

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-47` | Lean destapó que **`INV-08`, el orden temporal, estaba declarada, escrita y probada, y no la ejecutaba nadie** en el pipeline | Se enchufa en la puerta de capítulo | Cerrado (`b2f097c`). La puerta y `L-1` coinciden en el veredicto sobre la misma base |
| `F-54` | Con la tabla de eventos **presente y vacía, Lean aprobaba**: cero violaciones sobre cero eventos | Tercera salida, `2` = sin veredicto, que tampoco publica | Cerrado. Es la Regla 8 aplicada al propio validador formal |
| `F-55` | El orden del discurso salía de ordenar `capitulo` como cadena, y se rompe justo en el capítulo 10 | Se extrae el número final del identificador | Corregido en `specs/lean/` |
| `F-46` | `L-4` **no puede disparar nunca** sobre datos reales: nadie guarda en qué evento un personaje deja de poder aparecer | Nada todavía | Abierto. Falta la fuente del dato |

## Tras TLC

### Sobre el backend (`specs/tla/HarnessBackend.tla`)

Desde `EX-07`, el modelo es el de `backend/`, y cada acción dice qué función implementa.
Rompió invariantes con el código de entonces:

| Contraejemplo | Qué se vio | Qué cambió |
| --- | --- | --- |
| `F-110` | Relanzar reinicia todos los contadores de reintento: los topes valen por ejecución | Abierto; la corrección está modelada (`ReanudarReiniciaContadores = FALSE`) |
| `F-111` | Relanzar la planificación pisaba las filas del plan anterior | Cerrado: relanzar añade rondas |
| `F-112` | Consolidar son dos transacciones, y una caída entre ellas deja un estado que la reanudación no lee | Abierto; modelado (`DosTransaccionesAlConsolidar = FALSE`) |
| `F-113` | La puerta publicaba un capítulo que el Editor no llegó a juzgar | Cerrado: un `INV-26` sin veredicto impide publicar |
| `F-114` | El tope de delegaciones por obra no podía saltar nunca en la novela regalo | Cerrado: se compara el total de la obra |
| `F-115` | Una generación parada salía con código 0 | Cerrado: sale con 1 |
| `F-116` | Una caída entre consolidar y resumir deja el capítulo sin memoria para siempre | Abierto; modelado (`ReanudarSaltaLaMemoria = FALSE`) |

### Sobre el flujo de `main` (histórico)

El primer modelo era el del flujo de la rama `main`; los cambios de abajo fueron al modelo y a
los documentos de ese flujo.

| Contraejemplo | Qué se vio | Qué cambió |
| --- | --- | --- |
| `CE-1` | Si el freno de delegaciones salta antes del primer capítulo, **se publica una novela vacía** | `PublicarAlAgotarTope = FALSE`: frenar es parar, no terminar |
| `CE-2` | Un capítulo con la escalera agotada **entra sin haber pasado los validadores** | `ExigirValidacionCompleta = TRUE`: con un fallo bloqueante abierto no hay rendición |
| `CE-3` | La frase *«en orden»* del documento, implementada literalmente, **reescribe la novela entera** ante un cambio del lector en el capítulo 1 | El modelo toma el menor capítulo pendiente. El código ya lo hacía; lo que se corrige es el documento |
| `CE-4` | Tras una caída, un capítulo con los intentos gastados **deja la generación parada para siempre** | La segunda rama del guardián de `AgotarEscalera`. Lección: un checkpoint guarda la decisión que provocaron los intentos, no solo el contador |
| `CE-5` | `VersionesSoloCrecen` estaba **en verde por no poder distinguir dos versiones** con los mismos capítulos | El campo `ronda` da identidad a la versión. En el proyecto: `F-43`, y de ahí `SPEC-23` `D-2`, versiones con identidad propia |

## Pendiente

- **La iteración de tuning** que pide el enunciado: **no completada**, por decisión del autor
  (§ "El tuning" arriba). La pasada «antes» está ejecutada con los cinco briefs; `T1` está
  commiteado sin medir, y la «después» no se lanzó. Lo que la bloquea es `F-155`.
- Los abiertos de arriba: `F-110`, `F-112`, `F-116`, `F-120`, `F-142` y `F-145`.
- **La repetición de la obra de diez capítulos** con los arreglos dentro (`F-52`).
