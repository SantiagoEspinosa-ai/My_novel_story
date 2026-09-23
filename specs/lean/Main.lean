/-
  El ejecutable que corre las invariantes y decide si la version se publica.

  CODIGO DE SALIDA
  ----------------
    0  la obra limpia pasa, y la adversaria falla en las cuatro invariantes.
    1  cualquier otra cosa.

  Que se exija tambien que la adversaria **falle** no es una curiosidad: es lo
  que impide que este ejecutable termine en verde por no estar comprobando
  nada. Si alguien rompe una invariante y la deja siempre satisfecha, la obra
  limpia seguiria pasando y nadie se enteraria. Con el caso negativo dentro
  del propio arranque, esa averia sale en la primera ejecucion.

  Esto es lo que engancha con la puerta de publicacion: `verificar` devuelve 1
  y la version no se publica.
-/
import Cronologia

open Cronologia

/-- Cuantas violaciones de una invariante concreta hay en un informe. -/
def cuenta (i : Informe) (inv : String) : Nat :=
  (i.violaciones.filter (fun v => v.invariante == inv)).length

def main : IO UInt32 := do
  let limpia := verificar obraLimpia
  let adversaria := verificar obraAdversaria

  IO.println "== obra limpia =="
  IO.println limpia.comoTexto
  IO.println ""
  IO.println "== obra adversaria (caso negativo: TIENE que fallar) =="
  IO.println adversaria.comoTexto
  IO.println ""

  let invariantes := ["L-1", "L-2", "L-3", "L-4"]
  let sinCasoNegativo := invariantes.filter (fun inv => cuenta adversaria inv == 0)

  IO.println "== resultado =="
  if !limpia.pasa then
    IO.println "FALLO: la obra limpia tiene violaciones; alguna invariante marca lo correcto."
    return 1
  if !sinCasoNegativo.isEmpty then
    IO.println s!"FALLO: estas invariantes no dispararon contra la obra adversaria: {sinCasoNegativo}"
    IO.println "Una invariante que no falla cuando debe no esta verificada, solo declarada."
    return 1
  IO.println "La obra limpia pasa las cuatro invariantes."
  IO.println "La obra adversaria las viola las cuatro: cada una tiene su caso negativo."
  return 0
