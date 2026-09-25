# El Revisor caza un plan que contradice la ficha antes de escribir nada

Caso real del 2026-09-25. Obra `obra-b113c7dd8c`, ficha de la semilla (datos inventados) y primera generación. Los modelos del Planificador y del Revisor eran sonnet (`backend/config/sistema.json`).

## Qué dice la ficha

Tiene tres elementos (`SELECT ficha FROM entrevista WHERE obra='obra-b113c7dd8c'`):

| Tipo | Descripción | Nombre |
| --- | --- | --- |
| rasgo | colecciona mapas antiguos | — |
| recuerdo | el viaje en tren a Lisboa | — |
| mascota | **un galgo muy lento** | Brisa |

Los agentes no ven los nombres reales, sino pseudónimos (`SPEC-34`; tabla `pseudonimo`):

| Nombre real | Pseudónimo | Papel |
| --- | --- | --- |
| Irene | Patricia | destinatario |
| Valdés | Aranda | destinatario |
| Brisa | Jara | mascota |

## Las rondas del plan

Fuente: `SELECT version, aprobado, origen, objeciones FROM plan_de_obra WHERE obra='obra-b113c7dd8c'`. Las objeciones van copiadas literalmente.

| Versión | Quién la devolvió | Objeción |
| --- | --- | --- |
| 1 | código (cobertura) | «el protagonista se llama «Irene Valdés» en la ficha y el plan no tiene ningun personaje con ese nombre exacto». El Planificador había escrito `[NOMBRE_ANONIMIZADO]` (`F-215`) |
| 2 | **Revisor** | «El tono declarado en la ficha es "divertido", pero los capítulos 3, 4 y 7 (ejes cordura/seguridad/vida en negativo) construyen una atmósfera inquietante y hasta amenazante -tinta que se mueve sola de noche, estación vacía a horas imposibles, vagones que se borran y amenazan con deshacer el tren entero- sin ningún contrapunto de humor. Solo el capítulo 6 aporta comedia (Brisa tropezando al camarero). Hay que reescribir la sinopsis de esos tres capítulos para que el peligro se trate con ligereza y gracia -por ejemplo dándole a Irene o a Brisa una reacción cómica ante lo sobrenatural, o un gag visual en la estación vacía y en los vagones que desaparecen- de modo que el tono predominante sea divertido y no de suspense inquietante.» |
| 3 | **Revisor** | «El elemento 'mascota' de la ficha describe a [MASCOTA_ANONIMIZADA] (id obra-b113c7dd8c-per-jara) como 'un galgo muy lento', pero el plan contradice ese rasgo: en obra-b113c7dd8c-cap-03, obra-b113c7dd8c-cap-04, obra-b113c7dd8c-cap-06, obra-b113c7dd8c-cap-07 y obra-b113c7dd8c-cap-08 se la muestra persiguiendo su cola, resbalando a la carrera, saltando entre vagones y persiguiendo destellos ladrando con entusiasmo. Hay que reescribir esas sinopsis para que sus movimientos reflejen lentitud (por ejemplo, trote pausado, llegar siempre un paso por detrás de la acción, quedarse rezagada) en vez de carreras y saltos ágiles, manteniendo el resto de la escena igual.» |
| 4 | código (cobertura) | la misma que en la versión 1: otra vez `[NOMBRE_ANONIMIZADO]` |

- Con eso se agotaron las rondas y la generación se paró con `PlanNoAprobado`.
- El conductor la reanudó (`backend/salida/conducir.log`, 09:06:34), y el plan volvió a empezar en la versión 5.
- **Coste de la parada:** 1,5115 USD, repartidos así (`SELECT agente, sum(coste_usd), count(*) FROM gasto_de_delegacion WHERE obra='obra-b113c7dd8c' GROUP BY agente`, tomado en ese momento):

  | Agente | USD | Delegaciones |
  | --- | --- | --- |
  | Planificador | 1,2438 | 5 |
  | Revisor | 0,2677 | 2 |

- **No se escribió ningún capítulo.**

## Por qué se cuenta bien

- **El Revisor juzga la fidelidad a la ficha, no la calidad del plan.**
  - La ficha dice «un galgo muy lento», y el plan hacía correr y saltar a la mascota en cinco capítulos.
  - Ninguna regla del código puede ver eso: la cobertura (`planificacion/cobertura.py`) comprueba que cada imprescindible tenga capítulo, no que el plan lo respete.
- **Lo caza antes de escribir.**
  - El juicio le costó 0,2677 USD en dos rondas.
  - Descubrirlo en el Editor habría significado escribir los capítulos y reescribirlos. Un capítulo reescrito cuesta más que eso: en `obra-6845dbb0d0`, el Escritor costó 3,9119 USD en 19 delegaciones.
- **La objeción dice qué cambiar y dónde:** los capítulos concretos y qué hacer con la mascota («trote pausado, llegar siempre un paso por detrás»). Es lo que pide `PROMPT_REVISOR`: «Cada objecion dice que cambiar y donde» (`planificacion/service.py`).

## Lo que enseña de paso

La objeción de la versión 3 lleva `[MASCOTA_ANONIMIZADA]` donde iría el nombre: la sesión delegada anonimizó el pseudónimo de la mascota. `F-146` no se limita al destinatario. Hoy no bloquea, porque el id `per-jara` salva la objeción; está anotado en `F-215`.
