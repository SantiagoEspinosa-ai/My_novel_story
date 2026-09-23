/-
  Dos obras de ejemplo, y las dos hacen falta.

  `obraLimpia` es una cronologia correcta. Sirve para demostrar que las
  invariantes **no marcan lo que esta bien**: un validador que marca todo es
  tan inutil como uno que no marca nada, y sin este caso no se distinguen.

  `obraAdversaria` viola las cuatro, una vez cada una. Es **el caso negativo
  obligatorio** que `docs/verification.md` exige de todo validador: una
  invariante que nunca ha fallado en las pruebas no esta verificada, solo
  declarada.

  Las dos estan escritas a mano y no salen de la base de datos a proposito. El
  fichero que genera `generar_lean.py` a partir de SQLite tiene exactamente
  esta forma, asi que estas dos obras son tambien la especificacion de lo que
  el generador tiene que escribir.
-/
import Cronologia.Basic

namespace Cronologia

/-- Atajo para fechas sin hora, que es como las escribe el arquitecto. -/
def dia (a : Int) (m d : Nat) : Fecha := { anio := a, mes := m, dia := d }

def presente (p : String) : Participacion := { personaje := p, presencia := Presencia.presente }
def mencionado (p : String) : Participacion := { personaje := p, presencia := Presencia.mencionado }

/-! ## Una cronologia que cuadra -/

def obraLimpia : Obra :=
  { id := "obra-limpia"
  , personajes :=
      [ { id := "per-ana",   nacimiento := some (dia 1985 3 14) }
      , { id := "per-marta", nacimiento := some (dia 1989 11 2) } ]
  , eventos :=
      [ { id := "ev-1", tFabula := dia 2019 6 1, inicioMin := 26_064_000
        , duracionMin := 120, lugar := "lug-casa", tDiscurso := 1, capitulo := "cap-1"
        , participan := [presente "per-ana", mencionado "per-marta"] }
      , { id := "ev-2", tFabula := dia 2019 6 1, inicioMin := 26_064_180
        , duracionMin := 60, lugar := "lug-sotano", tDiscurso := 2, capitulo := "cap-1"
        -- Empieza una hora despues de que acabe `ev-1`: no solapan, y ademas
        -- Ana ha tenido tiempo de bajar.
        , participan := [presente "per-ana"] }
      , { id := "ev-3", tFabula := dia 2019 6 2, inicioMin := 26_065_440
        , duracionMin := 90, lugar := "lug-bosque", tDiscurso := 3, capitulo := "cap-2"
        , participan := [presente "per-ana", presente "per-marta"] }
        -- Una analepsis **declarada**: el discurso avanza y la fabula
        -- retrocede doce anios, y eso es legitimo porque lo dice.
      , { id := "ev-4", tFabula := dia 2007 8 9, inicioMin := 19_762_560
        , duracionMin := 45, lugar := "lug-casa", tDiscurso := 4, capitulo := "cap-2"
        , analepsis := true
        , participan := [presente "per-marta"] } ]
  }

/-! ## Una cronologia con las cuatro incoherencias

    Es la que produce el brief adversario pensado para provocar una
    incoherencia temporal. Cada evento lleva escrito que invariante rompe. -/

def obraAdversaria : Obra :=
  { id := "obra-adversaria"
  , personajes :=
      [ { id := "per-ana",   nacimiento := some (dia 1985 3 14) }
      , { id := "per-marta", nacimiento := some (dia 1989 11 2) }
        -- Sin fecha: no viola nada, pero su edad **no se comprueba**, y el
        -- informe tiene que decirlo en vez de contarlo como correcto.
      , { id := "per-luis",  nacimiento := none } ]
  , eventos :=
      [ { id := "ev-a1", tFabula := dia 2019 6 10, inicioMin := 26_076_960
        , duracionMin := 60, lugar := "lug-casa", tDiscurso := 1, capitulo := "cap-1"
        , participan := [presente "per-ana", presente "per-luis"] }

        -- L-1: se lee despues y ocurre antes, sin declarar analepsis.
      , { id := "ev-a2", tFabula := dia 2019 6 8, inicioMin := 26_074_080
        , duracionMin := 30, lugar := "lug-casa", tDiscurso := 2, capitulo := "cap-2"
        , participan := [presente "per-ana"] }

        -- L-2: Marta nacio en 1989 y aqui esta presente en 1984.
      , { id := "ev-a3", tFabula := dia 1984 5 1, inicioMin := 8_540_640
        , duracionMin := 60, lugar := "lug-bosque", tDiscurso := 3, capitulo := "cap-3"
        , analepsis := true
        , participan := [presente "per-marta"] }

        -- L-3: este y el siguiente empiezan en el mismo minuto, en dos
        -- lugares distintos, con Ana presente en los dos.
      , { id := "ev-a4", tFabula := dia 2019 7 1, inicioMin := 26_107_200
        , duracionMin := 60, lugar := "lug-sotano", tDiscurso := 4, capitulo := "cap-4"
        , participan := [presente "per-ana"] }
      , { id := "ev-a5", tFabula := dia 2019 7 1, inicioMin := 26_107_200
        , duracionMin := 60, lugar := "lug-faro", tDiscurso := 5, capitulo := "cap-4"
        , participan := [presente "per-ana"] }

        -- L-4: Luis queda excluido aqui y reaparece en `ev-a7`.
      , { id := "ev-a6", tFabula := dia 2019 7 2, inicioMin := 26_108_640
        , duracionMin := 30, lugar := "lug-faro", tDiscurso := 6, capitulo := "cap-5"
        , excluye := ["per-luis"]
        , participan := [presente "per-luis", presente "per-ana"] }
      , { id := "ev-a7", tFabula := dia 2019 7 5, inicioMin := 26_112_960
        , duracionMin := 30, lugar := "lug-casa", tDiscurso := 7, capitulo := "cap-6"
        , participan := [presente "per-luis"] } ]
  }

end Cronologia
