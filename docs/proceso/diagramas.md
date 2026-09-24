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

**Construido no es ejercido.** La columna *Ejercido en real* dice si el validador ha corrido
alguna vez con datos de una ejecución real, y qué hizo; lo comprueba contra las bases
(`backend/regalo-prueba.db`, `backend/regalo-real.db`) y el registro de hooks la auditoría del
2026-09-24. Todos los que dicen *sin ejercer* existen y pasan sus pruebas con dobles, y **nunca
han visto un dato real**: un validador que no ha podido fallar no está verificado, solo
declarado.

| Validador | Tipo | Dónde se ejecuta | Si falla | Ejercido en real |
| --- | --- | --- | --- | --- |
| Schema de la ficha | Programático | Al cerrar la entrevista, y al arrancar `novela_regalo.py` | No se entrega la ficha | **En parte**: validó las dos fichas de las ejecuciones reales al arrancar. Al cerrar una entrevista, nunca: no hay ninguna entrevista real (`F-70`) |
| Contradicciones de la entrevista | Programático | Durante la entrevista | Se pregunta al comprador | **Sin ejercer** |
| Schema de la salida de cada rol | Programático | Al recibir cada salida | La ronda o el intento se repite | **Sí**: rechazó 4 planes reales, dos por base. El contrato del Escritor pasó 3 veces. Editor y Resumidor, sin ejercer |
| Cobertura del plan (`SPEC-26` `RF-06`) | Programático | Antes del Revisor del plan | El plan vuelve al Planificador | **Sí, sin haber fallado nunca**: los dos planes que llegaron al Revisor la pasaron |
| Revisor del plan | Semántico | Tras la cobertura | Objeciones, hasta 3 revisiones | **Sí**: aprobó un plan y devolvió otro con objeciones |
| `validar_capitulo.py` | Programático, hook `Stop` | Al terminar el Escritor, dentro de su sesión | Se le devuelve en la misma sesión | **Sin ejercer sobre un capítulo**: sus 4 ejecuciones reales fueron con el Planificador o el Revisor, en la rama que sale sin comprobar nada (`F-61`) |
| `policy.py` | Programático, hook `PreToolUse` | Antes de cada herramienta de un agente del pipeline | Se niega y va al audit log | **Sin ejercer**: ninguna ejecución registrada |
| `INV-21` palabras vetadas | Programático, `bloqueante` | Tras el Escritor, antes del Editor | Reescritura, tope 2; agotado, se para | **Sí, y solo en falso**: sus 46 coincidencias reales fueron «coño» normalizada en «con» (`F-59`). El arreglo está sin ejercer |
| `INV-22` nombres exactos | Programático, `bloqueante` | Tras el Escritor, antes del Editor | Reescritura, tope 2; agotado, se para | **Sí, con toda probabilidad en falso**: no deja rastro en el audit log (`F-73`), y con el código de hoy los tres borradores reales dan positivo por «Nada» y «Nadie» (`F-71`) |
| `INV-23` palabras clave de los imprescindibles | Programático, `mayor` | Tras el Escritor | Reescritura dentro de los intentos de calidad | **Sin ejercer**: los tres intentos reales se pararon antes |
| `INV-17` longitud | Programático, `mayor` | Puerta de escena | Hallazgo | **Sí**: un hallazgo real, 1.564 palabras |
| `INV-03` conocimiento | Programático, `bloqueante` | Puerta de escena | La escena se para | **Sí**: dos hallazgos en la primera ejecución real, por los imprescindibles (`F-60`, cerrado y sin ejercer desde el arreglo) |
| `INV-26` nota del Editor por criterio | Semántico, `mayor` | Rol editor, tras las reglas | Reescritura, hasta 3 | **Sin ejercer**: el Editor no se ha llamado nunca en la novela regalo |
| `INV-08` orden temporal | Programático, `mayor` | Puerta de capítulo | Hallazgo | **Sin ejercer**: ninguna escena consolidada |
| `INV-24` cada imprescindible en algún capítulo | Programático, `bloqueante` | Nivel obra | La novela no se da por terminada | **Sin ejercer** |
| `INV-25` prosa repetitiva | Programático, `menor` | Nivel obra | Hallazgo | **Sin ejercer** |
| `INV-27` juicio de obra del Editor | Semántico, `mayor` | Nivel obra, en la puerta | Bloquea la publicación (`SPEC-30` `RF-07`) | **Sin ejercer** |
| Lean `L-1`…`L-4` | Formal | Puerta de publicación | No se publica; vuelve al Editor, tope 2 | **Sin ejercer en una generación**: la puerta no se ha alcanzado nunca. Lean de verdad sí ha corrido desde el backend, sobre dos bases sembradas y sobre `regalo-prueba.db`, que dio `2` por cero eventos (`specs/lean/medidas.md`) |
| Validación visual con browser MCP | Programático | Sobre la lectura web | Vuelve al rol correspondiente | **No existe**: espera al frontend (`EX-04`) |
| Revisión humana | Semántico | Una novela completa, fuera del pipeline | Compara con el Editor | **No existe** (`SPEC-31`) |

El envío de los scores a Langfuse está construido (`SPEC-29`, `PLAN-29` E6) y **ningún score
ha llegado nunca a una instancia real**.
