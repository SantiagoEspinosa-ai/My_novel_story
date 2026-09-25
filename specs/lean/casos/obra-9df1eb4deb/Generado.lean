/-
  FICHERO GENERADO. No editar a mano: lo reescribe `generar_lean.py`.

  Obra: obra-9df1eb4deb
  Eventos convertidos: 10
  Personajes: 4 (sin fecha de nacimiento: 3)
  Eventos descartados por fecha ilegible: 0

  `excluye` va vacia en todos los eventos, y no porque nadie muera: porque no
  hay de donde sacarlo. `entidad` guarda el estado vital **actual** y no en que
  evento cambio (`F-46`). Mientras siga asi, `L-4` no puede disparar sobre
  datos reales y un cero suyo no significa nada.
-/
import Cronologia.Basic

namespace Cronologia

/-- Lo que se pudo mirar y lo que no. `MainReal` lo usa para poder decir "sin
    veredicto" en vez de aprobar una obra que nadie llego a comprobar. -/
def coberturaReal : Cobertura :=
  { eventos := 10
  , eventosSinFechaLegible := 0
  , personajesSinNacimiento := 3
  , eventosConExclusion := 0
  , capitulosNoOrdenables := 0 }

def obraReal : Obra :=
  { id := "obra-9df1eb4deb"
  , personajes :=
  [
    { id := "obra-9df1eb4deb-per-ana", nacimiento := some { anio := 1992, mes := 9, dia := 25, hora := 0, minuto := 0 } },
    { id := "obra-9df1eb4deb-per-casimiro", nacimiento := none },
    { id := "obra-9df1eb4deb-per-hachi", nacimiento := none },
    { id := "obra-9df1eb4deb-per-teodoro", nacimiento := none }
  ]
  , eventos :=
  [
    { id := "evt-obra-9df1eb4deb-cap-01-e1", tFabula := { anio := 2026, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 66654720, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-casa", tDiscurso := 1, capitulo := "obra-9df1eb4deb-cap-01", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-hachi", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-02-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-vagon", tDiscurso := 2, capitulo := "obra-9df1eb4deb-cap-02", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-03-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-vagon", tDiscurso := 3, capitulo := "obra-9df1eb4deb-cap-03", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-04-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-locomotora", tDiscurso := 4, capitulo := "obra-9df1eb4deb-cap-04", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-casimiro", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-05-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-vagon", tDiscurso := 5, capitulo := "obra-9df1eb4deb-cap-05", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-06-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-vagon-restaurante", tDiscurso := 6, capitulo := "obra-9df1eb4deb-cap-06", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-07-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-vagon", tDiscurso := 7, capitulo := "obra-9df1eb4deb-cap-07", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-08-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-locomotora", tDiscurso := 8, capitulo := "obra-9df1eb4deb-cap-08", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-casimiro", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-09-e1", tFabula := { anio := 2012, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 59292000, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-estacion-lisboa", tDiscurso := 9, capitulo := "obra-9df1eb4deb-cap-09", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-casimiro", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-teodoro", presencia := Presencia.presente }] },
    { id := "evt-obra-9df1eb4deb-cap-10-e1", tFabula := { anio := 2026, mes := 9, dia := 25, hora := 0, minuto := 0 }, inicioMin := 66654720, duracionMin := 0, lugar := "obra-9df1eb4deb-lug-casa", tDiscurso := 10, capitulo := "obra-9df1eb4deb-cap-10", analepsis := false, excluye := [], participan := [{ personaje := "obra-9df1eb4deb-per-ana", presencia := Presencia.presente }, { personaje := "obra-9df1eb4deb-per-hachi", presencia := Presencia.presente }] }
  ]
  }

end Cronologia
