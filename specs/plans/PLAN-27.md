---
id: PLAN-27
spec: SPEC-27
titulo: Implementación de la exportación a PDF
estado: aplicada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 1
fecha_aplicacion: 2026-09-24
---

# PLAN-27 — Exportar la novela a PDF

Cómo se construye `SPEC-27`. Cada paso empieza por la prueba que falla, deja las pruebas
actuales en verde y se puede commitear solo. **Ningún paso llama al modelo real**: todo va
contra bases en memoria, salvo E10, que gasta dinero y necesita un sí explícito.

## Cómo se lleva la dependencia de `SPEC-30` y `SPEC-32`

Las dos están `aprobada`, y sus planes (`PLAN-30`, `PLAN-32`) están en revisión. Este plan no
hace el trabajo de otro ni se adelanta a él.

| Paso | Depende de | Por qué |
| --- | --- | --- |
| E1–E5 | Nada | Leen tablas que ya existen (`escena`, `borrador`, `capitulo`, `entidad`, `lugar`) o añaden columnas que `docs/definitions.md` ya define |
| E6 | El paso de `PLAN-30` que **guarda** el veredicto de la puerta | `RF-01`: solo se exporta lo publicado, y hoy «publicada» no existe en el código |
| E7 | El paso de `PLAN-32` que añade `Obra.dedicatoria` con su migración | `SPEC-32` `RF-04`: la portada lee `Obra.dedicatoria`, nunca la ficha |
| E8 | E6 | La terminal es la única salida pública; sin la puerta exportaría cualquier cosa |
| E10 | E6, E7, E8, una novela que pase la puerta y la ficha de ejemplo | `RF-03` |

**Lo que E6 necesita de `PLAN-30`**: una consulta que responda, para una obra, **si su
versión pasó la puerta**, leída de la base y no de la memoria de un proceso. Si `PLAN-30` no
deja nada guardado, E6 no se puede escribir tal como está y este plan se revisa antes de
seguir.

**Las migraciones chocan de número.** E2 añade una, y `PLAN-32` añade la de
`Obra.dedicatoria`. Hoy la última es la **8** (`backend/app/commons/db/migraciones.py`). Se
usa el número siguiente al que haya **en el momento del commit**, y `validar_secuencia` caza
un número repetido.

**E3 y `PLAN-32` tocan los mismos sitios**: `orquestacion/novela.py:montar` y el prompt del
Planificador. Van en commits separados y en serie, nunca en paralelo en dos worktrees.

## Lo que se encontró al preparar el plan

1. **El ensamblador recorta el borde del manuscrito.** `features/manuscrito/exportar.py:130`
   hace `"".join(partes).strip()`. Sin títulos se come el blanco inicial de la primera escena,
   y con o sin títulos el blanco final de la última.
   `test_el_texto_de_cada_escena_es_byte_a_byte_el_del_borrador` no lo ve porque compara con
   `in` y sus borradores no tienen blanco en los bordes. **Es `VER-60` incumplido en los
   bordes**, y el PDF no puede heredarlo.
2. **Los nombres de personajes y lugares no están en la base.** `entidad` guarda
   `(id, vital, lugar, fecha_de_nacimiento)` (`consolidacion/aplicar.py`) y `lugar` guarda
   `(id, accesos)` (`consolidacion/mundo.py`), aunque `docs/definitions.md` define
   `Personaje.nombre_canonico`. Los nombres solo existen en el JSON del plan aprobado
   (`plan_de_obra`). Es `G-03` de `SPEC-22`, todavía abierto. Una ficha titulada `per-01` no
   sirve de regalo.
3. **En la novela regalo nadie guarda quién está en cada escena.** `montar`
   (`orquestacion/novela.py:27`) no pasa `personajes_presentes` a `guardar_escaleta`, y
   `EscenaDelPlan` (`commons/configuracion/esquemas.py:134`) no tiene ese campo, así que la
   columna queda a `NULL` en todas las escenas. `participa_en` (`SPEC-22` `RF-44`) **no se
   puede calcular hoy** para la novela regalo. `ocurre_en` sí: `escena.lugar` es un `id` de
   lugar validado contra el plan.
4. **Rellenar `personajes_presentes` enciende `INV-02` en la novela regalo.**
   `puertas.verificar` (`verificacion/puertas.py`) comprueba que cada presente esté vivo y
   pueda llegar al lugar de la escena. Hoy no hace nada en la novela regalo porque la lista
   está vacía. Y `cronologia/extraccion.py` registra a los presentes como participantes del
   evento. Es un cambio de comportamiento, y va en E3 con la decisión de abajo.
5. **Dos `INSERT` se rompen al añadir columnas.** `mundo.sembrar_lugares` inserta por
   posición (`mundo.py:80`, `INSERT OR REPLACE INTO lugar VALUES (?, ?)`), y `aplicar.sembrar`
   usa `INSERT OR REPLACE` con tres columnas: volver a sembrar deja a `NULL` todo lo demás,
   nombre incluido. Por eso el nombre se fija **después** de sembrar, igual que
   `fijar_fecha_de_nacimiento`.
6. **`manuscrito/` no está en el árbol de `docs/architecture.md`** y no tiene
   `repository.py`: su SQL vive en `exportar.py`. El código nuevo pone el SQL en
   `repository.py`, como pide la skill `backend-feature`. `orquestacion/obra.py`
   (`_texto_elegido`) repite la regla de `exportar._texto_de`; este plan no la unifica.

## Una decisión que la spec no toma y el plan necesita

**La novela regalo declara quién está en cada escena, y con eso `INV-02` empieza a
comprobarlo** (hallazgos 3 y 4). Es la única forma de que *aparecer* signifique
`participa_en`, como exige `RF-05`. El coste: puede aparecer una parada `bloqueante` que hoy
no existe, si el plan pone a alguien en un lugar al que no puede llegar. Cuántas veces pasará
está **sin medir**. **Aprobar este plan es aprobar esto.** Si se rechaza, E3 desaparece, las
fichas de personaje dicen «sin calcular» y `RF-05` no se cumple: habría que volver a la spec.

No hace falta ningún identificador `INV` nuevo.

## La librería: fpdf2

| Candidata | Por qué sí o por qué no |
| --- | --- |
| **fpdf2** (elegida) | Python puro; enlaces internos y fuentes TrueType para Unicode |
| reportlab | Válida, pero más pesada para una portada, un índice, capítulos y fichas |
| WeasyPrint | Necesita Pango/GTK nativos en Windows: descartada |
| xhtml2pdf | Va encima de reportlab y añade un paso HTML innecesario |
| Imprimir la web | Lo prohíbe `RF-07` |

**Lo de fpdf2 sale de su documentación y no está comprobado aquí**: no está instalada
(`backend/requirements.txt` no la lleva). La primera prueba de E5 lo comprueba.

**La fuente va en el repositorio.** Las fuentes básicas de PDF solo cubren latin-1, y la prosa
lleva comillas tipográficas y rayas que están fuera: la librería fallaría o sustituiría el
carácter, y sustituir es tocar el texto (`RF-02`). Se commitea una TTF Unicode de licencia
libre, **DejaVu Sans** (con su negrita), junto con su licencia. Su tamaño está sin medir.

**pypdf** entra en `requirements.txt` para las pruebas: leen el PDF generado y comprueban
texto y enlaces.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `features/manuscrito/exportar.py` | `capitulos_de(con, obra)`: el texto exacto de cada capítulo; `manuscrito()` pasa a usarlo |
| `features/manuscrito/repository.py` (nuevo) | El SQL del libro, y en E6 el veredicto de publicación |
| `features/manuscrito/libro.py` (nuevo) | `componer(con, obra) -> Libro`: portada, índice, capítulos y fichas como datos, sin PDF |
| `features/manuscrito/pdf.py` (nuevo) | `a_pdf(libro, ruta)`: la maquetación |
| `features/manuscrito/service.py` (nuevo) | `exportar_pdf(con, obra, ruta)`: se niega si no está publicada |
| `features/manuscrito/fuentes/` (nueva) | DejaVu Sans y su licencia |
| `features/consolidacion/aplicar.py`, `mundo.py` | Guardar el nombre de personajes y lugares |
| `commons/db/migraciones.py` | La migración de esas dos columnas |
| `commons/configuracion/esquemas.py`, `features/planificacion/service.py`, `features/orquestacion/novela.py` | `personajes_presentes` en el plan, en su prompt y en `montar` (E3) |
| `backend/leer_obra.py` | `--pdf RUTA` |

`manuscrito/` no importa de ninguna feature: lee tablas por SQL, como ya hace `exportar.py`.
El cálculo de en qué capítulos aparece cada entidad lo necesitará también la web (`RF-44`);
cuando la necesite **se sube a `commons/`, no se copia**.

## Pasos

### E1 · El texto de cada capítulo, sin recortar

`capitulos_de(con, obra)` devuelve los capítulos en orden de lectura, con el texto elegido de
sus escenas (`borrador_aceptado`, y si no consta, el último) **sin tocarlo**. `manuscrito()`
lo usa, y sus separadores ya no se ponen para luego quitarlos con `strip()`.

**Prueba que falla primero:** `test_el_borde_de_la_primera_y_la_ultima_escena_no_se_recorta`.
Además `test_capitulos_de_devuelve_el_texto_byte_a_byte_con_comillas_y_rayas`, que compara
con `==`, nunca con `in`. `test_una_escena_sin_texto_se_dice_y_no_se_salta` sigue en verde.

### E2 · Los nombres del canon, guardados al montar

`entidad.nombre_canonico` y `lugar.nombre`, que `docs/definitions.md` ya define, con su
migración. `aplicar.fijar_nombre(con, id, nombre)`, con la forma de
`fijar_fecha_de_nacimiento`. `sembrar_lugares` pasa a columnas con nombre. `montar` fija los
nombres del plan **después** de sembrar. Las bases anteriores se quedan con `NULL`: no se
finge.

**Prueba que falla primero:** `test_montar_guarda_el_nombre_de_cada_personaje_y_de_cada_lugar`.
Además `test_la_migracion_de_nombres_anade_las_columnas_sin_perder_filas`,
`test_sembrar_lugares_no_depende_del_orden_de_las_columnas` y
`test_volver_a_sembrar_no_borra_un_nombre_ya_fijado` (si no se puede cumplir por el
`OR REPLACE`, `sembrar` pasa a `INSERT ... ON CONFLICT DO UPDATE`).

### E3 · Quién está en cada escena de la novela regalo

Con la decisión de arriba aprobada. `EscenaDelPlan` gana `personajes_presentes` (es
`Escena.personajes_presentes`: no es un campo nuevo del dominio), vacío por defecto para que
los planes guardados sigan validando, y cada uno tiene que ser un personaje declarado. El
prompt del Planificador lo pide y `montar` lo pasa a `guardar_escaleta`, que ya lo guarda
(`escaleta/repository.py:93`).

**Prueba que falla primero:** `test_una_escena_del_plan_con_un_presente_no_declarado_no_valida`.
Además `test_montar_guarda_los_personajes_presentes_de_cada_escena`,
`test_el_prompt_del_planificador_pide_los_personajes_presentes` y
`test_un_presente_que_no_puede_llegar_al_lugar_para_la_escena_por_inv_02`, que deja escrito el
cambio de comportamiento.

### E4 · El libro como dato

`componer(con, obra) -> Libro`: título; capítulos por `capitulo.orden`, con el texto de E1;
fichas de personaje (`participa_en`) y de lugar (`ocurre_en`). Una entidad sin nombre usa su
`id` y lo marca. `personajes_presentes` a `NULL` es «no declarado» y el `Libro` lo dice.
`Libro` **no tiene campos de estado ni de hallazgos** (`RF-06`). Si una escena no tiene texto,
**`componer` falla**: una versión publicada no puede tener un hueco.

**Prueba que falla primero:**
`test_un_personaje_aparece_en_los_capitulos_de_las_escenas_en_que_participa`. Además
`test_un_lugar_aparece_en_los_capitulos_donde_ocurre_una_escena`,
`test_una_mencion_en_el_texto_no_cuenta_como_aparecer`,
`test_presentes_sin_declarar_se_dicen_y_no_se_leen_como_nadie`,
`test_una_entidad_sin_nombre_usa_su_id_y_lo_dice`, `test_el_libro_no_lleva_estados_ni_hallazgos`
y `test_una_escena_sin_texto_impide_componer_el_libro`.

### E5 · El PDF

`a_pdf(libro, ruta)`: portada, índice con enlace interno a cada capítulo, un capítulo por
página y las fichas con enlaces a sus capítulos. El texto va **tal cual**. La fecha de
creación se fija desde fuera, para que dos exportaciones se puedan comparar.

**Prueba que falla primero:** `test_cada_entrada_del_indice_enlaza_a_la_pagina_de_su_capitulo`.
Además `test_cada_ficha_enlaza_a_los_capitulos_donde_aparece`,
`test_un_texto_con_comillas_tipograficas_y_rayas_se_escribe_sin_sustituir` y
`test_el_texto_extraido_de_cada_capitulo_coincide_con_el_del_libro`, que normaliza los
blancos: **ese es su punto ciego**. El byte a byte se verifica en el `Libro` (E4).

Entre E5 y E6, ninguna salida pública expone `componer` ni `a_pdf`.

### E6 · Solo lo publicado *(espera a `PLAN-30`)*

`exportar_pdf` consulta el veredicto de la puerta y lanza `VersionNoPublicada` con la
condición que faltó. La versión que se exporta es **la única que hay** (`F-43`, `EX-14`).
**`RF-04` se queda en «basta el de la última»**: el PDF por versión no sale gratis mientras no
haya versiones.

**Prueba que falla primero:** `test_una_version_que_no_paso_la_puerta_no_se_exporta`. Además
`test_una_version_con_veredicto_negativo_de_lean_no_se_exporta` y
`test_una_version_publicada_se_exporta_y_el_pdf_existe`, con las filas de veredicto en la
forma que defina `PLAN-30`.

### E7 · La dedicatoria en la portada *(espera a `PLAN-32`)*

`componer` lee `obra.dedicatoria`. Sin dedicatoria, la portada lleva solo el título.

**Prueba que falla primero:** `test_la_portada_lleva_la_dedicatoria_de_la_obra`. Además
`test_la_portada_no_lee_la_ficha` y `test_una_obra_sin_dedicatoria_no_inventa_una`.

### E8 · Exportar desde la terminal

`leer_obra.py --pdf RUTA` llama a `exportar_pdf` e informa de la negativa con su motivo.

**Prueba que falla primero:**
`test_leer_obra_con_pdf_se_niega_si_no_esta_publicada_y_sale_con_1`. Además
`test_leer_obra_con_pdf_escribe_el_fichero_de_una_obra_publicada`.

### E9 · `docs/` y spec al día

- `SPEC-22` §1.2: la fila «Publicar la obra a un formato de libro» pasa a decir que la
  interfaz de lectura no exporta y que la exportación la cubre `SPEC-27`.
- `docs/architecture.md`: `manuscrito/` en el árbol, y § "El ensamblador del manuscrito no
  corrige nada" extendido al PDF.
- `docs/verification.md`, `docs/cobertura-examen.md` (`EX-09`), `SPEC-22` `G-03` y `G-04`, y
  el comando en `AGENTS.md` y `CLAUDE.md`.

`SPEC-27` pasa a `aplicada` con su commit propio, y **no sin E10**, porque `RF-03` es parte
de la spec.

### E10 · La novela de ejemplo (gasta dinero; necesita un sí explícito)

Los diez capítulos con `novela_regalo.py`, sobre la ficha de ejemplo. Tiene que pasar la
puerta de `SPEC-30`: si un capítulo se rinde, **no hay PDF**, y eso se informa. Después
`leer_obra.py --pdf ejemplos/novela-ejemplo.pdf` y el commit del PDF. El coste está **sin
medir**, y se informa con lo que diga la medida.

## Cuestiones abiertas para la aprobación

1. **La decisión de `INV-02`** de arriba.
2. **De dónde sale la ficha de ejemplo.** `RF-03` dice «el brief de ejemplo del README», y
   `README.md` no existe. *Propuesta:* E10 añade `ejemplos/ficha-ejemplo.json`, que es también
   el brief base de `SPEC-31` `RF-10`, y el README la cita cuando exista.
3. **Lo que E6 necesita de `PLAN-30`**: un veredicto de publicación guardado y legible.

## Qué filas `VER-xx` cierra o abre

- **`VER-60`, ampliada:** el texto de cada capítulo en el `Libro` es byte a byte el del
  borrador (E1, E4); en el PDF se comprueba la extracción con blancos normalizados (E5).
- **`VER-nueva-A`:** solo se exporta una versión que pasó la puerta (`RF-01`). E6.
- **`VER-nueva-B`:** una ficha enlaza exactamente los capítulos donde la entidad participa u
  ocurre, y una mención no cuenta (`RF-05`). E4. Punto ciego: se fía de
  `personajes_presentes` declarado.
- **`VER-nueva-C`:** cada enlace interno lleva a la página del capítulo que nombra. E5.
- **`VER-nueva-D`:** el PDF no lleva estados ni hallazgos (`RF-06`). E4.
- La portada lee `Obra.dedicatoria` y no la ficha: **es la misma fila que abre `PLAN-32`**, no
  una segunda.

## Lo que este plan no hace

- No construye la puerta ni Lean (`PLAN-30`), ni añade `Obra.dedicatoria` (`PLAN-32`).
- No expone el PDF por HTTP: el contrato de `SPEC-22` está congelado y no hay frontend.
- No pone título a los capítulos: `Capitulo` no tiene `titulo`; el índice dice «Capítulo N».
- No llena las fichas con rasgos, rol ni descripción: no están guardados (`G-03`).
- No hace la página de novedades, ni cuida la tipografía, ni un PDF por versión.
- No unifica `_texto_elegido` con `_texto_de`, ni escribe el `README.md`.
