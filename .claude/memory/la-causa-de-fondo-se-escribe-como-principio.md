---
name: la-causa-de-fondo-se-escribe-como-principio
description: "En My_novel_story, al corregir un fallo hay que elevar su causa de fondo a principio escrito y comprobar que la corrección no degrade a falso positivo una detección real anterior."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-23T02:28:20.621Z
---

# La causa de fondo se escribe como principio, y la corrección no degrada lo ya detectado

Corrigiendo el punto muerto de `INV-03` (`F-31`), el usuario pidió dos cosas que
van más allá de ese caso y que conviene aplicar siempre en este proyecto.

## Lo que causó el fallo se escribe como principio, no solo se arregla

El fallo de fondo era que `prompt.py` le daba al modelo **la forma** del campo
`revelaciones` y no **su significado**, así que el modelo lo dedujo —
correctamente — mientras el código suponía otra cosa. El usuario señaló que ese
punto de la lista era más importante que su sitio sugería y pidió textualmente:

> "Un contrato que no dice qué significan sus campos no es un contrato — que eso
> quede escrito como principio, no solo como arreglo de este caso."

En la práctica: cuando un fallo tiene una causa que se repetirá en otros sitios,
no basta con arreglar la instancia. Se añade como regla numerada en
`Docs/verification.md` (así nacieron las Reglas 1 a 5) o como decisión en el
documento normativo que corresponda, y el arreglo la cita. Un arreglo sin
principio se vuelve a cometer en el siguiente módulo.

## Una corrección no puede degradar a falso positivo una detección real

Al decidir que "revelar es aprender", el caso de `F-24` —el único hallazgo real
que el sistema había producido— dejaba de violar `INV-03`. El usuario no aceptó
que se perdiera en la corrección:

> "Con (a), lo que hizo Ana deja de violar `INV-03`, pero sigue siendo algo […]
> no es actuar con conocimiento indebido, es adquirir conocimiento sin fuente.
> Déjalo como decisión abierta […] si no, `F-24` pasa de detección real a falso
> positivo, y no lo era."

La regla que se deriva: antes de dar por buena una corrección, hay que mirar qué
hallazgos anteriores dejarían de dispararse con ella. Lo que siga siendo un
defecto real, aunque ya no sea el mismo defecto, se deja **escrito como decisión
abierta** con el atributo o mecanismo que lo cubriría, en vez de desaparecer en
silencio. Reclasificar retroactivamente una detección real como falso positivo
falsea el historial del harness, que es lo que el proyecto usa para saber qué
funciona.

## El umbral: a la tercera repetición, regla propia

El usuario fijó el número al ver un mismo tipo de defecto por tercera vez:

> *"Va camino de ser la familia más frecuente del proyecto. Cuéntalas. Si van
> tres o más, merece regla propia junto a las otras."*

Así que la respuesta correcta al reconocer un patrón repetido no es decir que se
parece a otro caso: es **contar las instancias explícitamente, nombrándolas por
su identificador**, y si salen tres o más, escribir la regla junto a las
existentes con su tabla de manifestaciones. Si salen menos de tres, se dice el
número y se deja anotado, sin inflar la cuenta para justificar la regla.
