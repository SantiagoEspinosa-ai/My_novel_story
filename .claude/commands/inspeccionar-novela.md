---
description: Inspecciona una generacion de la novela regalo contra su base, sus hooks y Langfuse, y separa lo que termino de lo que funciono.
argument-hint: <base.db> <obra>
---

Inspecciona la generacion de la obra `$2` en la base `backend/$1`, siguiendo la skill
`.agents/skills/novela-regalo/SKILL.md` § "Inspeccionar". Abre la base solo en modo lectura.

Dame, en una tabla, para cada pregunta de esa seccion: la respuesta con su cifra leida, y si
delata un fallo callado. Despues comprueba Langfuse con las APIs v2 y v3 para la sesion de la
obra: numero de observaciones por tipo, suma de coste frente al del informe, y si alguna
observacion lleva input, output o modelo.

No reproduzcas nombres de personas de la base: si la obra no es de datos inventados, para y
dilo. No inventes cifras: lo que no puedas leer dice «sin medir».
