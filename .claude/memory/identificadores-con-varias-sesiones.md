---
name: identificadores-con-varias-sesiones
description: En My_novel_story, con varias sesiones escribiendo a la vez hay que reservar el identificador antes de escribir, y si dos colisionan el primero publicado conserva el número.
metadata:
    pinned: false
---

# Identificadores publicados cuando hay varias sesiones escribiendo

`My_novel_story` numera casi todo —`SPEC-NN`, `PLAN-NN`, `INV-xx`, `VER-xx`,
`MF-xx`, `F-xx`— y tiene la regla de que **un identificador publicado no se
reutiliza ni se renumera**. Con tres sesiones de Claude Code trabajando a la vez
sobre el mismo repositorio esa regla se rompió sola: aparecieron dos `F-39` y
dos `F-40` con contenidos distintos en `Docs/verification.md`, porque cada
sesión miró cuál era el último identificador usado y las tres vieron el mismo.

## Cómo elegir el número antes de escribir

**Mirar el último usado no basta.** Entre la lectura y el commit, otra sesión
puede haber publicado ese mismo número. El usuario pide una de estas dos cosas:

- **Reservar antes de escribir**: anunciar el identificador a las otras sesiones
  y escribirlo en su documento antes de desarrollar el contenido, para que quede
  ocupado.
- **Comprobar al commitear**: volver a mirar los identificadores publicados
  justo antes del commit, no al empezar a redactar.

## Cómo resolver una colisión que ya ocurrió

El criterio del usuario es el mismo que aplica a las specs:

1. **El que se publicó primero conserva el número.** Se decide por el historial
   de git, no por cuál parece más importante.
2. **El segundo pasa al siguiente identificador libre.** No se fusionan ni se
   borra ninguno: son dos hallazgos distintos.
3. **Se actualizan las referencias cruzadas** en el mismo cambio, porque un
   identificador movido sin sus citas deja el documento apuntando a otra cosa.
4. **Lo hace una sola sesión.** Hay que coordinarlo explícitamente con las
   demás antes de tocar nada; dos sesiones renumerando a la vez reproduce el
   problema que se está arreglando.
