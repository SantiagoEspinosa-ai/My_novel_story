---
name: listar-antes-de-borrar
description: "En My_novel_story, antes de borrar código o documentación que ya no sirve, hay que listárselo al usuario y separar lo específico del caso viejo de lo que es general y se queda."
metadata:
  node_type: memory
  pinned: false
  originSessionId: aef45756-578d-4a65-8b8c-e244131917e7
  modified: 2026-09-23T21:03:14.720Z
---

# Listar antes de borrar, y separar lo específico de lo general

Al pasar el proyecto `My_novel_story` de novelas de terror a novelas para
regalar, el usuario autorizó limpiar lo que ya no sirve con una condición
explícita: *«adelante, pero lístamelo antes de borrar»*. Y añadió el criterio:
separar lo que es **específico** del caso anterior (en terror: la curva de
dread, los presagios, el grado de explicación de la amenaza) de lo que **parece**
específico y en realidad es narrativa general. *«Lo segundo se queda.»*

Cómo aplicarlo:

1. Antes de borrar ficheros, clases, invariantes o secciones de documentos, se
   presenta una lista con cada elemento, dónde vive y por qué sobra. Se borra
   solo después de que el usuario la vea.
2. La lista va en dos columnas: lo que es específico y se propone borrar, y lo
   que parece específico pero es general y se conserva, con el motivo. El error
   caro es borrar algo general porque tenía nombre de terror.
3. En este proyecto borrar no es quitar sin rastro: un identificador publicado
   (`INV-xx`, `VER-xx`, `SPEC-NN`) se marca como obsoleto, no se renumera ni
   desaparece (regla de `AGENTS.md`).

Va en la misma línea que la preferencia de diagnosticar y enseñar los hallazgos
antes de aplicar un arreglo: el usuario quiere ver el alcance antes de que el
cambio sea irreversible.
