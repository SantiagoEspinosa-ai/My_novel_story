@AGENTS.md

# CLAUDE.md

La línea de arriba importa `AGENTS.md` entero: Claude Code la expande al arrancar la sesión y carga ese contenido como si estuviera escrito aquí. Se mantiene un solo mapa de contexto y lo leen todos los agentes. Todo lo que sigue es lo específico de este proyecto.

## Requisitos técnicos

| Área | Decisión | Restricción |
| --- | --- | --- |
| Backend | FastAPI | Único servicio HTTP. Nada de lógica de dominio en el frontend |
| Frontend | React | Consume la API, no toca la base de datos |
| Contexto del modelo | 100.000 tokens | Límite duro **sobre lo que el harness manda** en una delegación, incluida la reserva de salida |
| Persistencia | SQLite con soporte vectorial | Una sola base. Sin servicio de vectores externo |

### FastAPI

- Los modelos Pydantic son la frontera de validación y replican las clases de `docs/definitions.md`. Un campo que no está definido allí no entra en un esquema.
- Los valores de los vocabularios controlados se implementan como `Enum`, no como cadenas libres. Un valor fuera de la enumeración es un error de validación, no un aviso.
- Las llamadas al modelo son asíncronas. Generar una escena tarda, así que el endpoint arranca un trabajo y devuelve su identificador; no bloquea.

### React

- La interfaz muestra estado, no lo calcula. El cambio de valor de una escena y el estado de las invariantes vienen resueltos de la API.
- Una escena se muestra siempre con su estado (`planificada`…`consolidada`) y con los hallazgos abiertos que tenga. Un texto sin ese contexto induce a darlo por bueno.

### Límite de contexto: 100.000 tokens

**Es un límite sobre lo que mandamos, no sobre la ventana del otro lado.** El harness delega
en sesiones de Claude Code y no administra su contexto: puede medir lo que ensambla y no
puede reservar nada sobre un techo ajeno. Sigue siendo un límite real sobre algo real —lo
que sale de nuestro lado— y lo que desaparece es la garantía sobre lo que pasa al recibirlo.
El reparto por niveles, el orden de recorte y `RF-26` no cambian: mandar menos sigue siendo
mejor (`SPEC-14` C-1).

El presupuesto se reparte por niveles de memoria y se comprueba antes de cada llamada. Si no cabe, se recorta por el nivel de menor prioridad, nunca truncando por el final.

| Nivel | Presupuesto | Contenido |
| --- | --- | --- |
| Inmutable | 15.000 | Premisa, guía de estilo, reglas del mundo, anclas de estilo |
| Estado actual | 10.000 | Instantánea del mundo en el momento de la escena |
| Local | 25.000 | Escena anterior completa y resumen de las tres previas |
| Recuperado | 20.000 | Fichas de entidades presentes, setups pendientes, registro de conocimiento aplicable |
| Resúmenes | 10.000 | Condensaciones de capítulo y de parte |
| Salida | 20.000 | Reserva para el texto generado y su delta |

**Estas cifras están sin ejercitar, y conviene saberlo antes de razonar sobre ellas.** El
contexto medido de una escena real es de **1.339 tokens** —el 1,3% del techo— y en cinco
ejecuciones **no se ha recortado nunca**. El reparto no está mal: está sin ejercer, y un
mecanismo que nunca se ejerce **no está verificado, solo declarado**. Las pruebas lo
ejercitan con techos artificiales, lo que comprueba que el algoritmo funciona y no que el
reparto sea el correcto. Está abierto en `docs/verification.md` con dos salidas: ajustar las
cifras a lo que se mide, o declarar que describen una obra larga que todavía no existe.

**Y esa cifra medía lo que se montaba, no lo que se enviaba** (`F-58`). Hasta el arreglo, el
Escritor recibía la lista de tamaños de los bloques en vez de su texto, en todas las
escenas: lo enviado era mucho menos que 1.339 tokens y no llevaba ni la premisa. Desde el
arreglo lo montado y lo enviado coinciden, pero **el contexto enviado está sin medir**: se
mide en la primera ejecución real de la novela regalo, y hasta entonces 1.339 no dice cuánto
sobra. **Primera medida (E13): 419 tokens estimados** para el capítulo 1 de la novela regalo.
Sesga hacia abajo: es el primer capítulo, sin capítulo anterior ni resúmenes, que son los
bloques que más crecen. Todavía no dice cuánto se envía a mitad de novela.

Nunca se manda el texto completo de la obra **al modelo**. El límite de 100.000 tokens es sobre **lo que se envía en una llamada**, no sobre lo que el código lee de la base: una comprobación determinista puede leer el texto de un capítulo para medirlo —`INV-15` calcula así la distancia estilométrica— sin tocar el presupuesto. Si una **llamada al modelo** parece necesitar la obra entera, el fallo está en los resúmenes o en la recuperación, no en el presupuesto.

### SQLite con soporte vectorial

- Una sola base de datos guarda el estado estructurado y los embeddings. La búsqueda por similitud se hace con una extensión vectorial de SQLite; no se añade un servicio aparte.
- Se indexan fichas de entidad, resúmenes de escena y setups pendientes (los presagios, específicos de terror, se retiraron en `SPEC-26` v3). El texto completo de las escenas se guarda pero no se recupera por similitud: para eso están los resúmenes.
- El estado del mundo se reconstruye acumulando los deltas de escena en orden. No se relee el texto para averiguar qué pasó.
- Las migraciones de esquema se versionan. Un cambio en `docs/definitions.md` que altere un atributo obligatorio necesita su migración en el mismo commit.

## Reglas de trabajo

- No inventes campos, clases ni valores de enumeración. Si algo falta, se añade primero a `docs/definitions.md`.
- Una comprobación del harness cita siempre su invariante por identificador.
- Las invariantes `bloqueante` detienen la escena en la puerta; `mayor` y `menor` generan hallazgo y dejan seguir. Esa diferencia se respeta en el código, no se resuelve caso por caso.
- Antes de dar por buena una escena, su delta tiene que estar aplicado. Es lo que corta la propagación del error.

## Comandos

El comando exacto, no una descripción de él.

```
cd backend && pip install -r requirements.txt   # una vez
cd backend && python -m pytest app -q           # las pruebas
```

Todavía no hay build: el backend se ejecuta con `uvicorn app.main:app` y el frontend no existe.

La entrevista del destinatario (`SPEC-25`) se hace desde la terminal con el backend levantado. **Cada turno llama al modelo**, así que gasta dinero; necesita `modelos.entrevistador` en `backend/config/sistema.json`:

```
cd backend && python -X utf8 entrevista_cli.py
```

La novela regalo de principio a fin (`SPEC-26`), a partir de la ficha cerrada de una entrevista. **Gasta dinero** en cada capítulo; necesita los modelos del Planificador, el Revisor, el Editor, el Escritor y el Resumidor en `backend/config/sistema.json`:

```
cd backend && python -X utf8 novela_regalo.py FICHA.json --capitulos 1
```

El PDF de una obra (`SPEC-27`), **solo si la puerta de publicación la publicó**; si no, dice por qué y sale con 1:

```
cd backend && python -X utf8 leer_obra.py --base ejemplo.db --obra obra-ejemplo --pdf ../ejemplos/novela-ejemplo.pdf
```

Un brief de evaluación (`SPEC-31`) de principio a fin, con su entrevista si el brief es un guion. **Gasta dinero**: sin `--confirmo-el-gasto` solo enseña lo gastado, lo que queda hasta el techo de 150 USD (una decisión de presupuesto, no una medida) y el mayor coste medido de una novela completa, y sale. El libro de gasto (`--libro`) se comparte; la novela va a una base propia por ejecución (`F-100`). Regenera `harness/evals/resultados.md`:

```
cd backend && python -X utf8 evaluar.py ../harness/evals/brief-base.json --pasada antes --confirmo-el-gasto
```

**La puerta de publicación ejecuta Lean** (`SPEC-30`): necesita `lake` (Lean 4.34.0). Se busca en `HARNESS_LAKE`, `ELAN_HOME`, el `PATH` y `~/.elan/bin`; sin él, la versión no se publica y el informe lo dice.

**Los guiones de ejecución real gastan dinero** y por eso no están aquí como comando suelto: `backend/f6_seis_escenas.py` delega en sesiones de verdad. Necesitan `HARNESS_MODELO_ESCRITOR`, `HARNESS_MODELO_JUEZ` y `HARNESS_MODELO_RESUMIDOR`, y se lanzan con `python -X utf8` porque la consola de Windows no es UTF-8 por defecto.
