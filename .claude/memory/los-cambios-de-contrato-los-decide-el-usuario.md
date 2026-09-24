---
name: los-cambios-de-contrato-los-decide-el-usuario
description: "En My_novel_story, cualquier cambio del comportamiento contractual del harness lo decide el usuario, aunque parezca una mejora obvia; hay que proponerlo, no implementarlo."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2fbfe393-2b72-4929-8585-aee17e40f162
  modified: 2026-09-17T22:11:38.446Z
---

# Los cambios de contrato los decide el usuario

Al encargar el registro de tokens y la telemetría de Langfuse, el usuario cerró
el encargo con una frase que va más allá de esa tarea concreta: *"No implementes
la parada anticipada por puntuación. Es un cambio de contrato y lo decido yo."*

La distinción que hace es entre dos clases de trabajo que desde dentro del
código se parecen mucho:

- **Instrumentar, medir, documentar o arreglar un contador que miente** son
  cosas que se pueden hacer sin preguntar: no cambian lo que el harness decide,
  solo lo que se sabe de lo que decidió.
- **Cambiar cuándo el harness para, aprueba, reintenta o descarta** es un cambio
  de contrato. Aunque sea una mejora evidente y aunque ahorre delegaciones, se
  propone y se espera; no se implementa por iniciativa propia.

Esto es más estricto que la regla que ya está en el `CLAUDE.md` del proyecto
(que pide avisar antes de tocar algo que contradiga `EJECUCION.md`). Aquí el
usuario está diciendo que ni siquiera un cambio que *mejoraría* el documento se
hace sin su visto bueno: la política de calidad de la novela es suya, no una
decisión de ingeniería.

En la práctica, la forma correcta de responder a una idea de ese tipo es
terminar lo encargado, y mencionar la propuesta en una o dos frases al final,
sin código escrito por adelantado.
