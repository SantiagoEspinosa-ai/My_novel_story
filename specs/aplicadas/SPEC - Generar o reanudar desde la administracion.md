---
id: SPEC-44
titulo: Generar o reanudar una novela desde la administración
estado: aplicada
aprobada_por: "autor del proyecto, en sesión: «Hay otras novelas sin generar, genera un boton para poder reanudarlas o generarlas»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: 86adacc
---

# SPEC-44 — Generar o reanudar desde la administración

## Qué problema resuelve

Hoy solo hay dos formas de lanzar o reanudar una novela desde la web, y las dos están escondidas:
- **Lanzar una novela que nunca se generó:** solo desde la estantería, pasando por la entrevista.
- **Reanudar una parada:** solo en la página de esa novela en la administración (`SPEC-39`).

La tabla de la administración no ofrece nada, y una novela sin generar ni siquiera tiene acciones: la API responde que no existe, porque la obra no se monta hasta que hay plan.

## Qué tiene que ser verdad al terminar

- **RF-01 · Generar es una acción más, junto a publicar y reanudar** (`SPEC-39` `RF-07`). El backend decide si se puede y por qué no. Se puede generar cuando se cumplen las cuatro condiciones:
  - la entrevista está cerrada;
  - la novela no se ha lanzado nunca;
  - no hay nada suyo en curso;
  - lo gastado en la base no alcanza el techo.
- **RF-02 · Una novela que solo tiene entrevista tiene acciones.** No es un 404.
- **RF-03 · Antes de gastar, se avisa de cuánto.** La estimación es la media de lo que costaron las novelas publicadas en esta base. Si no hay ninguna, se usa la referencia de la novela de ejemplo, y se dice de dónde sale. Es una estimación, no un precio.
- **RF-04 · La tabla de la administración ofrece, en cada fila, la acción que toca:**
  - «Generar» para una novela sin generar;
  - «Reanudar» para una parada;
  - «Publicar» para una escrita sin publicar.

  El botón lleva a la página de esa novela, donde está la confirmación con el coste. Una fila sin acción posible no ofrece nada.

## Qué queda explícitamente fuera

- Lanzar desde la tabla sin pasar por la confirmación.
- Generar sin una entrevista cerrada.

## Lo que la gobierna

`SPEC-33` `RF-12`, `RF-13` (el techo y el aviso de gasto), `SPEC-39` (publicar y reanudar), `SPEC-42` (la administración enseña la estantería).
