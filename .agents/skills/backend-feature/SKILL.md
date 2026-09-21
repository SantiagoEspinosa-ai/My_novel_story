---
name: backend-feature
description: >
  Where backend code goes in this repository and which imports are allowed.
  Use when creating or modifying anything under `backend/`: adding a feature,
  deciding whether code belongs in a feature or in `commons`, adding a router,
  schema, service or repository, defining an Enum or a Pydantic model,
  resolving an import between features, or wiring a new step of the scene
  pipeline. Complements the official `fastapi` skill: that one covers FastAPI
  idioms, this one covers placement and dependency rules.
---

# Estructura del backend

Dónde va cada fichero en `backend/` y quién puede importar a quién. Es la
contraparte de `feature-sliced-design` para el servidor.

> **Esta skill no sustituye a la oficial de FastAPI.** Para cómo se declara una
> dependencia, cómo se tipa una respuesta o cómo se hace streaming, usa la skill
> `fastapi`. Esta responde a otra pregunta: *¿dónde va esto y de qué puede
> depender?*

## La regla, en una frase

**Una carpeta por caso de uso del pipeline, más `commons/` para lo compartido.**
Una feature es un caso de uso —algo que se ejecuta, se prueba y se rompe solo—,
no un plano del dominio ni una entidad.

```
backend/app/
  main.py                  # monta los routers
  commons/                 # config, db, dominio (Enums), modelo, invariantes, trabajos
  features/
    brief/  escaleta/  contexto/  generacion/  verificacion/
    revision/  consolidacion/  auditoria/  orquestacion/  lectura/
```

## Dónde va esto: árbol de decisión

Recórrelo en orden y para en la primera que se cumpla:

1. **¿Es un `Enum` de un vocabulario controlado de `Docs/definitions.md`?**
   → `commons/dominio/`. En ningún otro sitio, nunca.
2. **¿Lo van a usar dos o más features?** → `commons/`, en el subpaquete que le
   toque (`db/`, `modelo/`, `invariantes/`, `trabajos/`).
3. **¿Coordina varias features en un proceso?** → `features/orquestacion/`.
4. **¿Es una consulta de solo lectura para pintar el frontend?**
   → `features/lectura/`.
5. **En cualquier otro caso** → la feature del caso de uso al que pertenece.

Si dudas entre dos features, casi siempre la respuesta es que el código es de
`commons/` o que estás partiendo mal el caso de uso.

## La forma de una feature

Siempre los mismos ficheros, siempre con el mismo papel:

| Fichero | Contiene | No contiene |
| --- | --- | --- |
| `router.py` | Endpoints: valida, llama al servicio, devuelve | Lógica de negocio |
| `schemas.py` | Modelos Pydantic de entrada y salida | Acceso a datos |
| `service.py` | La lógica del caso de uso | SQL |
| `repository.py` | Acceso a datos; el único que ve SQL | Reglas de negocio |
| `agente.py` | Prompt y contrato del agente, si lo hay | Lógica que no sea del agente |
| `tests/` | Incluye el caso negativo de cada invariante que la feature comprueba | — |

## Las cuatro reglas de dependencia

Son lo que hace que la estructura valga para algo. Si se incumplen, la carpeta
es decoración:

1. **Una feature nunca importa de otra feature.** Si dos la necesitan, sube a
   `commons/`.
2. **`commons/` nunca importa de una feature.** La flecha va en un solo sentido.
3. **`features/orquestacion/` es la única excepción a la regla 1.** Existe para
   componer features en un proceso. Sin esa excepción la coordinación se cuela
   por las rendijas y acaba repartida entre todas.
4. **Los `Enum` de los vocabularios controlados viven solo en
   `commons/dominio/`.** Un valor fuera de la enumeración es un error de
   validación, no un aviso.

Antes de escribir un `import` entre paquetes, comprueba que no rompe ninguna. Si
la rompe, la solución no es una excepción: es mover el código.

## Reglas de dominio que afectan al código

- **Pydantic es la frontera de validación** y replica las clases de
  `Docs/definitions.md`. **Un campo que no está definido allí no entra en un
  esquema.** Si hace falta uno nuevo, primero se añade a `Docs/definitions.md`.
- **No inventes campos, clases ni valores de enumeración.** Ni "provisionales",
  ni "para probar".
- **Las llamadas al modelo son asíncronas.** Un endpoint que dispara trabajo del
  modelo encola y devuelve un identificador de trabajo; no bloquea.
- **Toda comprobación cita su invariante por identificador** (`INV-07`), nunca
  por descripción.
- **Un cambio en `Docs/definitions.md` que altere un atributo obligatorio necesita
  su migración en el mismo commit.**

## Antes de escribir código

Dos puertas del proceso de `AGENTS.md`, que aquí no se saltan:

- No se escribe código sin **plan de implementación aprobado**.
- Se escribe con **TDD**: primero la prueba que falla, después el código mínimo,
  después el refactor.

## Errores que hay que vigilar

| Error | Por qué aparece | Qué hacer |
| --- | --- | --- |
| Feature que importa de otra | Un caso de uso mal partido | Subir a `commons/` o rehacer el corte |
| `Enum` duplicado en una feature | Prisa por no tocar `commons/` | Moverlo a `commons/dominio/` |
| SQL en `service.py` | Saltarse el repositorio | Bajarlo a `repository.py` |
| Lógica en `router.py` | Endpoint que "solo era un `if`" | Subirla a `service.py` |
| Campo nuevo inventado en un esquema | Falta en `Docs/definitions.md` | Añadirlo allí primero |
| Carpeta `utils/` dentro de una feature | Cajón de sastre | Nombrar lo que hace, o `commons/` |
