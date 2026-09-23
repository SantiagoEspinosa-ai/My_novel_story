# Especificación TLA+ del harness

2026-09-23 · Verificada con TLC 2.19 sobre OpenJDK 21.0.12.1

> **Pendiente para quien lleve esta especificación — `EX-07` de `docs/cobertura-examen.md`.**
> El usuario decidió (2026-09-23) que el entregable es `backend/`, no `main`. La tabla
> "Qué implementa cada acción" tiene que rehacerse contra `backend/`, y el modelo también:
> la escalera `haiku → sonnet → opus` de `Reintentar` desaparece, porque `backend/` usa un
> modelo por agente (`backend/config/sistema.json`). Va a plan, y es de esta especificación.

Modelo formal del flujo de generación de una novela: **configuración →
planificación → escritura → validación → publicación**, más los tres caminos que
lo complican (reintentos, reanudación desde checkpoint y regeneración pedida por
el lector).

---

## El hallazgo: el defecto estaba en el documento, no en el código

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

## Cómo se ejecuta

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

### El tamaño del modelo, y por qué es el que es

`NumCapitulos = 5` y `MaxIntentos = 2` los fija el enunciado. `MaxCaidas = 1` y
`MaxRegeneraciones = 1` los fijamos nosotros, y **no son arbitrarios**: caer y
regenerar son las dos únicas acciones que pueden repetirse sin fin, así que sin
cota el espacio de estados es infinito y TLC no termina nunca. Con 1 ya se
recorre entero el camino caída → reanudación → publicación y el camino
publicación → cambio del lector → republicación, que es todo lo que hay que
verificar: un segundo ciclo no visita ninguna transición nueva.

## Qué implementa cada acción

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

### Lo que el modelo simplifica a propósito

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

## Contraejemplos

Los cinco están reproducidos. Ninguno se arregló en silencio: cada uno lleva el
cambio que provocó y la ejecución que lo demuestra.

### CE-1 · Se publica una novela vacía

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

### CE-2 · Se publica un capítulo que no pasó los validadores

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

### CE-3 · Un cambio del lector en un capítulo reescribe la novela entera

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

### CE-4 · Tras una caída, un capítulo con la escalera agotada bloquea la generación

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

### CE-5 · La propiedad estaba en verde por no poder distinguir nada

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

## Discrepancias entre el código y los documentos

Se documentan y se resuelve a favor del documento, que es lo normativo.

| | Discrepancia | Resolución |
| --- | --- | --- |
| **D-1** | `docs/architecture.md` modela **escenas** con ocho estados y dos puertas humanas (`A-04`: la aceptación la dispara una persona). `main` trabaja por **capítulos** y sin ninguna puerta humana | La especificación modela capítulos, porque es lo que pide el enunciado y lo que existe. **La ausencia de puerta humana es un hueco real**, no una simplificación del modelo |
| **D-2** | La regeneración por cambio del lector **no existía en ningún documento** cuando se escribió esta especificación. No había transición, ni estado, ni versión. **Desde entonces la describen `SPEC-22` `RF-50`..`RF-55` (`aprobada`) y `SPEC-23` `D-2` (`en_revision`), que adopta versiones con identidad propia por `CE-5`**; en `docs/` sigue sin estar | La acción `Regenerar` es nueva. Antes de implementarla hace falta spec: es un cambio que decide algo nuevo |
| **D-3** | `EJECUCION.md` §3.5 describe un bucle "en orden"; el código usa lista de pendientes | Gana el código, y el documento debe corregirse. Ver CE-3 |
| **D-4** | Rendición incondicional (`EJECUCION.md` regla 1) frente a rendición condicionada a que no quede ninguna invariante `bloqueante` (`docs/architecture.md`) | Gana `docs/architecture.md`. Ver CE-2 |

## Lo que apareció al formalizar y las máquinas no dicen

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

## Estado de la verificación

| Ejecución | Configuración | Resultado |
| --- | --- | --- |
| Corregida | `HarnessNovela.cfg` | **Pasa.** 10.649 estados generados, 4.856 distintos, profundidad 30 |
| Código de hoy | `CodigoDeHoy.cfg` | Falla `NuncaPierdeCapitulos` a los 11 estados (CE-1) |

### Cada invariante con su caso negativo

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
