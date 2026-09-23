---
id: SPEC-19
titulo: Los beats declaran qué hechos establecen, y algo cruza lo prometido con lo entregado
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 9db3321
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-19 — Lo prometido y lo entregado

## Qué problema resuelve

`F-37`, medido en una generación real. La escaleta de `e2` decía:

> *"Marta encuentra el sótano cerrado y no aparece la llave."*

El texto se escribió, **pasó todas las puertas** y se consolidó. Y `hec-sotano-cerrado` y
`hec-llave-perdida` siguen **sin establecer**: el delta no declaró ninguna revelación. Dos
escenas después, `INV-03` bloqueó a Marta por actuar sobre el sótano cerrado — que era
exactamente lo que `e2` prometía haberle enseñado.

**La invariante cazó la consecuencia, no la causa, y con dos escenas de retardo.** Lo que
falló fue que el delta de `e2` no declaró lo que su propio texto estaba haciendo, y eso no
lo mira nadie.

### Por qué nadie lo mira

> **El plan promete en prosa y el delta entrega identificadores.**

Los `beats` de una escena son texto libre. El delta son referencias (`SPEC-03`). Las dos
descripciones de la misma escena están escritas en lenguajes que no se pueden comparar, así
que no hay comprobación posible: no es que falte un validador, es que **faltaba el dato**.

Es el mismo movimiento que `SPEC-03` hizo con las revelaciones y `SPEC-15` con los hechos:
lo que hay que comprobar deja de ser prosa. Y es el hueco que `SPEC-15` C-3 hizo
**nombrable** —*"un hecho declarado y nunca establecido"*— sin darle todavía con qué
detectarlo en el momento.

---

## C-1 · Un `Beat` puede declarar qué hechos establece

`Beat` gana `establece[]` → `HechoCanonico`, opcional.

**Opcional y no obligatorio**, porque no todo beat establece un hecho: muchos mueven tensión,
posición o relación sin añadir nada al canon. Exigirlo llenaría la escaleta de listas vacías
y enseñaría a rellenarlas por inercia, que es la forma más rápida de que un campo deje de
significar nada.

Los identificadores tienen que existir en `Escaleta.hechos_canonicos[]` (`SPEC-15`): un beat
no inventa hechos, los sitúa.

## C-2 · Una comprobación cruza lo prometido con lo entregado

Al cerrar una escena, lo que sus beats prometían establecer se compara con lo que su delta
declaró. **Es una diferencia de conjuntos**, barata y determinista, y por eso es una regla y
no un juez (`comprobaciones deterministas no las hace un modelo`).

Dos diferencias, y **no son el mismo defecto**:

| Caso | Qué significa |
| --- | --- |
| Prometido y no entregado | El plan dijo que esta escena establecería el hecho y el delta no lo declara. **El texto puede haberlo hecho igual**: lo que consta mal es el delta |
| Entregado y no prometido | El texto estableció algo que el plan no previó. `SPEC-15` P-4 ya decidió que **se permite y se marca** |

La primera es la que produce hallazgo. La segunda ya está resuelta y no se toca.

## C-3 · Su punto ciego, declarado

**No comprueba que el texto haga lo que el delta dice.** Compara dos declaraciones —el plan y
el delta— y las dos las escribe alguien que podría estar equivocado sobre el texto. Un
modelo que declare la revelación sin escribirla pasa esta comprobación limpiamente.

Eso lo cubre `INV-11`, que es de tipo juez, y **es un punto ciego distinto** del que ya
tienen los demás, que es lo que la Regla 2 exige para admitir una comprobación nueva.

## C-4 · Se comprueba en la escena, no al cerrar el capítulo

El retardo es el defecto, no el hallazgo. Detectarlo al cierre de capítulo lo encontraría
igual y **seguiría permitiendo que cuatro escenas se generaran encima de un canon
incompleto**, que es exactamente lo que pasó.

## Qué queda explícitamente fuera

- **La severidad del hallazgo nuevo.** Ver las preguntas.
- **Que el Escaletador rellene `establece[]` solo.** Aquí se decide que el campo existe y que
  algo lo cruza; quién lo escribe es del plan de implementación.
- **Comparar el texto con el delta.** `C-3`: es `INV-11` y es un juez.
- **Los `beats` dejan de ser prosa.** No. Siguen siendo prosa **y además** pueden llevar
  referencias. Quitarles la prosa perdería lo único que el escritor lee.

### Migración

`beat` no tiene tabla propia hoy —`Escena.beats` se guarda como JSON—, así que esto no
altera ninguna columna. Si el día que la tenga `establece[]` pasara a obligatorio, ese
cambio sí llevaría la suya.

## Qué gobierna esto

`Beat`, `HechoCanonico`, `Escaleta.hechos_canonicos[]` e `INV-11` de `Docs/definitions.md`;
`SPEC-03`, `SPEC-15` C-3 y `SPEC-15` P-4; `F-37` de `Docs/verification.md`; la Regla 2, que
es la que obliga a declarar el punto ciego de `C-3`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿La comprobación es una invariante nueva o una ampliación de una existente? | **Invariante nueva.** Ninguna de las diecisiete dice nada sobre el plan: todas miran el texto, el delta o el estado. Ampliar una haría que su historial dejara de significar lo mismo |
| 2 | ¿Qué severidad? | **`mayor`.** No corrompe el canon —lo que falta es una declaración, no una falsedad— así que no debe detener la escena; pero **tiene que impedir cerrar el capítulo**, porque es el hueco por el que `INV-03` acaba bloqueando dos escenas después |
| 3 | ¿Qué pasa con un hecho prometido en un beat de `e2` que el delta de `e4` sí declara? | **Se resuelve y deja de contar.** La promesa era *que se establezca*, no *dónde*. Lo contrario convertiría un reordenamiento narrativo legítimo en un defecto permanente |
| 4 | ¿Un beat puede prometer un hecho que ninguna otra escena establece nunca? | Sí durante la obra, **no al firmarla**. Es el defecto que `SPEC-15` C-3 nombró y esta spec le da por fin con qué detectarlo |
| 5 | ¿`establece[]` va en el prompt del Escritor? | **Sí, y es media spec.** Si no le decimos qué hechos tiene que establecer esta escena, exigirle que los declare es pedirle lo imposible (Regla 4), y la comprobación nueva sería merecida e inútil |

Las cinco se respondieron el 2026-09-23. La **5 se resolvió en la dirección de la Regla 4 y
no es un detalle de implementación**: es la tercera vez que el proyecto tropieza con lo
mismo —`F-21` con los identificadores, `F-34` con el POV, y ahora los hechos a establecer—.
El patrón ya no admite duda: **cada vez que se añade algo que el contrato exige, hay que
preguntarse si el prompt lo pide**, porque exigir sin pedir produce un rechazo merecido e
inútil, y el sistema se para por una causa que nadie nombró.
