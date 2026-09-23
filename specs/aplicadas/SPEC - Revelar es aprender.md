---
id: SPEC-16
titulo: Revelar es aprender, y actuar es otro campo
estado: aplicada
aprobada_por: "@Santiago Espinosa Domínguez"
fecha_aprobacion: 2026-09-23
fecha_aplicacion: 2026-09-23
commit_de_aplicacion: 2ec463d
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-23
version: 1
---

# SPEC-16 — Revelar es aprender

## Qué problema resuelve

`SPEC-15` arregló un punto muerto y destapó el suyo, `F-31`: **la puerta de `INV-03`
bloquea la primera revelación de la obra, sea cual sea.**

> Trata toda entrada de `delta.revelaciones` como *actuar sabiendo ya*, y exige que el hecho
> conste en el `RegistroDeConocimiento` **antes** de la escena. Pero el registro solo se
> escribe **desde esas mismas revelaciones**, en la consolidación, que ocurre **después** de
> la puerta. **Nadie puede llegar a saber nada nunca.**

Las dos lecturas estaban escritas en el repositorio y se contradicen. Una dice que la
revelación es el momento de **aprender**; la otra la trata como **actuar**. Y ninguna de las
dos está escrita donde tendría que estar: **el prompt le da al modelo la forma de
`revelaciones` y no su significado**, así que el modelo llevaba todo este tiempo
deduciéndolo. Dedujo lo correcto mientras el código suponía otra cosa.

**Los dos fallos se tapaban mutuamente.** Sin hechos declarados no había revelaciones, y sin
revelaciones `INV-03` nunca llegaba a mirar. Por eso la generación de seis escenas terminó
con cero bloqueos: no era que la obra estuviera limpia, era que la puerta no miraba (`F-30`).

---

## C-1 · Revelar es aprender, e `INV-03` deja de mirar las revelaciones

Una entrada de `delta.revelaciones` significa: **el sujeto pasa a conocer ese hecho a partir
de esta escena**. Es lo que ya hace la consolidación y lo que el modelo venía entendiendo.

`INV-03` **deja de comprobar las revelaciones**. Aprender no puede exigir saber de antes, y
mientras siga mirándolas el punto muerto sigue en pie.

## C-2 · El delta gana `acciones`, y es lo que `INV-03` comprueba

`DeltaDeEscena` gana `acciones[]`, con la forma `{personaje, hecho}`: **este personaje obró
en esta escena sirviéndose de este hecho.**

`INV-03` conserva su enunciado —*ningún personaje actúa sobre un hecho que no conoce en
`t`*— y pasa a compararlo contra `acciones`, leyendo el `RegistroDeConocimiento` como
siempre. Su severidad no cambia: sigue `bloqueante`.

**Esta cláusula es la que sostiene a la anterior.** Sin `acciones`, `C-1` deja a `INV-03`
sin nada que comprobar, y una invariante sin objeto no es una invariante laxa: es una regla
declarada y no verificada, que es exactamente lo que este proyecto rechaza. Si `C-2` no se
aprueba, la decisión correcta no es dejar `INV-03` como está, es **retirarla**.

**Y es lo que conserva `F-24`**, la única detección real que el sistema ha producido: un
personaje que obra sirviéndose de algo que solo sabía su hermana sigue siendo una violación,
solo que ahora la declara el campo que significa obrar.

## C-3 · El contrato dice qué significan sus campos, no solo su forma

El prompt pasa a decir **qué significa cada campo del delta**, no solo cómo se escribe.

Y queda como principio, porque no es el arreglo de este caso:

> **Regla 5 — Un contrato que no dice qué significan sus campos no es un contrato.**
>
> Fija una forma y deja el significado a la intuición de quien responde. Cuando las dos
> intuiciones coinciden, funciona y nadie se entera; cuando divergen, **las dos partes
> cumplen el contrato y el sistema está roto**, sin error, sin excepción y sin nada que
> falle. Aquí el modelo dedujo lo correcto mientras el código suponía otra cosa, y el fallo
> no apareció hasta que el otro punto muerto dejó de taparlo.

Es la tercera mitad de la **Regla 4**, que ya exigía dos: el prompt lleva los identificadores
disponibles y el contrato comprueba que la respuesta los use. Faltaba que el prompt dijera
**qué se está pidiendo con cada uno**.

## C-4 · Establecer un hecho es su primera revelación

`HechoCanonico.escena_de_establecimiento` se rellena con la **primera** escena que revela ese
hecho. No hace falta un tercer campo: lo normal es que coincidan —Marta encuentra la llave,
el texto lo establece y ella lo aprende en el mismo momento—, y separarlos pediría declarar
por partida doble algo que casi siempre es lo mismo.

Un hecho que el plan no declaró puede establecerse igual y **se marca**, que es lo que ya
decidió `SPEC-15` P-4.

## C-5 · No hay invariante nueva para *"aprender antes de establecer"*

Con `C-4`, establecer **es** la primera revelación, así que el caso no puede darse. Una
invariante que no puede fallar no verifica nada: solo añade una línea verde que se lee como
cobertura. Es la **Regla 2** por la puerta de al lado.

## Decisión que esto abre y no cierra

**Conocimiento adquirido sin fuente que lo explique.**

Con `C-1`, lo que hizo Ana en `F-24` deja de violar `INV-03`. Pero **sigue siendo algo**: se
enteró de un hecho que solo sabía su hermana, sin que el texto explicara cómo. Eso no es
actuar con conocimiento indebido — es **adquirir conocimiento sin fuente**, y en terror esa
es la diferencia entre un misterio y un agujero de guion.

`RegistroDeConocimiento.fuente` existe desde `SPEC-03` precisamente para esto, y hoy no lo
comprueba nadie. Queda como **decisión abierta**: una invariante que exija que toda
revelación deje al personaje sabiendo algo con una fuente que lo explique.

**No se abre en esta spec**, pero queda escrita. Si no, `F-24` pasaría de detección real a
falso positivo, y no lo era.

## Qué queda explícitamente fuera

- **La invariante de la fuente.** Queda como decisión abierta, arriba.
- **Reabrir el enunciado o la severidad de `INV-03`.** Ninguno cambia: cambia contra qué
  campo del delta se comprueba.
- **Que el Escaletador declare las `acciones` por adelantado.** Son del delta, es decir, de
  lo que el texto hizo. Lo que el plan declara son los hechos (`SPEC-15`).
- **Los identificadores desconocidos en `acciones`.** Se rechazan en el contrato como ya se
  rechazan los de `revelaciones` (`SPEC-03`, Regla 4). No es materia nueva.

### Migración

**No hace falta.** `acciones` es un campo del delta, y el delta no se persiste en ninguna
tabla: se aplica y lo que queda es `escena_consolidada`. Ninguna columna cambia y ningún
atributo obligatorio se altera, así que la regla de `CLAUDE.md` —*un cambio en
`Docs/definitions.md` que altere un atributo obligatorio necesita su migración en el mismo
commit*— no se dispara aquí.

## Qué gobierna esto

`DeltaDeEscena`, `RegistroDeConocimiento`, `HechoCanonico.escena_de_establecimiento` e
`INV-03` de `Docs/definitions.md`; `F-24`, `F-29`, `F-30` y `F-31` de
`Docs/verification.md`; `VER-64` y `VER-37`, que siguen sin dato hasta que esto se aplique;
y las **Reglas 2 y 4**, de las que `C-5` y `C-3` salen respectivamente.

## Preguntas respondidas al aprobar

| # | Pregunta | Respuesta |
| --- | --- | --- |
| 1 | ¿`INV-03` deja de mirar `revelaciones` por completo? | **Sí.** Revelar es aprender, y aprender no puede exigir saber de antes |
| 2 | ¿El delta gana un canal para *actuar sabiendo*? | **Sí: `acciones[]`.** Es la que decide: sin ella, la 1 deja a `INV-03` sin objeto y habría que retirarla |
| 3 | ¿El prompt dice qué significa cada campo, no solo su forma? | **Sí, y queda como principio** (Regla 5), no como arreglo de este caso |
| 4 | ¿Quién establece un hecho: el plan o la primera revelación? | **La primera revelación.** Normalmente coinciden, y separarlos pediría un tercer campo para casi ningún caso |
| 5 | ¿Invariante nueva para *"aprender antes de establecer"*? | **No.** Con la 4 el caso no puede darse, y una regla que no puede fallar no verifica nada |

Las cinco se respondieron el 2026-09-23. La 2 se confirmó como la que decide, y la 3 se
elevó a principio en la misma respuesta: *"un contrato que no dice qué significan sus campos
no es un contrato"*. En esa misma respuesta quedó abierta la decisión sobre la fuente del
conocimiento, para que `F-24` no se degrade a falso positivo al corregir lo demás.
