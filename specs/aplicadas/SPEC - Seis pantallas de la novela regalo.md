---
id: SPEC-35
titulo: Seis pantallas de la novela regalo, rediseñadas — entrevista, cuaderno, cambio, versión y portada
estado: aplicada
aprobada_por: "autor del proyecto, en sesión («aprovado»)"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 5
fecha_aplicacion: 2026-09-25
commit_de_aplicacion: 8666d03
---

> **v5 (2026-09-24), la página de la generación; decidido por la sesión autónoma por
> delegación escrita del autor («Decide tú todo […] No pares a consultarme»).** El autor pidió
> terminar «las pantallas de entrevista y generación de `SPEC-35`», pero la generación no
> estaba entre las seis: la propuesta visual la dibujaba como «el escritor en su mesa», que esta
> spec dejó fuera. Sin ella, quien encarga la novela no ve en qué acaba lo que ha pagado: la
> página de `SPEC-33` no dice nada si el lanzamiento falla antes del primer capítulo (por
> ejemplo, sin `claude` en la máquina), y al terminar no lleva a leer. Entra **`RF-13`**, y
> sigue fuera «el escritor en su mesa» como ilustración. No cambia ninguna otra decisión.

> **v4 (2026-09-25), lo que encontró el plan; no cambia ninguna decisión.** `RF-02` choca con
> `CLAUDE.md`, que dice que una escena se muestra siempre con su estado y con los hallazgos
> abiertos que tenga, y en lo técnico `CLAUDE.md` manda sobre una spec. `RF-02` **no se aplica
> al estado ni a los hallazgos de una escena mostrada con su texto** (el índice y el capítulo):
> se rediseñan, pero no se quitan. Quitarlos para el cliente exige revisar `CLAUDE.md`, y eso
> es una decisión del autor.

> **v3 (2026-09-25), decisión del autor:** *«La entrevistadora que se llame Xime.»* La
> cuestión 1 pasa de «Clara» a **«Xime»**, con el nombre en la configuración de la interfaz
> igual que antes. La spec sigue aprobada: es la decisión del autor.

> **v2 (2026-09-25), aprobada** sin comentarios: se aprueban las propuestas de las cuestiones 1
> a 4. La entrevistadora se llama «Clara», con el nombre en la configuración de la interfaz. El
> PDF solo se ofrece con la obra publicada. Las páginas de `PLAN-22` las rediseña esta spec,
> con un reparto de ficheros acordado con esa sesión antes de aprobar el plan. Y el orden es
> primero las cuatro de rediseño y después la entrevista y el cuaderno, tras el plan de
> `SPEC-34`.

# SPEC-35 — Seis pantallas de la novela regalo, rediseñadas

> **Lo que el autor ya decidió, el 2026-09-25**, sobre la propuesta visual del lienzo
> «Novela regalo · propuesta visual», página «Recorrido completo (A + D)»:
>
> - *«Me quedo con cinco pantallas: la entrevista con el cuaderno, el cuaderno completo, pedir
>   un cambio, qué se reescribe y la versión nueva. Más la portada al sacar el libro.»*
> - *«No necesitamos la versión móvil.»*
> - *«No abrimos la edición manual de texto: SPEC-20 lo prohíbe y no lo voy a cambiar por una
>   pantalla.»*
> - Sobre el coste en el cuaderno completo: **mantener la confirmación** de `SPEC-33` `RF-12`.
> - Sobre el cuaderno lateral: **incluirlo, y la parte de los nombres después de `SPEC-34`**.
> - Entran **descargar el PDF en la portada**, **el aviso «por tu cambio: …»** y **el nombre de
>   la entrevistadora**. Las respuestas rápidas a los avisos quedan fuera.

## Qué problema resuelve

La web de la novela regalo funciona (`SPEC-22`, `SPEC-33`), pero está hecha como una
herramienta: enseña lo que el harness sabe, con su vocabulario. Quien encarga un regalo
necesita otra cosa. Necesita una conversación con alguien y un cuaderno donde ve lo que ya se
sabe. Necesita un libro que se abre, y un cambio que se entiende sin saber qué es una
«versión de obra».

**Casi todo ya existe y esta spec lo rediseña, no lo construye.** De las seis pantallas,
cuatro tienen ya todo su comportamiento en el frontend. Lo nuevo son cuatro piezas:

| Pantalla | Qué existe hoy | Qué es nuevo |
| --- | --- | --- |
| Entrevista con el cuaderno | La conversación con los avisos en su turno (`SPEC-33` `RF-05`..`RF-10`) | El cuaderno lateral, con la ficha tal como va. El nombre de la entrevistadora |
| Cuaderno completo | El estado «se puede cerrar» y la confirmación de gasto (`SPEC-33` `RF-09`, `RF-12`) | El repaso de la ficha, y el título, la premisa y la dedicatoria propuestos, antes de cerrar |
| Pedir un cambio | Todo (`SPEC-22` `RF-47`..`RF-51`, `RF-55`) | Nada funcional |
| Qué se reescribe | Todo: los capítulos que se tocan, la promesa y su punto ciego | Nada funcional |
| Versión nueva | «Cambió», el selector de versión y la versión anterior navegable (`SPEC-22` `RF-52`..`RF-54`) | El aviso con el texto de la petición que la originó |
| Portada | El título, la dedicatoria y los enlaces (`SPEC-22` `RF-46`) | Descargar el PDF |

## Qué tiene que ser verdad al terminar

Los identificadores `RF-xx` son de esta spec y no se renumeran.

### Lo común

- **RF-01** — Las seis pantallas llevan el estilo elegido en la propuesta: crema y madera para
  leer y encargar, y noche para lo que ocurre mientras se escribe. Títulos en una serif de
  presentación y lectura en una serif de texto. Todos los colores nuevos entran en los tokens de
  `shared/ui/tema` (`SPEC-22` `RF-59`), y ningún fichero fuera de allí escribe un color. **La
  paleta sigue siendo provisional**, marcada como tal, hasta que llegue la de Qaracter.
- **RF-02** — Ninguna de las seis pantallas enseña notas del Editor, hallazgos, delegaciones ni
  vocabulario interno (`estado_de_escena`, «consolidada», «suelo», identificadores). **La
  excepción es la confirmación de gasto** de `RF-07`: la decidió el autor en `SPEC-33` y la
  mantiene aquí.
- **RF-03** — Cambiar el aspecto no cambia el comportamiento: todo lo que `SPEC-22` y `SPEC-33`
  exigen de estas pantallas sigue siendo verdad. Ejemplos: la interfaz no calcula estado, un dato
  ausente se dice como ausente y el botón que gasta no aparece hasta tener sus cifras. Sus
  pruebas siguen pasando o se reescriben diciendo qué comprobaban, nunca se borran.

### La entrevista con el cuaderno

- **RF-04** — La conversación tiene **una entrevistadora con nombre y cara**. El nombre sale de
  la configuración de la interfaz, y el Entrevistador (el agente) no cambia: la web lo presenta,
  y el modelo no finge ser nadie.
- **RF-05** — A su lado, **un cuaderno** enseña lo que la ficha ya sabe, lo que falta y cuánto
  falta, **tal como lo da el backend**; la web no cuenta campos. Hoy el historial no trae la
  ficha, así que exponerla es trabajo del backend.
- **RF-06** — **Los nombres del cuaderno son los de `SPEC-34` `RF-01`**: los campos propios
  donde el comprador escribe los nombres, fuera del modelo. Esa parte del cuaderno **no se
  construye antes de que exista el plan de `SPEC-34`**. Cómo se piden los nombres y qué guarda
  el historial lo decide aquel plan, y esta spec solo les da estilo. El cuaderno enseña siempre
  el nombre real y nunca el pseudónimo.

### El cuaderno completo

- **RF-07** — Cuando el backend dice `puede_cerrar`, la entrevista enseña **el cuaderno
  completo**: el repaso de la ficha y el título, la premisa y la dedicatoria propuestos, con la
  opción de seguir la conversación si algo no está bien. Cerrar la ficha es un acto aparte y
  **sin vuelta atrás** (`SPEC-25`), y la pantalla lo dice. Después de cerrar viene **la
  confirmación de `SPEC-33` `RF-12`** con sus tres cifras, rediseñada y sin quitarle nada. **No se
  lanza ninguna generación sin esa confirmación.**

### Cambiar un capítulo

- **RF-08** — **Pedir un cambio** conserva el flujo de `SPEC-22` `RF-47`..`RF-51` y `RF-55`: el
  fragmento citado, qué hecho o qué nombre cambiar, las palabras del lector, y nada cambia
  hasta confirmar.
- **RF-09** — **Qué se reescribe** enseña los capítulos que el backend propone como una balda,
  con los que se tocarían resaltados, y la promesa y su punto ciego juntos y tal como llegan.
  Confirmar manda exactamente la lista recibida. El texto de la pantalla no promete nada que el
  sistema no haga.
- **RF-10** — **La versión nueva** conserva «cambió», el selector de versión y la versión
  anterior navegable. **Nuevo:** un capítulo cambiado dice qué petición lo cambió, con las
  palabras del lector. Hoy la versión solo guarda el identificador de la petición, así que el
  texto lo tiene que dar el backend. Una versión sin petición no enseña ningún aviso.

### La portada

- **RF-11** — La portada es la cubierta de un libro, con el título y la dedicatoria (`SPEC-32`).
  Desde ella se empieza a leer o se abre el índice.
- **RF-12** — **Descargar el PDF**: una ruta HTTP sobre la generación que ya existe
  (`SPEC-27`), con el libro de la versión vigente. Si esa obra no tiene PDF que dar, la portada
  no ofrece el botón y el backend lo dice con su motivo (cuestión 2).

### La generación (v5)

- **RF-13** — La página de la generación (`SPEC-33` `RF-14`..`RF-17`) lleva **el estilo noche**
  de `RF-01` y no pierde nada de lo que enseña. Dos cosas nuevas, las dos resueltas por el
  backend: **si el último lanzamiento de la obra falló**, la página lo dice con el motivo tal
  como llega, aunque no haya empezado ningún capítulo; y **cuando la novela termina**, lleva a
  leerla: «Leer la novela» si se publicó, y si no se publicó, «Leer lo escrito» diciendo que
  no está publicada y por qué, tal como lo dice el backend. Lo que ya escribió la versión se
  puede leer siempre: la vigente de una obra sin publicar es la 1 (`F-121`).

## Qué queda explícitamente fuera

| Fuera | Por qué |
| --- | --- |
| **Editar a mano el texto** | `SPEC-20`: el estado consolidado no se toca a mano. Decisión literal del autor, arriba |
| El diseño móvil | *«No necesitamos la versión móvil.»* Las pantallas no rompen a 390 px, pero no tienen un diseño propio |
| La estantería de madera, el escritor en su mesa (como ilustración; la página de la generación entra en `RF-13`) y la vista de administración | Se eligieron en la propuesta, pero no entran en esta spec. Cada una sería otra spec; la de administración necesita decidir antes quién administra y cómo entra, y hoy no hay usuarios |
| Las respuestas rápidas a los avisos | Decisión del autor |
| Cambiar la tipografía de interfaz | La propuesta usa otra; no se ha decidido |
| La lectura a dos páginas, la entrega «lista para regalar» | No están entre las seis |
| La forma de los campos de nombres | Es del plan de `SPEC-34` (su cuestión 4) |

## Lo que la gobierna

- `SPEC-20` (qué se puede editar a mano), `SPEC-22` (la lectura y la petición de cambio, y el
  contrato congelado), `SPEC-23` (versiones), `SPEC-25` (la entrevista), `SPEC-27` (el PDF),
  `SPEC-32` (la dedicatoria), `SPEC-33` (la novela regalo en la web y la confirmación de gasto),
  `SPEC-34` (los nombres fuera del modelo).
- `CLAUDE.md`: la interfaz muestra estado, no lo calcula.

## Cuestiones para la aprobación

Cada una lleva una propuesta. Aprobar sin comentarios es aprobar las propuestas.

1. **El nombre de la entrevistadora.** **Decidido en v3: «Xime».** *Propuesta original:* «Clara», como en la propuesta visual, en la
   configuración de la interfaz para poder cambiarlo sin tocar código.
2. **Cuándo se ofrece el PDF.** *Propuesta:* solo con la obra **publicada**. Un PDF de una
   novela a medio escribir o parada se leería como el regalo terminado.
3. **Quién toca las páginas de `PLAN-22`.** La portada, el índice, el capítulo y
   `features/pedir-cambio` los hizo la otra sesión. *Propuesta:* los rediseña esta spec, y el
   reparto de ficheros se acuerda con esa sesión antes de aprobar el plan, como en `SPEC-33`.
4. **El orden.** *Propuesta:* primero las cuatro pantallas que son solo rediseño (pedir un
   cambio, qué se reescribe, la versión nueva y la portada, con sus dos lecturas nuevas) y
   después la entrevista y el cuaderno, que esperan al plan de `SPEC-34`.
