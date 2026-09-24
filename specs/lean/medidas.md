# Medidas de la verificación formal en la puerta de publicación

`PLAN-30` E12, 2026-09-24. Lean 4.34.0 y Lake 5.0.0, en la máquina de desarrollo (Windows 11,
`lake` en `~/.elan/bin`). Ejecutado con `VerificadorLean` del backend —el mismo camino que usa
la puerta: copia temporal de `specs/lean/`, generador, `lake build verificar-real` y
`lake exe verificar-real`—, sin llamar al modelo.

| Base | Resultado | Segundos |
| --- | --- | --- |
| `backend/regalo-prueba.db` (la primera ejecución real; `evento_cronologico` vacía) | `2`, «el generador convirtió cero eventos» | 0,2 |
| Base limpia: dos eventos en orden, con un personaje con fecha de nacimiento | `0` | 3,9 |
| La misma base con el segundo evento antes en la fábula | `1`, `L-1` sobre `ev-1,ev-2` | 3,8 |

## Cómo leer los tiempos

- **Una sola ejecución por caso.** La varianza está sin medir.
- **Son tiempos en caliente.** La copia temporal lleva el `.lake` ya compilado del repositorio,
  así que `lake build` solo recompila `Generado.lean`. **Una compilación en frío** —un clon
  nuevo, sin `.lake`— compila todo el proyecto, y ese tiempo **está sin medir**. Sesga hacia
  abajo: el primer arranque en otra máquina tardará más.
- El caso de la base vacía no llega a Lean: el generador para antes, y por eso tarda 0,2 s.

## Lo que decide

`TIEMPO_MAXIMO_LEAN_SEGUNDOS = 300` (`backend/app/commons/config.py`) queda **elegido con esta
medida delante**: casi 80 veces lo medido en caliente, para cubrir la compilación en frío que no
se ha medido. Quedarse corto no da un verde falso: un tiempo agotado es «sin veredicto», que
bloquea la publicación (`SPEC-30` `RF-09`).
