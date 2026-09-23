---
id: SPEC-25
titulo: El destinatario, la entrevista y las palabras vetadas
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-23
version: 1
---

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

Faltan cuatro cosas, y ninguna existe en `Docs/definitions.md`:

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

**Los valores los aporta el comprador, no un catálogo.** Género, tono, ocasión y
papel del destinatario se preguntan y se anotan con las palabras que el
comprador elija. Ver la cuestión abierta `O-1`.

## Qué tiene que ser verdad al terminar

### La ficha y el destinatario

- **RF-01.** Existe la ficha de la entrevista con los apartados del anexo, y
  cada apartado declara si es obligatorio.
- **RF-02.** Son obligatorios: nombre del destinatario, edad, ocasión, género,
  tono, papel del destinatario en la historia, al menos un rasgo y al menos un
  recuerdo. Una ficha sin alguno de ellos **no es un brief válido** y no arranca
  la generación.
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
- **RF-08.** El entrevistador detecta al menos estas **tres contradicciones**:
  - **edad frente a género o tono**: por ejemplo, un destinatario menor de 12
    años con romance o terror;
  - **ocasión frente a tono**: por ejemplo, un nacimiento con un tono sombrío;
  - **recuerdo frente a edad**: un recuerdo situado antes de que el destinatario
    naciera, o a una edad que no ha cumplido.
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

- **RF-21.** Cuando la novela **se entrega**, los datos de la entrevista se
  borran. **La novela no se borra.** Qué entra exactamente en «los datos de la
  entrevista» depende de `O-2`.
- **RF-22.** Los briefs de prueba y los de evaluación usan **datos inventados**.
  Un brief de evaluación con datos de una persona real es un defecto.

## Cuestiones abiertas antes de aprobar

- **O-1. Valores libres o vocabulario controlado.** `CLAUDE.md` exige que los
  vocabularios controlados sean `Enum`. Si género, tono y ocasión son texto
  libre, las contradicciones de `RF-08` solo las puede juzgar el modelo, es
  decir, son un juicio y no una regla. Si son una lista con una opción «otro»,
  hay una comprobación determinista y el entrevistador sigue preguntando con
  palabras naturales.
- **O-2. Qué se borra al entregar.** Las regeneraciones que pide el lector
  (sección 2 del enunciado) ocurren **después** de la entrega y necesitan las
  palabras vetadas de la novela para no reintroducirlas. Si se borran con el
  brief, una regeneración puede volver a meter el nombre de la expareja sin que
  nada lo detecte.

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
  normalizar. Se añade a `Docs/definitions.md` al aplicar esta spec.
- `Docs/definitions.md` § `Brief`: `tono` y `prohibiciones` ya existen. Esta spec
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
- Para qué se regala: cumpleaños, boda, aniversario, jubilación, nacimiento… **(O)**
- Quién la regala y qué relación tiene con el destinatario.

**3. La historia que quiere**
- Género: aventura, romance, misterio, fantasía… **(O)**
- Tono: tierno, divertido, emotivo, épico… **(O)**
- Papel del destinatario: protagonista, personaje secundario u otro. **(O)**
- Extensión: no se pregunta; se informa de que son 10 capítulos de 1.000 a 1.500
  palabras.

**4. Los recuerdos**
- Momentos reales que deberían aparecer. Al menos uno. **(O)** **(I)**
- Si el comprador lo sabe, cuándo pasó cada uno (fecha o edad del destinatario).

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
