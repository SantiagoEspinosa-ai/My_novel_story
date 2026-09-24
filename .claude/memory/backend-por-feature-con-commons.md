---
name: backend-por-feature-con-commons
description: El backend FastAPI de My_novel_story se organiza en una carpeta por feature (caso de uso del pipeline) más una carpeta commons para lo compartido.
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-21T16:30:07.435Z
---

# El backend se organiza por feature, con una carpeta `commons`

El usuario fijó esta decisión de arquitectura de forma explícita al encargar
`Docs/architecture.md`: *"Decisión: Architecture Backend: Cada Feature una carpeta
con una carpeta de commons para temas comunes"*. No es una sugerencia a evaluar,
es la estructura que debe seguir el backend de este proyecto.

Al preguntarle qué cuenta como *feature*, eligió **el caso de uso del pipeline**,
no el plano del dominio ni el agregado. Es decir: `escaleta/`, `generacion/`,
`verificacion/`, `revision/`, `consolidacion/`, `contexto/`, `auditoria/`,
`orquestacion/`, `lectura/` — y no `obra/`, `mundo/`, `terror/`… ni
`escena/`, `personaje/`, `lugar/`. El motivo que le convenció es que un caso de
uso como "generar escena" cruza los cinco planos del dominio, así que partir por
plano dejaría cada caso de uso repartido entre carpetas.

En consecuencia, al escribir código de backend en este repositorio:

- Cada feature lleva siempre los mismos ficheros: `router.py`, `schemas.py`,
  `service.py`, `repository.py`, `agente.py` (si tiene agente) y `tests/`.
- Una feature nunca importa de otra feature; lo que necesiten dos se sube a
  `commons/`. `commons/` nunca importa de una feature.
- La única excepción es `orquestacion/`, que existe precisamente para componer
  features; sin esa excepción la coordinación se reparte entre todas.
- En `commons/` viven la configuración, el acceso a SQLite y sus migraciones, los
  `Enum` de los vocabularios controlados, el cliente del modelo, el registro de
  invariantes y la tabla de trabajos.

La decisión está escrita en `Docs/architecture.md`, pero ese documento no se
carga automáticamente al arrancar la sesión (el usuario decidió no añadirlo a
`AGENTS.md`), así que conviene recordarla desde aquí.
