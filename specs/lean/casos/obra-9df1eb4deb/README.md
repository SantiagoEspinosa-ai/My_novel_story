# Caso real de Lean: `obra-9df1eb4deb` (EX-15)

**Primera vez que Lean detecta, sobre una novela generada y pagada, incoherencias que ningún otro validador vio.** La puerta de publicación no la publicó.

## La novela

| Dato | Valor | Fuente |
| --- | --- | --- |
| Obra | `obra-9df1eb4deb` | `backend/web.db` |
| Ficha | la de la semilla (datos inventados), copiada de `obra-en-curso` | `backend/salida/conducir.log` |
| Capítulos | 10 de 10 `consolidada` | `SELECT capitulo, estado FROM escena WHERE obra='obra-9df1eb4deb'` |
| Coste | **6,5627 USD en 44 delegaciones**, todas con coste medido | `SELECT sum(coste_usd), count(*) FROM gasto_de_delegacion WHERE obra='obra-9df1eb4deb'` |
| Modelos | Escritor opus; Planificador, Revisor y Editor sonnet; Resumidor haiku | `backend/config/sistema.json` (copia de trabajo), `traza_de_delegacion.modelo` |
| Fecha | 2026-09-25, rondas de la puerta a las 14:37:59 y 14:38:25 (UTC) | `veredicto_de_publicacion.cuando` |

## Qué dijo Lean

- **Código de salida 1. 52 violaciones: 8 de `L-1` y 44 de `L-3`.** Además, 13 comprobaciones sin datos.
  - 3 personajes no tienen fecha de nacimiento, así que su edad no se comprueba (`L-2`).
- **Salida literal completa:** [`salida-verificar-real.txt`](salida-verificar-real.txt).
- **Cronología que Lean recibió:** [`Generado.lean`](Generado.lean).
- **Cómo se obtuvieron** los dos ficheros, reproducidos después sobre una copia de la base (`backend/salida/web-caso-lean-EX-15.db`, que git no guarda):

  ```
  python -X utf8 generar_lean.py <copia de web.db> obra-9df1eb4deb --salida Cronologia/Generado.lean
  lake build verificar-real
  lake exe verificar-real      # exit 1
  ```

- **Es la misma salida que dio la puerta en real:** `veredicto_de_publicacion`, rondas 1 y 2, `codigo_lean = 1`, `publica = 0`. También el hallazgo `INV-28` `bloqueante`, `abierto` (id 46).

Las primeras líneas:

```
== obra-9df1eb4deb ==
cobertura: eventos: 10 · sin fecha legible: 0 · sin nacimiento: 3 · con exclusion: 0 · capitulos no ordenables: 0
violaciones: 52 · sin datos: 13
  [L-1] evt-obra-9df1eb4deb-cap-02-e1 se lee despues de evt-obra-9df1eb4deb-cap-01-e1 (discurso 1 -> 2) pero ocurre antes en la fabula (2012-9-25 0:0 < 2026-9-25 0:0) y no declara analepsis
  ...
  [L-3] obra-9df1eb4deb-per-ana esta presente en evt-obra-9df1eb4deb-cap-02-e1 (obra-9df1eb4deb-lug-vagon) y en evt-obra-9df1eb4deb-cap-04-e1 (obra-9df1eb4deb-lug-locomotora) a la vez
  ...
Hay incoherencias temporales: la version NO se publica.
```

## Qué pasaba en la novela

La cronología (`evento_cronologico`) tiene un evento por capítulo:

| Capítulos | `t_fabula` |
| --- | --- |
| 1 y 10 | `2026-09-25` |
| 2 a 9 | `2012-09-25`, la misma fecha, sin hora |

- **`L-1`, 8 violaciones.** Los capítulos 2 a 9 se leen después del 1 y ocurren antes en la fábula. Es un recuerdo contado como analepsis, y hoy no hay dónde declararla (`SPEC-24`, aprobada y sin plan).
- **`L-3`, 44 violaciones.** Los capítulos 2 a 9 comparten el mismo instante y transcurren en lugares distintos (vagón, locomotora, vagón restaurante, estación). Así, cada personaje presente en dos de ellos está «en dos lugares a la vez».
- **La causa está en el plan.** El Planificador puso la misma fecha, sin hora, a ocho escenas sucesivas, y una fecha anterior a la del capítulo 1.

## Qué vieron los demás validadores

| Validador | Resultado en esta obra | Fuente |
| --- | --- | --- |
| Revisor del plan (semántico) | aprobó el plan, en la reanudación | `backend/salida/conducir.log` |
| Puertas de escena: `INV-02` (accesibilidad) e `INV-03` (conocimiento) | pasaron: miran escena a escena, no dos escenas del mismo instante | `SELECT invariante, count(*) FROM hallazgo WHERE escena LIKE 'obra-9df1eb4deb%' GROUP BY 1` → solo `INV-17` 2, `INV-25` 11, `INV-28` 1 |
| Editor, `INV-26` | sin hallazgos | ídem |
| Juicio de obra, `INV-27` | sin hallazgos | ídem |
| **`INV-08` (orden temporal, nivel capítulo)** | **ningún hallazgo**, aunque es la regla que tenía que cazar las 8 `L-1` | ídem, y `F-214` |

**Por qué `INV-08` no la vio (`F-214`).** La puerta de capítulo sí se evalúa:
- `orquestacion/obra.py:359` guarda en `g.cierre` el resultado de `evaluar_cierre`, que con estas fechas dice `puede_cerrarse: False`.
- Pero en la novela regalo nadie lee ese resultado: `orquestacion/novela.py:522` lo copia en `total.cierre`, el capítulo siguiente lo sobrescribe, y nada para ni deja hallazgo.

Es el mismo patrón que `F-47`: una regla que se calcula y no actúa. Y otra vez lo destapa Lean, que sí se ejecuta. Las 44 `L-3` no las cubre ninguna otra regla: `INV-02` mira la accesibilidad escena a escena y no compara escenas del mismo instante (`docs/cobertura-examen.md`, `EX-15`).

## Qué se hizo después

- El plan ya no puede repetir el problema (`F-213`). `planificacion/cobertura.py` devuelve al Planificador, sin pagar al Revisor, un plan cuya `t_fabula` no avanza estrictamente de una escena a la siguiente.
- El prompt del Planificador pide fecha y hora distintas por escena, coherentes con el orden del discurso.
- La novela se relanza con la misma ficha en una obra nueva. Esta se conserva tal cual, como prueba del caso.
