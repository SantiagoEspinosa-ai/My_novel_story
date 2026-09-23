---
id: SPEC-20
titulo: El frontend, y el contrato que nadie comprueba
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-20 — El frontend, y el contrato que nadie comprueba

## Qué problema resuelve

`frontend/` no existe. `A-09` eligió su estructura, `Docs/architecture.md` § "Frontend —
React" enumeró sus vistas y sus dos reglas de presentación, y `VER-16`…`VER-19` llevan desde
entonces esperando a una carpeta que nadie ha creado. Esta spec decide **qué frontend se
construye y contra qué se valida**, no cómo se construye.

Pero el hueco que importa no es la carpeta que falta, sino **la frontera**. Hoy el contrato
entre las dos piezas vive en una tabla de markdown —`SPEC-01` §3.2.1— y **el código ya no la
cumple**: la tabla promete `GET /escenas/{id}`, `GET /trabajos/{id}`, `GET /trabajos` y
`POST /obras/{id}/escaleta`, y ninguno de los cuatro está montado; promete que
`GET /obras/{id}` devuelve partes, capítulos con su `estado_de_capitulo` y escenas con su
`estado_de_escena`, y lo que devuelve es una lista de identificadores de capítulo. **La tabla
no se enteró**, porque una tabla en prosa no falla cuando el código cambia.

Eso es la **Regla 5 de `Docs/verification.md` en esta frontera**: una forma fijada y un
significado que cada lado deduce por su cuenta. Mientras las dos intuiciones coinciden,
funciona y nadie se entera; cuando divergen, **las dos partes cumplen el contrato y el sistema
está roto**, sin error y sin nada que falle. Con un frontend delante, el síntoma no es una
excepción: es una página que pinta un cero donde no se midió nada, o que muestra un texto sin
sus hallazgos. Exactamente el fallo que las puertas existen para evitar.

Y hay una segunda mitad, que es de dónde salen las pruebas. `D3-5` de `REV-01` ya lo señaló
sobre `RF-23` y `RF-25`: **un requisito de backend no puede cerrarse con una prueba de
frontend**, y la fila `VER` hubo que partirla en dos. La misma raya vale en el otro sentido y
es el principio de esta spec.

---

## C-1 · El contrato es un esquema OpenAPI congelado y versionado

FastAPI ya genera el esquema OpenAPI de la API. **Ese esquema se congela como artefacto del
repositorio y pasa a ser el contrato**: lo que el frontend puede suponer del backend es lo que
ahí está escrito, y nada más. Dónde vive el artefacto, con qué nombre y en qué formato lo
decide el plan.

Congelarlo hace dos cosas que una tabla no hace. Lo vuelve **comparable** —dos ficheros se
diferencian, dos prosas no— y lo vuelve **fechable**: se ve en qué commit cambió el contrato y
quién lo firmó, que es lo que hoy no se puede saber de `SPEC-01` §3.2.1.

No se escribe a mano. Un contrato redactado aparte del código es un tercer documento que
también deriva; el congelado **se deriva del backend** y su única fuente es el esquema que
FastAPI genera.

## C-2 · Un validador compara el congelado con el que el backend genera hoy

**Si el backend cambia y el contrato no, falla.** Se genera el esquema del backend actual, se
compara con el congelado y cualquier diferencia es un fallo, no un aviso. Congelar sin
comparar no sirve de nada: el fichero envejecería en silencio, que es el defecto que esta spec
viene a cerrar.

Tres cosas sobre este validador, y las tres son decisiones:

1. **No es una prueba de frontend** (`C-4`). Cruza los dos lados de la frontera, así que no
   vive con ninguno: es un validador del harness, como los que comprueban documentos.
2. **Falla del lado que se movió.** El mensaje dice qué operación, qué campo y en qué
   dirección cambió. Un "el contrato no coincide" obliga a diffear a mano y se acaba
   regenerando el congelado sin mirar, que es peor que no tenerlo.
3. **Actualizar el congelado es un acto deliberado y va en el mismo commit que el cambio de
   la API.** Es la misma exigencia que `VER-21` le hace a una migración: el cambio y su
   consecuencia, juntos o ninguno.

**Su punto ciego, declarado:** compara **forma**, no **significado**. Un campo que conserva su
nombre y su tipo y cambia lo que quiere decir pasa entero. Por eso hace falta `C-3`, y por eso
`C-3` no es una nota de estilo.

## C-3 · El contrato dice qué significa cada campo, no solo su forma

Es la Regla 5 escrita como requisito. Cada operación y cada campo del esquema congelado llevan
**qué significan**, y los valores cerrados viajan como enumeración —`estado_de_escena`,
`estado_de_capitulo`, `estado_de_hallazgo`, `severidad`— con los literales de
`Docs/definitions.md`, no como cadena libre. Un valor fuera de la enumeración es un error de
validación en el esquema, igual que lo es en Pydantic.

Dos significados que **el esquema tiene que poder expresar**, porque son justo los dos que el
proyecto ya sabe que se confunden:

- **Ausente no es cero** (`RF-25`, `VER-19`). Un dato sin medir se transmite como ausente o
  nulo y **nunca como `0`**. Si el contrato permite las dos lecturas para el mismo campo, la
  interfaz acierta pintando lo que le llega y el dato miente: es el punto ciego que `VER-19`
  ya tiene declarado, y se cierra en el contrato o no se cierra.
- **Un `409` es contrato, no texto libre.** Hoy el cuerpo que acompaña a un conflicto es un
  diccionario distinto por endpoint, así que el esquema congelado diría de él que es
  cualquier cosa. Los cuerpos de error que el frontend necesita para actuar —qué escenas no
  están `consolidada`, qué hallazgos `mayor` siguen abiertos (`RF-28`, `RF-29`)— llevan forma
  declarada.

## C-4 · Los validadores del frontend comprueban el frontend

**Principio de esta spec.** Una prueba del frontend falla cuando el frontend está mal. Si
falla porque el backend devolvió otra cosa, no está probando la interfaz: está duplicando la
suite del backend, con menos detalle y más lentitud, y el día que el backend cambie habrá dos
sitios que arreglar y una verdad repartida.

De ahí el corolario operativo: **las pruebas del frontend no arrancan un backend.** Se validan
contra el contrato congelado de `C-1` y contra datos que se derivan de él. Un backend
corriendo dentro de una prueba de interfaz mete en ella todo lo que el backend pueda hacer
mal.

Esto ya está decidido y esta spec solo lo lleva a su consecuencia: `D3-5` obligó a partir en
dos las filas que trazaban un requisito de backend a una prueba de frontend, y
`Docs/architecture.md` fija la frontera —*el frontend nunca toca la base de datos y nunca
calcula nada del dominio*—. **El backend devuelve, la interfaz muestra.** Si para pintar algo
la interfaz tuviera que calcularlo, **falta un campo en la respuesta** y el arreglo es del
backend.

La contrapartida se declara aquí y no se esconde: validado así, **el frontend no comprueba que
el backend diga la verdad**. Eso lo comprueban las filas `VER` del backend, y que los dos
lados sigan hablando del mismo contrato lo comprueba `C-2`. Ningún otro sitio.

## C-5 · Índice de capítulos navegable

La obra se recorre por su estructura: partes, capítulos en orden y escenas en orden, cada
capítulo con su `estado_de_capitulo` y cada escena con su `estado_de_escena`. Desde el índice
se llega al texto de un capítulo y de ahí al de una escena.

**Ninguna escena se muestra sin su estado y sus hallazgos abiertos** (`VER-18`,
`Docs/architecture.md`). Vale también dentro de la lectura continua de un capítulo: un texto
suelto induce a darlo por bueno. Una escena `aceptada_por_rendicion` se distingue siempre de
una `aceptada`, porque no son el mismo hecho (`SPEC-10`).

El orden, los estados y la pertenencia de una escena a su capítulo **llegan resueltos de la
API**. Hoy no llegan, y no es un detalle: ver `G-01` y `G-02`.

## C-6 · Fichas de personajes y lugares, con enlace a los capítulos donde aparecen

Una ficha muestra lo que el canon sabe de una entidad —`Personaje` con su `nombre_canonico`,
sus alias, su `rol_dramatico` y su `estado_vital`; `Lugar` con su `nombre` y su atmósfera— y
**los capítulos en los que aparece, enlazados**.

"Aparece" tiene aquí un significado exacto y no se deja a la intuición: para un `Personaje` es
la relación `participa_en`, y para un `Lugar` es `ocurre_en`, las dos de
`Docs/definitions.md`. Lo que no es: aparecer no es que la ficha entrara en el contexto de la
escena, ni que el texto mencione el nombre.

**La lista de capítulos la calcula el backend.** Deducirla en el navegador a partir de las
escenas sería calcular dominio, que es justo lo prohibido.

Ninguna de las dos relaciones está persistida hoy, y las dos clases del canon tampoco existen
como tales: `G-03` y `G-04`.

## C-7 · Portada con dedicatoria

La obra se abre por una portada con su `titulo` y una **dedicatoria**. La dedicatoria la
escribe una persona y **la guarda el backend**, porque el frontend no persiste nada.

`Obra` no tiene hoy ese atributo, así que es un cambio del dominio con su spec y su migración
(`G-11`). Y antes de eso hay que responder **de quién es la dedicatoria**: si es una por obra,
es un atributo de `Obra`; si es una por lector —"personalizada" se puede leer así—, no lo es,
y aparece un concepto que el dominio no tiene. Está en las preguntas abiertas.

## C-8 · El lector selecciona un fragmento y pide un cambio

Desde la página, quien lee **selecciona un fragmento del texto y pide un cambio en palabras
propias**. La petición queda registrada, se le devuelve un identificador de trabajo y la
página puede seguirlo; **no se responde de forma síncrona**, porque detrás hay llamadas al
modelo (`Docs/architecture.md`, regla transversal de `SPEC-01` §3.2.1).

Una selección es **un rango sobre un `Borrador` concreto y su `version`**, no sobre "el
texto": el texto cambia, y una petición anclada a un texto que ya no existe no se puede
interpretar después. Qué representa ese ancla y qué pasa cuando el texto anclado desaparece
tras una regeneración es decisión de dominio, no de interfaz (`G-10`).

La interfaz **no decide qué se regenera**. Manda la selección y la petición; qué capítulos
quedan afectados lo resuelve el backend (`C-9`).

## C-9 · Regeneración selectiva, con la versión anterior conservada y lo cambiado marcado

Al aceptar una petición, el sistema **identifica los capítulos que usan el hecho afectado,
regenera solo esos y marca cuáles cambiaron respecto a la versión anterior**. La versión
anterior **se conserva** y se puede leer entera.

Lo que esta spec fija del lado de la interfaz:

- **Qué capítulos se van a tocar se enseña antes de tocarlos.** Regenerar es caro y no es
  reversible por accidente.
- **"Cambió" lo dice el backend, capítulo a capítulo.** La interfaz no compara textos: eso
  sería calcular dominio.
- **La versión anterior es navegable**, no un respaldo invisible. Un capítulo se lee en la
  versión que uno elija, y en las dos se sigue viendo el estado de sus escenas (`C-5`).

Y lo que esta spec **no** fija, porque no le toca: qué significa que un capítulo *use* un
hecho, qué le pasa a las escenas posteriores cuya continuidad se construyó sobre el delta
viejo, y qué es una versión de la obra. Son las piezas más caras de la lista de abajo —`G-05`
a `G-09`— y **ninguna es un endpoint**: son una decisión de dominio, y esa decisión es
**`SPEC-21`**. Sin ella, `C-9` no se puede implementar, y esta spec puede aprobarse igual: declara qué
tiene que ser verdad, y declara que hoy no lo es.

---

## Lo que esta spec necesita del backend y hoy no existe

Se comprobó contra el código, no contra los documentos. Cada fila dice qué falta, qué se
rompería sin ella y de qué clase es el trabajo. **`Decisión` significa que hay algo que
acordar antes de escribir nada**, y ninguna de esas se decide aquí.

| # | Qué falta | Qué depende de ello | Clase |
| --- | --- | --- | --- |
| **G-01** | **Ninguna escena sabe a qué capítulo pertenece.** Existe la tabla `capitulo` y existe la tabla `escena`, y no hay vínculo entre las dos: la escena guarda `obra` y `orden`. Peor: el cierre de capítulo pide las escenas *del capítulo* a una consulta que filtra **por obra**, así que hoy la puerta de `RF-28` evalúa la obra entera. `Capitulo.escenas[]` es obligatorio en `Docs/definitions.md` y la relación `contiene` está en su tabla | `C-5`, `C-6`, `C-9` — y además es un defecto por sí solo, que no espera a ningún frontend | Esquema + defecto |
| **G-02** | **No hay `Parte`, ni la obra devuelve su estructura.** `SPEC-01` §3.2.1 promete partes, capítulos con estado y escenas con estado; lo que se devuelve es una lista de identificadores de capítulo, sin orden, sin estado y sin escenas | `C-5` | Esquema + API |
| **G-03** | **`Personaje`, `Lugar` y `Objeto` no existen como entidades del canon.** Lo que hay es una tabla de entidades con estado vital y ubicación, y un lugar con sus accesos. Faltan `nombre_canonico`, alias, `rol_dramatico`, y el `nombre` de `Lugar`, que el dominio marca obligatorio. La tabla de fichas guarda un resumen de texto generado al consolidar: sirve para inyectar en contexto, no para enseñar una ficha | `C-6` | Esquema |
| **G-04** | **`participa_en` y `ocurre_en` no están persistidas.** `Escena.personajes_presentes` viaja por el pipeline y no se guarda en ninguna parte; `escena.lugar` es una columna de texto sin clave foránea. "En qué capítulos aparece Marta" no se puede responder hoy, ni a posteriori | `C-6` | Esquema |
| **G-05** | **El `DeltaDeEscena` no se guarda.** `SPEC-01` §3.2.2 lo declara *fuente de verdad del estado*; el código lo aplica y lo tira. En particular se pierde `acciones` —qué personaje obró sirviéndose de qué hecho—, que es lo más cercano que el dominio tiene a *esta escena usa este hecho*. Sin el delta persistido, el estado del mundo deja de ser reconstruible, que es lo que `VER-09` comprueba | `C-9`, y `VER-09` | Esquema |
| **G-06** | **No existe la relación hecho → capítulos, y antes falta su definición.** El dominio relaciona `Escena` con `HechoCanonico` por `establece`, por `revela_a_lector` y por las `acciones` del delta; **una escena puede depender de un hecho sin ninguna de las tres**, por el solo hecho de que entrara en su contexto. Y la traza de la llamada registra fichas, presagios y resúmenes: **no registra hechos ni entradas del registro de conocimiento**, así que tampoco es reconstruible. Decidir qué cuenta como *usar un hecho* es la pieza que falta: sin ella, "estos son los capítulos afectados" es una lista cuyo significado nadie conoce, que es la Regla 5 otra vez | `C-9` | **Decisión** + esquema |
| **G-07** | **La obra no tiene versión.** El `Borrador` sí la tiene, por escena, y con su texto conservado; lo que no existe es un nombre para *la novela tal como estaba antes de esta petición*, ni nada a lo que referir "qué capítulos cambiaron respecto a la anterior" | `C-9` | **Decisión** + esquema |
| **G-08** | **Una escena `consolidada` no tiene transición de salida.** `rechazada` vuelve a `generada`, y de `consolidada` no sale nada. Además `RF-19` e `INV-05` prohíben generar mientras la anterior no esté consolidada, y el estado del mundo se reconstruye acumulando deltas **en orden**: regenerar una escena del medio invalida el estado sobre el que se escribieron todas las siguientes. Falta decidir la invalidación en cascada: qué pasa con lo posterior | `C-9` | **Decisión** |
| **G-09** | **Un capítulo `cerrado` no se reabre** (`RF-30`: dos valores y una sola transición). El alcance pide regenerar capítulos que, en una obra terminada, están cerrados. O cambia la enumeración, o la regeneración produce una versión nueva en vez de tocar la cerrada —que es `G-07`—. La interfaz no puede elegir | `C-9` | **Decisión** |
| **G-10** | **No hay lector, ni ancla de una selección.** Las dos puertas con firma humana (`RF-17`, `RF-27`) las cierra quien conduce la generación; el alcance introduce a alguien que lee y pide cambios sin firmar puertas, y el proyecto no ha decidido si son la misma persona. Y `PaseDeRevision` tiene `tipo`, `ambito` y `hallazgos[]`: ninguno ancla un rango de texto a un `Borrador` y su `version`. La feature de revisión está vacía | `C-8` | **Decisión** + esquema |
| **G-11** | **`Obra` no tiene dedicatoria** ni nada de portada. Es un atributo nuevo del dominio: spec, `Docs/definitions.md` y migración en el mismo commit. Antes hay que responder si es una por obra o una por lector (`C-7`) | `C-7` | **Decisión** + esquema |
| **G-12** | **Faltan endpoints que `SPEC-01` ya declara**: consultar una escena (`RF-23`), consultar un trabajo y listar trabajos (`RF-24`), y lanzar la escaleta. El módulo de lectura ya tiene la **forma** de la respuesta de escena y de trabajo —texto, estado y hallazgos juntos; tokens ausentes como "sin medir"— y **ningún router la expone**. Sin consultar una escena no hay vista de escena posible y `VER-18` no se puede cerrar | `C-5`, `C-8`, `C-9` | API |
| **G-13** | **No hay lectura continua.** El texto sale por escena, y el índice necesita leer un capítulo entero. `VER-60` ya habla de ensamblar un manuscrito y no hay nada que lo ensamble | `C-5` | API |
| **G-14** | **Los cuerpos de error no tienen forma declarada.** Un conflicto devuelve hoy un diccionario distinto por endpoint, de modo que el esquema congelado no diría nada de él. Lo que `RF-28` y `RF-29` obligan a enseñar —qué escenas faltan, qué `mayor` sigue abierto, qué `menor` se deja pasar— es contrato | `C-3` | API |
| **G-15** | **El frontend es una pieza desplegable aparte y el backend no declara nada sobre su origen.** Sin esa decisión, la primera llamada real desde el navegador falla por una razón que no tiene nada que ver con el contrato | `C-1` | Decisión menor |

**Dos filas de esta tabla ya no viven aquí, y conviene saberlo antes de leerla:**

- **`G-01` no es un hueco, es un defecto activo.** Que la puerta de cierre evalúe la obra
  entera en vez del capítulo está roto **hoy**, sin frontend de por medio, y contra un
  requisito ya aprobado (`RF-28`). Va por su cuenta y va antes que esta spec: no decide nada
  nuevo, así que no necesita spec propia, solo la prueba que lo caza.
- **`G-05`, `G-06`, `G-07` y `G-08` son una sola pregunta** —qué es regenerar en una obra cuya
  continuidad es acumulativa— y son **`SPEC-21`**, que las trata juntas y enumera las salidas
  posibles sin elegir ninguna. Siguen listadas arriba porque `C-9` sigue dependiendo de ellas;
  lo que ya no hace falta es decidirlas desde aquí.

## Qué queda explícitamente fuera

- **Las decisiones de `G-06` a `G-11`.** Esta spec las nombra, dice qué depende de ellas y no
  las toma. Cada una es un cambio del dominio y el dominio se cambia por su propia spec.
- **La implementación del backend que falta.** La lista de arriba es una dependencia, no el
  plan de trabajo de esta spec.
- **Autenticación y control de acceso.** El proyecto no los tiene y esta spec no los
  introduce; `G-10` solo pregunta si el lector y quien firma las puertas son la misma persona.
- **Las vistas de operación** —Puertas, Continuidad, Trabajos— que `Docs/architecture.md` ya
  enumera. Esta spec cubre la lectura de la obra y la petición de cambio; aquellas siguen
  pendientes y su tabla no se reescribe aquí.
- **Elegir tecnología dentro del frontend.** React y FSD v2.1 ya están decididos por
  `CLAUDE.md` y `A-09`; todo lo demás es del plan.
- **Publicar la obra a un formato de libro.** Portada y dedicatoria son de la interfaz de
  lectura, no de una exportación.

## Qué tiene que ser verdad al terminar

1. Existe un esquema OpenAPI congelado y versionado, derivado del backend (`C-1`).
2. Hay un validador que falla cuando el backend y el congelado divergen, y que dice qué
   cambió (`C-2`).
3. Ninguna prueba del frontend necesita un backend corriendo (`C-4`).
4. El contrato expresa la diferencia entre ausente y cero, y los vocabularios cerrados viajan
   como enumeración (`C-3`).
5. `VER-16`…`VER-19` dejan de estar a la espera: tienen dónde ejecutarse. Esta spec no las
   crea ni las reescribe.
6. El índice, las fichas y la portada se pintan **sin calcular nada del dominio en el
   navegador** (`C-5`…`C-7`).
7. Toda escena mostrada lleva su estado y sus hallazgos abiertos (`VER-18`).

**Filas nuevas en `Docs/verification.md`.** Esta spec obliga al menos a un modo de fallo
—*el contrato se movió de un lado y el otro no se enteró*, que hoy no está catalogado— y a las
filas `VER` del congelado y de su comparación. **No se numeran aquí**: los identificadores los
asigna el commit que las escribe, y el rango libre empieza hoy en `MF-26` y en `VER-65`.

## Qué gobierna esto

`CLAUDE.md` § React; `A-01`, `A-04` y `A-09` de `Docs/architecture.md`, su § "Frontend —
React" y su frontera *el frontend nunca toca la base de datos y nunca calcula nada del
dominio*; `Obra`, `Parte`, `Capitulo`, `Escena`, `Borrador`, `DeltaDeEscena`, `Personaje`,
`Lugar`, `HechoCanonico`, `PaseDeRevision` y las relaciones `contiene`, `participa_en`,
`ocurre_en`, `establece` y `revela_a_lector` de `Docs/definitions.md`; `RF-17`, `RF-19`,
`RF-23`, `RF-24`, `RF-25`, `RF-27`, `RF-28`, `RF-29` y `RF-30` de `SPEC-01`, y su §3.2.1;
`INV-05`; `VER-09`, `VER-16`, `VER-17`, `VER-18`, `VER-19`, `VER-21` y `VER-60`; la **Regla 5**
de `Docs/verification.md`; y `D3-5` de `REV-01`.

## Preguntas que hay que responder antes de aprobar

Ninguna se rellena por suposición. Una spec con huecos supuestos es peor que no tenerla,
porque parece acordada.

| # | Pregunta | Por qué bloquea |
| --- | --- | --- |
| 1 | **¿Qué significa que un capítulo *use* un hecho?** ¿Lo establece, lo revela, alguien obra con él, o basta con que entrara en su contexto? | Sin respuesta, `C-9` devuelve una lista de capítulos cuyo significado no está escrito: la Regla 5 otra vez (`G-06`) |
| 2 | **¿Qué es una versión de la obra?** ¿Una foto de los borradores aceptados, o algo que se nombra y se conserva entero? | `C-9` dice "respecto a la versión anterior" y hoy no hay nada que se llame así (`G-07`) |
| 3 | **Al regenerar un capítulo del medio, ¿qué pasa con lo que venía después?** ¿Se invalida, se marca sospechoso, o se deja como está? | El estado del mundo es acumulativo. Cualquiera de las tres es defendible y la diferencia es enorme (`G-08`) |
| 4 | **¿El lector que pide el cambio es quien firma las puertas?** | Decide si aparece un actor nuevo, y si su petición necesita aprobación antes de gastar dinero en generación (`G-10`) |
| 5 | **¿La dedicatoria es una por obra o una por lector?** | Si es por lector, deja de ser un atributo de `Obra` y aparece un concepto que el dominio no tiene (`G-11`) |
| 6 | **¿La comparación del contrato falla en CI, o solo en local?** | Un validador que no corre donde se integra no protege nada, y `C-2` es toda la protección de esta frontera |
| 7 | **¿El frontend entra ahora o después del backend que le falta?** | Quince huecos, seis de ellos con una decisión de dominio dentro. El orden lo decide quien aprueba, no esta spec |
