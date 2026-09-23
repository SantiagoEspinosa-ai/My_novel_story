/-
  Las cuatro invariantes temporales, y la distincion que las hace utiles.

  Cada comprobacion devuelve DOS listas y no una:

    `violaciones`  lo que esta mal y se puede demostrar que esta mal.
    `sinDatos`     lo que no se ha podido mirar por falta de un dato.

  Separarlas no es pulcritud: es la diferencia entre «no hay incoherencias» y
  «no he podido buscarlas». Una invariante que se salta en silencio cuando le
  falta un campo **no esta en verde, esta ausente**, y desde fuera las dos se
  ven igual. Ese fallo ya ocurrio en este proyecto (`F-34`) y costo dos
  invariantes inactivas sin que nada lo dijera.

  QUE APORTA LEAN AQUI, SIENDO QUE DOS DE ESTAS REGLAS YA ESTAN EN PYTHON
  ----------------------------------------------------------------------
  `INV-02` e `INV-08` comprueban lo mismo que `L-3` y `L-1`, escena a escena,
  **en el momento de la puerta**. Lean mira la obra **entera y a la vez**,
  cuando ya esta escrita. La diferencia importa porque una incoherencia
  temporal entre el capitulo 2 y el capitulo 9 no es visible desde la puerta
  del capitulo 9: cada escena, por separado, es impecable. Es el mismo tipo de
  hueco que la Regla 6 describe, en otro eje: lo que solo existe **entre** dos
  cosas no lo ve nada que mire una cosa.
-/
import Cronologia.Basic

namespace Cronologia

structure Violacion where
  invariante : String
  detalle    : String
  deriving Repr

/-- Constructor corto. Existe por una razon practica: Lean es sensible a la
    indentacion dentro de `{ ... }`, y un literal de estructura partido en
    varias lineas dentro de una lista anidada se vuelve fragil. Con esto cada
    violacion se construye en una linea y el codigo dice lo que hace. -/
def viol (inv det : String) : Violacion := { invariante := inv, detalle := det }

structure Informe where
  violaciones : List Violacion := []
  sinDatos    : List String := []
  deriving Repr, Inhabited

def Informe.unir (a b : Informe) : Informe :=
  { violaciones := a.violaciones ++ b.violaciones, sinDatos := a.sinDatos ++ b.sinDatos }

/-- **L-1 · El orden temporal se respeta salvo analepsis declarada.**

    Espejo de `INV-08`. Si el discurso avanza y la fabula retrocede, es una
    inversion; y una inversion solo vale si el evento posterior en el discurso
    la declara. Se miran todos los pares y no solo los consecutivos: para una
    secuencia, la monotonia entre adyacentes implica la monotonia entera, asi
    que el resultado es el mismo y el codigo no necesita ordenar nada. -/
def orden (o : Obra) : Informe :=
  let malos := (paresDe o.eventos).foldr (fun (par : Evento × Evento) acc =>
    let (a, b) := par
    -- `despues` es el que va mas tarde en el DISCURSO.
    let (antes, despues) := if a.tDiscurso ≤ b.tDiscurso then (a, b) else (b, a)
    if antes.tDiscurso == despues.tDiscurso then acc
    else if despues.tFabula.menorQue antes.tFabula && !despues.analepsis then
      viol "L-1" s!"{despues.id} se lee despues de {antes.id} (discurso {antes.tDiscurso} -> {despues.tDiscurso}) pero ocurre antes en la fabula ({despues.tFabula.comoTexto} < {antes.tFabula.comoTexto}) y no declara analepsis" :: acc
    else acc) []
  { violaciones := malos }

/-- **L-2 · La edad es coherente con la fecha de nacimiento.**

    Un personaje presente en un evento anterior a su nacimiento es imposible.
    Quien no tiene fecha no se comprueba, y eso se dice: va a `sinDatos`. -/
def edad (o : Obra) : Informe :=
  o.eventos.foldr (fun e acc =>
    e.presentes.foldr (fun p acc2 =>
      match o.personaje? p with
      | none => Informe.unir acc2 { sinDatos := [s!"{p} no esta en la lista de personajes (evento {e.id})"] }
      | some per =>
        match per.nacimiento with
        | none => Informe.unir acc2 { sinDatos := [s!"{p} no tiene fecha de nacimiento: su edad no se comprueba"] }
        | some nac =>
          if e.tFabula.menorQue nac then
            Informe.unir acc2 { violaciones := [viol "L-2" s!"{p} esta presente en {e.id} el {e.tFabula.comoTexto}, y nacio el {nac.comoTexto}: tendria {edadEn nac e.tFabula} anios"] }
          else acc2) acc) {}

/-- **L-3 · Nadie esta en dos lugares en el mismo momento.**

    Espejo de la mitad de accesibilidad de `INV-02`, pero sobre la obra entera
    en vez de escena a escena. Solo cuentan los `presente`. -/
def ubicuidad (o : Obra) : Informe :=
  let malos := (paresDe o.eventos).foldr (fun (par : Evento × Evento) acc =>
    let (a, b) := par
    if a.lugar == b.lugar then acc
    else if !(a.solapaCon b) then acc
    else
      let comunes := a.presentes.filter (fun p => b.presentes.contains p)
      comunes.foldr (fun p acc2 =>
        viol "L-3" s!"{p} esta presente en {a.id} ({a.lugar}) y en {b.id} ({b.lugar}) a la vez" :: acc2) acc) []
  { violaciones := malos }

/-- **L-4 · Nadie aparece despues de un evento que lo excluye.**

    Un personaje al que un evento saca de la ficcion —muere, o se va para no
    volver— no puede estar presente en nada posterior de la fabula.

    **Hoy esta comprobacion no puede disparar contra datos reales**, porque
    `Evento.excluye` llega siempre vacia del generador: no hay tabla que diga
    en que evento alguien dejo de poder aparecer (`F-46`). Contra el fixture si
    dispara, que es lo que demuestra que la comprobacion funciona y que lo que
    falta es el dato. Decir «cero violaciones de L-4» sobre una obra real seria
    exactamente el verde falso que `F-34` enseño a no dar por bueno. -/
def exclusion (o : Obra) : Informe :=
  let malos := (paresDe o.eventos).foldr (fun (par : Evento × Evento) acc =>
    let (a, b) := par
    let (antes, despues) := if b.tFabula.menorQue a.tFabula then (b, a) else (a, b)
    let expulsados := antes.excluye.filter (fun p => despues.presentes.contains p)
    expulsados.foldr (fun p acc2 =>
      viol "L-4" s!"{p} queda excluido en {antes.id} ({antes.tFabula.comoTexto}) y aparece en {despues.id} ({despues.tFabula.comoTexto})" :: acc2) acc) []
  { violaciones := malos }

/-- Las cuatro, en el orden en que conviene leerlas. -/
def verificar (o : Obra) : Informe :=
  Informe.unir (Informe.unir (orden o) (edad o)) (Informe.unir (ubicuidad o) (exclusion o))

/-- El veredicto, que **no** es solo «hay violaciones o no».

    La Regla 8 otra vez, en el terreno de la verificacion formal: una obra de
    la que no se pudo convertir ningun evento no esta limpia, es que no se ha
    mirado. Y un capitulo cuyo identificador no deja deducir su orden hace que
    el eje del discurso sea una suposicion, asi que `L-1` tampoco se puede
    afirmar sobre ella. En los dos casos la respuesta es `sinVeredicto`, que es
    distinto de las otras dos y tiene que verse distinto. -/
def veredictoDe (c : Cobertura) (i : Informe) : Veredicto :=
  if c.eventos == 0 then Veredicto.sinVeredicto
  else if c.capitulosNoOrdenables > 0 then Veredicto.sinVeredicto
  else if i.violaciones.isEmpty then Veredicto.limpio
  else Veredicto.conViolaciones

def Cobertura.comoTexto (c : Cobertura) : String :=
  s!"eventos: {c.eventos} · sin fecha legible: {c.eventosSinFechaLegible} · " ++
  s!"sin nacimiento: {c.personajesSinNacimiento} · con exclusion: {c.eventosConExclusion} · " ++
  s!"capitulos no ordenables: {c.capitulosNoOrdenables}"

def Informe.pasa (i : Informe) : Bool := i.violaciones.isEmpty

def Informe.comoTexto (i : Informe) : String :=
  let v := String.intercalate "\n" (i.violaciones.map (fun x => s!"  [{x.invariante}] {x.detalle}"))
  let s := String.intercalate "\n" (i.sinDatos.map (fun x => s!"  - {x}"))
  let cabecera := s!"violaciones: {i.violaciones.length} · sin datos: {i.sinDatos.length}"
  let cuerpo := if i.violaciones.isEmpty then "" else "\n" ++ v
  let cola := if i.sinDatos.isEmpty then "" else s!"\nno comprobado por falta de dato:\n{s}"
  cabecera ++ cuerpo ++ cola

end Cronologia
