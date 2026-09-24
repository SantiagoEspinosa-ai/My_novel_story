---
name: un-hallazgo-se-escribe-donde-vive-la-regla
description: "En My_novel_story, un hallazgo hay que escribirlo donde vive la regla que afecta, no solo en el artefacto donde se descubrió, y lo que cae fuera del encargo se registra como hallazgo numerado."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 02b8c887-4903-4ad6-a29f-28e552cdb4de
  modified: 2026-09-23T16:19:07.405Z
---

# Un hallazgo se escribe donde vive la regla, no solo donde se encontró

Al entregar una especificación TLA+ con su README, dejé en ese README varios
hallazgos que el análisis formal había destapado. El usuario lo corrigió: uno de
ellos —que dos reglas distintas permitían publicar algo sin verificar, escritas
en sitios separados y sin referenciarse— **«merece quedar escrito donde viven
esas dos reglas, no solo en tu README»**. Y otro, sobre una propiedad de la
reanudación que yo había encontrado en un docstring del código, tenía que
escribirse **en la máquina de estados**, que es donde alguien lo va a buscar.

La regla general que se deduce, y que este proyecto ya aplica a otras cosas:

- **El artefacto donde se descubre algo no es su sitio definitivo.** Un README de
  verificación, una revisión o una especificación formal son donde el hallazgo
  *aparece*; su sitio es el documento normativo que gobierna la regla afectada
  (`Docs/architecture.md`, `Docs/definitions.md`). Dejarlo solo en el artefacto
  lo condena a no ser leído por quien reimplemente esa parte.
- **Un riesgo que cruza dos reglas se escribe en las dos, y cada una referencia
  a la otra.** El peligro de ese tipo de defecto es justamente que cada regla
  por separado parece razonable; si no se citan mutuamente, nadie las vuelve a
  ver juntas.
- **Lo que está solo en un docstring está escondido.** Si una propiedad explica
  por qué un mecanismo es correcto, va en el documento de la máquina de estados
  o del diseño, no únicamente en el código que la implementa.

## Lo que cae fuera del encargo se registra, no se arregla ni se calla

Cuando el trabajo destapa algo que pertenece a otra pieza o a otra sesión, el
usuario pide **anotarlo como hallazgo numerado** —la serie `F-NN` de
`Docs/verification.md`— con una referencia cruzada al identificador con el que
la otra sesión lo está siguiendo (en ese caso, `G-07` de la spec de frontend).
Así lo recoge quien corresponda en vez de quedarse en la cabeza de una sesión
que termina. No se arregla por iniciativa propia y tampoco se deja solo
mencionado en prosa dentro del entregable.
