/-
  FICHERO GENERADO. No editar a mano: lo reescribe `generar_lean.py`.

  Obra: obra-x
  Eventos convertidos: 4
  Personajes: 3 (sin fecha de nacimiento: 1)
  Eventos descartados por fecha ilegible: 0

  `excluye` va vacia en todos los eventos, y no porque nadie muera: porque no
  hay de donde sacarlo. `entidad` guarda el estado vital **actual** y no en que
  evento cambio (`F-46`). Mientras siga asi, `L-4` no puede disparar sobre
  datos reales y un cero suyo no significa nada.
-/
import Cronologia.Basic

namespace Cronologia

def obraReal : Obra :=
  { id := "obra-x"
  , personajes :=
  [
    { id := "per-ana", nacimiento := some { anio := 1985, mes := 3, dia := 14, hora := 0, minuto := 0 } },
    { id := "per-luis", nacimiento := none },
    { id := "per-marta", nacimiento := some { anio := 1989, mes := 11, dia := 2, hora := 0, minuto := 0 } }
  ]
  , eventos :=
  [
    { id := "ev-1", tFabula := { anio := 2019, mes := 6, dia := 10, hora := 21, minuto := 0 }, inicioMin := 62819820, duracionMin := 60, lugar := "lug-casa", tDiscurso := 1, capitulo := "cap-1", analepsis := false, excluye := [], participan := [{ personaje := "per-ana", presencia := Presencia.presente }, { personaje := "per-marta", presencia := Presencia.mencionado }] },
    { id := "ev-2", tFabula := { anio := 2019, mes := 6, dia := 8, hora := 10, minuto := 0 }, inicioMin := 62816280, duracionMin := 30, lugar := "lug-sotano", tDiscurso := 2, capitulo := "cap-2", analepsis := false, excluye := [], participan := [{ personaje := "per-ana", presencia := Presencia.presente }] },
    { id := "ev-3a", tFabula := { anio := 2019, mes := 6, dia := 12, hora := 18, minuto := 0 }, inicioMin := 62822520, duracionMin := 60, lugar := "lug-faro", tDiscurso := 3, capitulo := "cap-3", analepsis := false, excluye := [], participan := [{ personaje := "per-marta", presencia := Presencia.presente }] },
    { id := "ev-3b", tFabula := { anio := 2019, mes := 6, dia := 12, hora := 18, minuto := 0 }, inicioMin := 62822520, duracionMin := 60, lugar := "lug-bosque", tDiscurso := 4, capitulo := "cap-3", analepsis := false, excluye := [], participan := [{ personaje := "per-luis", presencia := Presencia.presente }, { personaje := "per-marta", presencia := Presencia.presente }] }
  ]
  }

end Cronologia
