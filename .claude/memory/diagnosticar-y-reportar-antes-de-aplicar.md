---
name: diagnosticar-y-reportar-antes-de-aplicar
description: "En My_novel_story el usuario pide diagnosticar y enseñar los hallazgos antes de aplicar un arreglo, y prohíbe sustituir en silencio un dato que no se ha podido obtener."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: e52256e3-d959-4d0f-be48-c48f62092794
  modified: 2026-09-18T16:19:23.979Z
---

# Diagnosticar y enseñar los hallazgos antes de aplicar nada

El usuario de `My_novel_story` ha pedido de forma repetida, y en el mismo
mensaje por tres vías distintas, que el trabajo se haga en dos tiempos:
primero averiguar y contar lo averiguado, y solo después tocar el código.

Las tres formas en que lo expresó, al encargar cambios sobre `panel.html`:

- Ante un fallo: «Diagnostica antes de tocar nada [...] dime cuál falla y con
  qué código. No lo arregles a ciegas». Es decir, reproducir el fallo y
  enseñar la evidencia concreta (la ruta que falla y su código de respuesta)
  antes de proponer o aplicar la corrección.
- Ante un dato externo: al pedir la paleta de color real de una web, «dime
  cuáles encontraste antes de aplicarlos».
- Y el límite explícito: «Si no los consigues, dímelo y uso una paleta de
  trabajo; **no los inventes en silencio**».

La regla que se deduce, y que conviene aplicar por defecto en este proyecto:
cuando un dato que hace falta no se puede obtener, no se sustituye por una
estimación propia sin avisar. O se dice que no se consiguió, o se usa un
sustituto **declarándolo** como tal. Un valor inventado que se presenta como
medido es peor que no tener el dato, porque después ya no se distingue de uno
real: es el mismo razonamiento que el propio harness aplica a su contador de
delegaciones, que se marca como «suelo» en vez de corregirse a ojo.

Esto encaja con la preferencia ya registrada de que los cambios de
comportamiento contractual se proponen y los decide el usuario.

## Dónde está el corte: pregunta nueva, no paso nuevo

En la sesión del 2026-09-22 el usuario afinó el ritmo, con palabras que lo
amplían a partir de ahora y no solo a esa tarea: **«Puedes encadenar sin
pararte lo que tenga una sola respuesta correcta. Párate siempre que aparezca
una pregunta nueva — eso es lo que quiero que sigas haciendo.»**

Es decir, lo que pide parada **no es cada paso**, sino cada **decisión**. Si un
lote de trabajo ya aprobado se compone de correcciones cuya respuesta está
determinada —por la jerarquía de documentos, por tres fuentes que coinciden o
por un vocabulario canónico—, se encadenan todas seguidas y se informa al
final. Pedir confirmación entre ellas es fricción, no prudencia.

Lo que sí corta es que aparezca algo que el usuario no ha decidido todavía:
una contradicción entre dos documentos sin regla que la resuelva, una carpeta
que nadie declaró, una convención que habría que inventar. Entonces se para,
se enseña la evidencia de los dos lados y se propone, sin aplicar.

El usuario elogió expresamente el caso en que, al intentar cerrar un hallazgo,
salió que la estructura contra la que había que resolverlo no existía en
ningún documento: pararse ahí y enseñarlo, en vez de elegir una estructura por
cuenta propia, fue lo que pidió que se siga haciendo.
