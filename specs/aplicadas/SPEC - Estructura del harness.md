---
id: SPEC-06
titulo: Estructura de harness/, y dónde viven los validadores que no son tests de una feature
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: d39d90a
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-06 — Estructura del harness

## Qué problema resuelve

**No existe ninguna estructura declarada de `harness/`.** La hubo mientras se escribieron
cinco validadores a modo de prueba, y se borró con la carpeta. `AGENTS.md` reserva la ruta
y dice para qué es —*"ejecución de los validadores de `docs/verification.md` y sus
fixtures"*— pero no dice qué hay dentro.

La consecuencia es que **ninguna ruta bajo `harness/` se puede juzgar**. Eso es lo que
`F-2` detectó y no supo cerrar: señalaba que `harness/esquema/` *"no es ninguna de las
carpetas de la estructura del harness"*, cuando el problema real era que esa estructura no
está escrita en ninguna parte. Y `VER-45`, que ya resuelve las rutas contra el árbol
declarado de `docs/architecture.md`, no tiene contra qué resolver las de `harness/`.

### Por qué estas seis filas no caben en el backend

`F-2` se cerró a medias moviendo tres filas al árbol declarado: `VER-01` a
`commons/dominio/tests/`, `VER-38` a `commons/invariantes/tests/` y `VER-22` a `CI`.
Quedan seis, y **ninguna es un test de una feature**:

| Fila | Qué hace | Por qué no es un test de feature |
| --- | --- | --- |
| `VER-45` | Toda ruta citada en un documento existe o encaja en el árbol | No toca código de producción. Su sujeto son los documentos |
| `VER-46` | Todo literal de enumeración citado en un documento se escribe como en `definitions.md` | Lo mismo |
| `VER-26` | El Juez no aprueba sistemáticamente lo que una persona rechaza | Eval contra un modelo, con corpus y medición, no aserción |
| `VER-40` | El Juez caza el defecto conocido del canario | Lo mismo |
| `VER-51` | La deriva de voz se mide por personaje | Lo mismo |
| `VER-30` | El Escritor no viola las reglas de la amenaza bajo prompts adversarios | Red-teaming, con corpus adversario |

Meterlas en `backend/app/features/` sería mentir sobre lo que son: un linter de documentos
y cuatro evals. La estructura por feature de `A-01` responde a *"un caso de uso del
pipeline que se pueda ejecutar, probar y romper solo"*, y ninguna de las seis lo es.

## Qué tiene que ser verdad al terminar

### C-1 · `harness/` tiene una estructura declarada en `docs/architecture.md`

Declarada en el mismo sitio y con la misma forma que la de `backend/`, para que `VER-45`
resuelva contra ella igual que contra el árbol del backend.

| Carpeta | Contiene | Filas que la usan |
| --- | --- | --- |
| `harness/documentos/` | Validadores cuyo sujeto son los documentos del proyecto | `VER-45`, `VER-46` |
| `harness/evals/` | Evals contra el modelo: corpus, medición y umbral | `VER-26`, `VER-40`, `VER-51` |
| `harness/adversarial/` | Corpus adversario y su ejecución | `VER-30` |

Tres carpetas, no más. `harness/esquema/` **no entra**: sus dos filas ya se movieron al
backend, que es donde vive lo que comparan.

### C-2 · El criterio de pertenencia queda escrito

Lo que decide si un validador va a `harness/` o a `backend/`:

- **Va al backend** si su sujeto es **código de producción**: compara, ejecuta o muta algo
  que vive en `backend/app/`. Entonces vive junto a lo que prueba.
- **Va a `harness/`** si su sujeto son **los documentos** o **el comportamiento de un
  modelo**. No hay código de producción al lado del que ponerlo.

El criterio es el mismo que ya usa el proyecto para el caso negativo de una invariante:
vive en la feature que la ejecuta, no en un directorio aparte. `harness/` no es el cajón de
lo que no sabemos dónde poner; es el sitio de lo que no tiene feature.

### C-3 · `F-2` se cierra

Con las seis filas reubicadas y la estructura declarada, `F-2` pasa de *cerrado a medias* a
cerrado. Su identificador no se reutiliza.

## Qué queda explícitamente fuera

- **La forma interna de cada carpeta** —qué ficheros, qué fixtures, qué nombres—. Eso es
  del plan, no de la spec.
- **Escribir los validadores.** Siguen siendo cero implementados.
- **Los umbrales** de `VER-26`, `VER-40` y `VER-51`, que salen de medir.
- **Si `harness/` cuelga de la raíz o de otro sitio.** `AGENTS.md` ya la reserva en la
  raíz y esta spec no lo discute.

## Qué gobierna esto

`A-01` y `A-02` (estructura por feature y sus dependencias), `F-2`, `VER-45` y la regla de
`AGENTS.md` de que las rutas reservadas se declaran antes de usarse.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿Tres carpetas, o `adversarial/` es una subcarpeta de `evals/`? | Tres. Un eval mide concordancia; el red-teaming busca una violación. Distinta pregunta, distinto corpus |
| 2 | ¿`harness/` queda cerrado a estas tres carpetas? | Sí. Una cuarta necesita spec, que es justo lo que faltó para que `harness/esquema/` apareciera sin que nadie lo decidiera |
| 3 | ¿Los validadores de documentos podrían ir a CI en vez de a `harness/`? | No. `CI` es **dónde se ejecuta**, no dónde vive el código. `VER-22` está en `CI` por eso mismo y no contradice esto |
| 4 | ¿Se declara la estructura en `architecture.md` o en `AGENTS.md`? | En `architecture.md`, junto a la del backend. `AGENTS.md` es el mapa y apunta; no es donde se decide |
