---
name: avanzar-parametrizable-en-vez-de-bloquear
description: En My_novel_story, una decisión que se puede dejar parametrizable no justifica parar; se avanza y se cuenta al final.
metadata:
    pinned: false
---

# Avanzar dejándolo parametrizable en vez de bloquear con preguntas

El usuario de `My_novel_story` interrumpió una tanda de preguntas con esta
instrucción, que generaliza más allá de la tarea en curso:

> «Párame solo en una cosa […]. Si te topas con que hace falta elegir antes de
> poder seguir, dime las opciones y para; si puedes avanzar dejándolo
> parametrizable, avanza y me lo cuentas al final.»

La regla que se deriva tiene tres partes:

1. **Antes de preguntar, hay que comprobar si la decisión se puede diferir.**
   Si el diseño admite dejar el punto abierto —una columna con vocabulario
   ampliable, un umbral en configuración, una estrategia enchufable— eso es lo
   que se hace, y la elección se le presenta al final con el trabajo ya hecho.
   Preguntar algo que el propio diseño podía absorber le cuesta al usuario un
   turno a cambio de nada.
2. **Solo se para en la decisión que el usuario ha señalado explícitamente**
   como suya, o en la que de verdad impide escribir la siguiente línea. Las
   demás (esquema, índices, dónde engancha el código) las decide quien
   implementa.
3. **Lo diferido se cuenta al terminar**, no se deja en silencio. La respuesta
   final dice qué quedó parametrizable, qué valor lleva por defecto y qué
   cambiaría al elegir otro.

Encaja con dos preferencias que este usuario ya había expresado: ejecutar el
contrato de generación sin pedir confirmación entre intentos ni entre
capítulos, y no interrumpir un trabajo largo para confirmar pasos intermedios.
No contradice su regla de diagnosticar y enseñar los hallazgos antes de aplicar
un arreglo: eso es sobre arreglos en código existente que ya falla, esto es
sobre elecciones de diseño en trabajo nuevo.
