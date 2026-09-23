---------------------------- MODULE HarnessNovela ----------------------------
(***************************************************************************)
(* Especificacion del flujo de generacion de una novela en My_novel_story.  *)
(*                                                                          *)
(* QUE MODELA                                                               *)
(*   configuracion -> planificacion -> escritura -> validacion -> publicada *)
(* mas los tres caminos que complican esa linea recta:                      *)
(*   - reintentos por capitulo (la escalera de modelos),                    *)
(*   - caida y reanudacion desde el checkpoint (`salida/estado.json`),      *)
(*   - regeneracion parcial pedida por el lector sobre una version ya       *)
(*     publicada.                                                           *)
(*                                                                          *)
(* PRINCIPIO DE ESCRITURA: se modela EL SISTEMA QUE HAY, no el que          *)
(* quisieramos. Donde `EJECUCION.md` describe un comportamiento que         *)
(* contradice una invariante del enunciado, ese comportamiento se modela    *)
(* tal cual y se deja que TLC lo encuentre. Un modelo que solo dice lo que  *)
(* queremos oir no verifica nada.                                           *)
(*                                                                          *)
(* Los tres interruptores `ExigirValidacionCompleta`,                       *)
(* `PublicarAlAgotarTope` y `ConservarVersionAlRegenerar` existen para eso: *)
(* con los valores del codigo de hoy la especificacion FALLA, y con los     *)
(* valores corregidos PASA. La diferencia entre las dos ejecuciones es      *)
(* exactamente la lista de cambios que el codigo necesita. Ver README.md.   *)
(***************************************************************************)

EXTENDS Naturals, FiniteSets, Sequences

CONSTANTS
    NumCapitulos,                 \* Capitulos de la novela. Modelo pequeno: 5.
    MaxIntentos,                  \* Intentos por capitulo. Modelo pequeno: 2.
    MaxCaidas,                    \* Cota de caidas, para que el modelo sea finito.
    MaxRegeneraciones,            \* Cota de cambios pedidos por el lector.
    ExigirValidacionCompleta,     \* FALSE = codigo de hoy (ACEPTADO_POR_PUNTUACION).
    PublicarAlAgotarTope,         \* TRUE  = codigo de hoy (regla 6: "ensambla lo que haya").
    ConservarVersionAlRegenerar,  \* FALSE = regenerar pisa la salida anterior.
    ReanudarPorCursor             \* FALSE = codigo de hoy (se re-deriva del disco).

Capitulos == 1..NumCapitulos

\* El menor elemento de un conjunto no vacio de capitulos: por donde vuelve a
\* empezar el bucle cuando el lector pide un cambio.
Menor(S) == CHOOSE x \in S : \A y \in S : x =< y

\* El siguiente capitulo sobre el que hay que trabajar, dado el estado de
\* todos ellos. Devuelve NumCapitulos+1 cuando no queda ninguno pendiente.
\*
\* ESTA FUNCION ES LA CORRECCION DE CE-3, y merece leerse despacio: el bucle
\* NO avanza con `actual + 1`, sino al menor capitulo que siga pendiente. La
\* diferencia no se nota en una generacion desde cero, donde los dos
\* coinciden capitulo a capitulo; se nota cuando el lector pide un cambio y
\* solo unos pocos capitulos vuelven a estar pendientes. Con un contador, el
\* bucle sigue hasta el final y reescribe capitulos que nadie habia tocado.
\* Ver README.md, CE-3.
SiguientePendienteEn(f) ==
    LET pendientes == {c \in Capitulos : f[c] = "pendiente"}
    IN IF pendientes = {} THEN NumCapitulos + 1 ELSE Menor(pendientes)

VARIABLES
    fase,            \* Donde esta el orquestador.
    actual,          \* Capitulo en curso. Puede valer NumCapitulos+1 (ninguno).
    intentos,        \* intentos[c]: cuantas veces se ha escrito el capitulo c.
    estadoCap,       \* estadoCap[c]: en que punto esta cada capitulo.
    checkpoint,      \* Lo unico que sobrevive a una caida (`salida/estado.json`).
    versiones,       \* Versiones publicadas, en orden. Nunca deberia encoger.
    caidas,          \* Caidas ocurridas (acotadas para tener modelo finito).
    regeneraciones,  \* Cambios del lector atendidos (acotados por lo mismo).
    topeAgotado      \* El freno de mano de `delegaciones_max_totales`.

vars == <<fase, actual, intentos, estadoCap, checkpoint, versiones,
          caidas, regeneraciones, topeAgotado>>

Fases == {"configuracion", "planificacion", "escritura", "validacion",
          "ensamblado", "publicada", "detenido", "caido"}

\* "aceptado_por_puntuacion" es un capitulo CON texto que NO paso los
\* validadores: se agoto la escalera y se conservo el menos malo. Es un estado
\* real del sistema (`informe-validacion.md`), no una invencion del modelo.
EstadosCapitulo == {"pendiente", "escrito", "aprobado", "aceptado_por_puntuacion"}

Cerrados == {c \in Capitulos : estadoCap[c] \in {"aprobado", "aceptado_por_puntuacion"}}

TypeOK ==
    /\ fase \in Fases
    /\ actual \in 1..(NumCapitulos + 1)
    /\ intentos \in [Capitulos -> 0..MaxIntentos]
    /\ estadoCap \in [Capitulos -> EstadosCapitulo]
    /\ checkpoint \in [cerrados: SUBSET Capitulos, actual: 1..(NumCapitulos + 1)]
    /\ caidas \in 0..MaxCaidas
    /\ regeneraciones \in 0..MaxRegeneraciones
    /\ topeAgotado \in BOOLEAN

Init ==
    /\ fase = "configuracion"
    /\ actual = 1
    /\ intentos = [c \in Capitulos |-> 0]
    /\ estadoCap = [c \in Capitulos |-> "pendiente"]
    /\ checkpoint = [cerrados |-> {}, actual |-> 1]
    /\ versiones = << >>
    /\ caidas = 0
    /\ regeneraciones = 0
    /\ topeAgotado = FALSE

(***************************************************************************)
(* FASE 1 y 2: configuracion y planificacion.                              *)
(* El arquitecto produce la biblia y el outline de una vez; aqui no se      *)
(* modela su contenido, solo que ocurre antes de escribir nada.             *)
(***************************************************************************)

Configurar ==
    /\ fase = "configuracion"
    /\ fase' = "planificacion"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, versiones,
                   caidas, regeneraciones, topeAgotado>>

Planificar ==
    /\ fase = "planificacion"
    /\ fase' = "escritura"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, versiones,
                   caidas, regeneraciones, topeAgotado>>

(***************************************************************************)
(* FASE 3: escritura de un capitulo. Consume un intento de la escalera.     *)
(***************************************************************************)

Escribir ==
    /\ fase = "escritura"
    /\ actual \in Capitulos
    /\ ~topeAgotado
    /\ intentos[actual] < MaxIntentos
    /\ intentos' = [intentos EXCEPT ![actual] = @ + 1]
    /\ estadoCap' = [estadoCap EXCEPT ![actual] = "escrito"]
    /\ fase' = "validacion"
    /\ UNCHANGED <<actual, checkpoint, versiones, caidas, regeneraciones,
                   topeAgotado>>

(***************************************************************************)
(* FASE 4: validacion. Los cuatro validadores (continuidad, genero, estilo  *)
(* y el contador de longitud) se modelan como un unico veredicto: aprueban  *)
(* todos o no aprueba ninguno, que es justo lo que el contrato dice         *)
(* (`EJECUCION.md` 3.5d: un solo FALLO dispara la reescritura). Distinguir  *)
(* cual de los cuatro fallo no cambia ninguna transicion, asi que meterlos  *)
(* por separado multiplicaria el espacio de estados sin anadir una sola     *)
(* comprobacion.                                                            *)
(***************************************************************************)

\* Siguiente fase segun si queda trabajo pendiente.
FaseTras(prox) == IF prox > NumCapitulos THEN "ensamblado" ELSE "escritura"

ValidarPasa ==
    /\ fase = "validacion"
    /\ actual \in Capitulos
    /\ estadoCap[actual] = "escrito"
    /\ LET nuevo == [estadoCap EXCEPT ![actual] = "aprobado"]
           prox  == SiguientePendienteEn(nuevo)
       IN /\ estadoCap' = nuevo
          /\ actual' = prox
          /\ checkpoint' = [cerrados |-> checkpoint.cerrados \cup {actual},
                            actual   |-> prox]
          /\ fase' = FaseTras(prox)
    /\ UNCHANGED <<intentos, versiones, caidas, regeneraciones, topeAgotado>>

Reintentar ==
    /\ fase = "validacion"
    /\ actual \in Capitulos
    /\ estadoCap[actual] = "escrito"
    /\ intentos[actual] < MaxIntentos
    /\ fase' = "escritura"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, versiones,
                   caidas, regeneraciones, topeAgotado>>

(***************************************************************************)
(* Escalera agotada. AQUI ESTA LA DECISION QUE EL ENUNCIADO Y EL CODIGO NO  *)
(* RESUELVEN IGUAL.                                                         *)
(*                                                                          *)
(*   ExigirValidacionCompleta = FALSE  -> codigo de hoy. Regla inviolable 1 *)
(*     de `EJECUCION.md`: "ningun capitulo detiene la generacion". El       *)
(*     capitulo se queda con el mejor intento y se marca como              *)
(*     ACEPTADO_POR_PUNTUACION, sin haber pasado los validadores.           *)
(*                                                                          *)
(*   ExigirValidacionCompleta = TRUE   -> lo que pide el enunciado. La      *)
(*     generacion se detiene con error antes que publicar un capitulo sin   *)
(*     validar.                                                             *)
(***************************************************************************)

\* El guardian admite DOS situaciones, y la segunda es la correccion de CE-4:
\*
\*   fase = "validacion" y capitulo "escrito"  -> el caso normal: se acaba de
\*     validar el ultimo intento y no paso.
\*
\*   fase = "escritura" y capitulo "pendiente" -> se reanudo tras una caida y
\*     el capitulo ya tenia la escalera agotada. El texto en vuelo se perdio,
\*     pero los intentos no: `salida/estado.json` se escribe tras cada intento.
\*     Sin esta rama no se puede escribir (no quedan intentos) ni cerrar (no
\*     hay texto que juzgar), y la generacion se queda parada para siempre.
\*
\* La leccion, que vale mas que la rama: el checkpoint guardaba cuantos
\* intentos se habian gastado, pero no la DECISION que esos intentos habian
\* provocado. Un checkpoint tiene que permitir rehacer la decision, no solo
\* recordar el contador. Ver README.md, CE-4.
AgotarEscalera ==
    /\ \/ (fase = "validacion" /\ actual \in Capitulos /\ estadoCap[actual] = "escrito")
       \/ (fase = "escritura"  /\ actual \in Capitulos /\ estadoCap[actual] = "pendiente")
    /\ intentos[actual] = MaxIntentos
    /\ IF ExigirValidacionCompleta
       THEN /\ fase' = "detenido"
            /\ UNCHANGED <<actual, estadoCap, checkpoint>>
       ELSE LET nuevo == [estadoCap EXCEPT ![actual] = "aceptado_por_puntuacion"]
                prox  == SiguientePendienteEn(nuevo)
            IN /\ estadoCap' = nuevo
               /\ actual' = prox
               /\ checkpoint' = [cerrados |-> checkpoint.cerrados \cup {actual},
                                 actual   |-> prox]
               /\ fase' = FaseTras(prox)
    /\ UNCHANGED <<intentos, versiones, caidas, regeneraciones, topeAgotado>>

(***************************************************************************)
(* El freno de mano: `limites.delegaciones_max_totales` (regla inviolable   *)
(* 6). Cuando salta, el contrato dice "se ensambla lo que haya", y lo que   *)
(* haya puede ser media novela.                                             *)
(***************************************************************************)

AgotarTope ==
    /\ fase \in {"escritura", "validacion"}
    /\ ~topeAgotado
    /\ topeAgotado' = TRUE
    /\ fase' = IF PublicarAlAgotarTope THEN "ensamblado" ELSE "detenido"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, versiones,
                   caidas, regeneraciones>>

(***************************************************************************)
(* Caida y reanudacion. Lo unico que sobrevive es `checkpoint`; el trabajo  *)
(* en vuelo del capitulo no cerrado se pierde. Los intentos SI sobreviven,  *)
(* porque `salida/estado.json` se escribe tras cada intento.                *)
(***************************************************************************)

Caer ==
    /\ fase \in {"escritura", "validacion"}
    /\ caidas < MaxCaidas
    /\ caidas' = caidas + 1
    /\ fase' = "caido"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, versiones,
                   regeneraciones, topeAgotado>>

(***************************************************************************)
(* LAS DOS FORMAS DE REANUDAR, Y POR QUE HAY DOS.                          *)
(*                                                                          *)
(* ReanudarPorCursor = FALSE es el codigo de hoy. `siguiente_paso` de       *)
(*   `src/orquestacion.py` lo dice en su docstring: "la decision se toma    *)
(*   SIEMPRE mirando el disco, nunca un valor recordado". El texto de cada  *)
(*   intento se escribe en `salida/.tmp/cap-NN-intento-M.md` ANTES de       *)
(*   validarlo (EJECUCION.md 3.5b), asi que una caida no se lo lleva: al    *)
(*   volver, el capitulo sigue escrito y lo que toca es validarlo.          *)
(*                                                                          *)
(* ReanudarPorCursor = TRUE es la alternativa que parece razonable y no lo  *)
(*   es: fiarse de `checkpoint.actual` y dar por perdido el trabajo en      *)
(*   vuelo. Se modela para PODER ROMPERLA. Sin esta rama, las invariantes   *)
(*   de reanudacion pasan sin haber sido puestas a prueba nunca, que es     *)
(*   justo lo que `Docs/verification.md` llama un validador sin caso        *)
(*   negativo.                                                              *)
(***************************************************************************)

Reanudar ==
    /\ fase = "caido"
    /\ IF ReanudarPorCursor
       THEN LET recuperado == [c \in Capitulos |->
                                  IF c \in checkpoint.cerrados
                                  THEN estadoCap[c] ELSE "pendiente"]
            IN /\ estadoCap' = recuperado
               /\ actual' = checkpoint.actual
               /\ fase' = FaseTras(checkpoint.actual)
       ELSE LET escritos == {c \in Capitulos : estadoCap[c] = "escrito"}
                prox     == SiguientePendienteEn(estadoCap)
            IN /\ estadoCap' = estadoCap
               /\ actual' = IF escritos # {} THEN Menor(escritos) ELSE prox
               /\ fase'   = IF escritos # {} THEN "validacion" ELSE FaseTras(prox)
    /\ UNCHANGED <<intentos, checkpoint, versiones, caidas, regeneraciones,
                   topeAgotado>>

(***************************************************************************)
(* FASE 5: publicacion. `capitulos` es lo que entra en el manuscrito y      *)
(* `limpios` los que ademas pasaron los validadores. Separar los dos        *)
(* conjuntos es lo que permite que la invariante de publicacion diga algo:  *)
(* si fueran el mismo campo, no habria nada que comparar.                   *)
(***************************************************************************)

\* `ronda` es la identidad de la version: cuantos cambios del lector se habian
\* atendido cuando se publico. Sin este campo dos versiones con los mismos
\* capitulos son el mismo valor para TLC, y `VersionesSoloCrecen` pasa aunque
\* la publicacion pise la anterior, porque pisarla con un valor identico no se
\* ve. Fue asi durante una ejecucion entera: la propiedad estaba en verde por
\* no poder distinguir nada. Ver README.md, CE-5.
Publicar ==
    /\ fase = "ensamblado"
    /\ LET v == [capitulos |-> Cerrados,
                 limpios   |-> {c \in Capitulos : estadoCap[c] = "aprobado"},
                 ronda     |-> regeneraciones]
       IN versiones' = IF ConservarVersionAlRegenerar \/ versiones = << >>
                       THEN Append(versiones, v)
                       ELSE [versiones EXCEPT ![Len(versiones)] = v]
    /\ fase' = "publicada"
    /\ UNCHANGED <<actual, intentos, estadoCap, checkpoint, caidas,
                   regeneraciones, topeAgotado>>

(***************************************************************************)
(* Regeneracion por cambio del lector: "el perro se llama Nala". Se         *)
(* identifican los capitulos que usan ese hecho y solo esos se reabren. El  *)
(* conjunto es cualquiera no vacio: el modelo no sabe que hechos usa cada   *)
(* capitulo, y suponer uno concreto seria verificar un caso, no la regla.   *)
(***************************************************************************)

Regenerar ==
    /\ fase = "publicada"
    /\ regeneraciones < MaxRegeneraciones
    /\ \E S \in (SUBSET Capitulos) \ {{}} :
        /\ estadoCap' = [c \in Capitulos |->
                            IF c \in S THEN "pendiente" ELSE estadoCap[c]]
        /\ intentos'  = [c \in Capitulos |-> IF c \in S THEN 0 ELSE intentos[c]]
        /\ checkpoint' = [cerrados |-> checkpoint.cerrados \ S,
                          actual   |-> Menor(S)]
        /\ actual' = Menor(S)
    /\ regeneraciones' = regeneraciones + 1
    /\ fase' = "escritura"
    /\ UNCHANGED <<versiones, caidas, topeAgotado>>

(***************************************************************************)
(* Estado terminal. Existe para que TLC no confunda "aqui se acaba" con     *)
(* "aqui se atasca": sin este paso de repeticion, toda ejecucion que        *)
(* termina bien se reportaria como deadlock.                                *)
(***************************************************************************)

Terminado ==
    /\ \/ fase = "detenido"
       \/ /\ fase = "publicada"
          /\ regeneraciones = MaxRegeneraciones
    /\ UNCHANGED vars

Next ==
    \/ Configurar
    \/ Planificar
    \/ Escribir
    \/ ValidarPasa
    \/ Reintentar
    \/ AgotarEscalera
    \/ AgotarTope
    \/ Caer
    \/ Reanudar
    \/ Publicar
    \/ Regenerar
    \/ Terminado

(***************************************************************************)
(* Equidad: sobre todo lo que el sistema debe hacer, y sobre NADA que sea   *)
(* un fallo. `Caer` y `AgotarTope` no llevan equidad a proposito: exigir    *)
(* que ocurran seria especificar que el sistema tiene que caerse.           *)
(***************************************************************************)

Equidad ==
    /\ WF_vars(Configurar)
    /\ WF_vars(Planificar)
    /\ WF_vars(Escribir)
    /\ WF_vars(ValidarPasa)
    /\ WF_vars(Reintentar)
    /\ WF_vars(AgotarEscalera)
    /\ WF_vars(Reanudar)
    /\ WF_vars(Publicar)

Spec == Init /\ [][Next]_vars /\ Equidad

(***************************************************************************)
(* INVARIANTES DE SEGURIDAD                                                 *)
(***************************************************************************)

\* S-1. Nunca se publica una version con un capitulo que no paso todos los
\* validadores.
NuncaPublicaSinValidar ==
    \A i \in 1..Len(versiones) : versiones[i].capitulos = versiones[i].limpios

\* S-2a. Ninguna version publicada pierde capitulos.
NuncaPierdeCapitulos ==
    \A i \in 1..Len(versiones) : versiones[i].capitulos = Capitulos

\* S-2b. La reanudacion no reescribe un capitulo ya cerrado. Es la mitad
\* "no duplica" de la invariante del enunciado.
NoReescribeCerrados ==
    (fase = "escritura" /\ actual \in Capitulos) => actual \notin checkpoint.cerrados

\* S-2c. El cursor nunca deja atras un capitulo sin escribir. Es la mitad
\* "no pierde".
NoSaltaCapitulos ==
    \A c \in Capitulos : (c < actual) => estadoCap[c] # "pendiente"

\* S-3. El numero de intentos de un capitulo nunca supera el limite.
ReintentosAcotados ==
    \A c \in Capitulos : intentos[c] =< MaxIntentos

\* S-4. La version anterior se conserva siempre: la lista de versiones solo
\* crece y lo ya publicado no se toca. Es una propiedad de ACCION, no un
\* invariante de estado: habla de la relacion entre un estado y el siguiente.
VersionesSoloCrecen ==
    [][ /\ Len(versiones') >= Len(versiones)
        /\ \A i \in 1..Len(versiones) : versiones'[i] = versiones[i] ]_vars

(***************************************************************************)
(* PROPIEDAD DE VIVACIDAD                                                   *)
(* Toda generacion acaba publicando o deteniendose con error. Nunca se      *)
(* queda dando vueltas.                                                     *)
(***************************************************************************)

Terminacion == <>(fase \in {"publicada", "detenido"})

=============================================================================
