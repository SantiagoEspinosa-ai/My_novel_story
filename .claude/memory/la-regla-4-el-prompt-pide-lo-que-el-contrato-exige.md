---
name: la-regla-4-el-prompt-pide-lo-que-el-contrato-exige
description: "En My_novel_story, cada vez que se añade algo que el contrato exige al modelo hay que comprobar que el prompt lo pida, porque exigir sin pedir produce un rechazo merecido e inútil."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-23T16:17:54.476Z
---

# Si el contrato lo exige, el prompt tiene que pedirlo

En `My_novel_story` el proyecto ha tropezado **tres veces** con el mismo error, y
el usuario lo señaló como patrón la tercera vez, al resolver la pregunta 5 de
`SPEC-19`:

- `F-21` — el contrato exigía identificadores en el delta y el prompt no decía
  cuáles existían. El modelo devolvió prosa y el rechazo fue merecido e inútil.
- `F-34` — `Borrador.pov_usado` era obligatorio en el dominio y el prompt no
  decía qué punto de vista se había planificado. El modelo eligió, y eligió mal:
  escribió la escena sobre otro personaje.
- `SPEC-19` — `INV-18` iba a comprobar que el delta declarase los hechos que el
  plan prometía, y el prompt no le decía al Escritor cuáles eran.

La regla que se deriva, y que el proyecto tiene escrita como **Regla 4** en
`Docs/verification.md`:

> **Un prompt bien construido no garantiza una respuesta bien formada, y un
> contrato bien escrito no sirve de nada si el prompt no pide lo que exige.**
> Las dos mitades o ninguna.

## Qué hacer en la práctica

Cada vez que se añade un campo obligatorio a la respuesta de un agente, o una
comprobación nueva sobre lo que ese agente devuelve, hay que preguntarse
explícitamente **si el prompt lo pide**. Si no lo pide, la comprobación no
detecta un defecto del modelo: detecta que se le pidió lo imposible, y el
sistema se para por una causa que nadie nombró.

El síntoma es siempre el mismo y es difícil de leer desde el hallazgo: una
invariante que bloquea con una descripción que suena razonable, cuando la causa
real está en lo que no se le dijo al modelo.
