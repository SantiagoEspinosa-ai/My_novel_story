# Ontología de novelas IA — Árbol y diagramas

2026-09-21 · @Santiago Espinosa Domínguez

El árbol de la ontología en diagramas Mermaid, partido en vistas de menos de quince nodos para que cada una se lea de un golpe. Las definiciones de cada clase están en `Docs/definitions.md`, que es la fuente: estos diagramas son una vista suya y, ante cualquier discrepancia, manda la definición.

## Árbol raíz

```mermaid
flowchart TD
  O["Ontología<br/>Novela IA"]
  O --> P1["Plano Obra<br/>anatomía del texto"]
  O --> P2["Plano Mundo<br/>canon y estado"]
  O --> P3["Plano Terror<br/>tensión y amenaza"]
  O --> P4["Plano Proceso<br/>producción y contexto"]
  O --> P5["Plano Calidad<br/>medición y puertas"]
```

Los cinco planos son independientes en su definición y se cruzan solo a través de las relaciones. Obra y Mundo son declarativos; Terror es una capa de control sobre ambos; Proceso y Calidad describen el sistema, no la ficción.

## Plano Obra

```mermaid
flowchart TD
  P1["Plano Obra"]
  P1 --> C["Contenedores"]
  P1 --> U["Unidad atómica"]
  P1 --> F["Clases de función"]
  C --> C1["Obra"]
  C --> C2["Parte"]
  C --> C3["Capitulo"]
  U --> U1["Escena"]
  U1 --> U2["Beat"]
  F --> F1["ArcoNarrativo"]
  F --> F2["POV"]
  F --> F3["MomentoNarrativo"]
  F --> F4["LineaArgumental"]
```

La Escena cuelga aparte a propósito: es la unidad que se genera, se verifica y se recupera, mientras que los contenedores solo la ordenan. Las clases de función no contienen texto, califican escenas.

## Plano Mundo

```mermaid
flowchart TD
  P2["Plano Mundo"]
  P2 --> E["Entidades"]
  P2 --> V["Verdad canónica"]
  P2 --> S["Estado"]
  E --> E1["Personaje"]
  E --> E2["Lugar"]
  E --> E3["Objeto"]
  E --> E4["Faccion"]
  V --> V1["HechoCanonico"]
  V --> V2["ReglaDelMundo"]
  V --> V3["EventoCronologico"]
  S --> S1["EstadoDelMundo"]
  S --> S2["RegistroDeConocimiento"]
```

La rama de estado es la que cambia con cada escena; entidades y verdad canónica son relativamente estables. El `RegistroDeConocimiento` está aquí y no en el plano Obra porque es un hecho del mundo —quién sabe qué— aunque su sujeto pueda ser el lector.

## Plano Terror

```mermaid
flowchart TD
  P3["Plano Terror"]
  P3 --> A["Amenaza"]
  P3 --> T["Gestión de tensión"]
  P3 --> D["Daño acumulado"]
  A --> A1["FuenteDelMiedo"]
  A --> A2["Tell"]
  A --> A3["Grado de explicación"]
  T --> T1["CurvaDeDread"]
  T --> T2["Valvula"]
  T --> T3["Presagio"]
  T --> T4["SetupYPago"]
  D --> D1["Deterioro"]
  D --> D2["PuntoDeNoRetorno"]
```

Las tres ramas responden a preguntas distintas: qué amenaza, cómo se dosifica y qué se va perdiendo. Un sistema que solo modela la primera produce monstruos, no miedo.

## Proceso y Calidad

```mermaid
flowchart LR
  P4["Plano Proceso"]
  P4 --> PL["Planificación"]
  P4 --> PR["Producción"]
  P4 --> MM["Memoria"]
  PL --> PL1["Brief"]
  PL --> PL2["GuiaDeEstilo"]
  PL --> PL3["Escaleta"]
  PR --> PR1["Borrador"]
  PR --> PR2["PaseDeRevision"]
  MM --> MM1["DeltaDeEscena"]
  MM --> MM2["Ficha"]
  MM --> MM3["Resumen"]
  MM --> MM4["AnclaDeEstilo"]
```

```mermaid
flowchart LR
  P5["Plano Calidad"]
  P5 --> Q1["DimensionDeCalidad"]
  P5 --> Q2["Verificador"]
  P5 --> Q3["Puerta"]
  P5 --> Q4["AntiPatron"]
  Q2 --> V1["Por regla"]
  Q2 --> V2["Juez LLM"]
  Q2 --> V3["Humano"]
  Q2 --> V4["Rubrica"]
  Q3 --> G1["Hallazgo"]
```

La rama de memoria es la que decide si el sistema escala: sin `DeltaDeEscena` hay que releer el texto para saber el estado, y eso se rompe hacia el capítulo diez.

## Relaciones núcleo

Un árbol de clases no dice nada por sí solo. Estas son las aristas que hacen trabajar a la ontología.

```mermaid
flowchart LR
  ARC["ArcoNarrativo"]
  BEAT["Beat"]
  ESC["Escena"]
  LUG["Lugar"]
  HEC["HechoCanonico"]
  CON["Personaje / Narrador / Lector<br/>(RegistroDeConocimiento)"]
  EST["EstadoDelMundo"]
  PRE["Presagio"]
  DRE["CurvaDeDread"]
  BEAT -->|sirve_a| ARC
  ESC -->|realiza| BEAT
  ESC -->|ocurre_en| LUG
  ESC -->|establece| HEC
  ESC -->|revela_a_lector| HEC
  CON -->|conoce| HEC
  ESC -->|modifica| EST
  PRE -->|se_paga_en| ESC
  ESC -->|escala| DRE
```

Fíjate en el par crítico: `establece` y `revela_a_lector` apuntan al mismo hecho pero desde escenas distintas, y `conoce` añade una tercera fecha por cada sujeto. La distancia entre esas tres es, literalmente, donde vive el suspense.

## Ciclo de vida de una escena

Los nombres de estado son los literales de la enumeración `estado_de_escena` de
`Docs/definitions.md`, no una versión bonita de ellos.

```mermaid
stateDiagram-v2
  state "planificada" as planificada
  state "generada" as generada
  state "en_verificacion" as en_verificacion
  state "rechazada" as rechazada
  state "en_revision" as en_revision
  state "aceptada" as aceptada
  state "consolidada" as consolidada
  [*] --> planificada
  planificada --> generada: modelo escribe
  generada --> en_verificacion: puerta
  en_verificacion --> rechazada: falla regla
  en_verificacion --> en_revision: juez marca
  rechazada --> generada: regenera
  en_revision --> generada: reescribe
  en_verificacion --> aceptada: pasa todo
  aceptada --> consolidada: aplica delta
  consolidada --> [*]
```

La transición que importa es `Aceptada → Consolidada`: hasta que el delta no se aplica, el estado del mundo no ha cambiado y la escena siguiente no puede generarse. Es ahí donde se corta la propagación del error.

## Generación de una escena

```mermaid
sequenceDiagram
  participant O as Orquestador
  participant M as Memoria
  participant G as Generador
  participant V as Verificadores
  O->>M: pide contexto de la escena
  M-->>O: estado, fichas, anclas
  O->>G: prompt + contexto
  G-->>O: texto + delta propuesto
  O->>V: pasa las puertas
  V-->>O: hallazgos o visto bueno
  O->>M: aplica delta y resume
```

El generador devuelve dos cosas, no una: el texto y el diff estructurado de lo que ha cambiado en el mundo. Pedir el delta en la misma llamada es más barato y más fiel que extraerlo después releyendo la escena.
