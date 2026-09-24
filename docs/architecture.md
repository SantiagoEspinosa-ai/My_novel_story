# Arquitectura — My_novel_story

2026-09-21 · @Santiago Espinosa Domínguez

Cómo se construye el sistema que escribe la novela: el reparto frontend/backend, la
estructura de carpetas, los agentes del pipeline con sus habilidades y el proceso que
recorre una escena desde que se planifica hasta que se consolida.

## Qué manda sobre qué

Este documento no es normativo sobre el dominio ni sobre el stack. Desarrolla el *cómo*
de decisiones que se toman en otro sitio.

| Pregunta | Documento que manda | Papel de este documento |
| --- | --- | --- |
| Qué tecnología se usa y cuánto contexto cabe | `CLAUDE.md` | No repite sus tablas. Las referencia y explica cómo se implementan |
| Qué clases, atributos, enumeraciones e invariantes existen | `docs/definitions.md` | No define ninguna. Dice qué componente ejecuta cada `INV-xx` |
| Cómo se ve el modelo de un vistazo | `docs/domain-knowledge.md` | Es una vista del dominio; aquí los diagramas son del sistema |
| Cómo se organiza el código y quién habla con quién | **este documento** | Fuente |

Si una tabla de aquí contradice a `CLAUDE.md`, gana `CLAUDE.md` y esta se corrige. Si un
nombre de clase o de enumeración de aquí no está en `docs/definitions.md`, es un error de
este documento, no una extensión del modelo.

## Qué se ha recogido de los documentos de dominio

El encargo era separar de `docs/definitions.md` y `docs/domain-knowledge.md` lo que no es
estrictamente definición ni conocimiento de dominio. Esto es lo que se ha identificado y
se desarrolla aquí.

**La limpieza sigue pendiente (`A-08`).** El contenido queda por ahora duplicado a
propósito: borrar de los originales y dejar un puntero es un cambio aparte que todavía no
está hecho, y mientras no se haga, la copia de referencia sigue siendo la del documento
original. De los originales se han tocado dos cosas, y ninguna mueve el
contenido duplicado: correcciones documentales —rutas, literales de un diagrama, una
arista mal nombrada— y los cambios de dominio que aplicaron `SPEC-02`, `SPEC-03` y
`SPEC-04`, que pasaron por su propia puerta. La duplicación que describe `A-08` sigue
intacta.

| Origen | Fragmento | Por qué no es definición ni dominio |
| --- | --- | --- |
| `definitions.md` | Tabla "Jerarquía de memoria" | Es el diseño del ensamblador de contexto. Las clases `Ficha`, `Resumen` y `AnclaDeEstilo` sí son dominio; repartirlas en niveles con presupuesto es arquitectura |
| `definitions.md` | Párrafo de los "tres mecanismos" (delta, anclas de estilo, ventana de coherencia frente a ventana de continuidad) | Justificación de diseño: explica por qué el sistema está montado así, no qué es verdad en la ficción |
| `definitions.md` | Sección "Verificadores por tipo" | Reparto de implementación: qué comprueba código, qué comprueba un modelo y qué comprueba una persona |
| `definitions.md` | "Cada invariante debe tener al menos un caso de prueba negativo" | Política de pruebas del harness |
| `definitions.md` | Sección "Decisiones abiertas" | Registro de decisiones. Su sitio natural es `docs/decisions/`, que aún no existe |
| `definitions.md` | Párrafos de justificación en negrita ("La curva de dread evita el fallo más común…", "El registro de conocimiento merece rango propio") | Argumentan la decisión de modelado; la definición es la fila de la tabla, no el párrafo |
| `domain-knowledge.md` | Diagrama "Generación de una escena" | Arquitectura pura: `Orquestador`, `Memoria`, `Generador` y `Verificadores` no son clases de `docs/definitions.md`. Ningún diagrama de dominio debería introducir participantes que el modelo no define |
| `domain-knowledge.md` | Diagrama "Ciclo de vida de una escena" | Mitad y mitad: los estados **son** dominio (enumeración `estado_de_escena`), pero quién dispara cada transición es orquestación |
| `domain-knowledge.md` | Nota "La rama de memoria es la que decide si el sistema escala" | Justificación de diseño |

**Defecto corregido.** `docs/domain-knowledge.md` apuntaba en su segundo párrafo a
`project/697dd43c-600e-4664-a8ce-d8e6c08b6b8f`, un identificador de proyecto externo que
para cualquiera que leyera el repositorio era un enlace roto. Ahora apunta a
`docs/definitions.md` y dice explícitamente que los diagramas son una vista de ese
documento.

## El sistema

Dos piezas desplegables y una base de datos. Nada más.

```mermaid
flowchart LR
  subgraph Navegador
    R["Frontend React<br/>muestra estado y cierra puertas"]
  end
  subgraph Servidor
    API["FastAPI<br/>features + commons"]
    W["Worker de trabajos<br/>mismo proceso"]
  end
  subgraph Externo
    M["Modelo de lenguaje"]
  end
  DB[("SQLite<br/>estado + embeddings")]
  R -->|HTTP/JSON| API
  API --> DB
  API -->|encola| DB
  W -->|consume| DB
  W --> M
  W --> DB
```

La frontera es estricta: el frontend nunca toca la base de datos y nunca calcula nada del
dominio. El cambio de valor de una escena y el estado de las
invariantes llegan resueltos desde la API. Si el frontend necesitara calcular algo para
pintarlo, falta un campo en la respuesta.

### Backend — FastAPI

**Decisión: una carpeta por feature, más una carpeta `commons` para lo compartido.** Una
feature es un **caso de uso del pipeline**, no un plano del dominio ni una entidad. El
criterio es que una feature se pueda ejecutar, probar y romper sola.

```
backend/
  app/
    main.py                  # monta los routers de cada feature
    commons/
      config.py              # configuración y presupuesto de contexto
      db/                    # motor SQLite, extensión vectorial, migraciones versionadas
      dominio/               # Enums de los vocabularios controlados y modelos Pydantic base
      modelo/                # cliente del LLM, conteo de tokens, control de presupuesto
      invariantes/           # registro INV-01..INV-16, severidad, resultado tipado
      trabajos/              # tabla de trabajos, worker, estados de un trabajo
      politica/              # detector de palabras vetadas y audit log del policy engine (SPEC-25)
      errores.py
    features/
      brief/                 # alta de la obra: premisa, tono, guia de estilo, prohibiciones
      escaleta/              # plan de escenas antes de escribir
      contexto/              # ensamblado del contexto de una escena dentro del presupuesto
      generacion/            # producir borrador + delta propuesto
      verificacion/          # puertas: reglas deterministas y jueces
      revision/              # pases dirigidos sobre texto ya generado; la peticion de cambio del lector (PLAN-23)
      consolidacion/         # aplicar el delta y resumir
      auditoria/             # invariantes de nivel obra y capitulo
      entrevista/            # la ficha del destinatario, por turnos, y el texto libre (SPEC-25)
      planificacion/         # de la ficha a un plan aprobado: Planificador, Revisor y cobertura (SPEC-26)
      politica/              # listas de palabras vetadas en tres niveles (SPEC-25)
      evaluacion/            # briefs de evaluacion, libro de gasto, tabla por brief y rastro de exfiltracion (SPEC-31)
      orquestacion/          # compone las anteriores; unica autorizada a hacerlo
      lectura/               # consultas de solo lectura que alimentan el frontend
      manuscrito/            # la obra entera: el texto sin tocar, el libro como dato y su PDF (SPEC-27)
```

**La raíz de estas rutas es `backend/app/`, y se escriben relativas a ella.** Cuando
cualquier documento del proyecto cita `commons/invariantes/` o `features/contexto/tests/`,
se refiere a `backend/app/commons/invariantes/` y a `backend/app/features/contexto/tests/`.
El prefijo se declara aquí y no se repite: escribirlo en cada cita serían decenas de
copias del mismo dato, y la próxima vez que `app/` se mueva divergirían una a una. `VER-45`
resuelve las rutas contra esta raíz.

Cada feature tiene la misma forma, y siempre los mismos ficheros:

| Fichero | Contiene |
| --- | --- |
| `router.py` | Endpoints. Sin lógica: valida, llama al servicio y devuelve |
| `schemas.py` | Modelos Pydantic de entrada y salida. Frontera de validación |
| `service.py` | La lógica del caso de uso |
| `repository.py` | Acceso a datos. Es el único que ve SQL |
| `agente.py` | El prompt y el contrato del agente, si esta feature tiene uno |
| `tests/` | Incluye el caso negativo de cada invariante que esta feature comprueba |

**Reglas de dependencia**, que son lo que hace que la estructura valga para algo:

1. Una feature **nunca** importa de otra feature. Si dos la necesitan, se sube a `commons`.
2. `commons` **nunca** importa de una feature. La flecha va en un solo sentido.
3. `orquestacion/` es la única excepción a la regla 1: existe precisamente para componer
   features en un proceso. Sin esa excepción, la coordinación se colaría por las rendijas
   y acabaría repartida entre todas.
4. Los `Enum` de los vocabularios controlados viven en `commons/dominio/` y en ningún otro
   sitio. Un valor fuera de la enumeración es un error de validación, no un aviso.

### Frontend — React

**Decisión: el frontend mira y además cierra las puertas.** No es solo un panel: es donde
la persona ejecuta las transiciones de la máquina de estados. Una puerta sin interfaz para
cerrarla es teatro, porque todo pasa cuando no hay nadie que la cierre.

| Vista | Qué muestra | Qué deja hacer |
| --- | --- | --- |
| Obra | Estructura de partes y capítulos, progreso | Navegar |
| Escena | Texto, estado (`planificada`…`consolidada`), delta propuesto, hallazgos abiertos | Lanzar generación, aceptar, rechazar, pedir reescritura |
| Puertas | Resultado de cada invariante con su identificador y severidad | Cerrar la puerta o devolver la escena |
| Continuidad | Estado del mundo en `t`, registro de conocimiento, setups sin pagar | Consultar |
| Trabajos | Trabajos en curso y su estado | Seguir un trabajo por su identificador |

Dos reglas de presentación:

- Una escena **nunca** se muestra sin su estado y sin sus hallazgos abiertos. Un texto
  suelto induce a darlo por bueno, que es exactamente el fallo que las puertas evitan.
- Un dato que no se ha medido se muestra como **"sin medir"**, nunca como cero. Un cero se
  lee como una medición; un hueco se lee como lo que es.

**Decisión: el frontend se organiza con Feature-Sliced Design (FSD) v2.1.** Es la
contraparte de A-01 en el navegador, y trae el criterio que al backend se lo da la regla
de features: dónde va cada fichero y quién puede importar a quién.

```
frontend/src/
  app/          # arranque, providers, enrutado
  pages/        # composición por ruta: Obra, Escena, Puertas, Continuidad, Trabajos
  features/     # interacciones reutilizables: aceptar, rechazar, pedir reescritura
  entities/     # modelos de dominio reutilizables: escena, hallazgo, personaje
  shared/       # cliente de la API, componentes sin lógica de negocio, utilidades
```

Tres cosas que conviene no perder de vista:

1. **`shared/` es el equivalente frontend de `commons/`.** Infraestructura sin lógica de
   negocio: el cliente de la API, el sistema de componentes, las utilidades.
2. **La regla de importación es más estricta que en el backend.** Un módulo solo importa
   de capas **estrictamente inferiores**, y los cross-imports entre slices de la misma
   capa están prohibidos. En el backend hay una excepción (`orquestacion/`); aquí no la
   hay, porque la composición ya tiene su capa, que es `pages/`.
3. **No se crean capas vacías por si acaso.** FSD v2.1 recomienda empezar con `shared/`,
   `pages/` y `app/`, y extraer a `features/` o `entities/` solo cuando el mismo código se
   usa ya en varios sitios, tiene una razón de cambio propia y una responsabilidad
   acotada. La capa `widgets/` está desaconsejada por la metodología y no se usa.

La skill oficial de FSD está instalada en el repositorio
(`.agents/skills/feature-sliced-design/`) y es la que manda sobre las dudas de colocación.

### Persistencia — SQLite con soporte vectorial

Una sola base de datos guarda el estado estructurado, los embeddings y la cola de
trabajos. No hay servicio de vectores aparte ni cola externa.

- Se indexan por similitud: fichas de entidad, resúmenes de escena y setups pendientes (`SPEC-26` v3).
- El texto completo de las escenas se guarda pero **no** se recupera por similitud. Para
  eso están los resúmenes. Nunca se manda la obra entera al modelo.
- El estado del mundo se reconstruye acumulando los deltas de escena en orden. No se relee
  el texto para averiguar qué pasó.
- Las migraciones se versionan. Un cambio en `docs/definitions.md` que altere un atributo
  obligatorio necesita su migración en el mismo commit.

**Decisión: la cola de trabajos es una tabla de esta misma base.** Generar una escena
tarda, así que el endpoint inserta una fila en `trabajo`, devuelve su identificador y no
bloquea; un worker del mismo proceso la consume. Con la cola en memoria, un reinicio a
mitad de escena pierde el trabajo en silencio; con la cola en la tabla, sobrevive y el
frontend lo sigue por su identificador.

## Agentes del pipeline

**Decisión: un agente es una llamada al modelo con su propio contexto, su propio prompt y
su propia salida tipada.** Sale más caro en llamadas, y a cambio el Escritor no ve las
rúbricas del Juez, cada salida se valida por separado y un fallo se atribuye a un agente
concreto en vez de a "la generación".

No todo lo que participa en el proceso es un agente. Lo que se puede comprobar con código
se comprueba con código: pedírselo a un modelo es más caro, más lento y menos fiable.

| Agente | ¿Llama al modelo? | Habilidades | Entrada → Salida | Invariantes que toca |
| --- | --- | --- | --- | --- |
| **Orquestador** | No | Aplicar la máquina de estados; decidir la siguiente transición legal; detener en puerta bloqueante | Estado de la escena → transición | `INV-05` (que el delta esté aplicado antes de seguir) |
| **Escaletador** | Sí | Repartir el cambio de valor por escena; asignar beats a arcos | `Brief` + `GuiaDeEstilo` → `Escaleta` | `INV-01`, `INV-07`, `INV-12`, `INV-16` en su forma prevista |
| **Ensamblador de contexto** | No | Recuperar por similitud; seleccionar fichas y setups pendientes; recortar por nivel de prioridad; contar tokens | Escena planificada → contexto dentro del presupuesto | Ninguna; hace cumplir el límite de `CLAUDE.md` |
| **Escritor de escena** | Sí | Escribir la escena; sostener el POV; respetar las anclas de estilo; **devolver el delta estructurado en la misma llamada** | Contexto → `Borrador` + `DeltaDeEscena` | Produce el material de `INV-01`…`INV-04` |
| **Verificador de reglas** | No | Continuidad de entidades; coherencia cronológica; **comparación contra el registro de conocimiento en `t`**; repetición léxica; distribución de longitud de frase | Borrador + delta + estado → `Hallazgo[]` | `INV-01`, `INV-02`, `INV-03`, `INV-04`, `INV-07`, `INV-13` (incremental), `INV-17` |
| **Juez de rúbrica** | Sí | Puntuar con `Rubrica`: función dramática, credibilidad del diálogo, eficacia del setup, adecuación al POV, calidad del cambio de valor | Borrador + rúbrica → puntuación + `Hallazgo[]` | `INV-10`. Como desempate: `INV-03`, `INV-11`, `INV-14` |
| **Revisor** | Sí | Un `PaseDeRevision` por tipo: continuidad, voz, ritmo, densidad, línea | Borrador + hallazgos → borrador nuevo | Las del hallazgo que corrige |
| **Resumidor** | Sí | Condensar escena → capítulo → parte; extraer hechos clave; actualizar fichas de entidad | Escena consolidada → `Resumen`, `Ficha` | Ninguna; es lo que hace que el sistema escale |
| **Consolidador** | No | Aplicar el delta al estado; detectar delta incompatible; reindexar embeddings | Delta aceptado → `EstadoDelMundo(t+1)` | `INV-05`, `INV-06` |
| **Auditor de obra** | Mixto | Comprobaciones de nivel obra y capítulo, que no se pueden hacer escena a escena | Obra completa → `Hallazgo[]` | Obra: `INV-06`, `INV-09`, `INV-11`, `INV-12`, `INV-13`, `INV-14`, `INV-16`. Capítulo: `INV-08`, `INV-15` |
| **Entrevistador** | Sí | Preguntar al comprador con naturalidad; traducir cada respuesta a la ficha y a sus listas cerradas; explicar una contradicción sin juzgar; juzgar lo que queda en `otro` (`SPEC-25` `RF-08b`) | Respuesta del comprador + ficha + lo que el código calculó → ficha actualizada + siguiente pregunta | Ninguna: **qué falta, qué se contradice y si se puede cerrar lo decide el código**, no el agente |
| **Guardián de política** | No | Normalizar y buscar palabras vetadas en tres niveles; devolver la escena al Escritor con el fragmento exacto; parar al agotar las reescrituras; registrar cada decisión en el audit log | Texto de la escena + vetadas de la obra → coincidencias | `INV-21` |
| **Planificador** | Sí | Convertir la ficha en el plan de 10 capítulos de una escena; situar cada imprescindible con sus palabras clave; declarar la cronología (`t_fabula`, nacimientos, exclusiones) | Ficha → `PlanDeLaObra` | Ninguna directa: la cobertura (`RF-06`) la cuenta el código antes del Revisor (`SPEC-26`) |
| **Revisor del plan** | Sí | Comparar plan y ficha: género, tono, ocasión, papel, que no invente ni contradiga, que haya arco | Ficha + plan → aprobado u objeciones | Ninguna: sin plan aprobado no se escribe, hasta 3 rondas (`RF-05`..`RF-07`) |
| **Editor** | Sí | Nota 1–5 por criterio con justificación e instrucción; no reescribe. Y el juicio de obra sobre resúmenes y último capítulo | Capítulo → `ValoracionDelEditor[]`; novela → arco y final | `INV-26`, `INV-27` |

**Qué significa «en su forma prevista».** El Escaletador comprueba `INV-01`, `INV-07`,
`INV-12` e `INV-16` **contra la `Escaleta`, antes de que exista ningún texto**: que cada
escena planificada tenga su `cambio_de_valor`, que sus beats sirvan a un arco, y que la
curva de dread prevista tenga su máximo en el clímax y varianza suficiente *(obsoleto desde `SPEC-26` v3: `INV-12` e `INV-16` se retiraron y el Escaletador ya no prevé la curva)*. Es la misma
invariante sobre el plan en vez de sobre la obra, y por eso no sustituye a la comprobación
del Auditor: un plan correcto que se ejecuta mal sigue fallando, y quien lo caza es el
barrido final sobre la curva realizada.

**Por qué el Verificador de reglas no comprueba invariantes de nivel obra.** Su entrada es
una escena —borrador, delta y estado en `t`—, y `INV-09`, `INV-12` e `INV-16` no se pueden
contestar desde ahí: un setup es huérfano solo cuando la obra termina sin pagarlo, y el
máximo y la varianza de la curva necesitan la serie entera. `INV-06` tampoco es suya: su
forma incremental —que el delta no contradiga el estado en `t`— es del Consolidador, y así
lo dice `RF-20` de `SPEC-01`. Las cuatro son del Auditor de obra.

**`INV-13` es la excepción, y a propósito: se comprueba dos veces.** El Verificador hace la
forma **incremental** —si esta escena revela un hecho que ya estaba revelado, lo dice en la
escena donde ocurre, que es cuando todavía se puede corregir sin rehacer nada— y el Auditor
hace el **barrido** sobre la obra, que es la red por si el incremental falló. No es
duplicación: son dos momentos distintos con dos costes de corrección distintos.

Como los dos pueden levantar un `Hallazgo` de `INV-13`, **hay que poder distinguir cuál
fue**. El dominio ya lo permite: `Hallazgo.verificador` es un atributo obligatorio. Lo que
faltaba era comprobarlo, y eso es la fila `VER-12` de `docs/verification.md`.

**`INV-05` no es del Verificador.** La tiene el Orquestador —que no deja pasar a la escena
siguiente sin delta aplicado— y el Consolidador, que es quien lo aplica. La del Verificador
estaba a pelo, sin razón escrita, y era duplicación sin función. Si alguien la quiere de
vuelta, que la escriba con su motivo.

**Decisión: el modelo del Juez es fijo dentro de una obra.** Cambiarlo a mitad rompe la
comparabilidad entre puntuaciones, y desde `SPEC-10` la comparabilidad decide cuál borrador
se queda en `Escena.borrador_aceptado`. No aplica al Escritor: cambiarle el modelo afecta al
estilo y eso lo caza `INV-15`; cambiárselo al Juez no lo caza nada. La traza registra qué
modelo se usó, o la regla no se puede comprobar después.

**Decisión: el Juez no ve las reglas del proyecto.** Ni `docs/definitions.md`, ni los
enunciados de las invariantes, ni este documento: recibe el texto, la rúbrica y nada más. Si
las viera, su juicio sería un eco del nuestro — y desde `SPEC-04` el Juez es el **desempate**
de `INV-03`, `INV-11` e `INV-14`. Un desempate que ve lo mismo que la regla no desempata:
confirma. Es la Regla 3 de `docs/verification.md` aplicada a un agente en vez de a un
validador.

**Decisión: el Juez no comparte sesión con el Escritor.** Recibe el texto y la rúbrica, no
el prompt ni el razonamiento que produjeron ese texto. Un modelo que juzga su propia
salida con su propio contexto delante tiende a aprobarla. Modelo distinto si se puede;
sesión limpia como mínimo.

### Presupuesto de contexto por agente

El límite duro y el reparto por nivel de memoria están en `CLAUDE.md` y no se repiten
aquí. Lo que sí es arquitectura es **qué niveles recibe cada agente**, porque no todos
necesitan todos.

**Aquí aparecen solo los agentes que llaman al modelo**, porque son los únicos que
consumen el presupuesto de contexto y esta tabla reparte ese presupuesto. El Orquestador,
el Consolidador y el Verificador de reglas no mandan ningún prompt: lo que necesitan para
trabajar está en su columna de habilidades, no aquí. Y el Ensamblador de contexto no
recibe niveles, los **construye**. El criterio se escribe porque estaba implícito, y un
criterio implícito no impide que alguien añada una fila que no le corresponde.

| Agente | Inmutable | Estado actual | Local | Recuperado | Resúmenes |
| --- | --- | --- | --- | --- | --- |
| Escaletador | sí | sí | no | sí | sí |
| Escritor de escena | sí | sí | sí | sí | según profundidad |
| Juez de rúbrica | guía de estilo y anclas | no | escena anterior | no | no |
| Revisor | sí | sí | sí | solo lo que cita el hallazgo | no |
| Resumidor | no | no | la escena que resume | no | los del nivel inferior |
| Auditor de obra | anclas de estilo | sí | la escena que se desempata | setups pendientes | sí, todos |

**El Auditor recibe resúmenes porque es lo que cabe en un prompt, no porque sea lo único
que puede leer.** Esta tabla reparte lo que se **envía** al modelo; sus comprobaciones son
de tipo `regla`, y una regla consulta la base. `INV-15` mide la distancia estilométrica
sobre la prosa real del capítulo sin tocar el presupuesto, y `INV-09` compara filas de
`SetupYPago` —que tiene su plantado y su cobro propios; antes `Presagio`, obsoleta en `SPEC-26` v3—, no líneas de un
resumen: una condensación que se deje un setup no esconde nada.

Recibe `Estado actual` por `INV-06`, que compara hechos vigentes entre sí; `Recuperado`
por los setups pendientes de `INV-09`; y del nivel inmutable solo las anclas de estilo,
que es contra lo que `INV-15` mide la distancia. De `Local` recibe **solo la escena que se
desempata**: es `Mixto` porque `INV-11` e `INV-14` son suyas y escalan al juez, y los dos
desempates preguntan por el texto —si una reversión está justificada, si una revelación
implícita cuenta—, así que necesita esa escena y no la obra entera.

El reparto numérico de tokens entre agentes **no está fijado y no se inventa aquí**. Se
fija cuando haya medidas reales de cuánto consume cada uno; hasta entonces cada agente usa
el presupuesto por nivel de `CLAUDE.md`. **Caduca con:** `backend/app/features/orquestacion/`, que es lo que produce las medidas.

**La regla de recorte no se reenuncia aquí: vive en `CLAUDE.md` § "Límite de contexto" y
este documento la usa, no la redefine.** La precedencia de `AGENTS.md` ya dice que en lo
técnico manda `CLAUDE.md`, así que repetirla era una copia sin autoridad. Y era una copia
con consecuencia: `SPEC-01` §2.4 va a corregir esa regla y declara que modifica
`CLAUDE.md`, sin mencionar este documento, de modo que la corrección habría entrado a
medias y habría dejado los dos textos diciendo lo contrario.

## El proceso

### Una escena, de principio a fin

```mermaid
sequenceDiagram
  participant F as Frontend
  participant API as FastAPI
  participant T as Tabla de trabajos
  participant W as Worker
  participant CTX as Ensamblador
  participant E as Escritor
  participant VR as Verificador de reglas
  participant J as Juez
  participant C as Consolidador
  F->>API: POST /escenas/{id}/generar
  API->>T: inserta trabajo
  API-->>F: 202 + id_trabajo
  W->>T: toma el trabajo
  W->>CTX: pide contexto de la escena
  CTX-->>W: contexto dentro del presupuesto
  W->>E: prompt + contexto
  E-->>W: borrador + delta propuesto
  W->>VR: puerta determinista
  VR-->>W: hallazgos con su INV-xx
  W->>J: puerta de rubrica (sesion limpia)
  J-->>W: puntuacion + hallazgos
  W->>T: resultado del trabajo
  F->>API: GET /escenas/{id}
  API-->>F: texto, estado, hallazgos abiertos
  F->>API: POST /escenas/{id}/aceptar
  API->>C: aplica delta y resume
```

Dos cosas que el diagrama fija y conviene no perder de vista. El Escritor devuelve **dos**
cosas en la misma llamada, texto y delta: pedir el delta después, releyendo la escena, es
más caro y menos fiel. Y la aceptación la dispara la persona desde el frontend, no el
worker: la puerta la cierra alguien.

### La máquina de estados y quién dispara cada transición

Los estados son los de la enumeración `estado_de_escena` de `docs/definitions.md`. Lo que
añade este documento es la columna de quién los mueve.

| Transición | Quién la dispara | Condición |
| --- | --- | --- |
| `planificada` → `generada` | Worker | El Escritor devuelve borrador y delta |
| `generada` → `en_verificacion` | Orquestador | Automática |
| `en_verificacion` → `rechazada` | Verificador de reglas | Falla una invariante `bloqueante` |
| `en_verificacion` → `en_revision` | Juez de rúbrica | Hallazgo `mayor` o `menor` |
| `en_verificacion` → `aceptada` | Orquestador | Pasa todas las puertas |
| `rechazada` → `generada` | Persona desde el frontend | Regeneración |
| `en_revision` → `generada` | Revisor | Reescritura dirigida |
| `en_revision` → `aceptada_por_rendicion` | Orquestador | Se agotaron los intentos y ninguna invariante `bloqueante` sigue abierta. Se elige el menos malo |
| `aceptada` → `consolidada` | Consolidador | Delta aplicado sin conflicto |

**Una escena rendida no pasa a `consolidada`** (`SPEC-30` v4 `RF-11`): el Consolidador aplica su delta igual y lo registra en `escena_consolidada`, pero el estado se queda en `aceptada_por_rendicion`. Esa transición existía y borraba el único dato duradero de que la escena se rindió, que `docs/definitions.md` define como estado; y la puerta de publicación necesita leerlo (`INV-29`).

**No hay rendición desde `rechazada`.** Una invariante `bloqueante` abierta no se rinde
nunca: el delta de una escena rendida entra al canon igual que el de una limpia, y una
falsedad en el canon la heredan todas las escenas siguientes. `Escena.intentos` cuenta y se
enseña, y la salida es humana.

> **Primera de las dos salidas por las que algo sin verificar podría llegar al canon.** La
> otra es el tope de presupuesto, en § "Los estados de un trabajo". Las dos se leen juntas
> o no se entiende ninguna: **cada una por separado parece razonable, y juntas, si se
> relajan, hacen inalcanzable la garantía de que nada se publique sin haber pasado las
> puertas.** Esta se mantiene cerrada con la condición de arriba —ninguna `bloqueante`
> abierta—; la otra, no publicando lo que quedó a medias. Quien toque una tiene que mirar
> la otra en el mismo cambio.

La transición que importa es `aceptada → consolidada`. Hasta que el delta no está
aplicado, el estado del mundo no ha cambiado y la escena siguiente **no puede generarse**:
es ahí donde se corta la propagación del error.

#### El capítulo tiene su propia transición

Los estados de capítulo son los de `estado_de_capitulo`, no los de `estado_de_escena`, así
que van en su propia tabla: mezclar las dos escalas en una sola invita a comparar valores
que no pertenecen al mismo vocabulario.

| Transición | Quién la dispara | Condición |
| --- | --- | --- |
| `abierto` → `cerrado` | **Cliente de la API** | Todas las escenas del capítulo están `consolidada` y ninguna tiene un hallazgo `mayor` abierto |

Los hallazgos `menor` abiertos **no bloquean el cierre**: se listan al firmar, para que
quien cierra sepa qué deja pasar. Los `resuelto` y los `descartado` tampoco cuentan; para
eso existe `descartado`.

Es la **segunda puerta con firma humana** del sistema, junto con la aceptación de escena de
`A-04`, y es la que da sentido a la primera. Al decidir que un hallazgo `mayor` no detiene
la escena, el control no desapareció: se movió aquí, que es donde una persona puede juzgar
si el conjunto se sostiene. Sin esta puerta, un hallazgo `mayor` se quedaba sin ninguna
consecuencia.

### La puerta de publicación (`SPEC-30` v4)

Cuando la novela entera está escrita, `novela.escribir` llama a la puerta
(`orquestacion/publicacion.py`) y nadie la lanza a mano. Una versión se publica solo si
ningún capítulo está rendido (`INV-29`, **decisión nuestra, más estricta que el enunciado**),
no queda ninguna `bloqueante` abierta, Lean devuelve `0` (`INV-28`; el `2` y un Lean que no
se pudo ejecutar también bloquean) y no queda ningún hallazgo de obra del Editor (`INV-27`).
La decisión es una función pura (`auditoria/publicacion.py`) y cada ronda deja su veredicto en
`veredicto_de_publicacion`, que es lo que lee la exportación a PDF.

- **Un fallo de Lean vuelve al Editor como feedback y la generación se detiene sin
  reescribir** (`RF-06`): lo que Lean mira lo fija el plan antes de escribir.
- **Un `INV-27` se convierte en instrucciones** para los capítulos implicados, que se
  reescriben a **delta fijo** (`RF-10`): se acepta solo si los hechos no cambian, y el canon no
  se mueve. Tope de 2 rondas, contado en la base para que relanzar no lo reinicie.
- **`INV-06` queda sin ejecutar** y cada veredicto lo dice (`RF-12`): exige una comparación
  semántica y hoy no hay quién la haga.

`INV-27` sigue siendo `mayor`: que bloquee la publicación es regla de esta puerta, no un cambio
de severidad.

### Regenerar en una obra acumulativa (`SPEC-23` v2, `PLAN-23` Parte A)

Lo común a las dos salidas está construido; **qué se escribe** espera a la medida del arrastre
(`S-1` si la media es ≤ 3 capítulos, `S-2` si es > 3). Hasta entonces `regeneracion.SALIDA` es
`None` y pedir un cambio responde `409` sin encolar nada.

- **La medida** es `orquestacion/arrastre.py` (y `backend/medir_arrastre.py`): lee tablas, no
  escribe, se niega sin obra completa, sin usos o sin procedencia, y lleva en el mismo objeto la
  dirección de su sesgo, **a la baja, hacia `S-1`**.
- **Versiones con identidad** (`D-2`): `version_de_obra` y `capitulo_de_version` en
  `features/brief/`, con disparadores que impiden cambiar una versión creada. Un capítulo que no
  cambió **se comparte por referencia**; uno nuevo en la misma posición es otro capítulo, y
  `capitulo` ya no tiene `UNIQUE (obra, orden)`, que lo borraba.
- **El estado se reconstruye desde los deltas guardados**: `consolidacion/mundo.acumular` es
  puro; `rebobinar` escribe un mundo en las tablas vivas, que son **las de la versión que se
  escribe** (`C-2`). La semilla sale del plan aprobado y del conocimiento anterior al relato.
- **La reverificación** (`D-1`) vuelve a pasar las puertas deterministas de cada escena de una
  versión contra el estado que esa versión reconstruye, sin modelo y sin escribir en `hallazgo`
  (`features/verificacion/repository.py`). Un verde solo cuenta con la **huella** del estado
  vigente (`C-3`); si no, la escena está `sin_reverificar`. `INV-06` e `INV-04` salen como no
  ejecutadas, cada una con su motivo.
- **Cada lector ve solo su versión**: `regeneracion.escenas_de_version` (la vigente si no se
  dice) la usan el bucle de escenas, la memoria del Escritor, el cierre, la puerta de
  publicación, la story bible, el manuscrito y la medida. Los imprescindibles se asignan por
  posición del capítulo en la versión, no por un identificador construido.
- **La petición** (`C-4`) es de un hecho o de un nombre y vive en `features/revision/`. No edita
  nada: los hechos, los nombres y las vetadas **de una versión** se componen desde su cadena de
  peticiones (`hechos_de_version`, `nombres_de_version`, `vetadas_de_version`), y la versión
  anterior sigue leyendo lo suyo. Lo afectado por un renombrado lo decide el texto aceptado y
  la presencia, no el modelo.
- **Endpoints**: `GET /obras/{id}/versiones`, `GET /obras/{id}/versiones/{numero}`,
  `POST /obras/{id}/cambios/propuesta` y `POST /obras/{id}/cambios`. El trabajo
  `regenerar_obra` tiene su worker (`regeneracion.atender`), que **no escribe nada** mientras
  no haya rama: las ramas son de la Parte B.

Lo que no hace: la puerta de publicación y el PDF **por versión**, ni la cronología y el
generador de Lean por versión (`F-93`).

### Severidad: bloqueante frente a mayor y menor

La diferencia se implementa una vez, en `commons/invariantes/`, y no se resuelve caso por
caso en cada verificador:

- **`bloqueante`** detiene la escena en la puerta. No pasa a `aceptada`.
- **`mayor`** y **`menor`** generan `Hallazgo` y dejan seguir, pero el hallazgo queda
  abierto y el frontend lo muestra junto al texto.
- La diferencia entre `mayor` y `menor` está **una puerta más arriba**: un `mayor` abierto
  impide cerrar el capítulo, un `menor` solo se lista al firmar. Sin esa puerta las dos
  severidades producirían exactamente el mismo comportamiento, y una escala cuyos valores
  no se distinguen en nada es una etiqueta, no un control.

Todo hallazgo cita su invariante por identificador (`INV-07`), nunca por descripción.

### Los estados de un trabajo

La tabla de trabajos **no es dominio**: no existiría si la novela se escribiera a mano, y
por eso vive en `commons/trabajos/` y su vocabulario se declara aquí y no en
`docs/definitions.md`. Sigue las mismas reglas de nombres —ASCII, `snake_case`— porque es
el mismo código leyendo el mismo tipo de valor, y dos convenciones para lo mismo es como
`juez LLM` acabó divergiendo de `juez_llm`.

| Estado | Qué significa |
| --- | --- |
| `en_cola` | Encolado y sin tomar |
| `esperando_presupuesto` | Tomado, pero no hay techo de contexto disponible (`P-3`) |
| `en_curso` | Con presupuesto reservado y llamada en vuelo |
| `terminado` | Acabó y dejó su resultado |
| `fallido` | Acabó mal, y **se sabe cómo**: fallo de contrato, o tope de reintentos agotado |
| `abandonado` | Un worker lo tomó y no se supo más de él. **No se sabe si llegó a pasar** |
| `detenido_por_presupuesto` | No arrancó porque el tope global de llamadas estaba alcanzado. **No falló nada** |

> **Segunda de las dos salidas por las que algo sin verificar podría llegar al canon.** La
> otra es la rendición de escena, en § "La máquina de estados y quién dispara cada
> transición". Aquí se mantiene cerrada porque `detenido_por_presupuesto` **no publica
> nada**: el trabajo no arrancó, no falló nada, y lo hecho hasta ahí se queda como está.
>
> **La tentación concreta que hay que resistir es "ya que paramos, entreguemos lo que
> haya".** Suena a cortesía y es la brecha: entregar media obra la convierte en una obra
> entregada a la que le faltan escenas, y nadie distingue después una obra corta de una
> obra truncada. El harness de la rama `main` sí cae en ella —`EJECUCION.md` regla 6
> ensambla lo que haya cuando salta el freno—, y combinada con su regla 1, que rinde
> capítulos sin condición, publica una novela que no pasó las puertas. **Las dos reglas
> están escritas en sitios distintos de aquel documento y no se referencian**, que es
> exactamente por lo que nadie las vio juntas: `CE-1` y `CE-2` de `specs/tla/README.md`
> las encontraron al formalizarlas.

**`fallido` y `abandonado` no son el mismo hecho**, y por eso son dos estados y no un
estado con un campo. Uno significa que sabemos qué pasó; el otro, que no sabemos si llegó
a pasar. La consecuencia práctica está en el tope: un `abandonado` no cuenta contra él,
porque no es un intento que falló sino uno cuyo resultado se desconoce. Con un campo en
lugar de un estado, una interfaz que solo mire el estado los confunde y alguien lo relanza
a mano creyendo que falló, que es pagar dos veces por otra puerta.

| Transición | Quién la dispara | Condición |
| --- | --- | --- |
| `[*]` → `en_cola` | Cliente de la API | Se encola el trabajo |
| `en_cola` → `en_curso` | Worker | Lo toma y hay techo disponible |
| `en_cola` → `esperando_presupuesto` | Worker | Lo toma y **no** hay techo (`P-3`) |
| `esperando_presupuesto` → `en_curso` | Worker | Se libera techo |
| `en_curso` → `terminado` | Worker | La llamada devuelve algo válido |
| `en_curso` → `en_cola` | Worker | Fallo **de transporte** y tope no agotado: reintenta desde el ensamblado |
| `en_curso` → `fallido` | Worker | Fallo **de contrato**, o tope agotado |
| `en_cola` → `detenido_por_presupuesto` | Worker | El tope global de llamadas está alcanzado. No llega a arrancar |
| `en_curso` → `abandonado` | *(sin decidir: ver Decisiones abiertas)* | Se excedió el margen desde que se tomó |
| `abandonado` → `en_cola` | Persona | Relanzamiento manual, viendo qué pasó |

Se vuelve a `en_cola` y no a `en_curso` al reintentar porque se reintenta **el trabajo
entero desde el ensamblado del contexto**: entre un intento y el siguiente el estado del
mundo pudo cambiar.

#### Reanudar no duplica ni pierde porque el estado se re-deriva, no se recuerda

Esta es la propiedad que hace segura la reanudación, y hasta ahora solo estaba escrita en
un docstring del código: **al volver de una caída, lo que toca hacer se deduce mirando qué
hay guardado, nunca un cursor que alguien apuntó antes de caerse.** Se pregunta qué escenas
están `consolidada` y qué borradores existen, y de ahí sale la siguiente; no se lee un
«iba por la escena 4».

La diferencia no es de estilo. Un cursor y el disco pueden desincronizarse en la ventana
entre escribir el artefacto y actualizar el cursor, y esa ventana existe siempre: si la
caída cae dentro, el cursor apunta antes de lo hecho —y se reescribe algo ya hecho, que es
`F-38`— o después —y se salta algo sin hacer, que deja un hueco permanente en la obra—. Un
conjunto reconstruido del estado no tiene esa ventana, porque no hay nada que actualizar.

Por eso las dos mitades de la garantía se sostienen solas: **no duplica** porque lo ya
cerrado se reconoce como cerrado mirándolo, y **no pierde** porque lo que no dejó rastro
sigue pendiente por definición. Lo comprueba `VER-28`, y la especificación TLA+ de
`specs/tla/` modela las dos reanudaciones —la del disco y la del cursor— justamente para
poder romper la segunda: con cursor, TLC encuentra una ejecución que se queda parada para
siempre (`CE-4` de `specs/tla/README.md`).

**Quien reimplemente esto no puede sustituirlo por un contador «por dónde iba» aunque
parezca equivalente y más rápido.** No lo es: es el mecanismo, no una optimización de él.

### La traza de una llamada al modelo

`T-1` y `T-2` de `SPEC-01` piden traza de cada llamada, incluidas las que fallan. Qué
registra:

- El agente, la escena y el trabajo.
- El **`prompt_hash`**. Vive también aquí y no solo en `Borrador`, porque una llamada
  fallida no produce ningún `Borrador` y es justo la que hay que diagnosticar.
- **Los identificadores que entraron en el contexto**, no su texto: qué fichas con su
  `version_en_t`, qué setups, qué resúmenes y qué niveles. Guardar el contexto entero
  sería duplicar hasta 80.000 tokens que se reconstruyen desde el estado; guardar los ids
  cuesta nada y es lo que hace la reconstrucción **posible**, porque el índice vectorial
  crece al consolidar y los empates de una consulta KNN no tienen orden definido: sin los
  ids no se sabe cuáles entraron, aunque su contenido siga ahí.
- **Los recortes que aplicó el ensamblador**, distinguiendo **reducciones** de
  **eliminaciones**, que desde `SPEC-12` no son lo mismo. Van aquí y no en un registro
  aparte porque la traza ya guarda **qué entró** en el contexto, y los recortes son la otra
  cara del mismo dato: separarlos obligaría a reconciliar dos fuentes de lo mismo.
  **La serie por obra es lo que importa, no el recorte suelto.** Si en la escena 40 hay
  recortes que no había en la 3, la ventana crece con N y la compactación no funciona: es la
  señal de alarma más importante que el sistema puede dar, y es lo único que dirá si el
  orden de `SPEC-01` §2.4 era el bueno.
- **Qué modelo se usó**, que es lo que hace comprobable la regla de abajo.
- Los tokens, en los dos campos de abajo.
- El resultado. Si fue un fallo de contrato, **la salida entera**: es pequeña, no se
  reconstruye, y es lo único que permite diagnosticar un delta fuera de esquema.

**El `prompt_hash` detecta, no reconstruye.** Sirve para saber si una reconstrucción es
fiel, no para recuperar lo que se mandó. Por eso no sustituye a los identificadores.

#### Por qué la traza lleva los tokens en dos campos

`VER-41` reconcilia lo que registra la traza contra lo que declara el modelo, y es **la
segunda fuente independiente que exige la Regla 3** de `docs/verification.md`. Si los dos
números salen del mismo sitio, `VER-41` compara un número consigo mismo: pasa siempre y es
un eco. `PC-8` dejaría de ser *"los dos podrían equivocarse igual"* y pasaría a ser *"no
hay segunda fuente"*, que es peor y que además nadie vería, porque el validador estaría en
verde. Y de `VER-41` depende `VER-34`.

| Campo | De dónde sale | Quién lo escribe |
| --- | --- | --- |
| `tokens_estimados` | El contador propio, **antes** de la llamada, el que reserva presupuesto por `P-2` | `commons/modelo/`, control de presupuesto |
| `tokens_declarados` | El `usage` de la respuesta del proveedor, **copiado literal** | El límite de transporte, al deserializar |

Tres reglas que hacen la independencia estructural en vez de una buena intención:

1. **`tokens_declarados` no se calcula nunca.** Se copia. Si no viene, queda **ausente**,
   no en cero: un cero se lee como un dato y un hueco no.
2. **El código que calcula `tokens_estimados` no escribe `tokens_declarados`.** Es la
   condición que impide el eco, y es comprobable de forma estática.
3. `VER-41` compara los dos campos y los cita por nombre, para que en su propia fila se vea
   que son dos y no uno.

### Cuando algo falla

Hasta aquí el camino feliz. Esto es lo que pasa cuando no lo es, y es tan arquitectura como
lo anterior: `A-05` eligió una tabla de trabajos en SQLite frente a `BackgroundTasks`
porque *"un reinicio pierde el trabajo en silencio"*, y esa decisión no vale nada si después
no se dice qué pasa con el trabajo que el reinicio interrumpió.

**El fallo vive en el trabajo, no en la escena.** Si la llamada al modelo falla, la escena
se queda en `planificada` y es el trabajo el que pasa a un estado de fallo.
`estado_de_escena` no gana ningún valor nuevo y la tabla de transiciones de arriba no gana
ninguna fila: un fallo no es una transición del dominio, es un intento que no llegó a
producir nada. Por eso **la tabla de trabajos no es dominio** y vive en
`commons/trabajos/`: no existiría si la novela se escribiera a mano.

La contrapartida hay que decirla, porque `RF-23` de `SPEC-01` promete que una escena se
muestra siempre con su estado: **el frontend saca el motivo del fallo del trabajo, no de la
escena.** Una escena en `planificada` con tres trabajos fallidos detrás se pinta como
`planificada`, y lo que explica por qué no avanza está en el trabajo. Si la interfaz no lo
enseña junto a la escena, el usuario ve una escena quieta sin motivo, que es el mismo fallo
silencioso que las puertas evitan.

#### Qué se reintenta y qué no

**Solo los fallos de transporte, y los reintenta el worker.** Un timeout, un corte de
conexión o un límite de tasa son sucesos que se resuelven repitiendo. Un delta fuera de
esquema, una respuesta sin texto o un valor fuera de una enumeración no: repetirlos repite
el error y gasta presupuesto en volver a fallar igual. Esos se marcan fallidos y los ve una
persona.

Se reintenta **el trabajo entero, desde el ensamblado del contexto**, no solo la llamada.
Entre un intento y el siguiente el estado del mundo pudo cambiar, y reutilizar el contexto
viejo es generar contra un mundo que ya no existe.

**El tope de reintentos es provisional y se declara como tal.** Su número no está medido
—`O-3` de `SPEC-01` lo hace depender de observar la tasa real de fallos transitorios, y no
hay sistema que observar— así que el valor se fija en el plan de implementación y lleva su
marca de caducidad. Lo que sí está decidido aquí es que el tope **existe** y que es
provisional declarado: un número sin medir que no se declara es un número inventado con
aspecto de medido. **Caduca con:** `backend/app/features/orquestacion/`, que es donde se observará la tasa real de fallos transitorios que `O-3` espera.

#### El trabajo que nadie terminó

Un trabajo que un worker tomó y no terminó solo se distingue de uno en curso **por el
tiempo**, así que la tabla registra cuándo se tomó y a partir de cierto margen se considera
abandonado. Ese margen es un número sin medir, como el tope, y se fija igual.

**El worker comprueba su propio estado antes de escribir.** Si al volver se encuentra
`abandonado`, **no escribe su resultado y no se relanza**: deja constancia de que volvió, en
la traza, y lo que traía se descarta. Es lo que convierte el margen de abandono en un
parámetro de **latencia** y no de **corrección**: si se elige corto, cuesta repetir trabajo;
si no existiera esta comprobación, un margen mal elegido corrompería el estado escribiendo
el resultado de un trabajo que alguien ya dio por perdido. **Ningún número sin medir debería
poder corromper el estado.**

**Un trabajo abandonado no se reintenta solo.** Pudo haber llamado al
modelo y haber cobrado antes de morir, y relanzarlo a ciegas paga dos veces sin saberlo.
Lo relanza una persona, viendo qué pasó. Por eso tampoco cuenta contra el tope de
reintentos: no es un intento que falló, es un intento cuyo resultado no se conoce.

#### El delta se aplica entero o no se aplica

**La aplicación del delta al estado del mundo es atómica.** Es arquitectura y no detalle de
implementación, por esto: `INV-05` exige que el delta esté aplicado antes de generar la
escena siguiente, y un delta a medias es un estado que la invariante **no sabe
clasificar** —lo dará por aplicado o por no aplicado según qué parte se mire—. La puerta
que corta la propagación del error dejaría de cortarla justo en el caso en que más falta
hace.

#### El tope global de llamadas

El techo de 100.000 tokens acota lo **concurrente** y el tope de reintentos de `SPEC-07`
acota los fallos **de transporte**. Ninguno acota **cuántas veces** se llama al modelo, y
desde `SPEC-10` eso hace falta: una invariante `bloqueante` **no admite rendición**, así que
una escena que insiste puede reintentarse sin final hasta que llegue una persona.

**Hay dos topes, y hacen falta los dos.** Uno por escena, que acota a la que insiste; otro
por obra, que acota el agregado. Con uno solo, el otro caso pasa entero.

**Cuentan todas las llamadas al modelo, no solo las del Escritor.** Si los verificadores
gastan más que el Escritor, **eso por sí solo no dice nada del coste** —se midió: el
Resumidor gastó más tokens que el Juez y costó menos de la mitad, porque el precio del
modelo pesa más que el volumen—. El contador cuenta **delegaciones y tokens**, que son las
dos cosas que acota; el **coste** se lee del `total_cost_usd` que devuelve cada delegación,
y no se deduce de ninguna de las otras dos. Contando
solo al Escritor eso no se ve nunca.

El contador se comprueba **antes** de cada llamada. Si el tope se ha alcanzado, el trabajo
no arranca y pasa a **`detenido_por_presupuesto`**, que es un estado más de los de
`commons/trabajos/` y **no es `fallido`**: no falló nada, se agotó un presupuesto. La parada
es ordenada —se escribe el estado y se deja constancia— y **no se pierde lo hecho**.

Los dos números son provisionales y se fijan en el plan, como el tope de reintentos.
**Caduca con:** `backend/app/features/orquestacion/`.

#### El interbloqueo del presupuesto ~~(retirado)~~

**`SPEC-14` C-1 se llevó esta sección con su causa.** Sin reserva no hay techo retenido, así que el interbloqueo que describe **dejó de ser posible**. Se conserva tachada porque el razonamiento sigue enseñando algo: era un fallo que no salía de ningún error, sino de cruzar dos decisiones correctas por separado.

**Un solo trabajo abandonado del Escritor deja el sistema entero parado hasta que expire el
margen**, y no es consecuencia del número elegido: sale de cruzar dos decisiones que por
separado son correctas. `P-2` de `SPEC-01` dice que una llamada reserva su presupuesto antes
de salir y lo libera **al volver**; un worker que muere no vuelve nunca, así que no libera
nada. Y `P-5` dice que una llamada del Escritor a tamaño completo agota el techo global y es
**exclusiva**. Juntas: el techo se queda retenido por un trabajo que ya no existe.

El margen de abandono **acota** ese bloqueo, no lo arregla: es el tiempo de recuperación del
interbloqueo, no su prevención. Quien suba el margen está alargando esa parada, y conviene
que lo sepa antes de subirlo. Está catalogado como `MF-25` en `docs/verification.md`.

Es además la única categoría de fallo de la que no se sale reintentando. Los otros tres
detienen el trabajo y dejan el estado intacto; este lo corrompe, y a partir de ahí todo lo
que se genere encima hereda la corrupción sin que nada avise.

### El harness — validadores que no son tests de una feature

No todo validador de `docs/verification.md` es un test de código de producción. El criterio
que decide dónde vive cada uno:

- **Va al backend** si su sujeto es **código de producción**: compara, ejecuta o muta algo
  que vive en `backend/app/`. Entonces vive junto a lo que prueba, en el `tests/` de su
  feature o de su módulo de `commons/`.
- **Va a `harness/`** si su sujeto son **los documentos** o **el comportamiento de un
  modelo**. No hay código de producción al lado del que ponerlo.

`harness/` no es el cajón de lo que no sabemos dónde poner: es el sitio de lo que no tiene
feature.

```
harness/
  documentos/            # validadores cuyo sujeto son los documentos del proyecto
  evals/                 # evals contra el modelo: corpus, medicion y umbral
  adversarial/           # corpus adversario y su ejecucion
```

Tres carpetas y no más. Una cuarta necesita spec, que es justo lo que faltó para que
`harness/esquema/` apareciera sin que nadie lo decidiera. `VER-45` resuelve las rutas de
`harness/` contra este árbol, igual que las del backend contra el suyo.

**Un eval y el red-teaming no son lo mismo**, y por eso son dos carpetas: un eval mide
concordancia contra un criterio, y el red-teaming busca una violación bajo presión
adversaria. Distinta pregunta, distinto corpus, distinto criterio de salida.

**Qué hay hoy en cada una** (`SPEC-31`, `PLAN-31` E1–E14):

- `evals/`: los cinco briefs de `RF-01` y `RF-10` —ficha o guion de entrevista, nunca los
  dos—, `resultados.md`, la tabla por brief que **genera** `backend/evaluar.py` y no se
  edita a mano, y `medidas.md`. El formato lo valida `features/evaluacion/briefs.py`.
- `adversarial/`: `casos.json` (`RT-01`…`RT-06`, cada uno con su detector o `ninguno`) y las
  dos fichas disjuntas del caso de exfiltración. Lo que no detectó nadie está también.
- `documentos/`: sigue sin existir.

**Lo que se ejecuta contra el modelo lo lanza `backend/evaluar.py`, y gasta.** La pieza
que sí es código de producción vive en el backend: `features/evaluacion/` —el formato de
los briefs, el libro `gasto_de_evaluacion`, la tabla y el rastro— y
`orquestacion/evaluacion.py`, que reúne lo que dice cada validador de una obra porque
cruza features (`A-02`). La regla de lectura de la tabla —**sin constancia de ejecución
no hay «pasó»**— está en ese módulo, con la constancia que declara cada validador.

**Una base por ejecución, un libro para todas.** El techo de 150 USD se acumula en el
libro (`--libro`), y cada novela se escribe en su propia base (`--base`), porque la segunda
novela de una base recibe el mundo de la primera (`F-100`).

### El ensamblador del manuscrito no corrige nada

Lo que se entrega es **exactamente** lo que se auditó. El ensamblador del manuscrito no
retoca una transición floja ni unifica un nombre que baila, por muy tentador que sea con la
obra entera delante.

**El motivo es de trazabilidad, no de estilo.** Si retocara el texto, el informe dejaría de
describir el manuscrito: diría que la escena 7 se aceptó con tres hallazgos abiertos, y la
escena 7 del manuscrito ya no sería esa. La trazabilidad entre lo auditado y lo entregado es
lo único que hace útil al informe.

**Desde `SPEC-10` hace más falta que antes.** Una escena en `aceptada_por_rendicion` llega
al manuscrito **con sus hallazgos abiertos**: si algo la retoca por el camino, esos hallazgos
describen un texto que ya no existe. Lo comprueba `VER-60`.

**El PDF hereda la misma regla** (`SPEC-27` `RF-02`, `PLAN-27`). `exportar.capitulos_de` da el
texto elegido de cada escena tal cual, sin recortar los bordes (`F-63`); `libro.componer` lo
convierte en portada, capítulos y fichas **sin estados ni hallazgos** (`RF-06`); y `pdf.a_pdf`
lo escribe con una fuente Unicode del repositorio para no sustituir rayas ni comillas. Solo se
exporta lo que la puerta publicó (`service.exportar_pdf`, `RF-01`). `manuscrito/` lee las tablas
por SQL y no importa ninguna feature.

## Pruebas

El plan completo —qué afirmación se prueba con qué metodología, con qué criterio de salida
y dónde vive cada prueba— está en `docs/verification.md`. Aquí solo quedan las tres reglas
que condicionan cómo se escribe el código.

- Cada invariante tiene al menos un caso negativo: un fragmento que la viole a propósito.
  Una invariante que nunca ha fallado en las pruebas no está verificada, solo declarada.
- El caso negativo vive **en la feature que ejecuta esa invariante**, en su `tests/`, no en
  un directorio de tests aparte. Este documento llegó a decir las dos cosas: que vivían en
  `harness/` y que no vivían en un directorio aparte. Manda esta segunda, que es la que
  coinciden en decir la tabla de ficheros de feature de más arriba y la skill
  `harness-invariantes`.
- Un doble de prueba tiene la misma forma que lo real. Si el modelo devuelve texto y delta
  en la misma respuesta, el doble también.

## Decisiones tomadas

Fijadas en la sesión del 2026-09-21. Se trasladarán a `docs/decisions/` cuando ese
directorio exista.

| # | Decisión | Alternativa descartada y por qué |
| --- | --- | --- |
| A-01 | Una carpeta por feature, con `commons` para lo compartido | Por plano del dominio: un caso de uso como "generar escena" cruza los cinco planos y quedaría repartido |
| A-02 | Una feature es un caso de uso del pipeline | Por agregado: multiplica carpetas y deja la orquestación sin casa |
| A-03 | Un agente = una llamada al modelo con contexto propio | Agrupar por fase: más barato, pero un fallo no se atribuye a un agente concreto |
| A-04 | El frontend cierra las puertas, no solo observa | Solo lectura: las puertas se vuelven teatro si nadie las cierra |
| A-05 | Cola de trabajos en una tabla de la misma SQLite | `BackgroundTasks` en memoria: un reinicio pierde el trabajo en silencio |
| A-06 | El Juez usa modelo distinto o sesión limpia | Misma llamada que el Escritor: sesgo de autoevaluación |
| A-07 | `CLAUDE.md` manda; este documento desarrolla y no duplica sus tablas | Duplicar: dos copias que divergen |
| A-08 | Los originales de dominio no se modifican todavía | Cortar ya: se prefiere un cambio aparte y revisable |
| A-09 | El frontend se organiza con Feature-Sliced Design v2.1 | Estructura libre: sin criterio, las carpetas del frontend derivan hacia un `components/` que lo absorbe todo |

## Decisiones abiertas

Sin cerrar. Afectan al código, así que conviene fijarlas antes de escribirlo.

**Dos etiquetas, y la diferencia importa.** Las decisiones marcadas **«se contesta sola»**
esperan un dato y el dato las resuelve. Las marcadas **«deja de ser ciega»** esperan un dato
que las informa y **no las decide**: seguirán necesitando que alguien elija, solo que ya no
a oscuras. Estaban todas escritas en el mismo tono, y eso prometía que ejecutar las
resolvería todas — el día que llegue la primera traza, alguien miraría las segundas
esperando una respuesta que el dato no da.

- [ ] **Granularidad de generación.** ¿La unidad que se le pide al modelo es la escena **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
  completa o el beat? Cambia el tamaño del delta y el coste de revisión.
- [ ] **Persistencia del estado.** ¿Los deltas son la fuente de verdad, o se materializa **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
  el `EstadoDelMundo` en cada `t`? Lo primero es más fiel, lo segundo más barato de consultar.
- [x] ~~**Escala de la curva de dread.**~~ **Obsoleta**: `SPEC-26` v3 retiró la curva de dread. ¿Presión absoluta 0–100 anotada por un juez, o **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide.
  relativa entre escenas contiguas? La relativa es más estable entre modelos.
- [ ] **Umbrales de `INV-15` e `INV-16`.** Sin números concretos el harness las salta en **Se contesta sola** con una traza real.
  silencio. Los números salen de medir, no de estimar. Es la misma decisión "Umbrales" de
  `docs/definitions.md` y las filas `VER-32` y `VER-33` de `docs/verification.md`: las tres se
  cierran a la vez o ninguna.
- [ ] **Reparto de tokens por agente.** Pendiente de medida real (`VER-34`). **Se contesta sola** con una traza real.
- [x] ~~**Coste por escena con la decisión `A-03`**~~ — **medido el 2026-09-23 en `PLAN-01` E5, y el número está aquí porque conviene verlo antes de decidir nada.**

  **0,2508 $** por una escena de 325 palabras, en 22 segundos, con **un solo agente**. El
  desglose dice dónde se va: 1.188 tokens de salida —la escena— contra **9.476 de creación
  de caché**. **Lo que cuesta es montar el contexto, no escribir.**

  Y `A-03` dice *un agente = una llamada con contexto propio*, así que **cada agente paga su
  propia creación de caché**. La proyección a una obra —10 agentes × 60 escenas = 600
  delegaciones, sin reintentos ni rendición— usando una tarifa mezclada de 0,0235 $/1k
  tokens derivada de esa única medida:

  | Contexto por delegación | Por delegación | Obra completa |
  | --- | --- | --- |
  | El medido (138 tokens) | 0,25 $ | **150 $** |
  | 50.000 tokens | 1,20 $ | **722 $** |
  | El techo de 100.000 | 2,38 $ | **1.428 $** |

  **Lo que hace esto provisional, y hay que decirlo alto:** el contexto de esa escena fueron
  **138 tokens**, así que el coste lo domina un arranque que con estado real será otra cosa,
  y **no sabemos en qué dirección**. Puede subir —más contexto por delegación— o bajar
  mucho, porque en la medida `cache_read` fue **cero**: era la primera llamada y nada se
  amortizó. Si el caché se reutiliza entre delegaciones, la columna de la derecha se cae.
  **Una sola medida no distingue las dos cosas.**

  **Segunda medida, 2026-09-23, ciclo completo con tres agentes y caché ya caliente.** La
  incógnita era si el caché amortiza, porque en la primera `cache_read` fue cero. **Amortiza
  en parte**: el Escritor leyó 1.553 tokens de caché y el Juez 1.572, pero la creación sigue
  dominando —8.434 en el Escritor—.

  | Agente | Modelo | Tokens | Coste | % del ciclo |
  | --- | --- | --- | --- | --- |
  | Escritor | `fable` | 2.511 | **0,2968 $** | 75 % |
  | Juez | `opus` | 1.567 | 0,0689 | 17 % |
  | Resumidor | `haiku` | 1.872 | 0,0294 | 7 % |
  | **Escena completa** | | 5.950 | **0,3951 $** | |

  **Dos cosas que el número enseña y que no se deducían.** La primera: **los tokens no
  predicen el coste.** El Resumidor gastó más tokens que el Juez y costó menos de la mitad,
  porque el precio del modelo pesa más que el volumen. La segunda: **aislar al Juez lo hizo
  cuatro veces más barato.** Su directorio no tiene `CLAUDE.md`, así que crea 2.562 tokens de
  caché en vez de 8.434. El aislamiento se decidió por corrección —`SPEC-11` C-4— y resultó
  ser también la partida más rentable del ciclo.

  **La proyección se estrecha un orden de magnitud:**

  | Escenario | Obra de 60 escenas |
  | --- | --- |
  | Con este contexto (9.237 tokens) | **24 $** |
  | Con el contexto al techo de 100.000 | **148 $** |

  El rango anterior era de 150 a 1.428 $ y salía de una sola medida en frío con un contexto
  de 138 tokens. **`A-03` sigue sin revisarse**, pero ya no por falta de datos: por falta de
  una obra larga que diga por dónde crece el contexto de verdad.
- [ ] **Suficiencia del reparto por niveles de `CLAUDE.md`.** Nunca se ha ensamblado el **Se contesta sola** con una traza real.
  contexto de una escena real para ver si los niveles caben (`VER-37`).
- [ ] **Desempate juez contra regla.** Con `INV-03` ya de tipo `regla`, la pregunta deja **Deja de ser ciega, pero no se contesta sola**: el dato informa, no decide. **La traza dirá cuántas veces discrepan y en qué dirección, no quién gana.**
  de ser teórica: hay dos resultados que comparar en cada escena. Falta decidir qué gana
  cuando la regla no ve nada y el Juez marca. Lo mismo para `INV-11` e `INV-14`.
- [ ] **Qué necesita una persona para desatascar una `bloqueante` rápido.** La decisión de
  **no rendirse** ante una `bloqueante` no cambia con la escala, y con sesenta escenas es
  aún más necesaria: rendirse ante `INV-03` mete un hecho falso en el registro de
  conocimiento y todo lo que venga después se genera encima. **Lo que sí cambia es el coste
  de desatascar.** Con una escena, parar y mirar es trivial; con sesenta, si cada bloqueo
  exige entender el estado entero, el sistema es **inusable aunque sea correcto**. Hay que
  fijar tres cosas: **qué dice el hallazgo** para que se entienda sin reconstruir la obra,
  **qué se puede editar** sin romper lo ya consolidado, y **si se puede reintentar la escena
  con una instrucción añadida** en vez de replanificar el capítulo.
- [ ] **Quién detecta un trabajo abandonado.** `SPEC-07` decidió qué se hace con él —se
  marca `abandonado`, no cuenta contra el tope y lo relanza una persona— pero no quién lo
  detecta: el worker al arrancar, un barrido aparte, o una persona. La transición
  `en_curso` → `abandonado` tiene la celda vacía a propósito.
- [ ] **El nivel `Resúmenes` de una traza no es reconstruible todavía.** `Ficha` tiene
  `version_en_t` y `Resumen` no, así que una condensación de capítulo consumida en la
  escena 5 no se distingue de la de la escena 40. Lo cierra `SPEC-09`.
- [ ] **Qué valida una persona y cuándo.** Con `A-04` el frontend lo permite; falta decidir
  en qué puertas es obligatorio.
- [ ] **Limpieza de los documentos de dominio.** Mover lo listado arriba y arreglar el
  enlace roto de `docs/domain-knowledge.md`.

## Los hooks de Claude Code (`SPEC-26` `RF-17`..`RF-19`)

Dos scripts en `backend/hooks/`, declarados en `.claude/settings.json`:

| Hook | Evento | Qué hace | A quién |
| --- | --- | --- | --- |
| `validar_capitulo.py` | `Stop` | Comprueba longitud, vetadas y nombres del último mensaje; si falla, sale con 2 y Claude Code se lo devuelve **en la misma sesión**, una sola vez (`stop_hook_active`) | Solo al Escritor |
| `policy.py` | `PreToolUse` | Allowlist por agente (`SPEC-28` `RF-07`): el Escritor y el Editor pueden llamar a `mcp__story_bible__hechos`, `ficha` y `cronologia`; cualquier otra herramienta se niega y queda en el audit log (`herramienta_denegada`) | A cualquier agente del pipeline; el Editor y el Juez lo reciben en su directorio aislado con ruta absoluta |

**Solo actúan sobre el pipeline**: `SesionDelegada` lanza cada delegación con `HARNESS_AGENTE` y, si las hay, `HARNESS_REGLAS`; sin esa variable los dos scripts salen con 0. Una sesión interactiva en el mismo proyecto no se toca. **Las puertas del código siguen mandando**: el hook es una primera línea más barata que una delegación nueva, no la única. Desde `SPEC-28` el de policy sí se dispara: el Escritor y el Editor tienen tools.

### Las tools de lectura de la story bible (`SPEC-28`)

Un servidor MCP propio por stdio (`backend/herramientas/story_bible.py`, sobre
`commons/modelo/mcp.py`) ofrece tres tools de solo lectura —`hechos`, `ficha` y `cronologia`—
con esquema de entrada y de salida (`commons/dominio/story_bible.py`). Las atiende
`orquestacion/story_bible.py`: valida, lee **solo la obra de la delegación** (la fija el harness;
no es argumento), valida la salida, estima los tokens de lo devuelto y deja una fila en
`llamada_a_herramienta`, sin argumentos ni resultado. Ninguna devuelve el texto de una escena.

Cuatro barreras, porque ninguna está probada todavía contra Claude Code real: toda delegación
del pipeline lleva `--tools ""` y `--strict-mcp-config` —**toda**, tenga o no tools, desde
`PLAN-22` DP-6: sin él, una delegación sin tools cargaría el browser MCP del `.mcp.json` de la
raíz—; el Escritor y el Editor, además, `--mcp-config` (en un fichero) y `--allowedTools` con sus
tres tools; el hook de policy es una allowlist; y el frontmatter las declara.

**El `.mcp.json` de la raíz declara un solo servidor, Playwright MCP**, fijado a una versión, y
es para la sesión de Claude Code que inspecciona la lectura web (`PLAN-22` E13), no para los
agentes: ninguna delegación lo carga y el hook niega sus tools a todo agente del pipeline.

**Punto ciego declarado**: lo que un agente trae con una tool entra en su contexto sin pasar por
el presupuesto de `CLAUDE.md`, que es sobre lo que mandamos. Se mide y se registra junto a la
traza; no se presupuesta, porque el harness no administra el contexto de la sesión delegada.
