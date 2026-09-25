---
id: SPEC-38
titulo: La página de cada novela como matriz por capítulo, con la línea de tiempo en una pestaña
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: «Quiero cambiar la página de cada novela a la matriz por capítulo, como la propuesta B» con su descripción"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
---

# SPEC-38 — La matriz por capítulo

## Qué problema resuelve

`SPEC-37` puso la historia de cada novela como línea de tiempo. El autor quiere que la página
se abra con **la matriz por capítulo** (la propuesta B de
`docs/proceso/propuestas-visuales/administracion.html`), que compara capítulos y criterios de un
vistazo, y que la línea de tiempo siga, como segunda pestaña.

## Qué tiene que ser verdad al terminar

- **RF-01 · Arriba**, el título y cuatro cifras en tarjetas: el coste de la novela, sus
  delegaciones, lo gastado en la base frente al techo de la web, y los hallazgos abiertos.
- **RF-02 · La tabla**, para la versión elegida (por defecto la vigente, con un selector de
  versión): una fila por capítulo con las **seis notas del Editor en celdas de color**, el
  coste, los intentos, los hallazgos abiertos por severidad y si **cambió** en esa versión. Una
  fila marcada si el capítulo tuvo una parada. **Al final, medias y totales.** El coste de un
  capítulo compartido es el de la versión que lo escribió.
- **RF-03 · Debajo**, las paradas y las rondas de la puerta con Lean de esa versión.
- **RF-04 · Una leyenda** de qué significa cada color, y el color nunca solo: la nota va escrita.
- **RF-05 · Se conserva**: el coste por agente y los hallazgos con su invariante y severidad, en
  un panel al lado; y el aviso de que **el coste por capítulo es una atribución y no una
  medida** (`SPEC-37` `RF-04`).
- **RF-06 · La línea de tiempo de `SPEC-37`** sigue entera, como **segunda pestaña**, con su
  propia dirección para poder enlazarla.
- **RF-07 · Todo lo resuelve el backend**, las medias y los totales incluidos; los colores de
  las notas son tokens del tema (`SPEC-22` `RF-59`).

## Qué queda explícitamente fuera

- Medir el coste por capítulo en vez de atribuirlo (sigue fuera, como en `SPEC-37`).
- Login y acciones (`SPEC-36`).

## Lo que la gobierna

`SPEC-37`, `SPEC-36` `RF-03`, `SPEC-33` `RF-12` (el techo), `CLAUDE.md`.
