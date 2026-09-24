---
id: PLAN-30
spec: SPEC-30
titulo: Implementación de la puerta de publicación, con Lean
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-24
version: 2
---

> **Historial.** v2 (2026-09-24): el autor resuelve `C-1` a `C-4` y `SPEC-30` pasa a v4 con
> ellas. Aquí cambian E4, E10 y E13, y la tabla de evaluación de `PLAN-31` gana la columna
> «no ejecutado» de `INV-06`.

# PLAN-30 — La puerta de publicación

Cómo se construye `SPEC-30`. Cada paso empieza por la prueba que falla, deja las pruebas en
verde y se puede commitear solo. **Ningún paso llama al modelo real**, salvo E14, que gasta
dinero y necesita un sí explícito. Lean no es un modelo: E5 y E12 lo ejecutan de verdad sin
coste.

Las cuatro cosas que la spec no decidía (§ "Cuatro decisiones, resueltas") las decidió el autor
el 2026-09-24, y están en `SPEC-30` v4.

## Lo que se encontró al preparar el plan

1. **La rendición no sobrevive a la consolidación.** La escena rendida se queda en
   `aceptada_por_rendicion` y, al consolidar, `ciclo.consolidar_y_resumir` llama a
   `repo.marcar_consolidada` (`ciclo.py:309`), que escribe `consolidada` encima. `rendidas`
   vive en memoria y se pierde al relanzar, y `lectura/vista.py` calcula
   `se_acepto_rindiendose` por el estado, así que tras consolidar dice `False`. **Es una
   contradicción entre documentos**: `docs/definitions.md` dice que la rendición *«es un estado
   y no un campo»* porque quien lea el manuscrito necesita saberlo, y `docs/architecture.md`
   (con `maquina.py`) tiene la transición `aceptada_por_rendicion → consolidada` que lo borra.
   → `C-3`.
2. **Ningún hallazgo se cierra nunca.** `repo.cerrar_hallazgo` no tiene llamadas fuera de las
   pruebas. Un `INV-26` de un primer intento que salió limpio en el segundo sigue `abierto`. La
   puerta no puede usar `evaluar_cierre`, que bloquea por cualquier `mayor` abierto, y tras un
   reintento un `INV-27` de la ronda anterior la dejaría cerrada para siempre. **La puerta
   recalcula en cada ronda y cierra lo que la ronda nueva ya no encuentra.**
3. **Lo que ve Lean en la novela regalo lo fija el plan, no el Escritor.** El evento de cada
   escena sale de `t_fabula`, `lugar` y `personajes_presentes`; `montar` escribe los dos
   primeros desde el plan y **no escribe `personajes_presentes`** (el mismo hallazgo que
   `PLAN-27`). Así, `L-2`, `L-3` y `L-4` no tienen presentes que mirar —un `0` de Lean hoy es
   «`L-1` limpio»—, y reescribir la prosa no cambia ningún evento: un fallo de `L-1` vuelve igual
   tras cualquier reescritura. → `C-2`.
4. **Reescribir un capítulo ya consolidado no está permitido hoy.** De `consolidada` no sale
   ninguna transición (`SPEC-23`, en revisión), y `aplicar.consolidar` levanta `YaConsolidada`.
   Cuando la puerta corre, todos los capítulos están consolidados. → `C-1`.
5. **`INV-06` es `bloqueante` de nivel obra y no la comprueba nadie**: solo existe en el
   registro. `RF-01` pide que no quede ninguna `bloqueante` de obra abierta, y de esta no se
   puede afirmar nada. → `C-4`.
6. **Lean no emite las violaciones en forma legible por máquina.** `MainReal.lean` solo imprime
   `#COBERTURA` y `#PAR L-1`, y `Violacion` no guarda los eventos. `RF-03` pide «los eventos
   implicados»: hay que tocar Lean (E5).
7. **`Cronologia/Generado.lean` está versionado**, y `generar_lean.py` lo sobrescribe por
   defecto. Se trabaja en una copia temporal.
8. **`generar_lean.py` sale con 1 cuando hay cero eventos**, y `MainReal` con 2 en ese caso: el
   1 del generador no se puede confundir con el 1 de Lean.
9. **`lake` está instalado y no está a la vista**: no está en el `PATH`, `ELAN_HOME` no está
   definida, y existen `~/.elan/bin/lake.exe` y la toolchain `leanprover/lean4:v4.34.0`. Dentro
   de `specs/lean/` responde `Lake version 5.0.0-src+293d5d0 (Lean version 4.34.0)`.
10. **`SPEC-30` citaba el interruptor TLA+ equivocado**: `PublicarAlAgotarTope` gobierna el
    freno de delegaciones; el que se parece a la rendición es `ExigirValidacionCompleta`. Los
    dos tienen el valor estricto en `HarnessNovela.cfg`, así que la decisión se sostiene. La cita
    ya está corregida en `SPEC-30` como cambio documental.
11. **Menores.** `MainReal.lean` cita `F-53` donde quiere decir `F-54`. `INV-19` e `INV-20` están
    reservadas para edad y ubicuidad: los números nuevos no las toman. No hay código de Langfuse
    en `backend/`.

## Cuatro decisiones, resueltas

El autor eligió la propuesta en las cuatro: `C-1` (a), `C-2` (b), `C-3` (a) y `C-4` (a), esta
última con dos condiciones —escrita como decisión nuestra con su motivo, y visible como
«no ejecutado» en la tabla de evaluación—. Se conservan las opciones tal como se plantearon.

- **`C-1` · Qué es reescribir un capítulo consolidado** (bloquea E9 y E10).
  (a) **Reescribir a delta fijo** (`SPEC-23` `S-3`): el borrador nuevo pasa por las puertas de
  texto y su delta se compara con el guardado; solo se acepta si coincide. El canon no se mueve.
  (b) Esperar a `SPEC-23`. (c) Tope 0 hasta entonces, lo que incumple `RF-06`.
  **Propuesta: (a).** Cuesta que una reescritura que cambie el delta se rechace y gaste su
  intento.
- **`C-2` · Qué hacer con un fallo de Lean que ninguna reescritura puede arreglar** (bloquea
  E10). (a) Literal: el Editor da instrucciones, se reescribe, Lean falla igual y tras dos
  reintentos se para —gasto sin efecto, cuánto está sin medir—. (b) **El fallo vuelve al Editor
  como feedback** (lo que pide `EXAMEN.md` §5c), su diagnóstico queda en el informe de parada, y
  la generación se detiene según `RF-04` **sin reescribir**, diciendo que el dato viene del
  plan. **Propuesta: (b).** Con ella, el bucle de reintentos solo atiende a `INV-27`.
- **`C-3` · Dónde consta la rendición** (bloquea E2). (a) **La escena rendida se queda en
  `aceptada_por_rendicion` tras consolidar**, y que está consolidada lo sigue diciendo
  `escena_consolidada`. Es lo que dice `docs/definitions.md`; cambia `docs/architecture.md` y
  `maquina.py`. (b) Un campo o una tabla aparte, que `definitions.md` rechaza expresamente.
  **Propuesta: (a).**
- **`C-4` · `INV-06` sin implementar.** (a) La puerta la lista como **«no comprobada»** en su
  veredicto y no bloquea por ella, con una fila `VER` abierta. (b) Bloquea, y ninguna novela se
  publica hasta implementarla. **Propuesta: (a)**, dicha en voz alta: es una excepción a la
  Regla 8, y la tiene que aceptar el autor.

## Dos identificadores que la spec no nombra y el plan necesita

- **`INV-nueva-A`** (`bloqueante`, obra, `regla`): la verificación formal de la cronología
  devuelve `0` (`RF-01`.3, `RF-09`).
- **`INV-nueva-B`** (`bloqueante`, obra, `regla`): ningún capítulo de una versión publicada está
  en `aceptada_por_rendicion` (`RF-01`.1).

Lean es determinista, así que va como `regla`. `INV-28` está libre en todo el árbol. **Aprobar
este plan es aprobar esos dos identificadores.** `INV-27` sigue siendo `mayor`: que bloquee la
publicación es regla de esta puerta (`RF-07`), no un cambio de severidad.

## Dónde vive

| Dónde | Qué |
| --- | --- |
| `features/auditoria/publicacion.py` (nueva) | `decidir(...)`: las condiciones de `RF-01`, sobre datos ya resueltos |
| `features/auditoria/lean.py` (nueva) | El adaptador a `lake`: localizar, copia temporal, generar, compilar, ejecutar, interpretar |
| `features/auditoria/repository.py` (nueva) | La tabla `veredicto_de_publicacion`, que es lo que `PLAN-27` E6 necesita leer |
| `features/orquestacion/publicacion.py` (nueva) | Evaluar, cerrar lo superado, pedir instrucciones al Editor, reescribir, contar rondas |
| `features/orquestacion/obra.py`, `ciclo.py` | `reescribir_capitulo` y `consolidar=False` en `ciclo.ejecutar` |
| `features/escaleta/repository.py`, `orquestacion/maquina.py` | La rendición persiste (`C-3`) |
| `commons/dominio/edicion.py` | `InstruccionesDeReescritura` |
| `commons/config.py`, `configuracion/esquemas.py`, `config/sistema.json` | El tope 2 y el tiempo máximo de Lean |
| `specs/lean/Cronologia/Invariantes.lean`, `MainReal.lean` | Los eventos de cada violación y la línea `#VIOLACION` |
| `backend/novela_regalo.py` | Lean real, informe de la puerta y código de salida |

## Pasos

### E1 · El dominio primero

`docs/definitions.md`: las dos invariantes nuevas y la clase `VeredictoDePublicacion` (`obra,
ronda, publica, condiciones[], codigo_lean`); `registro.py` las gana.

**Prueba que falla primero:** `test_las_de_la_puerta_de_publicacion_son_de_obra_y_bloqueantes`.

### E2 · La rendición sobrevive a la consolidación *(depende de `C-3`)*

`marcar_consolidada` no pisa `aceptada_por_rendicion`, y `maquina.py` quita esa transición.

**Prueba que falla primero:** `test_una_escena_rendida_sigue_rendida_despues_de_consolidar`.
Negativo: `test_una_escena_limpia_queda_consolidada`. Además
`test_relanzar_salta_una_escena_rendida_y_consolidada`.

### E3 · El tope y el tiempo de Lean, en configuración

`TOPE_REINTENTOS_DE_PUBLICACION = 2`, contrato y no estimación, con su propio contador.
`TIEMPO_MAXIMO_LEAN_SEGUNDOS`, **provisional, no medido**.

**Prueba que falla primero:** `test_el_tope_de_publicacion_es_2_y_cuenta_aparte`. Negativo:
`test_un_tope_de_publicacion_negativo_no_carga`.

### E4 · La decisión de la puerta, como función pura

`decidir(capitulos, bloqueantes, lean, hallazgos_de_obra, no_comprobadas)` devuelve si se
publica y **todas** las condiciones que fallan, cada una con si es reintentable. Reintentables:
`INV-27` y, según `C-2`, Lean con violaciones. No reintentables: rendición, `bloqueante`
abierta, Lean `2`, Lean no disponible.

**Prueba que falla primero:** `test_todo_limpio_publica`, y una por condición con su negativo:
`test_un_capitulo_rendido_no_publica_y_lo_nombra`, `test_una_bloqueante_de_obra_abierta_no_publica`,
`test_una_vetada_en_un_capitulo_no_publica`, `test_lean_1_no_publica`,
`test_el_2_de_lean_bloquea_igual_que_el_1`, `test_lean_no_disponible_no_publica_y_no_es_reintentable`,
`test_un_inv27_abierto_no_publica`, `test_un_inv27_sin_veredicto_no_publica`,
`test_un_fallo_de_lean_no_es_reintentable` (`C-2`),
`test_un_menor_de_obra_no_bloquea`,
`test_un_mayor_de_capitulo_de_un_intento_anterior_no_bloquea` y
`test_inv06_sale_como_no_ejecutada_y_no_bloquea` (`C-4`: el veredicto la lista como no
ejecutada, con su motivo).

### E5 · Lean dice qué eventos implica cada violación

`Violacion` gana `eventos`, y `MainReal` imprime `#VIOLACION <inv> <ev,ev> <detalle>`. Se corrige
`F-53` → `F-54`. `lake exe verificar` tiene que seguir dando `0`, y `verificar-real` sobre el
`Generado.lean` versionado tiene que dar `1` con sus líneas `#VIOLACION`.

**Prueba que falla primero:** `test_verificar_real_emite_una_linea_por_violacion`, que **se
salta si no encuentra `lake`**. En esta máquina se salta salvo que `HARNESS_LAKE` o `ELAN_HOME`
estén puestas, así que la salida de los dos comandos va pegada en el mensaje del commit.

### E6 · El adaptador de Lean y su doble

`localizar_lake()` busca en `HARNESS_LAKE`, `ELAN_HOME/bin`, `PATH` y `~/.elan/bin`.
`VerificadorLean.verificar` copia `specs/lean/` a un temporal, genera, compila y ejecuta con
tiempo máximo; `interpretar` es pura. El doble es `LeanFijo`.

**Prueba que falla primero:** `test_un_0_con_cobertura_es_limpio`. Negativos:
`test_un_0_sin_linea_de_cobertura_no_es_limpio`, `test_el_1_del_generador_no_es_el_1_de_lean`,
`test_un_codigo_desconocido_o_un_tiempo_agotado_es_sin_veredicto`, `test_sin_lake_es_no_disponible`,
`test_verificar_no_escribe_en_el_generado_versionado` y `test_una_base_en_memoria_es_sin_veredicto`.

### E7 · Qué capítulos implica cada fallo

`L-1` se imputa al evento posterior, con la misma regla que la puerta de capítulo; `L-2` y `L-4`
al evento donde aparece la persona; `L-3` a los dos; `INV-27` al capítulo donde se guardó.

**Prueba que falla primero:** `test_una_inversion_entre_cap02_y_cap03_implica_solo_cap03`.
Negativo: `test_un_evento_sin_capitulo_se_informa_y_no_se_pierde`.

### E8 · Evaluar la puerta una vez, con Lean automático

`evaluar` recalcula el cierre de la novela, lee los capítulos rendidos, vuelve a comprobar
`INV-21`, busca las `bloqueante` abiertas, **ejecuta Lean siempre** —aunque falle otra condición,
porque `RF-04` informa de todas— y llama a `decidir`. Cierra lo que la ronda nueva ya no
encuentra y guarda su `VeredictoDePublicacion`.

**Prueba que falla primero:** `test_lean_se_ejecuta_sin_que_nadie_lo_pida` (`RF-02`). Además
`test_todo_limpio_guarda_el_veredicto_publicado`, `test_con_inv24_fallando_lean_se_ejecuta_igual`,
`test_un_inv27_que_la_ronda_nueva_no_ve_se_cierra_con_motivo` y el negativo
`test_un_inv27_que_sigue_no_se_cierra`.

### E9 · Reescribir un capítulo consolidado sin mover el canon *(depende de `C-1`)*

`ciclo.ejecutar(..., consolidar=False)`. `obra.reescribir_capitulo` corre las puertas de texto y
compara el delta nuevo con el guardado: si coincide, cambia `borrador_aceptado`; si no, rechaza
el intento con «el delta cambió: no es una corrección local».

**Prueba que falla primero:** `test_reescribir_no_aplica_el_delta_otra_vez`. Además
`test_una_reescritura_con_el_mismo_delta_cambia_el_texto_aceptado` y los negativos
`test_una_reescritura_que_cambia_el_delta_se_rechaza` y
`test_una_reescritura_con_una_vetada_no_se_acepta`.

### E10 · El bucle: Lean al Editor y parada; `INV-27` con instrucciones, tope 2

`publicar` evalúa la puerta: si se abre, publica. **Si Lean falla, el Editor recibe las
violaciones con sus eventos como feedback, su diagnóstico va al informe y la generación se
detiene sin reescribir** (`SPEC-30` `RF-06`). Si queda un hallazgo `INV-27`, el Editor recibe
los hallazgos y los resúmenes —nunca la obra entera— y devuelve instrucciones por capítulo, que
se reescriben según E9. Si se agota el tope o falla algo no reintentable, **se detiene con
error** (`RF-04`). Las rondas se cuentan en `veredicto_de_publicacion`, así que **relanzar no
reinicia el contador** (la lección de `CE-4`).

**Prueba que falla primero:**
`test_el_fallo_de_lean_llega_al_editor_con_la_violacion_y_los_eventos` (`RF-03`). Además
`test_un_final_abrupto_arreglado_en_la_segunda_ronda_publica`, el negativo
`test_nunca_hay_un_tercer_reintento`,
`test_una_instruccion_para_un_capitulo_no_implicado_se_ignora_y_se_informa`,
`test_no_gasta_las_reescrituras_del_editor`, `test_relanzar_no_reinicia_el_contador`,
`test_toda_secuencia_de_veredictos_termina_publicada_o_detenida` y
`test_un_fallo_de_l1_va_al_editor_y_detiene_sin_reescribir` (`C-2`).

### E11 · Conectarlo a la novela y al guion

`novela.escribir` llama a `publicar` tras `cerrar`, si se escribió la novela entera.
`novela_regalo.py` imprime `=== PUBLICACIÓN ===` con cada condición que falla y **sale con 1** si
la puerta no abre. El veredicto de la puerta y el de Lean se guardan con nombre de score; el envío
a Langfuse es de `PLAN-29`.

**Prueba que falla primero:** `test_escribir_la_novela_entera_pasa_por_la_puerta`. Además el
negativo `test_con_hasta_capitulo_no_se_evalua_la_puerta` y
`test_el_codigo_de_salida_es_1_si_la_puerta_no_abre`.

### E12 · Lean de verdad sobre una base real, sin modelo

Contra una base con `evento_cronologico` vacía tiene que dar **`2` y no publicar**; contra el
fixture, `0`. Se mide cuánto tarda `lake build` en una copia temporal: hoy está sin medir.

### E13 · `docs/` y spec al día

`docs/definitions.md`; `docs/architecture.md` (la puerta en la máquina de estados, la
transición de la rendición según `C-3`, y que `INV-27` bloquea la publicación);
`docs/verification.md`; `docs/cobertura-examen.md` (`EX-03`; `EX-15` sigue abierto);
`specs/lean/README.md` (el backend lo llama, el contrato `#VIOLACION`, y que en la novela regalo
solo `L-1` tiene datos mientras nadie declare presentes); `AGENTS.md` y `CLAUDE.md` (`lake` es
requisito, `HARNESS_LAKE`). `SPEC-30` a `aplicada` con su commit propio.

### E14 · Una novela entera hasta la puerta (gasta dinero; necesita un sí explícito)

Los diez capítulos con una ficha inventada: comprueba que Lean corre solo, que el Editor devuelve
instrucciones legibles y cuánto cuesta una ronda. Lo que no llegue se dice «sin medir».

## Qué filas `VER-xx` abre

- `VER-nueva-A`: la puerta decide las condiciones de `RF-01`, cada una con su negativo.
- `VER-nueva-B`: Lean se ejecuta solo y el `2` bloquea (`INV-nueva-A`, `RF-09`).
- `VER-nueva-C`: el fallo llega al Editor con violaciones y eventos (`RF-03`).
- `VER-nueva-D`: tope 2, terminación y contador que sobrevive al relanzar (`RF-04`, `RF-06`).
- `VER-nueva-E`: la rendición persiste y bloquea (`INV-nueva-B`).
- `VER-nueva-F`: el adaptador nunca da «limpio» sin cobertura y no toca el `Generado.lean`
  versionado.
- `VER-nueva-G`: `INV-06` no comprobada, abierta hasta implementarla (`C-4`).

## Lo que este plan no hace

- No envía nada a Langfuse (`PLAN-29`), ni da identidad a una versión (`F-43`, `EX-14`).
- No implementa `INV-06`, ni hace que el plan declare personajes presentes (`PLAN-27` E3).
- No rehace el modelo TLA+ (`EX-07`) ni exporta PDF (`SPEC-27`).
- No es el caso real de Lean que pide el enunciado (`EX-15`): E14 puede darlo o no.
