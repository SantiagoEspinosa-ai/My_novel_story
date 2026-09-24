# Diagramas

Los cuatro que pide el enunciado. Los del modelo de dominio —árbol por planos, relaciones,
ciclo de vida de la escena— están en `docs/domain-knowledge.md` y no se repiten aquí.

## Arquitectura del harness

Un capítulo es una escena (`SPEC-26` `RF-01`). Cada caja con borde grueso es un agente
delegado en su propia sesión de Claude Code (`A-03`, `SPEC-14`).

```mermaid
flowchart TD
  C([Comprador]) --> E[[Entrevistador]]
  E -->|ficha validada con schema| P[[Planificador]]
  P --> CP{Cobertura del plan<br/>en código}
  CP -->|huecos| P
  CP --> RP[[Revisor del plan]]
  RP -->|objeciones, hasta 3| P
  RP -->|plan aprobado| M[Montar la obra<br/>desde el plan]
  M --> CTX[Ensamblar contexto<br/>por niveles, 100.000 tokens]
  CTX --> W[[Escritor]]
  W -->|hook Stop| HV{validar_capitulo.py}
  HV -->|falla: misma sesión| W
  HV --> R{Reglas en código<br/>INV-21, INV-22, INV-23, INV-17}
  R -->|reescribir con tope| W
  R --> ED[[Editor, aislado]]
  ED -->|nota < umbral, hasta 3| W
  ED --> CO[Consolidar: aplicar delta,<br/>resumir, usos y cronología]
  CO --> PC{Puerta de capítulo<br/>INV-08}
  PC -->|siguiente capítulo| CTX
  PC -->|diez capítulos| OB{Nivel obra<br/>INV-24, INV-25, INV-27}
  OB --> PP{Puerta de publicación<br/>Lean · SPEC-30}
  PP -->|falla: vía Editor, tope 2| W
  PP --> V[(Versión publicada)]
  DB[(SQLite + sqlite-vec<br/>story bible)] -.-> CTX
  CO -.-> DB
  classDef pendiente stroke-dasharray: 5 5
  class PP,V pendiente
```

Lo punteado está aprobado y sin construir: la puerta de publicación (`SPEC-30`) y las
versiones (`SPEC-23`, `EX-14`). Tampoco aparecen todavía las tools (`SPEC-28`) ni Langfuse
(`SPEC-29`).

## Máquina de estados de TLA+

Las acciones de `specs/tla/HarnessNovela.tla`. **Modela el flujo de la rama `main`, no el de
`backend/`**; rehacerlo contra `backend/` está decidido y pendiente (`EX-07`), y la escalera
de modelos de `Reintentar` y `AgotarEscalera` desaparece al hacerlo.

```mermaid
stateDiagram-v2
  [*] --> Configurado: Configurar
  Configurado --> Planificado: Planificar
  Planificado --> Validando: Escribir
  Validando --> Validando: Reintentar
  Validando --> Planificado: ValidarPasa
  Validando --> Planificado: AgotarEscalera
  Planificado --> Publicada: Publicar
  Validando --> Caido: Caer
  Caido --> Planificado: Reanudar
  Planificado --> Detenido: AgotarTope
  Publicada --> Planificado: Regenerar
  Publicada --> [*]: Terminado
  Detenido --> [*]: Terminado
```

Los estados son una lectura para el diagrama; en la especificación el estado es el valor de
sus variables. Lo que TLC comprueba sobre 5 capítulos y 2 intentos: `NuncaPublicaSinValidar`,
`NuncaPierdeCapitulos`, `NoReescribeCerrados`, `NoSaltaCapitulos` y `ReintentosAcotados`
como invariantes, y `VersionesSoloCrecen` y `Terminacion` como propiedades temporales
(`specs/tla/HarnessNovela.cfg`).

## Esquema SQLite

Las tablas de la story bible y su contorno inmediato, con las columnas que se leen en los
`CREATE TABLE` del backend. Faltan las de infraestructura (`trabajo`, `procedencia`,
`esquema_version`, `vectores`).

```mermaid
erDiagram
  obra ||--o{ capitulo : tiene
  obra ||--o{ escena : tiene
  obra ||--o{ plan_de_obra : "versiones del plan"
  escena ||--o{ borrador : versiones
  escena ||--o{ delta_de_escena : "delta por versión"
  escena ||--o{ hallazgo : tiene
  obra ||--o{ hecho_canonico : declara
  hecho_canonico ||--o{ uso_de_hecho : "se usa en"
  escena ||--o{ uso_de_hecho : usa
  obra ||--o{ evento_cronologico : cronologia
  evento_cronologico ||--o{ participacion_en_evento : presentes
  entidad ||--o{ participacion_en_evento : participa
  entidad ||--o{ ficha : "versiones en t"
  escena ||--o{ resumen : resume
  obra ||--o{ palabra_vetada : "nivel novela"
  obra ||--o{ entrevista : "nace de"
  entrevista ||--o{ turno_de_entrevista : turnos

  obra { text id text titulo text premisa text genero text extension_objetivo }
  capitulo { text id text obra int orden text estado }
  escena { text id text obra text capitulo int orden text estado text borrador_aceptado text t_fabula int t_discurso }
  borrador { text escena int version text texto text modelo text prompt_hash }
  delta_de_escena { int orden text escena int version text contenido }
  hallazgo { text id text invariante text escena text severidad text estado }
  hecho_canonico { text id text obra text enunciado text durabilidad }
  uso_de_hecho { text hecho text escena text capitulo text tipo text origen }
  evento_cronologico { text id text obra text t_fabula text lugar text escena text capitulo }
  participacion_en_evento { text evento text personaje text presencia }
  entidad { text id text vital text lugar text fecha_de_nacimiento }
  ficha { text entidad text obra int t_discurso int version_en_t text resumen }
  resumen { text escena text obra int t_discurso text nivel text texto }
  palabra_vetada { text forma text nivel text franja text obra }
  plan_de_obra { text obra int version text plan int aprobado }
  entrevista { text id text obra text ficha int cerrada }
  turno_de_entrevista { text entrevista int orden text pregunta text respuesta }
```

Fuera del diagrama, junto a él: `traza_de_delegacion` (una fila por delegación, con los dos
campos de tokens), `lectura_de_contexto` (qué entró en cada contexto), `decision_de_politica`
(el audit log) y `edicion_manual`.

## Validadores y su punto de ejecución

| Validador | Tipo | Dónde se ejecuta | Si falla | Estado |
| --- | --- | --- | --- | --- |
| Schema de la ficha | Programático | Al cerrar la entrevista | No se entrega la ficha | Construido |
| Contradicciones de la entrevista | Programático | Durante la entrevista | Se pregunta al comprador | Construido |
| Cobertura del plan (`SPEC-26` `RF-06`) | Programático | Antes del Revisor del plan | El plan vuelve al Planificador | Construido |
| Revisor del plan | Semántico | Tras la cobertura | Objeciones, hasta 3 revisiones | Construido |
| `validar_capitulo.py` | Programático, hook `Stop` | Al terminar el Escritor, dentro de su sesión | Se le devuelve en la misma sesión | Construido; **no dejó constancia** en la ejecución real (`F-61`) |
| `policy.py` | Programático, hook `PreToolUse` | Antes de cada herramienta de un agente del pipeline | Se niega y va al audit log | Construido; allowlist por agente pendiente (`SPEC-28`) |
| `INV-21` palabras vetadas | Programático, `bloqueante` | Tras el Escritor, antes del Editor | Reescritura, tope 2; agotado, se para | Construido |
| `INV-22` nombres exactos | Programático, `bloqueante` | Tras el Escritor, antes del Editor | Reescritura, tope 2; agotado, se para | Construido |
| `INV-23` palabras clave de los imprescindibles | Programático, `mayor` | Tras el Escritor | Reescritura dentro de los intentos de calidad | Construido |
| `INV-17` longitud | Programático, `mayor` | Puerta de escena | Hallazgo | Construido |
| `INV-26` nota del Editor por criterio | Semántico, `mayor` | Rol editor, tras las reglas | Reescritura, hasta 3 | Construido |
| `INV-08` orden temporal | Programático, `mayor` | Puerta de capítulo | Hallazgo | Construido (`b2f097c`) |
| `INV-24` cada imprescindible en algún capítulo | Programático, `bloqueante` | Nivel obra | La novela no se da por terminada | Construido |
| `INV-25` prosa repetitiva | Programático, `menor` | Nivel obra | Hallazgo | Construido |
| `INV-27` juicio de obra del Editor | Semántico, `mayor` | Nivel obra | Bloquea la publicación (`SPEC-30` `RF-07`) | Construido el juicio; el bloqueo, pendiente |
| Lean `L-1`…`L-4` | Formal | Puerta de publicación | No se publica; vuelve al Editor, tope 2 | Funciona fuera del pipeline; **sin enchufar** (`SPEC-30`) |
| Validación visual con browser MCP | Programático | Tras publicar, sobre la lectura web | Vuelve al rol correspondiente | **No existe**: espera al frontend (`EX-04`) |
| Revisión humana | Semántico | Una novela completa, fuera del pipeline | Compara con el Editor | **Sin hacer** (`SPEC-31`) |

Ningún validador envía todavía su score a Langfuse (`SPEC-29` `RF-04`).
