# Ontología de novelas IA — Definiciones

2026-09-21 · @Santiago Espinosa Domínguez

Documento de definiciones del harness: la referencia normativa de clases, atributos, relaciones, vocabularios e invariantes de un sistema de IA que escribe novelas largas (caso base: terror, una sola obra). El documento de diagramas Mermaid es su vista, no su fuente; ante cualquier discrepancia manda este.

## Alcance y convenciones

La ontología separa seis planos porque mezclarlos es el error habitual: lo que el texto es, lo que el mundo contiene, lo que da miedo, cómo se produce, cómo se mide y para quién se escribe. El sexto, Destinatario, llegó con `SPEC-25`.

| Plano | Pregunta que responde | Uso en el sistema |
| --- | --- | --- |
| Obra | ¿Cómo está partido y ordenado el texto? | Unidad de generación y de recuperación |
| Mundo | ¿Qué existe y qué es verdad en la ficción? | Estado canónico, base de continuidad |
| Terror | ¿Qué produce el miedo y cómo escala? | Control de tensión y de revelación |
| Proceso | ¿Qué artefactos y pasos producen el texto? | Orquestación y gestión de contexto |
| Calidad | ¿Qué es un buen resultado y cómo se verifica? | Puertas, rúbricas y métricas |

**Fábula vs. discurso.** La fábula es la historia en orden cronológico; el discurso es el orden en que se presenta. En terror la distinción es funcional, no académica: casi todo el miedo vive en la diferencia entre ambos, es decir, en lo que ya ocurrió y el lector aún no sabe. El sistema debe guardar las dos líneas por separado y poder mapearlas.

**Fichas de clase.** Cada clase se define con nombre, definición en una frase y atributos clave. Los atributos en **negrita** son obligatorios: sin ellos la instancia no puede entrar en el estado. El resto son opcionales o derivados.

**`FraseRecurrente` no es un tic prohibido, y por eso es una clase aparte.**
`GuiaDeEstilo.tics_prohibidos[]` es lo que el **autor** prohibió: una regla, que no caduca.
Una `FraseRecurrente` es lo que el **sistema** observó: puede ser falsa, y sí caduca. Una
frase que apareció dos veces en el capítulo tres y no volvió a salir no era una muletilla,
y por eso la clase guarda `apariciones` y `desde_capitulo` —para poder decidirlo— y
`ultima_aparicion` —para poder descartarla—. Alimentar `tics_prohibidos` con lo detectado
borraría el origen, y sin origen no se puede revisar.

**Las fichas no enumeran valores.** Cuando un atributo está gobernado por un vocabulario controlado, la ficha escribe `atributo → nombre_de_la_enumeracion` y nada más. Los valores viven en un solo sitio, la tabla "Vocabularios controlados". Enumerarlos también aquí es lo que hizo que las dos copias divergieran en el pasado: la ficha decía `juez LLM` donde la tabla decía `juez_llm`.

**Referencias, no prosa.** Un atributo cuyo contenido es un *puntero a otra cosa* se escribe como identificador o lista de identificadores, nunca en lenguaje natural. La ficha lo marca con `atributo[] → Clase` o `atributo → Clase`. El motivo no es de estilo: un dato en prosa solo se puede comprobar buscando palabras dentro de palabras, y todos los validadores léxicos comparten el mismo punto ciego, así que el segundo ya no cubre nada que no cubriera el primero. Escribir referencias es lo que permite que dos validadores tengan puntos ciegos distintos. **No todo debe dejar de ser prosa**: ver "Lo que debe seguir siendo prosa" al final de este documento.

**Atributos obsoletos.** Lo que deja de aplicar no se borra: se escribe ~~tachado~~ seguido de `(obsoleto)` y de qué lo sustituye. Así el nombre sigue siendo localizable por quien lea código antiguo y nadie lo reutiliza para otra cosa.

**Convención de nombres.** Clases en `PascalCase`, atributos en `snake_case`, relaciones como verbo en minúscula (`ocurre_en`, `revela`). **Todo identificador es ASCII, sin tildes ni eñes**: nombres de clase, de atributo, de enumeración, de miembro y valores. La prosa y las definiciones sí llevan tildes; lo que se escribe en código, no. El motivo es que una cadena acentuada admite dos representaciones Unicode equivalentes a la vista y distintas byte a byte, así que dos valores que se leen igual dejan de compararse iguales, y fallan en silencio. Los identificadores son estables y opacos: el nombre de un personaje puede cambiar dentro de la ficción, su `id` no.

**Uso como esquema.** El harness consume este documento como contrato, así que los nombres de clase, atributo y valor de enumeración son literales: no admiten sinónimos ni traducción. Un identificador de clase o de invariante no se reutiliza ni se renumera una vez publicado; si algo deja de aplicar, se marca como obsoleto pero no se borra. Todo lo que el harness deba comprobar aparece como invariante numerada, no como afirmación en prosa.

## Plano Obra

La **Escena** es la unidad atómica: la unidad que se genera, se verifica y se recupera. Todo lo demás son contenedores o funciones sobre ella.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Obra | La novela completa como unidad publicable. | **id**, **titulo**, **premisa**, genero, subgenero, extension\_objetivo, guia\_de\_estilo, contrato\_con\_el\_lector, dedicatoria (texto de la obra: se copia de la ficha al montar y sobrevive al borrado de la ficha, `SPEC-32`) |
| Parte | Agrupación de capítulos con unidad dramática (acto). | **id**, **orden**, funcion\_estructural, valor\_inicial, valor\_final |
| Capitulo | Unidad de lectura con corte deliberado. | **id**, **orden**, **estado** → `estado_de_capitulo`, gancho\_de\_cierre, escenas\[\] |
| Escena | Bloque continuo de tiempo y espacio con un cambio de valor. | **id**, **capitulo** → Capitulo (`SPEC-21` C-1), **pov**, **lugar**, **momento\_narrativo**, **objetivo\_dramatico**, **conflicto**, **cambio\_de\_valor**, **estado** → `estado_de_escena`, personajes\_presentes\[\], salida, longitud\_objetivo, intentos, borrador\_aceptado → Borrador |
| Beat | Micro-unidad de cambio dentro de una escena. | **id**, tipo, valor\_antes, valor\_despues, establece\[\] → HechoCanonico |

**`Beat.establece[]` es opcional, y esa es la decisión** (`SPEC-19` C-1). No todo beat añade algo al canon: muchos mueven tensión, posición o relación. Exigirlo llenaría la escaleta de listas vacías y enseñaría a rellenarlas por inercia, que es la forma más rápida de que un campo deje de significar nada. Los identificadores tienen que existir en `Escaleta.hechos_canonicos[]`: **un beat no inventa hechos, los sitúa.**
| ArcoNarrativo | Trayectoria de cambio de un personaje o de una tensión a lo largo de la obra. | **id**, **sujeto**, estado\_inicial, estado\_final, hitos\[\] |
| POV | Punto de vista y distancia narrativa de una escena. | **personaje**, **persona** → `persona_narrativa`, **tiempo\_verbal** → `tiempo_verbal`, distancia, fiabilidad |
| MomentoNarrativo | Posición de la escena en la fábula (cronología) y en el discurso (orden de lectura). | **t\_fabula**, **t\_discurso**, duracion\_ficcional |
| LineaArgumental | Hilo de trama que atraviesa varias escenas. | **id**, tipo, escenas\[\], estado |
| VersionDeObra | Una versión de la obra: la lista ordenada de sus capítulos, con identidad propia (`SPEC-23` `D-2`). La regeneración crea una nueva y la anterior no cambia. | **obra** → Obra, **numero** (la identidad; la `ronda` de `CE-5`), anterior → VersionDeObra, **capitulos\[\]** → Capitulo (en orden; un capítulo que no cambió se **comparte por referencia**), peticion → PeticionDeCambio, **commit** (con qué código se creó: `MF-27`), creada\_en |

**Cambio de valor.** Toda escena mueve un valor dramático de un polo a otro (seguro→amenazado, ignorante→informado, unido→aislado). Es el criterio de existencia de la escena: si no cambia nada, sobra. Modelarlo como par `{eje, signo}` permite verificarlo automáticamente y detectar tramos planos.

**Una versión se distingue por su número, no por sus capítulos** (`SPEC-23` `D-2`, `CE-5`, `F-43`). Con la versión representada como el conjunto de sus capítulos, regenerar y volver a aprobarlos todos daba un valor idéntico al anterior, y «se conserva la versión anterior» pasaba por no poder distinguir nada. Un capítulo compartido es **la misma fila** en las dos versiones; uno nuevo en la misma posición es otro capítulo, con otro `id`.

**Momento narrativo doble.** Guardar `t_fabula` y `t_discurso` por separado es lo que habilita analepsis, relatos enmarcados y narradores no fiables sin romper la continuidad.

## Plano Mundo

El canon es lo que es verdad dentro de la ficción, con independencia de cómo se cuente. Es la fuente contra la que se verifica la continuidad.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Personaje | Agente con voluntad dentro de la ficción. | **id**, **nombre\_canonico**, alias\[\], rol\_dramatico → `rol_dramatico`, deseo, necesidad, miedo, herida, voz (léxico, sintaxis, muletillas), rasgos\_fisicos, estado\_vital → `estado_vital`, fecha\_de\_nacimiento (ISO-8601, **opcional**: `SPEC-21` C-3) |
| Lugar | Espacio donde puede ocurrir una escena. | **id**, **nombre**, tipo, atmosfera, accesos\_y\_salidas\[\] → Lugar, reglas\_locales, contiene\[\] |
| Objeto | Cosa con relevancia dramática. | **id**, **nombre**, propiedades, poseedor\_actual, ubicacion\_actual |
| Faccion | Grupo con intereses propios. | **id**, **nombre**, objetivo, miembros\[\], relacion\_con\[\] |
| HechoCanonico | Proposición verdadera en la ficción. | **id**, **enunciado**, escena\_de\_establecimiento, **durabilidad** → `durabilidad_del_hecho`, certeza → `certeza_canonica`, contradice\[\] |
| ReglaDelMundo | Restricción estable que gobierna lo que puede pasar. | **id**, **enunciado**, ambito, coste, excepciones\[\] |
| EventoCronologico | Suceso situado en la fábula, se narre o no. | **id**, **t\_fabula** (fecha absoluta ISO-8601), participantes\[\] → Personaje (+ tipo\_de\_presencia → `tipo_de_presencia`), consecuencias\[\], lugar → Lugar, capitulo → Capitulo, duracion (minutos), escena → Escena |

**La unidad de la cronología es el evento y no el capítulo** (`SPEC-21` C-3). Un capítulo es un intervalo, no un instante: con un instante por capítulo, *«nadie está en dos lugares a la vez»* es falsa por construcción en cuanto un capítulo dure lo bastante para que alguien viaje. Una escena aporta un evento; puede haber más. Y `t_fabula` es **absoluta** porque es lo único que permite demostrar a la vez el orden —que se compara—, la ubicuidad —que necesita intervalos— y la edad, que sólo se puede restar de algo absoluto.
| EstadoDelMundo | Instantánea del canon en un momento `t`. | **t**, entidades\_vivas\[\], ubicaciones, posesiones, relaciones, hechos\_vigentes\[\], huella (la lista ordenada de deltas aplicados para llegar a él, más la semilla: identifica el estado contra el que se verificó algo, `SPEC-23` `C-3`) |
| RegistroDeConocimiento | Quién sabe qué y desde cuándo. | **sujeto**, **hecho**, desde\_escena (**opcional desde `SPEC-17`**: vacío significa *anterior al relato*), tipo\_de\_sujeto → `tipo_de_sujeto`, grado → `grado_de_conocimiento`, **fuente** → Escena \| Personaje \| `anterior_al_relato` |

**El registro de conocimiento merece rango propio.** Tiene tres tipos de sujeto —personaje, narrador y lector— y casi todos los fallos de tensión, así como los agujeros de trama, son incoherencias en esa tabla: un personaje que actúa sabiendo algo que aún no ha descubierto, o una revelación que el lector ya tenía.

**Estado derivado, no redactado.** El `EstadoDelMundo` en `t` no se guarda a mano ni se relee del texto: se reconstruye aplicando en orden los deltas que devuelve cada escena (ver plano Proceso).

## Plano Terror

**Desde `SPEC-26` v3 lo específico de terror está obsoleto** —la amenaza con su tell y su grado de explicación, la fuente del miedo, los presagios, la curva de dread y sus válvulas— y se conserva marcado, sin borrar, porque los identificadores publicados no desaparecen. **Lo que queda en este plano es narrativa general**: `SetupYPago`, `PuntoDeNoRetorno` y `Deterioro`. Terror sigue siendo un género: se escribe con su género y su tono en el prompt, como cualquier otro.

Una ontología narrativa genérica se queda corta aquí. Estas clases son las que permiten controlar el miedo como variable, no como adjetivo.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| ~~Amenaza~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Lo que puede dañar y organiza la tensión de la obra. | **id**, **naturaleza**, **reglas**, limites, coste\_de\_invocacion, tell, curva\_de\_escalada, grado\_de\_explicacion\_permitido |
| ~~FuenteDelMiedo~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | El mecanismo psicológico sobre el que opera la obra. | **tipo** → `fuente_del_miedo`, intensidad |
| ~~Tell~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Señal perceptible de que la amenaza está cerca. | **id**, canal\_sensorial, primera\_aparicion, fiabilidad |
| ~~Presagio~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Elemento plantado que anticipa un suceso posterior. | **id**, escena\_de\_plantado, escena\_de\_pago, estado → `estado_de_presagio`, sutileza |
| ~~CurvaDeDread~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Presión acumulada a lo largo de la obra. | **serie** (presión por escena), valvulas\[\], pendiente\_media, mesetas\[\] |
| ~~Valvula~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Alivio deliberado que reinicia la capacidad de asustarse del lector. | **escena**, tipo → `tipo_de_valvula`, duracion |
| PuntoDeNoRetorno | Escena tras la cual el coste de retroceder es prohibitivo. | **escena**, que\_se\_pierde |
| Deterioro | Degradación progresiva de un personaje. | **sujeto**, **eje** → `eje_de_deterioro`, serie\_por\_escena, umbral\_critico |
| SetupYPago | Par de elementos ligados: lo plantado y su cobro (registro de Chéjov). | **setup**, **pago**, distancia\_en\_escenas, estado → `estado_de_presagio` |

**El grado de explicación es un parámetro, no un descuido.** Explicar del todo la amenaza mata el miedo; no explicar nada rompe el contrato con el lector. El valor debe fijarse en el brief y verificarse al final: cuánto sabe el lector sobre la amenaza al cerrar el libro.

**La curva de dread evita el fallo más común de los sistemas generativos.** Sin este objeto explícito, un modelo produce intensidad plana o escalada monótona, porque cada escena se genera localmente y tiende a la media. Las válvulas son parte del diseño, no una concesión.

## Plano Proceso y contexto

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| Brief | Contrato inicial de la obra: qué se va a escribir y bajo qué reglas. | **premisa**, **tono**, extension, referentes, prohibiciones, contrato\_con\_el\_lector |
| GuiaDeEstilo | Reglas de superficie que no deben derivar. | **persona** → `persona_narrativa`, **tiempo\_verbal** → `tiempo_verbal`, registro, densidad\_sensorial, tics\_prohibidos\[\] (cadenas literales) |
| Escaleta | Plan de escenas antes de escribirlas. | **escenas\[\]**, **hechos\_canonicos\[\]** → HechoCanonico, **conocimiento\_inicial\[\]** (`{sujeto, hecho, grado}`: quién sabe qué **antes de la escena 1**), cambios\_de\_valor, curva\_de\_dread\_prevista (solo en obras de terror: `SPEC-26` `RF-20`), imprescindibles\[\] (`{elemento, capitulo, palabras_clave[]}`: dónde aparece cada elemento imprescindible de la ficha y qué palabras lo delatan, `SPEC-26` `RF-03`), exclusiones\_previstas\[\] (`{personaje, capitulo, estado_vital}`: quién sale de la historia y dónde, `RF-04`) |

**El plan declara quién sabe qué al empezar, y no solo qué hechos existen** (`SPEC-17` C-1). Sin esto el `RegistroDeConocimiento` arranca vacío y **ninguna acción es posible en la primera escena de una obra** (`F-32`): un personaje llega sabiendo cosas de antes del relato —Ana heredó la casa— y eso no es una revelación de ninguna escena.
| Borrador | Texto generado de una escena, con versión. | **escena**, **version**, **pov\_usado** (`persona` → `persona_narrativa`, `tiempo_verbal` → `tiempo_verbal`), texto, modelo, prompt\_hash |
| DeltaDeEscena | Diff estructurado que la escena devuelve junto al texto. | **escena**, version (la del `Borrador` del que vino; ausente si no consta, nunca cero), **cambio\_de\_valor** (`{eje, signo}`), cambios\_de\_estado\_vital\[\] (`{personaje, de, a}`, con `de` y `a` → `estado_vital`), ~~muertes~~ (obsoleto: lo sustituye cambios\_de\_estado\_vital), movimientos, revelaciones (`{sujeto, hecho}`: el sujeto **pasa a conocer** ese hecho desde esta escena), **acciones** (`{personaje, hecho}`: el personaje **obró sirviéndose** de ese hecho), setups\_pagados, cambios\_de\_posesion, deterioros |

**Una petición no edita el canon: vale en la versión nueva.** El enunciado nuevo de un hecho y el nombre nuevo de un personaje viven en la petición, y los de una versión son los del plan con los de su cadena de peticiones. `HechoCanonico` no se edita y la story bible no se versiona (`PLAN-23` `C-4`); la versión anterior sigue leyendo lo que leía.

**`revelaciones` y `acciones` son cosas distintas, y confundirlas dejó el sistema muerto sin que nada fallara** (`SPEC-16`, `F-31`). Revelar es **aprender**: es el momento en que el sujeto se entera, y es lo que escribe el `RegistroDeConocimiento`. Actuar es **obrar sirviéndose de lo ya sabido**, y es lo único que `INV-03` comprueba. Mientras `INV-03` miró las revelaciones exigía saber de antes para poder aprender, así que **ningún personaje podía llegar a saber nada nunca**.
| Ficha | Resumen recuperable de una entidad, para inyectar en contexto. | **entidad**, resumen, version\_en\_t |
| Resumen | Condensación jerárquica: escena → capítulo → parte. | **nivel** → `nivel_de_evaluacion`, **ambito**, texto, hechos\_clave\[\] → HechoCanonico |
| AnclaDeEstilo | Pasaje ejemplar que fija la voz. | **texto**, que\_ejemplifica |
| FraseRecurrente | Frase que el sistema ha visto repetirse y que puede acabar siendo una muletilla. | **texto**, **desde\_capitulo**, **apariciones**, ultima\_aparicion |
| PaseDeRevision | Pasada específica sobre el texto ya generado. | **tipo** → `tipo_de_pase`, ambito, hallazgos\[\] |
| PeticionDeCambio | Lo que el lector pide cambiar de una versión de la obra (`SPEC-23`, `PLAN-23` `C-4`). No edita nada: produce una versión nueva. | **obra** → Obra, **version\_de\_partida** → VersionDeObra, **clase** → `clase_de_peticion`, hecho → HechoCanonico, enunciado\_nuevo, personaje → Personaje, nombre\_nuevo, **texto** (las palabras del lector), salida → `salida_de_regeneracion`, capitulos\_propuestos\[\] → Capitulo. Con `hecho`, lleva `hecho` y `enunciado_nuevo`; con `nombre`, `personaje` y `nombre_nuevo` |
| ProgresoDeGeneracion | En qué punto va la generación de una obra, para enseñarlo mientras corre (`SPEC-22` `RF-60`). Cada cambio de fase añade una fila; la última es el progreso de hoy. | **obra** → Obra, **fase** → `fase_de_generacion`, capitulo (el número de capítulo en que está, 1-based; no el id), total\_de\_capitulos, **desde** (ISO-8601: cuándo entró en la fase), motivo (solo en `parada`: por qué), **ultima\_actividad** (derivada, no se persiste: lo más reciente entre `desde`, la última traza de delegación de una escena de la obra y la última llamada a tool de la obra), **segundos\_desde\_la\_ultima\_actividad** (derivada, la calcula el servidor con su reloj al responder) |

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

## Plano Destinatario

La novela se escribe **para alguien** (`SPEC-25`). Estas clases recogen quién es, qué hay que contar de él y qué no debe aparecer. Las rellena el Entrevistador preguntando al comprador; el Planificador y el Escritor solo leen la ficha terminada.

| Clase | Definición | Atributos clave |
| --- | --- | --- |
| FichaDeEntrevista | Lo acordado con el comprador: el único canal entre él y el Escritor. | **destinatario** → Destinatario, **ocasion** → `ocasion`, **genero** → `genero_de_la_historia`, **tono** → `tono_de_la_historia`, **extension** → `extension_de_capitulo` (se pregunta: `SPEC-32`), **papel** → `papel_del_destinatario`, **titulo**, **premisa** (los propone el entrevistador a partir de los recuerdos y rasgos: `SPEC-25` v3), literales\_de\_otro, regalado\_por, vetadas\[\] (cadenas), nombres\_vetados\[\] (cadenas: se vetan completos y por su nombre de pila), dedicatoria, hechos\_propuestos\[\] → HechoPropuesto, contradicciones\_resueltas\[\] |
| Destinatario | La persona que recibe la novela. | **nombre**, **edad**, elementos\[\] → ElementoPersonal |
| ElementoPersonal | Un rasgo, recuerdo, persona o mascota del destinatario. | **tipo** → `tipo_de_elemento_personal`, **descripcion**, nombre, relacion, momento (`{anio, edad}`: cuándo pasó un recuerdo), imprescindible |
| HechoPropuesto | Hecho extraído del texto libre, pendiente de que el comprador lo confirme. | **id**, **texto**, **estado** → `estado_de_hecho_propuesto` |
| PalabraVetada | Palabra o expresión que no puede aparecer en un capítulo aceptado. | **forma**, **nivel** → `nivel_de_veto`, franja, obra |
| DecisionDePolitica | Una fila del audit log del policy engine. | **tipo** → `tipo_de_decision_de_politica`, **momento**, obra, detalle |

**«otro» no es un valor vacío.** En `ocasion`, `genero_de_la_historia`, `tono_de_la_historia` y `papel_del_destinatario`, elegir `otro` obliga a guardar las palabras literales del comprador en `literales_de_otro`. Es lo que permite preguntar con naturalidad y seguir comprobando con código (`SPEC-25` `O-1`).

**La extensión no está en la ficha porque no se decide**: son 10 capítulos de 1.000 a 1.500 palabras (`SPEC-25` `RF-03`).

**Las palabras vetadas y `GuiaDeEstilo.tics_prohibidos` son cosas distintas.** Los tics son estilo y dan un hallazgo `menor`; las vetadas son política y las comprueba `INV-21`, que es `bloqueante`.

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
| ValoracionDelEditor | La nota del Editor a un criterio de un capítulo (`SPEC-26` `RF-09`). No reescribe: juzga y da una instrucción. | **criterio** → `criterio_de_edicion`, **nota** (1 a 5), **justificacion**, instruccion |
| Reverificacion | Las puertas deterministas de una escena, vueltas a pasar **en una versión** contra el estado que esa versión reconstruye (`SPEC-23` `D-1`). Sin modelo. | **version** → VersionDeObra, **escena** → Escena, **huella\_del\_estado** (la `huella` del `EstadoDelMundo` previo a la escena), **estado** → `estado_de_verificacion`, hallazgos\[\] (de esta versión; **no son filas de `Hallazgo`**, que no sabe de versiones) |
| VeredictoDePublicacion | El resultado de una ronda de la puerta de publicación (`SPEC-30`): si la versión se publica y por qué no. Lo lee la exportación a PDF (`SPEC-27`) | **obra**, **ronda**, **publica**, condiciones\[\] (cada una: la condición de `RF-01` que falla, su invariante, su capítulo, el detalle y si es reintentable), codigo\_lean, no\_ejecutadas\[\] (hoy `INV-06`: `SPEC-30` `RF-12`) |

**`Invariante` y `Hallazgo` guardan cosas distintas.** `invariante` dice **qué regla se violó** y `verificador` **quién lo detectó**: la misma `INV-03` puede marcarla un juez o una regla de continuidad, y saber cuál de los dos fue es lo que permite resolver el desempate. Por eso `Hallazgo` lleva los dos y ninguno sustituye al otro.

**Un verde solo cuenta contra la huella de su versión** (`SPEC-23` `D-1`, `MF-26`). Una `Reverificacion` cuya `huella_del_estado` no es la del estado vigente de su versión no cuenta: la escena está `sin_reverificar`, que es un verde heredado y **no es un verde**. Es un estado de la escena **en una versión** y no de `estado_de_escena`: no añade ninguna transición a la máquina.

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
| incluye | VersionDeObra | Capitulo | N:M (+ `orden`) | Qué capítulos forman una versión y en qué orden. No basta `contiene`: un capítulo compartido está en dos versiones (`SPEC-23` `D-2`) |
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
| usa | Escena | HechoCanonico | N:M (+ `tipo_de_uso_de_hecho`, `origen_de_uso`) | Dónde se **vuelve a usar** un hecho, que no es dónde nace (`SPEC-21` C-2) |
| obedece | ~~Amenaza~~ (obsoleta), Evento | ReglaDelMundo | N:M | Consistencia interna |
| se\_paga\_en | SetupYPago (antes `Presagio`, obsoleta en `SPEC-26` v3) | Escena | 1:0..1 | Detección de setups huérfanos |
| ~~escala~~ (obsoleta: `CurvaDeDread` se retiró en `SPEC-26` v3) | Escena | ~~CurvaDeDread~~ | 1:1 | Control de tensión |
| deteriora | Escena | Deterioro | N:M | Progresión de daño |
| contradice | HechoCanonico | HechoCanonico | N:M | Detección de conflictos |
| verificada\_por | Escena | Verificador | N:M | Puertas de calidad |
| deriva\_de | Borrador | Escena, Escaleta | N:1 | Linaje y reproducibilidad |
| valorado\_en | Borrador | ValoracionDelEditor | 1:N (una por `criterio_de_edicion`, hasta seis) | Las seis notas del Editor de **cada versión** del borrador, también las que no bajan del umbral: sin ellas no se puede comparar el Editor con el autor ni medir un tuning (`SPEC-31` `RF-03`, `RF-04`, `RF-08`; `PLAN-31` E4). Una valoración ilegible no deja ninguna |

**La relación que más rinde es `conoce`.** Con `sujeto`, `hecho`, `grado` y `desde_escena` se pueden detectar automáticamente tres clases de fallo: personajes que actúan con información que no tienen, revelaciones repetidas al lector y tensión que se desinfla porque el lector se adelantó sin que el texto lo aprovechara.

### Vistas derivadas de la lectura (`SPEC-22`, no se persisten)

Lo que la lectura web necesita y ninguna clase guarda. **Se calculan en el backend, al responder, y no tienen tabla**: la interfaz las recibe resueltas porque, si tuviera que deducirlas, estaría calculando dominio (`SPEC-22` `NF-06`). Son nombres literales del contrato, con las mismas reglas que un atributo.

| Vista | De qué clase | Qué es | De dónde sale |
| --- | --- | --- | --- |
| se\_acepto\_rindiendose | Escena | Verdadero si y solo si **estado** = `aceptada_por_rendicion`. Una rendida se distingue siempre de una aceptada limpia, también después de consolidar, porque una escena rendida no pasa a `consolidada` (`SPEC-30` `RF-11`) | `SPEC-22` `RF-40` |
| hallazgos\_abiertos\[\] → Hallazgo | Escena | Los hallazgos de la escena cuyo **estado** es `abierto` o `sin_veredicto`, cada uno **con su estado**: un `sin_veredicto` viaja como tal y no como `abierto`. Una lista vacía es *«se miró y no había»*, no *«no se sabe»* | `SPEC-22` `RF-39` |
| capitulos\_donde\_aparece\[\] → Capitulo | Personaje, Lugar | Los capítulos donde la entidad **aparece**, por **Capitulo.orden**: para un `Personaje`, los de las escenas en que `participa_en` (`Escena.personajes_presentes`); para un `Lugar`, los de las escenas que `ocurre_en` él (`Escena.lugar`). Una mención en el texto **no** cuenta, ni haber entrado en el contexto de la escena. Con `personajes_presentes` sin declarar, la lista del personaje es **desconocida**, no vacía | `SPEC-22` `RF-44` |
| hechos\_que\_usa\[\] → HechoCanonico | Escena | Los hechos que la escena **usa** (`usa`, con cualquier `tipo_de_uso_de_hecho`), **de la obra de la escena** y uno por hecho, con su **enunciado** del canon. Es lo que la página ofrece al lector cuando selecciona un fragmento para pedir un cambio. Una lista vacía es *«no usa ninguno»* | `PLAN-22` E14 |

## Vocabularios controlados

**No todos los del proyecto están aquí, y conviene saberlo antes de buscar.** Este
documento define los del **dominio**: lo que es verdad en la ficción o lo que el harness
comprueba sobre ella. Un vocabulario que describe infraestructura —algo que no existiría si
la novela se escribiera a mano— se declara donde vive esa infraestructura. Hoy hay uno
así: **los estados de un trabajo**, en `docs/architecture.md` § "Los estados de un
trabajo". Sigue las mismas reglas de nombres que estos, porque es el mismo código leyendo
el mismo tipo de valor.

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
| `durabilidad_del_hecho` | HechoCanonico.durabilidad | permanente, efimero |
| `tipo_de_uso_de_hecho` | relación `usa` | establece, menciona, depende, contradice |
| `origen_de_uso` | relación `usa` | regla, delta, juez\_llm, humano |
| `tipo_de_presencia` | EventoCronologico.participantes | presente, mencionado |
| `ocasion` | FichaDeEntrevista.ocasion | cumpleanos, boda, aniversario, jubilacion, nacimiento, otro |
| `genero_de_la_historia` | FichaDeEntrevista.genero | aventura, romance, comedia, fantasia, misterio, drama\_cotidiano, otro |
| `tono_de_la_historia` | FichaDeEntrevista.tono | tierno, divertido, emotivo, epico, nostalgico, otro |
| `extension_de_capitulo` | FichaDeEntrevista.extension | corta, media, larga (el rango de palabras de cada una es configuración, siempre dentro de 1.000–1.500: `SPEC-32`) |
| `papel_del_destinatario` | FichaDeEntrevista.papel | protagonista, personaje\_secundario, otro |
| `tipo_de_elemento_personal` | ElementoPersonal.tipo | rasgo, recuerdo, persona, mascota |
| `estado_de_hecho_propuesto` | HechoPropuesto.estado | propuesto, confirmado, descartado |
| `nivel_de_veto` | PalabraVetada.nivel | global, franja\_de\_edad, novela |
| `tipo_de_contradiccion` | FichaDeEntrevista.contradicciones\_resueltas | edad\_frente\_a\_genero, edad\_frente\_a\_ocasion, recuerdo\_frente\_a\_edad, juicio\_del\_modelo |
| `tipo_de_decision_de_politica` | DecisionDePolitica.tipo | coincidencia\_vetada, reescritura\_pedida, parada\_por\_vetada, instruccion\_en\_texto\_libre, contradiccion\_detectada, contradiccion\_resuelta, borrado\_al\_entregar, herramienta\_denegada, nombre\_mal\_escrito, parada\_por\_nombre |
| `criterio_de_edicion` | ValoracionDelEditor.criterio | continuidad, tono, arco, coherencia\_de\_personajes, ritmo, personalizacion |
| `clase_de_peticion` | PeticionDeCambio.clase | hecho, nombre (`PLAN-23` `C-4`) |
| `salida_de_regeneracion` | PeticionDeCambio.salida | cascada, selectiva (`S-1` y `S-2`; `SPEC-23` v2: la elige la medida del arrastre) |
| `estado_de_verificacion` | Reverificacion.estado | verificada, sin\_reverificar, fallida (`sin_reverificar` es la heredada, y **no cuenta como verde**: `D-1`) |
| `fase_de_generacion` | ProgresoDeGeneracion.fase | planificando, revisando\_plan, escribiendo, editando, resumiendo, en\_la\_puerta, publicada, parada, esperando\_revision |

**«Usar un hecho» son cuatro relaciones y no una** (`SPEC-21` C-2). Tienen condiciones de verdad distintas, consumidores distintos y distinto origen, y colapsarlas rompe las dos puntas a la vez: *«este elemento aparece en algún capítulo»* se satisface con `menciona` —exigir `depende` lo daría por incumplido—, y la regeneración selectiva necesita `depende` —y cuenta también `menciona`, **pendiente de medida** (`SPEC-21` C-2): excluirlo porque *«reescribiría media novela por una alusión de paso»* era una intuición de coste que no se había medido, y `menciona` es el único de los cuatro que mide el código—. Hoy `PARA_REGENERACION` sigue siendo `establece` y `depende` hasta que la medida lo confirme. `contradice` **no es un uso**: no cuenta como aparición y no arrastra regeneración hacia adelante, sino corrección hacia atrás. Vive en la misma relación porque es la misma arista con otro signo.

**Cuál de los cuatro cuenta lo decide cada consumidor, no esta tabla.** Es deliberado: cambiar de opinión es cambiar el conjunto de tipos que se consulta, y no hay migración detrás porque las cuatro clases de fila ya están escritas.

**`origen_de_uso` distingue lo medido de lo afirmado.** `menciona` lo calcula el código sobre el texto, así que es un dato medido; `establece` y `depende` los declara el delta, así que son afirmaciones no verificadas. Un demostrador formal no puede tratarlas igual, y sin la columna no hay forma de separarlas después. **`contradice` no lo deduce nadie todavía**, de modo que una consulta que no devuelva contradicciones está diciendo que nadie ha mirado, no que no las haya.
| ~~`fuente_del_miedo`~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | FuenteDelMiedo.tipo | desconocido, perdida\_de\_control, contaminacion, paranoia, culpa, aislamiento |
| `estado_de_presagio` | SetupYPago.estado (el nombre literal se conserva; `Presagio` está obsoleta) | declarado, plantado, pagado, huerfano |
| ~~`tipo_de_valvula`~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | Valvula.tipo | humor, ternura, informacion, seguridad\_falsa |
| `eje_de_deterioro` | Deterioro.eje | cordura, cuerpo, vinculos, recursos |
| `estado_de_escena` | Escena.estado | planificada, generada, en\_verificacion, rechazada, en\_revision, aceptada, aceptada\_por\_rendicion, consolidada |
| `estado_de_capitulo` | Capitulo.estado | abierto, cerrado |
| `estado_de_hallazgo` | Hallazgo.estado | abierto, resuelto, descartado, sin\_veredicto |

**Qué hace un `sin_veredicto`, que no es lo mismo que una violación** (`SPEC-18` C-3). *"No se pudo comprobar"* y *"se violó"* son cosas distintas, y el harness las trataba igual porque el hallazgo heredaba la severidad de su invariante. Un `sin_veredicto` **no detiene la escena** —no consta que nada se haya roto— pero **impide cerrar el capítulo**, que es donde `SPEC-10` C-2 exige que quien no se dejó auditar no gane por defecto. Es el mismo sitio en el que vive un `mayor`, y no reclasifica ninguna invariante: la severidad sigue diciendo cuánto pesa una violación **confirmada**.
| `tipo_de_verificador` | Verificador.tipo, Invariante.tipo | regla, juez\_llm, humano |
| `nivel_de_evaluacion` | DimensionDeCalidad.nivel, Invariante.nivel, Resumen.nivel | escena, capitulo, obra |
**La severidad podrá pesar, y todavía no pesa.** Para elegir el menos malo entre dos
borradores hace falta agregar hallazgos en un número, y eso exige un peso por severidad.
Los pesos **no se fijan aquí**: la calibración de otro sistema no se hereda —`main` usó
tres jueces y nosotros tenemos quince reglas y uno—. Lo que sí se hereda es la advertencia
que allí costó descubrir: **una puntuación así solo se puede comparar dentro de una misma
obra y entre intentos de la misma escena.** Dos obras distintas no son comparables porque
el muestreo del modelo no se puede fijar, así que la puntuación no es una medida estable
sino una comparación local. Copiar los pesos sin copiar esta frase es lo que haría que
alguien comparase dos novelas y creyera el número. **Caduca con:** `backend/app/features/orquestacion/`.

| `severidad` | Hallazgo.severidad, Invariante.severidad | bloqueante, mayor, menor |
| `tipo_de_pase` | PaseDeRevision.tipo | continuidad, voz, ritmo, densidad, linea |

### Correspondencia entre ejes de valor y campos del delta

`Escena.cambio_de_valor` y `DeltaDeEscena.cambio_de_valor` declaran el eje; esta
tabla dice **qué campo del delta lo evidencia**. Sirve para contrastar, no para
derivar.

**No se puede deducir el eje a partir del delta, y conviene saber por qué:**
ningún campo del delta lleva signo —`movimientos` dice que alguien se movió, no
si eso le hizo más o menos seguro—, y cuatro de los seis ejes solo tienen campo
para uno de los dos signos. Por eso el delta **declara** el eje y la tabla lo
**comprueba**: son dos fuentes independientes, y si el delta pudiera derivarlo,
la comprobación sería el propio dato mirándose al espejo.

| Eje | Campo del delta que lo evidencia | Ambigüedad |
| --- | --- | --- |
| `vida` | `cambios_de_estado_vital` | Solo el signo negativo |
| `conocimiento` | `revelaciones` | Solo el signo positivo |
| `cordura` | `deterioros` con `eje = cordura` | Sin ambigüedad relevante: `INV-14` ya contempla la reversión justificada |
| `vinculo` | `deterioros` con `eje = vinculos` | Solo el signo negativo |
| `control` | `cambios_de_posesion` | Ambiguo: el control también se pierde por coacción, y eso el delta no lo registra |
| `seguridad` | `movimientos` | El más ambiguo: un movimiento puede subir o bajar la seguridad, y una escena puede volverse insegura sin que nadie se mueva |

**`setups_pagados` no corresponde a ningún eje.** Pagar un setup es un suceso
estructural, no un movimiento de valor dramático. Queda escrito para que nadie
intente forzarlo dentro de la tabla.

### Huecos conocidos del modelo

Dos cosas que la novela puede hacer y el sistema **no puede representar**.
Aparecieron al escribir la correspondencia completa. No se resuelven aquí; se
dejan escritas para que nadie las descubra con una escena delante.

| Hueco | Qué no se puede representar |
| --- | --- |
| **El eje `vida` en positivo** | Sobrevivir a algo no deja rastro en el delta. Una escena cuyo cambio de valor es *amenazado → a salvo* declara el eje y no tiene ningún campo que lo evidencie |
| **El eje `conocimiento` en negativo** | Olvidar, dudar, o descubrir que lo que se sabía era falso no tiene campo. `revelaciones` solo suma; el registro de conocimiento solo crece |

El segundo es el más incómodo en terror, donde desaprender es material narrativo:
un personaje que descubre que su recuerdo era falso mueve el eje `conocimiento`
en negativo y el canon no sabe escribirlo.

**Por qué `estado_vital` tiene `desaparecido`.** En terror, "no se sabe si sigue vivo" es material narrativo, no un hueco de datos: colapsarlo en `vivo` o en `muerto` obliga a afirmar en el canon algo que la ficción mantiene en suspenso, y `INV-02` empezaría a dar por buenas presencias que el texto no sostiene.

**Por qué `estado_de_hallazgo` tiene `descartado`.** Separa el hallazgo que se arregló del que se revisó y se decidió que no era un problema. Sin ese tercer valor, la única forma de cerrar un falso positivo es marcarlo como `resuelto`, es decir, fingir que se corrigió algo que nunca estuvo mal, y el recuento de hallazgos deja de significar nada.

El harness usa `estado_de_escena` para saber qué transiciones son legales y cuáles indican un fallo de orquestación. El diagrama de ciclo de vida de `docs/domain-knowledge.md` dibuja esa misma máquina de estados, pero es una vista: **los literales se copian de esta tabla, nunca del diagrama.**

## Invariantes verificables

Cada invariante es un assert que el harness ejecuta contra el estado y el texto generado. `Bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y siguen.

| ID | Invariante | Nivel | Severidad | Tipo | Qué lee |
| --- | --- | --- | --- | --- | --- |
| INV-01 | Toda escena tiene `cambio_de_valor` no nulo | escena | bloqueante | regla | `Escena.cambio_de_valor` |
| INV-02 | Todo personaje presente tiene `estado_vital = vivo` y es accesible en `EstadoDelMundo(t)`. El estado vital que cuenta es el que deja la propia escena: un desaparecido que el delta de la escena devuelve a `vivo` puede estar presente (decisión del autor, 2026-09-24; familia de `SPEC-16`). Punto ciego: las puertas leen el delta, no la prosa | escena | bloqueante | regla | `Escena.personajes_presentes`, `EstadoDelMundo.entidades_vivas`, `EstadoDelMundo.ubicaciones`, `Lugar.accesos_y_salidas` |
| INV-03 | Ningún personaje actúa sobre un hecho que no conoce en `t` | escena | bloqueante | regla | `RegistroDeConocimiento` **más las `revelaciones` del delta que juzga** (`SPEC-17` C-4: `t` dentro de una escena es un intervalo), `HechoCanonico.escena_de_establecimiento`, `MomentoNarrativo.t_fabula`, **`acciones` del delta** (no `revelaciones`: `SPEC-16` C-1) |
| INV-04 | El POV no cambia dentro de una escena | escena | bloqueante | regla | `Escena.pov`, `Borrador.pov_usado` |
| INV-05 | Toda escena aceptada tiene su delta aplicado antes de la siguiente | escena | bloqueante | regla | `DeltaDeEscena`, `EstadoDelMundo` |
| INV-06 | Ningún `HechoCanonico` vigente contradice a otro | obra | bloqueante | regla | `HechoCanonico.contradice`, `EstadoDelMundo.hechos_vigentes` |
| INV-07 | Toda escena realiza al menos un beat que sirve a un arco | escena | mayor | regla | `Beat.sirve_a`, `ArcoNarrativo` |
| INV-08 | `t_fabula` es monótono dentro de una línea argumental salvo analepsis declarada | capitulo | mayor | regla | `MomentoNarrativo.t_fabula`, `LineaArgumental` |
| INV-09 | Todo setup plantado se paga antes del final (antes decía «presagio»: `SPEC-26` v3 lo apunta a `SetupYPago`, que es narrativa general) | obra | mayor | regla | `SetupYPago.estado` |
| ~~INV-10~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | La amenaza no viola sus propias reglas sin pagar el coste declarado | escena | mayor | juez\_llm | `ReglaDelMundo`, `Amenaza`, deterioros del delta |
| ~~INV-11~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | El grado de explicación acumulado no supera el fijado en el brief | obra | mayor | regla | `HechoCanonico` revelados, `Amenaza.grado_de_explicacion_permitido` |
| ~~INV-12~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | La presión máxima de la curva de dread cae en el clímax ±1 escena | obra | mayor | regla | `CurvaDeDread.serie` |
| INV-13 | Ningún hecho se revela dos veces al lector como si fuera nuevo | obra | mayor | regla | revelaciones del delta acumuladas |
| INV-14 | Cada deterioro es monótono, o su reversión está justificada en el texto | obra | menor | regla | `Deterioro.serie_por_escena` |
| INV-15 | La distancia estilométrica a las anclas se mantiene bajo umbral | capitulo | menor | regla | `Borrador.texto`, `AnclaDeEstilo.texto` |
| ~~INV-16~~ **(obsoleta: `SPEC-26` v3 `RF-21`)** | La varianza de la curva de dread supera el mínimo fijado | obra | menor | regla | `CurvaDeDread.serie` |
| INV-17 | La longitud de la escena cae dentro de su `longitud_objetivo` | escena | mayor | regla | `Borrador.texto`, `Escena.longitud_objetivo` |
| INV-18 | Todo hecho que los `beats` de una escena prometían establecer aparece en su delta | escena | mayor | regla | `Beat.establece[]`, `revelaciones` del delta, `HechoCanonico.escena_de_establecimiento` |
| INV-21 | Ningún capítulo aceptado contiene una palabra vetada de ninguno de los tres niveles, tras normalizar mayúsculas, acentos, plurales y género gramatical | capitulo | bloqueante | regla | `Borrador.texto`, `PalabraVetada.forma`, `Destinatario.edad` |
| INV-22 | Los nombres del destinatario y de los personajes aparecen escritos exactamente como en la story bible: ningún nombre parecido que no sea igual | escena | bloqueante | regla | `Borrador.texto`, `Personaje.nombre_canonico`, `Destinatario.nombre` |
| INV-23 | Las palabras clave de cada imprescindible aparecen en su capítulo previsto | escena | mayor | regla | `Borrador.texto`, `Escaleta.imprescindibles` |
| INV-24 | Cada imprescindible aparece en al menos un capítulo de la novela | obra | bloqueante | regla | `Escaleta.imprescindibles`, relación `usa` |
| INV-25 | La prosa no se repite: el nombre del destinatario no supera su umbral por capítulo y ninguna frase larga se repite entre capítulos | obra | menor | regla | `Borrador.texto`, `FraseRecurrente` |
| INV-26 | El Editor da a cada criterio de un capítulo al menos la nota umbral | escena | mayor | juez\_llm | `Borrador.texto`, `ValoracionDelEditor` |
| INV-27 | El juicio de obra no encuentra un arco roto ni un final abrupto | obra | mayor | juez\_llm | resúmenes de capítulo, `Borrador.texto` del último capítulo |
| INV-28 | La verificación formal de la cronología de la obra devuelve `0`: ninguna violación de `L-1`…`L-4`, y con dato bastante para mirar (`2` no es `0`) | obra | bloqueante | regla | `EventoCronologico`, fechas de nacimiento, `specs/lean/` |
| INV-29 | Ningún capítulo de una versión publicada está en `aceptada_por_rendicion` | obra | bloqueante | regla | `estado_de_escena` de las escenas de cada capítulo |
| INV-30 | La lectura web de una versión renderiza la portada con su dedicatoria, el índice con todos los capítulos en orden y las fichas con enlaces que llevan a su capítulo, comprobado en el navegador con el browser MCP (`SPEC-22` `RF-58`) | obra | mayor | juez\_llm | la web servida, por Playwright MCP |

**La columna «Qué lee» existe para hacer verificable una regla del recorte.** `SPEC-12`
fija que la forma reducida de un bloque de contexto **nunca puede llevarse lo que lee una
invariante `bloqueante` de nivel escena**: si lo hace, la puerta sigue en pie y ya no puede
decidir. Sin esta columna esa regla es una intención, porque nadie sabe qué lee cada una.
Es la misma exigencia que el proyecto aplica a todo lo demás: una regla que nadie puede
comprobar no está verificada, solo declarada.

**Lo que el plan declara puede no estar todavía en el texto, y eso es un dato.**
`HechoCanonico.escena_de_establecimiento` y `Presagio.escena_de_plantado` son **opcionales**
desde `SPEC-15`: significan *dónde lo establece o lo planta el texto*, no *dónde nació*. Un
hecho declarado sin establecer y un presagio `declarado` sin plantar son **defectos
nombrables**: la obra prometió algo en su plan y el texto no lo entregó. Antes ni siquiera
se podían escribir.

**Y lo de `Presagio` era peor que lo de `HechoCanonico`.** Con `escena_de_plantado`
obligatorio, un presagio previsto y no plantado era **inexpresable**, no invisible. La
diferencia importa: **lo invisible se puede buscar; lo inexpresable ni se puede escribir.**

**Un hecho puede establecerse en una escena que el plan no previó, y se marca.** Prohibirlo
obligaría a replanificar por cada hallazgo del texto; no marcarlo perdería la diferencia
entre lo planificado y lo improvisado, que es justo lo que declarar los hechos conserva.

**Qué hechos existen lo declara el plan; quién los sabe es otra cosa.** `HechoCanonico`
responde a *"¿esto es verdad en la ficción?"* y `RegistroDeConocimiento` a *"¿quién lo sabe,
y desde cuándo?"*. Son dos preguntas y juntarlas sale caro: al derivar la lista de hechos
disponibles del registro de conocimiento se creó un **punto muerto** —no había hechos hasta
que alguien los supiera, y nadie podía saberlos hasta que existieran— y una generación
entera de seis escenas salió hueca sin que nada fallara (`F-29`). Es la misma forma de error
que confundir `certeza` con `durabilidad`: dos ejes independientes tratados como uno.

**La durabilidad decide qué se recorta del estado, no qué necesita una puerta.** Son dos
ejes que se confunden al escribir y solo se separan cruzando dos tablas. Al implementar
`PLAN-01` C1 salió el caso: la forma reducida del estado del mundo se quedaba con los hechos
`permanente`, y `INV-03` necesita la `escena_de_establecimiento` de **cualquier** hecho sobre
el que el delta declare una acción —para comprobar que obrar no precede a conocer; `SPEC-16`
C-1 retiró de aquí la comparación contra las revelaciones— y un hecho `efimero`
tiene esa fecha igual que uno permanente. Un dato puede ser perfectamente efímero **y**
imprescindible para una puerta, y quedarse solo con lo duradero se lo lleva.

**Y `durabilidad` no se deriva de `certeza`.** Son ejes independientes: *"la puerta está
abierta"* es `establecido` y `efimero`; *"la casa no quiere que se vayan"* es `implicito` y
`permanente`. Derivar una de la otra confundiría cuánto sabemos de algo con cuánto dura, y
el recorte se llevaría hechos estructurales por implícitos.

**`INV-17` existe porque un juez no debe contar palabras.** Una escena fuera de su
`longitud_objetivo` no la caza ninguna invariante de juicio: repartir toda la auditoría
entre jueces deja fuera lo que ninguno mira. El caso que lo demostró —un capítulo de 944
palabras, 256 por debajo del mínimo, aprobado por el mismo validador que en el intento
anterior había pedido acortarlo— está escrito junto a la Regla 2 de `docs/verification.md`.
Es `mayor` y no `menor` porque un `menor` no bloquea el cierre de capítulo desde `SPEC-04`,
así que una escena corta entraría firmada y nadie la vería, que es exactamente el fallo que
la motivó.

**`INV-18` es la primera invariante que mira el plan** (`SPEC-19`). Las diecisiete anteriores miran el texto, el delta o el estado, y ninguna compara lo que la escaleta prometió con lo que la escena entregó. Su severidad es `mayor` porque **no corrompe el canon** —lo que falta es una declaración, no una falsedad— pero **impide cerrar el capítulo**, que es lo que corta el hueco por el que `INV-03` acababa bloqueando dos escenas después de la causa (`F-37`).

**Su punto ciego, declarado como exige la Regla 2:** compara **dos declaraciones** —el plan y el delta— y no ve el texto. Un modelo que declare la revelación sin escribirla la pasa limpiamente. Eso lo cubre `INV-11`, que es un juez, y es un punto ciego distinto del que ya tenían las demás.

**`sin_veredicto` pesa el máximo de la escala, no más que la escala.** La frase "pesa lo
máximo posible" invita a leerlo como un peso que gana a cualquier combinación, y **no es
eso**. Un validador mudo es un agujero en la validación, y por eso pesa lo máximo; pero no
es **peor** que un fallo confirmado: uno dice que algo está mal, el otro que no sabemos. Si
el mudo ganara siempre, un intento con un juez caído sería automáticamente peor que otro con
tres fallos reales, y eso no es cierto. Toma el mayor valor de los pesos por severidad, sea
cual sea ese valor cuando se fije.

**`sin_veredicto` no es un hallazgo más.** Significa que el verificador no llegó a emitir
juicio: su salida no se pudo interpretar. **Pesa lo máximo posible**, porque si no
auditarse saliera barato la auditoría sería decorativa, y un intento que no se dejó
auditar nunca debe ganar por defecto a uno que sí. Los campos obligatorios de `Hallazgo`
**no se relajan**: `descripcion` y la localización se rellenan con **qué se intentó
comprobar y dónde**, que es información que sí existe. Lo que falta es el juicio, no el
contexto.

**Una `bloqueante` no admite rendición; `mayor` y `menor` sí.** La asimetría no es
arbitraria: una escena aceptada **aplica su delta al estado del mundo**, así que rendirse
ante una `bloqueante` mete una falsedad en el canon y todas las escenas siguientes se
generan encima. Degradar la prosa y corromper el estado no son el mismo riesgo, y del
segundo no se sale: no hay forma de deshacer un delta que ya heredaron treinta escenas.
Para las `bloqueante`, `Escena.intentos` cuenta y se enseña, y la salida es humana —editar
la escaleta, cambiar la escena, corregir el canon—. Para el resto, se agotan los intentos,
se elige el menos malo, `borrador_aceptado` dice cuál y la escena queda en
**`aceptada_por_rendicion`**.

**Es un estado y no un campo**, por el mismo motivo por el que `abandonado` no es un campo
sobre `fallido`: una escena que pasó sus comprobaciones y otra que agotó los intentos no
son el mismo hecho, y cualquier interfaz que mire solo el estado las confundiría. Aquí pesa
más que en un trabajo, porque **el delta de una escena rendida entra igual al canon** y
quien lea el manuscrito después necesita saber cuáles fueron. Y permite contar cuántas
escenas de una obra se aceptaron rindiéndose, que es una medida de salud del sistema y con
un campo se pierde.

**Tres invariantes son de tipo `regla` y escalan al juez para desempatar.** `INV-03`, `INV-11` e `INV-14` eran de tipo `juez_llm` y su núcleo resultó ser una comparación: una resta sobre una serie numérica, un conteo, y un cruce de identificadores. La regla decide primero y el juez solo interviene en lo que la regla no puede ver: si una reversión está justificada en el texto (`INV-14`), si una revelación implícita cuenta (`INV-11`), y si un personaje **actúa sobre** un hecho que el delta no declaró (`INV-03`). El escalado se describe aquí y no en la columna `Tipo` porque `tipo_de_verificador` tiene tres valores y ninguno significa "regla con desempate": el tipo dice **quién decide primero**.

**`INV-03` conserva su severidad `bloqueante`.** Reclasificarla es fácil de leer como un ablandamiento y no lo es: lo que cambia es **quién decide**, no **cuánto pesa**. Sigue deteniendo la escena en la puerta; lo que ya no hace es detenerla basándose en un modelo cuya fiabilidad no está medida.

Cada invariante debe tener al menos un caso de prueba negativo en el harness: un fragmento que la viole deliberadamente. Una invariante que nunca ha fallado en las pruebas no está verificada, solo declarada.

## Lo que debe seguir siendo prosa

**Léase antes de convertir ningún atributo más en referencia.** El principio de
"referencias, no prosa" tiene un límite, y aplicarlo en bloque empobrece el
modelo en vez de hacerlo comprobable.

Estos atributos son prosa **porque su contenido es prosa**, y convertirlos en
identificadores no los haría verificables: los haría más pobres.

| Atributo | Por qué se queda |
| --- | --- |
| `HechoCanonico.enunciado` | Es una proposición sobre la ficción. Un identificador no dice qué es verdad, solo que algo lo es |
| `ReglaDelMundo.enunciado` | Igual: la restricción **es** su redacción |
| `Personaje.deseo`, `necesidad`, `miedo`, `herida` | Son la interioridad del personaje. Enumerarlos produciría un catálogo de arquetipos, que es justo lo que el sistema intenta no escribir |
| `Escena.conflicto` | El conflicto concreto de una escena no se repite lo bastante como para tener catálogo |
| `AnclaDeEstilo.texto` | Es un pasaje ejemplar. Su valor está en la prosa literal |

La pregunta que decide, y que conviene hacerse siempre antes de convertir algo:
**¿el atributo apunta a otra cosa, o la contiene?** Si apunta, es una referencia.
Si la contiene, es prosa y se queda.

## Decisiones abiertas

Estas son las que conviene fijar antes de escribir esquema o código.

- [ ] **Formalización.** No hace falta OWL salvo que quieras razonamiento automático (inferir contradicciones, clasificar instancias). Un grafo de propiedades o un esquema JSON versionado suele bastar y tiene la ventaja de ser directamente el estado que consume el sistema.
- [ ] **Granularidad de generación.** ¿La unidad que se pide al modelo es la escena completa o el beat? Afecta al tamaño del delta y al coste de revisión. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
- [ ] **Persistencia del estado.** ¿Los deltas son la fuente de verdad (event sourcing) o se materializa el `EstadoDelMundo` en cada `t`? Lo primero es más fiel, lo segundo más barato de consultar. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
- [ ] **Escala de la curva de dread.** ¿Presión absoluta 0–100 anotada por un juez, o relativa entre escenas contiguas? La relativa es más estable entre modelos. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
- [ ] **Qué valida un humano y cuándo.** Sin esta decisión las puertas se vuelven teatro: todo pasa porque nadie las cierra.
- [ ] **Multi-obra (cerrado: una sola novela).** ¿La ontología describe una novela o una serie con canon compartido? Si es lo segundo, `Obra` dejaría de ser la raíz; con una sola novela se mantiene y el árbol no cambia.

* [ ] **Umbrales.** Las invariantes `menor` (INV-15, INV-16) necesitan números concretos antes de poder ejecutarse; sin ellos el harness las salta en silencio. **Se contesta sola** con una traza real.
* [ ] **Corpus de fixtures.** Qué obra o fragmento sirve de caso base para los tests negativos de cada invariante.
* [ ] **Una invariante para lo declarado y nunca entregado.** `SPEC-15` hizo nombrable un defecto que antes no existía: un `HechoCanonico` declarado y nunca establecido, y un `Presagio` `declarado` y nunca plantado. **No se amplía `INV-09`**, y el motivo es que no son el mismo daño: un presagio nunca plantado **incumple el plan**; uno plantado y no pagado **rompe una promesa al lector**. El segundo lo nota quien lee; el primero, solo quien compara plan y texto. Probablemente sea `menor` — pero desde `SPEC-04` un `menor` **no bloquea el cierre de capítulo**, así que una obra podría firmarse habiendo incumplido su propio plan. Merece mirarse con calma antes de fijar la severidad.
* [ ] **Una invariante para el conocimiento adquirido sin fuente.** `SPEC-16` decidió que revelar es **aprender**, así que un personaje que se entera de algo que solo sabía otro ya no viola `INV-03`. **Pero sigue siendo un defecto**: no es actuar con conocimiento indebido, es **adquirir conocimiento sin fuente**, y en terror esa es la diferencia entre un misterio y un agujero de guion. Es lo que ocurrió en `F-24`, la única detección real del harness hasta hoy, y dejarlo sin recoger la degradaría a falso positivo. `RegistroDeConocimiento.fuente` existe desde `SPEC-03` **precisamente para esto** y no lo comprueba nadie. La invariante exigiría que toda revelación deje al sujeto sabiendo algo con una fuente que lo explique.
* [ ] **Si `FraseRecurrente` se convierte en invariante.** La clase guarda la señal; nadie la comprueba todavía. Puede quedarse como material para el Revisor o pasar a ser `INV-18`.
* [ ] **Los pesos por severidad.** Hacen falta para `Escena.borrador_aceptado`: sin un número no se puede elegir el menos malo. Salen de medir sobre esta implementación, no de copiar los de `main`. **Se contesta sola** con una traza real.
* [ ] **Desempate juez vs. regla.** Con INV-03 ya de tipo `regla` y el juez como desempate, la pregunta es operativa y no teórica: falta decidir qué gana cuando la regla no ve nada y el juez marca. Aplica igual a INV-11 y a INV-14. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide. **La traza dirá cuántas veces discrepan y en qué dirección, no quién gana.**
