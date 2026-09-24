---
name: corregir-lo-sobredicho-antes-que-nada
description: "En My_novel_story, un documento que dice más de lo que pasó se corrige en cuanto se descubre, antes que cualquier otro trabajo, porque es exactamente lo que evalúa el examen."
metadata:
  node_type: memory
  pinned: false
  originSessionId: 9b30e318-2141-4c9c-865b-7182b46d8e6c
  modified: 2026-09-24T15:38:30.140Z
---

# Lo que un documento dice de más se corrige antes que nada

En una auditoría de `My_novel_story` contra `EXAMEN.md` aparecieron documentos que
afirmaban más de lo que había pasado. Decían que los hooks «ya se ejecutan» cuando solo
habían corrido en la rama que no comprueba nada. Daban 21,6 USD como coste de una obra
cuando esa cifra era una lectura a mitad de generación y el log decía 26,03 USD como suelo.
Yo había dejado esas correcciones para el último bloque del plan, el de documentación. El
usuario lo corrigió:

> *"Corrige los documentos que dicen más de lo que pasó antes que nada. Eso no espera al
> bloque 7: es exactamente lo que el examen evalúa."*

El enunciado lo dice así: *«No se corrige el resultado, se corrige el razonamiento que
llevó a él»*. Un documento de proceso que sobredice es un fallo de ese razonamiento, no un
retoque de redacción pendiente.

## Cómo se aplica

- **En cuanto se descubre una afirmación sobredicha**, se corrige con la cifra o el hecho
  comprobado: se lee el log, la base o el código. No se agenda para después ni se agrupa con
  otras tareas de documentación.
- **Se barre el patrón entero, no la primera aparición.** La cifra de 21,6 USD estaba en
  cinco ficheros, uno de ellos una spec aprobada, y la de los hooks en otros cinco.
- **Una etiqueta como «Construido» esconde la distinción que se evalúa.** El estado de una
  pieza se dice con tres valores:
  - funciona, con una ejecución real que lo demuestra;
  - escrito y sin ejercer;
  - no existe.

  La pregunta del usuario para cada requisito es *«¿corre hoy?»*, no *«¿está escrito?»*.
- Corregir una cifra dentro de una spec aprobada es un cambio documental: conserva la
  aprobación, sube la `version` y lo explica en el historial.
