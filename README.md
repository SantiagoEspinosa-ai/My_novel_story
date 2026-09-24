# My_novel_story

Un sistema de agentes que escribe una **novela de diez capítulos para regalar**, a partir de una
entrevista con quien la compra, y el **harness** que la valida antes de publicarla: validadores
programáticos, semánticos y formales (Lean 4 sobre la historia, TLA+ sobre el propio harness),
un guardrail de palabras prohibidas, memoria en SQLite y observabilidad en Langfuse.

El enunciado es [`EXAMEN.md`](EXAMEN.md). Qué se decidió construir y por qué, y cómo se llegó,
está en [`docs/proceso/`](docs/proceso/README.md). El mapa del repositorio está en
[`AGENTS.md`](AGENTS.md).

> **Cómo leer el estado de este proyecto.** En `docs/` y en las specs, lo que no se ha ejecutado
> dice *sin ejecutar*, y lo que no se ha medido dice *sin medir*. La tabla de validadores de
> [`docs/proceso/diagramas.md`](docs/proceso/diagramas.md) separa, validador por validador, lo que
> **ha corrido con datos reales** de lo que existe y solo ha pasado sus pruebas con dobles. Qué exige
> el enunciado y qué falta está en [`docs/cobertura-examen.md`](docs/cobertura-examen.md).

## El brief de ejemplo

[`ejemplos/brief-ejemplo.json`](ejemplos/brief-ejemplo.json) es una ficha de entrevista cerrada, con
**datos inventados**: la destinataria, sus rasgos y recuerdos, su gato, el género y el tono, la
extensión, la dedicatoria, y una palabra y un nombre que no pueden aparecer. Es la entrada de la
novela de ejemplo, que se exporta a [`ejemplos/novela-ejemplo.pdf`](ejemplos/).

## Qué hace falta

- Python 3.12 y las dependencias de `backend/requirements.txt`.
- **Claude Code** en el `PATH` (`claude`): cada agente es una sesión delegada de Claude Code
  (`SPEC-14`), así que el harness no llama a ningún proveedor de modelos por la red.
- Los modelos de cada agente, en `backend/config/sistema.json`.
- Para Langfuse, las claves en `backend/.env`, con la forma de
  [`backend/.env.example`](backend/.env.example). **Sin claves no se envía nada**, y los guiones
  dicen que está apagado.
- Para la puerta de publicación, **Lean 4.34.0** con `lake` (se busca en `HARNESS_LAKE`,
  `ELAN_HOME`, el `PATH` y `~/.elan/bin`). Sin él, la versión no se publica y el informe lo dice.
- Para TLC, Java y `tla2tools.jar` (ver [`specs/tla/README.md`](specs/tla/README.md)).

```
cd backend && pip install -r requirements.txt
```

## Reproducir la novela de ejemplo

**Gasta dinero**: cada capítulo delega en el Planificador, el Revisor, el Escritor, el Editor y el
Resumidor. `-X utf8` hace falta porque la consola de Windows no es UTF-8 por defecto.

```
cd backend
python -X utf8 novela_regalo.py ../ejemplos/brief-ejemplo.json --base ejemplo.db --obra obra-ejemplo
python -X utf8 leer_obra.py --base ejemplo.db --obra obra-ejemplo --pdf ../ejemplos/novela-ejemplo.pdf
```

- El primero escribe los diez capítulos, pasa la puerta de publicación (con Lean) y termina con un
  informe: plan, capítulos, contexto enviado, coste leído, hooks ejecutados, publicación y Langfuse.
  Si se para, relanzarlo reanuda desde el último capítulo completado (probado con dobles;
  **sin ejercer** todavía en una ejecución real).
- `--capitulos 1` escribe solo el primero y no pasa la puerta.
- El segundo exporta el PDF **solo si la puerta publicó la versión**; si no, dice por qué y sale
  con 1.

## Las pruebas

```
cd backend && python -m pytest app -q
```

Ninguna prueba llama a un modelo ni envía nada a Langfuse: usan dobles con la forma de lo real.

## La verificación formal

```
cd specs/lean && lake build && lake exe verificar          # Lean sobre el fixture: 0
java -cp tla2tools.jar tlc2.TLC -config HarnessNovela.cfg HarnessNovela.tla   # en specs/tla
```

Qué comprueba cada invariante y qué contraejemplos encontró TLC, en
[`specs/lean/README.md`](specs/lean/README.md) y [`specs/tla/README.md`](specs/tla/README.md).

## La entrevista

Con el backend levantado (`cd backend && uvicorn app.main:app`), la entrevista se hace desde la
terminal. **Cada turno llama al modelo**:

```
cd backend && python -X utf8 entrevista_cli.py
```

## Vídeo de demo

Pendiente: irá en `presentacion/`, o enlazado desde aquí si supera el límite de GitHub.
