---
id: SPEC-11
titulo: Lo que hay que mirar mientras el sistema corre
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: f6b3eca
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-11 — Observabilidad del pipeline

Los cinco huecos de arquitectura que inventarió `SPEC-10` al comparar nuestro contrato con
el de la rama `main`. **Ninguno toca `docs/definitions.md`**: ese fue el criterio que los
separó de los cinco de dominio.

Son cinco cosas distintas con un hilo común: **el sistema no se puede conducir mirando solo
si falla.** Los cinco huecos son sitios donde algo va mal sin que nada falle.

---

## C-1 · Tope global de llamadas al modelo

**Es el más urgente de los cinco, y lo es desde `SPEC-10`.** Al decidir que **una
invariante `bloqueante` no admite rendición**, una escena que insiste puede reintentarse sin
final: la salida es humana, y hasta que una persona llegue no hay nada que la pare.

Lo que tenemos hoy no sirve para esto:

| Control | Qué acota | Por qué no basta |
| --- | --- | --- |
| Techo de 100.000 tokens (`P-1`…`P-5`) | Lo **concurrente** | Acota cuánto cabe a la vez, no cuántas veces |
| Tope de 3 reintentos (`SPEC-07`) | Los fallos **de transporte** | Un rechazo por invariante no es un fallo de transporte y no cuenta contra él |
| Rendición | Los `mayor` y `menor` | Las `bloqueante` la tienen prohibida, a propósito |

`main` lo resolvió con su Regla 6: contar delegaciones y frenar antes del límite, con parada
ordenada —escribir el estado, ensamblar lo que haya, dejar constancia—. Y escribió el
motivo, que sigue valiendo: *"un bucle de reintentos mal cerrado sigue siendo capaz de
encadenar cientos de delegaciones"*.

**Qué hay que fijar:** el alcance del tope —por escena, por capítulo, por obra o varios—,
qué pasa al alcanzarlo, y si el contador incluye todas las llamadas o solo las del Escritor.

## C-2 · La tendencia de los recortes

**Esto es lo que levanta la reserva escrita en `SPEC-01` §2.4.** El orden de recorte se
eligió razonando, dos veces. Lo único que dirá si es el bueno es la serie:

> *"Si en los últimos capítulos aparecen recortes que no aparecían en los primeros, la
> ventana está creciendo con N y la compactación no está haciendo su trabajo. Es la señal de
> alarma más importante del informe."* — `EJECUCION.md` §7

En `main`, `Ventana.recortes` es una lista en español que viaja con cada ventana y acaba en
el informe. Aquí el recorte ocurre y **no deja rastro**.

**Qué hay que fijar:** que cada ensamblado registre qué recortes aplicó —y **cuáles fueron
reducciones y cuáles eliminaciones**, que desde `SPEC-12` no es lo mismo—, y que la serie
por obra sea consultable. Un recorte suelto no dice nada; el que aparece en la escena 40 y
no aparecía en la 3, sí.

## C-3 · El modelo del Juez no cambia durante una obra

`main` lo tiene como regla inviolable, y el argumento es más fino de lo que parece: al
descubrir que **el muestreo no se puede fijar** —ni temperatura, ni semilla—, el modelo se
quedó como *"la única palanca que queda para que dos intentos del mismo capítulo sean
comparables"*.

Aquí importa desde `SPEC-10`: `Escena.borrador_aceptado` elige el menos malo, y elegir exige
comparar. Si el Juez cambia de modelo a mitad de obra, dos puntuaciones dejan de significar
lo mismo y la elección se vuelve arbitraria sin que nada avise.

**Qué hay que fijar:** que `A-06` diga que el modelo del Juez es fijo dentro de una obra,
qué pasa si hay que cambiarlo, y si la traza registra cuál se usó — sin eso, la regla no se
puede comprobar a posteriori.

## C-4 · Aislamiento: qué ve cada verificador

`main` da a cada validador **solo su ventana**, con `omitClaudeMd: true` y herramientas
mínimas, y razona por qué: *"si los tres vieran el mismo material y las reglas del proyecto,
serían tres copias del mismo juicio"*.

Es nuestra **Regla 3** de `docs/verification.md` aplicada a los jueces, y es la misma idea
que sostiene los dos campos de tokens de `SPEC-08`. `A-06` dice hoy que el Juez no comparte
sesión con el Escritor; no dice qué ve.

**Qué hay que fijar:** qué recibe cada verificador y qué se le niega explícitamente —en
particular si ve las reglas del proyecto, que es lo que convertiría su juicio en un eco del
nuestro—. Importa más desde `SPEC-04`, donde el Juez pasó a ser **desempate** de tres
invariantes: un desempate que ve lo mismo que la regla no desempata nada.

## C-5 · El ensamblador del manuscrito no corrige nada

`main` lo tiene como regla y explica el motivo con precisión:

> *"Si el ensamblador retocara el texto, el informe dejaría de describir el manuscrito:
> diría que el capítulo 7 se aceptó con tres problemas, pero el capítulo 7 del manuscrito ya
> no sería ese. La trazabilidad entre lo que se auditó y lo que se entrega es lo único que
> hace útil al informe."*

Aquí no hay ninguna regla que lo impida, y **desde `SPEC-10` hace más falta que antes**: una
escena en `aceptada_por_rendicion` llega al manuscrito con sus hallazgos abiertos, y si algo
la retoca por el camino, esos hallazgos describen un texto que ya no existe.

**Qué hay que fijar:** que lo que se entrega sea exactamente lo que se auditó, y dónde vive
esa prohibición.

---

## Qué queda explícitamente fuera

- **Los números**: topes, umbrales de alarma, retención de series.
- **El formato del informe.** Qué se mira está aquí; cómo se pinta es del frontend.
- **Métricas de calidad de la novela.** Eso es `docs/verification.md`.
- **Los `RF` y endpoints que esto genere en `SPEC-01`.** Vienen después.
- **Reabrir §2.4.** `C-2` construye el instrumento que permitirá releer el orden; releerlo
  es otra decisión, y la marca `Caduca con:` de §2.4 la disparará sola.

## Qué gobierna esto

De esta línea: `SPEC-10` huecos 6 a 10; `SPEC-12` §2.4 y su reserva; `A-06`; `P-1`…`P-5`;
`SPEC-07` y `SPEC-08`; la Regla 3 de `docs/verification.md`; `VER-26`, `VER-41`, `VER-56`.
De la rama `main`: `EJECUCION.md` §4 reglas 3, 5 y 6 y §7; `DECISIONES.md` decisión 9;
`src/contexto.py` y `src/ensamblador.py`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | `C-1`: ¿el tope global es por escena, por obra, o los dos? | **Los dos.** Por escena acota a la que insiste, que es el caso que abre `SPEC-10`; por obra acota el agregado, que es lo que `main` sufrió. Uno solo deja pasar el otro caso |
| 2 | `C-1`: ¿qué pasa al alcanzarlo? | Parada ordenada como en `main`: se escribe el estado, se deja constancia y **no se pierde lo hecho**. Distinguible de un fallo: no falló nada, se agotó un presupuesto |
| 3 | `C-1`: ¿cuenta todas las llamadas o solo las del Escritor? | Todas. `EJECUCION.md` §7 avisa de que *"si los validadores gastan más tokens que el escritor, estás pagando la auditoría más cara que la novela"*, y con solo el Escritor eso no se ve |
| 4 | `C-2`: ¿la serie de recortes vive en la traza de `SPEC-08` o aparte? | En la traza. Ya registra los identificadores que entraron; los recortes son la otra cara del mismo dato, y separarlos obliga a reconciliar dos fuentes de lo mismo |
| 5 | `C-3`: ¿el modelo fijo es del Juez solo, o de todos los agentes? | Del Juez. Cambiar el modelo del Escritor a mitad de obra afecta al estilo y lo caza `INV-15`; cambiar el del Juez rompe la comparabilidad, que no lo caza nada |
| 6 | `C-4`: ¿el Juez ve las reglas del proyecto? | **No.** Si las ve, su juicio es un eco del nuestro, y como desempate de `INV-03`, `INV-11` e `INV-14` dejaría de aportar la segunda opinión que justifica que exista |
| 7 | ¿`C-5` necesita validador, o basta con declararlo? | Necesita. Es la misma exigencia que aplicamos a la independencia de `VER-41`: una regla que nadie comprueba es una intención |


# Qué se tocó al aplicarla

`docs/architecture.md`: el tope global con su estado `detenido_por_presupuesto` y su
transición; los recortes y el modelo usado en la traza; dos decisiones nuevas sobre el Juez;
y la sección del ensamblador que no corrige. `docs/verification.md`: `VER-60` con su caso
negativo y los recuentos.

## Lo que la spec no previó

**Una marca `Caduca con:` estaba mal apuntada, y la puso esta misma línea de trabajo dos
commits antes.** La reserva de `SPEC-01` §2.4 apuntaba al **fichero de esta spec**, de modo
que habría caducado al moverla a `specs/aplicadas/`. Pero aplicar `SPEC-11` **diseña** el
registro de recortes; no lo crea. La reserva se levanta cuando exista el dato, no cuando
exista el diseño, así que la marca pasa a `backend/` como las otras siete.

Es el error que `SPEC-05` existe para evitar, cometido al ponerlo: una condición de
caducidad que se cumple antes que el hecho que describe. Lo cazó escribir esta spec, no
`VER-56`, que solo comprueba si la ruta existe y no si es la correcta — y eso ya está en su
punto ciego declarado.

**Tres reglas quedan sin validador**, y conviene decirlo: el tope global, el modelo fijo del
Juez y lo que el Juez no ve. Las tres se declaran aquí y ninguna se comprueba. Solo `C-5`
tenía su pregunta al respecto y por eso solo `C-5` salió con `VER-60`.
