---
id: SPEC-10
titulo: Cinco huecos del dominio que la rama main ya sufrió
estado: en_revision
aprobada_por:
fecha_aprobacion:
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-10 — Huecos del dominio que `main` ya sufrió

## Qué problema resuelve

La rama `main` contiene un harness anterior que **se ejecutó de verdad**: generó novelas,
midió tokens y dejó quince hallazgos fechados en `DECISIONES.md`. Esta línea de trabajo
tiene una ontología mucho más formal y **no se ha ejecutado nunca**.

Al comparar los dos contratos aparecieron diez huecos en el nuestro. Esta spec recoge los
**cinco que cambian el dominio**. Los otros cinco cambian solo la arquitectura y van
aparte; el reparto está al final.

Ninguno de los cinco es una idea nueva: los cinco son cosas que el contrato viejo ya
resolvió porque le costó un disgusto resolverlas.

---

## C-1 · Una escena que falla muchas veces no tiene salida

**Hoy:** la transición `rechazada` → `generada` la dispara *"Persona desde el frontend"*.
Sin tope, sin escalera y sin criterio de rendición. Una escena que falla su invariante
`bloqueante` diez veces vuelve diez veces a una persona, y `SPEC-01` no dice qué pasa a la
décima.

**Lo que `main` decidió.** `EJECUCION.md` Regla 1: *"Ningún capítulo detiene la generación.
Un capítulo que no pasa la validación se acepta por puntuación y se marca en el informe."*
Tiene una **escalera de modelos** —`escalera_escritor`, `intentos_por_modelo`, hasta seis
intentos— y, agotada, `mejor_intento()` se queda con el menos malo.

**Qué hay que fijar:**

- **Si existe rendición.** El contrato viejo y el nuestro parten de filosofías opuestas:
  allí nada detiene la generación, aquí una `bloqueante` detiene la escena en la puerta.
  Las dos son defendibles y la spec **no elige**.
- **Si hay escalera de modelos** al reintentar, o siempre el mismo.
- **Dónde se guarda el número de intentos.** Hoy `Borrador` tiene `version` y nadie cuenta
  intentos por escena.
- **Qué marca la escena que se aceptó sin pasar.** El viejo tiene `ACEPTADO_POR_PUNTUACION`
  como estado de capítulo. Aquí sería un valor más de `estado_de_escena`, o un campo.

**Por qué es dominio:** toca `estado_de_escena`, `Escena` y `Borrador`.

---

## C-2 · No hay categoría para "el validador no contestó"

**Hoy:** `severidad` clasifica el **hallazgo** —`bloqueante`, `mayor`, `menor`— y
`estado_de_hallazgo` su ciclo de vida. **Ninguna de las dos puede expresar que no hubo
veredicto.** Un Juez que devuelve basura no tiene sitio en el modelo, y ninguna de las 56
filas de `Docs/verification.md` lo cubre.

**Lo que `main` decidió.** Regla 2: un JSON que no parsea cuenta como `FALLO`, **jamás**
como `PASA`. El procedimiento es defensivo y está escrito: `json.loads` directo → extraer
el primer bloque `{...}` equilibrado → repetir la delegación **una vez** incluyendo el
error → registrar `INDETERMINADO` y tratarlo como `FALLO`. Y `src/puntuacion.py` le pone
gravedad **alta** a propósito:

> *"Un validador que no contesta es un agujero en la validación, no una pega menor, y así
> el intento nunca gana por defecto a otro que sí se dejó auditar."*

**Qué hay que fijar:**

- **Dónde vive la ausencia de veredicto**: un valor de `estado_de_hallazgo`, un atributo de
  `Hallazgo`, o una clase propia. No es un hallazgo corriente: no tiene descripción ni
  localización, porque nadie llegó a mirar.
- **Cómo pesa.** La propuesta del viejo —lo más grave posible— tiene un argumento fuerte:
  si pesara poco, no auditarse saldría barato.
- **Si el reintento defensivo es parte del contrato** o detalle de implementación.

**Por qué importa más de lo que parece.** Es `PC-3` por otra puerta. `PC-3` dice que la
fiabilidad del Juez no está medida; esto dice que **ni siquiera sabemos representar que el
Juez no funcionó**. Lo primero es un hueco de medida; lo segundo, de vocabulario.

**Por qué es dominio:** toca `severidad` o `estado_de_hallazgo`, y `Hallazgo`.

---

## C-3 · La longitud no la comprueba nadie

**Hoy:** `Escena` tiene `longitud_objetivo` y **ninguna de las 16 invariantes la mira**.

**Lo que costó descubrirlo** está escrito junto a la Regla 2 de `Docs/verification.md`, con
sus números: un capítulo de 944 palabras, 256 por debajo del mínimo, aprobado por el
validador que en el intento anterior había pedido acortarlo.

**Qué hay que fijar:** una invariante nueva —sería **`INV-17`**, porque los identificadores
publicados no se renumeran— con su nivel, su severidad y su tipo. Tipo `regla` sin
discusión: la longitud es un número, y pedirle a un juez que compruebe un número es lo que
dejó el hueco. `main` le puso gravedad **media** y razonó por qué: *"un capítulo corto o
largo sigue siendo un capítulo utilizable"*, pero *"pesa más que una muletilla, porque el
rango es un requisito explícito de la configuración y no una opinión sobre la prosa"*.

**Por qué es dominio:** añade una invariante.

---

## C-4 · No hay forma de comparar dos borradores

**Hoy:** un hallazgo está abierto o no lo está. **No existe agregación**, así que no hay
manera de decir que el intento 3 es mejor que el 2.

**Lo que `main` decidió.** Puntuación ponderada por gravedad —`alta` 5, `media` 2, `baja`
1— y menor es mejor. Con una advertencia que le costó la decisión 9 de `DECISIONES.md`: al
comprobar que la herramienta de delegación **ignora `temperature` en silencio**, la
puntuación dejó de ser una medida estable y pasó a ser *"una comparación entre intentos de
una misma generación"*. `EJECUCION.md` §7 lo dice sin rodeos: solo tiene sentido comparar
*"dentro de un mismo capítulo de una misma generación"*.

**Qué hay que fijar:**

- **Si `severidad` gana un peso numérico**, y cuáles.
- **Qué alcance tiene la comparación.** Si copiamos los pesos sin copiar la advertencia,
  alguien comparará dos obras distintas y el número no significará nada.
- **Si `Rubrica` absorbe esto** o es aparte. `Rubrica` ya tiene `niveles`, pero es del Juez;
  esto agrega hallazgos de todos los verificadores.

**Por qué es dominio:** da significado numérico a un vocabulario controlado.

---

## C-5 · Las muletillas entre capítulos no se detectan

**Hoy:** `INV-15` mide distancia estilométrica **global** a las anclas, y el Verificador
mide repetición léxica dentro de una escena. Entre las dos queda un hueco: la frase que
aparece una vez por capítulo durante ocho capítulos no se desvía de las anclas ni se repite
dentro de ninguna escena.

**Lo que `main` decidió.** El validador de estilo devuelve un campo de más,
`nuevas_frases_recurrentes`, que **no es un problema** sino material para los capítulos
siguientes. El comentario de `src/puntuacion.py` explica el porqué:

> *"Se conserva tal cual porque un `PASA` también puede traerlo: la frase llamativa de hoy
> es la muletilla del capítulo ocho, y perderla aquí sería perder la única señal que detecta
> repeticiones ENTRE capítulos."*

**Qué hay que fijar:** dónde vive esa memoria. `AnclaDeEstilo` no sirve: es un pasaje
ejemplar fijo, y esto es una lista que crece. O `GuiaDeEstilo.tics_prohibidos[]` se alimenta
sola, o hace falta una clase.

**Por qué es dominio:** añade un atributo o una clase, y probablemente una invariante.

---

## Qué queda explícitamente fuera

- **Los cinco huecos de arquitectura.** Ver el reparto de abajo.
- **Las decisiones de recorte de `src/contexto.py`.** Cambian §2.4 de `SPEC-01`, que ya está
  aprobada, así que van en su propia revisión.
- **Los números**: pesos, topes de intentos, rangos de longitud.
- **Qué código de `main` se reutiliza.** Esta spec trae el **conocimiento** a los
  documentos; el código es otra decisión.

## El reparto, y por qué no cabe en una spec

| # | Hueco | Toca | Dónde va |
| --- | --- | --- | --- |
| 1 | Salida para una escena que falla mucho | `estado_de_escena`, `Escena`, `Borrador` | **`SPEC-10`** · `C-1` |
| 2 | El validador que no contesta | `severidad`, `Hallazgo` | **`SPEC-10`** · `C-2` |
| 3 | La longitud | Invariante nueva | **`SPEC-10`** · `C-3` |
| 4 | Comparar borradores | `severidad` gana peso | **`SPEC-10`** · `C-4` |
| 5 | Muletillas entre capítulos | Atributo o clase nueva | **`SPEC-10`** · `C-5` |
| 6 | Fijar el modelo del Juez durante una obra | `A-06` | `SPEC-11` |
| 7 | Tope global de llamadas al modelo | Presupuesto | `SPEC-11` |
| 8 | Vigilar la tendencia de los recortes | Traza e informe | `SPEC-11` |
| 9 | Aislamiento entre varios jueces | `A-06` | `SPEC-11` |
| 10 | El ensamblador del manuscrito no corrige nada | Proceso | `SPEC-11` |

Los cinco de arriba **no se pueden escribir sin tocar `Docs/definitions.md`**; los cinco de
abajo **no lo tocan en absoluto**. Meterlos juntos serían dos migraciones y dos documentos
normativos en un solo commit, que es justo lo que `VER-21` vigila.

## Qué gobierna esto

`EJECUCION.md` §4 reglas 1, 2 y 3 y §7 de la rama `main`; `DECISIONES.md` decisión 9 y
hallazgo 11; `src/puntuacion.py`; y de esta línea, `PC-3`, la Regla 2 de
`Docs/verification.md`, `INV-15` y `estado_de_escena`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | `C-1`: ¿existe rendición, o una `bloqueante` detiene para siempre? | Sin propuesta. Es la diferencia filosófica entre los dos contratos y la decides tú |
| 2 | `C-2`: ¿la ausencia de veredicto es un valor de enumeración, un atributo o una clase? | Un valor de `estado_de_hallazgo`. Es el cambio más pequeño que lo hace expresable, y `SPEC-02` ya añadió `descartado` por un motivo parecido |
| 3 | `C-2`: ¿pesa lo máximo posible? | Sí. Si no auditarse saliera barato, la auditoría sería decorativa — que es el argumento literal de `main` |
| 4 | `C-3`: ¿`INV-17` es `mayor` o `menor`? | `menor`, siguiendo a `main`: un capítulo fuera de rango es utilizable. Pero con `SPEC-04`, un `menor` ya no bloquea el cierre de capítulo, así que un capítulo corto entraría firmado. Merece mirarse |
| 5 | `C-4`: ¿los pesos son `alta` 5 / `media` 2 / `baja` 1? | Sin propuesta: son números de `main` que funcionaron ahí, y copiarlos sin medir es heredar una calibración de otro sistema |
| 6 | ¿`SPEC-11` se escribe ya, o después de aprobar esta? | Después. Si `C-1` se resuelve como «no hay rendición», el hueco 7 —tope global de llamadas— cambia de forma |
