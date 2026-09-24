---
name: una-condicion-comprobable-no-una-nota
description: "En My_novel_story una advertencia que caduca se escribe como condición comprobable —al estilo de las marcas \"Caduca con:\"— y no como una nota que alguien tenga que acordarse de revisar."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:41:05.488Z
---

# Una condición comprobable, no una nota que alguien tiene que recordar

El repositorio tiene una convención propia: las marcas `Caduca con: <ruta>`, que acompañan a
un número provisional o a una afirmación que solo es cierta mientras algo no exista. No son
un comentario más — dicen **cuándo** dejan de valer, y hay una prueba que comprueba que
siguen ahí.

El usuario la elevó a criterio general al pedirme que abriera la causa de fondo de `MF-26`
como decisión propia:

> *«Es la misma idea que las marcas `Caduca con:` — una condición comprobable en vez de una
> nota que alguien tiene que recordar.»*

El caso concreto: un resultado de verificación no guarda contra qué estado se evaluó, así que
un verde que dejó de valer no se puede caducar ni encontrar. Si lo guardara, **caducaría
solo**.

**Cómo aplicarlo.** Cuando escriba una salvedad, un valor provisional, una suposición que
depende de algo que todavía no existe o un resultado que puede quedarse obsoleto, la forma
correcta no es *«recordar revisar esto cuando…»*: es dejar escrito el dato que permite
comprobar si sigue siendo cierto, y a poder ser que algo lo compruebe. El motivo que da el
usuario es el que importa: **nadie se acuerda**. Una nota que depende de la memoria de
alguien ya ha fallado el día que se escribe.

Vale igual para lo que yo dejo dicho en un documento, en un docstring o en una respuesta: si
una afirmación tiene fecha de caducidad, esa fecha se escribe como condición, no como
intención.

## Su forma en el código es una prueba con nombre

El usuario aprobó explícitamente la misma idea aplicada a una decisión deliberada que alguien
podría «arreglar» más tarde sin saber que era deliberada. Escribí una prueba llamada
`test_las_lecturas_no_miran_el_recorte_y_eso_es_deliberado`, y su respuesta fue:

> *«Un comentario se ignora; esa prueba obliga a pensar antes de borrarla.»*

Así que cuando el código haga algo aparentemente subóptimo **a propósito** —sobre-aproximar,
no afinar, aceptar de más—, la protección correcta no es un comentario explicando por qué:
es una prueba cuyo nombre dice que es deliberado. Un comentario se lee si alguien pasa por
esa línea; una prueba que falla no se puede ignorar, y borrarla es un acto consciente.
