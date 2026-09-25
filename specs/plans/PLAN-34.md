---
id: PLAN-34
spec: SPEC-34
titulo: Implementación de la pseudonimización de los nombres
estado: aplicada
aprobada_por: "sesión autónoma del 2026-09-24, por delegación explícita del autor («Decide tú todo […] No pares a consultarme»)"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 2
fecha_aplicacion: 2026-09-24
---

> **v2 (2026-09-24), lo hecho frente a lo planeado.** E1–E7 terminados, sin llamar al modelo.
> - **La entrega borra las parejas en E3, no en E4.** La prueba que ya existía
>   (`test_tras_entregar_no_queda_ningun_dato_de_la_ficha_en_ninguna_tabla`) lo cazó en cuanto
>   E3 guardó la primera pareja.
> - **El género, con listas** (`F-205`): la regla de la terminación dio un pseudónimo
>   masculino a «Irene». Antes de la terminación se miran dos listas de nombres conocidos.
> - **Los restos solo son diminutivos y plurales**: con la raíz sola, un «Martín» inventado por
>   el Planificador habría sido un resto de «Marta» en cada escena, con su reescritura pagada.
> - **Los guiones de la evaluación** (`SPEC-31`) contestan la primera pregunta con una frase
>   («Se llama…»). Lo que el comprador teclea en el campo es el nombre que el guion espera en
>   la ficha de ese turno (`evaluar.nombre_del_primer_turno`).
> - **Sin campo de nombres, como antes**: si una entrevista no lo usa (la CLI vieja, un
>   guion), los nombres vetados que saque el modelo se aceptan, y cualquier nombre que el
>   modelo ponga en la ficha recibe pseudónimo desde el turno siguiente.
> - **La conexión de las tools es de solo lectura**: leer las parejas no crea la tabla.
> - **Punto ciego nuevo**: el nombre nuevo de un renombrado (`SPEC-23`) lo da el lector y no
>   está en la ficha, así que sale tal cual.

# PLAN-34 — Los nombres, fuera del modelo

Cómo se construye `SPEC-34` (v2, aprobada). **Ningún paso llama al modelo**: todo se
prueba con dobles. Cada paso empieza por la prueba que falla y deja en verde la suite
entera del backend, la del validador del contrato y, cuando toca la web, la del frontend.
Rama `web-de-principio-a-fin`, sobre `examen-cierre`.

## Cómo se aprobó este plan, y la cuestión 4

`SPEC-34` dejaba abierta su cuestión 4: la sesión del frontend quería revisar cómo pide los
nombres la entrevista antes de aprobar el plan. **Esa sesión ya no existe**: el autor retomó
el proyecto en una máquina nueva con una sola sesión, y le delegó todas las decisiones por
escrito. La revisión la hace esta sesión, que lleva a la vez el backend y la web, y el
resultado es la sección «La entrevista» de abajo y los pasos E3 y E4. `SPEC-35` `RF-06` le
da estilo en `PLAN-35` v3.

## Lo que se encontró al preparar el plan

1. **Langfuse ya no recibe ningún texto de la obra.** Los tipos de
   `commons/observabilidad/envio.py` tienen `extra="forbid"`: ni el prompt, ni la respuesta,
   ni el término de una vetada que no sea global (`SPEC-29` `RF-06`). `RF-03` de
   `SPEC-34` para Langfuse **ya se cumple por construcción**; lo que falta es la prueba que
   lo demuestre en una generación entera (`RF-06`, paso E7).
2. **Todo lo que llega a un agente pasa por `llamar(prompt) -> dict`.** El Entrevistador, el
   extractor del texto libre, el Planificador, el Revisor, el Escritor, el Editor, el Juez y
   el Resumidor. Ya hay cuatro envolturas con esa firma (`ConReintentos`, `ConFase`,
   `Contador`, `SesionObservada`). **La frontera es una quinta envoltura**: pseudonimiza el
   prompt y restituye la respuesta. Así la sustitución vive en un solo sitio, y ningún prompt
   se puede olvidar.
3. **Hay tres salidas que no pasan por `llamar`**: lo que devuelven las tools de la story
   bible (`herramientas/story_bible.py`, un proceso aparte), el fichero de reglas del hook
   `Stop` (que el hook compara con el texto **pseudonimizado** del Escritor) y el motivo con
   el que ese hook devuelve el capítulo (que cita esas reglas). Las tres se pseudonimizan con
   la misma tabla.
4. **`EXAMEN.md` §1 dice que el Entrevistador recoge el nombre.** Con `RF-01` el nombre se
   escribe en un campo propio. **No se contradicen**: la conversación sigue preguntándolo —es
   la primera pregunta, igual que hoy—, la respuesta va a la ficha y la ficha lo lleva al
   brief. Lo único que cambia es que esa respuesta se escribe en un campo y el agente la
   recibe con pseudónimo. El brief sigue teniendo el nombre real.
5. **El género gramatical.** Si «Olivia» llega al Escritor como «Bruno», el texto dirá «él»,
   y al restituir quedará «Olivia… él». El pseudónimo tiene que conservar el género que el
   modelo leería en el nombre real. La ficha no tiene género y `SPEC-34` no lo añade, así
   que se usa **la misma lectura que haría el modelo**: un nombre de pila terminado en `a` va
   a la lista femenina y el resto a la masculina. Es un punto ciego declarado (un «Andrea»
   italiano, un «Noa» masculino) y se anota en `docs/verification.md`.

## Decisiones del plan

- **Un pseudónimo por palabra del nombre, no por nombre entero** (`RF-08`). «Olivia
  Carranza» → «Elena Robles» son dos parejas, `Olivia→Elena` y `Carranza→Robles`. Cada forma
  que registre `formas_de_nombre` («Olivia Carranza», «Olivia») sale sustituida sin
  guardarla aparte, y un «Carranza» suelto también. Las partículas en minúscula («de», «la»)
  no se sustituyen.
- **La pareja se guarda** en una tabla nueva, `pseudonimo`, con la obra, la palabra real, el
  pseudónimo y de quién es (`RF-02`). Se asigna una vez y se lee siempre; no se vuelve a
  calcular.
- **Cómo se elige.** De cuatro listas fijas en el código (pila femenina, pila masculina,
  apellidos, mascotas), empezando en una posición que sale de una huella de la obra y la
  palabra: estable, y distinto entre obras. Se salta cualquier candidato que choque con una
  palabra real de la tabla, con un pseudónimo ya dado, con una vetada o con un nombre vetado.
  «Chocar» incluye **compartir raíz** (todas las letras menos la última), para que un resto
  como «Elenita» se pueda reconocer sin confundirlo con un nombre real.
- **Sustitución exacta, con mayúsculas y límites de palabra.** Nunca aproximada (`RF-04`).
- **Los nombres vetados no se mandan** (`RF-07`). La ficha que reciben el Entrevistador, el
  Planificador y el Revisor va sin `nombres_vetados`. Como red para cualquier otro camino
  —la lista de vetadas del Escritor, que los mezcla con las palabras—, la envoltura cambia
  cada nombre vetado completo por `[nombre vetado]` antes de enviar. La comprobación
  (`INV-21`) sigue haciéndose sobre el texto restituido, con la lista entera.
- **Lo que no se puede restituir se ve** (`RF-04`). Se decide que un resto (una palabra con
  mayúscula que empieza por la raíz de un pseudónimo) es un **hallazgo** de una invariante
  nueva, **`INV-31`** (escena, `mayor`, regla): *«ningún texto restituido contiene un
  pseudónimo ni una forma derivada de él»*. Es `mayor` y no `bloqueante` porque el texto se
  puede reescribir, igual que `INV-23`: el hallazgo provoca otro intento. En el plan y en la
  ficha no hay escena: un resto en el plan es un hueco de cobertura, y el plan vuelve al
  Planificador; un resto en la ficha es un aviso del turno, que el comprador ve.
- **La tabla se borra al entregar**, con la ficha (`SPEC-25` `RF-21`). Si la cascada de
  `SPEC-23` vuelve a delegar con `--ficha`, la tabla se reconstruye igual, porque la elección
  es determinista.

## La entrevista (la cuestión 4, resuelta)

- La **primera pregunta** sigue siendo la del nombre, fija y del sistema. En la web y en la
  terminal se contesta **en un campo de nombres**, no con un turno del modelo:
  `PUT /entrevistas/{id}/nombres`. El sistema guarda los nombres, asigna los pseudónimos,
  registra el turno (la respuesta es el nombre y la pregunta siguiente es fija: la edad) y
  **no llama a ningún agente**.
- El mismo campo admite, en cualquier momento de la entrevista: **quién regala**, **las
  personas y mascotas con nombre** (nombre, tipo, relación) y **los nombres que no deben
  aparecer**. Cada persona o mascota declarada entra en la ficha como `ElementoPersonal`, con
  la relación como descripción, para que el Entrevistador la vea (con pseudónimo) y pregunte
  por ella.
- En cada turno, **el código repone los nombres declarados** sobre la ficha que devuelve el
  Entrevistador: el nombre del destinatario, quién regala, los nombres vetados y los
  elementos declarados que el modelo haya quitado. El modelo no puede cambiar un nombre.
- Los **avisos de nombres** (`SPEC-25` `RF-10`, un nombre vetado que comparte pila con otro)
  ya no los puede confirmar el modelo, porque no ve el nombre vetado. **Se confirman en el
  campo de nombres**: `POST /entrevistas/{id}/avisos/confirmar`. El prompt se lo dice al
  Entrevistador para que no pregunte por ellos.
- **El historial dice qué se pidió fuera del modelo**: trae `nombres` (lo declarado, siempre
  con el nombre real) y cada turno, `fuera_del_modelo: true|false`. `TurnoDeEntrevista`
  lleva ese atributo nuevo (migración).
- **Punto ciego que ya declara la spec**: un nombre que el comprador escribe en una respuesta
  o en el texto libre sin haberlo declarado sale tal cual.

## Pasos

### E1 · La pareja guardada y la invariante (`RF-02`, `RF-08`, `RF-04`)

- `docs/definitions.md`: la clase `Pseudonimo` en el plano Destinatario, su relación con la
  obra, el vocabulario `titular_de_pseudonimo` (destinatario, quien_regala, persona, mascota)
  e `INV-31`. `TurnoDeEntrevista.fuera_del_modelo`.
- `commons/db/migraciones.py`: migración 19, la tabla `pseudonimo` y la columna
  `fuera_del_modelo` de `turno_de_entrevista`.
- `commons/dominio/enumeraciones.py`: `TitularDePseudonimo`. `commons/invariantes/registro.py`:
  `INV-31`.
- `commons/politica/pseudonimos.py` (nuevo): `asignar`, `de_la_obra`, `Tabla.pseudonimizar`,
  `Tabla.restituir` (recorre diccionarios y listas, sin tocar `medidas`), `Tabla.residuos`,
  `Tabla.ocultar_vetados`, `borrar_de_la_obra`.

**Prueba que falla primero:** `test_cada_palabra_del_nombre_tiene_su_pseudonimo`. Además:
- `test_el_pseudonimo_es_estable_y_se_lee_de_la_base`;
- `test_el_pseudonimo_no_choca_con_nombres_vetadas_ni_raices`;
- `test_un_nombre_femenino_recibe_un_pseudonimo_femenino`;
- `test_restituir_devuelve_el_texto_original_en_listas_y_diccionarios`;
- `test_una_forma_derivada_del_pseudonimo_es_un_residuo`;
- `test_los_nombres_vetados_se_ocultan`;
- la de la migración y las de `VER-01`/`VER-02` (clase y enumeración nuevas).

### E2 · La envoltura (`RF-03`, `RF-04`, `RF-07`)

`commons/politica/pseudonimos.py`: `SesionPseudonimizada(sesion, tabla, vetados)`, con la
firma de las otras cuatro: el prompt sale pseudonimizado y sin nombres vetados, la respuesta
vuelve restituida, los restos quedan en `residuos`, y lo que se configura (`reglas`,
`entorno`, `herramientas`, `anotador`) pasa a la sesión de dentro.

**Prueba que falla primero:** `test_el_agente_no_ve_el_nombre_real_y_quien_llama_si`. Además
`test_la_configuracion_llega_a_la_sesion_de_dentro` y
`test_un_resto_en_la_respuesta_queda_en_residuos`.

### E3 · Los nombres entran fuera del modelo (`RF-01`, `RF-07`)

- `features/entrevista/`: `service.declarar_nombres`, `service.confirmar_aviso`; `turno` y
  `pegar_texto` envuelven al agente con la tabla de la obra, mandan la ficha sin
  `nombres_vetados` y reponen los nombres declarados; un resto en la ficha es un aviso del
  turno. `PUT /entrevistas/{id}/nombres`, `POST /entrevistas/{id}/avisos/confirmar`. El
  historial trae `nombres` y `fuera_del_modelo`. Contrato regenerado.
- `backend/entrevista_cli.py`: la primera respuesta y la orden nueva `:nombres` van al campo
  de nombres.
- `.claude/agents/entrevistador.md`: el nombre y los nombres vetados los declara el
  comprador en su campo, y los avisos de nombres no se preguntan.

**Prueba que falla primero:** `test_declarar_el_nombre_no_llama_al_agente_y_registra_el_turno`.
Además:
- `test_el_entrevistador_recibe_pseudonimos_y_la_ficha_guarda_los_reales`;
- `test_el_modelo_no_puede_cambiar_un_nombre_declarado`;
- `test_los_nombres_vetados_no_llegan_al_entrevistador`;
- `test_un_aviso_de_nombre_se_confirma_fuera_del_modelo`;
- `test_el_historial_dice_que_se_pidio_fuera_del_modelo`;
- las de la CLI (`test_cli.py`), que no importa `app`.

### E4 · La generación (`RF-03`, `RF-05`, `RF-07`)

- `orquestacion/novela.py`: `preparar_agentes` envuelve a los cinco agentes con la tabla
  (la asigna desde la ficha si la obra no la tiene: las fichas de un JSON, en la CLI y en
  la evaluación); las reglas del hook se escriben pseudonimizadas y sin nombres vetados.
- `planificacion/service.py`: el Planificador y el Revisor reciben la ficha sin
  `nombres_vetados`; un resto en el plan es un hueco.
- `orquestacion/ciclo.py`: `INV-31` sobre el texto restituido, junto a `INV-23`, con la
  tabla de la obra de la escena.
- `orquestacion/entrega.py`: la tabla se borra con la ficha.

**Prueba que falla primero:** `test_ningun_prompt_de_la_generacion_lleva_un_nombre_real`.
Además:
- `test_el_texto_guardado_lleva_los_nombres_reales`;
- `test_inv22_y_las_vetadas_miran_el_texto_restituido`;
- `test_un_resto_en_el_texto_es_un_hallazgo_inv31`;
- `test_las_reglas_del_hook_van_pseudonimizadas`;
- `test_entregar_borra_los_pseudonimos`.

### E5 · Las tools de la story bible (`RF-03`)

`orquestacion/story_bible.py`: `atender` pseudonimiza lo que devuelve con la tabla de la
obra de la delegación. **Prueba que falla primero:**
`test_la_ficha_de_un_personaje_llega_con_pseudonimo`.

### E6 · El inspector visual mira datos inventados (`RF-09`)

`semilla_lectura.py` y `semilla_regalo.py` marcan su base como inventada (una fila en
`procedencia`), y `inspeccion_visual.py` se niega sobre una base sin esa marca, diciendo
por qué. **Prueba que falla primero:**
`test_la_inspeccion_se_niega_sobre_una_base_que_no_es_inventada`.

### E7 · La prueba de que no sale ninguno (`RF-06`) y `docs/` al día

- **La prueba:** una generación entera con dobles —de la entrevista a la puerta— que guarda
  cada prompt enviado, cada salida de tool y cada objeto que llega al exportador de Langfuse,
  y no encuentra ninguna palabra real de la ficha. Es `VER-134`.
- **Documentación:** `docs/verification.md` (`VER-134`…`VER-136`, `F-146` cerrado con su
  punto ciego, el del género), `docs/architecture.md` (la frontera), `AGENTS.md` y
  `SPEC-34` → `aplicada`.

## Filas `VER-xx` que cierra

- **`VER-134`**: ningún nombre real sale hacia un agente, una tool o Langfuse en una
  generación con dobles (`RF-06`).
- **`VER-135`**: lo que vuelve se restituye antes de guardarse, y un resto es un hallazgo
  `INV-31` (`RF-04`, `RF-05`).
- **`VER-136`**: los nombres se declaran fuera del modelo, y el modelo no puede cambiarlos
  (`RF-01`, `RF-07`).

## Lo que este plan no hace

- No detecta un nombre real que el comprador escriba sin declararlo (fuera de la spec).
- No migra las bases ya generadas (fuera de la spec).
- No cambia el nombre de un personaje inventado por el Planificador: no es de nadie real.
- No añade el género a la ficha: se usa la lectura del nombre (hallazgo 5).
