---
name: harness-invariantes
description: >
  Implement, modify or review an invariant check (INV-01..INV-16) in this
  project's harness. Use when writing a rule check or an LLM-judge check,
  deciding whether a check should be deterministic code or a judge, wiring a
  finding (Hallazgo) with its severity, adding the mandatory negative test case
  for an invariant, deciding what blocks a scene at the gate versus what only
  raises a finding, or adding a new invariant to the catalogue.
---

# Invariantes del harness

Cómo se implementa una comprobación `INV-xx`. Las invariantes **se definen** en
`Docs/definitions.md`; esta skill dice **cómo se ejecutan**.

## Regla número uno: lo determinista no lo verifica un modelo

Si la comprobación se puede hacer con código —un orden, un contador, una
pertenencia a un conjunto, una referencia que existe o no existe— **se hace con
código**. Pedírsela a un juez LLM es más caro, más lento y menos fiable, y
además convierte un `sí/no` en una opinión.

Un juez solo entra cuando la comprobación necesita criterio sobre el texto:
función dramática, credibilidad del diálogo, eficacia del presagio, adecuación
al POV, calidad del cambio de valor.

**El reparto ya está decidido en `Docs/definitions.md`**, en la columna `Tipo` de la
tabla de invariantes. No lo reinterpretes caso por caso: doce son de regla,
cuatro son de juez. Si crees que una está mal clasificada, eso es un cambio en
`Docs/definitions.md` y necesita su spec, no un apaño en el código.

## Severidad: se implementa una vez, no caso por caso

En `commons/invariantes/`, y en ningún otro sitio:

| Severidad | Qué hace | Consecuencia |
| --- | --- | --- |
| `bloqueante` | Detiene la escena en la puerta | No pasa a `aceptada` |
| `mayor` | Genera `Hallazgo` y deja seguir | El hallazgo queda abierto y visible |
| `menor` | Genera `Hallazgo` y deja seguir | Igual que `mayor`, con menos prioridad |

Que `mayor` y `menor` dejen seguir **no** significa que se puedan ignorar: el
hallazgo queda abierto y el frontend lo muestra junto al texto. Una escena nunca
se muestra sin sus hallazgos abiertos.

## Todo hallazgo cita su invariante por identificador

`INV-07`, nunca "la regla de los beats". Un `Hallazgo` con descripción libre y
sin identificador es un defecto: no se puede agregar, ni contar, ni cerrar.

## El caso negativo es obligatorio

**Una invariante que nunca ha fallado en las pruebas no está verificada, solo
declarada.** Cada `INV-xx` necesita al menos un caso que la viole a propósito y
que la comprobación debe cazar.

- El caso negativo vive en la feature que ejecuta esa invariante, en su
  `tests/`, no en un directorio de tests aparte.
- Escribe el caso negativo **antes** que la comprobación: es TDD y además es la
  única forma de saber que la comprobación hace algo.
- Un doble de prueba tiene la misma forma que lo real. Si el modelo devuelve
  texto y delta en la misma respuesta, el doble también.

## Dónde vive cada cosa

| Qué | Dónde |
| --- | --- |
| El registro de `INV-01`…`INV-16`, la severidad y el resultado tipado | `commons/invariantes/` |
| Las comprobaciones de escena, de regla | `features/verificacion/` |
| Las comprobaciones de juez, con su `Rubrica` | `features/verificacion/` |
| Las comprobaciones de nivel obra y capítulo | `features/auditoria/` |
| Los casos negativos | `tests/` de la feature que ejecuta la invariante |

Las de nivel obra y capítulo van aparte porque no se pueden hacer escena a
escena. De **obra**: `INV-06`, `INV-09`, `INV-11`, `INV-12`, `INV-13`, `INV-14`
e `INV-16`. De **capítulo**: `INV-08` e `INV-15`.

`INV-14` faltaba en esta lista y no estaba asignada a ningún agente que pudiera
ejecutarla; `INV-08` e `INV-15` son de capítulo y estaban colgando del
verificador de escena. Las tres las ejecuta el Auditor de obra.

## Añadir una invariante nueva

En este orden, sin saltarse ninguno:

1. Se define en `Docs/definitions.md` con su identificador, nivel, severidad y tipo.
   Antes de eso no existe.
2. El identificador **no se reutiliza ni se renumera**. Lo que deja de aplicar
   se marca obsoleto, no se borra.
3. Se añade su fila en `Docs/verification.md` con su caso negativo.
4. Se implementa, empezando por el caso negativo.

Y como es un cambio que decide algo nuevo, necesita **spec aprobada** antes de
tocar `Docs/definitions.md`. Ver el proceso en `AGENTS.md`.

## Errores que hay que vigilar

| Error | Por qué está mal |
| --- | --- |
| Pedirle a un juez algo que decide una regla | Caro, lento, no determinista, y el resultado no se puede reproducir |
| Resolver la severidad dentro de cada verificador | Acaba habiendo tres comportamientos distintos para `mayor` |
| `Hallazgo` sin identificador de invariante | No se puede agregar ni cerrar |
| Comprobación sin caso negativo | No está verificada, solo declarada |
| Invariante inventada en el código | Si no está en `Docs/definitions.md`, no existe |
| Bajar una `bloqueante` a `mayor` para desatascar | Es exactamente lo que la puerta existe para impedir |
