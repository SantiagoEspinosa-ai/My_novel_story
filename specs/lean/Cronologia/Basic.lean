/-
  El modelo de datos de una cronologia de fabula.

  Esto es el espejo en Lean de dos tablas de SQLite que ya existen
  —`evento_cronologico` y `participacion_en_evento`, creadas por `SPEC-21`— mas
  la columna `entidad.fecha_de_nacimiento`. El generador
  (`generar_lean.py`) lee esas tablas y escribe un fichero con estas mismas
  estructuras rellenas.

  POR QUE HAY DOS REPRESENTACIONES DEL TIEMPO, Y NO ES UNA DUPLICACION
  --------------------------------------------------------------------
  Cada evento lleva su instante dos veces:

    `tFabula`   como `Fecha`, para **comparar** y para calcular edades.
    `inicioMin` como entero, para **hacer aritmetica** con la duracion.

  La razon es que un calendario de verdad no se puede hacer con una formula:
  los meses tienen longitudes distintas y los anios bisiestos existen. Aqui se
  puede comparar una `Fecha` con otra sin saber nada de eso —basta el orden
  lexicografico— pero *no* se puede sumar una duracion en minutos. Asi que la
  aritmetica del calendario la hace Python, que tiene `datetime`, y Lean
  recibe el resultado ya convertido a minutos desde una epoca.

  Inventarse aqui un `dias_por_mes = 30` habria dado un orden que parece
  correcto y falla en los limites de mes, que es justo donde una novela pone
  «la noche del 31».
-/

namespace Cronologia

/-- Un instante de la fabula, tal como lo escribe el arquitecto en ISO-8601. -/
structure Fecha where
  anio   : Int
  mes    : Nat
  dia    : Nat
  hora   : Nat := 0
  minuto : Nat := 0
  deriving Repr, DecidableEq, Inhabited

/-- Orden lexicografico sobre los cinco campos. No necesita calendario: para
    decir cual de dos fechas es anterior basta compararlas por orden de
    significacion, y eso es exacto. -/
def Fecha.menorQue (a b : Fecha) : Bool :=
  if a.anio ≠ b.anio then a.anio < b.anio
  else if a.mes ≠ b.mes then a.mes < b.mes
  else if a.dia ≠ b.dia then a.dia < b.dia
  else if a.hora ≠ b.hora then a.hora < b.hora
  else a.minuto < b.minuto

def Fecha.comoTexto (f : Fecha) : String :=
  s!"{f.anio}-{f.mes}-{f.dia} {f.hora}:{f.minuto}"

/-- Los anios cumplidos de alguien nacido en `nac` en el instante `t`.
    Se resta uno si todavia no ha llegado su cumpleanios ese anio. -/
def edadEn (nac t : Fecha) : Int :=
  let bruta := t.anio - nac.anio
  let yaCumplio := (nac.mes < t.mes) || (nac.mes == t.mes && nac.dia ≤ t.dia)
  if yaCumplio then bruta else bruta - 1

/-- Estar en un evento no es que hablen de ti (`SPEC-21` C-3). Solo `presente`
    cuenta para «nadie en dos lugares a la vez»: si un personaje nombrado
    contara, cada vez que dos personajes se acordaran del mismo ausente el
    validador diria que ese ausente esta en dos sitios. -/
inductive Presencia where
  | presente
  | mencionado
  deriving Repr, DecidableEq, Inhabited

structure Participacion where
  personaje : String
  presencia : Presencia
  deriving Repr, Inhabited

structure Evento where
  id          : String
  /-- Instante en la **fabula**: cuando ocurre en la cronologia de la ficcion. -/
  tFabula     : Fecha
  /-- El mismo instante en minutos desde una epoca, calculado por el generador.
      Solo para sumar la duracion; nunca para comparar. -/
  inicioMin   : Int
  duracionMin : Nat
  lugar       : String
  /-- Posicion en el **discurso**: el orden en que el lector lo lee. Fabula y
      discurso son dos ejes distintos, y casi todo el terror vive en su
      diferencia. -/
  tDiscurso   : Nat
  capitulo    : String
  /-- `INV-08` no prohibe que el tiempo retroceda: prohibe que retroceda **sin
      declararlo**. Una analepsis es exactamente un retroceso declarado. -/
  analepsis   : Bool := false
  /-- Personajes que, a partir de este evento, ya no pueden aparecer: muertos,
      o que se van para no volver.

      **Hoy el generador siempre la deja vacia**, y no porque no pase nunca:
      porque no hay de donde sacarlo. La tabla `entidad` guarda el estado vital
      **actual** y no en que evento cambio, y `cambios_de_estado_vital` del
      delta se aplica y no se conserva. Ver `F-46`. El campo existe ya para que
      la invariante este escrita y probada contra el fixture el dia que el dato
      llegue: lo que falta es la fuente, no la comprobacion. -/
  excluye     : List String := []
  participan  : List Participacion := []
  deriving Repr, Inhabited

structure Personaje where
  id : String
  /-- Opcional a proposito: exigirla rompe todas las obras generadas hasta hoy.
      Como es opcional, **quien no la tenga no pasa la comprobacion de edad: se
      la salta**, y el informe lo dice aparte. Un «cero incoherencias» junto a
      un «tres sin fecha» no significa que las edades cuadren. -/
  nacimiento : Option Fecha := none
  deriving Repr, Inhabited

structure Obra where
  id         : String
  personajes : List Personaje
  eventos    : List Evento
  deriving Repr, Inhabited

/-- Los presentes de un evento. Los `mencionado` se quedan fuera. -/
def Evento.presentes (e : Evento) : List String :=
  (e.participan.filter (fun p => p.presencia == Presencia.presente)).map (·.personaje)

/-- Dos eventos se solapan en el tiempo.

    El intervalo es **medio abierto** `[inicio, inicio+duracion)`, asi que dos
    eventos pegados —uno acaba a las 21:30 y el otro empieza a las 21:30— no
    solapan: dar por conflictivo a quien sale de una habitacion y entra en otra
    llenaria de falsos positivos cualquier novela con movimiento.

    Y hay una segunda condicion porque con duracion cero el intervalo esta
    vacio y la primera no se cumple nunca: sin ella, dos cosas instantaneas a
    la misma hora en dos sitios distintos se colarian sin que nadie las viera.
    Es la misma regla que `cronologia/consultas.py`. -/
def Evento.solapaCon (a b : Evento) : Bool :=
  let seCruzan := a.inicioMin < b.inicioMin + (b.duracionMin : Int)
                  && b.inicioMin < a.inicioMin + (a.duracionMin : Int)
  seCruzan || a.inicioMin == b.inicioMin

def Obra.personaje? (o : Obra) (id : String) : Option Personaje :=
  o.personajes.find? (fun p => p.id == id)

/-- Pares ordenados sin repetir, para las invariantes que hablan de dos
    eventos. Se escribe a mano en vez de usar una utilidad de listas porque
    asi queda claro que cada par se mira **una** vez. -/
def paresDe {α : Type} : List α → List (α × α)
  | [] => []
  | x :: xs => xs.foldr (fun y acc => (x, y) :: acc) (paresDe xs)

end Cronologia
