---
name: examen-md-manda-sobre-las-decisiones
description: "En My_novel_story, EXAMEN.md (el enunciado del examen final) tiene precedencia sobre cualquier decisión del proyecto; si una spec o un documento lo contradice, se revisa la decisión, no el enunciado."
metadata:
  node_type: memory
  pinned: false
  originSessionId: 756a2d02-1bea-4a4e-b9da-71319686dfee
  modified: 2026-09-24T00:30:10.072Z
---

# EXAMEN.md manda sobre las decisiones del proyecto

El usuario de `My_novel_story` añadió `EXAMEN.md` a la raíz como fuente de verdad
sobre **qué hay que entregar**, y pidió que su precedencia quedara escrita en
`AGENTS.md`: si algo del enunciado contradice a una decisión del proyecto
—`CLAUDE.md`, `Docs/`, una spec o un plan—, **gana el enunciado y la decisión se
revisa**. Lo que el enunciado no menciona lo siguen gobernando las reglas del
proyecto.

El usuario acotó la precedencia con dos matices que gobiernan cualquier contraste
contra el enunciado: **`EXAMEN.md` dice qué entregar, no cómo construirlo**, y
**un mínimo suyo no es un techo** (si pide tres roles y hay diez, no es un hueco).
Y distingue dos clases de hueco: de documentación (el enunciado lo pide y ningún
documento lo recoge, o un documento lo contradice), que se cierran corrigiendo
documentos, y de sistema (documentado y el código no lo hace), que se registran y
van a plan. El registro vive en `Docs/cobertura-examen.md` con IDs `EX-xx`.

**Cuando una decisión va más allá de lo que pide el enunciado, se escribe como
decisión nuestra, con su motivo, y no como obligación del enunciado.** El usuario
lo pidió dos veces seguidas al revisar las specs de la novela regalo: el techo de
150 USD de la evaluación *«es mío, no del enunciado… que la spec diga que es una
decisión de presupuesto y no un requisito»*, y el bloqueo de publicar un capítulo
en rendición, que es más estricto de lo pedido: *«regístralo como decisión nuestra
y no como obligación del enunciado, con el motivo: un capítulo que se rindió no es
un capítulo que pasó»*. El motivo: si se atribuye al enunciado, nadie sabrá que se
puede revisar. Y lo que el enunciado no pide y cuesta trabajo (un PDF por versión)
se hace solo si sale gratis del diseño.

Y lo formuló como regla general para todo el trabajo que sigue: *«puedes modificar lo que
haga falta —specs, planes, código, decisiones anteriores— pero nada puede contradecir
EXAMEN.md. Si un cambio choca con el enunciado, para y dímelo en vez de aplicarlo.»* Así que
antes de aplicar una decisión, se contrasta con el enunciado y se dice que se ha hecho; si
choca, no se aplica.

Añadió un matiz sobre los validadores que no se ejecutan: *«Un validador que no corre no es
un validador que pasó, y el enunciado se cumple solo si eso se dice.»* Toda tabla de
resultados distingue «no ejecutado» de «pasó».

En la práctica:

- Al escribir o revisar una spec, contrastarla con `EXAMEN.md`. Una exclusión
  explícita que choque con el enunciado es un defecto de la spec. El primer caso
  que apareció fue `SPEC-22`, que dejaba fuera "publicar la obra a un formato de
  libro" cuando el enunciado exige el PDF aunque la lectura sea web.
- Revisar la decisión sigue el proceso normal de puertas: una spec que la cambie,
  aprobada antes del código. La precedencia dice qué gana, no permite saltarse
  las puertas.
- Al decir que algo del enunciado "no está cubierto", buscar en todo el
  repositorio, no solo en las specs abiertas: parte del trabajo (Lean y TLA+ en
  `specs/lean/` y `specs/tla/`, briefs en `harness/evals/`) existe fuera de
  cualquier spec.
