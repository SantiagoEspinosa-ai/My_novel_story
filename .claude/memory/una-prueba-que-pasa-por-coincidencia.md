---
name: una-prueba-que-pasa-por-coincidencia
description: "En My_novel_story, un fixture que hace coincidir dos identificadores distintos apaga todas las comprobaciones que los distinguen; los datos de prueba se eligen distintos a propósito."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T17:28:12.457Z
---

# Una prueba que pasa por coincidencia

En `My_novel_story` el endpoint de cierre de capítulo pedía sus escenas con una consulta que
filtra **por obra**, pasándole un identificador de **capítulo**. Estuvo mal desde que se
escribió y sus dos pruebas estuvieron **en verde desde que se escribieron**, porque el guion
de generación creaba una obra por capítulo y los dos identificadores eran la misma cadena: la
consulta equivocada devolvía el resultado correcto.

No lo encontró ninguna revisión. Lo encontró **cambiar el guion** a una obra con diez
capítulos dentro. El usuario pidió que quedara escrito, con esta formulación:

> *"Una prueba que pasa por coincidencia es indistinguible de una que pasa por corrección, y
> solo se ve cuando la coincidencia desaparece."*

Quedó como **Regla 11** en `Docs/verification.md`.

## Qué cambia en cómo trabajo

- **Los identificadores de un fixture se eligen distintos a propósito.** Si en los datos de
  prueba `obra` y `capitulo` valen `"cap-1"`, ninguna prueba de esa base puede detectar que se
  confunden. Distintos entre sí, no solo distintos de los de al lado.
- **Cuando cambia una suposición sobre los datos** —un guion, un esquema, un formato— hay que
  **ir a buscar lo que la coincidencia estaba tapando**, sistemáticamente y de una vez, en
  lugar de esperar a que los fallos aparezcan durante la ejecución. El usuario lo pidió así:
  *"Tu sospecha hay que perseguirla, no dejarla como aviso"*. El barrido encontró dos
  instancias más que nadie había visto.
- Es distinta de la regla hermana sobre el orden (allí falta un segundo elemento que ejerza la
  distinción): **aquí los dos elementos existen y valen lo mismo**.
