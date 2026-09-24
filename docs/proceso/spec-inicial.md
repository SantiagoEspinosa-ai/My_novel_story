# Spec inicial: qué se decidió construir y por qué, antes del código

## La secuencia, con fechas del historial de git

| Momento | Qué | Commit |
| --- | --- | --- |
| 2026-09-21 15:15 | El modelo de dominio llega al repositorio: lo que hoy es `docs/definitions.md` | `85c702a` |
| 2026-09-21 15:58 | `CLAUDE.md`: stack, límite de contexto de 100.000 tokens, SQLite con soporte vectorial | `2ac0fd9` |
| 2026-09-21 17:55 | `SPEC-01`, la spec del backend, y el proceso de trabajo con sus tres puertas | `763a4d7` |
| 2026-09-22 20:54 | `SPEC-01` aprobada y `PLAN-01` abierto | `7ecfe4b` |
| 2026-09-22 21:47 | **La primera línea de código del backend** | `491f76a` |

Entre el primer documento y la primera línea de código pasaron más de treinta horas, y el
código solo empezó cuando la spec y su plan estaban aprobados. Es la regla del proyecto
(`AGENTS.md` § "Proceso de trabajo"), no una casualidad del calendario.

## Qué decidió `SPEC-01`

**Propósito**, en sus palabras: *«llevar una escena de principio a fin con todas las
puertas cerrándose de verdad, que es lo más pequeño que ejercita la arquitectura entera:
presupuesto de contexto, agentes, invariantes, delta y reconstrucción de estado. Un sistema
que hace eso una vez, lo hace cien veces; uno que no, no escala por mucho que genere
texto.»*

**Por qué una escena y no una novela.** Porque lo difícil de una novela larga no es el
volumen sino la continuidad, y la continuidad depende de cuatro mecanismos —el presupuesto
de contexto, el delta, la reconstrucción del estado y las puertas— que ya aparecen enteros
en una sola escena. Generar volumen antes de tenerlos habría producido texto sin forma de
saber si era coherente.

**Qué dejó fuera, y por qué** (`SPEC-01` §1.2): las invariantes de obra, porque con una
escena no se pueden ejercitar; el frontend, que es otra spec; y la novela completa, porque
*«el objetivo es la escena, no el volumen»*.

## Cómo llegó la novela regalo

El caso base de partida era una novela de terror. El producto del examen —una novela
personalizada para regalar— entró después, **también por spec y antes de su código**:

- `SPEC-14` (2026-09-23): no había clave de API sino una suscripción, así que los agentes
  se ejecutan delegando en sesiones de Claude Code.
- `SPEC-25` (2026-09-23): el destinatario, la entrevista, el texto libre como contenido no
  confiable y las palabras vetadas en tres niveles.
- `SPEC-26` (2026-09-23): el pipeline de la novela regalo —Planificador con Revisor del
  plan, Editor con rúbrica, validadores de personalización, los dos hooks— y, en su v3, la
  retirada de lo específico de terror.
- `SPEC-27`…`SPEC-31` (2026-09-23): lo que el contraste con `EXAMEN.md`
  (`docs/cobertura-examen.md`) encontró sin recoger: PDF, tools, Langfuse, puerta de
  publicación y evaluación.

**Lo que no cambió al cambiar de producto** es la decisión de fondo de `SPEC-01`: el harness
se construye para la continuidad, y la personalización se mide con validadores igual que la
calidad, no en lugar de ella.
