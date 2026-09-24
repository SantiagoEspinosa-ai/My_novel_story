---
name: verification-plan
description: >
  Produce a verification plan document (verification.md, also called
  validation.md or evaluation.md) for a software system or agentic system,
  from a context seed of project documents. Use when asked to write, review or
  update a verification, validation or evaluation plan; to decide how a claim,
  requirement or invariant will be proven; to classify requirements as
  Test/Analysis/Inspection/Demonstration/Unverifiable (T/A/I/D/U); or to choose
  between verification methodologies such as type checking, static analysis,
  property-based testing, mutation testing, contract testing, evals, tracing,
  red-teaming or model checking. Works for both artifact-level verification
  (is the code correct?) and process-level verification (is the agent behaving
  reliably?).
---

# Plan de verificación

Convierte una **semilla de contexto** —los documentos que describen un
proyecto— en un `verification.md`: una tabla donde cada afirmación verificable
del proyecto tiene asignada una metodología, un criterio de salida y un sitio
donde vive su prueba.

> El catálogo de metodologías procede de la hoja de referencia *Verification
> Methodologies — Reference Sheet*
> (`https://claude.ai/artifact/Rass3RVfaN5KSJDdG2FQhR`). Esa hoja es un
> **inventario**, no un protocolo: no trae plantilla, ni flujo, ni criterios de
> selección. Todo eso lo pone esta skill.

## Cuándo usarla

Cuando alguien pida un `verification.md`, un `validation.md` o un
`evaluation.md`. **Son el mismo documento con tres nombres distintos**; no
preguntes cuál de los tres, pregunta qué se va a verificar. Usa el nombre que
haya pedido quien lo encarga.

## Antes de empezar: dos preguntas que hay que responder

No escribas nada hasta tener estas dos respuestas, porque cambian el documento
entero:

1. **¿Qué se verifica, el sistema o su producto?** En un sistema que genera
   algo —texto, imágenes, código—, verificar *el producto* y verificar *el
   sistema que lo produce* son dos documentos distintos. Un proyecto que ya
   tiene reglas de calidad sobre su producto normalmente necesita el segundo:
   la pregunta no es "¿es buena la salida?" sino "¿hace el código lo que dice
   que hace?".
2. **¿Nivel artefacto, nivel proceso o los dos?** El nivel artefacto pregunta
   si el código es correcto; el nivel proceso pregunta si el agente se comporta
   de forma fiable. Un sistema con agentes necesita los dos, pero en secciones
   separadas: mezclarlos produce una tabla que no se puede leer.

## El proceso, en seis pasos

### 1. Leer la semilla de contexto

Lee los documentos que definen el proyecto: el de restricciones técnicas, el de
dominio, el de arquitectura y el mapa de contexto si lo hay. Léelos enteros; un
plan de verificación construido sobre medio documento verifica media cosa.

### 2. Extraer las afirmaciones verificables

Recorre la semilla y saca **cada frase que afirma que el sistema hace o no hace
algo**. Son las que empiezan por "nunca", "siempre", "no puede", "antes de",
"solo". Esas frases son el material del documento.

Una afirmación entra en la tabla si cumple las tres:

- **Es falsable.** Se puede describir un caso concreto que la viole.
- **Es del sistema, no del gusto.** "El código es legible" no entra; "una
  feature nunca importa de otra" sí.
- **Tiene consecuencias si falla.** Si nadie nota que se rompió, no merece una
  fila.

Numera cada una con un identificador estable (`VER-01`, `VER-02`…) y **anota de
qué fichero y qué sección sale**. Una afirmación sin origen no es verificable:
es una opinión tuya.

Los identificadores publicados no se reutilizan ni se renumeran. Lo que deja de
aplicar se marca como obsoleto, no se borra.

### 3. Clasificar cada afirmación en T/A/I/D/U

Es el marco *Trust Spec*. Cada afirmación se prueba de una de estas cinco
formas, y elegir la correcta es la mitad del trabajo:

| Clase | Significa | Se reconoce porque |
| --- | --- | --- |
| **T** — Test | Se ejecuta el sistema y se compara con lo esperado | Hay una entrada y una salida que se pueden escribir |
| **A** — Analysis | Se demuestra sin ejecutar, por tipos, análisis estático o razonamiento | La afirmación es sobre la *forma* del código, no sobre su comportamiento |
| **I** — Inspection | Alguien mira y confirma | Requiere criterio, no cálculo |
| **D** — Demonstration | Se enseña funcionando en condiciones reales | La prueba es "míralo funcionar", no un assert |
| **U** — Unverifiable | Hoy no se puede probar | Falta un umbral, un dato o una herramienta |

**`U` es una clase legítima y hay que usarla.** Marcar algo como verificado
cuando no lo está es peor que declararlo no verificable. Toda fila `U` lleva
escrito **qué falta exactamente** para dejar de serlo.

### 4. Asignar metodología

Elige del catálogo (`references/metodologias.md`) la metodología más barata que
cierre la afirmación. Tres reglas de selección:

- **Lo determinista no lo verifica un modelo.** Si una afirmación se puede
  comprobar con código —una regla de importación, un contador, un orden, un
  valor de enumeración— se comprueba con código. Pedírselo a un juez LLM es más
  caro, más lento y menos fiable.
- **Sube de nivel solo cuando el de abajo no llega.** Tipos antes que análisis
  estático; análisis estático antes que tests; tests de ejemplo antes que
  property-based; property-based antes que verificación formal.
- **Una afirmación puede tener dos metodologías, pero no cinco.** Si necesitas
  cinco, la afirmación son en realidad varias y hay que partirla.

### 5. Fijar el criterio de salida y dónde vive la prueba

Cada fila necesita responder a **"¿cuándo está verificada?"** con algo que se
pueda comprobar, y a **"¿dónde está la prueba?"** con una ruta.

Nunca escribas un umbral numérico que no se haya medido. Si el criterio
necesita un número y ese número no existe todavía, la fila es `U` y el número
se anota como pendiente. Un umbral inventado que queda escrito ya no se
distingue de uno medido.

### 6. Escribir el documento

Usa `references/plantilla.md`. Respeta el orden de las secciones: quien lee un
plan de verificación busca primero el resumen de cobertura y después la fila
concreta.

## Reglas duras

Estas no son consejos; si el documento las incumple, está mal:

1. **Cada fila cita su origen** por fichero y sección, y su identificador.
2. **Cada fila tiene un criterio de salida** comprobable, no "que funcione".
3. **Ningún número sin medir.** Ni umbrales, ni porcentajes de cobertura, ni
   tiempos. Lo no medido se escribe "sin medir", nunca un cero ni una
   estimación silenciosa.
4. **Toda regla que el proyecto ya tenga numerada se referencia por su
   identificador**, no por su descripción.
5. **Una regla que nunca ha fallado en las pruebas no está verificada, solo
   declarada.** Cada afirmación de clase `T` necesita al menos un caso negativo:
   una entrada que la viole a propósito y que la prueba debe cazar.
6. **El resumen de cobertura cuenta filas, no promete calidad.** Di cuántas
   afirmaciones hay en cada clase y cuántas están cubiertas hoy; no digas que el
   sistema es fiable.

## Anti-patrones de un plan de verificación

| Anti-patrón | Síntoma | Qué hacer |
| --- | --- | --- |
| Plan de deseos | Filas que describen lo que se querría verificar algún día | Márcalas `U` con lo que falta, o bórralas |
| Juez para todo | Un modelo evaluando cosas que una regla decide | Baja al nivel determinista |
| Umbral inventado | Un número redondo sin medición detrás | `U` y número pendiente |
| Cobertura como nota | "Cobertura del 85%, luego está bien" | La cobertura mide qué se ejecutó, no qué se comprobó |
| Fila sin dueño | Nadie sabe dónde vive la prueba | Ruta concreta o `U` |
| Verificar el producto creyendo verificar el sistema | El plan evalúa la calidad de la salida y no toca el código | Vuelve a la pregunta 1 |

## Ficheros de referencia

Cárgalos solo cuando los necesites:

- `references/metodologias.md` — el catálogo completo: 8 metodologías de nivel
  artefacto, 11 de nivel proceso, con definición y enlace a la explicación.
- `references/plantilla.md` — la plantilla del documento de salida.
