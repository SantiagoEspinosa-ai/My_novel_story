---------------------------- MODULE HarnessBackend ----------------------------
(***************************************************************************)
(* El flujo de generacion de la novela regalo TAL COMO LO HACE `backend/`.  *)
(*                                                                          *)
(*   configuracion -> planificacion -> escritura de capitulo -> validacion  *)
(*   -> puerta de publicacion -> version publicada                          *)
(*                                                                          *)
(* mas los tres caminos que complican la linea recta: los reintentos (seis  *)
(* topes distintos, cada uno con su contador), la reanudacion tras una      *)
(* caida y la regeneracion pedida por el lector.                            *)
(*                                                                          *)
(* Sustituye a `HarnessNovela.tla`, que modelaba el flujo de la rama `main` *)
(* (`src/`, `EJECUCION.md`) y se conserva como historia: sus CE-1..CE-5     *)
(* siguen valiendo para lo que describian. Los identificadores de sus       *)
(* invariantes se mantienen aqui con el mismo nombre y el mismo sentido.    *)
(*                                                                          *)
(* QUE ES CADA PASO. Un paso de TLA+ es lo que el codigo deja escrito en la *)
(* base en UNA transaccion. Por eso `Consolidar` y `MarcarConsolidada` son  *)
(* dos acciones y no una: `aplicar.consolidar` y `repo.marcar_consolidada`  *)
(* hacen dos `with con:` seguidos, y una caida puede caer entre los dos.    *)
(* La tabla accion -> funcion esta en README.md.                            *)
(*                                                                          *)
(* LOS INTERRUPTORES. Cada constante booleana vale TRUE con lo que hace el  *)
(* codigo hoy. `BackendDeHoy.cfg` los pone asi y FALLA; `HarnessBackend.cfg`*)
(* los pone con la correccion propuesta y PASA. La diferencia entre las dos *)
(* ejecuciones es la lista de hallazgos (F-110..F-114 y F-116 en           *)
(* `docs/verification.md`). `VigenteEsLaUltimaCreada` y                     *)
(* `RondasDePuertaPorObra` no son de `backend/` sino del diseno aprobado de *)
(* `PLAN-23`, que se esta escribiendo en otra rama. Y                       *)
(* `ConservarVersionAlRegenerar` vale TRUE en las dos: existe para su caso  *)
(* negativo (CE-5).                                                         *)
(***************************************************************************)

EXTENDS Naturals, FiniteSets, Sequences

CONSTANTS
    NumCapitulos,             \* Modelo pequeno: 5 (el real: 10, `EXTENSION["capitulos"]`).
    ReescriturasDelEditor,    \* `topes.reescrituras_del_editor`. Modelo: 2 reintentos.
    ReescriturasPorVetada,    \* `topes.reescrituras_por_vetada` (INV-21 e INV-22 comparten).
    ReintentosDeTransporte,   \* `topes.reintentos_de_transporte`; tambien el tope de formato del plan (F-68).
    RevisionesDePlan,         \* `topes.revisiones_de_plan`.
    ReintentosDePublicacion,  \* `topes.reintentos_de_publicacion` (SPEC-30).
    TopeDelegaciones,         \* `topes.delegaciones_por_obra`, en ciclos del Escritor.
    MaxCaidas,                \* Cota de caidas, para que el modelo sea finito.
    MaxRegeneraciones,        \* Cota de cambios del lector, por lo mismo.
    \* --- Interruptores de `backend/`: TRUE = el codigo de hoy ---------------
    ReanudarReiniciaContadores,    \* F-110 y F-111
    DosTransaccionesAlConsolidar,  \* F-112
    PuertaAceptaSinVeredicto,      \* F-113
    TopePorCapitulo,               \* F-114
    ReanudarSaltaLaMemoria,        \* F-116
    \* --- Interruptores del diseno de `PLAN-23` (codigo en otra rama) ------
    VigenteEsLaUltimaCreada,       \* `brief.version_vigente` de PLAN-23 A3
    RondasDePuertaPorObra,         \* `veredicto_de_publicacion` con clave (obra, ronda)
    ConservarVersionAlRegenerar    \* TRUE = el disparador de A3; FALSE = el caso negativo de CE-5

\* `novela.py`: `tope_intentos=1 + sistema.topes.reescrituras_del_editor`.
MaxIntentos == 1 + ReescriturasDelEditor
\* Borradores que un capitulo puede dejar en UNA ejecucion: cada intento de
\* calidad y cada reescritura por vetada guardan borrador (`bucle.generar` lo
\* guarda antes de las puertas); el fallo de transporte y el de contrato, no.
MaxBorradores == MaxIntentos + ReescriturasPorVetada
\* Filas de `plan_de_obra` que una ejecucion puede escribir: cada ronda y cada
\* plan fuera de esquema, mas el que agota el tope de formato.
MaxFilasPlan == RevisionesDePlan + ReintentosDeTransporte + 1

Capitulos == 1..NumCapitulos
Menor(S) == CHOOSE x \in S : \A y \in S : x =< y

Fases == {"configuracion", "planificacion", "montaje", "escritura", "validacion",
          "rindiendo", "marcando", "consolidando_rendida", "resumen", "puerta",
          "reescritura_puerta", "publicada", "detenido", "caido"}

\* Por que se detuvo. Uno por cada `g.parada["motivo"]` y cada `return` de
\* `publicacion.publicar`, mas `plan` (`PlanNoAprobado`).
Motivos == {"ninguno", "plan", "transporte", "contrato", "vetada", "bloqueante",
            "ya_consolidada", "tope_delegaciones", "reverificacion", "lean",
            "no_reintentable", "tope_publicacion"}

\* La columna `escena.estado` que lee el bucle. `generada` cubre tambien
\* `en_revision`: el bucle no distingue entre las dos.
EstadosDeEscena == {"pendiente", "generada", "consolidada", "rendida"}

\* `estado_de_verificacion` de PLAN-23 A0, mas `propia`: el capitulo se escribio
\* en esta version y paso sus propias puertas.
EstadosDeVerificacion == {"propia", "verificada", "sin_reverificar", "fallida"}

VARIABLES
    fase, motivo, actual,
    \* Planificacion. `rondas`, `fallosFormato` y `versionPlan` viven en la
    \* memoria de `planificar`; `filasPlan` es la tabla `plan_de_obra`.
    planAprobado, filasPlan, filasEscritas, rondas, rondasTotales,
    fallosFormato, fallosTotales, versionPlan,
    \* Por capitulo, en la base.
    estado,     \* escena.estado
    delta,      \* fila en `escena_consolidada`: el delta esta en el canon
    memoria,    \* corrio el bloque de despues de consolidar (resumen, imprescindibles, fichas)
    juzgado,    \* el Editor dio veredicto sobre el texto aceptado
    verif,      \* estado_de_verificacion en la version en curso (PLAN-23)
    \* Del capitulo en curso. Los tres primeros, en la memoria de `_intentar`.
    numero, reescrituras, transporte,
    borradores, \* `repo.intentos_de`: cuantos borradores tiene, en la base
    ciclos,     \* fantasma: ciclos del Escritor en la obra (satura en Tope+1)
    \* Puerta y versiones.
    rondasObra,    \* `veredictos.rondas(con, obra)`: filas de `veredicto_de_publicacion`
    rondasVersion, \* fantasma: rondas de la version en curso
    creadas, vigente, enCurso, publicadas, montado,
    caidas, regeneraciones, salida

planVars  == <<planAprobado, filasPlan, filasEscritas, rondas, rondasTotales,
               fallosFormato, fallosTotales, versionPlan>>
capVars   == <<estado, delta, memoria, juzgado, verif>>
cicloVars == <<numero, reescrituras, transporte, borradores, ciclos>>
verVars   == <<rondasObra, rondasVersion, creadas, vigente, enCurso, publicadas, montado>>
cotaVars  == <<caidas, regeneraciones, salida>>
vars == <<fase, motivo, actual, planVars, capVars, cicloVars, verVars, cotaVars>>

\* `YA_HECHAS` de `orquestacion/obra.py`: lo que el bucle salta.
HechoEn(est, c) == est[c] \in {"consolidada", "rendida"}
Hecho(c) == HechoEn(estado, c)

\* Lo que queda por hacer en una posicion. Con `ReanudarSaltaLaMemoria` (hoy)
\* un capitulo hecho sin su bloque de memoria NO cuenta como trabajo: el bucle
\* lo salta por su estado y nadie vuelve a resumirlo.
TrabajoEn(est, ver, mem, c) ==
    \/ ~HechoEn(est, c)
    \/ ver[c] = "sin_reverificar"
    \/ (~ReanudarSaltaLaMemoria /\ ~mem[c])

\* El siguiente capitulo: el menor con trabajo. Es lo que hacen juntos el `for`
\* de `novela._escribir` (en el orden del plan) y el `continue` de
\* `generar_obra` sobre `YA_HECHAS`. NumCapitulos+1 = ninguno.
SiguienteEn(est, ver, mem) ==
    LET P == {c \in Capitulos : TrabajoEn(est, ver, mem, c)}
    IN IF P = {} THEN NumCapitulos + 1 ELSE Menor(P)

FaseDe(p, est, ver, mem) ==
    IF p > NumCapitulos THEN "puerta"
    ELSE IF HechoEn(est, p) /\ ver[p] # "sin_reverificar" THEN "resumen"
    ELSE "escritura"

TypeOK ==
    /\ fase \in Fases
    /\ motivo \in Motivos
    /\ actual \in 1..(NumCapitulos + 1)
    /\ planAprobado \in BOOLEAN
    /\ filasPlan \subseteq 1..MaxFilasPlan
    /\ filasEscritas \in 0..(MaxFilasPlan * (MaxCaidas + 1))
    /\ rondas \in 0..RevisionesDePlan
    /\ rondasTotales \in 0..(RevisionesDePlan * (MaxCaidas + 1))
    /\ fallosFormato \in 0..(ReintentosDeTransporte + 1)
    /\ fallosTotales \in 0..((ReintentosDeTransporte + 1) * (MaxCaidas + 1))
    /\ versionPlan \in 0..MaxFilasPlan
    /\ estado \in [Capitulos -> EstadosDeEscena]
    /\ delta \in [Capitulos -> BOOLEAN]
    /\ memoria \in [Capitulos -> BOOLEAN]
    /\ juzgado \in [Capitulos -> BOOLEAN]
    /\ verif \in [Capitulos -> EstadosDeVerificacion]
    /\ numero \in 0..MaxIntentos
    /\ reescrituras \in 0..ReescriturasPorVetada
    /\ transporte \in 0..ReintentosDeTransporte
    /\ borradores \in 0..(MaxBorradores * (MaxCaidas + 1))
    /\ ciclos \in 0..(TopeDelegaciones + 1)
    /\ rondasObra \in Nat
    /\ rondasVersion \in Nat
    /\ creadas \in 0..(1 + MaxRegeneraciones)
    /\ vigente \in 0..(1 + MaxRegeneraciones)
    /\ enCurso \in 0..(1 + MaxRegeneraciones)
    /\ montado \in BOOLEAN
    /\ caidas \in 0..MaxCaidas
    /\ regeneraciones \in 0..MaxRegeneraciones
    /\ salida \in {"cascada", "selectiva"}

\* `salida` es la de PLAN-23 B2: la fija una regla sobre un numero medido
\* (<= 3 -> S-1 cascada; > 3 -> S-2 selectiva) y no cambia en la vida de la
\* obra. El numero no existe todavia, asi que TLC recorre las dos.
Init ==
    /\ fase = "configuracion"
    /\ motivo = "ninguno"
    /\ actual = 1
    /\ planAprobado = FALSE
    /\ filasPlan = {}
    /\ filasEscritas = 0
    /\ rondas = 0
    /\ rondasTotales = 0
    /\ fallosFormato = 0
    /\ fallosTotales = 0
    /\ versionPlan = 0
    /\ estado = [c \in Capitulos |-> "pendiente"]
    /\ delta = [c \in Capitulos |-> FALSE]
    /\ memoria = [c \in Capitulos |-> FALSE]
    /\ juzgado = [c \in Capitulos |-> FALSE]
    /\ verif = [c \in Capitulos |-> "propia"]
    /\ numero = 0
    /\ reescrituras = 0
    /\ transporte = 0
    /\ borradores = 0
    /\ ciclos = 0
    /\ rondasObra = 0
    /\ rondasVersion = 0
    /\ creadas = 0
    /\ vigente = 0
    /\ enCurso = 0
    /\ publicadas = << >>
    /\ montado = FALSE
    /\ caidas = 0
    /\ regeneraciones = 0
    /\ salida \in {"cascada", "selectiva"}

Detener(m) == fase' = "detenido" /\ motivo' = m

(***************************************************************************)
(* 1. CONFIGURACION                                                         *)
(***************************************************************************)

Configurar ==
    /\ fase = "configuracion"
    /\ fase' = "planificacion"
    /\ UNCHANGED <<motivo, actual, planVars, capVars, cicloVars, verVars, cotaVars>>

(***************************************************************************)
(* 2. PLANIFICACION: `planificacion.reanudar_o_planificar` y `planificar`.  *)
(* Cada ronda guarda su fila en `plan_de_obra` con la clave (obra, version) *)
(* y `INSERT OR REPLACE`. Un plan fuera de esquema NO gasta ronda (F-68):   *)
(* tiene su propio contador y su propio tope, el de transporte.             *)
(***************************************************************************)

EscribirFilaPlan ==
    /\ versionPlan' = versionPlan + 1
    /\ filasPlan' = filasPlan \cup {versionPlan + 1}
    /\ filasEscritas' = filasEscritas + 1

PlanFueraDeEsquema ==
    /\ fase = "planificacion"
    /\ ~planAprobado
    /\ EscribirFilaPlan
    /\ fallosFormato' = fallosFormato + 1
    /\ fallosTotales' = fallosTotales + 1
    /\ IF fallosFormato + 1 > ReintentosDeTransporte
       THEN Detener("plan")
       ELSE UNCHANGED <<fase, motivo>>
    /\ UNCHANGED <<actual, planAprobado, rondas, rondasTotales, capVars, cicloVars,
                   verVars, cotaVars>>

\* Un hueco de cobertura (`origen = codigo`) o un rechazo del Revisor: los dos
\* gastan ronda y tienen el mismo efecto sobre el estado.
RechazarPlan ==
    /\ fase = "planificacion"
    /\ ~planAprobado
    /\ EscribirFilaPlan
    /\ rondas' = rondas + 1
    /\ rondasTotales' = rondasTotales + 1
    /\ IF rondas + 1 >= RevisionesDePlan
       THEN Detener("plan")
       ELSE UNCHANGED <<fase, motivo>>
    /\ UNCHANGED <<actual, planAprobado, fallosFormato, fallosTotales, capVars,
                   cicloVars, verVars, cotaVars>>

AprobarPlan ==
    /\ fase = "planificacion"
    /\ ~planAprobado
    /\ EscribirFilaPlan
    /\ rondas' = rondas + 1
    /\ rondasTotales' = rondasTotales + 1
    /\ planAprobado' = TRUE
    /\ fase' = "montaje"
    /\ UNCHANGED <<motivo, actual, fallosFormato, fallosTotales, capVars, cicloVars,
                   verVars, cotaVars>>

\* F-67: la obra ya tiene plan aprobado; no se vuelve a pagar.
ReutilizarPlan ==
    /\ fase = "planificacion"
    /\ planAprobado
    /\ fase' = "montaje"
    /\ UNCHANGED <<motivo, actual, planVars, capVars, cicloVars, verVars, cotaVars>>

(***************************************************************************)
(* `novela.montar`: si la escaleta existe no toca nada. Despues, el bucle   *)
(* empieza por el primer capitulo con trabajo.                              *)
(***************************************************************************)

Montar ==
    /\ fase = "montaje"
    /\ LET p == SiguienteEn(estado, verif, memoria)
       IN /\ actual' = p
          \* Con los contadores en la base, un capitulo que ya gasto sus intentos
          \* vuelve a rendirse, no a escribirse: el checkpoint tiene que rehacer la
          \* decision y no solo recordar el contador (CE-4, y CE-6 aqui).
          /\ fase' = IF p = actual /\ p \in Capitulos /\ ~HechoEn(estado, p)
                        /\ numero >= MaxIntentos
                     THEN "rindiendo"
                     ELSE FaseDe(p, estado, verif, memoria)
          /\ IF p = actual
             THEN UNCHANGED <<numero, reescrituras, transporte, borradores>>
             ELSE /\ numero' = 0 /\ reescrituras' = 0 /\ transporte' = 0
                  /\ borradores' = 0
    /\ montado' = TRUE
    \* PLAN-23 A3: `alta_de_obra` crea la version 1.
    /\ creadas' = IF montado THEN creadas ELSE 1
    /\ enCurso' = IF montado THEN enCurso ELSE 1
    /\ vigente' = IF montado \/ ~VigenteEsLaUltimaCreada THEN vigente ELSE 1
    /\ UNCHANGED <<motivo, planVars, capVars, ciclos, rondasObra, rondasVersion,
                   publicadas, cotaVars>>

(***************************************************************************)
(* 3. ESCRITURA DE UN CAPITULO: `obra.generar_obra` -> `_intentar` ->       *)
(* `ciclo.ejecutar` -> `bucle.generar`. Un capitulo es una escena.          *)
(***************************************************************************)

\* `generar_obra` comprueba el tope ANTES de cada escena, con el `g` que acaba
\* de crear. `novela._escribir` llama a `generar_obra` una vez por capitulo y
\* cada capitulo tiene una escena, asi que lo que compara es SIEMPRE 0: el
\* tope de la obra no salta nunca (F-114).
AlEmpezarCapitulo == numero = 0 /\ reescrituras = 0 /\ transporte = 0
PresupuestoAgotado ==
    IF TopePorCapitulo
    THEN AlEmpezarCapitulo /\ 0 >= TopeDelegaciones
    ELSE ciclos >= TopeDelegaciones

PuedeEscribir ==
    /\ fase = "escritura"
    /\ actual \in Capitulos
    /\ ~Hecho(actual)
    /\ numero < MaxIntentos

\* Un ciclo del Escritor; el contador fantasma satura para que el modelo sea finito.
Ciclo == ciclos' = IF ciclos > TopeDelegaciones THEN ciclos ELSE ciclos + 1

AgotarTope ==
    /\ PuedeEscribir
    /\ PresupuestoAgotado
    /\ Detener("tope_delegaciones")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, verVars, cotaVars>>

\* F-72: el Escritor se reintenta desde el ciclo, con su propio contador.
FalloDeTransporteDelEscritor ==
    /\ PuedeEscribir
    /\ ~PresupuestoAgotado
    /\ Ciclo
    /\ IF transporte < ReintentosDeTransporte
       THEN /\ transporte' = transporte + 1
            /\ UNCHANGED <<fase, motivo>>
       ELSE /\ Detener("transporte")
            /\ UNCHANGED transporte
    /\ UNCHANGED <<actual, planVars, capVars, numero, reescrituras, borradores,
                   verVars, cotaVars>>

\* Contrato roto o contexto que no cabe (`RF-26`): no se reintenta (`O-3`).
FalloDeContrato ==
    /\ PuedeEscribir
    /\ ~PresupuestoAgotado
    /\ Ciclo
    /\ Detener("contrato")
    /\ UNCHANGED <<actual, planVars, capVars, numero, reescrituras, transporte,
                   borradores, verVars, cotaVars>>

\* El Escritor contesta y el borrador se guarda, antes de ninguna puerta.
Escribir ==
    /\ PuedeEscribir
    /\ ~PresupuestoAgotado
    /\ Ciclo
    /\ borradores' = borradores + 1
    /\ estado' = [estado EXCEPT ![actual] = "generada"]
    /\ fase' = "validacion"
    /\ UNCHANGED <<motivo, actual, planVars, delta, memoria, juzgado, verif,
                   numero, reescrituras, transporte, verVars, cotaVars>>

(***************************************************************************)
(* 4. VALIDACION: las puertas deterministas de `bucle.generar`, las de      *)
(* personalizacion de `ciclo.ejecutar` (INV-21, INV-22, INV-23) y el Editor *)
(* (INV-26). Cada resultado es una accion porque cada uno lleva el bucle a  *)
(* un sitio distinto.                                                       *)
(***************************************************************************)

EnValidacion == fase = "validacion" /\ actual \in Capitulos

\* INV-21 o INV-22: su propio contador, que no gasta intentos de calidad.
PedirReescrituraPorVetada ==
    /\ EnValidacion
    /\ IF reescrituras >= ReescriturasPorVetada
       THEN /\ Detener("vetada")
            /\ UNCHANGED reescrituras
       ELSE /\ reescrituras' = reescrituras + 1
            /\ fase' = "escritura"
            /\ UNCHANGED motivo
    /\ UNCHANGED <<actual, planVars, capVars, numero, transporte, borradores,
                   ciclos, verVars, cotaVars>>

\* Una `bloqueante` de las puertas, o un delta que no entra en el mundo.
Bloquear ==
    /\ EnValidacion
    /\ Detener("bloqueante")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, verVars, cotaVars>>

\* INV-23 (`mayor`) o una nota del Editor bajo el umbral (INV-26): gasta un
\* intento. Agotados, el capitulo se rinde.
FallarCalidad ==
    /\ EnValidacion
    /\ numero' = numero + 1
    /\ fase' = IF numero + 1 < MaxIntentos THEN "escritura" ELSE "rindiendo"
    /\ UNCHANGED <<motivo, actual, planVars, capVars, reescrituras, transporte,
                   borradores, ciclos, verVars, cotaVars>>

\* `aplicar.consolidar`: el delta entra en el canon en su transaccion. Con dos
\* transacciones (hoy) la escena sigue `generada` hasta `MarcarConsolidada`.
Consolidar(juzga) ==
    /\ EnValidacion
    /\ ~delta[actual]
    /\ delta' = [delta EXCEPT ![actual] = TRUE]
    /\ juzgado' = [juzgado EXCEPT ![actual] = juzga]
    /\ IF DosTransaccionesAlConsolidar
       THEN /\ fase' = "marcando"
            /\ UNCHANGED estado
       ELSE /\ estado' = [estado EXCEPT ![actual] = "consolidada"]
            /\ fase' = "resumen"
    /\ UNCHANGED <<motivo, actual, planVars, memoria, verif, cicloVars, verVars,
                   cotaVars>>

\* Sale limpia y el Editor la aprobo.
PasarLimpio == Consolidar(TRUE)

\* Sale limpia porque el Editor NO contesto algo legible: `_editar` guarda un
\* `sin_veredicto` y no lo mete en los hallazgos del intento, asi que la
\* escena se consolida como si hubiera pasado (`SPEC-18` C-3).
PasarSinVeredicto == Consolidar(FALSE)

\* `YaConsolidada`: el delta de esta escena ya estaba en el canon.
ChocarConSuDelta ==
    /\ fase \in {"validacion", "consolidando_rendida"}
    /\ actual \in Capitulos
    /\ delta[actual]
    /\ Detener("ya_consolidada")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, verVars, cotaVars>>

MarcarConsolidada ==
    /\ fase = "marcando"
    /\ estado' = [estado EXCEPT ![actual] = "consolidada"]
    /\ fase' = "resumen"
    /\ UNCHANGED <<motivo, actual, planVars, delta, memoria, juzgado, verif,
                   cicloVars, verVars, cotaVars>>

\* `repo.rendir_escena` y despues `consolidar_y_resumir`: tambien dos
\* transacciones, y en el orden contrario. Aqui el estado va primero.
Rendir ==
    /\ fase = "rindiendo"
    /\ estado' = [estado EXCEPT ![actual] = "rendida"]
    /\ IF DosTransaccionesAlConsolidar
       THEN /\ fase' = "consolidando_rendida"
            /\ UNCHANGED delta
       ELSE /\ delta' = [delta EXCEPT ![actual] = TRUE]
            /\ fase' = "resumen"
    /\ UNCHANGED <<motivo, actual, planVars, memoria, juzgado, verif, cicloVars,
                   verVars, cotaVars>>

ConsolidarRendida ==
    /\ fase = "consolidando_rendida"
    /\ ~delta[actual]
    /\ delta' = [delta EXCEPT ![actual] = TRUE]
    /\ fase' = "resumen"
    /\ UNCHANGED <<motivo, actual, planVars, estado, memoria, juzgado, verif,
                   cicloVars, verVars, cotaVars>>

\* El Resumidor y lo que `generar_obra` hace despues de consolidar: resumen,
\* imprescindibles (INV-24 los lee), hechos establecidos y fichas. Despues, el
\* siguiente capitulo, con contadores nuevos: es otra llamada a `_intentar`.
Resumir ==
    /\ fase = "resumen"
    /\ actual \in Capitulos
    /\ LET mem == [memoria EXCEPT ![actual] = TRUE]
           p   == SiguienteEn(estado, verif, mem)
       IN /\ memoria' = mem
          /\ actual' = p
          /\ fase' = FaseDe(p, estado, verif, mem)
    /\ numero' = 0 /\ reescrituras' = 0 /\ transporte' = 0 /\ borradores' = 0
    /\ UNCHANGED <<motivo, planVars, estado, delta, juzgado, verif, ciclos,
                   verVars, cotaVars>>

(***************************************************************************)
(* PLAN-23 A4 y B-S2.1: un capitulo compartido y posterior al cambio se     *)
(* reverifica con reglas, sin modelo, contra el mundo de la version nueva.  *)
(* Si falla, se para y decide una persona.                                  *)
(***************************************************************************)

Reverificar(ok) ==
    /\ fase = "escritura"
    /\ actual \in Capitulos
    /\ Hecho(actual)
    /\ verif[actual] = "sin_reverificar"
    /\ IF ok
       THEN LET ver == [verif EXCEPT ![actual] = "verificada"]
                p   == SiguienteEn(estado, ver, memoria)
            IN /\ verif' = ver
               /\ actual' = p
               /\ fase' = FaseDe(p, estado, ver, memoria)
               /\ UNCHANGED motivo
       ELSE /\ verif' = [verif EXCEPT ![actual] = "fallida"]
            /\ Detener("reverificacion")
            /\ UNCHANGED actual
    /\ numero' = 0 /\ reescrituras' = 0 /\ transporte' = 0 /\ borradores' = 0
    /\ UNCHANGED <<planVars, estado, delta, memoria, juzgado, ciclos, verVars,
                   cotaVars>>

(***************************************************************************)
(* 5. PUERTA DE PUBLICACION: `orquestacion/publicacion.publicar`. Cada      *)
(* evaluacion guarda una fila en `veredicto_de_publicacion`, y el tope se   *)
(* lee de ahi, asi que relanzar no lo reinicia (la leccion de CE-4).        *)
(***************************************************************************)

RondasPrevias == IF RondasDePuertaPorObra THEN rondasObra ELSE rondasVersion
HayRendido == \E c \in Capitulos : estado[c] = "rendida"
SinJuzgar  == \E c \in Capitulos : ~juzgado[c]

PuedeEvaluar == fase = "puerta" /\ RondasPrevias <= ReintentosDePublicacion
Evaluar == /\ rondasObra' = rondasObra + 1
           /\ rondasVersion' = rondasVersion + 1

\* Lo que ha pasado todos los validadores: consolidado (no rendido), juzgado
\* por el Editor y, si es de una version regenerada, verificado en ella.
Limpios == {c \in Capitulos : /\ estado[c] = "consolidada"
                              /\ juzgado[c]
                              /\ verif[c] \in {"propia", "verificada"}}

PuertaAgotada ==
    /\ fase = "puerta"
    /\ RondasPrevias > ReintentosDePublicacion
    /\ Detener("tope_publicacion")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, verVars, cotaVars>>

\* `auditoria/publicacion.decidir` sin condiciones. Mira INV-29 (rendidos),
\* las `bloqueante`, Lean (INV-28) e INV-27. NO mira INV-26 `sin_veredicto`,
\* que es `mayor`: por eso, hoy, `SinJuzgar` no cierra la puerta (F-113).
PublicarVersion ==
    /\ PuedeEvaluar
    /\ ~HayRendido
    /\ ~PuertaAceptaSinVeredicto => ~SinJuzgar
    /\ Evaluar
    /\ LET v == [numero    |-> enCurso,
                 capitulos |-> {c \in Capitulos : Hecho(c)},
                 limpios   |-> Limpios]
       IN publicadas' = IF ConservarVersionAlRegenerar \/ publicadas = << >>
                        THEN Append(publicadas, v)
                        ELSE [publicadas EXCEPT ![Len(publicadas)] = v]
    /\ vigente' = IF VigenteEsLaUltimaCreada THEN vigente ELSE enCurso
    /\ fase' = "publicada"
    /\ UNCHANGED <<motivo, actual, planVars, capVars, cicloVars, creadas, enCurso,
                   montado, cotaVars>>

\* INV-28: Lean con violaciones, sin veredicto o sin ejecutar. Vuelve al Editor
\* como diagnostico y se detiene sin reescribir (`RF-06`).
FallarLean ==
    /\ PuedeEvaluar
    /\ Evaluar
    /\ Detener("lean")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, creadas, vigente, enCurso,
                   publicadas, montado, cotaVars>>

\* INV-29 (un capitulo rendido) o una `bloqueante` de obra (INV-24, INV-21):
\* no se arregla reescribiendo. Puede pasar siempre; si hay un rendido, es lo
\* unico que puede pasar ademas de Lean.
FallarSinArreglo ==
    /\ PuedeEvaluar
    /\ Evaluar
    /\ Detener("no_reintentable")
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, creadas, vigente, enCurso,
                   publicadas, montado, cotaVars>>

\* INV-27 abierto (y, corregido F-113, un capitulo sin veredicto del Editor):
\* el Editor da instrucciones y se reescribe a delta fijo, salvo tope.
PedirReescrituraDeObra ==
    /\ PuedeEvaluar
    /\ ~HayRendido
    /\ Evaluar
    /\ IF RondasPrevias + 1 > ReintentosDePublicacion
       THEN Detener("tope_publicacion")
       ELSE /\ fase' = "reescritura_puerta"
            /\ UNCHANGED motivo
    /\ UNCHANGED <<actual, planVars, capVars, cicloVars, creadas, vigente, enCurso,
                   publicadas, montado, cotaVars>>

\* `obra.reescribir_capitulo`: pasa las puertas de texto y el Editor, y solo se
\* acepta si el delta no cambia. El canon no se mueve; lo que cambia es el
\* texto aceptado y, con el, si el Editor lo juzgo.
ReescribirEnPuerta ==
    /\ fase = "reescritura_puerta"
    /\ \E c \in Capitulos, r \in {"juzgada", "sin_veredicto", "rechazada"} :
         /\ estado[c] = "consolidada"
         /\ juzgado' = IF r = "rechazada" THEN juzgado
                       ELSE [juzgado EXCEPT ![c] = (r = "juzgada")]
    /\ fase' = "puerta"
    /\ UNCHANGED <<motivo, actual, planVars, estado, delta, memoria, verif,
                   cicloVars, verVars, cotaVars>>

(***************************************************************************)
(* 6. REGENERACION POR CAMBIO DEL LECTOR: el diseno aprobado de PLAN-23.    *)
(*   A7   la peticion (un hecho o un nombre) y los capitulos que toca.      *)
(*   A3   la version n+1 se crea con identidad: compartidos por referencia  *)
(*        y nuevos, y ninguna fila de la anterior cambia.                   *)
(*   B-S1.1 cascada: del primer capitulo que usa el hecho hasta el final.   *)
(*   B-S2.1 selectiva: solo esos; los posteriores compartidos se            *)
(*        reverifican.                                                      *)
(* El conjunto S es cualquiera no vacio: el modelo no sabe que hechos usa   *)
(* cada capitulo, y suponer uno seria verificar un caso y no la regla.      *)
(***************************************************************************)

Regenerar ==
    /\ fase = "publicada"
    /\ regeneraciones < MaxRegeneraciones
    /\ \E S \in (SUBSET Capitulos) \ {{}} :
         LET k       == Menor(S)
             Cambian == IF salida = "cascada" THEN k..NumCapitulos ELSE S
         IN /\ estado'  = [c \in Capitulos |-> IF c \in Cambian THEN "pendiente" ELSE estado[c]]
            /\ delta'   = [c \in Capitulos |-> IF c \in Cambian THEN FALSE ELSE delta[c]]
            /\ memoria' = [c \in Capitulos |-> IF c \in Cambian THEN FALSE ELSE memoria[c]]
            /\ juzgado' = [c \in Capitulos |-> IF c \in Cambian THEN FALSE ELSE juzgado[c]]
            /\ verif'   = [c \in Capitulos |->
                              IF c \in Cambian THEN "propia"
                              ELSE IF c > k THEN "sin_reverificar"
                              ELSE verif[c]]
            /\ actual' = k
    /\ regeneraciones' = regeneraciones + 1
    /\ creadas' = creadas + 1
    /\ enCurso' = creadas + 1
    /\ vigente' = IF VigenteEsLaUltimaCreada THEN creadas + 1 ELSE vigente
    /\ rondasVersion' = 0
    /\ numero' = 0 /\ reescrituras' = 0 /\ transporte' = 0 /\ borradores' = 0
    /\ fase' = "escritura"
    /\ UNCHANGED <<motivo, planVars, ciclos, rondasObra, publicadas, montado,
                   caidas, salida>>

(***************************************************************************)
(* CAIDA Y REANUDACION. Caer es lo que el sistema sufre: el proceso muere o *)
(* un agente que no es el Escritor agota sus reintentos y `FalloDeTransporte`*)
(* sube hasta `novela_regalo.main`, que dice "relanzar reanuda". Se pierde  *)
(* todo lo que vive en memoria; sobrevive la base.                          *)
(***************************************************************************)

Caer ==
    /\ fase \in {"planificacion", "montaje", "escritura", "validacion", "rindiendo",
                 "marcando", "consolidando_rendida", "resumen", "puerta",
                 "reescritura_puerta"}
    /\ caidas < MaxCaidas
    /\ caidas' = caidas + 1
    /\ fase' = "caido"
    /\ UNCHANGED <<motivo, actual, planVars, capVars, cicloVars, verVars,
                   regeneraciones, salida>>

\* Relanzar `novela_regalo.py`: todo se re-deriva de la base. Los contadores
\* de `planificar` y de `_intentar` son variables locales y vuelven a cero
\* (hoy); corregido, se leen de la base como ya hace la puerta.
Reanudar ==
    /\ fase = "caido"
    /\ fase' = "planificacion"
    /\ IF ReanudarReiniciaContadores
       THEN /\ rondas' = 0 /\ fallosFormato' = 0 /\ versionPlan' = 0
            /\ numero' = 0 /\ reescrituras' = 0 /\ transporte' = 0
       ELSE UNCHANGED <<rondas, fallosFormato, versionPlan, numero, reescrituras,
                        transporte>>
    /\ UNCHANGED <<motivo, actual, planAprobado, filasPlan, filasEscritas,
                   rondasTotales, fallosTotales, capVars, borradores, ciclos,
                   verVars, cotaVars>>

\* Estado terminal: sin este paso de repeticion TLC confundiria "aqui se
\* acaba" con "aqui se atasca".
Terminado ==
    /\ \/ fase = "detenido"
       \/ fase = "publicada" /\ regeneraciones = MaxRegeneraciones
    /\ UNCHANGED vars

\* Todo lo que el sistema hace por si mismo, mas `Reanudar`, que es una persona
\* relanzando el guion. Quedan fuera `Caer` (un fallo, no una obligacion) y
\* `Regenerar` (el lector puede no pedir nada).
Avanza ==
    \/ Configurar \/ PlanFueraDeEsquema \/ RechazarPlan \/ AprobarPlan
    \/ ReutilizarPlan \/ Montar
    \/ AgotarTope \/ FalloDeTransporteDelEscritor \/ FalloDeContrato \/ Escribir
    \/ PedirReescrituraPorVetada \/ Bloquear \/ FallarCalidad
    \/ PasarLimpio \/ PasarSinVeredicto \/ ChocarConSuDelta \/ MarcarConsolidada
    \/ Rendir \/ ConsolidarRendida \/ Resumir
    \/ Reverificar(TRUE) \/ Reverificar(FALSE)
    \/ PuertaAgotada \/ PublicarVersion \/ FallarLean \/ FallarSinArreglo
    \/ PedirReescrituraDeObra \/ ReescribirEnPuerta
    \/ Reanudar

Next == Avanza \/ Caer \/ Regenerar \/ Terminado

Spec == Init /\ [][Next]_vars /\ WF_vars(Avanza)

(***************************************************************************)
(* INVARIANTES DE SEGURIDAD. Las cinco primeras conservan el nombre y el    *)
(* sentido de `HarnessNovela.tla`.                                          *)
(***************************************************************************)

\* S-1. Nunca se publica una version con un capitulo que no paso todos los
\* validadores.
NuncaPublicaSinValidar ==
    \A i \in 1..Len(publicadas) : publicadas[i].capitulos = publicadas[i].limpios

\* S-2a. Ninguna version publicada pierde capitulos.
NuncaPierdeCapitulos ==
    \A i \in 1..Len(publicadas) : publicadas[i].capitulos = Capitulos

\* S-2b. No se reescribe un capitulo cuyo delta ya esta en el canon: la mitad
\* "no duplica" de la reanudacion.
NoReescribeCerrados ==
    (fase = "validacion" /\ actual \in Capitulos) => ~delta[actual]

\* S-2c. Nunca se trabaja en un capitulo dejando atras uno sin hacer: la
\* mitad "no pierde".
NoSaltaCapitulos ==
    (fase \in {"escritura", "validacion"} /\ actual \in Capitulos) =>
        \A p \in 1..(actual - 1) : Hecho(p) /\ verif[p] \in {"propia", "verificada"}

\* S-2d. INV-05: solo se escribe sobre un mundo al que ya se aplicaron los
\* deltas de todo lo anterior.
SoloSobreConsolidadas ==
    (fase \in {"escritura", "validacion"} /\ actual \in Capitulos) =>
        \A p \in 1..(actual - 1) : delta[p]

\* S-2e. Al llegar a la puerta, todo capitulo tiene su memoria: el juicio de
\* obra (INV-27) lee los resumenes y INV-24 los imprescindibles.
MemoriaCompleta ==
    fase = "puerta" => \A c \in Capitulos : memoria[c]

\* S-3. Ningun contador supera su tope, contando todas las ejecuciones. La
\* holgura `caidas` de los borradores es honesta, no un apano: una caida entre
\* guardar el borrador y juzgarlo se lleva ese intento sin que nadie lo juzgue,
\* y eso cuesta un borrador por caida. Lo que no puede costar es un tope
\* entero nuevo por cada relanzamiento, que es lo que pasa hoy (F-110).
ReintentosAcotados ==
    /\ borradores <= MaxBorradores + caidas
    /\ rondasTotales <= RevisionesDePlan
    /\ fallosTotales <= ReintentosDeTransporte + 1
    /\ rondasVersion <= ReintentosDePublicacion + 1

\* S-3b. Ninguna ronda del plan se pierde: cada una tiene su fila.
RondasDePlanConservadas ==
    Cardinality(filasPlan) = filasEscritas

\* S-3c. El tope de delegaciones de la obra acota la obra.
DelegacionesAcotadas ==
    ciclos <= TopeDelegaciones

\* S-3d. Una version que se detiene por tope de puerta gasto SUS rondas.
CadaVersionTieneSuTope ==
    (fase = "detenido" /\ motivo = "tope_publicacion") =>
        rondasVersion > ReintentosDePublicacion

\* S-4b. Lo que el lector ve es una version publicada.
LectorVeLoPublicado ==
    Len(publicadas) > 0 =>
        \E i \in 1..Len(publicadas) : publicadas[i].numero = vigente

\* S-4. La version anterior se conserva siempre. Propiedad de accion.
VersionesSoloCrecen ==
    [][ /\ Len(publicadas') >= Len(publicadas)
        /\ \A i \in 1..Len(publicadas) : publicadas'[i] = publicadas[i] ]_vars

(***************************************************************************)
(* VIVACIDAD. Toda generacion acaba publicando o detenida, y se queda ahi   *)
(* hasta que el lector pida otro cambio. Nunca da vueltas sin fin.          *)
(***************************************************************************)

Terminacion == <>[](fase \in {"publicada", "detenido"})

=============================================================================
