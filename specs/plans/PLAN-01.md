---
id: PLAN-01
spec: SPEC-01
titulo: Plan de implementación del backend del harness
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# PLAN-01 — Backend del harness

Implementa `SPEC-01`, aprobada el 2026-09-22.

## El formato, y por qué este

Es el primer plan del proyecto, así que la forma se propone aquí. Cada paso lleva **cinco
campos** y ninguno es decorativo:

| Campo | Por qué está |
| --- | --- |
| **Ficheros** | `AGENTS.md` lo exige. Además es lo que permite ver si un paso es demasiado grande |
| **La prueba que falla primero** | El proyecto es TDD: *"ningún código de producción nace sin una prueba que haya fallado antes"*. Si un paso no sabe decir qué prueba escribe primero, no está pensado |
| **Qué `VER-xx` pasa a implementable** | `AGENTS.md` pide qué filas cierra. Distingo **implementable** de **cerrada**: una fila se cierra cuando se escribe, y este plan solo dice cuándo deja de estar bloqueada |
| **Por qué va aquí** | Sin esto la tabla es una lista de deseos ordenada por intuición. Si un paso no puede decir qué le obliga a ir donde va, puede moverse |
| **Qué queda funcionando** | *"Cada paso debe dejar el repositorio funcionando"*. Es el campo que impide partir un paso en dos mitades que solo sirven juntas |

**Y una sección propia para los dos órdenes que tiran en direcciones opuestas.** Este es el
rasgo del proyecto que hace que el plan no sea trivial, y lo explico abajo antes de la
tabla, porque es lo que justifica el orden entero.

No llevo estimaciones de tiempo. No se han medido y un número inventado con aspecto de
medido es peor que no tenerlo.

## Dos órdenes en conflicto

`Docs/verification.md` tiene ya una **"Orden de implantación"** de doce puestos, ordenada
por *hueco que tapa*: `VER-38` va primero porque valida a otros tres, y los comprobadores
de estructura van octavos aunque sean baratos, porque comparten `PC-1` y dan sensación de
cobertura sin añadirla.

Ese orden **no se puede seguir tal cual**, y no por desacuerdo: un validador no se puede
escribir antes que el código que valida. `VER-38` es el primero de los doce y necesita que
exista `commons/invariantes/`.

Los dos órdenes se reconcilian así, y es la regla que gobierna la tabla:

> **Se construye en orden de dependencia. Dentro de lo que ya es construible, se elige lo
> que tapa el hueco más grande.**

Por eso `commons/invariantes/` es el paso 2 y no el 6: es lo primero que desbloquea el
validador que `Docs/verification.md` puso el primero de todos.

## Dependencias que obligan a un orden concreto

No todo el orden es obligatorio. Estas seis aristas sí lo son:

| Obliga | A ir antes de | Por qué |
| --- | --- | --- |
| `commons/dominio/` | **Todo** | `CLAUDE.md`: los modelos Pydantic son la frontera de validación y las enumeraciones son `Enum`. Cualquier otro módulo los importa |
| `commons/invariantes/` | `features/verificacion/` | No se puede ejecutar una invariante sin su registro con nivel, severidad y tipo |
| `commons/db/` | Todo lo que persiste | Incluida la cola: `A-05` la pone en la misma base |
| `commons/modelo/` | Toda feature que llame al modelo | Y con él la traza, que `VER-41` necesita |
| `features/contexto/` | `features/generacion/` | El Escritor no se puede llamar sin contexto ensamblado dentro del presupuesto |
| `features/consolidacion/` | La segunda escena de una obra | `INV-05`: sin delta aplicado, la siguiente **no puede generarse** |

Lo que **no** está forzado: el orden entre `features/lectura/`, `features/revision/` y
`features/auditoria/`. Van al final porque consumen lo anterior, pero entre ellas da igual.

---

## Fase A — Cimientos

| # | Paso | Ficheros | La prueba que falla primero | Pasa a implementable | Por qué va aquí | Queda funcionando |
| --- | --- | --- | --- | --- | --- | --- |
| **A1** | Esqueleto y dominio | `backend/app/main.py`, `commons/dominio/`, `commons/errores.py`, `pyproject` | Un modelo Pydantic con un valor fuera de una enumeración **levanta error de validación, no un aviso** (`CLAUDE.md`) | `VER-15`, `VER-01` | Todo lo demás lo importa. Y `VER-01` compara esquemas contra las fichas de `Docs/definitions.md`, así que la comparación empieza a tener sentido desde el primer fichero | Un `main.py` que arranca y no sirve nada |
| **A2** | Registro de invariantes | `commons/invariantes/` + `tests/` | Un registro cuya severidad de `INV-01` no coincide con `Docs/definitions.md` **falla** | **`VER-38`**, `VER-11`, `VER-12` | `VER-38` es el puesto 1 de `Docs/verification.md` porque valida a otros tres. Es lo primero construible de esa lista | El registro y el comportamiento de severidad, sin nadie que los use todavía |
| **A3** | Persistencia | `commons/db/` + migraciones versionadas | Una migración que cambia un atributo obligatorio y no viene en el mismo commit **falla** (`VER-21`) | `VER-21`, `VER-08` | `A-05` pone la cola en la misma base, así que la base va antes que la cola | Base creada y migrable, vacía |
| **A4** | Cola y worker | `commons/trabajos/` + `tests/` | Un trabajo que un worker toma y no termina **no vuelve a `en_cola` por su cuenta** (`O-2`) | `VER-03`, `VER-04`, `VER-29` | Todo endpoint que llama al modelo devuelve `202` y un identificador. Sin cola no hay endpoint asíncrono | Se puede encolar, tomar y fallar un trabajo de mentira |

**Los dos números provisionales entran en A4**, y la sección de abajo dice cómo.

## Fase B — La primera vertical

| # | Paso | Ficheros | La prueba que falla primero | Pasa a implementable | Por qué va aquí | Queda funcionando |
| --- | --- | --- | --- | --- | --- | --- |
| **B1** | Alta de obra | `features/brief/` + `tests/` | `POST /obras` con un `Brief` sin premisa devuelve `422` | `VER-13`, `VER-14` | Es la feature más pequeña con router, schemas, service y repository. Prueba la forma antes de repetirla nueve veces | `POST /obras` y `GET /obras/{id}` de verdad |
| **B2** | Cliente del modelo y traza | `commons/modelo/` + `tests/` | `tokens_declarados` **no lo escribe** el código que calcula `tokens_estimados` | **`VER-41`**, `VER-24` | `VER-41` es el puesto 4 y **desbloquea `VER-34`, `VER-36` y `VER-37`**, que sin él medirían sobre un dato sin validar. Es lo que más rinde por lo que cuesta | Se puede llamar al modelo y queda traza, también si falla |

## Fase C — El camino de una escena

| # | Paso | Ficheros | La prueba que falla primero | Pasa a implementable | Por qué va aquí | Queda funcionando |
| --- | --- | --- | --- | --- | --- | --- |
| **C1** | Ensamblado y recorte | `features/contexto/` + `tests/` | Un recortador que **itera por los seis niveles de `CLAUDE.md` en vez de por los bloques de §2.4** se lleva el registro de conocimiento (`VER-06`) | `VER-05`, `VER-06`, `VER-07` | `RF-26` falla antes que generar, así que el recorte tiene que existir antes que el Escritor | Se ensambla contexto de una escena y se mide |
| **C2** | Escaleta | `features/escaleta/` + `tests/` | Una escena planificada sin `cambio_de_valor` no pasa (`INV-01` en su forma prevista) | `VER-02` | El Escritor necesita una escaleta de la que salir | `POST /obras/{id}/escaleta` |
| **C3** | Generación | `features/generacion/` + `tests/` | Una respuesta del Escritor **con texto y sin delta** se rechaza antes de las puertas | `VER-20`, `VER-25` | Es lo que produce el material que verifican las puertas | Una escena se genera y queda en `generada` |
| **C4** | Puertas | `features/verificacion/` + `tests/` | El caso negativo de **cada** `INV-xx` que esta feature ejecuta | `VER-10`, `VER-11`, `VER-12`, `VER-22` | Puesto 7 de `Docs/verification.md`, y ya construible. Va después de `VER-38` (A2), que es quien garantiza que las severidades sobre las que opera son correctas | Una escena generada pasa o no pasa las puertas |
| **C5** | Consolidación | `features/consolidacion/` + `tests/` | Un delta que falla a mitad **no deja el estado a medias** | `VER-09`, `VER-10`, `VER-42` | `INV-05`: sin esto la segunda escena de la obra no se puede generar. Es donde se corta la propagación del error | Una obra de dos escenas |

## Fase D — Cierre

| # | Paso | Ficheros | La prueba que falla primero | Pasa a implementable | Por qué va aquí | Queda funcionando |
| --- | --- | --- | --- | --- | --- | --- |
| **D1** | Lectura | `features/lectura/` + `tests/` | Una escena se devuelve **sin** sus hallazgos abiertos: falla (`RF-23`) | `VER-18`, `VER-19` | El frontend no existe todavía, pero `RF-23` y `RF-25` son contrato | Los `GET` que el frontend necesitará |
| **D2** | Orquestación | `features/orquestacion/` + `tests/` | Existe un camino de `planificada` a `consolidada` que **no** pasa por `en_verificacion`: falla | `VER-28`, `VER-13` | Es la única feature autorizada a componer otras, así que va cuando ya hay qué componer | El ciclo entero de una escena, automático |
| **D3** | Revisión y auditoría | `features/revision/`, `features/auditoria/` + `tests/` | Un `mayor` abierto **impide cerrar el capítulo**; un `menor` no, y se lista | `VER-45`, `VER-46`, `VER-56` | Cierran el ciclo: la puerta de capítulo y las invariantes de nivel obra | La puerta de capítulo y el barrido de obra |

---

## Los dos números provisionales

`SPEC-07` decidió que existen, que son provisionales y que se declaran como tales. Este
plan los fija, y el riesgo es exactamente el que hay que evitar: **que por el camino dejen
de ir acompañados de su declaración y se conviertan en números a secas con aspecto de
medidos.**

| Número | Dónde vive | Valor |
| --- | --- | --- |
| Tope de reintentos de fallo de transporte (`O-3`) | `commons/config.py` | **Sin fijar en este plan.** Se propone al aprobarlo, no se decide aquí |
| Margen tras el cual un trabajo se considera `abandonado` | `commons/config.py` | Igual |

Los dos entran en el paso **A4** y van con su marca, literalmente:

```python
# Provisional: no está medido. O-3 lo hace depender de observar la tasa real de
# fallos transitorios, y todavía no hay sistema que observar.
# Caduca con: backend/
TOPE_REINTENTOS_TRANSPORTE = ...
```

**Dos reglas para que la declaración no se pierda:**

1. **El número y su marca son una sola cosa.** No se mueve el valor a otro fichero, a una
   variable de entorno o a un fichero de configuración sin llevarse el comentario. Si se
   separan, queda un número sin procedencia y nadie sabrá que no está medido.
2. **La API los devuelve marcados.** `RF-25` ya exige que un dato sin medir se devuelva
   **ausente y distinguible de cero**. Un tope provisional que la interfaz pinta como un
   número normal es un dato sin medir presentado como medido.

**No fijo los valores aquí**, y es deliberado: fijarlos sería inventarlos en el documento
que menos se relee. Van en la aprobación de este plan, donde se ven.

---

## Cómo se aprueba

**Fase a fase, no el plan entero de golpe.** Catorce pasos es demasiado para una sola
aprobación, y la Fase A son tres: si el formato está mal, se ve en tres pasos en vez de en
catorce. Cada fase se aprueba cuando la anterior está terminada, y aprobar una fase es
autorización para escribir su código y solo el suyo.

## Lo que este plan no hace

- **No escribe frontend.** `SPEC-01` es solo el backend.
- **No cierra ninguna fila `VER-xx`.** Dice cuándo dejan de estar bloqueadas; cerrarlas es
  escribirlas, y cada una lleva su caso negativo en el mismo commit.
- **No resuelve las cuatro decisiones abiertas de `SPEC-01` §5.3.** La v1 asume lo que cada
  una dice asumir, y el plan asume lo mismo.
- **No toca `harness/`.** Sus tres carpetas son de `SPEC-06` y no dependen de este plan,
  salvo `VER-56`, que ya es implementable hoy.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿Qué valor provisional tiene el tope de reintentos? | Sin propuesta: no tengo base para proponerlo, y estimarlo sería el fallo que la marca existe para evitar. Un número tuyo, declarado, vale más que uno mío inventado |
| 2 | ¿Y el margen de abandono? | Igual |
| 3 | `VER-15` y `D-3` dicen que los `Enum` de los vocabularios controlados viven **solo** en `commons/dominio/`. Los estados de un trabajo son vocabulario controlado y **no** son dominio. ¿Dónde va su `Enum`? | Ver abajo: es una decisión, no la tomo |
| 4 | `VER-56` recorre las marcas `Caduca con:` **de los documentos**. Los dos números las llevan en **código**. ¿Se amplía su alcance? | Ampliarlo. Si no, las dos marcas que más fácil se pierden son justo las que nadie vigila |
| 5 | ¿Las fases se aprueban una a una, o el plan entero de golpe? | Una a una. Catorce pasos es mucho para una sola aprobación, y la Fase A ya enseña si el formato sirve |

### Sobre la pregunta 3

Salió al repartir ficheros, y es el tipo de cosa que solo aparece cuando se intenta.

- `VER-15`: *"Los `Enum` de los vocabularios controlados viven solo en `commons/dominio/`"*.
- `D-3` de `SPEC-01` dice lo mismo.
- `SPEC-08` decidió que los estados de un trabajo son vocabulario controlado y que **no**
  son dominio, y por eso se declaran en `Docs/architecture.md` y no en `Docs/definitions.md`.

Las tres afirmaciones son razonables y juntas no dejan sitio donde poner el `Enum`. Las dos
salidas:

- **Ponerlo en `commons/dominio/`** aunque no sea dominio. Respeta `VER-15` sin tocarlo, y
  rompe el criterio de pertenencia que acabamos de usar para decidir dónde se declara.
- **Reescribir `VER-15` y `D-3`** para que digan *"los del dominio"*. Respeta el criterio, y
  obliga a decir dónde viven los demás — que es `commons/trabajos/`.

Me inclino por la segunda, porque la primera deja el `Enum` en un sitio que su propia
documentación dice que no le corresponde. Pero toca un validador y un requisito de una spec
ya aprobada, así que lo decides tú.
