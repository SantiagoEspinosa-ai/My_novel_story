---
name: un-validador-comprueba-su-propio-lado
description: "En My_novel_story, un validador comprueba el lado en el que vive, y el contrato entre dos lados se congela en un fichero del repositorio y se compara contra lo que el código genera hoy."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:01:23.346Z
---

# Un validador comprueba su propio lado, y el contrato se congela

Al encargar la spec del frontend, el usuario fijó dos reglas que valen más allá de esa
tarea y que conviene no volver a hacerle repetir.

## El validador comprueba el lado en el que vive

Dicho por él: *"los validadores del frontend comprueban el frontend, no el backend. Si una
prueba de front falla porque el backend está mal, estamos duplicando su suite"*. Lo apoyó
en algo ya decidido en el proyecto, `D3-5` de `Docs/revisiones/REV-01`, que obligó a partir
en dos las filas `VER` que trazaban un requisito de backend a una prueba de frontend, y en
la frontera de `Docs/architecture.md`: **el backend devuelve, la interfaz muestra**.

En la práctica: una prueba de interfaz no arranca un backend, se valida contra el contrato
y contra datos derivados de él. Una comprobación que cruza los dos lados no pertenece a
ninguno de los dos: vive en el harness. Y si para pintar algo la interfaz tuviera que
calcularlo, falta un campo en la respuesta y el arreglo es del backend, no de la interfaz.

## Un contrato entre dos piezas se congela y se compara

Para la frontera con FastAPI pidió congelar el esquema OpenAPI en un fichero del
repositorio, validar el frontend contra ese fichero —nunca contra un backend corriendo— y
tener un validador que compare el congelado con el que el código genera hoy: **si el
backend cambia y el contrato no, tiene que fallar**. El motivo que dio es el del proyecto
entero: si no, el front se rompe **en silencio**, que es la Regla 5 de
`Docs/verification.md` —una forma fijada sin significado, las dos partes cumpliendo el
contrato y el sistema roto sin que nada falle— aplicada a esa frontera.

Generaliza: cuando dos piezas del proyecto se hablan a través de algo que hoy solo vive en
prosa (una tabla de markdown, un prompt, una respuesta acordada), la protección es un
artefacto derivado del código, versionado, y una comprobación que falle cuando el código y
el artefacto divergen.

## Y una tercera cosa, sobre el encargo

Junto con la spec pidió la lista de lo que le falta al backend para soportarla, y dijo que
esa lista **vale tanto como la spec**. Al escribir una spec que depende de algo que no
existe, enumerar las dependencias reales —comprobadas contra el código, no contra los
documentos— es parte del entregable, no un apéndice.
