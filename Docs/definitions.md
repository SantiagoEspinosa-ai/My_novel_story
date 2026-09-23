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
| Obra | La novela completa como unidad publicable. | **id**, **titulo**, **premisa**, genero, subgenero, extension\_objetivo, guia\_de\_estilo, contrato\_con\_el\_lector |
| Parte | Agrupación de capítulos con unidad dramática (acto). | **id**, **orden**, funcion\_estructural, valor\_inicial, valor\_final |
| Capitulo | Unidad de lectura con corte deliberado. | **id**, **orden**, **estado** → `estado_de_capitulo`, gancho\_de\_cierre, escenas\[\] |
| Escena | Bloque continuo de tiempo y espacio con un cambio de valor. | **id**, **pov**, **lugar**, **momento\_narrativo**, **objetivo\_dramatico**, **conflicto**, **cambio\_de\_valor**, **estado** → `estado_de_escena`, personajes\_presentes\[\], salida, longitud\_objetivo, intentos, borrador\_aceptado → Borrador |
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
| Lugar | Espacio donde puede ocurrir una escena. | **id**, **nombre**, tipo, atmosfera, accesos\_y\_salidas\[\] → Lugar, reglas\_locales, contiene\[\] |
| Objeto | Cosa con relevancia dramática. | **id**, **nombre**, propiedades, poseedor\_actual, ubicacion\_actual |
| Faccion | Grupo con intereses propios. | **id**, **nombre**, objetivo, miembros\[\], relacion\_con\[\] |
| HechoCanonico | Proposición verdadera en la ficción. | **id**, **enunciado**, **escena\_de\_establecimiento**, **durabilidad** → `durabilidad_del_hecho`, certeza → `certeza_canonica`, contradice\[\] |
| ReglaDelMundo | Restricción estable que gobierna lo que puede pasar. | **id**, **enunciado**, ambito, coste, excepciones\[\] |
| EventoCronologico | Suceso situado en la fábula, se narre o no. | **id**, **t\_fabula**, participantes\[\], consecuencias\[\] |
| EstadoDelMundo | Instantánea del canon en un momento `t`. | **t**, entidades\_vivas\[\], ubicaciones, posesiones, relaciones, hechos\_vigentes\[\] |
| RegistroDeConocimiento | Quién sabe qué y desde cuándo. | **sujeto**, **hecho**, **desde\_escena**, tipo\_de\_sujeto → `tipo_de_sujeto`, grado → `grado_de_conocimiento`, **fuente** → Escena \| Personaje |

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
| GuiaDeEstilo | Reglas de superficie que no deben derivar. | **persona** → `persona_narrativa`, **tiempo\_verbal** → `tiempo_verbal`, registro, densidad\_sensorial, tics\_prohibidos\[\] (cadenas literales) |
| Escaleta | Plan de escenas antes de escribirlas. | **escenas\[\]**, cambios\_de\_valor, curva\_de\_dread\_prevista |
| Borrador | Texto generado de una escena, con versión. | **escena**, **version**, **pov\_usado** (`persona` → `persona_narrativa`, `tiempo_verbal` → `tiempo_verbal`), texto, modelo, prompt\_hash |
| DeltaDeEscena | Diff estructurado que la escena devuelve junto al texto. | **escena**, **cambio\_de\_valor** (`{eje, signo}`), cambios\_de\_estado\_vital\[\] (`{personaje, de, a}`, con `de` y `a` → `estado_vital`), ~~muertes~~ (obsoleto: lo sustituye cambios\_de\_estado\_vital), movimientos, revelaciones, setups\_pagados, cambios\_de\_posesion, deterioros |
| Ficha | Resumen recuperable de una entidad, para inyectar en contexto. | **entidad**, resumen, version\_en\_t |
| Resumen | Condensación jerárquica: escena → capítulo → parte. | **nivel** → `nivel_de_evaluacion`, **ambito**, texto, hechos\_clave\[\] → HechoCanonico |
| AnclaDeEstilo | Pasaje ejemplar que fija la voz. | **texto**, que\_ejemplifica |
| FraseRecurrente | Frase que el sistema ha visto repetirse y que puede acabar siendo una muletilla. | **texto**, **desde\_capitulo**, **apariciones**, ultima\_aparicion |
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

**No todos los del proyecto están aquí, y conviene saberlo antes de buscar.** Este
documento define los del **dominio**: lo que es verdad en la ficción o lo que el harness
comprueba sobre ella. Un vocabulario que describe infraestructura —algo que no existiría si
la novela se escribiera a mano— se declara donde vive esa infraestructura. Hoy hay uno
así: **los estados de un trabajo**, en `Docs/architecture.md` § "Los estados de un
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
| `fuente_del_miedo` | FuenteDelMiedo.tipo | desconocido, perdida\_de\_control, contaminacion, paranoia, culpa, aislamiento |
| `estado_de_presagio` | Presagio.estado, SetupYPago.estado | plantado, pagado, huerfano |
| `tipo_de_valvula` | Valvula.tipo | humor, ternura, informacion, seguridad\_falsa |
| `eje_de_deterioro` | Deterioro.eje | cordura, cuerpo, vinculos, recursos |
| `estado_de_escena` | Escena.estado | planificada, generada, en\_verificacion, rechazada, en\_revision, aceptada, aceptada\_por\_rendicion, consolidada |
| `estado_de_capitulo` | Capitulo.estado | abierto, cerrado |
| `estado_de_hallazgo` | Hallazgo.estado | abierto, resuelto, descartado, sin\_veredicto |
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

El harness usa `estado_de_escena` para saber qué transiciones son legales y cuáles indican un fallo de orquestación. El diagrama de ciclo de vida de `Docs/domain-knowledge.md` dibuja esa misma máquina de estados, pero es una vista: **los literales se copian de esta tabla, nunca del diagrama.**

## Invariantes verificables

Cada invariante es un assert que el harness ejecuta contra el estado y el texto generado. `Bloqueante` detiene la escena en la puerta; `mayor` y `menor` generan hallazgo y siguen.

| ID | Invariante | Nivel | Severidad | Tipo | Qué lee |
| --- | --- | --- | --- | --- | --- |
| INV-01 | Toda escena tiene `cambio_de_valor` no nulo | escena | bloqueante | regla | `Escena.cambio_de_valor` |
| INV-02 | Todo personaje presente tiene `estado_vital = vivo` y es accesible en `EstadoDelMundo(t)` | escena | bloqueante | regla | `Escena.personajes_presentes`, `EstadoDelMundo.entidades_vivas`, `EstadoDelMundo.ubicaciones`, `Lugar.accesos_y_salidas` |
| INV-03 | Ningún personaje actúa sobre un hecho que no conoce en `t` | escena | bloqueante | regla | `RegistroDeConocimiento`, `HechoCanonico.escena_de_establecimiento`, `MomentoNarrativo.t_fabula`, revelaciones del delta |
| INV-04 | El POV no cambia dentro de una escena | escena | bloqueante | regla | `Escena.pov`, `Borrador.pov_usado` |
| INV-05 | Toda escena aceptada tiene su delta aplicado antes de la siguiente | escena | bloqueante | regla | `DeltaDeEscena`, `EstadoDelMundo` |
| INV-06 | Ningún `HechoCanonico` vigente contradice a otro | obra | bloqueante | regla | `HechoCanonico.contradice`, `EstadoDelMundo.hechos_vigentes` |
| INV-07 | Toda escena realiza al menos un beat que sirve a un arco | escena | mayor | regla | `Beat.sirve_a`, `ArcoNarrativo` |
| INV-08 | `t_fabula` es monótono dentro de una línea argumental salvo analepsis declarada | capitulo | mayor | regla | `MomentoNarrativo.t_fabula`, `LineaArgumental` |
| INV-09 | Todo presagio plantado se paga antes del final | obra | mayor | regla | `Presagio.estado` |
| INV-10 | La amenaza no viola sus propias reglas sin pagar el coste declarado | escena | mayor | juez\_llm | `ReglaDelMundo`, `Amenaza`, deterioros del delta |
| INV-11 | El grado de explicación acumulado no supera el fijado en el brief | obra | mayor | regla | `HechoCanonico` revelados, `Amenaza.grado_de_explicacion_permitido` |
| INV-12 | La presión máxima de la curva de dread cae en el clímax ±1 escena | obra | mayor | regla | `CurvaDeDread.serie` |
| INV-13 | Ningún hecho se revela dos veces al lector como si fuera nuevo | obra | mayor | regla | revelaciones del delta acumuladas |
| INV-14 | Cada deterioro es monótono, o su reversión está justificada en el texto | obra | menor | regla | `Deterioro.serie_por_escena` |
| INV-15 | La distancia estilométrica a las anclas se mantiene bajo umbral | capitulo | menor | regla | `Borrador.texto`, `AnclaDeEstilo.texto` |
| INV-16 | La varianza de la curva de dread supera el mínimo fijado | obra | menor | regla | `CurvaDeDread.serie` |
| INV-17 | La longitud de la escena cae dentro de su `longitud_objetivo` | escena | mayor | regla | `Borrador.texto`, `Escena.longitud_objetivo` |

**La columna «Qué lee» existe para hacer verificable una regla del recorte.** `SPEC-12`
fija que la forma reducida de un bloque de contexto **nunca puede llevarse lo que lee una
invariante `bloqueante` de nivel escena**: si lo hace, la puerta sigue en pie y ya no puede
decidir. Sin esta columna esa regla es una intención, porque nadie sabe qué lee cada una.
Es la misma exigencia que el proyecto aplica a todo lo demás: una regla que nadie puede
comprobar no está verificada, solo declarada.

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
`permanente`, y `INV-03` necesita la `escena_de_establecimiento` de **cualquier** hecho que
el delta revele —para comprobar que revelar no precede a establecer— y un hecho `efimero`
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
anterior había pedido acortarlo— está escrito junto a la Regla 2 de `Docs/verification.md`.
Es `mayor` y no `menor` porque un `menor` no bloquea el cierre de capítulo desde `SPEC-04`,
así que una escena corta entraría firmada y nadie la vería, que es exactamente el fallo que
la motivó.

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
* [ ] **Si `FraseRecurrente` se convierte en invariante.** La clase guarda la señal; nadie la comprueba todavía. Puede quedarse como material para el Revisor o pasar a ser `INV-18`.
* [ ] **Los pesos por severidad.** Hacen falta para `Escena.borrador_aceptado`: sin un número no se puede elegir el menos malo. Salen de medir sobre esta implementación, no de copiar los de `main`. **Se contesta sola** con una traza real.
* [ ] **Desempate juez vs. regla.** Con INV-03 ya de tipo `regla` y el juez como desempate, la pregunta es operativa y no teórica: falta decidir qué gana cuando la regla no ve nada y el juez marca. Aplica igual a INV-11 y a INV-14. **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide. **La traza dirá cuántas veces discrepan y en qué dirección, no quién gana.**
