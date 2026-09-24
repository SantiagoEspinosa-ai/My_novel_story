# Registro de iteraciones

Qué cambió tras cada ejecución real, cada contraejemplo de TLC y cada resultado de Lean, y
por qué. Causa y efecto, no diario. El detalle completo de cada hallazgo está en su fila
`F-xx` de `docs/verification.md` § "Lo que se aprendió al implementar", o en su `CE-x` de
`specs/tla/README.md`; aquí va lo que hace falta para seguir la cadena.

Solo entran los hallazgos cuyo origen está comprobado. Los demás `F-xx` salieron de revisar
código y documentos, no de una ejecución, y viven en su tabla.

## Tras ejecuciones reales

### La primera obra de diez capítulos (21,6 USD, 54 escenas consolidadas de 60)

Era la novela de terror anterior, con la forma vieja: seis escenas por capítulo.

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
| `F-61` | Los hooks **no dejaron constancia** | Diagnóstico (`6c175a5`): Claude Code solo los carga desde la raíz del repositorio. Arreglo: las delegaciones arrancan en la raíz | Cerrado (`1ad5691`); en la segunda ejecución real los hooks ya se ejecutan |
| `F-62` | El Planificador devolvió **dos planes fuera de esquema** antes del bueno | Su prompt y su definición dicen que un campo de más hace rechazar el plan entero | Cerrado (`3dbc2d1`) |

## Tras Lean

| Hallazgo | Qué se vio | Qué cambió | Efecto |
| --- | --- | --- | --- |
| `F-47` | Lean destapó que **`INV-08`, el orden temporal, estaba declarada, escrita y probada, y no la ejecutaba nadie** en el pipeline | Se enchufa en la puerta de capítulo | Cerrado (`b2f097c`). La puerta y `L-1` coinciden en el veredicto sobre la misma base |
| `F-54` | Con la tabla de eventos **presente y vacía, Lean aprobaba**: cero violaciones sobre cero eventos | Tercera salida, `2` = sin veredicto, que tampoco publica | Cerrado. Es la Regla 8 aplicada al propio validador formal |
| `F-55` | El orden del discurso salía de ordenar `capitulo` como cadena, y se rompe justo en el capítulo 10 | Se extrae el número final del identificador | Corregido en `specs/lean/` |
| `F-46` | `L-4` **no puede disparar nunca** sobre datos reales: nadie guarda en qué evento un personaje deja de poder aparecer | Nada todavía | Abierto. Falta la fuente del dato |

## Tras TLC

La especificación modela el flujo de la rama `main` (`EX-07`); los cambios de abajo son al
modelo y a los documentos de ese flujo.

| Contraejemplo | Qué se vio | Qué cambió |
| --- | --- | --- |
| `CE-1` | Si el freno de delegaciones salta antes del primer capítulo, **se publica una novela vacía** | `PublicarAlAgotarTope = FALSE`: frenar es parar, no terminar |
| `CE-2` | Un capítulo con la escalera agotada **entra sin haber pasado los validadores** | `ExigirValidacionCompleta = TRUE`: con un fallo bloqueante abierto no hay rendición |
| `CE-3` | La frase *«en orden»* del documento, implementada literalmente, **reescribe la novela entera** ante un cambio del lector en el capítulo 1 | El modelo toma el menor capítulo pendiente. El código ya lo hacía; lo que se corrige es el documento |
| `CE-4` | Tras una caída, un capítulo con los intentos gastados **deja la generación parada para siempre** | La segunda rama del guardián de `AgotarEscalera`. Lección: un checkpoint guarda la decisión que provocaron los intentos, no solo el contador |
| `CE-5` | `VersionesSoloCrecen` estaba **en verde por no poder distinguir dos versiones** con los mismos capítulos | El campo `ronda` da identidad a la versión. En el proyecto: `F-43`, y de ahí `SPEC-23` `D-2`, versiones con identidad propia |

## Pendiente

- **La iteración de tuning** que pide el enunciado: ajustar el prompt del Escritor y medirlo
  con la nota del Editor por criterio, antes y después (`SPEC-31` `RF-03`, `RF-08`). **Sin
  ejecutar.**
- **La repetición de la obra de diez capítulos** con los arreglos dentro (`F-52`).
