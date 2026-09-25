---
id: SPEC-42
titulo: La administración enseña las novelas de la estantería, las mismas y en el mismo orden
estado: aprobada
aprobada_por: "autor del proyecto, en sesión: «La administración solo enseña las novelas de la estantería, las mismas y en el mismo orden. Ni las retiradas ni las que no están ahí.»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# SPEC-42 — La administración enseña la estantería

## Qué problema resuelve

`SPEC-41` `RF-01` dejaba las novelas retiradas en la administración, con su motivo. El autor
decide ahora que la administración enseñe exactamente lo que enseña la estantería. Una lista
distinta en cada pantalla obliga a comparar dos listas para saber qué ve el lector.

## Qué tiene que ser verdad al terminar

- **RF-01 · La administración enseña las mismas novelas que la estantería, en el mismo orden.**
  Una novela retirada no sale, ni ninguna que no esté en la estantería.
- **RF-02 · Retirar no borra nada.** La retirada y su motivo siguen guardados (`SPEC-41` `RF-01`,
  `RF-02`) y se leen en la base. Devolver una novela a la estantería la devuelve también a la
  administración.
- **RF-03 · Los totales de gasto no cambian.** Lo gastado sigue siendo el de toda la base,
  incluidas las retiradas, porque se pagó (`SPEC-33` `RF-12`).

Sustituye la parte de `SPEC-41` `RF-01` que decía «sigue en la administración, con su motivo a
la vista». El resto de `SPEC-41` sigue vigente.

## Qué queda explícitamente fuera

- Una pantalla propia para las retiradas.
- Borrar de verdad una novela.

## Lo que la gobierna

`SPEC-36` `RF-03` (la administración), `SPEC-41` (retirar), `SPEC-33` `RF-12` (el gasto).
