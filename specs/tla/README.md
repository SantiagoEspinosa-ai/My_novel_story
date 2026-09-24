# Especificación TLA+ del harness

2026-09-24 · Verificada con TLC 2.19 sobre Eclipse Adoptium 21.0.12.1 (lo dice la cabecera de
cada `tlc-*.txt`)

`HarnessBackend.tla` modela **`backend/`**, el entregable (`EX-07`): el flujo de la novela
regalo tal como lo hacen hoy `backend/novela_regalo.py` y `backend/app/features/`. El modelo
anterior, `HarnessNovela.tla`, modelaba la rama `main` (`src/`, `EJECUCION.md`), que no está en
este árbol; se conserva con sus `CE-1`…`CE-5` en [la historia](#historia-el-modelo-de-la-rama-main-obsoleto),
al final.

**Lo que el modelo cubre**: configuración → planificación (con el reintento de esquema que no
gasta ronda) → escritura de cada capítulo → validación (puertas, vetadas, Editor, rendición) →
consolidación → puerta de publicación con Lean → versión publicada; y los tres caminos que el
enunciado pide: **reintentos** (seis topes, cada uno con su contador), **reanudación** tras una
caída y **regeneración** por cambio del lector según el diseño aprobado de `PLAN-23`.

---

## Lo que salió: siete defectos de `backend/` y dos del diseño de `PLAN-23`

La regla de escritura que hizo el trabajo: **un paso de TLA+ es una transacción de la base, no
una función.** Donde el código escribe dos veces en dos `with con:` seguidos, el modelo tiene
dos acciones, y una caída puede caer entre ellas. Y cada comportamiento dudoso es un
interruptor: con los valores del código (`BackendDeHoy.cfg`) TLC rompe nueve invariantes; con
la corrección (`HarnessBackend.cfg`) pasa todo. La diferencia entre los dos ficheros es la
lista de lo que hay que arreglar.

| | Qué | Dónde se rompe | Hallazgo |
| --- | --- | --- | --- |
| `CE-7` | Relanzar reinicia los contadores de reintento: los topes valen por ejecución | `ReintentosAcotados` | `F-110` |
| `CE-8` | Relanzar la planificación pisa las filas de `plan_de_obra` | `RondasDePlanConservadas` | `F-111` |
| `CE-9` | Caída entre `aplicar.consolidar` y `marcar_consolidada`: el capítulo se reescribe y muere en `YaConsolidada` en cada relanzamiento | `NoReescribeCerrados` | `F-112` |
| `CE-10` | Caída entre `rendir_escena` y la consolidación: se sigue escribiendo sobre un mundo sin ese delta | `SoloSobreConsolidadas` (`INV-05`) | `F-112` |
| `CE-11` | La puerta publica un capítulo que el Editor no juzgó (`sin_veredicto`) | `NuncaPublicaSinValidar` | `F-113` |
| `CE-12` | `delegaciones_por_obra` no salta nunca en la novela regalo | `DelegacionesAcotadas` | `F-114` |
| `CE-13` | Caída después de consolidar: el capítulo se queda sin resumen para siempre | `MemoriaCompleta` | `F-116` |
| `CE-14` | `PLAN-23`: la versión vigente es la última **creada**, y se crea antes de escribirla | `LectorVeLoPublicado` | Diseño de `PLAN-23` |
| `CE-15` | `PLAN-23`: las rondas de la puerta son de la obra, así que la versión 2 hereda las gastadas por la 1 | `CadaVersionTieneSuTope` | Diseño de `PLAN-23` |

Y dos que no son de `backend/`: `CE-6` es un error de la propia corrección, encontrado por TLC
antes de que el modelo corregido pasara, y `F-115` (una parada sale con código 0) salió al
escribir la tabla de abajo, no de TLC.

**Ningún arreglo se ha aplicado a `backend/`**: esta sesión no toca código. Cada defecto está
registrado en `docs/verification.md` con su evidencia, y el modelo corregido dice qué tiene que
cumplir el arreglo. El enunciado pide *«el cambio que hizo en el código»*: para `CE-6`…`CE-15`
ese cambio **todavía no existe** y aquí se dice en vez de fingirlo.

---

| Archivo | Qué es |
| --- | --- |
| `HarnessBackend.tla` | La especificación de `backend/` |
| `HarnessBackend.cfg` | Modelo pequeño **corregido**: 5 capítulos, 2 reintentos. **Pasa** |
| `BackendDeHoy.cfg` | El mismo modelo con los valores del código de hoy y todas las invariantes. **Falla** |
| `BackendDeHoyVivacidad.cfg` | El código de hoy, con lo que sí cumple: `Terminacion` y `VersionesSoloCrecen` |
| `ce/CE-07.cfg` … `ce/CE-15.cfg` | Una invariante cada uno, para que TLC dé la traza más corta de cada contraejemplo |
| `ce/Negativo-Versiones.cfg` | El caso negativo de `VersionesSoloCrecen` |
| `tlc-backend-corregido.txt`, `tlc-backend-de-hoy-vivacidad.txt`, `tlc-ce-06.txt` … `tlc-ce-15.txt`, `tlc-negativo-versiones.txt`, `tlc-mutante-terminacion.txt` | Salidas literales de TLC |
| `tlc-backend-de-hoy-vivacidad-5-capitulos-interrumpida.txt` | La vivacidad del código de hoy con 5 capítulos, **interrumpida sin resultado**; se guarda porque es la medida de por qué la de hoy se hizo con 3 |
| `HarnessNovela.tla`, `HarnessNovela.cfg`, `CodigoDeHoy.cfg`, `tlc-corregido.txt`, `tlc-codigo-de-hoy.txt` | **Obsoletos**: el modelo de `main`. Se conservan como historia |

## Cómo se ejecuta

TLC necesita Java y `tla2tools.jar`, y **ninguno de los dos está en este repositorio**: son
~50 MB que no tienen por qué versionarse. Se descargan así:

```powershell
# JRE portable (no necesita instalación ni permisos de administrador)
Invoke-WebRequest "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse" -OutFile jre.zip
Expand-Archive jre.zip -DestinationPath jre
Invoke-WebRequest "https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar" -OutFile tla2tools.jar
```

Y desde `specs/tla/`:

```powershell
java -XX:+UseParallelGC -cp tla2tools.jar tlc2.TLC -workers auto -config HarnessBackend.cfg          HarnessBackend.tla
java -XX:+UseParallelGC -cp tla2tools.jar tlc2.TLC -workers auto -config BackendDeHoyVivacidad.cfg   HarnessBackend.tla
java -XX:+UseParallelGC -cp tla2tools.jar tlc2.TLC -workers auto -config ce/CE-07.cfg               HarnessBackend.tla
```

`BackendDeHoy.cfg` con todas las invariantes a la vez se para en la primera violación. Se
intentó con `-continue` para verlas todas en una salida: produjo más de un millón de líneas de
trazas repetidas y terminó con una `ArrayIndexOutOfBoundsException` interna de TLC, así que se
descartó y cada contraejemplo tiene su `ce/CE-NN.cfg`.

### El tamaño del modelo, y por qué es el que es

`NumCapitulos = 5` y `ReescriturasDelEditor = 2` (dos reintentos, tres intentos) son los del
enunciado. Los demás topes valen 1 —`RevisionesDePlan` vale 2, para que haya un rechazo antes
de aprobar—, que es lo mínimo que recorre cada contador y su agotamiento; los valores reales
están en `backend/config/sistema.json` y no cambian la forma de ninguna transición.
`MaxCaidas = 1` y `MaxRegeneraciones = 1` porque caer y regenerar son lo único que puede
repetirse sin fin: sin cota TLC no termina. `TopeDelegaciones = 8` deja publicar una novela
limpia (cinco ciclos) y agota el presupuesto en una con muchos reintentos.

La salida de la regeneración (`S-1` cascada o `S-2` selectiva) la fija en `PLAN-23` B2 una regla
sobre un número **que todavía no se ha medido**. El modelo no elige: `salida` toma los dos
valores en el estado inicial y TLC recorre las dos.

## Estado de la verificación

Las cifras son las de las salidas; ninguna se ha redondeado ni estimado.

| Ejecución | Configuración | Resultado | Estados generados | Distintos | Profundidad |
| --- | --- | --- | --- | --- | --- |
| Corregido, 5 capítulos | `HarnessBackend.cfg` | **Pasa**: las doce invariantes, `VersionesSoloCrecen` y `Terminacion` | 1.226.620 | 756.394 | 41 |
| Código de hoy, vivacidad, 3 capítulos | `BackendDeHoyVivacidad.cfg` | **Pasa** `Terminacion`, `VersionesSoloCrecen`, `TypeOK`, `NuncaPierdeCapitulos` y `NoSaltaCapitulos` | 8.921.820 | 5.482.194 | 63 |
| Código de hoy, vivacidad, 5 capítulos | La misma con `NumCapitulos = 5` | **Sin resultado**: interrumpida a los 37 minutos con 37.643.441 distintos y 6.425.511 en cola (`tlc-backend-de-hoy-vivacidad-5-capitulos-interrumpida.txt`) | — | — | — |
| Código de hoy, cada invariante | `ce/CE-07.cfg` … `ce/CE-15.cfg` | **Fallan las nueve** (tabla de arriba) | Por traza, abajo | | |
| Caso negativo de `VersionesSoloCrecen` | `ce/Negativo-Versiones.cfg` | Falla, como tiene que fallar: la versión 2 sustituye a la 1 | 468.798 | 315.951 | 25 |
| Mutante de `Terminacion` | Copia con `Evaluar` sin guardar rondas | Falla: la traza vuelve al estado 24 y da vueltas para siempre | 1.090.188 | 607.146 | — |

**La vivacidad del código de hoy está comprobada en 3 capítulos, no en 5**, y conviene leerlo
así. Con 5, el código de hoy no tiene el freno que en el modelo corregido poda las novelas con
muchos reintentos (`F-114`: el tope de delegaciones no salta), y el espacio no terminó en 37
minutos. Con 3 se ejercitan las mismas acciones —primer capítulo, intermedio, último, puerta y
regeneración desde cualquiera—; lo que no se ha comprobado es que nada cambie con más
capítulos. **El sesgo va hacia lo cómodo**: si hubiera un bucle que solo aparece con más de tres
capítulos, esta ejecución no lo vería. Ninguna acción del modelo depende del número de
capítulos más allá de «el siguiente con trabajo», y aun así eso es un argumento, no una medida.

## Qué implementa cada acción

Rutas relativas a `backend/`; las líneas son las del árbol de `examen-cierre` en
`1299652`. **«Hoy»** quiere decir que la transición existe en ese árbol. Lo de `PLAN-23` está
en la rama `plan23-regeneracion`, que **no está fusionada**: al escribir esto tenía A0–A8
commiteados (el último, `df40a79`, A8) y ningún paso de la Parte B.

| Acción TLA+ | Estado o transición en el código | ¿Existe? |
| --- | --- | --- |
| `Configurar` | `novela_regalo.main` (`novela_regalo.py:156`): `carga.cargar_sistema` (`:166`), `migraciones.migrar` (`:169`), `procedencia.registrar` (`:170`) | Hoy |
| `PlanFueraDeEsquema` | `planificacion/service.py` `planificar`, el `except (ValueError, ValidationError)` (`:142-150`): fila `origen = "esquema"`, `fallos_de_formato += 1` y `PlanNoAprobado` al pasar de `tope_de_formato`, que es `topes.reintentos_de_transporte` (`:125-127`). **No gasta ronda** (`F-68`): el `continue` salta el `rondas += 1` | Hoy |
| `RechazarPlan` | `planificar`: `rondas += 1` (`:151`) y un hueco de cobertura (`:152-156`, `origen = "codigo"`) o un rechazo del Revisor (`:157-163`, `origen = "revisor"`); `PlanNoAprobado` al salir del `while rondas < tope` (`:164-166`). Cada fila, `repository.guardar` (`planificacion/repository.py:34-39`) | Hoy |
| `AprobarPlan` | `planificar`, `if aprobado: return PlanAprobado(...)` (`:161-162`) | Hoy |
| `ReutilizarPlan` | `reanudar_o_planificar` (`service.py:169-185`): con plan aprobado en `plan_de_obra`, `reutilizado=True` (`F-67`) | Hoy |
| `Montar` | `novela.montar` (`novela.py:28-80`), que no reinicia una obra montada (`:38-39`); el `for` de `_escribir` (`:352`) y el salto de `YA_HECHAS` de `generar_obra` (`orquestacion/obra.py:223-225`). Que `alta_de_obra` cree la versión 1 es `PLAN-23` A3 | Hoy; la versión 1, `PLAN-23` A3 en la rama (`a76830a`) |
| `AgotarTope` | `generar_obra`, `rendicion.queda_presupuesto(g.delegaciones, tope)` (`obra.py:227-232`; `rendicion.py:87-94`), con el `g` recién creado (`obra.py:204`) | Hoy, y no puede saltar (`F-114`) |
| `FalloDeTransporteDelEscritor` | `bucle.generar` captura `FalloDeTransporte` (`orquestacion/bucle.py:197-200`); `_intentar` reintenta con su contador (`obra.py:515-518`) y, agotado, `generar_obra` para (`:261-267`) | Hoy |
| `FalloDeContrato` | `bucle.generar` devuelve `no_cabe` (`bucle.py:169`, `:195`) o `contrato` (`:207`); no se reintenta (`O-3`) y `generar_obra` para (`obra.py:241-245`, `:261-267`) | Hoy |
| `Escribir` | `bucle.generar` → `repo.guardar_borrador` (`bucle.py:222`; `escaleta/repository.py:257-273`), que pone la escena en `generada` **antes** de las puertas | Hoy |
| `PedirReescrituraPorVetada` | `ciclo.ejecutar`, `palabra_vetada` (`orquestacion/ciclo.py:265-270`) y `nombre_mal_escrito` (`:273-278`); `_intentar`, un contador para los dos que no gasta intentos (`obra.py:472-514`) | Hoy |
| `Bloquear` | `puertas.verificar` (`bucle.py:233`) → `ciclo.ejecutar`, `c.fallo = "bloqueante"` (`ciclo.py:316-320`), o `DeltaIncompatible` al consolidar (`:348-350`); `generar_obra` para (`obra.py:261-267`) | Hoy |
| `FallarCalidad` | `INV-23` (`ciclo.py:281-295`) o una nota del Editor bajo el umbral (`_editar`, `:181-187`); `_intentar` guarda el intento y suma `numero` (`obra.py:520-524`). Agotado el `while numero < tope` (`:452`), `generar_obra` rinde (`:269`) | Hoy |
| `PasarLimpio` | El Editor aprueba (`ciclo.py:298-303`) y `consolidar_y_resumir` → `aplicar.consolidar` (`ciclo.py:344`; `consolidacion/aplicar.py:113-165`), una transacción | Hoy |
| `PasarSinVeredicto` | `_editar` no lee la valoración: guarda `INV-26` `sin_veredicto` y **no** lo añade a los hallazgos (`ciclo.py:174-179`), así que consolida igual (`:328-331`) | Hoy (`F-113`) |
| `MarcarConsolidada` | `repo.marcar_consolidada` (`escaleta/repository.py:276-292`), llamada **después** y en otra transacción (`ciclo.py:346`) | Hoy (`F-112`) |
| `ChocarConSuDelta` | `aplicar.consolidar` lanza `YaConsolidada` si la escena ya está en `escena_consolidada` (`aplicar.py:131-135`); `c.fallo = "delta:YaConsolidada"` (`ciclo.py:348-350`) y parada | Hoy |
| `Rendir` | `rendicion.menos_malo` y `repo.rendir_escena` (`obra.py:273-275`; `escaleta/repository.py:303-313`), en su propia transacción | Hoy (`F-112`) |
| `ConsolidarRendida` | `consolidar_y_resumir` del rendido (`obra.py:277-291`) | Hoy |
| `Resumir` | El Resumidor dentro de `consolidar_y_resumir` (`ciclo.py:352-354`) y lo que `generar_obra` hace después: resumen, imprescindibles, hechos establecidos y fichas (`obra.py:293-310`). Después, el siguiente capítulo del `for` (`novela.py:352`) | Hoy (`F-116`) |
| `Reverificar` | `regeneracion.reverificar` y `estado_de`, reglas sin modelo contra la huella de la versión (`PLAN-23` A4); parar si falla es `PLAN-23` B-S2.1 | A4 en la rama (`f24b665`); B-S2.1 sin escribir |
| `PuertaAgotada` | `publicacion.publicar`, `if previas > tope` con `previas = veredictos.rondas(con, obra)` (`orquestacion/publicacion.py:183-186`; `auditoria/repository.py:31-34`) | Hoy |
| `PublicarVersion` | `publicar` → `evaluar` (`publicacion.py:76-115`) → `decidir` sin condiciones (`auditoria/publicacion.py:92-104`) → `Publicacion(True, ...)` (`orquestacion/publicacion.py:190-191`). El `numero` de la versión publicada es de `PLAN-23` A3: hoy la publicación no tiene identidad (`F-43`) | La puerta, hoy; la versión con número, `PLAN-23` A3 en la rama |
| `FallarLean` | `publicar`, con `INV-28` el Editor da un diagnóstico y se para sin reescribir (`publicacion.py:193-205`) | Hoy |
| `FallarSinArreglo` | `publicar`, alguna condición no reintentable —`INV-29` o una `bloqueante`— (`publicacion.py:206-209`) | Hoy |
| `PedirReescrituraDeObra` | `publicar`: `if e.ronda > tope` (`publicacion.py:210-213`) o las instrucciones del Editor (`:214-220`) | Hoy |
| `ReescribirEnPuerta` | `publicar` llama a `reescribir` por capítulo implicado (`publicacion.py:221-229`), que es `obra.reescribir_capitulo` (`novela.py:385-392`; `obra.py:692-750`): puertas, Editor y delta fijo | Hoy |
| `Regenerar` | La petición y los capítulos que toca (`PLAN-23` A7), la versión `n+1` con identidad (A3) y la cascada o la selectiva (B-S1.1, B-S2.1). Hoy no hay ningún endpoint ni función que la dispare | A3 (`a76830a`) y A7 (`4c48925`) en la rama; B-S1.1 y B-S2.1 sin escribir |
| `Caer` | No es código: el proceso muere, o un agente envuelto en `ConReintentos` (`commons/modelo/cliente.py:36-60`; `novela.py:302-304`) agota sus reintentos y `FalloDeTransporte` sube hasta `novela_regalo.main` (`novela_regalo.py:193-208`) | — |
| `Reanudar` | Relanzar `novela_regalo.py`: todo se re-deriva de la base (`reanudar_o_planificar`, `montar`, `YA_HECHAS`, `veredictos.rondas`); lo que vivía en variables locales de `planificar` y `_intentar` se pierde | Hoy (`F-110`) |
| `Terminado` | `novela_regalo.main` devuelve `codigo_de_salida(r)` (`novela_regalo.py:255`, `:149-153`). **Aquí salió `F-115`**: una parada sale con 0 | Hoy |

### Lo que el modelo simplifica a propósito

- **Un capítulo es una escena**, porque en la novela regalo lo es (`novela.montar`, `:59-70`).
- **Los validadores se agrupan por lo que hacen con el bucle**, no por su nombre: los que paran
  (`Bloquear`), los que piden reescritura sin gastar intento (`INV-21`, `INV-22`), los que gastan
  intento (`INV-23`, `INV-26` bajo el umbral) y el Editor que no contesta. Distinguir más
  multiplicaría estados sin abrir una transición nueva.
- **El contenido no se modela.** Qué hallazgo sale y si Lean pasa es no determinista: TLC prueba
  todas las respuestas posibles, que es lo que hace falta para que la conclusión valga con
  cualquier modelo detrás.
- **Los reintentos de transporte de los agentes que no son el Escritor no aparecen como
  contador**: `ConReintentos` los reintenta dentro de una llamada y, agotados, eso es `Caer`.
- **`ciclos` cuenta ciclos del Escritor, no delegaciones**: cada ciclo es al menos una, así que
  `DelegacionesAcotadas` rota con ciclos está rota con delegaciones.
- **La regeneración es el diseño de `PLAN-23`, no código.** En particular, `PLAN-23` dice que *no*
  hace la puerta de publicación por versión (§ "Lo que este plan no hace"); el modelo supone que
  la versión nueva pasa por la misma puerta, que es la única que existe. Si no pasara por
  ninguna, `NuncaPublicaSinValidar` no tendría nada que proteger en la versión 2.

## Las invariantes, y el caso negativo de cada una

Una invariante que nunca ha fallado no está verificada, solo declarada. Las cinco primeras
conservan el nombre y el sentido de `HarnessNovela.tla`.

| Invariante | Qué dice | Caso negativo que la rompe |
| --- | --- | --- |
| `NuncaPublicaSinValidar` | Toda versión publicada tiene todos sus capítulos consolidados, juzgados por el Editor y, si se regeneró, verificados | `CE-11`, código de hoy |
| `NuncaPierdeCapitulos` | Una versión publicada tiene los cinco capítulos | **Ninguno.** En `backend/` la puerta solo se alcanza con todos los capítulos hechos: es cierta por construcción. Se mantiene porque es la del enunciado y la que rompía `main` (`CE-1`) |
| `NoReescribeCerrados` | No se escribe un borrador nuevo de un capítulo cuyo delta ya está en el canon | `CE-9`, código de hoy |
| `NoSaltaCapitulos` | No se trabaja en un capítulo con otro anterior sin hacer o sin verificar | **Ninguno.** Tampoco falló en `main`. Con el bucle por "el menor con trabajo" es cierta por construcción; se rompería si alguien volviera a un cursor |
| `SoloSobreConsolidadas` | `INV-05`: todo lo anterior tiene su delta aplicado | `CE-10`, código de hoy |
| `MemoriaCompleta` | En la puerta, todo capítulo tiene su resumen y su registro | `CE-13`, código de hoy |
| `ReintentosAcotados` | Ningún contador supera su tope contando todas las ejecuciones (con un borrador de holgura por caída, que es el intento en vuelo que la caída se lleva) | `CE-7`, código de hoy; y `CE-6` |
| `RondasDePlanConservadas` | Cada ronda del plan tiene su fila | `CE-8`, código de hoy |
| `DelegacionesAcotadas` | Los ciclos de la obra no pasan del tope | `CE-12`, código de hoy |
| `CadaVersionTieneSuTope` | Una versión que se para por el tope de la puerta gastó sus rondas | `CE-15`, diseño de `PLAN-23` |
| `LectorVeLoPublicado` | Publicada la primera versión, lo que el lector ve es una versión publicada | `CE-14`, diseño de `PLAN-23` |
| `VersionesSoloCrecen` (acción) | Una versión publicada no cambia ni desaparece | `ce/Negativo-Versiones.cfg`: publicar pisando la anterior, el caso de `CE-5` |
| `Terminacion` (vivacidad) | `<>[](fase ∈ {publicada, detenido})`: toda generación acaba publicada o detenida y se queda ahí | Mutante: la puerta sin guardar sus rondas (`tlc-mutante-terminacion.txt`) |

**El mutante de `Terminacion`** no está en el repositorio porque es una línea: en una copia de
`HarnessBackend.tla`, `Evaluar` pasa a ser `UNCHANGED <<rondasObra, rondasVersion>>`, y se
ejecuta con las constantes de `HarnessBackend.cfg` y `PROPERTIES Terminacion`. Es la forma
exacta de `CE-4` en la puerta: si el tope viviera en memoria, pedir reescritura y reescribir
podrían alternarse para siempre.

## Contraejemplos de `HarnessBackend.tla`

La numeración sigue a la de `HarnessNovela.tla`, que acabó en `CE-5`. Cada traza completa está
en su `tlc-ce-NN.txt`; aquí va la secuencia de acciones y lo que significa.

### CE-6 · La corrección de `F-110` no bastaba: el checkpoint recordaba el número y no la decisión

**Configuración:** `HarnessBackend.cfg`, antes del cambio. **Invariante:** `TypeOK`. **Traza:**
16 estados (`tlc-ce-06.txt`; 29.542 generados, 22.522 distintos).

```
Configurar → AprobarPlan → Montar → (Escribir → FallarCalidad) ×3 → Caer → Reanudar
→ ReutilizarPlan → Montar → Escribir → FallarCalidad         numero = 4 con tope 3
```

El primer modelo corregido guardaba los contadores en la base y **no hacía nada más**. El
capítulo agota sus tres intentos, cae justo antes de rendirse, y al reanudar el bucle lo pone
a escribir otra vez: un cuarto intento. Es **`CE-4` otra vez**, en otro sitio y con otra forma:
guardar cuántos intentos se gastaron no sirve si al volver no se rehace la decisión que esos
intentos habían provocado.

**Cambio que provoca, en el modelo:** `Montar` manda a `rindiendo` un capítulo con los intentos
agotados, y `PuedeEscribir` exige `numero < MaxIntentos`. `tlc-ce-06.txt` es la salida del
modelo **antes** de ese cambio, así que sus números de línea no son los del fichero de hoy.
**En el código:** es la mitad de `F-110` que no se ve leyendo el código, y queda escrita allí.

### CE-7 · Relanzar reinicia los contadores (`F-110`)

**Configuración:** `ce/CE-07.cfg`. **Invariante:** `ReintentosAcotados`. **Traza:** 7 estados
(159 generados, 144 distintos).

```
Configurar → RechazarPlan → Caer → Reanudar → RechazarPlan → RechazarPlan
rondasTotales = 3 con revisiones_de_plan = 2
```

La traza más corta está en el plan, pero la misma forma vale para `_intentar`: `numero`,
`reescrituras` y `reintentos_de_transporte` son variables locales y vuelven a cero con cada
relanzamiento. El tope de la puerta de publicación no tiene el defecto porque se lee de la base.

**Cambio en el código:** ninguno todavía; `F-110`, abierto.

### CE-8 · Relanzar la planificación pisa sus filas (`F-111`)

**Configuración:** `ce/CE-08.cfg`. **Invariante:** `RondasDePlanConservadas`. **Traza:** 6
estados (76 generados, 68 distintos).

```
Configurar → RechazarPlan → Caer → Reanudar → PlanFueraDeEsquema
filasEscritas = 2, filasPlan = {1}
```

Dos rondas escritas y una fila: la segunda ejecución vuelve a empezar en `version = 1` y el
`INSERT OR REPLACE` sustituye la fila del rechazo por la del plan fuera de esquema. Las
objeciones del Revisor de la primera ejecución desaparecen, y no falla nada.

**Cambio en el código:** ninguno todavía; `F-111`, abierto.

### CE-9 · Una caída entre las dos transacciones de consolidar bloquea la novela (`F-112` a)

**Configuración:** `ce/CE-09.cfg`. **Invariante:** `NoReescribeCerrados`. **Traza:** 12 estados
(3.806 generados, 3.077 distintos).

```
Configurar → RechazarPlan → AprobarPlan → Montar → Escribir → Consolidar → Caer → Reanudar
→ ReutilizarPlan → Montar → Escribir
estado[1] = "generada", delta[1] = TRUE, fase = "validacion"
```

El delta del capítulo 1 ya está en el canon y su escena sigue `generada`: el bucle no la salta y
se paga otra escritura. La traza se para ahí porque ahí se rompe la invariante; lo que sigue
en el código es `YaConsolidada` y una parada, en cada relanzamiento (`ChocarConSuDelta`).

**Cambio en el código:** ninguno todavía; `F-112`, abierto.

### CE-10 · Una caída al rendirse deja escribir sobre un mundo incompleto (`F-112` b)

**Configuración:** `ce/CE-10.cfg`. **Invariante:** `SoloSobreConsolidadas`. **Traza:** 15 estados
(19.242 generados, 14.761 distintos).

```
Configurar → AprobarPlan → Montar → (Escribir → FallarCalidad) ×3 → Rendir → Caer → Reanudar
→ ReutilizarPlan → Montar
estado[1] = "rendida", delta[1] = FALSE, actual = 2, fase = "escritura"
```

`rendir_escena` confirmó el estado y la caída se llevó la consolidación. El capítulo 1 cuenta
como hecho, su delta no se aplicó nunca y el capítulo 2 va a escribirse contra ese mundo:
`INV-05` roto.

**Cambio en el código:** ninguno todavía; `F-112`, abierto.

### CE-11 · Se publica un capítulo que el Editor no juzgó (`F-113`)

**Configuración:** `ce/CE-11.cfg`. **Invariante:** `NuncaPublicaSinValidar`. **Traza:** 25
estados (580.704 generados, 411.005 distintos).

```
Configurar → AprobarPlan → Montar → (Escribir → Consolidar → MarcarConsolidada → Resumir) ×5
→ PublicarVersion
juzgado = <<TRUE, TRUE, TRUE, TRUE, FALSE>>
publicadas = <<[numero |-> 1, capitulos |-> {1, 2, 3, 4, 5}, limpios |-> {1, 2, 3, 4}]>>
```

Ninguna caída, ningún reintento: una novela que va bien y en cuyo último capítulo el Editor
contesta algo ilegible. `PasarSinVeredicto` y `PasarLimpio` son la misma acción en la traza
(`Consolidar`), y lo que las distingue es `juzgado`. Es el camino que `F-76` recorrió de verdad
en `R0`.

**Cambio en el código:** ninguno; `F-113` es una decisión de contrato del autor.

### CE-12 · El tope de delegaciones de la obra no salta nunca (`F-114`)

**Configuración:** `ce/CE-12.cfg`. **Invariante:** `DelegacionesAcotadas`. **Traza:** 22 estados
(162.466 generados, 117.772 distintos).

```
capítulo 1: FalloDeTransporteDelEscritor → Escribir → PedirReescrituraPorVetada → Escribir
  → FallarCalidad → Escribir → FallarCalidad → Escribir → Consolidar → MarcarConsolidada → Resumir
capítulo 2: FalloDeTransporteDelEscritor → Escribir → PedirReescrituraPorVetada → Escribir
  → FallarCalidad → FalloDeTransporteDelEscritor          ciclos = 9 con TopeDelegaciones = 8
```

`AgotarTope` no se habilita en ningún estado del código de hoy, porque compara el contador de
un `Generacion` recién creado.

**Cambio en el código:** ninguno todavía; `F-114`, abierto.

### CE-13 · Una caída después de consolidar deja un capítulo sin memoria (`F-116`)

**Configuración:** `ce/CE-13.cfg`. **Invariante:** `MemoriaCompleta`. **Traza:** 27 estados
(985.093 generados, 682.954 distintos).

```
capítulo 1 → capítulo 2: Escribir → Consolidar → MarcarConsolidada → Caer → Reanudar
→ ReutilizarPlan → Montar → capítulos 3, 4 y 5 → fase = "puerta"
memoria = <<TRUE, FALSE, TRUE, TRUE, TRUE>>
```

El capítulo 2 se consolidó y el Resumidor no llegó a contestar. Al reanudar, `Montar` salta al
3: el 2 está hecho. Llega a la puerta sin resumen y el juicio de obra lo leerá sin él.

**Cambio en el código:** ninguno todavía; `F-116`, abierto.

### CE-14 · Con `PLAN-23`, el lector ve una versión que nadie ha escrito ni validado

**Configuración:** `ce/CE-14.cfg`. **Invariante:** `LectorVeLoPublicado`. **Traza:** 26 estados
(841.231 generados, 589.510 distintos).

```
... la versión 1 se publica → Regenerar
vigente = 2, creadas = 2, publicadas = <<[numero |-> 1, ...]>>
```

`PLAN-23` B-S1.1 crea la versión `n+1` **antes** de escribir sus capítulos, y
`brief.version_vigente` —ya escrita en la rama, `a76830a`— devuelve *«La ultima creada»*. En el
paso siguiente a pedir el cambio, todo lo que lee «la vigente» (desde A6, `brief.leer` y el
manuscrito) ve una versión con capítulos sin escribir; si la regeneración para a mitad, se
queda así. La corrección modelada: la vigente es la última **publicada**.

**Cambio en el código:** ninguno; es del diseño de `PLAN-23` y va a su sesión (`D-5`).

### CE-15 · Con `PLAN-23`, la versión 2 hereda las rondas de puerta que gastó la 1

**Configuración:** `ce/CE-15.cfg`. **Invariante:** `CadaVersionTieneSuTope`. **Traza:** 31 estados
(3.834.622 generados, 2.582.281 distintos).

```
... la versión 1 se publica en su primera ronda → Regenerar → capítulo 1 nuevo
→ PedirReescrituraDeObra        rondasObra = 2, rondasVersion = 1, motivo = "tope_publicacion"
```

`veredicto_de_publicacion` cuenta rondas por obra (`auditoria/repository.py:31-34`), y
`PLAN-23` dice que no hace la puerta por versión (su hallazgo 19). La versión 2 se detiene por
tope habiendo gastado **una** ronda de las dos que tiene: la ronda que la 1 usó para publicarse
se le descuenta.

**Cambio en el código:** ninguno; es del diseño de `PLAN-23` y va a su sesión (`D-5`).

## Discrepancias entre el código y los documentos

| | Discrepancia | Resolución |
| --- | --- | --- |
| **D-5** | `PLAN-23` A3 crea la versión antes de escribirla y `version_vigente` devuelve la última creada; el plan no hace la puerta por versión | Es `CE-14` y `CE-15`. Va a la sesión de `PLAN-23`: no es código de este árbol ni decisión de esta especificación |
| **D-6** | `SPEC-18` C-3, tal como lo resume `commons/invariantes/severidad.py`, dice que un `sin_veredicto` no pasa como éxito y que su sitio es el cierre de capítulo; en la novela regalo el cierre de capítulo solo informa (`g.cierre`, `novela.py:373`) y la puerta de publicación no lo mira | Es `CE-11` / `F-113`. Decide el autor, porque cambia `SPEC-30` `RF-01` |

## Historia: el modelo de la rama `main` (obsoleto)

> **Obsoleto desde el 2026-09-24.** Lo que sigue es el README de `HarnessNovela.tla`, que
> modelaba la rama `main` (`src/`, `EJECUCION.md`), no `backend/`. Se conserva entero porque
> `CE-1`…`CE-5` siguen siendo verdad de lo que describían y porque `CE-4` y `CE-5` gobiernan
> el modelo nuevo: la puerta lee su tope de la base por `CE-4`, y `VersionesSoloCrecen` tiene
> identidad por `CE-5`. **La tabla de acción a código de aquí abajo cita ficheros que no están
> en este árbol**; la vigente es la de arriba.

### El hallazgo: el defecto estaba en el documento, no en el código

De los cinco contraejemplos que TLC encontró, **`CE-3` es el que justifica haber
escrito esta especificación**, y no por el defecto en sí sino por dónde estaba.

`EJECUCION.md` §3.5 dice: *"para cada capítulo del outline, **en orden**"*.
**Esa frase, implementada literalmente, es un contador.** Y con un contador,
aprobar un cambio en el capítulo 1 reescribe en cascada hasta el final: el
lector pide cambiar una frase del primer capítulo, se regenera, se aprueba, el
contador avanza al 2 —que estaba aprobado y que nadie había tocado—, lo
reescribe, y sigue. "Regenerar solo los capítulos afectados" se convierte en
regenerar la novela entera, pagándola entera.

**El código no tiene este fallo.** `estado.capitulos_pendientes()` devuelve un
conjunto y `siguiente_paso()` toma `pendientes[0]`: el bucle ya va por lista de
trabajo, no por contador. El defecto vive **solo en el documento**.

Y esto solo se ve si se formaliza **lo que el documento dice** en vez de lo que
el código hace. Modelar el código habría producido una especificación que pasa a
la primera y no habría enseñado nada: el contraejemplo apareció justo porque la
especificación siguió la frase normativa, que es la que gobierna a quien
reimplemente esto mañana sin leer `estado.py`.

La consecuencia es una corrección de `EJECUCION.md`, no de Python: donde dice
*"en orden"* tiene que decir **"el menor de los pendientes"**, que es lo que el
código hace y lo que hay que seguir haciendo. Detalle completo y traza en
[`CE-3`](#ce-3--un-cambio-del-lector-en-un-capítulo-reescribe-la-novela-entera).

---

| Archivo | Qué es |
| --- | --- |
| `HarnessNovela.tla` | La especificación. Una sola, con cuatro interruptores que la hacen describir el sistema de hoy o el corregido |
| `HarnessNovela.cfg` | Modelo pequeño **corregido**: 5 capítulos, 2 intentos. **Pasa** |
| `CodigoDeHoy.cfg` | Mismo modelo con los valores que describe `EJECUCION.md`. **Falla**, y es su función |
| `tlc-corregido.txt` | Salida literal de TLC para `HarnessNovela.cfg` |
| `tlc-codigo-de-hoy.txt` | Salida literal de TLC para `CodigoDeHoy.cfg`, con el contraejemplo entero |

### Cómo se ejecuta

TLC necesita Java y `tla2tools.jar`, y **ninguno de los dos está en este
repositorio**: son ~50 MB que no tienen por qué versionarse. Se descargan así:

```powershell
# JRE portable (no necesita instalación ni permisos de administrador)
Invoke-WebRequest "https://api.adoptium.net/v3/binary/latest/21/ga/windows/x64/jre/hotspot/normal/eclipse" -OutFile jre.zip
Expand-Archive jre.zip -DestinationPath jre
Invoke-WebRequest "https://github.com/tlaplus/tlaplus/releases/latest/download/tla2tools.jar" -OutFile tla2tools.jar
```

Y desde `specs/tla/`:

```powershell
java -XX:+UseParallelGC -cp tla2tools.jar tlc2.TLC -config HarnessNovela.cfg HarnessNovela.tla
java -XX:+UseParallelGC -cp tla2tools.jar tlc2.TLC -config CodigoDeHoy.cfg   HarnessNovela.tla
```

#### El tamaño del modelo, y por qué es el que es

`NumCapitulos = 5` y `MaxIntentos = 2` los fija el enunciado. `MaxCaidas = 1` y
`MaxRegeneraciones = 1` los fijamos nosotros, y **no son arbitrarios**: caer y
regenerar son las dos únicas acciones que pueden repetirse sin fin, así que sin
cota el espacio de estados es infinito y TLC no termina nunca. Con 1 ya se
recorre entero el camino caída → reanudación → publicación y el camino
publicación → cambio del lector → republicación, que es todo lo que hay que
verificar: un segundo ciclo no visita ninguna transición nueva.

### Qué implementa cada acción

Las tres máquinas de estados del repositorio viven en `docs/architecture.md`
(escena, capítulo y trabajo) y el harness que de verdad genera novelas vive en la
rama `main`. La especificación modela **el flujo por capítulos de `main`**,
porque es el que el enunciado describe, y cita `docs/` donde la transición
existe también allí.

| Acción TLA+ | Estado o transición en el código | Documento |
| --- | --- | --- |
| `Configurar` | `src/config.py` → `validar()`, `ruta_salida()`. En el panel, `PUT /api/config` de `src/servidor.py` | `EJECUCION.md` §3.1 |
| `Planificar` | Delegación en el subagente `arquitecto`; `src/biblia.py` → `validar()` y `normalizar()`. Crea `salida/biblia.json` | `EJECUCION.md` §3.4 |
| `Escribir` | `siguiente_paso()` devuelve `{"paso": "escribir"}`; delegación en `escritor`; `guardar_intento()` escribe `salida/.tmp/cap-NN-intento-M.md`; `estado.registrar_intento()` | `EJECUCION.md` §3.5a–b |
| `ValidarPasa` | `siguiente_paso()` → `{"paso": "validar"}` y luego `{"paso": "resolver"}`; `puntuacion.aprueba(veredictos)` con los tres validadores más `veredicto_longitud()`; `estado.aprobar_capitulo()` | `EJECUCION.md` §3.5c–d. En `docs/architecture.md`: `en_verificacion → aceptada` |
| `Reintentar` | `escalon_de_intento()`, `modelo_de_escalon()`, `intentos_maximos()`. La escalera `haiku → sonnet → opus` | `EJECUCION.md` §3.5e. En `docs/architecture.md`: `en_revision → generada` |
| `AgotarEscalera` | `puntuacion.mejor_intento()` y `estado.marcar_capitulo()`. Produce `ACEPTADO_POR_PUNTUACION` en `informe-validacion.md` | `EJECUCION.md` §3.5f. En `docs/architecture.md`: `en_revision → aceptada_por_rendicion` |
| `AgotarTope` | `delegaciones_agotadas()` y `limite_delegaciones()` sobre `limites.delegaciones_max_totales`; `siguiente_paso()` → `{"paso": "limite"}` | `EJECUCION.md` regla inviolable 6. En `docs/architecture.md`: `en_cola → detenido_por_presupuesto` |
| `Caer` | No hay código: es el fallo que el sistema sufre, no una transición que dispare | `EJECUCION.md` §6 |
| `Reanudar` | `estado.debe_reanudar()`, `estado.cargar()`, `estado.capitulos_pendientes()`; y sobre todo `siguiente_paso()`, que re-deriva todo del disco | `EJECUCION.md` §6. En `docs/architecture.md`: `en_curso → en_cola` |
| `Publicar` | `siguiente_paso()` → `{"paso": "ensamblar"}`; `src/ensamblador.py` → `manuscrito()` y `portada()`. Escribe `salida/manuscrito.md` | `EJECUCION.md` §3.6. En `docs/architecture.md`: `abierto → cerrado` del capítulo |
| `Regenerar` | `POST /api/ampliar` de `src/servidor.py`, con `copiar_novela()` delante | **Sin equivalente en `docs/`**: ver D-2 |
| `Terminado` | Estado terminal. No es código: existe para que TLC distinguja "aquí se acaba" de "aquí se atasca" | — |

#### Lo que el modelo simplifica a propósito

- **Los cuatro validadores son uno.** Continuidad, género, estilo y el contador
  de longitud aparecen como un único veredicto, porque el contrato dice que un
  solo `FALLO` de cualquiera dispara la reescritura (`EJECUCION.md` §3.5d).
  Distinguirlos multiplicaría el espacio de estados sin habilitar ni una
  comprobación nueva.
- **El contenido no se modela.** La especificación sabe si un capítulo está
  escrito, aprobado o pendiente; no sabe qué dice. La coherencia del texto es
  trabajo de los validadores semánticos y de Lean, no de TLC.
- **El resumidor no aparece.** No participa en ninguna transición de estado del
  capítulo: corre después de aprobar y no puede impedir nada.

### Contraejemplos

Los cinco están reproducidos. Ninguno se arregló en silencio: cada uno lleva el
cambio que provocó y la ejecución que lo demuestra.

#### CE-1 · Se publica una novela vacía

**Configuración:** `CodigoDeHoy.cfg`. **Invariante:** `NuncaPierdeCapitulos`.
**Traza:** 5 estados, en `tlc-codigo-de-hoy.txt`.

```
Configurar → Planificar → AgotarTope → Publicar
versiones = <<[capitulos |-> {}, limpios |-> {}]>>
```

El freno de `delegaciones_max_totales` salta **antes del primer capítulo**. La
regla inviolable 6 dice que entonces "se ensambla lo que haya", y lo que hay es
nada: se publica una novela de cero capítulos como si fuera una entrega.

**Cambio que provoca:** `PublicarAlAgotarTope = FALSE`. Que salte el freno es
una parada, no un final: el trabajo debe quedar `detenido`, no `publicada`.
Nótese que `docs/architecture.md` ya lo tiene bien —su estado se llama
`detenido_por_presupuesto` y dice explícitamente "**no falló nada**", que es
otra cosa que publicar—; el que se desvía es `EJECUCION.md`.

#### CE-2 · Se publica un capítulo que no pasó los validadores

**Configuración:** `ExigirValidacionCompleta = FALSE`, `PublicarAlAgotarTope = FALSE`.
**Invariante:** `NuncaPublicaSinValidar`. **Traza:** 1.041 estados generados,
781 distintos.

Agotada la escalera, el capítulo se queda con el mejor intento y se marca
`ACEPTADO_POR_PUNTUACION`. Entra en el manuscrito sin haber pasado nada.

**Esto no es una discrepancia entre el código y el enunciado: son tres fuentes
contra una.** `EJECUCION.md` regla 1 dice "ningún capítulo detiene la
generación", sin condiciones. Pero `docs/architecture.md` —que es lo normativo—
sí pone condición: `aceptada_por_rendicion` exige que "**ninguna invariante
`bloqueante` siga abierta**", y añade que "una invariante `bloqueante` abierta no
se rinde nunca". El enunciado del examen pide lo mismo. La rendición
incondicional de `main` es la excepción, no la regla.

**Cambio que provoca:** `ExigirValidacionCompleta = TRUE`. En el código, que
`marcar_capitulo()` deje de ser la salida por defecto: con un fallo bloqueante
abierto la generación se detiene, y sin él se rinde como hasta ahora.

#### CE-3 · Un cambio del lector en un capítulo reescribe la novela entera

> **Este es el hallazgo principal del trabajo.** Está resumido arriba, al
> principio del documento; aquí va con su traza y su cambio.

**Invariante:** `NoReescribeCerrados`. **Traza:** 17 estados, 756 generados.

El lector pide cambiar solo el capítulo 1. Se regenera, se aprueba, y el cursor
avanza al 2 —que estaba aprobado y que nadie había tocado— y lo reescribe.
Y luego el 3, y el 4. "Regenerar solo los capítulos afectados" se convierte en
regenerar todo.

**Este es el contraejemplo más útil de los cinco, y no por el defecto sino por
dónde estaba.** El código de `main` **no tiene este fallo**:
`estado.capitulos_pendientes()` devuelve un conjunto y `siguiente_paso()` toma
`pendientes[0]`, así que el bucle ya va por lista de trabajo. El fallo estaba en
**el documento**: `EJECUCION.md` §3.5 dice "para cada capítulo del outline, **en
orden**", y eso, implementado literalmente, es un contador. Formalizar la frase
del documento en vez del código es lo que lo destapó.

**Cambio que provoca:** la función `SiguientePendienteEn(f)`, que devuelve el
menor capítulo pendiente en vez de `actual + 1`. En el código no hay nada que
cambiar; en `EJECUCION.md`, sí: la frase "en orden" debe decir "el menor de los
pendientes", que es lo que hace y lo que hay que seguir haciendo.

#### CE-4 · Tras una caída, un capítulo con la escalera agotada bloquea la generación

**Configuración:** `ReanudarPorCursor = TRUE` sin la segunda rama de
`AgotarEscalera`. **Propiedad:** `Terminacion`. **Traza:** 11.859 estados,
`Stuttering` en el estado 15.

Un capítulo gasta sus dos intentos y el proceso muere mientras se valida. Al
reanudar, el capítulo vuelve a `pendiente` pero sus intentos siguen gastados —el
checkpoint se escribe tras cada intento—. Entonces no se puede escribir (no
quedan intentos) ni cerrar (no hay texto que juzgar): **la generación se queda
parada para siempre**, que es exactamente lo que la propiedad de vivacidad
prohíbe.

**La lección vale más que el arreglo:** el checkpoint guardaba *cuántos intentos
se habían gastado*, pero no *la decisión que esos intentos provocaban*. Un
checkpoint tiene que permitir **rehacer la decisión**, no solo recordar el
contador.

**Cambio que provoca:** la segunda rama del guardián de `AgotarEscalera`, que
permite cerrar un capítulo pendiente cuya escalera está agotada. Está
comprobado que es la rama que cierra el bloqueo: quitarla reproduce el
*stuttering*, y ponerla lo elimina.

**El código de `main` tampoco tiene este fallo, y por un motivo que merece
copiarse:** el texto de cada intento se escribe en `salida/.tmp/` **antes** de
validarlo, y `siguiente_paso()` re-deriva el estado del disco —su docstring lo
dice: *"la decisión se toma SIEMPRE mirando el disco, nunca un valor
recordado"*—. Al volver, el capítulo sigue escrito y lo que toca es validarlo.
Por eso la especificación modela las dos reanudaciones: la del disco
(`ReanudarPorCursor = FALSE`, la real) y la del cursor (`TRUE`, la que parece
razonable y bloquea el sistema).

#### CE-5 · La propiedad estaba en verde por no poder distinguir nada

**Propiedad:** `VersionesSoloCrecen`. Este no es un defecto del harness sino
**de la propia especificación**, y se documenta porque es el error más fácil de
no ver.

Con `ConservarVersionAlRegenerar = FALSE` —regenerar pisando la salida— la
propiedad **pasaba**. El motivo: una versión se representaba como el conjunto de
sus capítulos, y al regenerar y volver a aprobarlos todos, la versión nueva era
un valor **idéntico** a la vieja. Pisar algo con una copia exacta no se ve.

**Cambio que provoca:** el campo `ronda` en el registro de versión, que le da
identidad. Con él, la misma configuración viola la propiedad de inmediato
(1.148 estados, profundidad 18).

Y deja un requisito para el código, que hoy no cumple: **una versión publicada
necesita identidad propia**. `copiar_novela()` guarda `salida-novela-1/`,
`salida-novela-2/`… y el número de carpeta es lo único que las distingue; nada
dentro de la novela dice de qué ronda es.

**Registrado como `F-43` en `docs/verification.md`**, porque no es trabajo de
esta especificación y se cruza con `G-07` de `SPEC - Frontend y contrato
congelado.md`, que llegó a lo mismo por el otro lado: la obra no tiene versión.

### Discrepancias entre el código y los documentos

Se documentan y se resuelve a favor del documento, que es lo normativo.

| | Discrepancia | Resolución |
| --- | --- | --- |
| **D-1** | `docs/architecture.md` modela **escenas** con ocho estados y dos puertas humanas (`A-04`: la aceptación la dispara una persona). `main` trabaja por **capítulos** y sin ninguna puerta humana | La especificación modela capítulos, porque es lo que pide el enunciado y lo que existe. **La ausencia de puerta humana es un hueco real**, no una simplificación del modelo |
| **D-2** | La regeneración por cambio del lector **no existía en ningún documento** cuando se escribió esta especificación. No había transición, ni estado, ni versión. **Desde entonces la describen `SPEC-22` `RF-50`..`RF-55` (`aprobada`) y `SPEC-23` `D-2` (`aprobada`, v2, 2026-09-24), que adopta versiones con identidad propia por `CE-5`**. Su plan es `PLAN-23`, y `HarnessBackend.tla` modela la regeneración con ese diseño | La acción `Regenerar` es nueva. Antes de implementarla hace falta spec: es un cambio que decide algo nuevo |
| **D-3** | `EJECUCION.md` §3.5 describe un bucle "en orden"; el código usa lista de pendientes | Gana el código, y el documento debe corregirse. Ver CE-3 |
| **D-4** | Rendición incondicional (`EJECUCION.md` regla 1) frente a rendición condicionada a que no quede ninguna invariante `bloqueante` (`docs/architecture.md`) | Gana `docs/architecture.md`. Ver CE-2 |

### Lo que apareció al formalizar y las máquinas no dicen

Cinco cosas. Las tres primeras son huecos; las dos últimas, propiedades que el
sistema tiene sin que nadie las haya escrito.

1. **Nadie dice qué pasa al reanudar un capítulo con la escalera agotada.** Ni
   `EJECUCION.md` §6, ni la máquina del trabajo, ni la de la escena. El código
   lo resuelve de hecho, por re-derivar del disco, pero no porque alguien lo
   decidiera. Es CE-4.
2. **Una versión publicada no tiene identidad.** Nada la distingue de otra con
   los mismos capítulos. Sin identidad, "se conserva la versión anterior" no es
   comprobable ni siquiera en principio. Es CE-5.
3. **Dos caminos distintos llevan a publicar algo que no pasó las puertas** —la
   escalera agotada y el freno de delegaciones— y están escritos en sitios
   distintos (reglas 1 y 6) sin referenciarse. Juntos hacen inalcanzable la
   primera invariante del enunciado, y por separado cada uno parece razonable.
4. **La reanudación es segura por una razón que ningún documento reivindica:**
   el estado se re-deriva del disco en vez de recordarse. Esa frase está en un
   docstring y debería estar en la máquina de estados, porque es lo que hace que
   la reanudación no duplique ni pierda nada.
5. **`copiar_novela()` solo se invoca desde `/api/ampliar`.** Cualquier otro
   camino que regenere se lleva por delante la versión anterior. La protección
   existe pero está enganchada a un solo sitio.

### Estado de la verificación

| Ejecución | Configuración | Resultado |
| --- | --- | --- |
| Corregida | `HarnessNovela.cfg` | **Pasa.** 10.649 estados generados, 4.856 distintos, profundidad 30 |
| Código de hoy | `CodigoDeHoy.cfg` | Falla `NuncaPierdeCapitulos` a los 11 estados (CE-1) |

#### Cada invariante con su caso negativo

Una invariante que nunca ha fallado no está verificada, solo declarada. Esta es
la prueba de que cada una puede fallar:

| Invariante | Caso negativo que la rompe |
| --- | --- |
| `NuncaPublicaSinValidar` | CE-2, con `ExigirValidacionCompleta = FALSE` |
| `NuncaPierdeCapitulos` | CE-1, con `PublicarAlAgotarTope = TRUE` |
| `NoReescribeCerrados` | CE-3, con el avance por contador |
| `ReintentosAcotados` | Mutante con el guardián de `Escribir` eliminado y el tipo ampliado: falla a los 84 estados |
| `VersionesSoloCrecen` | CE-5, con `ConservarVersionAlRegenerar = FALSE` |
| `Terminacion` | CE-4, mutante sin la segunda rama de `AgotarEscalera` |
| `NoSaltaCapitulos` | **Ninguno.** No ha fallado en ninguna de las seis ejecuciones |

**`NoSaltaCapitulos` no tiene caso negativo, y conviene decirlo en vez de
contarla como cobertura.** Con el avance por lista de pendientes es cierta por
construcción, y donde podría fallar —el avance por contador— salta antes
`NoReescribeCerrados`. Se mantiene porque es la que se rompería si alguien
reintrodujera un cursor, pero hoy no está demostrando nada que otra no
demuestre ya.
