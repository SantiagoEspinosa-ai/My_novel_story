# `harness/invariantes/` — vacío a propósito

Aquí va **un archivo por validador de dominio**: las comprobaciones de
`INV-01`…`INV-16` sobre escenas, deltas y estado del mundo.

Está vacío porque **todas dependen de código que aún no existe**. `INV-01`
necesita una `Escena` con su `cambio_de_valor`; `INV-05` necesita el
consolidador; `INV-02` necesita `EstadoDelMundo`. Sin `backend/` no hay nada
que comprobar, y escribir un test contra un doble que nos inventamos nosotros
comprobaría nuestra imaginación, no el sistema.

La diferencia con `harness/documentos/` es deliberada y conviene mantenerla:

| Carpeta | Qué valida | Se puede ejecutar hoy |
| --- | --- | --- |
| `documentos/` | Que los documentos de `Docs/` son coherentes entre sí | **Sí** |
| `invariantes/` | Que el código cumple las invariantes del dominio | No, hasta que haya `backend/` |

Cuando llegue la primera invariante, su caso negativo se escribe **antes** que la
comprobación: es TDD y además es la única forma de saber que la comprobación hace
algo. Los casos rotos a propósito van en `harness/fixtures/`.
