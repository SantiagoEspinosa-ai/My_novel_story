---
name: una-carpeta-por-sesion-y-commit-por-ruta
description: "En My_novel_story trabajan varias sesiones a la vez; cada una va en su propio git worktree y se commitea por ruta, nunca con add -A ni commit -a, y el add y el commit van en un solo comando."
metadata: 
  node_type: memory
  pinned: true
  originSessionId: 02b8c887-4903-4ad6-a29f-28e552cdb4de
  modified: 2026-09-23T16:26:47.892Z
---

# Una carpeta por sesión, y se commitea por ruta

En `My_novel_story` hay **varias sesiones trabajando a la vez sobre el mismo
repositorio**. Eso no es una anécdota del día: es la condición normal de este
proyecto, y cambia cómo hay que usar git.

## Las tres reglas

1. **Cada sesión trabaja en su propio `git worktree`**, una carpeta por sesión,
   todas compartiendo el mismo `.git`. Antes de empezar, `git worktree list`
   para ver cuál toca; si la carpeta propia no existe, se monta con
   `git worktree add -b <rama> ../My_novel_story-<nombre> <rama-de-partida>`.
   Una rama solo puede estar en un worktree a la vez. Lo ignorado —`.env`,
   `*.db`, `salida/`— no viaja a un worktree nuevo y hay que copiarlo a mano.
2. **Nunca `git add -A` ni `git commit -a`: se añade por ruta.** Un barrido se
   lleva lo que otra sesión dejó a medias y lo mete en un commit que no habla
   de ello.
3. **El `git add` y el `git commit` van en un solo comando**, con la ruta
   también en el commit:
   `git add <ruta> && git commit -F - -- <ruta>`. Separarlos en dos llamadas
   deja una ventana en la que otra sesión puede commitear y llevarse lo
   preparado.

## Por qué la tercera, que es la que se olvida

Pasó dos veces seguidas en una misma sesión, con el índice comprobado vacío
justo antes: entre el `git add` y el `git commit`, otra sesión commiteó y se
llevó los cambios preparados dentro de su commit. **El contenido sobrevivió
intacto; lo que se perdió fue el mensaje**, es decir, el porqué de cada
decisión, y el historial quedó atribuyendo el trabajo a un commit sobre otra
cosa. No falló nada en ningún momento: los dos `add` funcionaron, los commits
ajenos funcionaron, y el segundo intento dijo *"nothing to commit, working tree
clean"*, que es la frase de que todo está bien.

Quedó registrado en el repositorio como `F-40`, y su causa de fondo como la
**Regla 6** de `Docs/verification.md`: dos actores sobre un estado compartido
pierden trabajo en la ventana entre dos operaciones, y no falla nada porque
cada operación por separado terminó bien.

**Un worktree separa carpetas, no costumbres.** Tener carpeta propia no exime
de las reglas 2 y 3: el barrido sigue arrastrando lo que uno mismo tenía sin
terminar, y dos sesiones pueden acabar en la misma carpeta.

## Antes de abrir una spec o un identificador

Por el mismo motivo hay que **mirar los identificadores existentes antes de
elegir uno** (`SPEC-NN`, `F-NN`, `VER-NN`): con varias sesiones en marcha, dos
eligieron el mismo `SPEC-NN` dos veces seguidas.
