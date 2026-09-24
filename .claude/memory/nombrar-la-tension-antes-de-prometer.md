---
name: nombrar-la-tension-antes-de-prometer
description: "En My_novel_story, cuando una función pedida puede ser incompatible con el modelo, hay que nombrar la tensión al principio y dar las salidas con su coste —incluida la de que no se pueda— sin resolverla uno mismo."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:12:23.782Z
---

# Nombrar la tensión antes de prometer la función

Al encargar la spec de la regeneración selectiva, el usuario fijó cómo quiere que se escriba
un documento cuando lo pedido puede chocar con el modelo del sistema:

> *"Quiero que empiece reconociendo la tensión de fondo: el examen pide regenerar solo los
> capítulos afectados sin romper la continuidad, y nuestro modelo dice que el estado se
> reconstruye acumulando deltas en orden. Esas dos cosas pueden ser incompatibles, y si lo
> son quiero saberlo antes de prometer la función. No la resuelvas tú. Dame las salidas
> posibles con lo que cuesta cada una, incluida la de que no se pueda hacer sin cambiar el
> modelo."*

Tres reglas que se desprenden y que valen para cualquier documento parecido:

1. **La tensión va al principio, escrita como dos afirmaciones que ambas son verdad hoy**, no
   escondida en un apartado de riesgos al final ni disuelta en prosa optimista. Si la función
   prometida y el modelo no caben juntos, eso es lo primero que hay que poder leer.
2. **Las salidas se enumeran con su coste; no se elige.** La elección es del usuario, y un
   documento que llega con la decisión tomada no le deja nada que aprobar. Esto es la misma
   línea que ya sigue el proyecto para los cambios de comportamiento del harness: se proponen,
   no se implementan.
3. **"No se puede sin cambiar el modelo" es una salida legítima y hay que ofrecerla.** Omitirla
   para que la lista parezca más resolutiva es la versión estructural de inventar un número:
   deja al usuario decidiendo sobre un abanico que no es el real.

Conviene además declarar qué coste está medido y cuál no. Enumerar unidades —"una delegación
por escena regenerada"— y decir que la cantidad no se ha medido es correcto; poner una cifra
plausible no lo es.
