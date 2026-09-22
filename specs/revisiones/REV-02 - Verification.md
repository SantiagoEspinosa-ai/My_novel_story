---
id: REV-02
titulo: Revisión de Docs/verification.md — cobertura cruzada de validadores
tipo: revision_de_documento
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
documento_evaluado: "Docs/verification.md (37 afirmaciones VER-01…VER-37)"
---

# REV-02 — Cobertura cruzada de `Docs/verification.md`

## Qué es esto y qué cambia

`Docs/verification.md` está organizado como una lista de 37 afirmaciones, cada una con su
metodología y su criterio de salida. Está bien construido para responder *"¿cómo pruebo
esta afirmación?"* y **no responde a la pregunta que importa**: *¿qué fallo se cuela
aunque las 37 estén en verde?*

El principio de partida es que el modelo no garantiza nada, así que la fiabilidad no sale
de él: sale de los validadores que lo rodean. Y un validador aislado no significa nada,
porque **cada uno tiene un punto ciego por construcción**. Lo que importa es si los puntos
ciegos se solapan o se cubren entre sí.

Este documento **analiza, no reescribe**. `Docs/verification.md` no se toca hasta que
decidas qué entra.

**Separación que se mantiene en todo el documento:** un **hueco real** es un fallo
concreto que hoy se colaría, con ejemplo; una **mejora opinable** es una preferencia mía
sobre cómo está organizado el documento. Van en secciones distintas y no se mezclan.

---

# 1. Fortaleza y punto ciego de cada validador

La columna que hoy no existe es la tercera. Un validador sin punto ciego declarado es un
validador que no se ha entendido.

## Nivel artefacto

| ID | Detecta bien | Punto ciego, por construcción | Fallo concreto que se cuela |
| --- | --- | --- | --- |
| **VER-01** | Campos inventados en un esquema Pydantic | **Es unidireccional: mira campos de más, no campos de menos** | El esquema de `Hallazgo` sin `invariante` pasa en verde. `VER-12` buscará después un campo que el esquema nunca tuvo |
| **VER-02** | Que un `Enum` rechaza lo que no es suyo | Comprueba el **rechazo**, no la **completitud** del `Enum` | `estado_vital` implementado con `vivo` y `muerto` pasa: rechaza `narrador` igual de bien. Falta `desaparecido` y nadie lo nota |
| **VER-03** | Que el endpoint responde antes de terminar | No comprueba que el trabajo **llegue a ejecutarse** | El worker no arranca: todo devuelve `202` con un identificador de un trabajo que nadie consume. Verde |
| **VER-04** | Que la cola sobrevive a un reinicio | **No comprueba idempotencia.** Su criterio dice "el trabajo sigue ahí y se completa", no "se llamó al modelo una sola vez" | El worker muere tras llamar al modelo y antes de registrar. Al reanudar vuelve a llamar: se paga dos veces y sale otra escena distinta |
| **VER-05** | Desbordamiento del presupuesto | Mide el **techo**, no el **contenido**. Y **cuenta tokens con el mismo contador que usa el ensamblador** | Un contexto de 3.000 tokens que dejó fuera al protagonista pasa. Y si el tokenizador no es el del modelo, `VER-05` valida la mentira consigo misma y la llamada real se pasa |
| **VER-06** | Que no se trunca por el final ni se parte un bloque | Su criterio solo fija **dos de seis niveles**: *"el inmutable nunca se toca antes que los resúmenes"* | Se recorta `Estado actual` antes que `Recuperado`: pasa `VER-06` y rompe `INV-02` en la puerta siguiente, con la llamada ya pagada |
| **VER-07** | Que no entra el texto de escenas lejanas | Comprueba **ausencia de texto de escena**, no ausencia de **volumen equivalente** | El Resumidor devuelve resúmenes casi tan largos como la escena. El contexto lleva la obra entera en forma de resúmenes y `VER-07` está en verde |
| **VER-08** | Que el índice vectorial no contiene texto de escena | Comprueba el **índice**, no el **camino de lectura** | El ensamblador lee el texto por clave primaria y lo inyecta sin pasar por similitud. *(Lo cazaría `VER-07`: ver BC-7, es de las pocas redundancias reales.)* |
| **VER-09** | Equivalencia entre reconstrucción total e incremental | Comprueba **consistencia interna**, no **corrección**. Las dos reconstrucciones comparten el mismo aplicador de deltas | El delta dice que el personaje murió y el texto dice que se desmayó. Las dos reconstrucciones coinciden en el mismo error y el canon queda falso |
| **VER-10** | La puerta de `INV-05` | Comprueba que el delta **se aplicó**, no que se aplicara **entero** | Un delta con tres movimientos falla en el segundo sin transacción: estado a medias y escena consolidada |
| **VER-11** | El comportamiento de cada severidad | Comprueba el comportamiento **dada** una severidad, no que la severidad **asignada sea la correcta** | `INV-01` implementada como `mayor` en vez de `bloqueante`: `VER-11` pasa, porque trata bien a los `mayor`. Es exactamente el error que la skill `harness-invariantes` lista como *"bajar una bloqueante a mayor para desatascar"* |
| **VER-12** | Que el hallazgo lleva un identificador | Comprueba que el id **existe**, no que sea el **correcto** | Se copia un verificador y se olvida cambiar el id: todos los hallazgos salen como `INV-01` y el recuento por invariante miente |
| **VER-13** | Imports cruzados entre features | **Análisis estático: no ve importación dinámica ni acoplamiento por datos** | `features/generacion` lee la tabla `hallazgo` directamente: cero imports cruzados, acoplamiento real |
| **VER-14** | Imports de `commons/` hacia una feature | Mismo punto ciego que `VER-13` | `importlib.import_module("features.x")` dentro de `commons/` |
| **VER-15** | `Enum` de dominio fuera de `commons/dominio/` | **Sin punto ciego relevante.** Ver nota abajo | — |
| **VER-16** | Que el frontend no depende de un cliente de BD | Comprueba **dependencias**, no **lógica** | El componente deduce "esta escena está lista" mirando si hay delta, en vez de leer `estado`. Verde, y `CLAUDE.md` incumplido |
| **VER-17** | Violaciones de capa FSD | Estático, más: comprueba **capas**, no **responsabilidades** | `shared/` con lógica de negocio dentro: capa correcta, contenido incorrecto |
| **VER-18** | Que el componente no renderiza sin estado ni hallazgos | Comprueba el **componente**, no la **API** que lo alimenta; y presencia, no que sean **los abiertos** | La API devuelve también los `descartado`: se muestran, el usuario se acostumbra a ignorarlos y los `abierto` se pierden en el ruido |
| **VER-19** | Que la interfaz distingue ausente de cero | Comprueba la **presentación**, no el **origen** | El backend devuelve `0` donde no midió. El frontend pinta `0` correctamente. El fallo está aguas arriba y `VER-19` está en verde |
| **VER-20** | Que la respuesta del Escritor trae delta bien formado | Comprueba **forma**, no **correspondencia con el texto** | El modelo copia del contexto el delta de la escena anterior: esquema válido, contenido falso |
| **VER-21** | Que un cambio de atributo obligatorio trae migración | Comprueba que **existe** una migración, no que sea **correcta** ni que corresponda al cambio | Se añade `estado_vital` y se commitea una migración vacía. CI verde |
| **VER-22** | Que cada `INV-xx` tiene caso negativo | **Su metodología dice "mutation testing" y su criterio es un recuento.** Cuenta existencia, no eficacia | El caso negativo de `INV-07` usa una escena sin beats, pero el verificador no mira beats porque las tablas no existen. El test pasa por la razón equivocada |
| **VER-23** | Que el conjunto de identificadores solo crece | Ve el **conjunto**, no el **significado** | Se cambia el enunciado de `INV-14` manteniendo el número. El identificador es estable y lo que designa, no |

**`VER-15`, sin punto ciego relevante, y por qué.** La regla es puramente estructural
—dónde está definido un `Enum`— y el artefacto es puramente estático. El único escape
teórico sería crear un `Enum` en tiempo de ejecución con `Enum()`, que no es algo que se
haga por descuido: haría falta escribirlo a propósito. Es el único de los veintitrés donde
el punto ciego no produce un fallo plausible.

## Nivel proceso

| ID | Detecta bien | Punto ciego, por construcción | Fallo concreto que se cuela |
| --- | --- | --- | --- |
| **VER-24** | Que se emite traza por llamada | Comprueba que la traza **existe**, no que su **contenido sea el real** | Se registra el presupuesto **planificado** en vez del **consumido**. `VER-24` verde, y `VER-34`, `VER-36` y `VER-37` se medirán después sobre un dato falso |
| **VER-25** | Que el prompt del Escritor no llega al Juez | Comprueba **una** fuga concreta, no todas | Se le pasa el `Borrador` completo, que lleva `modelo` y `prompt_hash`. La información del Escritor entra por un campo que `VER-25` no mira |
| **VER-26** | Concordancia entre Juez y persona | Mide **concordancia**, no **corrección**. Y su criterio de salida es *"existe una medición publicada"* | Persona y Juez se equivocan igual: concordancia alta, fiabilidad nula. Y `VER-26` en verde significa "se midió", no "el Juez sirve" |
| **VER-27** | Salidas fuera de esquema | **Una salida vacía es esquema válido** | El Juez devuelve `Hallazgo[] = []` por un timeout mal capturado. Se lee como "todo bien" y la escena pasa todas las puertas |
| **VER-28** | Caminos ilegales en la máquina de estados | Verifica el **modelo**, no la **implementación** | Un script de reparación hace `UPDATE escena SET estado='consolidada'`. El model checker no lo ve |
| **VER-29** | Que el worker no tiene ruta hacia `aceptada` | Comprueba que **el worker no puede**, no que quien acepta sea **una persona**. Y §2.5 de `SPEC-01` dice *"sin autenticación"* | Un script llama al endpoint de aceptar en bucle. `VER-29` verde y la puerta humana es ficción |
| **VER-30** | Fallos bajo presión adversaria | **Es inspección, no test: no es reproducible ni regresivo** | Un fallo encontrado en marzo no se vuelve a comprobar en abril, salvo que alguien se acuerde |
| **VER-31** | Rutas que publican saltándose CI | Comprueba que **se pasa** por CI, no que CI **compruebe algo** | CI corre solo un linter. `VER-31` verde y no protege nada |

## Las seis filas `U`

`VER-32`…`VER-37` no tienen punto ciego: **no cubren nada todavía**, que es distinto. Pero
hay algo que sí conviene anotar: **`VER-34`, `VER-36` y `VER-37` dependen las tres de las
trazas de `VER-24`**, y `VER-24` no valida que lo que registra sea real. Las tres
mediciones futuras heredan ese punto ciego antes de existir.

---

# 2. Matriz de cobertura cruzada

Empiezo por los puntos ciegos, no por la cobertura: lo que ya está cubierto no informa.

## 2.1 Puntos ciegos compartidos — donde la redundancia es falsa

| # | Punto ciego compartido | Validadores que lo comparten | Fallo que se cuela con todos en verde |
| --- | --- | --- | --- |
| **BC-1** | **Forma sí, sentido no.** Comprueban que una estructura existe y está bien formada; ninguno comprueba que su contenido se corresponda con la realidad | `VER-01`, `VER-02`, `VER-12`, `VER-20`, `VER-21`, `VER-27` | El Escritor devuelve un delta bien formado que describe la escena **anterior**, copiado del contexto. Seis validadores verdes |
| **BC-2** | **Estático no ve ejecución.** Ni importación dinámica, ni escritura directa en la base, ni acoplamiento por datos | `VER-01`, `VER-12`, `VER-13`, `VER-14`, `VER-15`, `VER-16`, `VER-17`, `VER-23`, `VER-28`, `VER-31` — **diez de treinta y siete** | Un script de mantenimiento pone escenas en `consolidada` saltándose la máquina de estados. Diez validadores verdes |
| **BC-3** | **Autoconsistencia.** El validador usa la misma pieza que valida | `VER-05` (mismo contador de tokens), `VER-09` (mismo aplicador de deltas) | El tokenizador no es el del modelo: `VER-05` pasa y la llamada real se pasa del límite. Nadie lo ve hasta que el proveedor la rechaza |
| **BC-4** | **Nadie compara el texto con el delta** | `VER-09`, `VER-20`, `VER-27` — los tres tocan el delta y ninguno lo contrasta con el texto del que salió | El texto dice que Marta sale de la casa; el delta no registra el movimiento. `INV-02` dará por buena su presencia dentro de la casa en la escena siguiente |
| **BC-5** | **Se verifica el comportamiento, no la clasificación** | `VER-11` (trata bien cada severidad, no comprueba cuál es), `VER-12` (el id existe, no que sea el correcto), `VER-22` (el caso existe, no que sea eficaz) | `INV-01` implementada como `mayor`: la escena avanza con un fallo bloqueante, y tres validadores están en verde |
| **BC-6** | **Fallo silencioso por vacío válido** | `VER-27`, y por herencia `VER-11` y `VER-26` | El Juez devuelve lista vacía por un timeout. Ningún validador distingue *"no encontró nada"* de *"no funcionó"* |

**BC-2 es el más incómodo de los seis.** Diez validadores, casi un tercio del documento,
ciegos a lo mismo. Añadir un undécimo comprobador estático no cubre nada nuevo: es la
definición de redundancia falsa.

## 2.2 Afirmaciones con un solo validador y sin contraste

| Qué se afirma | Único validador | Por qué preocupa |
| --- | --- | --- |
| El estado se reconstruye bien | `VER-09` | Y es autoconsistente (BC-3). Nada contrasta el estado con el texto |
| La máquina de estados no tiene atajos | `VER-28` | Y verifica el modelo, no el código (BC-2) |
| La aceptación es humana | `VER-29` | Y no comprueba humanidad |
| El Juez es fiable | `VER-26` | Y su criterio es *"existe una medición"*, no un resultado |
| El presupuesto se respeta | `VER-05` + `VER-06` | Son dos filas pero **un solo contador y un solo fichero de tests**: si el contador está mal, caen las dos |

## 2.3 Fallos plausibles que ningún VER detecta

Estos no son puntos ciegos de un validador: son huecos del conjunto.

| # | Fallo | Por qué no lo caza nadie |
| --- | --- | --- |
| **H-1** | El delta no se corresponde con el texto | BC-4 |
| **H-2** | Una invariante está clasificada con la severidad equivocada en el código | BC-5 |
| **H-3** | Se llama al modelo dos veces por el mismo trabajo tras un reinicio | `VER-04` comprueba supervivencia, no unicidad |
| **H-4** | Un delta se aplica a medias | `VER-10` comprueba que se aplicó, no que fuera atómico |
| **H-5** | Los resúmenes crecen hasta reconstruir la obra | `VER-07` mira texto de escena, no volumen |
| **H-6** | Un agente devuelve vacío por fallo y se lee como "sin problemas" | BC-6 |
| **H-7** | La traza registra lo planificado en vez de lo consumido | `VER-24` no reconcilia con nada externo |
| **H-8** | Un esquema omite un campo obligatorio | `VER-01` solo mira en un sentido |
| **H-9** | Un `Enum` está incompleto | `VER-02` solo comprueba el rechazo |
| **H-10** | Una escena gira indefinidamente entre `rechazada` y `generada` | Ningún VER cuenta ciclos. Es `D4-8` de `REV-01` |

---

# 3. Sustituir juicio por código donde se pueda

Parcial cuenta. Un validador determinista que cubre parte de los casos con fiabilidad
conocida vale más que un juez que dice cubrirlos todos con fiabilidad sin medir.

| Validador | Qué se puede automatizar | Qué queda irreduciblemente para el juicio | Papel del juez después |
| --- | --- | --- | --- |
| **VER-26** (evals del Juez) | **La estabilidad del Juez, sin ninguna persona**: pasarle la misma escena N veces y medir la varianza de su veredicto. Un juez que se contradice consigo mismo no necesita corpus humano para descartarse | Si el Juez **acierta**, que sí necesita criterio humano | Sigue siendo primera línea, pero con un filtro previo que lo descarta barato si es inestable |
| **VER-30** (red-teaming) | **Convertir los prompts adversarios en corpus y ejecutarlos en CI.** Lo que hoy es inspección pasa a ser regresión: un fallo encontrado una vez se comprueba siempre | **Inventar** prompts nuevos | Pasa de ser el validador a ser el generador de casos |
| **VER-29** (aceptación humana) | **Cadencia entre aceptaciones.** Si el intervalo es menor que el tiempo de leer una escena, no las está leyendo nadie | Probar que hay una persona detrás, que sin autenticación no se puede | El juicio humano deja de presuponerse y pasa a monitorizarse |
| **VER-35** (desempate juez vs. regla) | **Medir cuántas veces discrepan y en qué dirección.** No decide quién gana, pero convierte una decisión abierta en un dato | La decisión de quién gana | Ninguno: es instrumentación, no juicio |

## 3.1 Y lo mismo aguas arriba: las cuatro invariantes de juez

No son filas `VER`, pero es donde más juicio hay y donde más barato sale quitarlo.
`Docs/definitions.md` clasifica `INV-03`, `INV-10`, `INV-11` e `INV-14` como `juez_llm`.

| Invariante | Parte programable | Parte irreducible | Propuesta |
| --- | --- | --- | --- |
| **INV-14** — *"cada deterioro es monótono, o su reversión está justificada en el texto"* | **La monotonía entera.** `Deterioro.serie_por_escena` es una serie numérica: comparar elementos consecutivos es aritmética | Solo la cláusula *"o su reversión está justificada"* | **Cambiar su tipo de `juez_llm` a `regla`, con el juez como desempate** solo cuando la serie no sea monótona. Hoy se pide juicio para hacer una resta |
| **INV-03** — *"ningún personaje actúa sobre un hecho que no conoce"* | Comparar los **ids** de `HechoCanonico` que el delta declara en `revelaciones` contra `registro_de_conocimiento` en `t`. Si el personaje aparece actuando sobre un hecho cuyo id no está en su registro, es determinista | Detectar en el **texto** que "actúa sobre" ese hecho | El código pasa a primera línea sobre los hechos declarados; el juez cubre lo que el delta no declaró |
| **INV-11** — *"el grado de explicación acumulado no supera el fijado"* | **Un conteo**: cuántos `HechoCanonico` sobre la amenaza están revelados al lector frente a `grado_de_explicacion_permitido` | Decidir si una revelación implícita cuenta | Código primero; el juez solo para lo implícito |
| **INV-10** — *"la amenaza no viola sus propias reglas sin pagar el coste"* | Si la escena invoca la amenaza y el delta no registra `coste_de_invocacion`, es señal directa | Si el texto describe una violación que el delta no declara | Código como filtro barato; el juez sigue siendo necesario |

**`INV-14` es el caso claro**: está pidiendo un juez LLM para comprobar si una lista de
números decrece. Los otros tres admiten un filtro previo que le quita al juez la mayoría
de los casos fáciles y le deja los que de verdad necesitan criterio.

---

# 4. Soluciones pícaras

Comprobaciones oblicuas: no miden el fallo directamente, miden algo que correlaciona con
él y cuesta diez líneas.

| # | Punto ciego / hueco | Atajo | Qué pilla y qué no |
| --- | --- | --- | --- |
| **P-1** | **H-1 / BC-4**, delta contra texto | **Comprobación de menciones.** Por cada entidad que el delta declara (muertes, movimientos, cambios de posesión), comprobar que su `nombre_canonico` o algún `alias` aparece literalmente en el texto de la escena. Y al revés: nombres que aparecen en el texto y no están en `personajes_presentes[]` | Pilla el delta copiado de otra escena y el personaje que actúa sin estar declarado. No pilla un delta que se equivoca sobre alguien **sí** mencionado |
| **P-2** | **H-5**, resúmenes que crecen | **Ratio de compresión.** `len(resumen) / len(escena)`. Es una división | Pilla al Resumidor que deja de resumir. No juzga si el resumen es bueno |
| **P-3** | Escena de relleno | **Delta vacío con `cambio_de_valor` no nulo.** La escena afirma que algo cambió y no registra qué: contradicción interna, determinista | Pilla el relleno declarado. No pilla la escena con un delta trivial pero no vacío |
| **P-4** | **VER-32 / INV-15**, deriva de voz | **Cuatro números por escena**, sin juicio estético: longitud media de frase, ratio de diálogo (contar rayas y comillas), densidad de adverbios en `-mente`, riqueza léxica (*type-token ratio*). La distancia de ese vector al de las anclas es la señal | **Se puede empezar hoy sin umbral**: se registra la serie y se mira su forma. El umbral sale después de mirarla, que es exactamente lo que `VER-32` está esperando |
| **P-5** | **H-6 / BC-6**, agente que devuelve vacío | **Canario.** Inyectar en cada lote de verificación una escena con un defecto conocido y comprobar que el Juez lo caza. Si no lo caza, el Juez no está funcionando, devuelva lo que devuelva | Pilla el fallo silencioso y la degradación del proveedor. No mide fiabilidad general |
| **P-6** | **H-3**, llamada duplicada | **Contar `Borrador` por escena.** Si el número crece sin que nadie haya pedido regeneración, hubo duplicado. El dato ya está en la tabla | Pilla el duplicado por reinicio. No lo previene |
| **P-7** | **H-2 / BC-5**, severidad mal clasificada | **Contrastar dos diccionarios.** Parsear la tabla de invariantes de `Docs/definitions.md` y compararla con el registro de `commons/invariantes/`: identificador, nivel, severidad y tipo | Cierra BC-5 entero. Es el atajo con mejor relación entre lo que cuesta y lo que tapa |
| **P-8** | **H-7**, traza falsa | **Reconciliación.** Restar los tokens que la traza registra menos los que devuelve el `usage` de la respuesta del modelo. Si la diferencia no es cero, la traza miente | Desbloquea de paso `VER-34`, `VER-36` y `VER-37`, que hoy medirían sobre un dato sin validar |
| **P-9** | **H-10**, bucle de regeneración | **Contar transiciones por escena.** Si supera un tope, parar y marcar | Trivial de implementar. El tope hay que medirlo antes de fijarlo |
| **P-10** | **H-4**, delta a medias | **Contar entradas aplicadas frente a entradas del delta.** Si no coinciden, no fue atómico | Pilla la aplicación parcial sin necesidad de razonar sobre transacciones |
| **P-11** | **H-8 / H-9**, esquema y `Enum` incompletos | **Hacer `VER-01` bidireccional** y **añadir a `VER-02` la comparación de cardinalidad**: el número de miembros del `Enum` frente al número de valores de la tabla | Coste casi cero: es el mismo comprobador recorrido en los dos sentidos |

---

# 5. Qué añadir, quitar o reordenar

## 5.1 Validadores nuevos — huecos reales

Cada uno cierra un hueco demostrado arriba con un ejemplo concreto. No hay ninguno que
exista solo para llenar la matriz.

| Propuesto | Afirmación | Cierra | Clase |
| --- | --- | --- | --- |
| **VER-38** | La severidad, el nivel y el tipo de cada invariante en el código coinciden con la tabla de `Docs/definitions.md` | `H-2`, y con él BC-5 entero | A |
| **VER-39** | Toda entidad que el delta declara aparece mencionada en el texto de la escena, y todo personaje mencionado está en `personajes_presentes[]` | `H-1`, parcialmente BC-4 | T |
| **VER-40** | El Juez caza el defecto conocido del canario en cada lote | `H-6`, BC-6 | T |
| **VER-41** | Los tokens que registra la traza coinciden con los que declara la respuesta del modelo | `H-7`, y desbloquea `VER-34`, `VER-36`, `VER-37` | T |
| **VER-42** | Aplicar un delta es atómico: o entran todas sus entradas o ninguna | `H-4` | T |
| **VER-43** | Una escena no supera un número acotado de ciclos de regeneración | `H-10` | T |
| **VER-44** | El ratio de compresión de los resúmenes se mantiene por debajo de lo fijado | `H-5` | T |

**Modificaciones a filas existentes, que valen más que una fila nueva:**

- **`VER-01` pasa a ser bidireccional** (`H-8`). Mismo comprobador, los dos sentidos.
- **`VER-02` añade la comprobación de cardinalidad del `Enum`** (`H-9`).
- **`VER-22` arregla su incoherencia**: dice *"mutation testing"* y su criterio es un
  recuento. O el criterio pasa a ser mutación de verdad —desactivar la comprobación y
  exigir que el caso negativo falle— o la metodología deja de llamarse mutación. El
  criterio 7 de `SPEC-01` ya lo dice bien: *"ese caso falla si se desactiva la
  comprobación"*.
- **`VER-30` cambia de clase `I` a `T`**: el corpus adversario en CI lo convierte en
  regresión. La inspección se queda solo para generar casos nuevos.

## 5.2 Qué sobra

**Nada sobra por cubrir lo mismo.** Lo comprobé fila a fila: no hay dos validadores cuya
afirmación se solape. Lo que sí hay es **redundancia falsa** —muchos con el mismo punto
ciego (BC-2)—, que no se arregla quitando filas sino añadiendo validadores de **otra
clase**. Quitar un comprobador estático no cubriría nada nuevo; añadir el undécimo,
tampoco.

Lo único que propondría fundir es organizativo, no de cobertura, y va en 5.4.

## 5.3 Sección nueva: puntos ciegos conocidos

Lo que asumimos a sabiendas, escrito para que nadie lo descubra con el sistema en marcha:

1. **El análisis estático no ve la ejecución.** Diez validadores comparten este límite. Un
   `UPDATE` directo a la base salta toda la máquina de estados y no lo caza nadie.
2. **`VER-05` y `VER-09` se validan con la pieza que validan.** Si el tokenizador o el
   aplicador de deltas están mal, los dos pasan.
3. **El Juez no tiene fiabilidad medida**, y `VER-26` en verde significa "se midió", no "es
   fiable". Hasta que haya corpus, cualquier puerta que dependa de él es una puerta de
   fiabilidad desconocida — y **`INV-03` es `bloqueante` y de tipo `juez_llm`**: es la única
   puerta que detiene una escena basándose en un modelo.
4. **No hay autenticación**, así que "lo acepta una persona" es una convención, no una
   garantía.
5. **Nada compara el texto con el delta** mientras `VER-39` no exista. El canon puede
   divergir del texto sin que ninguna puerta se entere.

## 5.4 Orden de implantación, por hueco cubierto

El orden de hoy prioriza por facilidad y por "lo que corta la propagación". Propongo
reordenar por **qué hueco se tapa**, que a veces coincide y a veces no.

| # | Qué | Por qué primero |
| --- | --- | --- |
| 1 | **VER-38** (severidad contra tabla) | Cierra BC-5 entero, y BC-5 es lo que hace que `VER-11`, `VER-12` y `VER-22` puedan estar los tres en verde con una invariante mal clasificada. Es el validador que **valida a otros tres** |
| 2 | **VER-39** (delta contra texto) | Tapa BC-4, el hueco más grande: el delta es la fuente de verdad del estado y nada lo contrasta con su origen |
| 3 | **VER-41** (reconciliación de trazas) | Barato, y desbloquea tres filas `U` que hoy medirían sobre un dato sin validar |
| 4 | **`VER-01` bidireccional + `VER-02` cardinalidad** | Coste casi nulo, y tapan dos huecos que ya se han materializado una vez con `SPEC-02` |
| 5 | **VER-40 (canario) y VER-42 (atomicidad)** | Los dos fallos silenciosos: el que devuelve vacío y el que aplica a medias |
| 6 | **P-4 (métricas de estilo) como instrumentación** | No es un validador todavía: es empezar a registrar la serie para poder fijar el umbral de `VER-32` con una medición en vez de con una intuición |
| 7 | **VER-43, VER-44** y el resto del orden actual | Siguen valiendo, pero después de lo anterior |

**Lo que cambia respecto al orden de hoy:** los comprobadores de estructura
(`VER-13`…`VER-17`, `VER-23`) bajan del segundo puesto. Son baratos y se escriben una vez,
pero **comparten el punto ciego BC-2 entre todos**, así que implantarlos pronto da una
sensación de cobertura que no se corresponde con los huecos que quedan. Siguen mereciendo
la pena; no merecen ir antes que `VER-38` y `VER-39`.

---

# 6. Mejoras opinables — no son huecos

Separadas a propósito. Ninguna tapa un fallo; son preferencias sobre el documento.

- **`VER-13`, `VER-14` y `VER-15` son tres filas con el mismo comprobador, el mismo punto
  ciego y el mismo sitio.** Igual `VER-16` y `VER-17`. Se pueden leer como una fila con
  varias reglas. Reduce ruido en el resumen de cobertura, no cambia la cobertura.
- **El resumen de cobertura cuenta filas por clase T/A/I/D/U.** Con el eje nuevo, el
  recuento que informaría es **cuántos huecos conocidos quedan abiertos**, no cuántas filas
  hay de cada clase. Las filas no son la unidad útil; los huecos sí.
- **El documento no dice quién mira los validadores cuando fallan.** No es un hueco de
  cobertura, pero un validador cuyo fallo nadie lee es equivalente a no tenerlo.
