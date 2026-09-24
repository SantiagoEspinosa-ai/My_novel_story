---
name: no-falla-pisa-el-dato-que-desaparece
description: En My_novel_story, el fallo recurrente no es que algo reviente sino que una escritura pise otra en silencio; hay que leerlo como patrón, no como bug suelto.
metadata:
    pinned: false
---

# «No fallaba: pisaba» — el patrón del dato que desaparece sin ruido

El usuario de `My_novel_story` señaló este patrón después de que apareciera por
tercera vez en una misma semana, y pidió expresamente que quedara anotado **con
esa lectura y no solo como el bug concreto de turno**.

## En qué consiste

Una clave de unicidad —`PRIMARY KEY`, `INSERT OR REPLACE`, un `dict` indexado—
deja fuera el campo que distingue dos filas que **no significan lo mismo**. El
resultado no es un error: es que la segunda escritura pisa a la primera, la
tabla se queda con una fila perfectamente creíble, y cuál sobrevive depende del
orden de escritura. Nada falla, nada avisa, y lo que se pierde es justo el campo
que separaba un dato medido de una afirmación no verificada.

Casos vistos en el proyecto:

- `F-39`: `hecho_canonico` tenía clave global por `id` mientras el código ya
  trataba el mismo identificador en dos obras como dos hechos. El segundo
  `declarar_hechos` dejaba a la obra anterior **sin ningún hecho**, y su prompt
  volvía a decir «hechos: (ninguno)».
- `uso_de_hecho` con clave `(hecho, escena, tipo)`: una fila `depende`
  **observada** y una **declarada** sobre el mismo par no cabían a la vez, y
  `origen_de_uso` existe precisamente para distinguirlas.
- El mismo mecanismo estaba detrás del `mayor` leído de la base que no bloqueaba
  nada, porque volvía como cadena y no como miembro de su enumeración.

## Qué hacer con él

1. **Al diseñar una clave, preguntar qué dos filas distintas podrían colisionar**
   y si alguna de ellas transporta la procedencia del dato. Si un campo existe
   para decir *quién lo afirma* o *a qué obra pertenece*, casi siempre pertenece
   a la clave.
2. **Reproducirlo antes de arreglarlo.** Escribir las dos filas y enseñar que
   sobrevive una: sin esa demostración, «he ampliado la clave» no se distingue
   de un cambio cosmético.
3. **Escribirlo como patrón** en la documentación del proyecto, no solo como la
   corrección puntual. El usuario lee estos hallazgos para reconocer el
   siguiente, y un bug contado como bug no ayuda a reconocer nada.
