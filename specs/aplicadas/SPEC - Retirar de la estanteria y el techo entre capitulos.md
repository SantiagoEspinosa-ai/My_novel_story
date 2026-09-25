---
id: SPEC-41
titulo: Retirar una novela de la estantería con su motivo, y el techo entre capítulos
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: «Si alguno no se puede terminar, bórralo de la estantería en vez de dejarlo ahí a medias — pero déjalo visible en /admin con su motivo» y «Sigue con el tope de 50 USD»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: f8b7477
---

# SPEC-41 — Retirar de la estantería, y el techo entre capítulos

## Qué problema resuelve

El autor pidió terminar todas las novelas de la estantería y quitar de ella las que no se
puedan terminar, sin perderlas de vista en la administración. Y pidió respetar el techo de
50 USD, que hoy la web solo mira **al lanzar**: una generación que empieza por debajo del
techo lo puede cruzar a mitad sin que nada la pare.

## Qué tiene que ser verdad al terminar

- **RF-01 · Una novela se puede retirar de la estantería con su motivo.** Queda guardado quién
  la retiró (el sistema o una persona), cuándo y por qué. No se borra nada de la novela: deja de
  salir en la estantería y **sigue en la administración, con su motivo a la vista**.
- **RF-02 · Retirar se deshace**: una novela retirada se puede volver a poner en la estantería.
- **RF-03 · El techo también entre capítulos** (`SPEC-33` `RF-13`): una generación lanzada desde
  la web comprueba lo gastado en la base al terminar cada capítulo, y si alcanza el techo se para
  **entre capítulos**, nunca a media delegación, con el motivo `techo_de_gasto`. Se puede
  reanudar cuando haya margen.

## Qué queda explícitamente fuera

- Borrar de verdad una novela de la base.
- Retirar desde la web con un botón: hoy lo hace quien administra por la API.

## Lo que la gobierna

`SPEC-33` `RF-01`, `RF-13`; `SPEC-36` `RF-03`; `SPEC-39` (reanudar).
