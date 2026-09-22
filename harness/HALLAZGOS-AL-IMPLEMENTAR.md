# Lo que `Docs/verification.md` no aguantó al llevarlo a código

Lista de lo que se rompió al intentar implementar los validadores: criterios de
salida ambiguos, referencias que no se pueden obtener y comprobaciones que no se
pueden escribir como están redactadas.

**No se ha corregido nada de `Docs/`.** Esto es la anotación; la decisión es de
quien mantiene el documento.

Fecha: 2026-09-22 · Al implementar `VER-38`, `VER-28` y `VER-23`.

---

## F-1 · `VER-38` no puede comprobar la severidad, que es un tercio de su enunciado

Dice: *"La severidad, el nivel y el tipo declarados en el código para cada
invariante coinciden con la tabla"*. Pero **la severidad solo existe en
`Docs/definitions.md`**: ni `Docs/architecture.md` ni la skill
`harness-invariantes` la declaran por invariante. No hay segunda fuente contra la
que contrastarla.

Lo implementado: nivel y tipo se cruzan entre las tres fuentes; la severidad solo
se comprueba contra su propio vocabulario controlado, que es coherencia interna,
no cruzada.

**Decisión pendiente:** o el criterio de salida reconoce que la severidad no es
cruzable hasta que haya código, o alguna otra fuente empieza a declararla.

## F-2 · El "dónde vive" de `VER-38` apunta a una carpeta que no existe en la estructura acordada

`Docs/verification.md` dice `harness/esquema/` para `VER-01` y `VER-38`. La
estructura del harness es `harness/{invariantes,documentos,fixtures}`. Está
implementado en `harness/documentos/`, que es donde encaja por lo que hace.

**Decisión pendiente:** actualizar la columna, o crear `harness/esquema/`.

## F-3 · `VER-01` no se puede implementar hoy, ni siquiera a medias

Compara los esquemas Pydantic con las fichas de clase. Sin `backend/` no hay
esquemas, así que **falta la mitad de la comparación**. Lo único que se podría
escribir hoy —comprobar que `definitions.md` es coherente consigo mismo— es otra
comprobación distinta y no está en el plan.

## F-4 · No hay ninguna fila `VER` para "las rutas citadas en los documentos existen"

Es el defecto que **de verdad ocurrió**: setenta y tres referencias rotas tras
renombrar `defintions` → `definitions.md` y `SRS.md` → `SPEC - Backend.md`. El
plan de verificación no lo cubre con ninguna fila.

Es el hueco más llamativo de los encontrados: hay validador para cosas que nunca
han fallado y no lo hay para la única que ya falló dos veces.

## F-5 · Tampoco hay fila para "los literales citados en los documentos son los de la tabla"

`VER-02` es sobre los `Enum` del código. Nada cubre que un documento cite
`EnVerificacion` donde la enumeración dice `en_verificacion`, que es lo que pasó
con el diagrama de ciclo de vida, ni que invente una relación como
`conocido_por`.

Se implementó como **precondición dentro de `VER-28`** —sin literales correctos,
explorar la máquina no demuestra nada—, pero es una comprobación sin fila propia
y por tanto sin dueño.

## F-6 · `VER-28` no dice de qué documento sale la máquina de estados

Su criterio es *"exploración exhaustiva de la máquina de estados"*. La máquina
está en dos sitios: la tabla de transiciones de `Docs/architecture.md` y el
diagrama de `Docs/domain-knowledge.md`.

Se eligió la tabla, porque el diagrama es una vista declarada y parsear Mermaid
es frágil. **Pero la elección la tomó el implementador, no el documento.**

## F-7 · `VER-23` no dice contra qué compara, y el criterio elegido tiene un agujero

*"El conjunto de identificadores solo crece"* — ¿respecto a qué? ¿Al commit
anterior, al último tag, a la rama base?

Se eligió `HEAD~1`. **Tiene un agujero conocido:** si alguien borra un
identificador en un commit y hace otro commit encima, la comparación
`HEAD`/`HEAD~1` ya no lo ve. Para cerrarlo haría falta comparar contra la rama
base o contra un inventario versionado de identificadores.

## F-8 · `VER-23` se salta en vez de fallar cuando no hay historial

Hubo que decidir qué pasa si el documento no existía en el commit anterior. Se
optó por `skip` con motivo, que es honesto, pero **significa que el validador
puede aparecer en verde sin haber comprobado nada**. El documento no dice qué
hacer en ese caso.

## F-9 · No se pudo escribir la comprobación de nivel del agente, y hace falta

`Docs/architecture.md` sigue asignando invariantes de nivel obra —`INV-06`,
`INV-09`, `INV-12`, `INV-13`, `INV-16`— al **Verificador de reglas**, que opera
escena a escena. Es el hallazgo que ya estaba abierto.

**No se implementó el validador que lo cazaría**, porque `architecture.md` no
declara el nivel de cada agente: habría que decidir que el Verificador de reglas
es de nivel escena, y eso es una decisión de dominio. Se paró aquí, como estaba
acordado.

Sí se implementó lo que no exige decidir nada: que **toda invariante tenga al
menos un agente que la ejecute**. Pasa.

## F-10 · Los datos normativos en prosa se rompen al editar

La skill `harness-invariantes` afirma *"doce son de regla, cuatro son de juez"*.
Es parseable —hay que convertir palabras a números— pero **cualquier reescritura
del párrafo rompe el parser**. Un dato que se compara debería vivir en una tabla,
no en una frase.

## F-11 · El escape `\_` de las tablas markdown es una trampa silenciosa

En una tabla, `juez\_llm` y en el texto `juez_llm` son la misma cosa y **cadenas
distintas**. Todo parser tiene que normalizarlo antes de comparar. No es un
defecto del documento, pero es el fallo de comparación más fácil de cometer y
conviene que esté escrito en alguna parte.
