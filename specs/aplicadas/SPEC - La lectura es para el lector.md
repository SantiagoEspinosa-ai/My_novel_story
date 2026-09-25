---
id: SPEC-43
titulo: La lectura es para el lector; el estado y los hallazgos de cada escena, en la administración
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: «La página de un capítulo es para el lector. Quítale todo lo técnico […] no lo quites del sistema: muévelo a /admin […] La lectura es para el lector y la administración para ti. Deja esa distinción escrita. Aplícalo a todos los capítulos»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: 52a242a
---

# SPEC-43 — La lectura es para el lector

## Qué problema resuelve

`CLAUDE.md` pide que una escena se muestre «siempre con su estado (`planificada`…`consolidada`) y con los hallazgos abiertos que tenga», y la lectura web lo cumplía en cada página. El lector de una novela regalo veía por eso cosas que no le importan:
- «consolidada»;
- «INV-25 menor abierto»;
- el identificador `obra-…-cap-02-e1` como título de la página de una escena.

Y al acabar un capítulo no tenía cómo pasar al siguiente.

La regla de `CLAUDE.md` existe para que quien revisa el sistema no dé por bueno un texto sin su contexto. Quien revisa es el que administra, no el lector.

## Qué tiene que ser verdad al terminar

- **RF-01 · Lo que ve el lector no enseña nada técnico.** Las páginas de lectura son el índice, el capítulo y la escena. En ninguna aparece:
  - el estado de una escena o de un capítulo;
  - un hallazgo ni un identificador `INV-xx`;
  - un identificador interno.

  Siguen las marcas que son del lector: «cambió por tu cambio» y «compartido» (`SPEC-35` `RF-10`).
- **RF-02 · El título es el del libro.** Es «Capítulo N» y, si el capítulo tiene título en el plan, «Capítulo N · su título». Es igual en el capítulo, en la escena y en el índice.
- **RF-03 · Al final de cada capítulo, navegación:** anterior (si lo hay), siguiente (si lo hay) y volver al índice, en el orden de lectura de la versión que se lee.
- **RF-04 · El estado y los hallazgos siguen en el sistema, en la administración.** La página de cada novela en `/admin` enseña cada escena con su estado y sus hallazgos abiertos. La API de lectura los sigue devolviendo, porque de ella leen la administración y las pruebas (`VER-18`).
- **RF-05 · La distinción queda escrita en `CLAUDE.md`:** la lectura es para el lector y la administración para quien revisa. La regla del estado y los hallazgos pasa a ser de la administración.

## Qué queda explícitamente fuera

- Quitar el estado o los hallazgos de la API.
- Cambiar el PDF.
- Títulos de capítulo en las versiones nacidas de un cambio que no estén en el plan: esos capítulos se titulan «Capítulo N».

## Lo que la gobierna

`CLAUDE.md` § React, `SPEC-22` `RF-39`…`RF-41` (lectura), `SPEC-35` `RF-10` (marca de cambio), `SPEC-38` (la página de cada novela en la administración), `VER-18`.
