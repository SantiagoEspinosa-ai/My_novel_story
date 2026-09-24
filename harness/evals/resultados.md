# Resultados de la evaluacion

Generado por `backend/evaluar.py` desde `gasto_de_evaluacion` y la base de cada ejecucion: **no se edita a mano**. Una fila por brief y pasada, una columna por validador (`SPEC-31` `RF-02`). Las columnas salen del registro de invariantes.

Como se lee: **pasó** solo con constancia de que el validador se ejecuto; **sin veredicto** es que no la hay, o que el validador no llego a juzgar; **sin ejecutar** es que el brief no se ejecuto; **no ejecutado** es que el sistema no ejecuta nunca ese validador (`INV-06`, `SPEC-30` `RF-12`); **no aplica** es una invariante obsoleta, o una comprobacion de la entrevista en un brief que entra por ficha. `INV-28` es Lean.

**Ningun brief se ha ejecutado todavia.** Todas las filas dicen «sin ejecutar»: no hay nada medido.

## Pasada «antes»

| brief | INV-01 | INV-02 | INV-03 | INV-04 | INV-05 | INV-06 | INV-07 | INV-08 | INV-09 | INV-10 | INV-11 | INV-12 | INV-13 | INV-14 | INV-15 | INV-16 | INV-17 | INV-18 | INV-21 | INV-22 | INV-23 | INV-24 | INV-25 | INV-26 | INV-27 | INV-28 | INV-29 | INV-26.continuidad | INV-26.tono | INV-26.arco | INV-26.coherencia_de_personajes | INV-26.ritmo | INV-26.personalizacion | schema.plan | entrevista.instrucciones | entrevista.contradicciones | publicacion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| brief-base | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-injection | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-incoherencia-temporal | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-contradicciones | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-vetadas-por-variantes | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |

| ejecucion | brief | coste |
| --- | --- | --- |
| sin ejecutar | brief-base | sin medir |
| sin ejecutar | brief-injection | sin medir |
| sin ejecutar | brief-incoherencia-temporal | sin medir |
| sin ejecutar | brief-contradicciones | sin medir |
| sin ejecutar | brief-vetadas-por-variantes | sin medir |

## Pasada «despues»

| brief | INV-01 | INV-02 | INV-03 | INV-04 | INV-05 | INV-06 | INV-07 | INV-08 | INV-09 | INV-10 | INV-11 | INV-12 | INV-13 | INV-14 | INV-15 | INV-16 | INV-17 | INV-18 | INV-21 | INV-22 | INV-23 | INV-24 | INV-25 | INV-26 | INV-27 | INV-28 | INV-29 | INV-26.continuidad | INV-26.tono | INV-26.arco | INV-26.coherencia_de_personajes | INV-26.ritmo | INV-26.personalizacion | schema.plan | entrevista.instrucciones | entrevista.contradicciones | publicacion |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| brief-base | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-injection | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-incoherencia-temporal | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-contradicciones | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |
| brief-vetadas-por-variantes | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | no ejecutado | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | no aplica | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | no aplica | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar | sin ejecutar |

| ejecucion | brief | coste |
| --- | --- | --- |
| sin ejecutar | brief-base | sin medir |
| sin ejecutar | brief-injection | sin medir |
| sin ejecutar | brief-incoherencia-temporal | sin medir |
| sin ejecutar | brief-contradicciones | sin medir |
| sin ejecutar | brief-vetadas-por-variantes | sin medir |
