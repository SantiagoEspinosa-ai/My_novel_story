---
id: SPEC-03
titulo: El dominio guarda referencias donde hoy guarda prosa
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: dface19
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-03 — Referencias del dominio

## La causa que comparten los tres

Tres cambios que se resistieron al cerrar los modos de fallo, y **no son tres
problemas: son tres síntomas del mismo**.

**El dominio guarda prosa donde debería guardar referencias.** Un atributo que
dice *"las reglas de la amenaza"* en lenguaje natural no se puede comparar con
nada; un atributo que dice *"los identificadores `RM-03` y `RM-07`"* se compara
con una intersección de conjuntos.

La consecuencia se ha visto tres veces seguidas al escribir validadores:

1. **Casi todos los validadores acaban siendo léxicos.** Si el dato es prosa, la
   única comprobación posible es buscar palabras dentro de palabras. Así nació
   `VER-39`, la comprobación de menciones, que es lo mejor que se puede hacer
   sobre texto y aun así no distingue si Marta coge el cuchillo o lo coge Luis.
2. **La Regla 2 los rechaza por punto ciego repetido.** Cuando el segundo
   validador léxico llega —el que contrastaría un resumen con su escena— tiene
   exactamente el mismo punto ciego que el primero, así que es cobertura falsa y
   no entra. Es lo que pasó con `MF-21`, que acabó como `PC-11`.
3. **La Regla 3 no se puede cumplir.** Un validador necesita una referencia
   independiente de lo que valida. Si el único dato disponible es la prosa que el
   modelo escribió, no hay segunda fuente: el sistema se valida a sí mismo.

Escribir referencias no es una mejora de estilo. **Es lo que hace que los
validadores puedan tener puntos ciegos distintos**, y por tanto lo que permite
que el conjunto cubra algo.

---

# 1. Qué cambia

## C-1 · El delta declara el cambio de valor, y el borrador la superficie

**Objeción al enunciado del encargo, antes de la propuesta.** El encargo pedía
añadir `cambio_de_valor`, `pov` y `tiempo_verbal` a `DeltaDeEscena`. **Dos de los
tres no van ahí.** `DeltaDeEscena` está definido como *"diff estructurado"* del
mundo, y todos sus campos actuales son cambios del canon. La persona narrativa y
el tiempo verbal no cambian el mundo: son propiedades de la superficie del texto.
Meterlos en el delta obligaría a leer el diff del mundo para saber en qué tiempo
está escrita una escena.

### Qué se añade

| Clase | Atributo nuevo | Forma | Obligatorio |
| --- | --- | --- | --- |
| `DeltaDeEscena` | `cambio_de_valor` | `{eje, signo}`, con `eje` de `eje_de_valor` y `signo` de `signo_de_cambio` — la misma forma que en `Escena` | Sí |
| `Borrador` | `pov_usado` | Referencia al `POV` que el texto usa de hecho: al menos `persona` y `tiempo_verbal` | Sí |

`Borrador` ya lleva `modelo` y `prompt_hash`, así que es donde vive lo que
caracteriza al texto producido. El Escritor sigue devolviendo lo mismo en una
sola llamada: texto y delta. Lo único que cambia es dónde se guarda cada dato.

### Qué desbloquea

| Se desbloquea | Cómo |
| --- | --- |
| **`MF-08`**, el único modo que resistió a las dos clasificaciones | Con `cambio_de_valor` en el delta, comparar lo entregado con lo que `Escaleta.cambios_de_valor` planificó es una igualdad de pares |
| **`VER-47` (b)** deja de ser vacía | Hoy compara campos que el Escritor podría no escribir nunca. Con `pov_usado` obligatorio hay algo que comparar siempre |
| **`VER-48`** pasa de única señal a **contraste** | La heurística morfológica deja de ser la única fuente: tiene contra qué cuadrar. Es la **Regla 3** aplicada, y es el cambio que más la mejora |
| **`MF-01`** cierra del todo | La parte de campos la cubre `VER-47`; la de texto, `VER-48` contra `pov_usado` |

### Migración

**Caduca con:** `backend/app/commons/db/`.

Ninguna hoy: no hay esquema ni base de datos. Cuando la haya, `cambio_de_valor`
es una columna obligatoria en `delta_de_escena` y `pov_usado` dos columnas en
`borrador`, y como son obligatorias haría falta rellenar las filas existentes
releyendo el texto con un modelo, que es exactamente lo que este cambio existe
para evitar. **Es la última vez que sale gratis.**

## C-2 · `Resumen.hechos_clave` pasa a ser una lista de identificadores

Hoy es prosa. Pasa a ser `hechos_clave[]` como **lista de identificadores de
`HechoCanonico`**. El texto del resumen sigue en `Resumen.texto`; lo que cambia
es que los hechos que afirma quedan además enumerados por referencia.

### Qué desbloquea

| Se desbloquea | Cómo |
| --- | --- |
| **`MF-21` deja de ser `PC-11`** | Contrastar un resumen con su escena pasa de comparación léxica a **intersección de conjuntos**: todo identificador de `hechos_clave` tiene que estar entre los que la escena estableció o reveló |
| **Un punto ciego propio**, que es lo que la Regla 2 exigía | El validador por identificadores no ve un resumen que **parafrasee** un hecho sin citarlo. Ese punto ciego es distinto del léxico de `VER-39`, así que ya no es cobertura falsa |
| **`INV-13`** —ningún hecho se revela dos veces como nuevo— | Comparar identificadores entre resúmenes en vez de buscar frases parecidas |

### Migración

Ninguna hoy. Con datos, habría que extraer identificadores de resúmenes escritos
en prosa, que solo se puede hacer con un modelo y sin garantía.

## C-3 · Correspondencia entre ejes de valor y campos del delta

**Lo primero, porque cambia el papel del cambio:** esta tabla **no sustituye a
`C-1`, la complementa.** No se puede derivar el eje a partir del delta, por dos
motivos que se ven en cuanto se escribe la correspondencia completa:

- **Ningún campo del delta lleva signo.** `movimientos` dice que alguien se
  movió, no si eso le hizo más o menos seguro.
- **Cuatro de los seis ejes solo tienen campo para uno de los dos signos.**

Así que la tabla sirve como **comprobación cruzada de coherencia** —si el delta
está lleno de muertes, el eje declarado difícilmente es `conocimiento`— y esa es
justamente la **segunda fuente independiente** que pide la Regla 3.

| Eje | Campo del delta que lo evidencia | Ambigüedad |
| --- | --- | --- |
| `vida` | `cambios_de_estado_vital` | **Solo el signo negativo.** Sobrevivir a algo no deja rastro en el delta |
| `conocimiento` | `revelaciones` | **Solo el signo positivo.** Olvidar, dudar, o descubrir que lo que sabías era falso no tiene campo |
| `cordura` | `deterioros` con `eje = cordura` | Sin ambigüedad relevante: `INV-14` ya contempla la reversión justificada, así que los dos signos existen |
| `vinculo` | `deterioros` con `eje = vinculos` | **Solo el signo negativo.** Un vínculo que se crea no tiene campo |
| `control` | `cambios_de_posesion` | **Ambiguo.** Perder un objeto es perder control, pero el control también se pierde por coacción, y eso el delta no lo registra |
| `seguridad` | `movimientos` | **El más ambiguo de los seis.** Un movimiento puede aumentar o disminuir la seguridad, y una escena puede volverse insegura sin que nadie se mueva: basta con que entre la amenaza |

**`setups_pagados` no corresponde a ningún eje.** Pagar un setup es un suceso
estructural, no un movimiento de valor dramático. Conviene dejarlo escrito para
que nadie intente forzarlo dentro de la tabla.

### Qué desbloquea

| Se desbloquea | Cómo |
| --- | --- |
| **La comprobación cruzada de `C-1`** | El `cambio_de_valor` que el delta declara tiene que ser compatible con lo que el resto del delta contiene |
| **`INV-01` sube de nivel** | Hoy comprueba que el cambio de valor **no sea nulo**. Con la tabla, comprueba además que **no sea incoherente** |

### Migración

Ninguna: la tabla es una sección nueva de `Docs/definitions.md`, no un atributo.

## C-4 · El delta puede expresar los tres valores de `estado_vital`

Incluido aquí a propuesta del encargo, y **encaja**: es exactamente el mismo
defecto. `SPEC-02` añadió `desaparecido` a `estado_vital` y el delta solo sabe
decir `muertes`, así que **hay un valor del vocabulario que el sistema no puede
alcanzar** y `INV-02` lee a un desaparecido como vivo. Es `D4-6` de `REV-01`, el
bloqueante que se reclasificó.

| Clase | Cambio | Forma |
| --- | --- | --- |
| `DeltaDeEscena` | `muertes` pasa a **obsoleto**, no se borra | — |
| `DeltaDeEscena` | `cambios_de_estado_vital[]` | Lista de `{personaje, de, a}`, con `de` y `a` de la enumeración `estado_vital` |

Un campo por transición y no uno por valor: así el vocabulario puede crecer sin
volver a tocar el delta, que es el error que se está corrigiendo.

### Qué desbloquea

`INV-02` deja de dar por vivo a un desaparecido. `VER-39` gana precisión: las
entidades que el delta toca pasan a incluir a quien desaparece.

---

# 2. Qué bloqueantes de `SPEC-01` se resuelven

Uno de los cuatro, y conviene no sobrevender los otros tres.

| Bloqueante de `SPEC-01` | ¿Lo resuelve esta spec? |
| --- | --- |
| **`D4-6`** — el delta no puede expresar `desaparecido` | **Sí**, con `C-4`. Es el motivo de incluirlo aquí |
| **`D4-4`** — faltan tablas para `Beat`, `ArcoNarrativo`, `POV`, `MomentoNarrativo` | **No.** Esta spec no crea tablas. Sí **prepara el terreno**: ver `R-5` y `R-8` del apartado siguiente, que hacen esas clases comprobables cuando existan |
| **`D2-1` / `D4-5`** — el orden de recorte de los niveles de memoria | **No.** Es una decisión de arquitectura pendiente de tu respuesta |
| **`D4-9`** — no existe la puerta de cierre de capítulo | **No.** Nace de la decisión `C-1` de `REV-01` y necesita su propia spec |

---

# 3. Dónde más guarda prosa el dominio

Buscado a propósito, recorriendo las cuarenta y tres fichas de clase en vez de
esperar a tropezar con ellas. Ordenado por lo que desbloquea, no por lo grave que
suena.

| # | Dónde | Hoy | Debería | Qué desbloquea |
| --- | --- | --- | --- | --- |
| **R-1** | `GuiaDeEstilo.tics_prohibidos` | Prosa | **Lista de cadenas literales** | Una comprobación determinista que hoy no se puede ni escribir: *ningún tic prohibido aparece en el texto*. Es una búsqueda de subcadena. **El mejor coste-beneficio de toda la lista** |
| **R-2** | `Lugar.accesos_y_salidas` | Prosa | Lista de referencias a otros `Lugar`, o de accesos con nombre propio | **Cierra `PC-10` y `MF-17`**: un cambio de topología entre escenas pasa a ser una diferencia de conjuntos |
| **R-3** | `Amenaza.reglas` | Prosa | Identificadores de `ReglaDelMundo` | `INV-10` —*la amenaza no viola sus propias reglas*— hoy ni siquiera puede **enumerar** qué reglas le aplican. Con ids, la parte de "¿qué reglas?" deja de necesitar juez |
| **R-4** | `Personaje.voz`, en concreto `muletillas` | Prosa dentro de un paréntesis | `muletillas[]` como lista de cadenas literales | Da a `VER-51` una señal **exacta** además de las cuatro métricas estadísticas: contar muletillas por personaje es exacto, medir su riqueza léxica es aproximado |
| **R-5** | `Beat.valor_antes` y `valor_despues` | Prosa | `{eje, signo}`, la misma forma que `Escena.cambio_de_valor` | Da una **segunda fuente independiente** para el cambio de valor de la escena: la suma de sus beats. Regla 3 otra vez |
| **R-6** | `RegistroDeConocimiento.fuente` | Prosa | Identificador de `Escena` o de `Personaje` | La parte determinista de `INV-03` —la que más reduciría `PC-3`— necesita saber de dónde salió el conocimiento, no solo que existe |
| **R-7** | `EstadoDelMundo.hechos_vigentes[]` | Sin especificar | Identificadores de `HechoCanonico` | `INV-06` —*ningún hecho vigente contradice a otro*— necesita comparar identificadores, y `HechoCanonico.contradice[]` ya apunta en esa dirección |
| **R-8** | `ArcoNarrativo.hitos[]` | Sin especificar | Identificadores de `Escena` o de `Beat` | `INV-07` —*toda escena realiza un beat que sirve a un arco*— necesita que el arco referencie algo comprobable |
| **R-9** | `Puerta.accion_si_falla` | Prosa | **Una enumeración nueva** | Hoy el comportamiento de una puerta se describe en prosa mientras `severidad` ya lo codifica. Dos formas de decir lo mismo, y una de ellas divergirá |
| **R-10** | `Brief.prohibiciones` | Prosa | Lista | Mismo argumento que `R-1`, aplicado al contrato de la obra |
| **R-11** | `Amenaza.tell` | Singular y en prosa | `tells[]` con identificadores de `Tell` | `Tell` es una clase con `id` y una amenaza puede tener varios. El singular es además un error de cardinalidad |
| **R-12** | `CurvaDeDread.valvulas[]`, `Rubrica.ejemplos_ancla[]`, `SetupYPago.setup` y `pago` | Sin especificar | Identificadores de `Valvula`, `AnclaDeEstilo` y `Presagio` | Son referencias que ya tienen clase destino con `id`: solo falta decirlo |

**`R-1` y `R-2` son las dos que más rinden.** La primera convierte un requisito
de estilo en una búsqueda de subcadena; la segunda cierra un punto ciego que hoy
está asumido a sabiendas.

**No todo lo que es prosa debería dejar de serlo**, y conviene decirlo para que
nadie aplique esto en bloque: `HechoCanonico.enunciado`, `ReglaDelMundo.enunciado`,
`Personaje.deseo`, `necesidad`, `miedo` y `herida`, `Escena.conflicto` y
`AnclaDeEstilo.texto` son prosa **porque su contenido es prosa**. Convertirlos en
referencias no los haría comprobables, los haría pobres.

---

# 4. Qué queda explícitamente fuera

- **Crear tablas o esquema.** Esta spec cambia `Docs/definitions.md`; la
  persistencia es de `SPEC-01` y de su plan.
- **`R-1` a `R-12`.** Se listan aquí porque se encontraron buscándolos, pero
  **no se aprueban con esta spec**: son su propio cambio y cada uno tiene su
  migración. Si se aprueban ahora, se aprueban por separado y a sabiendas.
- **Los umbrales** de cualquier validador que estos cambios desbloqueen. Siguen
  saliendo de medir.
- **Reclasificar `INV-11` e `INV-14`** de `juez_llm` a `regla`, que quedó
  pendiente al aplicar `SPEC-02`. Es de la misma familia pero no de la misma
  causa, y merece su propia decisión.

# 5. Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿`pov_usado` va en `Borrador` o en `DeltaDeEscena`? | En `Borrador`. El delta es el diff del mundo y la persona narrativa no cambia el mundo |
| 2 | ¿`pov_usado` lleva los cinco campos de `POV` o solo `persona` y `tiempo_verbal`? | Solo esos dos: son los que la guía de estilo fija y los que `VER-48` puede contrastar. `distancia` y `fiabilidad` no son comprobables hoy |
| 3 | ¿`hechos_clave` se queda **solo** con identificadores, o admite además una glosa? | Solo identificadores. Una glosa reintroduce la prosa que este cambio quita |
| 4 | ¿`muertes` se marca obsoleto o se borra? | Obsoleto. Es la regla del proyecto y aquí no cuesta nada |
| 5 | ¿Se aprueba alguno de `R-1` a `R-12` en este mismo commit? | `R-1` y `R-2` son las que más rinden y las más baratas. Las demás, después |

# 6. Resuelto al aprobar

Las cinco preguntas quedaron resueltas el 2026-09-22 en los términos propuestos,
con dos añadidos del decisor:

- **Se aprueban tres de los doce sitios, no dos**: `R-1` (`tics_prohibidos`),
  `R-2` (`accesos_y_salidas`) y **`R-6` (`RegistroDeConocimiento.fuente`)**. El
  tercero es el que más importa: la parte determinista de `INV-03` necesita saber
  **de dónde salió** el conocimiento, no solo que existe, e `INV-03` es la única
  puerta bloqueante que hoy depende de un juez. Es lo que más encoge `PC-3`.
- **Los dos huecos del modelo se anotan en `Docs/definitions.md`**, sin
  resolverlos: sobrevivir no deja rastro y olvidar no tiene campo. Son cosas que
  la novela puede hacer y el sistema no puede representar.

Los otros nueve sitios (`R-3`, `R-4`, `R-5`, `R-7` a `R-12`) **quedan listados y
sin aprobar**: son mejoras, pero no cambian qué se puede verificar.
