---
id: SPEC-36
titulo: La estantería de madera, el escritor en su mesa y la administración
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: eligió «A · Lomos en baldas», «A · Escritor en su mesa» y «Sí, sin login» sobre docs/proceso/propuestas-visuales/propuestas.html"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: 2e56305
---

# SPEC-36 — La estantería de madera, el escritor en su mesa y la administración

## Qué problema resuelve

En la propuesta visual de `/design` el autor eligió también **la estantería de madera, el
escritor en su mesa y la vista de administración**, y `SPEC-35` las dejó fuera («cada una sería
otra spec»). La web quedó con la estantería como rejilla de tarjetas y la generación sin
escena, que el autor lee como «el diseño anterior». El lienzo de `/design` no está en el
repositorio, así que las propuestas se volvieron a generar
(`docs/proceso/propuestas-visuales/propuestas.html`) y el autor eligió sobre ellas.

## Qué tiene que ser verdad al terminar

- **RF-01 · La estantería son lomos en baldas de madera** (propuesta «Estantería · A»). Cada
  obra es un lomo con su título y su estado en texto, en baldas que se reparten solas. Al pulsar
  un lomo se abre al lado **su ficha**: título, dedicatoria, destinatario, estado y lo que se
  puede hacer (leer, ver cómo se escribe, seguir la entrevista o escribir la novela). Lo ausente
  se dice como ausente, como en `SPEC-33` `RF-01`..`RF-03`. El botón único de `SPEC-33` `RF-04`
  pasa a llamarse **«Encargar una novela»**, como en la propuesta; sigue siendo uno.
- **RF-02 · La generación es el escritor en su mesa** (propuesta «Generación · A»): de noche,
  una lámpara, hojas y pluma dibujadas con CSS, el título de la novela, «Escribiendo el
  capítulo N de M» y los capítulos como una fila de hojas que se llenan. **Debajo sigue todo lo
  de `SPEC-33` `RF-14`..`RF-17` y `SPEC-35` `RF-13`**: cada capítulo con su estado, sus notas del
  Editor, el coste, el motivo de un fallo y el enlace a leer. El título llega del backend; sin
  obra montada todavía, no hay título y se dice.
- **RF-03 · Una vista de administración, sin login** («Sí, sin login»), en `/admin` y enlazada
  desde la cabecera: lo gastado frente al techo, cuántas novelas hay en cada fase y los
  hallazgos abiertos, y una tabla con cada novela, su fase, su coste (con suelo si lo es), sus
  delegaciones, sus hallazgos abiertos por severidad y el último código de Lean. **Todo lo
  resuelve el backend.** Queda declarado que **cualquiera que tenga la URL la ve**: es la
  decisión del autor mientras no haya usuarios.

## Qué queda explícitamente fuera

- Usuarios, login y permisos de la administración (decisión del autor: sin login).
- Acciones desde la administración (relanzar, borrar, entregar): solo lee.
- Cambiar la paleta, que sigue provisional (`SPEC-35` `RF-01`), y el diseño móvil.

## Lo que la gobierna

`SPEC-33` (la estantería, la generación, el gasto), `SPEC-35` (el estilo, `RF-13`),
`CLAUDE.md` (la interfaz muestra estado, no lo calcula; una escena siempre con su estado).
