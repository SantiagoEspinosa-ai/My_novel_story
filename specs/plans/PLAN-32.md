---
id: PLAN-32
spec: SPEC-32
titulo: Implementación de la dedicatoria en Obra y la extensión preguntada
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-24
version: 1
---

# PLAN-32 — La dedicatoria en `Obra` y la extensión preguntada

Cómo se construye `SPEC-32`. Cada paso empieza por la prueba que falla, deja las pruebas
actuales en verde y se puede commitear solo. **Ningún paso llama al modelo real**: todo va
contra dobles.

## Lo que se encontró al preparar el plan

1. **La extensión fija se lee en cinco sitios, no en uno.** La constante `EXTENSION` de
   `backend/app/commons/dominio/destinatario.py:26` la usan
   `entrevista/service.py:41` (la primera pregunta), `orquestacion/novela.py:49` (`montar`:
   la `longitud_objetivo` de cada capítulo), `orquestacion/novela.py:214` (las reglas del
   hook), `planificacion/service.py:117` (el prompt del Planificador) y
   `planificacion/cobertura.py:32` (exige los 10 capítulos). Guardarla en la ficha sin
   pasarla a esos sitios dejaría la extensión preguntada sin efecto. Lo señaló la otra sesión
   y está comprobado.
2. **El Escritor y `INV-17` ya leen la longitud de la escena**, no de la constante:
   `orquestacion/bucle.py:112` pasa `longitud_objetivo` al prompt, y `INV-17` compara contra
   ella. Basta con que `montar` escriba la elegida.
3. **`VER-69` busca «Irene» después de entregar, y el fixture pone «Para Irene, que siempre
   llega.» como dedicatoria** (`entrevista/tests/conftest.py:25`,
   `orquestacion/tests/test_entrega.py`). Hoy pasa porque esa prueba no monta la obra. Con
   `RF-02` la dedicatoria sobrevive **por decisión**, igual que el nombre sobrevive en el texto
   de los capítulos, que `RF-21` no borra. La prueba no se debilita: se separa lo que es de la
   ficha, que desaparece, de lo que es texto de la obra, que se queda, y el punto ciego de
   `VER-69` lo dice.
4. **La última migración es la 8** (`commons/db/migraciones.py`). `Obra.dedicatoria` necesita
   la siguiente y, por `F-51`, además la columna en el `CREATE TABLE` de
   `brief/repository.py`. Otros planes pueden pedir migraciones a la vez: **el número se
   vuelve a comprobar justo antes del commit** (`docs/sesiones-concurrentes.md`).
5. **Un vocabulario controlado va como `Enum`** (`CLAUDE.md` § "FastAPI"), pero `SPEC-32`
   deja los valores en configuración. Se reparte así: **los nombres de las opciones son el
   vocabulario** (en `docs/definitions.md` y en el `Enum`), y **el rango de palabras de cada
   una es configuración** (en `config/sistema.json`), validada contra 1.000–1.500.

## La propuesta que se aprueba con el plan

Aprobar este plan es aprobar esto, que `SPEC-32` deja al plan:

| Opción | Palabras por capítulo |
| --- | --- |
| `corta` | 1.000 – 1.150 |
| `media` | 1.150 – 1.350 |
| `larga` | 1.350 – 1.500 |

Los nombres del vocabulario son `extension_de_capitulo`: `corta`, `media`, `larga`.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `docs/definitions.md` | `Obra.dedicatoria`, `FichaDeEntrevista.extension` y el vocabulario `extension_de_capitulo` |
| `backend/app/commons/dominio/` | El `Enum`, el campo de la ficha y la función que da el rango de una extensión |
| `backend/app/commons/configuracion/` y `backend/config/sistema.json` | Los rangos, validados |
| `backend/app/features/entrevista/` | La pregunta y `que_falta` |
| `backend/app/features/orquestacion/novela.py`, `planificacion/` | Usar la extensión elegida |
| `backend/app/features/brief/repository.py`, `commons/db/migraciones.py` | La columna `dedicatoria` y su migración |

## Pasos

### E1 · El dominio primero

`docs/definitions.md`: `Obra` gana `dedicatoria`; `FichaDeEntrevista` gana
`extension → extension_de_capitulo`; el vocabulario nuevo con sus tres literales. Después el
`Enum` en `commons/dominio/enumeraciones.py`.

**Prueba que falla primero:** `test_extension_de_capitulo_tiene_los_literales_de_definitions`
en `commons/dominio/tests/test_enumeraciones.py`.

### E2 · Los rangos, en configuración y validados

`config/sistema.json` gana los rangos de la tabla de arriba; `commons/configuracion/` los
valida con `extra=forbid`: cada rango dentro de 1.000–1.500, mínimo menor que máximo, y una
entrada por cada literal del vocabulario.

**Pruebas:** `test_una_opcion_de_extension_fuera_de_1000_1500_es_error`,
`test_un_rango_con_el_minimo_mayor_que_el_maximo_es_error`,
`test_falta_el_rango_de_una_opcion_es_error`, `test_los_rangos_por_defecto_cargan`.

### E3 · La ficha guarda la extensión

`FichaDeEntrevista.extension: ExtensionDeCapitulo | None`. `que_falta` la pide **después del
tono**, que es el orden del enunciado (*«género, tono y extensión»*). La constante `EXTENSION`
se queda con los 10 capítulos y pierde las palabras; una función da el rango de la extensión
elegida.

**Pruebas:** `test_una_ficha_sin_extension_no_esta_completa`,
`test_la_extension_se_pide_despues_del_tono`,
`test_una_extension_que_no_esta_en_el_vocabulario_no_valida`.

### E4 · El entrevistador la pregunta

La primera pregunta anuncia los 10 capítulos y ya no fija las palabras; el bloque «EXTENSION
(no se pregunta, solo se informa)» del prompt pasa a ofrecer las tres opciones con sus rangos;
`.claude/agents/entrevistador.md` dice que se pregunta.

**Pruebas:** `test_el_prompt_ofrece_las_tres_opciones_de_extension`,
`test_la_primera_pregunta_no_fija_las_palabras`,
`test_la_ficha_cerrada_lleva_la_extension_elegida` (entrevista completa con el doble).

### E5 · El código la respeta

`montar` escribe en cada escena la `longitud_objetivo` de la extensión elegida; las reglas del
hook llevan esa longitud; el prompt del Planificador también. La cobertura sigue exigiendo 10
capítulos.

**Pruebas:** `test_montar_usa_la_longitud_de_la_extension_elegida`,
`test_las_reglas_del_hook_llevan_la_longitud_elegida`,
`test_el_prompt_del_planificador_lleva_la_longitud_elegida`, y un caso negativo:
`test_un_capitulo_de_1200_palabras_falla_INV_17_si_la_extension_es_larga`.

### E6 · `Obra.dedicatoria`

La columna en el `CREATE TABLE` de `brief/repository.py` y su migración (la 9, si sigue libre
al commitear), con `anadir_columnas`; `alta_de_obra` la acepta y `montar` le pasa
`ficha.dedicatoria`.

**Pruebas:** `test_montar_copia_la_dedicatoria_a_la_obra`,
`test_la_migracion_anade_dedicatoria_a_una_base_anterior`,
`test_una_ficha_sin_dedicatoria_deja_la_obra_sin_ella`.

### E7 · La dedicatoria sobrevive al borrado, y nada más de la ficha

Una variante de `VER-69` que **sí monta la obra** antes de entregar: tras `RF-21`, la
dedicatoria sigue en `obra` y ningún otro dato de la ficha queda en ninguna tabla. El punto
ciego de `VER-69` en `docs/verification.md` pasa a decir que el texto de la obra —capítulos y
dedicatoria— conserva por decisión los nombres que contenga.

**Pruebas:** `test_tras_entregar_la_dedicatoria_sigue_en_la_obra`,
`test_tras_entregar_una_obra_montada_no_queda_ningun_otro_dato_de_la_ficha`.

### E8 · `docs/` y spec al día

`docs/architecture.md` si la entrevista cambia de forma, la fila `VER-69` con su punto ciego,
las filas nuevas, `EX-16` y `EX-17` cerrados en `docs/cobertura-examen.md`, y `SPEC-32` a
`aplicada`.

## Qué filas `VER-xx` abre

| Fila | Qué comprueba | Paso |
| --- | --- | --- |
| `VER-nueva-A` | Una opción de extensión fuera de 1.000–1.500 es un error de configuración (`RF-07`) | E2 |
| `VER-nueva-B` | La longitud objetivo de cada capítulo, las reglas del hook y el prompt del Planificador usan la extensión de la ficha (`RF-09`) | E5 |
| `VER-nueva-C` | Tras entregar, la dedicatoria sigue en `Obra` y ningún otro dato de la ficha queda en la base (`RF-02`, `RF-03`) | E7 |

## Lo que este plan no hace

- **La portada.** La web es `SPEC-22` y el PDF `SPEC-27`: los dos leen `Obra.dedicatoria` y lo
  construyen sus planes.
- **Que la dedicatoria no suba a Langfuse** (`RF-05`): lo comprueba la prueba de `SPEC-29`
  `RF-07`, que tiene que llevar una dedicatoria entre sus datos inventados. Queda anotado en
  `PLAN-29`.
- Editar la dedicatoria desde la lectura, ni cambiar el número de capítulos.
