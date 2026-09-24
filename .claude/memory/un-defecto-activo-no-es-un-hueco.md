---
name: un-defecto-activo-no-es-un-hueco
description: "En My_novel_story, un defecto que ya está roto hoy se separa de la lista de capacidades que faltan y se arregla antes, porque no decide nada nuevo y no necesita spec."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:12:09.376Z
---

# Un defecto activo no es un hueco, y va aparte y antes

Al entregar una spec del frontend con una lista de quince carencias del backend, metí en esa
lista un defecto que ya está roto hoy: ninguna escena sabe a qué capítulo pertenece, de modo
que la puerta de cierre de capítulo pide las escenas *del capítulo* a una consulta que filtra
**por obra**, y acaba evaluando la obra entera. El usuario lo sacó de la lista:

> *"G-01 es un defecto activo y no un hueco — que la puerta de cierre evalúe la obra entera
> en vez del capítulo es un fallo hoy, sin frontend de por medio. Va aparte y antes."*

La distinción que pide, y que conviene aplicar a cualquier lista de carencias que yo escriba:

- **Un hueco** es una capacidad que nadie ha construido todavía. Depende de la función que la
  necesita y se prioriza con ella.
- **Un defecto activo** es algo que ya está mal **contra un requisito ya aprobado**, y que
  está produciendo daño ahora mismo aunque la función que lo destapó no exista. No depende de
  nada: se arregla antes, y por su cuenta.

Consecuencia práctica en este proyecto: un defecto así **no necesita spec**, porque no decide
nada nuevo —el requisito ya está aprobado y el dominio ya lo dice—; necesita la prueba que lo
caza, que es la exigencia de siempre. Enterrarlo en una lista de dependencias de una función
futura lo convierte en algo que espera a que alguien apruebe otra cosa.

Al escribir una lista de hallazgos, conviene separar las dos clases explícitamente en vez de
mezclarlas y dejar la distinción para el lector.
