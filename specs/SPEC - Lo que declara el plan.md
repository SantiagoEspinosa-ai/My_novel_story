---
id: SPEC-15
titulo: Qué hechos existen lo declara el plan; quién los sabe es otra cosa
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 9b40b2c
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-15 — Lo que declara el plan

## Qué problema resuelve

Una generación real de seis escenas salió con **conocimiento 0 y fichas 0**, y ningún
validador falló. La causa fue un **punto muerto**:

> La lista de identificadores del prompt se derivaba del **registro de conocimiento**. El
> registro solo crece cuando una escena **revela** algo. Revelar exige citar un
> identificador de la lista. **La lista estaba vacía y no podía llenarse.**

El modelo hizo lo correcto —el prompt decía *"hechos: (ninguno)"* y no citó ninguno— y el
sistema entero se quedó hueco sin que nada avisara. Funcionó en la ejecución anterior
**solo porque el fixture sembraba el registro a mano**.

### La distinción que faltaba, y que causó el ciclo

> **Qué hechos existen lo declara el plan. Quién los sabe es lo que comprueba `INV-03`.**

Son dos cosas y estaban juntas. Un `HechoCanonico` existe porque la obra lo planificó; que
`per-marta` lo sepa desde la escena 4 es un `RegistroDeConocimiento`. Derivar lo primero de
lo segundo crea el ciclo: no hay hechos hasta que alguien los sabe, y nadie puede saberlos
hasta que existen.

**El argumento de fondo es el mismo que gobierna el resto del plan.** La escaleta planifica
el cambio de valor, el POV y la curva de dread **antes de que exista texto**, y los hechos
son material del mismo tipo. Un hecho que nace al escribirse es **un hecho que nadie
planificó**, y entonces no se puede comprobar que la novela revele lo que se propuso
revelar: solo que revela algo.

---

## C-1 · Los `HechoCanonico` los declara el plan

`Escaleta` gana `hechos_canonicos[]`, y los hechos existen desde que se planifican, no
desde que se escriben.

**`escena_de_establecimiento` cambia de significado**, y en la dirección correcta:

| Antes | Después |
| --- | --- |
| Dónde **nació** el hecho | Dónde **se establece en el texto** |
| Obligatorio: un hecho no existe sin ella | **Opcional**: un hecho declarado puede no estar establecido todavía |

Ese es justamente el campo que `INV-03` compara —que revelar no preceda a establecer—, así
que pasa a significar lo que la invariante ya suponía que significaba.

## C-2 · `Presagio` tiene la misma ambigüedad, y es peor

`Presagio.escena_de_plantado` es **obligatorio**, así que un presagio **no puede existir sin
estar ya plantado**. Un presagio que el plan previó y el texto nunca plantó es hoy
**inexpresable**, no solo invisible. Y `estado_de_presagio` —`plantado`, `pagado`,
`huerfano`— no tiene valor para "declarado y sin plantar".

Mismo cambio: `escena_de_plantado` pasa a **opcional** y significa *dónde lo planta el
texto*. El estado gana un valor para el hueco que esto destapa.

**Y `INV-09` cambia de alcance sin cambiar de enunciado.** Dice *"todo presagio plantado se
paga antes del final"*, y con esto pasa a poder distinguir tres cosas donde antes veía dos:
plantado y pagado, plantado y huérfano, y **declarado y nunca plantado**, que hasta hoy no
existía como caso.

## C-3 · El hueco nuevo es detectable, y ese es medio motivo del cambio

**Un hecho declarado y nunca establecido** —y su gemelo, **un presagio declarado y nunca
plantado**— son defectos reales que hoy **no se pueden ni nombrar**: la novela prometió algo
en su plan y el texto no lo entregó.

Es exactamente el tipo de fallo que este proyecto persigue: silencioso, sin error, y que
solo se ve leyendo la obra entera y notando que falta algo. Con los hechos declarados pasa a
ser **una diferencia de conjuntos**, que es barata y tiene punto ciego propio.

## Qué queda explícitamente fuera

- **Quién declara los hechos**: si el Escaletador los propone, si vienen del `Brief`, o las
  dos cosas. Es del plan de implementación.
- **Los validadores del hueco de `C-3`.** La spec deja el hueco nombrable; el validador
  viene después y tendrá que declarar su punto ciego.
- **Reabrir `INV-03` o `INV-09`.** Ninguna cambia de enunciado.
- **Las fichas vacías.** Salen del mismo punto muerto y se arreglarán solas cuando los
  deltas vuelvan a tener revelaciones.

### Migración

`hecho_canonico` y `presagio` pierden una restricción `NOT NULL` y `escaleta` gana una
tabla. **Ya no es gratis**: desde `PLAN-01` A3 existen migraciones versionadas, así que esto
necesita la suya numerada en el mismo commit.

## Qué gobierna esto

`HechoCanonico`, `Presagio`, `SetupYPago`, `Escaleta` y `estado_de_presagio` de
`Docs/definitions.md`; `INV-03` e `INV-09`; `F-29` y `F-30` de `Docs/verification.md`;
`VER-37` y `VER-64`; y la Regla 4, porque el punto muerto se manifestó en la frontera del
prompt y se diagnosticó mirando el estado, no un error.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿`escena_de_establecimiento` pasa a opcional, o se añade un campo aparte? | **Opcional.** Un campo aparte tendría dos fuentes para la misma pregunta, y la vieja seguiría mintiendo |
| 2 | `estado_de_presagio` gana un valor para "declarado y sin plantar". ¿Cuál? | `declarado`, y va **antes** de `plantado`: es el estado en el que nace un presagio que el plan previó |
| 3 | ¿Los hechos se declaran en `Escaleta` o en `Brief`? | En `Escaleta`. El `Brief` es lo que el autor pide; la `Escaleta` es el plan, y un hecho canónico es material de plan |
| 4 | ¿Un hecho puede establecerse en una escena que el plan no previó? | Sí, y se marca. Prohibirlo obligaría a replanificar por cada hallazgo del texto; no marcarlo perdería la diferencia entre lo planificado y lo improvisado |
| 5 | ¿`INV-09` pasa a mirar también los `declarado`? | **No, y no se amplía: pide invariante propia.** Su enunciado no cambia y ampliarlo es una decisión de severidad: un presagio nunca plantado no es lo mismo que uno plantado y no pagado |


Las cinco se respondieron el 2026-09-23. La 5 abrió una decisión, anotada en
`Docs/definitions.md`: **lo declarado y nunca entregado pide invariante propia**, porque un
presagio nunca plantado incumple el plan y uno plantado y no pagado rompe una promesa al
lector — y con la puerta de capítulo, una severidad `menor` significaría que la obra se
firma habiendo incumplido su propio plan.
