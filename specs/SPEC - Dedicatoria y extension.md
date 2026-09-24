---
id: SPEC-32
titulo: La dedicatoria es de la obra, y la extensión se pregunta
estado: aprobada
aprobada_por: "autor del proyecto, en sesión (decisión literal citada abajo)"
fecha_aprobacion: 2026-09-24
fecha: 2026-09-24
version: 1
---

# SPEC-32 — La dedicatoria es de la obra, y la extensión se pregunta

> **Qué cuenta como aprobación aquí**, igual que en `SPEC-24`: la decisión literal del
> autor, del 2026-09-24.
>
> Sobre la dedicatoria: *«copia la dedicatoria a Obra.dedicatoria al montar la novela. Es
> texto de la obra, no dato de la ficha, y la portada tiene que sobrevivir al borrado.»*
>
> Sobre la extensión: *«la extensión la recoge el entrevistador, y no es nuestra decisión
> saltárnosla — el enunciado lo dice. Que la ficha la guarde y que las opciones caigan dentro
> del rango obligatorio de 1.000 a 1.500 palabras. Que el entrevistador la pregunte y el
> código la respete.»*

## Qué problema resuelve

Dos huecos de `docs/cobertura-examen.md`, encontrados en la vuelta 2:

- **`EX-16`.** La dedicatoria vive en `FichaDeEntrevista` (`docs/definitions.md`), y
  `SPEC-25` `RF-21` borra la ficha al entregar. `SPEC-22` `RF-46` la quiere como atributo de
  `Obra`, pero nadie la copia allí: después de entregar, la portada se quedaría sin ella.
- **`EX-17`.** `EXAMEN.md` §1 dice que el entrevistador *«recoge… género, tono y
  extensión»*. `SPEC-25` `RF-03` decidió no preguntarla, y además el código contradice a su
  spec: `RF-03` dice que la ficha la registra, y `backend/app/commons/dominio/destinatario.py`
  dice que no se guarda.

## Qué tiene que ser verdad al terminar

### La dedicatoria

- **RF-01.** `Obra` tiene el atributo `dedicatoria`, definido primero en
  `docs/definitions.md`, con su migración en el mismo commit. Es el atributo que `SPEC-22`
  `RF-46` ya pedía.
- **RF-02.** **Al montar la obra desde el plan aprobado, la dedicatoria de la ficha se copia a
  `Obra.dedicatoria`**, antes de que `SPEC-25` `RF-21` borre la ficha.
- **RF-03.** El borrado de `RF-21` no cambia: sigue borrando la ficha entera. La dedicatoria
  sobrevive porque **es texto de la obra, no dato de la ficha**, igual que el resto del texto
  de la novela.
- **RF-04.** La portada —la web (`SPEC-22` `RF-46`) y el PDF (`SPEC-27` `RF-05`)— lee
  `Obra.dedicatoria`, nunca la ficha.
- **RF-05.** La dedicatoria no sube a Langfuse: es contenido de la novela, y queda dentro del
  límite de `SPEC-29`.

### La extensión

- **RF-06.** **El entrevistador pregunta la extensión.** `SPEC-25` `RF-03` queda sustituida
  en esto.
- **RF-07.** La pregunta ofrece **opciones cerradas, y todas caen dentro de 1.000 a 1.500
  palabras por capítulo**. Una opción fuera de ese rango es un error de validación de la
  configuración, no un aviso.
- **RF-08.** **La ficha guarda la extensión elegida**, validada con su schema: un valor fuera
  de las opciones es un error de validación.
- **RF-09.** **El código respeta la extensión elegida**: la longitud objetivo de cada
  capítulo, `INV-17`, el hook `validar_capitulo.py` y el prompt del Escritor usan la de la
  ficha, no una constante. El prompt la pide, porque el contrato la exige (Regla 4).

## Lo que es decisión nuestra y lo que es del enunciado

- **Preguntar la extensión es del enunciado** (`EXAMEN.md` §1).
- **El rango de 1.000 a 1.500 palabras por capítulo es decisión nuestra.** Estaba en la
  primera versión del enunciado y de ahí pasó a `SPEC-25` `RF-03` y `SPEC-26` `RF-01`; la
  versión actual de `EXAMEN.md` ya no lo dice. Se mantiene como obligatorio porque todo el
  pipeline —el plan, las puertas, el Editor— está calibrado para capítulos de ese tamaño.
- **Los diez capítulos no se preguntan.** El enunciado los exige para la novela de ejemplo, y
  la extensión que se pregunta es la del capítulo.

## Qué queda explícitamente fuera

- **Los valores de las opciones.** Son configuración, validada contra el rango de `RF-07`; el
  plan propone los iniciales.
- Editar la dedicatoria después de montar la obra, desde la lectura.
- Cambiar el número de capítulos.

## Lo que la gobierna

`EXAMEN.md` §1 y §2; `SPEC-22` `RF-46`; `SPEC-25` `RF-03` y `RF-21`; `SPEC-26` `RF-01`;
`SPEC-27` `RF-05`; `SPEC-29`; `INV-17`; `EX-16` y `EX-17`.
