# Plantilla de `verification.md`

Estructura del documento de salida. Sustituye lo que va entre `<>` y borra los
comentarios en cursiva.

---

```markdown
# Verificación — <nombre del proyecto>

<fecha> · <autor>

<Una frase: qué verifica este documento y, sobre todo, qué NO verifica.>

## Qué se verifica aquí

<Responde explícitamente a las dos preguntas del paso 0: sistema o producto, y
nivel artefacto o proceso. Si el proyecto ya tiene reglas de calidad sobre su
producto, di aquí en qué se diferencian de este documento; si no, alguien las
confundirá.>

## Semilla de contexto

| Documento | Qué aporta a este plan |
| --- | --- |
| `<ruta>` | <qué afirmaciones salen de ahí> |

<Lista los ficheros leídos. Un plan construido sobre una semilla distinta es un
plan distinto, así que la semilla forma parte del documento.>

## Resumen de cobertura

| Clase | Afirmaciones | Cubiertas hoy |
| --- | --- | --- |
| T — Test | <n> | <n> |
| A — Analysis | <n> | <n> |
| I — Inspection | <n> | <n> |
| D — Demonstration | <n> | <n> |
| U — Unverifiable | <n> | — |
| **Total** | **<n>** | **<n>** |

<Cuenta filas. No escribas aquí ningún porcentaje de cobertura de código que no
se haya medido, ni ninguna valoración del tipo "el sistema es fiable".>

## Nivel artefacto — ¿es correcto el código?

| ID | Afirmación | Origen | Clase | Metodología | Criterio de salida | Dónde vive | Estado |
| --- | --- | --- | --- | --- | --- | --- | --- |
| VER-01 | <qué afirma el sistema> | `<fichero>` § <sección> | T | unit testing | <cuándo está verificada> | `<ruta>` | pendiente |

## Nivel proceso — ¿se comporta el agente de forma fiable?

<Misma tabla. Solo si el sistema tiene agentes.>

## No verificable hoy

| ID | Afirmación | Por qué no se puede verificar | Qué falta exactamente |
| --- | --- | --- | --- |
| VER-<n> | <…> | <…> | <el dato, el umbral o la herramienta que falta> |

<Esta sección es obligatoria aunque esté vacía. Si está vacía, dilo: "ninguna".
Un plan sin filas U casi siempre es un plan que ha marcado como verificado algo
que no lo está.>

## Casos negativos

<Para cada afirmación de clase T, el caso que la viola a propósito. Una regla
que nunca ha fallado en las pruebas no está verificada, solo declarada.>

| ID | Caso negativo | Qué debe cazarlo |
| --- | --- | --- |
| VER-01 | <entrada que viola la afirmación> | <la prueba concreta> |

## Orden de implantación

<En qué orden se van cerrando las filas y por qué. Primero lo que corta la
propagación de errores, después lo que cuesta poco, al final lo caro.>

## Decisiones abiertas

- [ ] <lo que hay que decidir antes de poder cerrar alguna fila>
```

---

## Comprobaciones antes de dar el documento por bueno

Recórrelas una a una:

- [ ] Cada fila cita fichero **y** sección de origen.
- [ ] Cada criterio de salida se puede comprobar; ninguno dice "que funcione".
- [ ] **Ningún criterio remite a algo que no esté escrito.** Busca artículos
      definidos sin antecedente —"la prioridad declarada", "el orden acordado"— y
      comparaciones sin segundo operando —"solo crece", "no supera lo fijado"—.
      Un criterio colgante no falla, no avisa y cuenta como cobertura. **No hay
      forma automática razonable de detectarlo: esta lectura es el control.**
- [ ] Ningún número aparece sin haber sido medido. Los que faltan dicen
      "sin medir" o están en la tabla `U`.
- [ ] Toda regla numerada del proyecto se referencia por su identificador.
- [ ] Toda fila `T` tiene su caso negativo en la sección correspondiente.
- [ ] Ninguna fila usa un juez LLM para algo que una regla decide.
- [ ] La sección "No verificable hoy" existe, aunque diga "ninguna".
- [ ] El resumen de cobertura cuenta filas y no promete calidad.
