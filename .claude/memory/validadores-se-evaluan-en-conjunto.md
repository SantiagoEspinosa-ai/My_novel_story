---
name: validadores-se-evaluan-en-conjunto
description: En My_novel_story un validador nunca se evalúa aislado; lo que cuenta es qué punto ciego tiene y qué huecos deja el conjunto.
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-22T15:55:06.422Z
---

# Los validadores se evalúan en conjunto, y cada uno declara su punto ciego

El usuario fijó este principio al encargar la revisión de `Docs/verification.md`, y
es la forma en que quiere que se piense la fiabilidad del sistema entero:

> "La IA no garantiza que sus resultados sean correctos, así que la fiabilidad no
> sale del modelo, sale de los validadores que le pones alrededor. Cada validador
> tiene una fortaleza y un punto ciego. Ninguno se evalúa aislado. El objetivo no
> es tener muchos validadores, es que el **conjunto** deje el mínimo de huecos."

Consecuencias concretas al trabajar en verificación en este proyecto:

- **Todo validador lleva su punto ciego declarado.** "Un validador sin punto
  ciego declarado es un validador que no se ha entendido." La pregunta útil no es
  qué detecta, sino qué se le escapa por construcción.
- **La pregunta central es qué fallo se cuela aunque todo esté en verde.** Se
  empieza el análisis por los puntos ciegos, no por la cobertura: lo que ya está
  cubierto no informa.
- **Ojo con la redundancia falsa**: varios validadores ciegos a lo mismo no se
  cubren entre sí. Añadir otro del mismo tipo no tapa nada nuevo.
- **Sin ejemplo concreto de fallo que se colaría, un punto ciego no cuenta.** Y
  no se inventan validadores para llenar una matriz.
- **Una comprobación determinista parcial vale más que un juez completo con
  fiabilidad desconocida.** Un validador que cubre parte de los casos con
  fiabilidad conocida gana a uno que dice cubrirlos todos sin medirla.
- **Se buscan comprobaciones oblicuas y baratas** antes que la medida directa y
  cara: contar frecuencias de palabra en vez de pedir un juicio estético, mirar
  si el delta está vacío en vez de leer el texto, comparar ids antes de llamar a
  un modelo. Cualquier señal lateral que correlacione con el fallo sirve.
