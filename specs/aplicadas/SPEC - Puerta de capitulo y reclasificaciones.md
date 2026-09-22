---
id: SPEC-04
titulo: La puerta de cierre de capítulo, y tres invariantes que eran comparaciones
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: 2df8e7e
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-04 — Puerta de capítulo y reclasificaciones

## Por qué las cuatro cosas van en una sola spec

Son **el mismo tipo de cambio sobre el mismo documento**: añaden o corrigen metadatos de
`Docs/definitions.md` —un atributo, una enumeración y la columna `Tipo` de tres
invariantes—. Partirlas en dos specs serían dos commits sobre la misma tabla y, por
`VER-21`, dos migraciones.

Lo que no comparten es el origen, y conviene no mezclarlo:

- **`D4-9`** nace de una decisión ya tomada que se quedó a medias. Al decidir que un
  hallazgo `mayor` no bloquea la escena, la salvaguarda fue que bloqueara el **cierre del
  capítulo**. Esa puerta no existe en ningún documento, así que hoy la decisión está
  aplicada a medias: se quitó el bloqueo de escena y no se puso el de capítulo, y un
  hallazgo `mayor` se quedó **sin ninguna consecuencia**.
- **Las tres reclasificaciones** nacen de un patrón que se repitió: hay invariantes
  clasificadas como `juez_llm` que son **comparaciones disfrazadas de juicio**. Se pide
  criterio a un modelo para hacer una resta.

---

# 1. La puerta de cierre de capítulo

## C-1 · `Capitulo` gana un estado

Hoy `Capitulo` tiene `id`, `orden`, `gancho_de_cierre` y `escenas[]`, y **ningún atributo
de estado**. `estado_de_escena` es de escena y no le sirve.

| Clase | Atributo nuevo | Gobernado por |
| --- | --- | --- |
| `Capitulo` | **estado** | `estado_de_capitulo` |

| Enumeración nueva | Atributos que la usan | Valores |
| --- | --- | --- |
| `estado_de_capitulo` | `Capitulo.estado` | `abierto`, `cerrado` |

Dos valores y no más. Un capítulo en curso y un capítulo firmado: no hace falta un estado
intermedio porque el cierre es instantáneo, lo dispara una persona y no hay trabajo
asíncrono de por medio.

## C-2 · La condición de cierre

**Un capítulo se puede cerrar cuando ninguna escena suya tiene un hallazgo `mayor`
abierto.** En detalle:

| Severidad | ¿Bloquea el cierre? | Qué pasa |
| --- | --- | --- |
| `bloqueante` | No llega a plantearse | Una escena con un `bloqueante` abierto no está `consolidada`, así que el capítulo no está completo |
| `mayor` | **Sí** | Hay que resolverlo o descartarlo antes de firmar |
| `menor` | **No** | Se **listan** al firmar, para que quien cierra sepa qué deja pasar |

Y `estado_de_hallazgo`: **solo `abierto` cuenta**. `resuelto` y `descartado` no bloquean —
para eso existe `descartado`, que `SPEC-02` añadió precisamente para poder cerrar un falso
positivo sin fingir que se corrigió.

**Por qué los `menor` no bloquean.** Si lo hicieran tendríamos otra vez una escala de tres
niveles con dos comportamientos reales, que es exactamente lo que se resolvió al decidir
que `mayor` no detiene la escena. Una escala cuyos valores no producen comportamientos
distintos es una etiqueta, no un control. Listarlos al firmar conserva la información sin
convertirlos en un segundo `mayor`.

## C-3 · Quién dispara el cierre

`Docs/architecture.md` gana una fila en su tabla de transiciones:

| Transición | Quién la dispara | Condición |
| --- | --- | --- |
| `abierto` → `cerrado` | **Cliente de la API** | Todas las escenas del capítulo están `consolidada` y ninguna tiene un hallazgo `mayor` abierto |

Es la **segunda puerta con firma humana** del sistema, junto con la aceptación de escena
de `A-04`. Y es la que da sentido a la primera: al quitar el bloqueo por escena, el control
no desapareció, se movió al capítulo, que es donde una persona puede juzgar si el conjunto
se sostiene.

## Qué desbloquea

| Se desbloquea | Cómo |
| --- | --- |
| **`D4-9` de `REV-01`** | Era el último bloqueante de `SPEC-01` |
| **La salvaguarda de la decisión de severidad** | Deja de estar aplicada a medias: un hallazgo `mayor` vuelve a tener consecuencia |
| **Un requisito y un endpoint en `SPEC-01`** | No entran aquí. Vienen después, cuando esta spec se apruebe |

## Migración

Ninguna hoy. Con datos, `capitulo` gana una columna con valor por defecto `abierto`, que
es la migración más barata que existe. **Ya no es gratis.** Desde `PLAN-01` A3 existe `backend/app/commons/db/` con migraciones versionadas y validación de secuencia, así que un atributo obligatorio nuevo necesita **su migración numerada en el mismo commit**. Las versiones no admiten huecos ni repeticiones: una publicada no se borra ni se renumera.

---

# 2. Tres invariantes que son comparaciones

El argumento es común a las tres: **están clasificadas como `juez_llm` y su núcleo es
aritmética o comparación de identificadores.** Pedir criterio a un modelo para hacer una
resta es caro, lento, no reproducible, y convierte un sí o no en una opinión.

Ninguna se convierte en `regla` a secas: las tres pasan a **`regla` con el juez como
desempate**, porque a todas les queda una parte que solo se ve leyendo.

## C-4 · `INV-14` — la monotonía de una serie numérica

*"Cada deterioro es monótono, o su reversión está justificada en el texto."*

`Deterioro.serie_por_escena` es una serie de números. **Comparar elementos consecutivos es
una resta.** Lo único que necesita criterio es la cláusula *"o su reversión está
justificada"*, y solo se consulta **cuando la serie no es monótona**.

| Hoy | Después |
| --- | --- |
| `tipo = juez_llm` | `tipo = regla`, con juez de desempate solo ante una reversión |

Es el caso más claro de los tres: hoy se pide un juez LLM para comprobar si una lista de
números decrece.

## C-5 · `INV-11` — un conteo contra el brief

*"El grado de explicación acumulado no supera el fijado en el brief."*

`Amenaza.grado_de_explicacion_permitido` es un valor del brief y lo acumulado es **cuántos
`HechoCanonico` sobre la amenaza están revelados al lector**. Con el registro de
conocimiento eso es un conteo sobre identificadores.

| Hoy | Después |
| --- | --- |
| `tipo = juez_llm` | `tipo = regla`, con juez de desempate para las revelaciones implícitas |

Lo irreducible: decidir si una revelación **implícita** cuenta. El texto puede dar a
entender algo sin establecerlo como hecho, y eso no está en ningún registro.

## C-6 · `INV-03` — comparación de identificadores, y la que más importa

*"Ningún personaje actúa sobre un hecho que no conoce en `t`."*

**Es la única puerta `bloqueante` del sistema que hoy depende de un juez cuya fiabilidad no
está medida.** Reclasificarla es lo que más encoge ese punto ciego.

La parte determinista es mayor de lo que parecía, y **creció con `SPEC-03`** al convertir
`RegistroDeConocimiento.fuente` en una referencia:

- Todo `HechoCanonico` citado en una revelación tiene su `escena_de_establecimiento`, y esa
  escena es anterior en `t_fabula`. Revelar antes de establecer es un fallo de orden: dos
  números.
- Si el delta declara que un personaje revela o usa un hecho, tiene que existir la fila
  `(sujeto, hecho)` con `desde_escena ≤ t`. Sin fila, o con `grado = ignora`, es violación
  sin discusión.
- **Con `fuente` como referencia**, además se comprueba que el conocimiento tenga un
  origen alcanzable: un personaje que sabe algo por una escena en la que no estuvo es un
  fallo detectable.

| Hoy | Después |
| --- | --- |
| `tipo = juez_llm`, severidad `bloqueante` | `tipo = regla`, severidad `bloqueante`, con juez de desempate |

Lo irreducible: decidir que el personaje **actúa sobre** el hecho. El delta declara lo que
el Escritor dijo que pasó; la invariante habla de lo que el texto muestra. Un personaje
puede esquivar una trampa sin que el delta registre ninguna revelación, y eso solo se ve
leyendo.

**El juez pasa de primera línea a desempate**, y eso cambia dónde hace daño su fiabilidad
desconocida: ya no decide si una escena se detiene, solo los casos que la regla no vio.

## Qué desbloquea

| Se desbloquea | Cómo |
| --- | --- |
| **`PC-3` encoge mucho** | La única puerta bloqueante que dependía de un juez pasa a depender de una regla |
| **`VER-35`** | *"Cuando el Juez marca `INV-03` y la regla no ve nada, gana el correcto"* deja de ser hipotético: con las dos ejecutándose, la discrepancia se puede medir |
| **El desempate juez contra regla** | Esa decisión abierta de `Docs/definitions.md` pasa de teórica a operativa: ahora hay dos resultados que comparar |

## Migración

Ninguna hoy: es la columna `Tipo` de tres filas de una tabla. Con código escrito, sería
mover tres comprobaciones del cliente del modelo al verificador de reglas.

---

# 3. Qué queda explícitamente fuera

- **El `RF` y el endpoint de cierre de capítulo en `SPEC-01`.** Vienen después, cuando
  esta spec se apruebe. Aquí solo se define el dominio.
- **Reclasificar `INV-10`.** Admite un filtro determinista —si la escena invoca la amenaza
  y el delta no registra el coste, es señal— pero conserva una parte central que solo el
  juez resuelve. No es una comparación disfrazada y se queda como está.
- **Qué pasa con un capítulo cerrado al que luego se le encuentra un defecto.** El cierre
  es irreversible en este diseño; si hace falta reabrirlo, es otra decisión.
- **Los umbrales** de cualquier validador que estos cambios desbloqueen.

# 4. Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿`estado_de_capitulo` tiene dos valores o hace falta un intermedio? | Dos. El cierre es instantáneo y lo dispara una persona |
| 2 | ¿Se puede reabrir un capítulo cerrado? | Fuera de alcance. Si se decide que sí, es un valor más y una transición más |
| 3 | ¿El cierre de capítulo exige que **todas** sus escenas estén `consolidada`? | Sí. Un capítulo con escenas a medias no es un capítulo |
| 4 | ¿Las tres reclasificaciones van juntas o por separado? | Juntas. Comparten argumento y tabla |
| 5 | ¿`INV-03` conserva la severidad `bloqueante` al pasar a `regla`? | Sí. Lo que cambia es quién decide, no cuánto pesa |

Las cinco se respondieron con la propuesta el 2026-09-22, al aprobar.

# 5. Qué se tocó al aplicarla

| Documento | Cambio |
| --- | --- |
| `Docs/definitions.md` | `Capitulo.estado` y la enumeración `estado_de_capitulo`; la columna `Tipo` de `INV-03`, `INV-11` e `INV-14`; dos notas bajo la tabla de invariantes —el escalado al juez y que `INV-03` conserva su severidad—; la decisión abierta del desempate, que deja de ser teórica |
| `Docs/architecture.md` | La tabla de transiciones de capítulo; `INV-03` pasa del Juez de rúbrica al Verificador de reglas y el Juez queda con `INV-10` más los tres desempates; la sección de severidad explica ya cuál es la consecuencia de un `mayor` |
| `Docs/verification.md` | `PC-3` encoge por segunda vez; `VER-06`, `VER-11` y `VER-35` cambian de criterio; `INV-03` entra en la tabla de juicio-que-era-comparación; se cierran dos decisiones abiertas |
| `specs/SPEC - Backend.md` | `RF-26` y §2.4 dicen ya que el orden de recorte opera sobre **bloques** y no sobre niveles |
| `.agents/skills/harness-invariantes/SKILL.md` | El recuento pasa de doce reglas y cuatro jueces a quince y uno |

## Lo que la spec no previó

**`tipo_de_verificador` no tiene un valor para "regla con desempate".** La spec escribe
*"pasan a `regla` con el juez como desempate"*, pero la enumeración tiene tres valores
—`regla`, `juez_llm`, `humano`— y ninguno significa eso. Se aplicó la lectura literal
—`tipo = regla`— y el escalado quedó documentado en prosa bajo la tabla de invariantes:
**el tipo dice quién decide primero**. Añadir un cuarto valor sería un cambio de
vocabulario controlado, y eso es otra spec.

**La tabla de transiciones de `Docs/architecture.md` es de `estado_de_escena`.** `C-3`
pedía "una fila" en ella, pero `abierto` y `cerrado` no pertenecen a ese vocabulario, así
que la fila fue a una tabla propia inmediatamente debajo. Mezclarlas invitaría a comparar
valores de dos enumeraciones distintas.

**`D4-9` se cierra a medias, y estaba previsto.** La tabla "Qué desbloquea" dice que era el
último bloqueante de `SPEC-01`, y lo era **como decisión**: ya no falta acordar nada. Pero
el enunciado de `D4-9` tenía dos mitades, y la segunda —*"`SPEC-01` no tiene ningún
requisito de cierre de capítulo"*— sigue en pie, porque §3 la dejó fuera a propósito.
`D4-9` baja de bloqueante a pendiente: ya no falta una decisión, falta escribir un `RF`.

**`PC-3` encoge pero también se desplaza.** Al dar consecuencia al `mayor`, `INV-10` —la
única invariante que sigue siendo del Juez— pasa a bloquear el cierre de capítulo. La
fiabilidad no medida del Juez deja de poder detener una escena y empieza a poder detener
una puerta humana. Es un punto ciego más pequeño, pero no el mismo.
