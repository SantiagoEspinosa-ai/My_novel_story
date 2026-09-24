---
name: corregir-la-duplicacion-no-las-copias
description: "En My_novel_story, cuando dos copias de un dato divergen, la corrección es eliminar la duplicación, no arreglar cada copia."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-21T20:52:52.128Z
---

# Cuando dos copias divergen, se elimina la duplicación, no se corrigen las copias

Es una preferencia que el usuario ha expresado en tres ocasiones distintas, así
que conviene aplicarla por defecto:

- Al decidir la precedencia entre documentos eligió que `CLAUDE.md` mandara y
  que `Docs/architecture.md` **no repitiera sus tablas**, sino que las
  referenciara, descartando explícitamente la opción de duplicarlas "para que
  cada documento se lea solo".
- Al pedir un SRS autocontenido aceptó la duplicación solo con una nota de
  precedencia explícita: si las copias discrepan, gana el documento original y
  la copia se corrige.
- Al encargar la spec de vocabulario lo dijo del modo más claro:
  *"Corrección estructural, que es la importante: las fichas de clase no deben
  volver a enumerar valores. Deben nombrar la enumeración que aplica y punto.
  La duplicación entre fichas y tabla de vocabularios es la causa raíz […] y si
  no se elimina volverá a pasar."*

En la práctica, ante un hallazgo del tipo "el valor `X` está escrito de dos
formas en dos sitios", la respuesta correcta **no** es corregir los dos sitios.
Es preguntar por qué el dato está escrito dos veces y quitar una de las dos
copias, dejando una fuente única y un puntero. Corregir las copias una a una
deja intacta la causa y garantiza la recaída en el siguiente cambio.

Lo mismo aplica al redactar: si al escribir un documento aparece una tabla que
ya existe en otro, el reflejo debe ser referenciarla, no copiarla; y si hay que
copiarla, decir en el propio documento cuál de las dos manda.
