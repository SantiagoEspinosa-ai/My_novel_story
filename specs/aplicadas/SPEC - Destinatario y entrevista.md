---
id: SPEC-25
titulo: El destinatario, la entrevista y las palabras vetadas
estado: aplicada
aprobada_por: "autor del proyecto, en sesión (sustituir por su identificador)"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 88e3a2e
fecha: 2026-09-23
version: 3
enmienda_aprobada: 2026-09-23
---

> **Historial.** v1: redactada con las respuestas de aclaración, con `O-1` y
> `O-2` abiertas. v2: `O-1` y `O-2` resueltas por el autor. Al pasar a listas
> cerradas, la contradicción «ocasión frente a tono» deja de ser comprobable
> entre categorías de la lista (ninguna pareja de la lista es incoherente por sí
> misma) y se sustituye por «edad frente a ocasión». La de ocasión y tono sigue
> existiendo como juicio del modelo cuando algún valor es «otro» (`RF-08b`).
> v3 (enmienda del autor, 2026-09-23): **la premisa y el título los propone el
> entrevistador**, no el planificador. En sus palabras: *«el enunciado dice que la
> entrevista recoge género y tono, y la premisa sale de los recuerdos y rasgos del
> destinatario — eso es material de la entrevista»*. Entran en la ficha como
> obligatorios (`RF-02`, `RF-02b`) y en el anexo como apartado propio.

# SPEC-25 — El destinatario, la entrevista y las palabras vetadas

> **De dónde salen las decisiones.** De las respuestas del autor a las preguntas
> de aclaración del 2026-09-23. La central, en sus palabras: *«el agente
> entrevistador va a tener que obtener esa información, deja un documento para
> que este agente antes de generar la novela pregunte al usuario, lo llene y
> luego el agente escritor escriba de acuerdo a lo que escribió el agente
> entrevistador»*. Ese documento es la **ficha de la entrevista** y su plantilla
> está en el anexo.

## Qué problema resuelve

El sistema escribe hoy **una obra de terror sin destinatario**. El brief
(`BriefDeObra`) tiene premisa, género, estilo y una escaleta escrita a mano, y
ningún campo que diga **para quién** es la novela. El producto del examen es el
contrario: una novela para regalar, en la que el destinatario se reconozca.

Faltan cuatro cosas, y ninguna existe en `docs/definitions.md`:

1. **Quién es el destinatario** y qué hay que contar de él: nombre, edad,
   rasgos, recuerdos, personas y mascotas cercanas, ocasión y dedicatoria.
2. **Alguien que lo pregunte.** Un comprador no rellena un JSON. Tiene que haber
   un agente que haga las preguntas, detecte lo que falta y lo que se
   contradice, y deje por escrito lo acordado.
3. **Una forma segura de aportar texto libre.** El comprador querrá pegar una
   carta o una anécdota. Ese texto lo escribe alguien ajeno al sistema y puede
   contener instrucciones dirigidas al modelo.
4. **Palabras vetadas de verdad.** Hoy solo existe `GuiaDeEstilo.tics_prohibidos`,
   que son muletillas de estilo comprobadas por igualdad exacta. El nombre de
   una expareja o un tema doloroso son otra cosa: una política, no un estilo.

## La ficha de la entrevista

**Es el único canal entre el comprador y el Escritor.** El entrevistador la
rellena preguntando; el Planificador y el Escritor escriben a partir de ella y de
nada más que venga del comprador. Lo que no está en la ficha no llega a la
novela, y lo que el comprador dijo pero no quedó en la ficha no se usa.

Tiene dos consecuencias buscadas:

- **Se puede auditar.** Ante una novela que no gusta, la primera pregunta es si
  el fallo está en la ficha (se preguntó mal) o en el texto (se escribió mal), y
  la ficha lo contesta.
- **El texto libre nunca llega al Escritor.** Llega lo que se extrajo de él y el
  comprador confirmó (`RF-07`). Es lo que corta la inyección.

**Se pregunta con naturalidad y se anota en una lista cerrada con «otro»**
(`O-1`). Género, tono, ocasión y papel del destinatario se preguntan con las
palabras que el comprador quiera; el entrevistador anota la categoría que
corresponde y, si ninguna encaja, anota «otro» junto con las palabras literales
del comprador. Así la ficha es natural para quien la rellena y comprobable para
el código (`CLAUDE.md`: los vocabularios controlados son `Enum`).

## Qué tiene que ser verdad al terminar

### La ficha y el destinatario

- **RF-01.** Existe la ficha de la entrevista con los apartados del anexo, y
  cada apartado declara si es obligatorio.
- **RF-02.** Son obligatorios: nombre del destinatario, edad, ocasión, género,
  tono, papel del destinatario en la historia, al menos un rasgo y al menos un
  recuerdo. Una ficha sin alguno de ellos **no es un brief válido** y no arranca
  la generación.
- **RF-02b.** También son obligatorios **la premisa y el título**. Los propone el
  entrevistador a partir de los recuerdos y rasgos ya recogidos, y el comprador
  los confirma o los cambia. El planificador los recibe hechos: no los decide.
- **RF-03.** La extensión **no se pregunta**: son 10 capítulos de entre 1.000 y
  1.500 palabras cada uno. La ficha la registra y el entrevistador informa de
  ella al comprador.
- **RF-04.** Cada rasgo, recuerdo, persona o mascota lleva una marca de
  **imprescindible**, que decide el comprador. Solo los imprescindibles tienen
  que aparecer obligatoriamente en la novela: exigirlo todo obliga a meter datos
  a la fuerza, que es lo que el enunciado penaliza. Esa comprobación sobre los
  capítulos es de otra spec (ver "Fuera").
- **RF-05.** La ficha terminada se convierte en un brief validado con schema. Un
  campo fuera del schema es un error de validación, no un aviso (`CLAUDE.md`).

### La entrevista

- **RF-06.** La entrevista funciona **por turnos**: cada turno recibe la
  respuesta del comprador y devuelve la siguiente pregunta, o la ficha
  terminada. Se usa desde la API y desde una CLI fina que no añade lógica
  propia.
- **RF-07.** El entrevistador **detecta lo que falta**: mientras quede un
  apartado obligatorio vacío, la entrevista no termina y la siguiente pregunta
  es sobre él.
- **RF-08.** Se detectan al menos estas **tres contradicciones**, y las tres son
  **deterministas**, porque comparan categorías y números:
  - **edad frente a género**: por ejemplo, un destinatario menor de 12 años con
    romance;
  - **edad frente a ocasión**: por ejemplo, una boda o una jubilación para un
    menor de 18 años;
  - **recuerdo frente a edad**: un recuerdo situado antes de que el destinatario
    naciera, o a una edad que todavía no ha cumplido.

  Las parejas incompatibles y sus límites de edad son **configuración**, como las
  franjas de `RF-16`; los ejemplos de arriba son el valor inicial.
- **RF-08b.** Cuando género, tono u ocasión quedan en «otro», el código no puede
  compararlos. En ese caso el entrevistador **juzga** si hay contradicción y, si
  la ve, la trata como las de `RF-08`. Ese juicio queda marcado en la ficha como
  juicio del modelo, no como comprobación: no se hace pasar por lo que no es.
- **RF-09.** Ante una contradicción, **la entrevista se bloquea y pregunta**. No
  avisa y sigue: no termina hasta que el comprador la resuelve, cambiando un dato
  o confirmando que es intencionado. La resolución queda anotada en la ficha.
- **RF-10.** Si el nombre de pila de una persona vetada coincide con el de otra
  persona o mascota de la ficha, el entrevistador **avisa** y pide confirmación
  (ver `RF-15`).

### El texto libre

- **RF-11.** El comprador puede pegar texto libre de **hasta 5.000 caracteres**.
  Un texto más largo se rechaza con el motivo; no se trunca en silencio.
- **RF-12.** El texto libre se trata **como dato, nunca como instrucciones**:
  llega al modelo delimitado y declarado como contenido no confiable.
- **RF-13.** De él solo salen **hechos propuestos**: personas, lugares, fechas y
  anécdotas. Un hecho propuesto **no entra en la ficha hasta que el comprador lo
  confirma**. El texto original no pasa a la ficha.
- **RF-14.** Si el texto contiene algo con forma de instrucción al sistema
  («ignora lo anterior», «escribe en su lugar…»), se registra como hallazgo en el
  audit log y **no produce ningún hecho**.

### Las palabras vetadas (`INV-21`)

- **RF-15.** Hay **tres niveles** de listas, guardados en SQLite:
  - **global**: insultos y términos ofensivos, igual para todas las novelas;
  - **por franja de edad**: se aplica según la edad del destinatario;
  - **por novela**: lo que el comprador veta en la entrevista.

  Un nombre propio vetado se veta **en sus dos formas**: completo y nombre de
  pila.
- **RF-16.** Las franjas de edad y sus límites son **configuración**, no código.
  El valor inicial propuesto es infantil (menos de 12 años) y juvenil (de 12 a
  17), y se puede cambiar sin tocar el código.
- **RF-17.** La detección **normaliza antes de comparar**: mayúsculas, acentos,
  plurales y variantes simples (género gramatical). Compara palabras completas,
  no subcadenas: vetar «ana» no veta «ventana».
- **RF-18.** Cada capítulo se comprueba antes de aceptarlo. Si hay coincidencia,
  **vuelve al Escritor** con la lista de coincidencias, **hasta 2 veces**. Si
  tras la segunda reescritura sigue habiendo coincidencias, **la generación se
  detiene y lo informa**. No hay rendición: un capítulo con una palabra vetada
  no se acepta nunca.
- **RF-19.** Las palabras vetadas y `GuiaDeEstilo.tics_prohibidos` **siguen
  separadas**. Los tics son estilo y generan un hallazgo `menor`. Las vetadas son
  política: `INV-21` es `bloqueante`.

### El audit log

- **RF-20.** Cada decisión del policy engine queda en un audit log en SQLite:
  coincidencia de una palabra vetada (con palabra, nivel, capítulo e intento),
  reescritura pedida, parada por agotar los intentos, instrucción detectada en el
  texto libre, contradicción detectada y cómo se resolvió, y borrado de datos
  (`RF-21`).

### Privacidad

- **RF-21.** Cuando la novela **se entrega**, se borran **la conversación de la
  entrevista, el texto libre pegado y la ficha**. **La novela no se borra**, y
  con ella se conservan **la lista de palabras vetadas de la novela** y **los
  hechos de la story bible**, porque sin ellos no se puede regenerar con
  seguridad después de la entrega (`O-2`). El borrado queda en el audit log
  (`RF-20`) con qué se borró y cuándo, nunca con el contenido borrado.
- **RF-22.** Los briefs de prueba y los de evaluación usan **datos inventados**.
  Un brief de evaluación con datos de una persona real es un defecto.

## Cuestiones resueltas

- **O-1. Valores libres o vocabulario controlado → lista cerrada con «otro».**
  Con texto libre, las contradicciones de `RF-08` solo las podría juzgar el
  modelo, es decir, serían un juicio y no una regla. Con una lista hay una
  comprobación determinista, y el entrevistador sigue preguntando con palabras
  naturales. Los valores iniciales de cada lista están en el anexo.
- **O-2. Qué se borra al entregar → la conversación, el texto libre y la ficha,
  pero no lo que la novela necesita.** Las regeneraciones que pide el lector
  (sección 2 del enunciado) ocurren **después** de la entrega y necesitan las
  palabras vetadas de la novela para no reintroducirlas. Si se borraran con el
  brief, una regeneración podría volver a meter el nombre de una expareja sin
  que nada lo detectara.

## Qué queda explícitamente fuera

- **El Planificador y la escritura** a partir de la ficha: la spec del pipeline
  de la novela regalo.
- **Comprobar sobre los capítulos** que los imprescindibles aparecen y que los
  nombres están escritos exactamente como en la story bible: la misma spec.
  Aquí solo se decide qué es imprescindible.
- **Enviar las coincidencias y decisiones a Langfuse**: la spec de
  observabilidad. Aquí quedan en el audit log con lo necesario para enviarlas
  después.
- **La interfaz web de la entrevista**: la spec de lectura web. Aquí están el
  endpoint por turnos y la CLI.
- **El contenido concreto de la lista global.** La spec decide que existe y dónde
  vive; su contenido inicial lo fija el plan.

## Lo que la gobierna

- `CLAUDE.md` § FastAPI: Pydantic como frontera de validación, vocabularios como
  `Enum` y llamadas al modelo asíncronas.
- `A-03`: el entrevistador es un agente, una llamada al modelo con su propio
  contexto.
- `SPEC-14`: el entrevistador se ejecuta por delegación, como el resto de
  agentes.
- `INV-21` (nueva, `bloqueante`, ámbito capítulo): un capítulo aceptado no
  contiene ninguna palabra vetada de ninguno de los tres niveles, tras
  normalizar. Se añade a `docs/definitions.md` al aplicar esta spec.
- `docs/definitions.md` § `Brief`: `tono` y `prohibiciones` ya existen. Esta spec
  los concreta y añade el destinatario; no los sustituye.

## Anexo — Plantilla de la ficha de la entrevista

El entrevistador recorre estos apartados en orden, pregunta con naturalidad y no
da la ficha por terminada hasta que están todos los obligatorios y no queda
ninguna contradicción abierta. **(O)** significa obligatorio e **(I)** que el
comprador puede marcar ese elemento como imprescindible.

**1. El destinatario**
- Nombre, tal como debe aparecer escrito en la novela. **(O)**
- Edad. **(O)**
- Cómo es: rasgos de carácter, aficiones y manías. Al menos uno. **(O)** **(I)**

**2. La ocasión**
- Para qué se regala. **(O)** Lista: cumpleaños, boda, aniversario, jubilación,
  nacimiento, otro.
- Quién la regala y qué relación tiene con el destinatario.

**3. La historia que quiere**
- Género. **(O)** Lista: aventura, romance, comedia, fantasía, misterio, drama
  cotidiano, otro.
- Tono. **(O)** Lista: tierno, divertido, emotivo, épico, nostálgico, otro.
- Papel del destinatario. **(O)** Lista: protagonista, personaje secundario, otro.

En todas las listas, «otro» se anota junto con las palabras literales del
comprador.
- Extensión: no se pregunta; se informa de que son 10 capítulos de 1.000 a 1.500
  palabras.

**4. Los recuerdos**
- Momentos reales que deberían aparecer. Al menos uno. **(O)** **(I)**
- Si el comprador lo sabe, cuándo pasó cada uno (fecha o edad del destinatario).

**4b. La historia en una frase**
- Premisa: de qué va la novela, en una o dos frases. El entrevistador la propone
  a partir de los recuerdos y rasgos, y el comprador la confirma o la cambia. **(O)**
- Título. El entrevistador lo propone y el comprador lo confirma. **(O)**

**5. Personas y mascotas**
- Nombre, relación con el destinatario y un detalle de cada una. **(I)**

**6. Lo que no debe aparecer**
- Palabras, nombres o temas vetados. Un nombre se veta completo y por su nombre
  de pila.

**7. La dedicatoria**
- El texto de la portada. Si el comprador no quiere escribirlo, el entrevistador
  propone uno y el comprador lo confirma.

**8. Texto libre (opcional)**
- Una carta o una anécdota, de hasta 5.000 caracteres. Solo se usan los hechos
  que el comprador confirme.

**Al cerrar:** el entrevistador enseña la ficha completa y el comprador la
confirma. Esa confirmación es lo que convierte la ficha en brief.
