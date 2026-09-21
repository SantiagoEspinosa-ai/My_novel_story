# Ontología de novelas IA — Definiciones

2026-09-21 · @Santiago Espinosa Domínguez

Documento de definiciones del harness: la referencia normativa de clases, atributos, relaciones, vocabularios e invariantes de un sistema de IA que escribe novelas largas (caso base: terror, una sola obra). El documento de diagramas Mermaid es su vista, no su fuente; ante cualquier discrepancia manda este.

## Alcance y convenciones

La ontología separa cinco planos porque mezclarlos es el error habitual: lo que el texto es, lo que el mundo contiene, lo que da miedo, cómo se produce y cómo se mide.

| Plano | Pregunta que responde | Uso en el sistema |
| --- | --- | --- |
| Obra | ¿Cómo está partido y ordenado el texto? | Unidad de generación y de recuperación |
| Mundo | ¿Qué existe y qué es verdad en la ficción? | Estado canónico, base de continuidad |
| Terror | ¿Qué produce el miedo y cómo escala? | Control de tensión y de revelación |
| Proceso | ¿Qué artefactos y pasos producen el texto? | Orquestación y gestión de contexto |
| Calidad | ¿Qué es un buen resultado y cómo se verifica? | Puertas, rúbricas y métricas |

**Fábula vs. discurso.** La fábula es la historia en orden cronológico; el discurso es el orden en que se presenta. En terror la distinción es funcional, no académica: casi todo el miedo vive en la diferencia entre ambos, es decir, en lo que ya ocurrió y el lector aún no sabe. El sistema debe guardar las dos líneas por separado y poder mapearlas.

**Fichas de clase.** Cada clase se define con nombre, definición en una frase y atributos clave. Los atributos en **negrita** son obligatorios: sin ellos la instancia no puede entrar en el estado. El resto son opcionales o derivados.

**Las fichas no enumeran valores.** Cuando un atributo está gobernado por un vocabulario controlado, la ficha escribe `atributo → nombre_de_la_enumeracion` y nada más. Los valores viven en un solo sitio, la tabla "Vocabularios controlados". Enumerarlos también aquí es lo que hizo que las dos copias divergieran en el pasado: la ficha decía `juez LLM` donde la tabla decía `juez_llm`.

**Convención de nombres.** Clases en `PascalCase`, atributos en `snake_case`, relaciones como verbo en minúscula (`ocurre_en`, `revela`). **Todo identificador es ASCII, sin tildes ni eñes**: nombres de clase, de atributo, de enumeración, de miembro y valores. La prosa y las definiciones sí llevan tildes; lo que se escribe en código, no. El motivo es que una cadena acentuada admite dos representaciones Unicode equivalentes a la vista y distintas byte a byte, así que dos valores que se leen igual dejan de compararse iguales, y fallan en silencio. Los identificadores son estables y opacos: el nombre de un personaje puede cambiar dentro de la ficción, su `id` no.

**Uso como esquema.** El harness consume este documento como contrato, así que los nombres de clase, atributo y valor de enumeración son literales: no admiten sinónimos ni traducción. Un identificador de clase o de invariante no se reutiliza ni se renumera una vez publicado; si algo deja de aplicar, se marca como obsoleto pero no se borra. Todo lo que el harness deba comprobar aparece como invariante numerada, no como afirmación en prosa.

## Plano Obra

La **Escena** es la unidad atómica: la unidad que se genera, se verifica y se recupera. Todo lo demás son contenedores o funciones sobre ella.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Obra | La novela completa como unidad publicable. | **id**, **titulo**, **premisa**, genero, subgenero, extension\_objetivo, guia\_de\_estilo, contrato\_con\_el\_lector |
| Parte | Agrupación de capítulos con unidad dramática (acto). | **id**, **orden**, funcion\_estructural, valor\_inicial, valor\_final |
| Capitulo | Unidad de lectura con corte deliberado. | **id**, **orden**, gancho\_de\_cierre, escenas\[\] |
| Escena | Bloque continuo de tiempo y espacio con un cambio de valor. | **id**, **pov**, **lugar**, **momento\_narrativo**, **objetivo\_dramatico**, **conflicto**, **cambio\_de\_valor**, **estado** → `estado_de_escena`, personajes\_presentes\[\], salida, longitud\_objetivo |
| Beat | Micro-unidad de cambio dentro de una escena. | **id**, tipo, valor\_antes, valor\_despues |
| ArcoNarrativo | Trayectoria de cambio de un personaje o de una tensión a lo largo de la obra. | **id**, **sujeto**, estado\_inicial, estado\_final, hitos\[\] |
| POV | Punto de vista y distancia narrativa de una escena. | **personaje**, **persona** → `persona_narrativa`, **tiempo\_verbal** → `tiempo_verbal`, distancia, fiabilidad |
| MomentoNarrativo | Posición de la escena en la fábula (cronología) y en el discurso (orden de lectura). | **t\_fabula**, **t\_discurso**, duracion\_ficcional |
| LineaArgumental | Hilo de trama que atraviesa varias escenas. | **id**, tipo, escenas\[\], estado |

**Cambio de valor.** Toda escena mueve un valor dramático de un polo a otro (seguro→amenazado, ignorante→informado, unido→aislado). Es el criterio de existencia de la escena: si no cambia nada, sobra. Modelarlo como par `{eje, signo}` permite verificarlo automáticamente y detectar tramos planos.

**Momento narrativo doble.** Guardar `t_fabula` y `t_discurso` por separado es lo que habilita analepsis, relatos enmarcados y narradores no fiables sin romper la continuidad.

## Plano Mundo

El canon es lo que es verdad dentro de la ficción, con independencia de cómo se cuente. Es la fuente contra la que se verifica la continuidad.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Personaje | Agente con voluntad dentro de la ficción. | **id**, **nombre\_canonico**, alias\[\], rol\_dramatico → `rol_dramatico`, deseo, necesidad, miedo, herida, voz (léxico, sintaxis, muletillas), rasgos\_fisicos, estado\_vital → `estado_vital` |
| Lugar | Espacio donde puede ocurrir una escena. | **id**, **nombre**, tipo, atmosfera, accesos\_y\_salidas, reglas\_locales, contiene\[\] |
| Objeto | Cosa con relevancia dramática. | **id**, **nombre**, propiedades, poseedor\_actual, ubicacion\_actual |
| Faccion | Grupo con intereses propios. | **id**, **nombre**, objetivo, miembros\[\], relacion\_con\[\] |
| HechoCanonico | Proposición verdadera en la ficción. | **id**, **enunciado**, **escena\_de\_establecimiento**, certeza → `certeza_canonica`, contradice\[\] |
| ReglaDelMundo | Restricción estable que gobierna lo que puede pasar. | **id**, **enunciado**, ambito, coste, excepciones\[\] |
| EventoCronologico | Suceso situado en la fábula, se narre o no. | **id**, **t\_fabula**, participantes\[\], consecuencias\[\] |
| EstadoDelMundo | Instantánea del canon en un momento `t`. | **t**, entidades\_vivas\[\], ubicaciones, posesiones, relaciones, hechos\_vigentes\[\] |
| RegistroDeConocimiento | Quién sabe qué y desde cuándo. | **sujeto**, **hecho**, **desde\_escena**, tipo\_de\_sujeto → `tipo_de_sujeto`, grado → `grado_de_conocimiento`, fuente |

**El registro de conocimiento merece rango propio.** Tiene tres tipos de sujeto —personaje, narrador y lector— y casi todos los fallos de tensión, así como los agujeros de trama, son incoherencias en esa tabla: un personaje que actúa sabiendo algo que aún no ha descubierto, o una revelación que el lector ya tenía.

**Estado derivado, no redactado.** El `EstadoDelMundo` en `t` no se guarda a mano ni se relee del texto: se reconstruye aplicando en orden los deltas que devuelve cada escena (ver plano Proceso).

## Plano Terror

Una ontología narrativa genérica se queda corta aquí. Estas clases son las que permiten controlar el miedo como variable, no como adjetivo.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Amenaza | Lo que puede dañar y organiza la tensión de la obra. | **id**, **naturaleza**, **reglas**, limites, coste\_de\_invocacion, tell, curva\_de\_escalada, grado\_de\_explicacion\_permitido |
| FuenteDelMiedo | El mecanismo psicológico sobre el que opera la obra. | **tipo** → `fuente_del_miedo`, intensidad |
| Tell | Señal perceptible de que la amenaza está cerca. | **id**, canal\_sensorial, primera\_aparicion, fiabilidad |
| Presagio | Elemento plantado que anticipa un suceso posterior. | **id**, **escena\_de\_plantado**, escena\_de\_pago, estado → `estado_de_presagio`, sutileza |
| CurvaDeDread | Presión acumulada a lo largo de la obra. | **serie** (presión por escena), valvulas\[\], pendiente\_media, mesetas\[\] |
| Valvula | Alivio deliberado que reinicia la capacidad de asustarse del lector. | **escena**, tipo → `tipo_de_valvula`, duracion |
| PuntoDeNoRetorno | Escena tras la cual el coste de retroceder es prohibitivo. | **escena**, que\_se\_pierde |
| Deterioro | Degradación progresiva de un personaje. | **sujeto**, **eje** → `eje_de_deterioro`, serie\_por\_escena, umbral\_critico |
| SetupYPago | Par de elementos ligados: lo plantado y su cobro (registro de Chéjov). | **setup**, **pago**, distancia\_en\_escenas, estado → `estado_de_presagio` |

**El grado de explicación es un parámetro, no un descuido.** Explicar del todo la amenaza mata el miedo; no explicar nada rompe el contrato con el lector. El valor debe fijarse en el brief y verificarse al final: cuánto sabe el lector sobre la amenaza al cerrar el libro.

**La curva de dread evita el fallo más común de los sistemas generativos.** Sin este objeto explícito, un modelo produce intensidad plana o escalada monótona, porque cada escena se genera localmente y tiende a la media. Las válvulas son parte del diseño, no una concesión.

## Plano Proceso y contexto

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Brief | Contrato inicial de la obra: qué se va a escribir y bajo qué reglas. | **premisa**, **tono**, extension, referentes, prohibiciones, contrato\_con\_el\_lector |
| GuiaDeEstilo | Reglas de superficie que no deben derivar. | **persona** → `persona_narrativa`, **tiempo\_verbal** → `tiempo_verbal`, registro, densidad\_sensorial, tics\_prohibidos |
| Escaleta | Plan de escenas antes de escribirlas. | **escenas\[\]**, cambios\_de\_valor, curva\_de\_dread\_prevista |
| Borrador | Texto generado de una escena, con versión. | **escena**, **version**, texto, modelo, prompt\_hash |
| DeltaDeEscena | Diff estructurado que la escena devuelve junto al texto. | **escena**, muertes, movimientos, revelaciones, setups\_pagados, cambios\_de\_posesion, deterioros |
| Ficha | Resumen recuperable de una entidad, para inyectar en contexto. | **entidad**, resumen, version\_en\_t |
| Resumen | Condensación jerárquica: escena → capítulo → parte. | **nivel** → `nivel_de_evaluacion`, **ambito**, texto, hechos\_clave\[\] |
| AnclaDeEstilo | Pasaje ejemplar que fija la voz. | **texto**, que\_ejemplifica |
| PaseDeRevision | Pasada específica sobre el texto ya generado. | **tipo** → `tipo_de_pase`, ambito, hallazgos\[\] |

### Jerarquía de memoria

El contexto se gestiona por niveles, no metiendo todo lo que quepa.

| Nivel | Contenido | Cuándo entra |
| --- | --- | --- |
| Inmutable | Premisa, guía de estilo, reglas del mundo, voces de personaje | Siempre |
| Estado actual | Instantánea del mundo en el momento `t` de la escena | Siempre |
| Local | Escena anterior completa y resumen de las tres previas | Siempre |
| Recuperado | Fichas de las entidades presentes, setups pendientes, registro de conocimiento aplicable | Por consulta |
| Resúmenes | Condensaciones de capítulo y de parte | Según profundidad |

Tres mecanismos marcan la diferencia. El **delta por escena** hace que el estado se reconstruya acumulando diffs en vez de releyendo el texto, que es lo que no escala. Las **anclas de estilo** en el nivel inmutable contrarrestan la deriva de voz, el fallo más insidioso en obra larga. Y conviene separar la **ventana de coherencia** (local: ¿esta escena se sostiene?) de la **ventana de continuidad** (global: ¿contradice el capítulo 4?), porque son pases distintos y resolverlas con el mismo prompt degrada las dos.

## Plano Calidad

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| DimensionDeCalidad | Eje evaluable del resultado. | **id**, **nombre**, nivel → `nivel_de_evaluacion`, peso |
| Verificador | Procedimiento que puntúa una dimensión. | **id**, **tipo** → `tipo_de_verificador`, entrada, salida, umbral |
| Invariante | Regla verificable del harness, con su identificador publicado. | **id** (`INV-xx`), **enunciado**, **nivel** → `nivel_de_evaluacion`, **severidad** → `severidad`, **tipo** → `tipo_de_verificador` |
| Puerta | Condición que un artefacto debe pasar para avanzar. | **etapa**, verificadores\[\], accion\_si\_falla |
| Hallazgo | Defecto detectado, con localización. | **invariante** (`INV-xx`), **verificador**, **escena**, severidad → `severidad`, estado → `estado_de_hallazgo`, descripcion |
| AntiPatron | Fallo recurrente que se vigila explícitamente. | **id**, **sintoma**, senal\_detectable, correccion |
| Rubrica | Criterios y escala que usa un juez LLM. | **dimension**, niveles\[\], ejemplos\_ancla\[\] |

**`Invariante` y `Hallazgo` guardan cosas distintas.** `invariante` dice **qué regla se violó** y `verificador` **quién lo detectó**: la misma `INV-03` puede marcarla un juez o una regla de continuidad, y saber cuál de los dos fue es lo que permite resolver el desempate. Por eso `Hallazgo` lleva los dos y ninguno sustituye al otro.

La tabla de "Invariantes verificables" de más abajo es el catálogo de instancias de `Invariante`: dieciséis, con su identificador publicado.

### Verificadores por tipo

La clave es no pedirle a un juez LLM lo que una regla resuelve mejor, ni al revés.

- **Por regla:** continuidad de entidades, coherencia cronológica, setups huérfanos, repetición léxica, distribución de longitud de frase, porcentaje de diálogo, densidad sensorial por escena, deriva de longitud.
- **Por juez LLM con rúbrica:** función dramática de la escena, credibilidad del diálogo, eficacia del presagio, adecuación al POV, calidad del cambio de valor.
- **Solo humano:** si da miedo de verdad, si el final satisface, si la voz es distinguible de la de cualquier otra novela generada.

### Anti-patrones a modelar

| Anti-patrón | Síntoma | Señal detectable |
| --- | --- | --- |
| Deriva de voz | El registro se aplana hacia la media del modelo | Distancia estilométrica frente a las anclas |
| Amnesia de estado | Contradicciones con el canon | Delta incompatible con el estado en `t` |
| Ritmo uniforme | Todas las escenas pesan igual | Varianza baja en la curva de dread |
| Clímax anticlimático | El final no paga la tensión | Presión máxima no coincide con el clímax |
| Sobreexplicación | La amenaza deja de dar miedo | Grado de explicación por encima del fijado |
| Escena sin cambio | Relleno | `cambio_de_valor` vacío o nulo |

Dos decisiones de diseño importan más que el catálogo. Las **puertas** impiden que el error se propague: una escena no se da por buena sin pasar los checks de continuidad, porque el fallo se hereda en todas las siguientes. Y la **trazabilidad** —cada escena apunta a su beat y a su función narrativa— convierte el relleno en detectable: si no puedes nombrar la función, la escena sobra.

## Relaciones

Las relaciones son lo que convierte una taxonomía en ontología. Esta tabla es la que debe implementarse como aristas del grafo.

| Relación | Dominio | Rango | Cardinalidad | Para qué sirve |
| --- | --- | --- | --- | --- |
| contiene | Obra, Parte, Capitulo | Parte, Capitulo, Escena | 1:N | Jerarquía estructural |
| realiza | Escena | Beat | N:M | Trazabilidad de función |
| sirve\_a | Beat | ArcoNarrativo | N:M | Justifica la existencia de la escena |
| ocurre\_en | Escena | Lugar | N:1 | Continuidad espacial |
| situada\_en | Escena | MomentoNarrativo | 1:1 | Doble cronología |
| narrada\_desde | Escena | POV | 1:1 | Control de focalización |
| participa\_en | Personaje | Escena | N:M | Coherencia de presencia |
| revela\_a\_lector | Escena | HechoCanonico | N:M | Gestión de la información del lector |
| conoce | Personaje, Narrador, Lector | HechoCanonico | N:M (+ `desde_escena`) | Registro de conocimiento |
| modifica | Escena | EstadoDelMundo | 1:1 (vía delta) | Reconstrucción de estado |
| establece | Escena | HechoCanonico | 1:N | Origen del canon |
| obedece | Amenaza, Evento | ReglaDelMundo | N:M | Consistencia interna |
| se\_paga\_en | Presagio | Escena | 1:0..1 | Detección de setups huérfanos |
| escala | Escena | CurvaDeDread | 1:1 | Control de tensión |
| deteriora | Escena | Deterioro | N:M | Progresión de daño |
| contradice | HechoCanonico | HechoCanonico | N:M | Detección de conflictos |
| verificada\_por | Escena | Verificador | N:M | Puertas de calidad |
| deriva\_de | Borrador | Escena, Escaleta | N:1 | Linaje y reproducibilidad |

**La relación que más rinde es `conoce`.** Con `sujeto`, `hecho`, `grado` y `desde_escena` se pueden detectar automáticamente tres clases de fallo: personajes que actúan con información que no tienen, revelaciones repetidas al lector y tensión que se desinfla porque el lector se adelantó sin que el texto lo aprovechara.

## Vocabularios controlados

Todo atributo con valores cerrados usa exactamente estos literales. Un valor fuera de la lista es un fallo de esquema, no una variante estilística.

| Enumeración | Atributos que la usan | Valores |
| --- | --- | --- |
| `rol_dramatico` | Personaje.rol\_dramatico | protagonista, antagonista, aliado, guardian\_del\_umbral, victima, testigo |
| `persona_narrativa` | POV.persona, GuiaDeEstilo.persona | primera, segunda, tercera\_limitada, tercera\_omnisciente |
| `tiempo_verbal` | POV.tiempo\_verbal, GuiaDeEstilo.tiempo\_verbal | presente, pasado |
| `eje_de_valor` | Escena.cambio\_de\_valor.eje | seguridad, conocimiento, control, vinculo, cordura, vida |
| `signo_de_cambio` | Escena.cambio\_de\_valor.signo | positivo, negativo |
| `tipo_de_sujeto` | RegistroDeConocimiento.tipo\_de\_sujeto | personaje, narrador, lector |
| `grado_de_conocimiento` | RegistroDeConocimiento.grado | ignora, sospecha, cree, sabe |
| `estado_vital` | Personaje.estado\_vital | vivo, muerto, desaparecido |
| `certeza_canonica` | HechoCanonico.certeza | establecido, implicito, disputado |
| `fuente_del_miedo` | FuenteDelMiedo.tipo | desconocido, perdida\_de\_control, contaminacion, paranoia, culpa, aislamiento |
| `estado_de_presagio` | Presagio.estado, SetupYPago.estado | plantado, pagado, huerfano |
| `tipo_de_valvula` | Valvula.tipo | humor, ternura, informacion, seguridad\_falsa |
| `eje_de_deterioro` | Deterioro.eje | cordura, cuerpo, vinculos, recursos |
| `estado_de_escena` | Escena.estado | planificada, generada, en\_verificacion, rechazada, en\_revision, aceptada, consolidada |
| `estado_de_hallazgo` | Hallazgo.estado | abierto, resuelto, descartado |
| `tipo_de_verificador` | Verificador.tipo, Invariante.tipo | regla, juez\_llm, humano |
| `nivel_de_evaluacion` | DimensionDeCalidad.nivel, Invariante.nivel, Resumen.nivel | escena, capitulo, obra |
| `severidad` | Hallazgo.severidad, Invariante.severidad | bloqueante, mayor, menor |
| `tipo_de_pase` | PaseDeRevision.tipo | continuidad, voz, ritmo, densidad, linea |

**Por qué `estado_vital` tiene `desaparecido`.** En terror, "no se sabe si sigue vivo" es material narrativo, no un hueco de datos: colapsarlo en `vivo` o en `muerto` obliga a afirmar en el canon algo que la ficción mantiene en suspenso, y `INV-02` empezaría a dar por buenas presencias que el texto no sostiene.

**Por qué `estado_de_hallazgo` tiene `descartado`.** Separa el hallazgo que se arregló del que se revisó y se decidió que no era un problema. Sin ese tercer valor, la única forma de cerrar un falso positivo es marcarlo como `resuelto`, es decir, fingir que se corrigió algo que nunca estuvo mal, y el recuento de hallazgos deja de significar nada.

El harness usa `estado_de_escena` para saber qué transiciones son legales y cuáles indican un fallo de orquestación. El diagrama de ciclo de vida de `Docs/domain-knowledge.md` dibuja esa misma máquina de estados, pero es una vista: **los literales se copian de esta tabla, nunca del diagrama.**

## Invariantes verificables

Cada invariante es un assert que el harness ejecuta contra el estado y el texto generado. `Bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y siguen.

| ID | Invariante | Nivel | Severidad | Tipo |
| --- | --- | --- | --- | --- |
| INV-01 | Toda escena tiene `cambio_de_valor` no nulo | escena | bloqueante | regla |
| INV-02 | Todo personaje presente tiene `estado_vital = vivo` y es accesible en `EstadoDelMundo(t)` | escena | bloqueante | regla |
| INV-03 | Ningún personaje actúa sobre un hecho que no conoce en `t` | escena | bloqueante | juez\_llm |
| INV-04 | El POV no cambia dentro de una escena | escena | bloqueante | regla |
| INV-05 | Toda escena aceptada tiene su delta aplicado antes de la siguiente | escena | bloqueante | regla |
| INV-06 | Ningún `HechoCanonico` vigente contradice a otro | obra | bloqueante | regla |
| INV-07 | Toda escena realiza al menos un beat que sirve a un arco | escena | mayor | regla |
| INV-08 | `t_fabula` es monótono dentro de una línea argumental salvo analepsis declarada | capitulo | mayor | regla |
| INV-09 | Todo presagio plantado se paga antes del final | obra | mayor | regla |
| INV-10 | La amenaza no viola sus propias reglas sin pagar el coste declarado | escena | mayor | juez\_llm |
| INV-11 | El grado de explicación acumulado no supera el fijado en el brief | obra | mayor | juez\_llm |
| INV-12 | La presión máxima de la curva de dread cae en el clímax ±1 escena | obra | mayor | regla |
| INV-13 | Ningún hecho se revela dos veces al lector como si fuera nuevo | obra | mayor | regla |
| INV-14 | Cada deterioro es monótono, o su reversión está justificada en el texto | obra | menor | juez\_llm |
| INV-15 | La distancia estilométrica a las anclas se mantiene bajo umbral | capitulo | menor | regla |
| INV-16 | La varianza de la curva de dread supera el mínimo fijado | obra | menor | regla |

Cada invariante debe tener al menos un caso de prueba negativo en el harness: un fragmento que la viole deliberadamente. Una invariante que nunca ha fallado en las pruebas no está verificada, solo declarada.

## Decisiones abiertas

Estas son las que conviene fijar antes de escribir esquema o código.

- [ ] **Formalización.** No hace falta OWL salvo que quieras razonamiento automático (inferir contradicciones, clasificar instancias). Un grafo de propiedades o un esquema JSON versionado suele bastar y tiene la ventaja de ser directamente el estado que consume el sistema.
- [ ] **Granularidad de generación.** ¿La unidad que se pide al modelo es la escena completa o el beat? Afecta al tamaño del delta y al coste de revisión.
- [ ] **Persistencia del estado.** ¿Los deltas son la fuente de verdad (event sourcing) o se materializa el `EstadoDelMundo` en cada `t`? Lo primero es más fiel, lo segundo más barato de consultar.
- [ ] **Escala de la curva de dread.** ¿Presión absoluta 0–100 anotada por un juez, o relativa entre escenas contiguas? La relativa es más estable entre modelos.
- [ ] **Qué valida un humano y cuándo.** Sin esta decisión las puertas se vuelven teatro: todo pasa porque nadie las cierra.
- [ ] **Multi-obra (cerrado: una sola novela).** ¿La ontología describe una novela o una serie con canon compartido? Si es lo segundo, `Obra` dejaría de ser la raíz; con una sola novela se mantiene y el árbol no cambia.

* [ ] **Umbrales.** Las invariantes `menor` (INV-15, INV-16) necesitan números concretos antes de poder ejecutarse; sin ellos el harness las salta en silencio.
* [ ] **Corpus de fixtures.** Qué obra o fragmento sirve de caso base para los tests negativos de cada invariante.
* [ ] **Desempate juez vs. regla.** Cuando INV-03 la marca un juez LLM y la regla de continuidad no ve nada, qué gana.
