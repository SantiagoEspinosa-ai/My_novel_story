/-
  Verifica la obra REAL, la que `generar_lean.py` saco de SQLite.

  Es un ejecutable aparte de `verificar` a proposito: aquel corre sobre el
  fixture y tiene que dar 0 siempre, porque comprueba que las invariantes
  funcionan. Este corre sobre datos y puede dar 1, porque comprueba la obra.
  Mezclarlos haria que un fallo de la novela pareciera un fallo del validador.

  TRES SALIDAS, NO DOS
  --------------------
    0  limpio: se miro y no hay incoherencias. Se puede publicar.
    1  hay violaciones. NO se publica.
    2  SIN VEREDICTO: no habia bastante dato para mirar. Tampoco se publica.

  El 2 es la Regla 8 aplicada a este validador, y es la correccion de un hueco
  real (`F-54`). Antes, una obra que llegaba con cero eventos —porque sus
  escenas no declaran `t_fabula`, o porque la tabla estaba vacia— producia
  cero violaciones y este programa decia «puede publicarse». El veredicto era
  correcto y la conclusion falsa.

  El caso hermano se midio en `F-52`: alli la tabla **no existia** y el
  generador murio con `no such table`, lo que salvo la situacion. Pero la
  salvo por accidente del caso. **Una tabla vacia es mas probable que una
  ausente**, y ahi no muere nadie: eso es lo que cierra este 2.
-/
import Cronologia.Invariantes
import Cronologia.Generado

open Cronologia

def main : IO UInt32 := do
  let informe := verificar obraReal
  IO.println s!"== {obraReal.id} =="
  IO.println s!"cobertura: {coberturaReal.comoTexto}"
  IO.println informe.comoTexto
  IO.println ""
  -- Bloque legible por maquina, para que `comparar_con_la_puerta.py` no tenga
  -- que parsear la prosa de arriba. Un mensaje se reescribe cualquier dia; un
  -- prefijo fijo, no.
  IO.println s!"#COBERTURA eventos={coberturaReal.eventos} no_ordenables={coberturaReal.capitulosNoOrdenables}"
  for (antes, despues) in paresL1 obraReal do
    IO.println s!"#PAR L-1 {antes} {despues}"
  -- Una linea por violacion, con los eventos implicados (`SPEC-30` `RF-03`): la
  -- puerta de publicacion se los pasa al Editor sin leer la prosa.
  for v in informe.violaciones do
    IO.println s!"#VIOLACION {v.invariante} {",".intercalate v.eventos} {v.detalle}"
  IO.println ""

  match veredictoDe coberturaReal informe with
  | Veredicto.sinVeredicto =>
      if coberturaReal.eventos == 0 then
        IO.println "SIN VEREDICTO: cero eventos convertidos. No hay nada que comprobar,"
        IO.println "y eso NO es lo mismo que estar en orden. La version no se publica."
      else
        IO.println s!"SIN VEREDICTO: {coberturaReal.capitulosNoOrdenables} capitulo(s) con identificador"
        IO.println "del que no se deduce su orden, asi que el eje del discurso es una"
        IO.println "suposicion y L-1 no se puede afirmar. La version no se publica."
      return 2
  | Veredicto.conViolaciones =>
      IO.println "Hay incoherencias temporales: la version NO se publica."
      return 1
  | Veredicto.limpio =>
      IO.println "Sin incoherencias temporales: la version puede publicarse."
      return 0
