# `harness/adversarial/`

El red-team de `SPEC-31` (`RF-05`, `RF-12`): los casos adversariales, qué validador los
detectó —o que no los detectó ninguno— y cómo se resolvieron. La carpeta la declara
`docs/architecture.md` § "El harness".

| Fichero | Qué es |
| --- | --- |
| `casos.json` | Los casos `RT-01`…`RT-06`: caso, cómo se probó, las pruebas que lo ejercitan, el detector (una columna de `harness/evals/resultados.md`, o `ninguno`), resultado, punto ciego y resolución |
| `brief-exfiltracion-a.json`, `brief-exfiltracion-b.json` | Dos fichas con nombres y palabras clave disjuntos, para el caso de exfiltración entre dos novelas de la misma base (`RT-05`, `RT-06`) |

`backend/app/features/evaluacion/tests/test_red_team.py` comprueba que cada caso nombra
su detector o dice `ninguno`, que las pruebas que cita existen y que hay casos de los
tres temas de `RF-12`. **El log no es de éxitos**: tres de los seis casos dicen `ninguno`.

## Lo que hay que saber antes de leerlo

- **Ningún caso se ha lanzado contra el modelo real.** Todos están probados con dobles o
  con las funciones reales sin modelo. Las ejecuciones reales son `PLAN-31` R2 (injection)
  y R5 (vetadas), y gastan.
- **`RT-05` es una fuga de verdad**, no un caso teórico: la segunda novela de una base
  recibe el mundo de la primera (`F-100`). Hasta que se arregle, cada ejecución real
  necesita su propia base.
- Los casos anteriores —el nombre casi igual, la herramienta que un agente no tiene— y
  los que aparecieron en ejecución sin buscarlos están en `docs/proceso/red-team-log.md`.
  **Se enlazan, no se copian**: dos copias del mismo caso acaban diciendo cosas distintas.
