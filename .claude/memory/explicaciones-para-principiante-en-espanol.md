---
name: explicaciones-para-principiante-en-espanol
description: El usuario es principiante y pide que se le explique en español qué hace cada archivo creado.
metadata: 
  node_type: memory
  pinned: true
  originSessionId: 42f078b1-eced-4fc3-96d7-83ec5aaa7645
  modified: 2026-09-17T16:11:41.473Z
---

# Explicaciones en español y a nivel de principiante

El usuario de este proyecto (`My_novel_story`, harness generador de novelas) se
describe a sí mismo como principiante en programación y pidió explícitamente que,
además de escribir el código, se le explique **en español y para cada archivo
creado** qué hace ese archivo y por qué existe.

Esto cambia dos cosas en la forma de trabajar:

- La respuesta final de cada sesión debe incluir un recorrido archivo por archivo,
  en español, con lenguaje llano: qué contiene, para qué sirve y cómo encaja con
  el resto. No basta con listar los archivos creados.
- Conviene que los comentarios y docstrings del propio código también estén en
  español y expliquen el porqué, no solo el qué, porque el usuario los va a leer
  para aprender.

Además, el usuario trabaja por etapas deliberadamente pequeñas (el
`CLAUDE.md` del proyecto exige una etapa del orden de implementación por sesión,
ejecutando antes de pasar a la siguiente), lo cual encaja con esta necesidad de
entender cada pieza antes de añadir la siguiente. No conviene adelantarse a
implementar etapas posteriores aunque parezcan triviales.
