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

- Los modelos Pydantic son la frontera de validación y replican las clases de `Docs/definitions.md`. Un campo que no está definido allí no entra en un esquema.
- Los valores de los vocabularios controlados se implementan como `Enum`, no como cadenas libres. Un valor fuera de la enumeración es un error de validación, no un aviso.
- Las llamadas al modelo son asíncronas. Generar una escena tarda, así que el endpoint arranca un trabajo y devuelve su identificador; no bloquea.

### React

- La interfaz muestra estado, no lo calcula. El cambio de valor de una escena, la curva de dread y el estado de las invariantes vienen resueltos de la API.
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
reparto sea el correcto. Está abierto en `Docs/verification.md` con dos salidas: ajustar las
cifras a lo que se mide, o declarar que describen una obra larga que todavía no existe.

Nunca se manda el texto completo de la obra **al modelo**. El límite de 100.000 tokens es sobre **lo que se envía en una llamada**, no sobre lo que el código lee de la base: una comprobación determinista puede leer el texto de un capítulo para medirlo —`INV-15` calcula así la distancia estilométrica— sin tocar el presupuesto. Si una **llamada al modelo** parece necesitar la obra entera, el fallo está en los resúmenes o en la recuperación, no en el presupuesto.

### SQLite con soporte vectorial

- Una sola base de datos guarda el estado estructurado y los embeddings. La búsqueda por similitud se hace con una extensión vectorial de SQLite; no se añade un servicio aparte.
- Se indexan fichas de entidad, resúmenes de escena y presagios pendientes. El texto completo de las escenas se guarda pero no se recupera por similitud: para eso están los resúmenes.
- El estado del mundo se reconstruye acumulando los deltas de escena en orden. No se relee el texto para averiguar qué pasó.
- Las migraciones de esquema se versionan. Un cambio en `Docs/definitions.md` que altere un atributo obligatorio necesita su migración en el mismo commit.

## Reglas de trabajo

- No inventes campos, clases ni valores de enumeración. Si algo falta, se añade primero a `Docs/definitions.md`.
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

**Los guiones de ejecución real gastan dinero** y por eso no están aquí como comando suelto: `backend/f6_seis_escenas.py` delega en sesiones de verdad. Necesitan `HARNESS_MODELO_ESCRITOR`, `HARNESS_MODELO_JUEZ` y `HARNESS_MODELO_RESUMIDOR`, y se lanzan con `python -X utf8` porque la consola de Windows no es UTF-8 por defecto.
