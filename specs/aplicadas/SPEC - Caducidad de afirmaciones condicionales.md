---
id: SPEC-05
titulo: Caducidad de las afirmaciones que son ciertas porque algo no existe
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: 7b04aa7
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-05 — Caducidad de afirmaciones condicionales

## Qué problema resuelve

`Docs/verification.md`, `Docs/architecture.md` y dos specs aplicadas contienen **nueve
afirmaciones que son ciertas porque algo no existe**. Las nueve son correctas hoy. Ninguna
es un error.

El problema es que **las nueve dejan de ser ciertas el mismo día** —el día que exista
`backend/`— y nada avisa. Un documento que se vuelve falso de golpe y en silencio es peor
que uno que nunca fue cierto, porque nadie lo va a releer buscando el momento.

Ya sabemos que este patrón muerde. `VER-45` tenía una exención de la misma forma
—*"se eximen las de la columna «Dónde vive», que son planes por construcción"*—, la premisa
era cierta, la conclusión no, y acabó tapando diecisiete rutas mal escritas que el
validador existe para cazar. Está registrado como `F-16` y es `MF-24`.

### Las nueve

| # | Afirmación | Condición que la sostiene | Dónde |
| --- | --- | --- | --- |
| 1 | «0 implementados · 43 bloqueados · 5 escritos y retirados» | No existen `backend/`, `frontend/`, `harness/` | `verification.md` §Estado de implantación |
| 2 | La exención y el punto ciego de `VER-45` | `features/` y `commons/` no existen en la raíz | **Ya materializada.** Cerrada en `F-16` |
| 3 | «Migración: ninguna hoy» · «la más barata que existe» | No hay base de datos | `SPEC-03`, `SPEC-04` |
| 4 | «El contenido queda **por ahora** duplicado a propósito» | La limpieza `A-08` no se ha hecho | `architecture.md` |
| 5 | «El reparto de tokens no está fijado… se fija **cuando haya medidas reales**» | No hay ejecuciones | `architecture.md` |
| 6 | «Aquí no se ha medido ninguna, y **no las hay porque no hay sistema que medir**» | No hay sistema | `verification.md` (prevalencias MAST) |
| 7 | «Métrica que no tenemos y conviene adoptar **cuando haya texto**» | No hay obra generada | `verification.md` (densidad ConStory) |
| 8 | «No es caro, **pero no hay base todavía**» | No hay base de datos | `PC-1` |
| 9 | «Sin identidad no hay nada que comprobar» | No hay autenticación | `PC-2` |

## Qué tiene que ser verdad al terminar

### C-1 · Cada afirmación condicional lleva su condición pegada, y en forma comprobable

Se adopta una marca, escrita **en la propia afirmación**, nunca en una lista aparte:

```
**Caduca con:** `backend/`
```

Dos reglas sobre la marca:

- **Es una ruta, no una frase.** `` `backend/` ``, no *"cuando tengamos backend"*. Una
  frase no se puede comprobar; una ruta sí.
- **Va pegada a la afirmación que sostiene.** Si la afirmación se mueve o se reescribe, la
  marca viaja con ella. Es lo único que impide que las dos se separen.

Cuando la condición no sea una ruta —el caso 9, la autenticación— la marca apunta al
documento y sección que la excluye: `` `SPEC-01` §2.5 ``. Se comprueba que esa sección siga
diciendo lo que la marca supone, que es la mitad de sustancia de una cita.

### C-2 · Un validador comprueba las marcas contra el repositorio

`VER-56` — *«Ninguna afirmación marcada con una condición de caducidad tiene su condición
ya cumplida.»*

| Campo | Valor |
| --- | --- |
| Clase | `A` — análisis estático |
| Metodología | static analysis |
| Criterio de salida | Se recorren las marcas `Caduca con:` de todos los documentos. Para cada una, la ruta **no** existe en disco. Cero marcas con su condición cumplida |
| Punto ciego | **Ve la ruta, no el argumento.** Que `backend/` no exista no garantiza que la afirmación siga siendo cierta por el motivo que dice. Y no detecta una afirmación condicional **sin marcar**: eso sigue siendo lectura humana, como `PC-13` |
| Dónde vive | `CI` |
| Caso negativo | Se crea `backend/` y una afirmación marcada con esa ruta: `VER-56` falla |

`VER-56` es el siguiente identificador libre: el máximo publicado es `VER-55` y `VER-44`
está quemado.

**Por qué pasa la Regla 2.** `VER-45` mira rutas **citadas** y pregunta si existen o encajan
en el árbol. `VER-56` mira rutas **marcadas** y pregunta lo contrario: que **no** existan.
Un fallo de `VER-45` es una ruta mal escrita; uno de `VER-56` es una afirmación que dejó de
ser cierta. No comparten punto ciego ni se tapan entre sí.

**Por qué pasa la Regla 3.** No comparte implementación con lo que valida: las marcas son
prosa en documentos, y el validador es código en CI.

## Qué queda explícitamente fuera

- **Una sección que reúna las nueve.** Se consideró y **se descarta**: sería una tercera
  copia de un dato que ya vive en dos sitios, se separaría de lo que describe y nada
  apuntaría de la afirmación a su fila. Es el mismo mecanismo que `A-08` y `MF-23`. La
  tabla de arriba es el inventario que justifica esta spec, no el registro permanente: se
  queda en esta spec y no se traslada a `Docs/`.
- **Detectar afirmaciones condicionales sin marcar.** No hay forma automática razonable;
  es la misma limitación de `PC-13` y se asume igual.
- **Qué hacer cuando una caduca.** `VER-56` avisa; qué se reescribe es de quien lo lea.
- **Marcar afirmaciones fuera de las nueve.** La convención queda disponible, pero esta
  spec solo se compromete a las nueve inventariadas.

## Qué gobierna esto

`MF-24` (criterio verde por construcción), `PC-13` (un criterio puede remitir a algo que no
existe), `F-16` (la materialización en `VER-45`), y la Regla 2 y la Regla 3 de
`Docs/verification.md`.

**Alcance ampliado el 2026-09-22.** `C-2` decía que `VER-56` recorre las marcas de los
documentos. Al aprobar `PLAN-01` se extendió **al código**: los dos números provisionales de
`SPEC-07` llevan su marca en `commons/config.py`, y un refactor las mueve sin que nadie las
lea, así que las dos marcas que más importan habrían sido las únicas sin vigilancia. Es el
mismo argumento que la regla de independencia de `SPEC-08`: no dejar sin vigilar el
mecanismo de vigilancia.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿La marca es `Caduca con:` o prefieres otra etiqueta? | `Caduca con:`. Es literal, se lee en prosa y se busca con `grep` |
| 2 | ¿Se marca el caso 2, que ya está materializado? | No. Se cerró en `F-16`; marcarlo sería marcar algo que ya caducó |
| 3 | ¿`VER-56` falla el build o solo avisa? | Falla. Un aviso en CI que nadie mira es el mismo problema otra vez |
| 4 | ¿Las marcas en `SPEC-03` y `SPEC-04` (caso 3) se tocan, estando ya aplicadas? | Sí, pero solo la marca. Una spec aplicada no se reescribe; añadir la condición de caducidad no cambia lo que decidió |
