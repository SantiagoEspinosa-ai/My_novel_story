---
id: SPEC-39
titulo: Publicar y reanudar una novela desde la web
estado: aprobada
aprobada_por: "autor del proyecto, en sesión: «Añade un botón de Publicar […] Añade un botón de Reanudar […]»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# SPEC-39 — Publicar y reanudar desde la web

## Qué problema resuelve

Una novela con todos sus capítulos escritos que no se publicó (sin Lean en la máquina, o una
ronda que no pasó) se queda «esperando revisión» y la web no ofrece nada. Una novela que se
paró a medias solo se puede reanudar por la terminal, aunque el checkpoint del backend ya salta
lo consolidado. Y si el servidor se reinicia a mitad de una generación, su trabajo se queda «en
curso» para siempre y bloquea volver a lanzarla (`F-208`).

## Qué tiene que ser verdad al terminar

- **RF-01 · «Publicar»** se ofrece solo a una novela con **todos los capítulos de la versión que
  se escribe terminados** (consolidados o rendidos), sin publicar, con su ficha y sin nada en
  curso. Pasa por **una ronda de la puerta de publicación** (`SPEC-30`), Lean incluido, **sin
  reescribir nada**. Si publica, la novela queda publicada. Si no, dice **qué condición falló**
  —invariante, capítulo y detalle— y qué dijo Lean.
- **RF-02 · Antes de publicar se avisa del gasto**: la ronda juzga la obra entera (`INV-27`), que
  es una delegación del Editor. Se enseña lo que ha costado de media el Editor en esta base, o
  que no está medido.
- **RF-03 · Sin Lean, se dice claro y no se gasta.** Si `lake` no está en la máquina, «Publicar»
  no se ofrece como botón: se dice que falta Lean, para qué hace falta y dónde se busca. El
  backend se niega igual (`409`) antes de llamar a nadie.
- **RF-04 · «Reanudar»** se ofrece a una novela **parada a medias**, con su ficha, sin nada en
  curso y con lo gastado por debajo del techo (`SPEC-33` `RF-13`). Relanza la misma generación,
  que reanuda desde el checkpoint (`EXAMEN.md` §4).
- **RF-05 · Antes de reanudar se avisa**, como con «Generar»: **desde qué capítulo sigue** y
  cuántos faltan, una **estimación** de lo que costará (el coste medio por capítulo medido en
  esa novela, o la referencia de la novela de ejemplo, diciendo cuál) y lo gastado frente al
  techo. Nada se lanza sin esa confirmación.
- **RF-06 · Una generación huérfana no bloquea** (`F-208`): al arrancar la API, lo que estaba en
  curso de un proceso anterior pasa a abandonado, y la obra a parada con ese motivo.
- **RF-07 · Todo lo decide el backend**: si se puede, por qué no, desde dónde y cuánto.

## Qué queda explícitamente fuera

- Reescribir capítulos desde «Publicar» (el bucle de `SPEC-30` `RF-07`): una ronda y se informa.
- Instalar Lean desde la web.

## Lo que la gobierna

`SPEC-30` (la puerta), `SPEC-33` `RF-11`..`RF-13` (lanzar y el techo), `SPEC-36`/`SPEC-38` (la
administración), `EXAMEN.md` §4 (checkpoint por capítulo) y §5c (Lean automático).
