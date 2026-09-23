/-
  Verifica la obra REAL, la que `generar_lean.py` saco de SQLite.

  Es un ejecutable aparte de `verificar` a proposito: aquel corre sobre el
  fixture y tiene que dar 0 siempre, porque comprueba que las invariantes
  funcionan. Este corre sobre datos y puede dar 1, porque comprueba la obra.
  Mezclarlos haria que un fallo de la novela pareciera un fallo del validador.

  Salida 1 = hay incoherencias y la version no se publica.
-/
import Cronologia.Invariantes
import Cronologia.Generado

open Cronologia

def main : IO UInt32 := do
  let informe := verificar obraReal
  IO.println s!"== {obraReal.id} =="
  IO.println informe.comoTexto
  if informe.pasa then
    IO.println "\nSin incoherencias temporales: la version puede publicarse."
    return 0
  else
    IO.println "\nHay incoherencias temporales: la version NO se publica."
    return 1
