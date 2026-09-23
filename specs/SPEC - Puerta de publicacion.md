---
id: SPEC-30
titulo: La puerta de publicación, con Lean
estado: en_revision
aprobada_por:
fecha_aprobacion:
fecha: 2026-09-23
version: 1
---

> **Historial.** v1: redactada con la decisión del autor sobre la rendición
> (2026-09-23). Quedan abiertas `O-1` a `O-3`; las propuestas marcadas como tales
> esperan confirmación.

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

Es la misma regla que ya verifica el modelo TLA+: `PublicarAlAgotarTope = FALSE`
en `specs/tla/HarnessNovela.cfg`. Y tiene un coste que hay que saber: una novela
con un capítulo rendido **no se publica nunca** sin volver a escribir ese
capítulo. Cuántas novelas caen ahí está **sin medir**.

## Qué tiene que ser verdad al terminar

- **RF-01.** Una versión se publica **solo si todo esto es verdad**:
  1. todos sus capítulos están aceptados, y **ninguno por rendición**;
  2. no queda abierta ninguna invariante `bloqueante` de nivel capítulo ni de
     nivel obra (`INV-24` entre ellas);
  3. Lean devuelve `0`.
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

## Cuestiones abiertas

- **O-1. Qué hace el Editor con el feedback de Lean.** El Editor no reescribe
  (`SPEC-26` `RF-09`). *Propuesta:* lo convierte en instrucciones para el
  Escritor sobre los capítulos implicados, que vuelven a escribirse y a pasar por
  sus puertas. **Sin propuesta sobre el tope de intentos** de ese bucle: es un
  número que decide cuándo se rinde el sistema, y lo decide el autor.
- **O-2. ¿Bloquean los hallazgos de obra del Editor** (`SPEC-26` `RF-12`, el
  juicio del arco y del final)? Sin propuesta: es una política de calidad.
- **O-3. Qué versiones cubre.** *Propuesta:* la primera versión desde ya, y las
  que produzca una regeneración cuando `SPEC-23` esté aprobada. Una «versión» con
  identidad propia todavía no existe en el código (`F-43`, `EX-14`).
- **Propuesta, pendiente de confirmar: el `2` de Lean bloquea igual que el `1`.**
  «No había bastante dato para mirar» no es «se miró y está bien» (`F-54`).

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
