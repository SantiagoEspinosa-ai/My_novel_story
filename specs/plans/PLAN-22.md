---
id: PLAN-22
spec: SPEC-22
titulo: Implementación del frontend de lectura y del contrato congelado
estado: en_revision
aprobada_por: ""
fecha_aprobacion: ""
fecha: 2026-09-24
version: 1
---

# PLAN-22 — La lectura web y el contrato congelado

Cómo se construye `SPEC-22`. Cada paso empieza por la prueba que falla, deja la suite en verde
(`python -m pytest app -q` desde `backend/` y, desde E6, `npm test` desde `frontend/`) y se puede
commitear solo. **Ningún paso llama al modelo real**, salvo E20b, que gasta dinero y necesita un sí
explícito. Se añade por ruta, nunca con `git add -A`.

## Un día, y en este orden

| Bloque | Pasos | Qué deja | Espera a |
| --- | --- | --- | --- |
| **1 · La lectura** | E1–E13 | Contrato congelado, portada, índice, capítulos con estado y hallazgos, fichas, Playwright MCP e inspección real | E5 espera a `PLAN-27` E2–E3 para los nombres y los presentes; sin ellos sale honesta, con `id` y «no declarado» |
| **2 · La petición de cambio** | E14–E18 | Selección, capítulos antes de tocar, trabajo, marcas de «cambió» y la versión anterior navegable | Los endpoints de `PLAN-23` A5 y A7 |
| **3 · La novela de ejemplo** | E19–E20 | Docs al día; la web apuntando a la novela real | `PLAN-27` E10 |

**Si el día se acaba, el corte está después de E13.** Ningún paso del bloque 2 se intercala en el
bloque 1. El frontend se construye primero contra fixtures derivados del congelado (`NF-04`),
porque no hay ninguna novela regalo completa. La web de verdad se inspecciona sobre una base con
datos inventados (E11) y más tarde sobre la novela de ejemplo (E20).

## Reparto con `PLAN-23`

| Pieza | De quién |
| --- | --- |
| La versión de obra con identidad, la reverificación, qué capítulos se tocan, la marca de «cambió», la medida del arrastre y el worker de la regeneración | `PLAN-23` |
| **Los endpoints de la petición** (`POST /obras/{id}/cambios/propuesta`, `POST /obras/{id}/cambios`) **y de las versiones** (`GET /obras/{id}/versiones`, `…/{numero}`) | `PLAN-23` (A5, A7). La petición recibe un **hecho**, no un ancla de texto |
| El contrato congelado y su validador; cada endpoint de `PLAN-23` lo actualiza en su commit | Este plan (E1, antes que `PLAN-23` A5) |
| Los endpoints de lectura (`features/lectura/`), incluido **qué hechos usa una escena**, que es lo que la página ofrece al lector cuando selecciona un fragmento | Este plan (E3–E5, E14) |
| Todo `frontend/`, `.mcp.json` y la inspección real | Este plan |

Con ese reparto, **`SPEC-22` `DA-6` (el ancla del fragmento) deja de bloquear**: la selección vive
en la página y lo que viaja al backend es el hecho elegido.

**Las migraciones chocan de número.** Hoy la última es la **10**. E14, `PLAN-27` E2 y `PLAN-23`
añaden más. Se usa el número siguiente al que haya **en el momento del commit**, y
`validar_secuencia` caza un número repetido.

## Lo que se encontró al preparar el plan

1. **§3.2.2 de `SPEC-22` está desfasada.** Dice *«Seis rutas montadas en total»* y que
   `GET /trabajos/{id}` **falta**. En el código, `orquestacion/router.py` la monta, y también
   `POST /obras/{id}/entregar` y las siete de `entrevista/router.py`. Cambio documental, en E19.
2. **`SPEC-22` sigue citando a `SPEC-23` en revisión.** `DA-1` asume el umbral «~2 / ~8» y que
   `RF-50`…`RF-55` no se implementan. `SPEC-23` está `aprobada` en su v2, con la regla ≤ 3 → `S-1`,
   > 3 → `S-2`, y fija que la interfaz de la petición es la web. La interfaz no depende de la salida:
   `RF-50` deja al backend decidir qué capítulos se tocan → cuestión abierta 1.
3. **`DA-6` lo resuelve el reparto** (ver arriba).
4. **El ejemplo del enunciado no es un hecho.** `EXAMEN.md` dice *«seleccionar un fragmento o un
   hecho»*, y *«el perro se llama Nala»* cambia `Personaje.nombre_canonico`, no un `HechoCanonico`.
   Es la cuestión abierta 1 de `PLAN-23`.
5. **«Hallazgo abierto» no significa lo mismo en la spec y en el código.** `SPEC-22` dice
   `estado = abierto`; el código cuenta también `sin_veredicto`, que es lo que pide
   `docs/definitions.md`. La web **pinta cada hallazgo con su `estado_de_hallazgo`**. `SPEC-22` se
   corrige en E19.
6. **`RF-35` y `lectura/vista.py` se contradicen.** `vista.consumo` devuelve `"sin medir"` en el
   sitio de un número. *«Sin medir»* es presentación: el contrato lleva `null` y la interfaz lo
   pinta. Este plan no expone `consumo`.
7. **Hay campos en esquemas que `docs/definitions.md` no define**: `se_acepto_rindiendose` y
   `hallazgos_abiertos` (`vista.py`), y `CapituloDelPlan.titulo`. `Capitulo` no tiene `titulo`; el
   índice dice «Capítulo N», como `PLAN-27`.
8. **No hay partes.** `Parte` está en `docs/definitions.md`, pero no hay tabla `parte` y el plan de
   la novela regalo no las declara → cuestión abierta 3.
9. **El congelado de hoy diría poco.** Seis rutas de `orquestacion/router.py` no tienen
   `response_model`. E14 le da forma a `GET /trabajos/{id}`, porque la petición la necesita.
10. **Nadie consume la cola de trabajos**: el worker es de `PLAN-23`.
11. **La promesa de `PLAN-28` `D-2` no se cumple para todas las delegaciones.** Solo las
    delegaciones con herramientas llevan `--strict-mcp-config`, y todas arrancan en la raíz. Con un
    `.mcp.json` en la raíz, el Planificador, el Revisor, el Resumidor o el Juez podrían cargar el
    browser MCP. El hook negaría la llamada, pero el servidor arrancaría igual → E12.
12. **El validador del contrato va en `harness/documentos/`**, que ya está declarada.
13. **Las fichas ordenan los capítulos por `id`, no por orden de lectura** (`cronologia/consultas.py`).
    Sale bien porque los `id` llevan ceros: Regla 11. La web y el PDF ordenan por `capitulo.orden`.
14. **`G-04` y `PLAN-27` dicen cosas distintas de `ocurre_en`.** Se sigue al código (`PLAN-27`), con
    una prueba negativa en E5.
15. **`alias`, `rol_dramatico` y `atmosfera` viajan nulos**: se pintan «sin dato», no «ninguno».
16. **No se usan bases reales.** Pueden contener datos de un destinatario real. La inspección va
    sobre datos inventados (E11) y, después, sobre la novela de ejemplo, que también es de datos
    inventados.
17. **`A-04` se queda sin interfaz**: este plan no cierra ninguna puerta desde la web.
18. **`EX-04` se cierra solo a medias.** El enunciado pide que cada validador tenga nombre, punto
    del harness y score en Langfuse, y que el error visual *«vuelva al writer»*. Este plan cubre la
    configuración y el uso real documentado → cuestión abierta 5.
19. **`PLAN-27` E2–E3 no están hechos.** E5 depende de ellos.
20. **La API ya persiste entre peticiones** desde `F-70`; E11 cuenta con ello.

## Decisiones que se aprueban con este plan

- **DP-1. El congelado vive en `contrato/openapi.json`**, con las claves ordenadas. Lo genera y lo
  compara `harness/documentos/contrato.py`. Corre en local: no hay CI.
- **DP-2. La lectura tiene rutas propias en `features/lectura/`.** `GET /obras/{id}` se queda como
  la respuesta del alta.
- **DP-3. El frontend se sirve con Vite, y el proxy de Vite manda `/api` a `uvicorn`.** Es la web de
  verdad, no una exportación estática.
- **DP-4. `VER-17` se cierra con Steiger**, el linter oficial de FSD.
- **DP-5. La regla del texto elegido y el cálculo de apariciones suben a `commons/obra/`**, porque
  los necesitan la lectura y `manuscrito/`. El primero de los dos planes que llegue lo sube.
- **DP-6. Toda delegación con agente lleva `--strict-mcp-config`**, tenga o no herramientas
  (hallazgo 11).

## Lo que falta en `docs/definitions.md`, y va allí primero

| Qué hace falta | Quién | Cuándo |
| --- | --- | --- |
| Que la rendición llegue resuelta (`RF-40`) | Este plan | E2 |
| La lista de hallazgos abiertos de una escena (`RF-39`) | Este plan | E2 |
| Los capítulos donde aparece una entidad, derivados de `participa_en` y `ocurre_en` (`RF-44`) | Este plan | E2 |
| La versión de obra, la petición, la marca de «cambió» y el verde heredado | `PLAN-23` A0 | Antes de E15 |
| El número de capítulos declarado, para `RF-42` | — | Cuestión abierta 4 |

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `contrato/openapi.json` (nuevo) | El congelado (DP-1) |
| `harness/documentos/contrato.py`, `tests/` (nuevos) | Generar, comparar y comprobar el significado |
| `backend/app/features/lectura/` | `router.py`, `schemas.py`, `service.py`, `repository.py` (nuevos) y `vista.py` |
| `backend/app/commons/obra/` (nuevo) | `texto.py` y `apariciones.py` (DP-5) |
| `backend/app/commons/modelo/proveedor.py` | DP-6 |
| `backend/app/main.py` | `include_router` de la lectura |
| `backend/semilla_lectura.py` (nuevo) | Una obra con datos inventados, sin modelo |
| `.mcp.json` (nuevo) | Playwright MCP |
| `frontend/` (nuevo) | `src/app`, `src/pages/{portada,indice,capitulo,escena,fichas}`, `src/entities/escena`, `src/features/pedir-cambio` (E16), `src/shared/{api,ui}` |

## Pasos

### E1 · El contrato congelado y su validador (`RF-31`, `RF-32`, `RF-33`)

`contrato.py` genera `app.main.app.openapi()` con las claves ordenadas y lo compara con
`contrato/openapi.json`. Cada diferencia sale con **operación**, **campo** (puntero JSON) y
**dirección** (añadido, quitado o cambiado). Con `--escribir` regenera el congelado; sin él, sale con
1 si hay diferencias.

**Prueba que falla primero:** `test_quitar_un_campo_de_una_respuesta_falla_y_dice_operacion_campo_y_direccion`.
Además `test_anadir_una_ruta_es_una_diferencia_y_no_un_aviso`,
`test_dos_generaciones_seguidas_son_identicas_byte_a_byte` y
`test_el_congelado_del_repositorio_coincide_con_el_backend_de_hoy`.

**Abre** `VER-102`.

### E2 · Lo que el contrato significa (`RF-34`, `RF-35`, `RF-57`)

Primero `docs/definitions.md`: las tres primeras filas de la tabla de arriba, como vistas derivadas
que no se persisten. Después el validador comprueba que los estados son `enum` con los literales de
`docs/definitions.md`, que ningún campo admite a la vez un número y una cadena, y que ningún nombre
de `config/sistema.json` aparece en el congelado.

**Prueba que falla primero:** `test_un_estado_como_cadena_libre_en_el_congelado_es_un_fallo`. Además
`test_un_campo_que_admite_numero_o_cadena_es_un_fallo`,
`test_ningun_campo_del_congelado_se_llama_como_la_configuracion_del_sistema` y
`test_los_literales_de_cada_enum_son_los_de_definitions`.

**Abre** `VER-103`.

### E3 · Portada e índice por la API (`RF-37`, `RF-38`, `RF-40`, `RF-46`)

`GET /obras/{id_obra}/indice` devuelve la obra (`id`, `titulo`, `dedicatoria`) y sus capítulos **por
`capitulo.orden`**, cada uno con su `estado` y sus escenas en orden; cada escena con su `estado`, la
rendición resuelta y sus hallazgos abiertos, cada uno con su `estado`.

**Prueba que falla primero:** `test_el_indice_de_una_obra_de_dos_capitulos_pone_cada_escena_bajo_el_suyo_y_en_orden`.
Además `test_el_indice_ordena_por_capitulo_orden_y_no_por_id`,
`test_con_dos_obras_en_la_base_el_indice_no_mezcla_capitulos`,
`test_un_id_de_obra_pedido_como_capitulo_da_404` y
`test_la_portada_trae_la_dedicatoria_de_la_obra_y_nula_si_no_hay`.

**Abre** `VER-104`.

### E4 · La lectura de un capítulo y de una escena (`RF-39`, `RF-40`, `RF-41`)

`commons/obra/texto.py` guarda la regla del texto elegido, con su `version`. Rutas
`GET /capitulos/{id_capitulo}` y `GET /escenas/{id_escena}`.

**Prueba que falla primero:** `test_ninguna_escena_de_la_lectura_de_un_capitulo_sale_sin_estado_ni_hallazgos`.
Además `test_el_texto_de_cada_escena_es_byte_a_byte_el_del_borrador_elegido_con_su_version`,
`test_una_escena_planificada_sale_con_texto_nulo_y_su_estado`,
`test_un_sin_veredicto_viaja_con_su_estado_y_no_como_abierto`,
`test_una_rendida_consolidada_sigue_saliendo_rendida` y
`test_get_escena_devuelve_lo_mismo_que_la_escena_dentro_del_capitulo`.

**Abre** `VER-105` y **amplía** `VER-60`, en la misma ampliación que `PLAN-27`.

### E5 · Las fichas (`RF-43`, `RF-44`) *(completa con `PLAN-27` E2–E3)*

`commons/obra/apariciones.py` calcula los capítulos de un `Personaje` por `participa_en` y los de un
`Lugar` por `ocurre_en`, **por `capitulo.orden`**. `GET /obras/{id_obra}/fichas`. Sin `PLAN-27` E2
el nombre viaja nulo; sin E3, los presentes viajan nulos: «no declarado», nunca «nadie».

**Prueba que falla primero:** `test_un_personaje_enlaza_los_capitulos_donde_participa_y_una_mencion_no_cuenta`.
Además `test_un_lugar_enlaza_los_capitulos_donde_ocurre_una_escena` (con su negativo de otra obra),
`test_presentes_sin_declarar_viajan_nulos_y_no_como_lista_vacia`,
`test_una_entidad_sin_nombre_guardado_viaja_con_nombre_nulo` y
`test_los_capitulos_de_una_ficha_van_en_orden_de_lectura_y_no_de_id`.

**Comparte** la fila que abre `PLAN-27`.

### E6 · El andamiaje del frontend, contra el congelado (`NF-01`, `NF-04`, `NF-05`, `NF-07`)

Vite, React y TypeScript, con Vitest, Testing Library, React Router, `openapi-typescript`
(`src/shared/api/contrato.ts` desde `../contrato/openapi.json`), Ajv y Steiger. **Ninguna versión
está comprobada** y `npm install` necesita red. `cliente.ts` recibe `fetch` inyectado; `tests/setup.ts`
sustituye el `fetch` global por uno que falla si se le llama.

**Prueba que falla primero:** `fixtures.test.ts › cada fixture valida contra su esquema del
congelado`. Además `› toda fixture con capítulos tiene al menos dos en una obra`,
`frontera.test.ts › ningún paquete es un cliente de base de datos`, `› solo shared/api llama a
fetch`, `› una prueba que llama a fetch sin inyectarlo falla` y `npx steiger src` sin violaciones.

**Abre** `VER-106`.

### E7 · La escena con su estado, siempre (`RF-39`, `RF-40`)

`EscenaConEstado` no pinta el texto sin su `estado` y sin su lista de hallazgos.
`shared/ui/sin-dato` pinta «sin dato» si el valor es nulo, y lo distingue de una lista vacía.

**Prueba que falla primero:** `EscenaConEstado › no pinta el texto si falta el estado o la lista de
hallazgos`. Además `› una rendida se ve distinta de una aceptada`, `› un sin_veredicto se pinta como
sin veredicto y no como abierto` y `› una escena sin texto pinta su estado y no un hueco`.

**Cierra** `VER-18`.

### E8 · Portada e índice (`RF-46`, `RF-38`)

El índice **no reordena nada**. Cada capítulo enlaza con su `id` de capítulo.

**Prueba que falla primero:** `Indice › pinta los capítulos y las escenas en el orden de la
respuesta`. Además `› cada capítulo enlaza con su id de capítulo` y `Portada › pinta la dedicatoria
de la obra y, sin ella, solo el título, sin texto de relleno`.

**Abre** `VER-107`.

### E9 · Lectura continua y vista de escena (`RF-39`, `RF-41`)

**Prueba que falla primero:** `Capitulo › cada escena de la lectura continua lleva su estado y sus
hallazgos`. Además `› no junta textos: una escena, un bloque` y `› el texto se pinta tal como llega`.

### E10 · Fichas (`RF-43`, `RF-44`)

**Prueba que falla primero:** `Fichas › cada ficha enlaza exactamente los capítulos que trae la
respuesta, ni uno más`. Además `› un nombre nulo pinta el id y lo dice`, `› alias, rol y atmósfera
nulos pintan «sin dato»` y `› presentes sin declarar se dicen «no declarado»`.

### E11 · La web de verdad, sobre una base con datos inventados (DP-3)

`semilla_lectura.py` monta una obra de **al menos dos capítulos**, sin modelo, con `novela.montar` y
una ficha y un plan **inventados y marcados como tales**, por las funciones del repositorio y nunca
con un `UPDATE` a mano. Deja escenas `consolidada`, `aceptada_por_rendicion`, `generada` con
hallazgos y `planificada`.

**Prueba que falla primero:** `test_la_semilla_deja_una_obra_de_dos_capitulos_que_la_api_lee_entera`,
con `HARNESS_BASE` y `TestClient` como hace `test_arranque.py`. Además
`test_la_semilla_no_escribe_en_una_base_que_ya_tiene_esa_obra` y `cliente.test.ts › todas las rutas
van bajo /api`.

### E12 · Playwright MCP en el repositorio, y fuera de toda delegación (DP-6)

`.mcp.json` en la raíz, con un solo servidor, el de Playwright. El paquete y la orden están **sin
comprobar aquí**, y también si hace falta instalar un navegador aparte. `proveedor` añade
`--strict-mcp-config` a toda delegación con agente.

**Prueba que falla primero:** `test_toda_delegacion_con_agente_lleva_strict_mcp_config_aunque_no_tenga_herramientas`.
Además `test_el_mcp_json_declara_un_solo_servidor_y_es_el_del_browser` y
`test_policy_niega_a_cualquier_agente_una_tool_del_browser`, que pasa desde el primer momento y queda
como regresión.

**Abre** `VER-108`.

### E13 · La inspección real con Playwright MCP, y su registro

Backend con `HARNESS_BASE` sobre la base de E11 y frontend con `npm run dev`. Una sesión de Claude
Code, con el MCP, abre la portada, el índice, cada capítulo y las fichas, y sigue cada enlace.

**No es una prueba: es una inspección (clase I).** Cada error visual se registra como el siguiente
`F-xx` libre en `docs/verification.md` y se devuelve a quien toca: un error de pintado, al frontend,
con la prueba roja en el commit que lo arregla; un error del texto, al Escritor **solo si lo cubre
una `INV-xx`**. `docs/proceso/claude-code.md` § "Browser MCP" dice qué inspeccionó, qué detectó y qué
cambio provocó, con su commit.

**Abre** `VER-109`. **Cierra la mitad de `EX-04`.**

### E14 · Lo que la página necesita para pedir un cambio

- **`GET /escenas/{id}/hechos`**: los hechos que usa una escena, de `uso_de_hecho`, con su
  enunciado. Es lo que la página ofrece al lector cuando selecciona un fragmento.
- **`GET /trabajos/{id}` gana `response_model`** (hallazgo 9).
- El congelado, al día.

**Prueba que falla primero:** `test_los_hechos_de_una_escena_son_los_de_sus_usos_y_de_su_obra`.
Además `test_una_escena_sin_usos_devuelve_una_lista_vacia_y_no_nula` y
`test_el_trabajo_tiene_forma_en_el_congelado`.

**Abre** `VER-110`.

### E15 · Leer una versión *(consume `PLAN-23` A5)*

Las rutas de lectura aceptan la versión como parámetro; cada capítulo lleva la marca de `PLAN-23` y
cada escena, su `estado_de_verificacion`.

**Prueba que falla primero:** `test_la_version_anterior_se_sigue_leyendo_entera`, con dos versiones
sembradas por el repositorio de `PLAN-23`. Además `test_cada_capitulo_trae_su_marca_de_cambio_y_no_se_calcula_aqui`
y `test_una_escena_con_verde_heredado_no_sale_como_verificada`.

**Amplía** `VER-104` y `VER-105`.

### E16 · Pedir un cambio desde la página (`RF-47`, `RF-49`, `RF-50`, `RF-51`, `RF-55`)

`features/pedir-cambio`, desde `pages/capitulo` y `pages/escena`. La selección ofrece los hechos de
esa escena (E14); el lector elige uno y escribe el cambio. Antes de confirmar se enseñan los
capítulos que se tocarían (`PLAN-23` A7), con la promesa de `SPEC-23` `D-3` y **su punto ciego**.
Después se sigue el trabajo.

**Prueba que falla primero:** `PedirCambio › manda el hecho elegido y el texto del lector, y ningún
capítulo`. Además `› no ofrece confirmar hasta haber enseñado los capítulos`, `› la promesa sale con
su punto ciego` y `› sigue el trabajo y, si falla, enseña su motivo`.

**Abre** `VER-111`.

### E17 · Las marcas de cambio y la versión anterior (`RF-52`, `RF-53`, `RF-54`)

**Prueba que falla primero:** `Indice › marca como cambiados exactamente los capítulos que marca la
respuesta, sin comparar textos`. Además `› la versión anterior se navega entera` y
`EscenaConEstado › un verde heredado no se pinta como verificado`.

**Abre** `VER-112`.

### E18 · Inspección real de la petición

La semilla gana una segunda versión, sembrada con el repositorio de `PLAN-23` y sin modelo. El MCP
recorre la petición: selección, capítulos, confirmación, marcas y versión anterior. **Amplía**
`VER-109`.

### E19 · `docs/` y spec al día

`docs/architecture.md`, `docs/verification.md` (filas nuevas y `MF-29`), `docs/cobertura-examen.md`
(`EX-04`, `EX-13`, `EX-14`), `AGENTS.md` (`frontend/`, `contrato/`, `.mcp.json`), `CLAUDE.md`
(`npm install`, `npm test`, `npx steiger src`, el validador del contrato y la semilla) y `SPEC-22`
(hallazgos 1, 2 y 5, como cambio documental). `SPEC-22` pasa a `aplicada` **solo** con
`RF-50`..`RF-55` hechos y E20a.

### E20 · La novela de ejemplo en la web

- **E20a** (sin coste, espera a `PLAN-27` E10): la web apunta a la base de la novela de ejemplo y se
  repite la inspección de E13.
- **E20b** (gasta dinero; sí explícito): la demo, una petición real desde la página. Es la misma
  ejecución que `PLAN-23` B4, no una segunda. El coste está **sin medir**.

## Qué filas `VER-xx` cierra o abre

Todos los números **están por reservar**. `PLAN-29` reservó `VER-94`…`VER-101` y `PLAN-23` usa
`VER-113`…`VER-118`. **Se vuelve a comprobar justo antes de cada commit.**

| Número | Afirmación | Paso |
| --- | --- | --- |
| `VER-102` | El congelado se deriva del backend, y cualquier diferencia falla con operación, campo y dirección | E1 |
| `VER-103` | En el congelado, los estados son enumeraciones con los literales de `definitions`, ningún campo admite dos lecturas y ninguno expone la configuración | E2 |
| `VER-104` | El índice llega resuelto: por `capitulo.orden`, sin mezclar obras y con la portada de `Obra` | E3, E15 |
| `VER-105` | Ninguna escena sale sin estado ni hallazgos, y su texto es byte a byte el del borrador elegido | E4, E15 |
| `VER-106` | Los fixtures se derivan del congelado, tienen al menos dos capítulos y ninguna prueba del frontend llama a un backend | E6 |
| `VER-107` | La interfaz pinta en el orden y con los enlaces que recibe, sin calcular | E8–E10 |
| `VER-108` | Un solo browser MCP en la configuración, y ninguna delegación lo carga | E12 |
| `VER-109` | La inspección visual real queda registrada, con lo que detectó y lo que cambió (clase I). **Punto ciego:** una vez, a mano, sin score | E13, E18 |
| `VER-110` | La página recibe los hechos de una escena y el trabajo tiene forma | E14 |
| `VER-111` | La interfaz no confirma sin enseñar los capítulos, y la promesa va con su punto ciego | E16 |
| `VER-112` | Las marcas de cambio y el verde heredado se pintan tal como llegan, y la versión anterior se navega entera | E17 |
| `MF-29` | *El contrato se movió de un lado y el otro no se enteró* | E1 |

## Cuestiones abiertas para la aprobación

1. **`DA-1` frente a `SPEC-23` v2.** *Propuesta:* un cambio documental de `SPEC-22` que cite la regla
   ≤ 3 / > 3 y deje construir `RF-50`..`RF-55` sin saber la salida.
2. **`DA-6` se da por resuelta con el reparto**: la selección vive en la página y viaja un hecho.
3. **Las partes de `RF-38`.** *Propuesta:* el índice no lleva partes mientras no haya dato, y se dice.
4. **`RF-42`** no tiene atributo en `Obra`. *Propuesta:* fuera del día.
5. **La mitad automática de `EX-04`**: un validador visual con nombre, punto del harness y score.
   Necesita una decisión.

## Lo que este plan no hace

- No crea versiones, no regenera, no reverifica y no mide el arrastre: es trabajo de `PLAN-23`.
- No pone nombres ni presentes en la novela regalo (`PLAN-27` E2–E3), ni exporta PDF.
- No cierra puertas desde la web (`A-04`), ni hace las vistas de Puertas, Continuidad y Trabajos.
- No da forma a los `409` (`RF-36`), salvo lo que E14 necesita de `GET /trabajos/{id}`.
- No crea CI, ni expone `vista.consumo`.
