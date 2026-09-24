---
id: PLAN-33
spec: SPEC-33
titulo: Implementación de la novela regalo en la web — entrevista, generación en vivo, coste, lanzamiento y estantería
estado: aprobada
aprobada_por: "autor del proyecto, en sesión («Aprobado PLAN-33. Empieza y realiza todo»)"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 2
---

> **v2 (2026-09-24), corrección de ubicación al implementar E4.** `docs/architecture.md`: *una
> feature no importa de otra, y `orquestacion/` es la única autorizada a componer*. El plan ponía
> en `features/regalo/` cosas que componen, y hacía que `regalo` importara de `lectura`. Cambia
> **dónde** viven tres piezas; los pasos, las pruebas y lo que cierra cada uno siguen igual:
> - **Escribir el gasto** (E4) va a `app/commons/modelo/gasto.py`, porque lo usan la entrevista
>   y la orquestación, y ninguna de las dos puede importar de `regalo`.
> - **`agentes()` y el lanzamiento** (E5, E11) van a módulos nuevos de `orquestacion/`
>   (`regalo.py` y `router_regalo.py`), sin tocar su `router.py`, que `PLAN-22` tiene a medias.
> - **`features/regalo/`** solo lee: la estantería, el gasto y el estado de la generación, por
>   SQL y sin importar `lectura` (E6 lee `progreso_de_generacion` directamente).
>
> Además, en E2–E3 el turno vive en `pages/entrevista` y no en `entities/turno` (steiger funde
> un slice con una sola referencia), y el intervalo es `INTERVALO_DE_REGALO_MS`.

# PLAN-33 — La novela regalo en la web

Cómo se construye `SPEC-33` (v3, aprobada). Cada paso empieza por la prueba que falla y deja la
suite en verde: `python -m pytest app -q` desde `backend/` y `npm test` desde `frontend/`, las
dos **enteras** y no solo la carpeta tocada. Cada paso se puede commitear solo. **Ningún paso
llama al modelo real** salvo E16, que gasta dinero y necesita un sí explícito. Se commitea por
ruta, con el `add` y el `commit` en un solo comando; nunca `git add -A`.

Se trabaja en `../My_novel_story-frontend`, rama `frontend-regalo`, que sale de `examen-cierre`
(`e3544e2`). Se rebasa sobre `examen-cierre` cuando la sesión de `PLAN-22` fusione
`plan22-peticion`.

## En este orden, y dónde se corta

| Bloque | Pasos | Qué deja | Espera a |
| --- | --- | --- | --- |
| **1 · La entrevista** | E0–E3 | El defecto `F-xx` registrado, el historial completo, y la conversación en la web | Nada |
| **2 · La generación visible y su coste** | E4–E8 | El coste de cada delegación guardado, el estado de los capítulos con las notas del Editor, y la página de la generación con su contador | Nada |
| **3 · Lanzar y la estantería** | E9–E13 | El techo de 50 USD, la confirmación, el lanzamiento, y la estantería con el botón | Nada |
| **4 · La web entera** | E14–E15 | Las rutas en `App.tsx`, la inspección real y `docs/` al día | La fusión de `plan22-peticion` (E14) |
| **5 · Una generación real** | E16 | La demo sobre una novela de verdad | **Un sí explícito**: gasta unos 17 USD |

**Si el día se acaba, el corte está después del bloque 2.** Es el orden de valor que la spec
pidió: la entrevista y la generación visible primero. Una generación de esos dos bloques se sigue
lanzando por la CLI. Ningún paso de un bloque se intercala en otro.

## Reparto con las otras sesiones

Acordado por mensaje con la sesión de `PLAN-22` el 2026-09-24.

| Pieza | De quién |
| --- | --- |
| `frontend/src/shared/ui/tema/` (los tokens y la paleta) | `PLAN-22`. Este plan **usa** los tokens y no los cambia |
| `frontend/src/app/App.tsx` | `PLAN-22`. Las rutas nuevas se piden por mensaje o entran en E14, después de su fusión |
| `features/lectura/`, `features/orquestacion/router.py` y `schemas.py` | `PLAN-22` / `PLAN-23`, que los tienen a medias. **Este plan no los edita**: la lectura del progreso se **importa** de `lectura.repository.progreso` y no se copia |
| `contrato/openapi.json` y `frontend/src/shared/api/contrato.ts` | **Quien añade una ruta los regenera en el mismo commit** (`SPEC-22` `RF-33`). Al fusionar, el conflicto se resuelve regenerando, no a mano |
| Lo nuevo de este plan | `backend/app/features/regalo/` (feature nueva: estantería, gasto, lanzamiento y estado de la generación), `commons/modelo/` (el anotador del gasto), y en `frontend/src/` las carpetas `pages/estanteria`, `pages/entrevista`, `pages/generacion`, `entities/obra`, `entities/turno`, `entities/nota-del-editor`, `features/confirmar-generacion` y `widgets/coste-en-vivo` |

**Las migraciones chocan de número.** En esta rama la última es la **15**. `PLAN-22` E14 y `PLAN-23`
añaden más. Se usa el número siguiente al que haya **en el momento del commit**, y
`validar_secuencia` caza un número repetido.

**No se tocan** los worktrees `plan22b`, `plan23b` ni `r1`, ni los puertos 8000 y 5173 (sirven la
novela de ejemplo). Este plan usa **8010** para el backend y **5183** para Vite.

## Lo que se encontró al preparar el plan

1. **El coste solo se guarda donde hay traza, y casi nada tiene traza.** `traza_de_delegacion` la
   escribe únicamente `ciclo.guardar_trazas`. El Planificador y el Revisor van envueltos en
   `Contador` (`commons/modelo/contador.py`), que suma en memoria y se pierde al terminar; el juicio
   de la puerta es `Contador(agentes["editor"])`; y el Entrevistador no se cuenta en ningún sitio
   de la base. **Todas las delegaciones pasan por `proveedor.SesionDelegada.llamar`**: el Escritor,
   el Resumidor, el Editor (`ciclo.editor_aislado` devuelve una `SesionDelegada`), el Planificador,
   el Revisor y el Entrevistador. Ahí se anota, una vez, y no en cada llamador.
2. **Una respuesta ilegible se pagó igual** (`PLAN-29` E1): su coste viaja en
   `RespuestaIlegible.medidas`. Un fallo de transporte no trae sobre. El anotador tiene que cubrir
   los dos casos: el primero con su coste y el segundo como ausente.
3. **`agentes()` vive en `novela_regalo.py`**, que es un guion. Si el lanzamiento desde la web lo
   copiara, habría dos pipelines (`RF-11`). Se mueve a `app/` y los dos lo llaman.
4. **El historial ya existe en parte**: `turno_de_entrevista (entrevista, orden, respuesta,
   pregunta)`, y `entrevista.repository.borrar_de_la_obra` ya lo borra con la ficha.
5. **El frontend ya tiene `INTERVALO_DE_PROGRESO_MS = 5000`**, que usa la barra de `PLAN-22`. No se
   cambia: la cuestión 5 aprobó 2 s para las páginas nuevas, que llevan su propia constante.
6. **El comentario de `FalloDeTransporte` en `novela_regalo.py` dice que el coste de lo escrito
   «queda en `traza_de_delegacion`»**, y no queda ahí (`SPEC-33`, § "Qué problema resuelve").

## Lo que va primero a `docs/definitions.md`

Cada clase entra en el mismo commit que su migración, en el paso que la usa:

- **`TurnoDeEntrevista`** (E1): **entrevista** → Entrevista, **orden**, **pregunta**, tema,
  **respuesta**, avisos\[\], contradicciones\[\], **cuando**. Se borra con la ficha (`SPEC-25`
  `RF-21`). Hoy la tabla existe y la clase no.
- **`GastoDeDelegacion`** (E4): **obra** → Obra, **agente**, generacion (el identificador de la
  ejecución; ausente fuera de una generación, como en un turno de entrevista), coste\_usd
  (**ausente si no se midió, nunca cero**), **cuando**.
- En la configuración del sistema (E9): `generacion_web.techo_de_gasto_usd`, que es una **decisión
  de presupuesto y no una medida**, con su marca junto al número en `commons/config.py`, igual que
  `TECHO_DE_GASTO_EVALUACION_USD`.

## Pasos

### E0 · El comentario que dice que el coste está donde no está (`F-xx`)

Se corrige el comentario de `novela_regalo.py` y se registra el hallazgo en `docs/verification.md`
con el siguiente `F-xx` libre, comprobado **justo antes del commit** (hoy el último es `F-142`).
Es documental: no lleva prueba.

### E1 · El historial completo de la entrevista (`RF-10`)

`TurnoDeEntrevista` en `docs/definitions.md`, la migración que añade `tema`, `avisos`,
`contradicciones` y `cuando` a `turno_de_entrevista`, `entrevista/repository.py` que los guarda en
cada turno, y `GET /entrevistas/{id}/turnos` en `entrevista/router.py`. Contrato regenerado.

**Prueba que falla primero:** `test_el_historial_trae_cada_turno_con_sus_avisos_y_contradicciones`.
Además `test_el_historial_esta_en_el_orden_de_los_turnos`,
`test_el_historial_de_una_entrevista_que_no_existe_es_404` y
`test_borrar_la_ficha_borra_tambien_los_avisos_del_historial`. Esta última vigila que las columnas
nuevas no sobrevivan al borrado, porque llevan datos personales.

### E2 · Las piezas de la conversación (`RF-05`, `RF-06`)

`entities/turno`: una pregunta con su respuesta, y **dentro del mismo turno** lo que falta, los
avisos y las contradicciones. Fixtures sacados del congelado (`NF-04`).

**Prueba que falla primero:** `Turno › enseña los avisos y las contradicciones dentro del turno`.
Además `› sin avisos no pinta un panel vacío` y `› cada aviso lleva texto, no solo color`.

### E3 · La página de la entrevista (`RF-05`–`RF-09`)

`pages/entrevista`: arranca del historial (`RF-10`), envía la respuesta, sondea `GET
/trabajos/{id}` cada `INTERVALO_DE_CONVERSACION_MS = 2000` (constante nueva en `shared/config`),
confirma o descarta los hechos propuestos y cierra.

**Prueba que falla primero:** `Entrevista › las preguntas anteriores siguen visibles al llegar la
nueva`. Además `› al recargar reconstruye la conversación del historial`, `› mientras el turno está
en curso lo dice`, `› si el trabajo falla enseña su motivo y conserva la respuesta escrita`, `›
cerrar solo se ofrece con puede_cerrar`, `› un 409 al cerrar enseña motivo, faltan y
contradicciones tal como vienen` y `› confirmar un hecho propuesto lo marca en la conversación`.

### E4 · Cada delegación anota su coste (`RF-18`, `RF-19`)

`GastoDeDelegacion` en `docs/definitions.md` y su migración. `SesionDelegada` acepta un
**anotador** opcional `(agente, medidas) -> None` que se llama después de cada delegación, también
cuando falla. Sin anotador se comporta como hoy. El anotador que escribe en la base vive en
`features/regalo/repository.py`.

**Prueba que falla primero:** `test_cada_delegacion_anota_su_coste`. Además
`test_una_delegacion_sin_coste_anota_ausente_y_no_cero`,
`test_una_respuesta_ilegible_anota_lo_que_costo`, `test_un_fallo_de_transporte_anota_sin_coste`
y `test_sin_anotador_la_sesion_no_cambia`. Los dobles tienen **la misma forma que la envoltura
real** (`medidas_de` sobre un sobre con `total_cost_usd`), no un diccionario con la forma que al
test le convenga.

### E5 · `agentes()` en un solo sitio, con el anotador puesto (`RF-11`, `RF-18`, `RF-21`)

`agentes()` se mueve de `novela_regalo.py` a `features/regalo/agentes.py`, y recibe el anotador y
el identificador de la generación. `novela_regalo.py` la importa: **no queda una segunda copia**.
La sesión del Entrevistador recibe el mismo anotador por su fábrica.

**Prueba que falla primero:** `test_todos_los_agentes_de_la_generacion_anotan`, que cubre los
cinco de `agentes()` y el juez de la puerta. Además
`test_el_total_anotado_cuadra_con_el_informe_de_la_cli`, que es `RF-21`: con dobles de coste
conocido, la suma de `GastoDeDelegacion` es igual a `usd` tal como lo suma `novela_regalo.main`.
Y `test_novela_regalo_usa_los_agentes_de_app`.

### E6 · El estado de la generación, capítulo a capítulo (`RF-14`–`RF-17`, `RF-20`)

`GET /obras/{id}/generacion` en `features/regalo/`: la fase de cada capítulo, la **última fila de
`progreso_de_generacion` con ese capítulo**, o ausente si no se ha llegado a él; el progreso
general, importado de `lectura.repository.progreso`; las seis notas de la `ValoracionDelEditor`
del borrador vigente de cada escena del capítulo, con la marca de las que bajan del umbral de
`INV-26`; y el coste acumulado de la generación con su número de delegaciones y cuántas no
tienen coste. Contrato regenerado.

**Prueba que falla primero:** `test_cada_capitulo_trae_su_ultima_fase`. Además
`test_un_capitulo_no_empezado_viene_sin_fase_y_no_con_una_inventada`,
`test_parada_trae_su_motivo`, `test_las_notas_son_las_del_borrador_vigente`,
`test_una_nota_bajo_el_umbral_viene_marcada`, `test_con_una_delegacion_sin_coste_el_total_es_suelo`,
`test_sin_ninguna_con_coste_el_total_es_sin_medir` y `test_obra_que_no_existe_es_404`.

### E7 · Los capítulos en fila y sus notas (`RF-14`–`RF-16`)

`entities/nota-del-editor` y `pages/generacion`: los capítulos en fila con **las nueve fases con
texto** (cuestión 3), la fila que se refresca cada 2 s, y las notas que aparecen al cerrarse cada
capítulo. Se reutiliza el `Progreso` de `PLAN-22` para la última actividad (`RF-17`), sin
modificarlo.

**Prueba que falla primero:** `Generacion › enseña cada capítulo con su fase en texto`. Además
`› un capítulo no empezado dice no empezado`, `› parada enseña su motivo`, `› las notas
aparecen cuando el capítulo las trae`, `› una nota bajo el umbral se distingue con texto y no
solo con color` y `› reutiliza la barra de progreso y su aviso de sin actividad`.

### E8 · El contador discreto (`RF-19`, `RF-20`)

`widgets/coste-en-vivo`: el coste acumulado y las delegaciones, en una esquina de la página de la
generación.

**Prueba que falla primero:** `CosteEnVivo › sube cuando la respuesta trae más gasto`. Además
`› con una delegación sin coste marca el total como suelo junto a la cifra` y `› sin ninguna
medida dice sin medir, nunca 0,00`.

### E9 · El techo de las generaciones (`RF-13`, cuestión 1: 50 USD)

`GeneracionWeb` en `commons/configuracion/esquemas.py`, con `techo_de_gasto_usd > 0`;
`TECHO_DE_GASTO_GENERACION_WEB_USD = 50` en `commons/config.py`, con su marca de decisión de
presupuesto; y `"generacion_web": {"techo_de_gasto_usd": 50}` en `backend/config/sistema.json`.

**Prueba que falla primero:** `test_el_techo_de_la_web_esta_separado_del_de_la_evaluacion`.
Además `test_un_techo_no_positivo_no_valida` y `test_el_techo_de_sistema_json_es_50`. Y el
validador de nombres de configuración de `harness/documentos/contrato.py`
(`nombres_de_configuracion`) tiene que seguir en verde.

### E10 · Lo que la confirmación enseña (`RF-12`, `RF-19`)

`GET /generaciones/gasto` en `features/regalo/`:
- lo gastado en la base, **como suelo**;
- el techo;
- la última generación medida, con su suelo, o ausente;
- la **referencia de la novela de ejemplo**, 16,8905 USD en 36 delegaciones, **con su fuente**
  (`R1`, `harness/evals/medidas.md`), guardada en `commons/config.py` como referencia declarada
  y no como medida de esta base.

Contrato regenerado.

**Prueba que falla primero:** `test_lo_gastado_es_suelo_y_lo_dice`. Además
`test_sin_generaciones_la_ultima_viene_ausente_y_no_a_cero`,
`test_la_referencia_viaja_con_su_fuente` y `test_el_techo_viene_de_la_configuracion`.

### E11 · Lanzar (`RF-11`, `RF-13`)

`POST /obras/{id}/generaciones` en `features/regalo/`: encola un trabajo `generacion_regalo`, lo
ejecuta en segundo plano con `novela.escribir` y los `agentes()` de E5, y devuelve `202` con
`id_trabajo`. Las sesiones salen de `app.state`, como `_fabrica` en `entrevista/router.py`: en las
pruebas son dobles. Contrato regenerado.

**Prueba que falla primero:** `test_lanzar_devuelve_un_trabajo_y_no_bloquea`. Además
`test_sin_entrevista_cerrada_es_409_con_motivo`, `test_una_segunda_generacion_en_curso_es_409`,
`test_con_lo_gastado_en_el_techo_es_409_con_motivo` y
`test_la_generacion_anota_su_gasto_con_su_identificador`.

### E12 · La confirmación (`RF-12`)

`features/confirmar-generacion`: las tres cifras con su procedencia, y el botón que gasta.

**Prueba que falla primero:** `Confirmar › el botón que gasta no está disponible hasta que las
cifras han cargado`. Además `› enseña la referencia con su fuente`, `› lo gastado lleva la marca
de suelo`, `› sin generaciones previas dice sin medir`, `› en el techo el botón no está
disponible y dice por qué` y `› un 409 al lanzar enseña su motivo`.

### E13 · La estantería (`RF-01`–`RF-04`)

`GET /obras` en `features/regalo/`: todas las obras con el título, la dedicatoria, el nombre del
destinatario (leído de la ficha de su entrevista, o ausente) y el estado (la última fase, o
ausente). Contrato regenerado. En el frontend, `entities/obra` (la tarjeta tipográfica) y
`pages/estanteria`, con un único botón «Generar novela» que crea la entrevista y lleva a ella.

**Prueba que falla primero:** `test_la_estanteria_trae_todas_las_obras`. Además
`test_una_obra_sin_progreso_viene_sin_estado`,
`test_con_la_ficha_borrada_el_destinatario_viene_ausente_y_la_dedicatoria_sigue`, y en el frontend
`Estanteria › una tarjeta por obra con título, dedicatoria, destinatario y estado`, `› sin
generación lo dice en texto`, `› destinatario ausente se ve como dato ausente` y `› hay un solo
botón Generar novela`.

### E14 · Las rutas (después de la fusión de `plan22-peticion`)

Se rebasa sobre `examen-cierre`. Rutas en `App.tsx`: `/` → estantería (sustituye a `Inicio`),
`/entrevistas/:entrevista` y `/obras/:obra/generacion`. Se regenera el contrato sobre el
resultado. Si la fusión no ha llegado, se le piden las rutas a la sesión de `PLAN-22` por mensaje
en lugar de editar su fichero.

**Prueba:** `App › la raíz es la estantería`, `npm run fsd` (steiger) y `npm run build` en verde.

### E15 · Inspección real y `docs/` al día (`RF-24`)

- La web entera, sobre una base con **datos inventados** (como `PLAN-22` E11), en los puertos 8010
  y 5183.
- Se recorre con Playwright MCP: la estantería, una entrevista entera con dobles, la confirmación
  y una generación simulada con capítulos en fases distintas y una delegación sin coste. Se
  registra lo que se vio.
- En `docs/`: `architecture.md` con la feature `regalo` y las páginas nuevas; `AGENTS.md` (las
  filas de backend y de planes); `verification.md` con las filas de E16.
- La spec se marca `aplicada` en su commit propio, con su `commit_de_aplicacion`, y se mueve a
  `specs/aplicadas/`.

### E16 · Una generación real desde la web *(gasta dinero; necesita un sí explícito)*

Una novela lanzada desde la estantería, de principio a fin. **Se mide**, no se supone:
- el coste que da la web frente al informe de Langfuse;
- cuánto tarda de verdad;
- si el contador subió en cada delegación.

Hasta que se ejecute, la duración de una generación **está sin medir**.

## Qué filas `VER-xx` abre

Todas **a reservar**: el identificador se comprueba justo antes del commit, porque hay varias
sesiones numerando.

- **El gasto guardado cuadra con el informe** (`RF-21`): lo cierra E5 en pruebas y lo confirma E16
  en real.
- **Ninguna delegación sale sin anotar**: cualquier agente nuevo que no pase por el anotador la
  rompe. La sostiene la prueba de E5.
- **El techo lo impone el backend** (`RF-13`): la sostiene E11, no la web.

## Lo que este plan no hace

- No toca la lectura, la petición de cambio ni la regeneración (`PLAN-22`, `PLAN-23`).
- No cambia los tokens ni la paleta: cuando llegue la de Qaracter, se cambia en
  `shared/ui/tema/tokens.ts` y nada más.
- No hace el texto libre, el streaming, ni parar o reanudar desde la web (`SPEC-33`, § "Fuera").
- No lanza ninguna generación real sin un sí explícito (E16).
