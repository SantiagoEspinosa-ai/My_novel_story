---
name: una-carpeta-por-sesion-y-nunca-add-a
description: "En My_novel_story cada sesión trabaja en su propio git worktree y nunca se usa git add -A ni commit -a; se añade por ruta, porque un barrido se lleva el trabajo a medias de otra sesión."
metadata: 
  node_type: memory
  pinned: true
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:23:00.358Z
---

# Una carpeta por sesión, y nunca `git add -A`

Trabajando en `My_novel_story` coincidieron dos sesiones de Claude Code en el **mismo
directorio**. El resultado fue concreto y feo: el repositorio cambió de rama a mitad de
sesión —de `ejecucion-spec-01` a `main` y de vuelta— mientras yo leía ficheros, y un commit
de la otra sesión **barrió un fichero mío sin trackear** y lo metió dentro de un commit que
hablaba de otra cosa. Además las dos sesiones eligieron el mismo `SPEC-NN` dos veces
seguidas sin enterarse.

El usuario pidió montar worktrees y **dejar escrita en `AGENTS.md` la regla que los hace
funcionar**, con su frase: *«Un worktree separa carpetas, no costumbres»*.

## Lo que hay que hacer

- **Una carpeta por sesión**, con `git worktree add -b <rama> ../My_novel_story-<nombre>
  <rama-de-partida>`. Comparten el mismo `.git` y una rama solo puede estar checkouteada en
  un worktree a la vez.
- **Nunca `git add -A` ni `git commit -a`. Se añade por ruta**, siempre. Esto no lo arregla
  el worktree: con carpetas separadas, un barrido sigue arrastrando lo que uno mismo tenía a
  medias.
- **Lo ignorado no viaja** a un worktree nuevo: `.env`, `*.db` y `salida/` hay que copiarlos
  a mano. Las skills sí viajan, porque `.agents/skills/` está versionado.
- **Antes de abrir una spec, mirar qué identificadores existen ya.** Si el número está
  cogido, se renumera el propio —nunca se reutiliza— y **conserva el número la spec que ya
  esté `aprobada`**, porque renumerar algo aprobado rompe lo que lo cite.

## Y antes de escribir, comprobar que el trabajo no está cogido

La misma concurrencia hace que un hallazgo mío pueda estar ya resuelto por una spec aprobada
de la otra sesión. Antes de implementar algo que salió de un análisis propio, conviene mirar
las specs y planes recién aprobados: implementarlo dos veces produce dos migraciones para la
misma columna.
