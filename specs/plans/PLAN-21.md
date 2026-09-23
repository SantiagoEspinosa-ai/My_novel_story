---
id: PLAN-21
spec: SPEC-21
titulo: Implementación de los usos del hecho y la cronología de la fábula
estado: aprobada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# PLAN-21 — Usos del hecho y cronología de la fábula

Implementa `SPEC-21`. Cada paso deja el repositorio funcionando y va con la prueba que
falla antes de escribir el código que la pasa.

## Dónde vive

Una feature nueva, `backend/app/features/cronologia/`, y ampliaciones de dos existentes.
La regla de `A-01` decide el reparto: **el que escribe el dato es quien ya escribe en esa
tabla**.

| Qué | Dónde | Por qué ahí |
| --- | --- | --- |
| Vocabularios `tipo_de_uso_de_hecho`, `origen_de_uso`, `tipo_de_presencia` | `commons/dominio/enumeraciones.py` | `D-3`: los vocabularios del dominio viven solo ahí |
| Migraciones 3 y 4 | `commons/db/migraciones.py` | Bases ya creadas necesitan las columnas nuevas |
| Tablas `uso_de_hecho`, `evento_cronologico`, `participacion_en_evento` | `features/cronologia/repository.py` | Feature nueva: es un caso de uso propio, no un anexo de la escaleta |
| Consultas parametrizadas | `features/cronologia/consultas.py` | Lo que consumen las cuatro capacidades |
| `escena.capitulo`, `t_fabula`, `personajes_presentes` | `features/escaleta/repository.py` | Es su tabla |
| `entidad.fecha_de_nacimiento` | `features/consolidacion/aplicar.py` | Es su tabla |
| Enganche al consolidar | `features/orquestacion/obra.py` | `A-02`: sólo orquestación compone entre features |

## Pasos

### E1 · Los tres vocabularios

Tres `Enum` nuevos en `commons/dominio/enumeraciones.py`, con sus literales ASCII.

**Prueba:** `test_enumeraciones.py` — los valores son exactamente los de
`Docs/definitions.md`, y `TipoDeUsoDeHecho` tiene los cuatro.

### E2 · `escena` gana capítulo, momento narrativo y presentes

Migración 3: `ALTER TABLE escena ADD COLUMN capitulo / t_fabula / t_discurso /
duracion_ficcional / personajes_presentes`. `guardar_escaleta` los escribe; `escenas_de` y
`escena` los devuelven. Una consulta nueva `escenas_de_capitulo` filtra **por capítulo**.

**Prueba:** guardar una escaleta con capítulo y leerla devuelve el capítulo; y
`escenas_de_capitulo` de un capítulo que no existe devuelve vacío en vez de la obra entera.

### E3 · La tabla `uso_de_hecho` y su escritura idempotente

`features/cronologia/repository.py`: tabla, índices y `registrar_usos`.

**Prueba:** escribir dos veces los mismos usos deja una fila por `(hecho, escena, tipo)`;
dos tipos distintos sobre el mismo par son dos filas.

### E4 · Los tres tipos que se rellenan solos

`features/cronologia/extraccion.py`: `establece` de `revelaciones`, `depende` de
`acciones`, `menciona` buscando el enunciado en el texto.

**Prueba:** un delta con una revelación y una acción sobre hechos distintos produce un
`establece` y un `depende`; un texto que nombra un hecho que el delta no declara produce un
`menciona` y nada más. Y el caso negativo: un hecho que no aparece ni en el delta ni en el
texto no produce ninguna fila.

### E5 · La cronología

Migración 4: `entidad.fecha_de_nacimiento`. Tablas `evento_cronologico` y
`participacion_en_evento` con sus índices, y `registrar_evento`.

**Prueba:** un evento con dos presentes y un mencionado devuelve dos presentes al
preguntar por presencia; y la escritura es idempotente por `id`.

### E6 · Las consultas que consumen las cuatro capacidades

`features/cronologia/consultas.py`: `capitulos_donde_se_usa`, `aparece_en_algun_capitulo`,
`capitulos_a_regenerar`, y las tres de Lean —`orden_temporal`, `edades_incoherentes`,
`ubicuidades`—.

**Prueba:** cada conjunto de tipos cuenta lo suyo y **sólo** lo suyo; un personaje sin
`fecha_de_nacimiento` sale en `sin_fecha_de_nacimiento` y **no** en `incoherentes`.

### E7 · Enganche en el bucle, dentro de la transacción

`orquestacion/obra.py`: el registro de usos y del evento ocurre donde hoy se marca
`escena_de_establecimiento`.

**Prueba:** consolidar una escena deja sus usos y su evento escritos; si el delta es
incompatible y la consolidación revierte, **no queda ninguna fila**.

### E8 · `Docs/` al día

`Docs/definitions.md`: los tres vocabularios, `Escena.capitulo`,
`Personaje.fecha_de_nacimiento`, `EventoCronologico.lugar` y `.capitulo`, y la relación
`usa` en la tabla de relaciones.

## Qué filas `VER-xx` cierra

Ninguna. `Docs/verification.md` no tiene hoy fila para estas dos relaciones porque no
existían. Las filas nuevas son trabajo de la spec que construya cada capacidad, que es
donde se podrá decir qué punto ciego tiene cada validador.
