---
id: SPEC-13
titulo: Un hecho dura o no dura, y eso no es lo mismo que saber cuánto se sabe de él
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-22
fecha_aplicacion: 2026-09-22
commit_de_aplicacion: 5bcb39f
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
version: 1
---

# SPEC-13 — Durabilidad de los hechos

## Qué problema resuelve

`SPEC-12` decidió que la forma reducida del bloque 4.º del recorte —el estado del mundo—
conserva el registro de conocimiento entero y **reduce los hechos del mundo a los
duraderos**. Para eso hace falta poder decir cuáles lo son, y hoy no se puede:
`HechoCanonico` tiene `id`, `enunciado`, `escena_de_establecimiento`, `certeza` y
`contradice[]`, y **ninguno dice cuánto dura**.

**El atajo que hay que no tomar** es derivar la durabilidad de `certeza`. Son **ejes
independientes**:

| | Efímero | Duradero |
| --- | --- | --- |
| `establecido` | *"la puerta está abierta"* | *"Marta es hermana de Ana"* |
| `implicito` | *"alguien ha estado fumando aquí"* | *"la casa no quiere que se vayan"* |
| `disputado` | *"Marta dice que oyó pasos"* | *"el padre murió en el incendio, según el pueblo"* |

Derivar una de la otra confundiría **cuánto sabemos de algo** con **cuánto dura**, y el
resultado sería que el recorte se llevara hechos estructurales por implícitos, o conservara
puertas abiertas por establecidas.

Es el mismo tipo de error que ya corregimos una vez: `certeza` responde a *"¿esto es verdad
en la ficción?"* y la durabilidad a *"¿sigue siéndolo dentro de diez escenas?"*.

## Qué tiene que ser verdad al terminar

### C-1 · `HechoCanonico` gana durabilidad

| Clase | Atributo nuevo | Gobernado por |
| --- | --- | --- |
| `HechoCanonico` | **durabilidad** | `durabilidad_del_hecho` |

| Enumeración nueva | Atributos que la usan | Valores |
| --- | --- | --- |
| `durabilidad_del_hecho` | `HechoCanonico.durabilidad` | `permanente`, `efimero` |

**Dos valores y no tres.** El recorte solo necesita una frontera: qué se puede perder y qué
no. Una escala de tres —permanente, duradero, efímero— tendría dos valores con el mismo
comportamiento mientras el recorte sea binario en ese eje, y una escala cuyos valores no se
distinguen en nada es una etiqueta, no un control. Es el mismo argumento que sostuvo dos
valores en `estado_de_capitulo`.

Es **obligatorio**: un hecho sin durabilidad no se puede clasificar al recortar, y el
recorte tendría que adivinar. Adivinar en esa dirección es `MF-05`.

### C-2 · `EstadoDelMundo` **no** gana el mismo atributo

Preguntaste si la instantánea necesita la misma distinción, y la respuesta es **no, y el
motivo es más útil que la respuesta**.

`EstadoDelMundo` tiene seis campos, y **cada campo tiene ya una durabilidad propia por su
naturaleza**: no hay dos clases de cosa mezcladas dentro de un campo, salvo en uno.

| Campo | Durabilidad | ¿Necesita atributo? |
| --- | --- | --- |
| `entidades_vivas[]` | Duradera | No. Quién está vivo no es efímero |
| `ubicaciones` | **Efímera**, y cambia cada escena | No. Lo es entera |
| `posesiones` | Efímera | No. Lo es entera |
| `relaciones` | Duradera | No |
| `hechos_vigentes[]` | **Mezclada** | **Ya resuelto por `C-1`**: son `HechoCanonico` y llevan su durabilidad |
| `t` | — | No |

Así que la instantánea **sí se puede reconstruir por niveles**, como intuías, pero **por
campo y no por elemento**. La única lista heterogénea es `hechos_vigentes[]`, y su
heterogeneidad la resuelve el atributo de `C-1`.

### C-3 · El núcleo irreducible del bloque 4.º no son solo los hechos duraderos

Y aquí aparece lo que la tabla de arriba destapa, que `SPEC-12` no había visto.

Tu corrección fue que la reducción no puede llevarse el registro de conocimiento, porque
`INV-03` sin él es **imposible**. **Ese argumento no se aplica solo al registro.**
`ubicaciones` es efímera por naturaleza —parecería la primera candidata a irse— pero
`INV-02` es `bloqueante` y dice que *"todo personaje presente tiene `estado_vital = vivo` y
es accesible en `EstadoDelMundo(t)`"*. Sin ubicaciones, la accesibilidad no se puede
comprobar.

**La regla general, que es lo que había que escribir:**

> La forma reducida de un bloque **nunca puede llevarse lo que lee una invariante
> `bloqueante` de nivel escena**. Si lo hace, la puerta sigue en pie y ya no puede decidir.

Aplicada al bloque 4.º, su núcleo irreducible es:

| Qué | Lo lee | Por qué no se puede reducir |
| --- | --- | --- |
| `entidades_vivas[]` y `ubicaciones` | `INV-02` (`bloqueante`) | Sin ellas no se comprueba que un personaje presente esté vivo y sea accesible |
| Registro de conocimiento | `INV-03` (`bloqueante`) | Sin él la invariante no es peor: es imposible |

Lo que **sí** se puede reducir del 4.º: `posesiones`, `relaciones` y los hechos `efimero`.

## Qué queda explícitamente fuera

- **Quién asigna la durabilidad.** Si la declara el Escritor en el delta, la deduce una
  regla o la decide el Escaletador, es del plan y de `SPEC-11`.
- **Reclasificar hechos existentes.** No hay ninguno.
- **La durabilidad de otras clases.** `Presagio` ya tiene su ciclo con `estado_de_presagio`
  y `Deterioro` es monótono por `INV-14`. Ninguna la necesita.
- **Aplicar `SPEC-12`**, que espera a esta.

### Migración

`hecho_canonico` gana una columna obligatoria. **Ya no es gratis.** Desde `PLAN-01` A3 existe `backend/app/commons/db/` con migraciones versionadas y validación de secuencia, así que un atributo obligatorio nuevo necesita **su migración numerada en el mismo commit**. Las versiones no admiten huecos ni repeticiones: una publicada no se borra ni se renumera.

## Qué gobierna esto

`SPEC-12` `C-2`; `HechoCanonico` y `EstadoDelMundo` de `Docs/definitions.md`; `INV-02` e
`INV-03`; `MF-05`; la respuesta a `P-A` de `SPEC-01` §2.4; y de la rama `main`,
`hechos_permanentes` frente a `hechos_efimeros` en `src/contexto.py`.

## Preguntas que hay que responder al aprobar

| # | Pregunta | Propuesta |
| --- | --- | --- |
| 1 | ¿`permanente` y `efimero`, o hace falta un valor intermedio? | Dos. Mientras el recorte sea binario en este eje, un tercer valor no produciría comportamiento distinto |
| 2 | ¿`durabilidad` es obligatorio? | Sí. Un hecho sin durabilidad obliga al recorte a adivinar, y adivinar ahí es `MF-05` |
| 3 | `C-3` generaliza tu corrección a una regla: *"la forma reducida nunca se lleva lo que lee una `bloqueante` de escena"*. ¿Vive aquí o en `SPEC-12`? | En `SPEC-12`, que es la spec del recorte. Aquí se descubrió; allí es donde gobierna |
| 4 | ¿`INV-02` necesita decir explícitamente que lee `ubicaciones`? | Sí, y es lo que hace comprobable la regla de `C-3`: sin saber qué lee cada `bloqueante`, "no te lleves lo que lee" no se puede verificar. Puede ser una columna nueva en la tabla de invariantes |


# Qué se tocó al aplicarla

`Docs/definitions.md`: `HechoCanonico.durabilidad`, la enumeración `durabilidad_del_hecho`,
la columna «Qué lee» con las diecisiete filas rellenas, y dos notas de justificación.
`specs/SPEC - Formas reducidas del recorte.md`: la regla `C-3 bis` con su referencia
cruzada. `Docs/verification.md`: `VER-59` con su caso negativo.

## Lo que la spec no previó

**La columna «Qué lee» destapó un conflicto dentro de `SPEC-12`.** La forma reducida del
bloque 2.º dice *"solo las entidades presentes; se van las mencionadas"*, y `INV-02` lee
`Lugar.accesos_y_salidas`: **un lugar que está en el camino entre dos lugares no es una
entidad presente**, así que esa reducción viola la regla que esta spec acaba de hacer
verificable. Queda anotado en `SPEC-12` y hay que resolverlo antes de aplicarla.

**La regla suena más amplia de lo que ata.** De las cinco invariantes `bloqueante` de nivel
escena, solo dos leen bloques del contexto: `INV-02` y `INV-03`. `INV-01` lee un campo de la
propia `Escena`, `INV-04` compara la escena con su borrador e `INV-05` mira el delta y el
estado después de generar. Saberlo importa: el coste de la regla es mucho menor de lo que
parecía, y **se concentra justo donde está el conflicto**.
