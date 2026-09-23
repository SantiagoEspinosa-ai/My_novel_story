---
id: SPEC-28
titulo: Tools de lectura de la story bible, con schema
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-23
version: 1
---

> **Historial.** v1: redactada con las cinco respuestas del autor (2026-09-23).
> Sin cuestiones abiertas.

# SPEC-28 — Tools de lectura de la story bible

## Qué problema resuelve

`EXAMEN.md` §3 pide *«tools con schema validado»*, y §6, que *«cada llamada a
tool»* aparezca como span. Hoy **el sistema no tiene tools**: todos los agentes
del pipeline declaran `tools: []` y el hook de policy niega cualquier
herramienta (`docs/architecture.md` § "Los hooks de Claude Code"; `PLAN-26`
E11). Es `EX-01` de `docs/cobertura-examen.md`.

Se descartó contar como tools los JSON que ya devuelven los agentes y valida el
backend: sería una lectura arriesgada del enunciado, y un span por llamada a tool
solo tiene sentido si las tools existen.

## Qué tiene que ser verdad al terminar

- **RF-01. Tres tools de lectura de la story bible:**
  1. **hechos**, cada uno con **los capítulos donde se usa** y el tipo de cada
     uso (`SPEC-21` `C-2`). Devolver el tipo junto a cada uso evita que la tool
     tenga que elegir qué tipos cuentan, que es lo que `C-2` deja a cada
     consumidor;
  2. **la ficha de un personaje o de un lugar**, con los mismos campos que
     `SPEC-22` `RF-43`;
  3. **la cronología**: eventos, momento, personajes presentes y lugar
     (`SPEC-21` `C-3`).
- **RF-02. Cada tool tiene un schema de entrada y otro de salida, validados.**
  Una entrada fuera de schema se rechaza con un error que el agente ve, y queda
  registrada. Los schemas replican las clases de `docs/definitions.md`, como
  cualquier modelo Pydantic del proyecto: un campo que no está allí no entra.
- **RF-03. Solo el Escritor y el Editor tienen tools.** El Planificador, el
  Revisor del plan, el Resumidor, el Entrevistador y el Juez siguen sin ninguna.
- **RF-04. Solo lectura.** Ninguna tool escribe. **El delta sigue siendo JSON**
  dentro de la respuesta del Escritor, con el contrato de siempre.
- **RF-05. Ninguna tool devuelve el texto de una escena.** Devuelven hechos,
  fichas y cronología. Es la regla de `CLAUDE.md` —nunca se manda el texto
  completo de la obra al modelo, y el texto de las escenas no se recupera— y una
  tool es otra forma de mandar.
- **RF-06. Cada tool solo lee la obra de la delegación que la llama.** Una tool
  que pudiera leer otra novela sería el camino de la exfiltración entre novelas
  que `SPEC-31` prueba en su red-team.
- **RF-07. El hook de policy pasa a allowlist por agente.** Cada agente puede
  llamar a sus tools y a nada más; todo lo demás se niega y queda en el audit log
  como hoy (`herramienta_denegada`). El hook sigue actuando solo sobre las
  delegaciones del pipeline (`SPEC-26` `RF-19`).
- **RF-08. Lo que devuelve una tool se mide y se registra en la traza, sin
  presupuestarlo.** Se cuentan sus tokens y se guardan junto a la llamada, pero
  no entran en el reparto por niveles de `CLAUDE.md`.
- **RF-09. Cada llamada a una tool es un span** en Langfuse (`SPEC-29`), con su
  nombre, su latencia, el resultado de la validación y el tamaño. Sus argumentos
  y lo que devuelve no suben: llevan datos de la story bible, y la story bible
  lleva al destinatario (`SPEC-29` § "El límite").

## Punto ciego declarado

**El límite de 100.000 tokens es sobre lo que mandamos, y lo que un agente trae
con una tool no pasa por él.** `CLAUDE.md` ya lo formula así (*«un límite sobre
lo que mandamos, no sobre la ventana del otro lado»*), y las tools lo amplían:
un Escritor que consulte veinte fichas mete en su contexto veinte fichas que el
ensamblador no midió ni recortó.

No se presupuesta porque el harness **no administra el contexto de la sesión
delegada** (`SPEC-14`) y no puede reservar nada sobre él. Se mide (`RF-08`) para
que la pregunta de si importa tenga respuesta con un número delante, y no por
intuición.

## Qué queda explícitamente fuera

- **Tools de escritura**, incluido pasar el delta a una tool.
- **Un servidor MCP para clientes externos** (`list_novels`, `get_chapter`…),
  que el enunciado deja como opcional.
- **Cómo se exponen las tools a la delegación**: es el plan.
- Tools para cualquier agente distinto del Escritor y el Editor.

## Lo que la gobierna

`EXAMEN.md` §3 y §6; `CLAUDE.md` § "Límite de contexto" y § "FastAPI";
`SPEC-14`; `SPEC-21` `C-2` y `C-3`; `SPEC-22` `RF-43`; `SPEC-26` `RF-18` y
`RF-19`; `SPEC-29`; `SPEC-31`; `EX-01`.
