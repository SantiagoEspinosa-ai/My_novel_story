---
id: PLAN-25
spec: SPEC-25
titulo: Implementación del destinatario, la entrevista y las palabras vetadas
estado: aplicada
aprobada_por: "autor del proyecto, en sesión (sustituir por su identificador)"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 88e3a2e
fecha: 2026-09-23
version: 2
---

> **Historial.** v2, durante la implementación: tres piezas cambian de carpeta
> por la regla de dependencias (`A-01`; skill `backend-feature`, reglas 1 y 2) y
> ninguna cambia de comportamiento. Los modelos de la ficha van a
> `commons/dominio/destinatario.py` porque `BriefDeObra`, en `commons/`, tiene
> que llevarlos. El detector de vetadas (`normalizar.py`, `vetadas.py`) y el
> audit log van a `commons/politica/` porque los usan dos features, `politica`
> (vía `orquestacion`) y `entrevista`, y una feature no importa de otra. Por el
> mismo motivo, **copiar las vetadas de la ficha a la tabla de la novela y
> entregar la obra lo compone `orquestacion/`**, no la entrevista. Se conserva
> la aprobación: la forma de los pasos y sus pruebas no cambian.

# PLAN-25 — Destinatario, entrevista y palabras vetadas

Cómo se construye `SPEC-25`. Cada paso empieza por la prueba que falla, deja las
433 pruebas actuales en verde y se puede commitear solo.

## Dónde vive

Dos features nuevas, porque son dos casos de uso distintos (`A-01`, `A-02`):

| Feature | Qué hace | Ficheros |
| --- | --- | --- |
| `features/entrevista/` | La ficha, la entrevista por turnos, el texto libre, las contradicciones y el borrado al entregar | `schemas.py`, `ficha.py`, `contradicciones.py`, `texto_libre.py`, `service.py`, `repository.py`, `router.py`, `tests/` |
| `features/politica/` | Las listas de palabras vetadas en sus tres niveles | `repository.py`, `tests/` |
| `commons/politica/` (v2) | El detector de vetadas y el audit log, que usan dos features | `normalizar.py`, `vetadas.py`, `auditoria.py`, `tests/` |
| `commons/dominio/destinatario.py` (v2) | Los modelos de la ficha, que lleva `BriefDeObra` | — |

Más:

- `.claude/agents/entrevistador.md`: el agente. Formula las preguntas y traduce
  las respuestas a categorías. **No decide** qué falta ni qué se contradice: eso
  lo calcula el código (`RF-07`, `RF-08`), y el agente solo juzga lo que el
  código no puede comparar (`RF-08b`).
- `backend/entrevista_cli.py`: la CLI fina. Solo habla HTTP con la API.
- `backend/config/vetadas.json`: el contenido inicial de las listas global y por
  franja de edad (lo pide `SPEC-25` § "Fuera").
- `backend/config/sistema.json`: gana `franjas_de_edad`, `contradicciones` y
  `topes.reescrituras_por_vetada`.

**Las tablas nuevas no necesitan migración.** Nacen con `CREATE TABLE IF NOT
EXISTS` en el `asegurar_tablas` de su feature, que es el patrón del repositorio.
La migración solo hace falta para alterar tablas existentes, y este plan no
altera ninguna. La sección `destinatario` de `BriefDeObra` es **opcional**, así
que `backend/config/brief.json` sigue siendo válido tal cual.

## Pasos

### E1 · El dominio primero

`Docs/definitions.md`: las clases `Destinatario`, `ElementoPersonal` (rasgo,
recuerdo, persona o mascota, con `imprescindible`), `FichaDeEntrevista`,
`HechoPropuesto`, `PalabraVetada` y `DecisionDePolitica`; los vocabularios
`ocasion`, `genero_de_la_historia`, `tono_de_la_historia`,
`papel_del_destinatario`, `nivel_de_veto`, `tipo_de_contradiccion` y
`tipo_de_decision_de_politica`; e `INV-21` en la tabla de invariantes.

**Prueba:** `test_enumeraciones.py` ya compara los `Enum` con
`Docs/definitions.md`. Se escriben los `Enum` que faltan y la prueba falla hasta
que cuadran literal a literal, `otro` incluido.

### E2 · Normalizar y detectar

`politica/normalizar.py` y `politica/vetadas.py`: una función pura
`coincidencias(texto, vetadas) -> list`. Pasa a minúsculas, quita los acentos,
reduce plurales (`-s`, `-es`) y género gramatical (`-o`/`-a`), compara **palabras
completas** y admite expresiones de varias palabras. Un nombre vetado genera dos
formas: completo y nombre de pila.

**Pruebas** (una por regla de `RF-17`): «Árbol» coincide con «arbol»; «perros»
con «perro»; «amiga» con «amigo»; «ana» **no** coincide en «ventana»; «Luis
Pérez» vetado coincide con «Luis» suelto; una expresión de dos palabras coincide
con saltos de línea en medio.

### E3 · Las listas en SQLite, en tres niveles

`politica/repository.py`: tabla `palabra_vetada` (`nivel`, `franja`, `obra`,
`forma`) y tabla `decision_de_politica` (el audit log de `RF-20`). La carga de
`config/vetadas.json` es idempotente. `vetadas_para(obra, edad)` junta los tres
niveles según la franja que corresponde a la edad.

Contenido inicial de `config/vetadas.json`, para revisar al aprobar:

- **global**: una veintena de insultos y términos ofensivos comunes en español;
- **infantil** (menos de 12 años): `sangre`, `matar`, `asesinar`, `cadaver`,
  `droga`, `borracho`, `sexo`;
- **juvenil** (de 12 a 17 años): `droga`, `sexo`.

**Pruebas:** exigidas por el enunciado, **una por nivel y una de variante**: una
palabra global se detecta en cualquier obra; una infantil se detecta con
destinatario de 8 años y no con uno de 40; una de la novela solo en su obra; y
«cadáveres» coincide con `cadaver` (acento y plural a la vez). Además: cargar dos
veces no duplica filas, y una franja cambiada en `sistema.json` cambia el
resultado sin tocar código (`RF-16`).

### E4 · `INV-21` en la puerta, con su propio tope

`commons/invariantes/registro.py` gana `INV-21` (`bloqueante`, ámbito
capítulo, `regla`). En `orquestacion/obra.py`, **antes de aceptar cada escena**
se comprueba su texto. Si hay coincidencias, vuelve al Escritor con la lista en
`problemas`, **hasta `reescrituras_por_vetada` = 2**, con un contador propio que
no consume `intentos_por_escena`. Si se agota, `g.parada` recibe
`motivo="palabra_vetada"`, **sin rendición**, y cada coincidencia, reescritura y
parada queda en `decision_de_politica`. `evaluar_cierre` vuelve a comprobar el
texto entero del capítulo como segunda línea.

**Se comprueba por escena y no solo al final del capítulo** porque el pipeline
de hoy escribe escena a escena: esperar al cierre obligaría a reescribir escenas
ya consolidadas cuyo delta ya se aplicó al mundo. Un capítulo sigue sin poder
aceptarse con una palabra vetada, que es lo que exige `RF-18`. Si la spec del
pipeline pasa a escribir por capítulo, el contador se mueve con ella.

**Regla 4** (el prompt pide lo que el contrato exige): `generacion/prompt.py`
incluye la lista de vetadas que aplican, con la instrucción de no usarlas.

**Pruebas**, con `DobleDelModelo`: un escritor que mete una vetada dos veces y la
tercera no → escena aceptada con 2 reescrituras y 3 filas en el audit log; uno
que la mete tres veces → parada `palabra_vetada`, ninguna escena aceptada por
rendición; `test_prompt.py` → el prompt contiene las vetadas; un capítulo con una
vetada que entró por edición manual → `evaluar_cierre` no lo deja cerrar.

### E5 · La ficha y su schema

`entrevista/schemas.py`: `FichaDeEntrevista` en Pydantic con los `Enum` de E1.
Un valor `otro` sin su texto literal es un error; un campo desconocido, un 422.
La extensión está fijada (10 capítulos, 1.000–1.500 palabras) y **no es un campo
editable**. `entrevista/ficha.py`: `que_falta(ficha)` devuelve los obligatorios
vacíos de `RF-02` **en el orden del anexo**, y `a_brief(ficha)` la convierte en
la sección `destinatario` de `BriefDeObra`, más las vetadas de la novela.

**Pruebas:** una ficha vacía devuelve los ocho obligatorios en orden; una
completa devuelve `[]`; `otro` sin literal falla; intentar fijar la extensión
falla; `a_brief` de una ficha incompleta lanza error en vez de producir un brief
a medias; `brief.json` actual sigue cargando sin `destinatario`.

### E6 · Las contradicciones deterministas

`entrevista/contradicciones.py`: `contradicciones(ficha, reglas)` con las
reglas de `sistema.json`: edad frente a género, edad frente a ocasión y recuerdo
frente a edad. Si algún valor comparado es `otro`, devuelve `requiere_juicio` en
vez de callar (`RF-08b`).

**Pruebas:** un caso positivo y uno negativo por cada tipo; un recuerdo fechado
antes del nacimiento; un recuerdo «a los 30» para alguien de 25; `otro` →
`requiere_juicio` y nunca «sin contradicción».

### E7 · El texto libre

`entrevista/texto_libre.py`: más de 5.000 caracteres → rechazo con motivo, sin
truncar. El texto va al modelo dentro de un sobre delimitado y declarado como no
confiable. Un detector de patrones con forma de instrucción («ignora», «olvida
las instrucciones», «a partir de ahora», «escribe en su lugar»…) registra un
hallazgo en el audit log y **descarta todos los hechos extraídos de ese texto**,
aunque el modelo los haya devuelto. Los hechos entran como `propuesto` y solo
pasan a la ficha al confirmarlos. El texto original no se guarda en la ficha.

**Pruebas:** 5.000 caracteres pasan y 5.001 se rechazan; un texto con
inyección y un doble que devuelve hechos igualmente → cero hechos y una fila en
el audit log; un hecho propuesto no aparece en la ficha hasta confirmarlo; la
ficha serializada no contiene ninguna frase del texto original.

### E8 · El agente y la entrevista por turnos

`.claude/agents/entrevistador.md` y `entrevista/service.py`. En cada turno: se
guarda la respuesta; el agente recibe la ficha actual, la respuesta y **lo que el
código ha calculado** (qué falta, qué contradicciones hay); devuelve un JSON con
la actualización de la ficha y la siguiente pregunta, validado con schema. Un JSON
inválido se reintenta con el tope de transporte existente y, agotado, falla de
forma visible. Mientras haya obligatorios vacíos o contradicciones abiertas, la
entrevista no puede cerrarse (`RF-07`, `RF-09`). Si un nombre de pila vetado
coincide con el de otra persona o mascota de la ficha, se avisa (`RF-10`).

**Pruebas**, con el doble: la entrevista no cierra con un obligatorio vacío; una
contradicción bloquea el cierre hasta que un turno la resuelve y la resolución
queda anotada; el aviso de `RF-10` aparece; un JSON inválido del agente no
modifica la ficha.

### E9 · Los endpoints

`entrevista/router.py`, sin lógica (`A-01`): `POST /entrevistas`,
`POST /entrevistas/{id}/turnos`, `POST /entrevistas/{id}/texto-libre`,
`POST /entrevistas/{id}/hechos/{h}/confirmar` y `POST /entrevistas/{id}/cerrar`,
que devuelve el brief. **Los turnos llaman al modelo, así que son asíncronos**
(`CLAUDE.md`): devuelven 202 y un trabajo de la cola existente (`A-05`), y el
cliente consulta el trabajo.

**Pruebas** con `TestClient`: flujo completo con el doble, de la creación al
brief; un turno devuelve 202 y un trabajo; cerrar una entrevista incompleta
devuelve 409 con la lista de lo que falta.

### E10 · La CLI fina

`backend/entrevista_cli.py`: pregunta, lee la respuesta, la envía y espera el
trabajo. No importa nada de `app.features`.

**Prueba:** con un transporte HTTP simulado, un diálogo de tres turnos llega a
la ficha; y una prueba estática comprueba que el módulo no importa
`app.features` (la CLI no puede tener lógica propia).

### E11 · El borrado al entregar

`POST /obras/{id}/entregar` marca la obra como entregada y borra la
conversación, el texto libre y la ficha. Conserva las vetadas de la novela y los
hechos de la story bible, y deja una fila en el audit log con qué se borró y
cuándo, **sin el contenido** (`RF-21`). La lectura web (spec posterior) llamará a
este mismo endpoint.

**Pruebas:** tras entregar, las tablas de la entrevista están vacías para esa
obra; las vetadas y los hechos siguen ahí; la fila del audit log no contiene
ningún texto de la conversación; entregar dos veces no falla y no duplica filas.

### E12 · `Docs/` y spec al día

`Docs/architecture.md`: las dos features y el agente entrevistador en la tabla de
agentes. `Docs/verification.md`: las filas nuevas de E13. `Docs/domain-knowledge.md`:
las clases nuevas en el árbol, después de `definitions.md` y nunca antes.
`AGENTS.md`: las dos features en la fila de `backend/`. Después, `SPEC-25` pasa a
`aplicada` con su commit propio y se mueve a `specs/aplicadas/`.

## Qué filas `VER-xx` cierra

Ninguna de las existentes: todas son anteriores al examen. Se abren y cierran
**cuatro nuevas**, con número comprobado al commitear (hoy el último publicado
es `VER-65`):

| Fila | Qué comprueba | Paso |
| --- | --- | --- |
| nueva 1 | `INV-21`: un nivel por caso, una variante y la parada al agotar | E2–E4 |
| nueva 2 | Las tres contradicciones y el `requiere_juicio` de `otro` | E6 |
| nueva 3 | La inyección en el texto libre no produce hechos y queda auditada | E7 |
| nueva 4 | El borrado al entregar conserva lo que la regeneración necesita | E11 |

## Lo que este plan no hace

- No escribe la novela a partir de la ficha ni cambia la forma de la obra: eso es
  la spec del pipeline de la novela regalo.
- No envía nada a Langfuse: el audit log guarda lo necesario para que lo haga la
  spec de observabilidad.
- No hace la interfaz web de la entrevista.
