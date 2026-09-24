---
id: SPEC-30
titulo: La puerta de publicación, con Lean
estado: aplicada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-23
version: 4
fecha_aplicacion: 2026-09-24
commit_de_aplicacion: a8b8311
---

> **Historial.** v1: redactada con la decisión del autor sobre la rendición
> (2026-09-23), con `O-1` a `O-3` abiertas. v2: el autor fija el tope en 2, decide
> que los hallazgos de obra del Editor bloquean y confirma las tres propuestas. Sin
> cuestiones abiertas. v3 (2026-09-24), corrección documental que conserva la aprobación:
> la regla de TLA+ que modela la rendición es `ExigirValidacionCompleta`, no
> `PublicarAlAgotarTope`, que es el freno de delegaciones. Lo encontró `PLAN-30`.
> v4 (2026-09-24): el autor decide las cuatro cuestiones que abrió `PLAN-30` (`C-1` a
> `C-4`), y con ellas cambian `RF-06` y `RF-07` y entran `RF-10` a `RF-12`. Aprobada con su
> decisión literal, citada en cada requisito. Contrastadas las cuatro con `EXAMEN.md`: ninguna
> lo contradice, y `C-2` es literalmente lo que pide §5c.

# SPEC-30 — La puerta de publicación

## Qué problema resuelve

`EXAMEN.md` §5 sitúa validadores en un *«gate antes de publicar una versión»*, y
§5c exige que Lean se ejecute de forma automática y que, *«si falla, la versión
de la novela no se publica y el fallo vuelve al editor como feedback»*. `SPEC-26`
lo aplazó a *«la spec de la puerta de publicación»*, que no existía. Hoy
`specs/lean/` devuelve un veredicto (`0`, `1` o `2`) y **nada del backend lo
llama**. Es `EX-03` de `docs/cobertura-examen.md`.

## Una decisión nuestra, no del enunciado

**Un capítulo en `aceptada_por_rendicion` bloquea la publicación.**

El enunciado dice que no se publique un capítulo que no pasó todos los
validadores; **no habla de rendición**. Una rendición ya exige que no quede
ninguna invariante `bloqueante` abierta (`docs/architecture.md` § "La máquina de
estados"), así que un capítulo rendido puede tener abiertos solo hallazgos
`mayor` o `menor`, y bloquearlo es **más estricto de lo pedido**.

Se mantiene, y el motivo es del autor: **un capítulo que se rindió no es un
capítulo que pasó.**

Es la misma regla que ya verifica el modelo TLA+: `ExigirValidacionCompleta = TRUE`
en `specs/tla/HarnessNovela.cfg`, que impide aceptar un capítulo con la escalera agotada
sin haber pasado los validadores (`CE-2`). Y tiene un coste que hay que saber: una novela
con un capítulo rendido **no se publica nunca** sin volver a escribir ese
capítulo. Cuántas novelas caen ahí está **sin medir**.

## Qué tiene que ser verdad al terminar

- **RF-01.** Una versión se publica **solo si todo esto es verdad**:
  1. todos sus capítulos están aceptados, y **ninguno por rendición**;
  2. no queda abierta ninguna invariante `bloqueante` de nivel capítulo ni de
     nivel obra (`INV-24` entre ellas);
  3. Lean devuelve `0`;
  4. no queda abierto ningún hallazgo de obra del Editor (`RF-07`).
- **RF-02.** Lean se ejecuta **de forma automática** al llegar a la puerta, sobre
  un fichero generado desde la story bible en SQLite, y su código de salida es el
  veredicto. Nadie lo lanza a mano.
- **RF-03.** Si Lean falla, **el fallo vuelve al Editor como feedback** con las
  violaciones concretas (`L-1`…`L-4` y los eventos implicados).
- **RF-04.** Si la puerta no se abre y no quedan intentos, **la generación se
  detiene con error y lo informa**: qué condición de `RF-01` falló y en qué
  capítulo. Nunca queda esperando: es la propiedad de terminación que el
  enunciado pide a TLA+.
- **RF-05.** El veredicto de la puerta y el de Lean se envían como scores
  (`SPEC-29`).

### Resuelto por el autor (v2)

- **RF-06 (antes `O-1`; cambia en v4, `C-2`). Un fallo de Lean vuelve al Editor como
  feedback y la generación se detiene, sin reescribir.** El Editor recibe las violaciones con
  sus eventos y su diagnóstico queda en el informe de parada (`RF-04`), que dice que el dato
  viene del plan. Motivo: lo que Lean comprueba lo fija el plan antes de escribir, así que
  reescribir la prosa no puede arreglarlo, y reintentar sería gasto sin efecto. En palabras
  del autor: *«Vuelve al Editor como feedback y la generación se detiene sin reescribir — el
  enunciado pide justo eso, que el fallo vuelva al editor.»*
- **RF-07 (antes `O-2`; cambia en v4). Los hallazgos de obra del Editor** (`SPEC-26`
  `RF-12`: el arco, la coherencia entre capítulos y el final) **bloquean la publicación.**
  El Editor los convierte en instrucciones para el Escritor sobre los capítulos implicados,
  que se reescriben según `RF-10` y vuelven a pasar por sus puertas. **Tope: 2 reintentos**,
  el mismo que `INV-21` e `INV-22`; no comparte las 3 reescrituras por nota del Editor
  (`SPEC-26` `RF-11`). Agotado el tope, se aplica `RF-04`.
- **RF-08 (antes `O-3`). Cubre la primera versión desde ya**, y las que produzca
  una regeneración cuando `SPEC-23` esté aprobada. Una «versión» con identidad
  propia todavía no existe en el código (`F-43`, `EX-14`).
- **RF-09. El `2` de Lean bloquea igual que el `1`.** «No había bastante dato
  para mirar» no es «se miró y está bien» (`F-54`).

### Decidido por el autor (v4)

- **RF-10 (`C-1`). Reescribir un capítulo ya consolidado es reescribir solo su texto, y
  aceptarlo solo si los hechos no cambian** (`SPEC-23` `S-3`): el borrador nuevo pasa por las
  puertas de texto y su delta tiene que coincidir con el que ya se aplicó. El canon no se
  mueve y nada posterior queda invalidado.
- **RF-11 (`C-3`). Una escena rendida se queda en `aceptada_por_rendicion` después de
  consolidar.** Que la consolidación lo pise contradice `docs/definitions.md`, que la define
  como estado y no como campo porque quien lea la obra necesita saber cuáles fueron. Que está
  consolidada lo sigue diciendo el registro de consolidación.
- **RF-12 (`C-4`). `INV-06` queda sin comprobar, y la puerta no bloquea por ella.** **Es una
  decisión nuestra, una excepción a la Regla 8, y este es su motivo: `INV-06` exige una
  comparación semántica entre hechos canónicos, y hoy no hay quién la haga.** Dos
  condiciones del autor van con ella: queda escrita así, y aparece en el veredicto de la
  puerta y en la tabla de evaluación (`SPEC-31`) como **validador no ejecutado**. En sus
  palabras: *«Un validador que no corre no es un validador que pasó, y el enunciado se
  cumple solo si eso se dice.»*

## Qué queda explícitamente fuera

- Las versiones y la regeneración por cambio del lector: `SPEC-22`, `SPEC-23`.
- Rehacer la correspondencia de TLA+ con `backend/`: `EX-07`, de la sesión de
  TLA+.
- Qué invariantes tiene Lean: están en `specs/lean/`, y el enunciado pide dos
  como mínimo.
- El PDF: `SPEC-27`, que exporta solo versiones que han pasado esta puerta.

## Lo que la gobierna

`EXAMEN.md` §5 y §5c; `SPEC-26` `RF-09`, `RF-11` y `RF-12`; `INV-24`;
`docs/architecture.md` § "La máquina de estados" y § "Severidad"; `F-43`, `F-54`
y `EX-03`; `specs/lean/README.md` y `specs/tla/HarnessNovela.cfg`.
