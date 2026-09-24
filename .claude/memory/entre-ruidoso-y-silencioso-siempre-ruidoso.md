---
name: entre-ruidoso-y-silencioso-siempre-ruidoso
description: "En My_novel_story, ante dos aproximaciones, se elige la que sobre-aproxima y falla de forma visible antes que la que se ajusta más y falla en silencio."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 39d2eac8-07ba-4c01-870b-412fdce2bc47
  modified: 2026-09-23T16:23:14.679Z
---

# Entre fallar ruidoso y fallar en silencio, siempre ruidoso

Al decidir de dónde saldría el conjunto de hechos del que depende una escena, le presenté al
usuario dos variantes: el conjunto **observado** —lo que el ensamblador de contexto metió de
verdad en el prompt, que sobre-aproxima y hace regenerar de más— y el **declarado** —lo que
el modelo dice que usó, que se ajusta mejor y puede omitir cosas—. El usuario eligió el
observado y generalizó el criterio:

> *«Tu argumento lo decide — sobre-aproxima y falla ruidoso frente a ajustarse y fallar en
> silencio. Este proyecto ha elegido el fallo ruidoso tres veces y las tres acertó.»*

Las tres veces que cita están escritas en el repositorio: `SPEC-10` C-2 —quien no se dejó
auditar no gana por defecto—, el `sin_veredicto` de `SPEC-18` C-3 —no es una violación y
tampoco pasa como éxito— y `RF-26` —si el contexto no cabe, el trabajo falla en vez de
generar—.

**Cómo usarlo.** Cuando haya que elegir entre dos aproximaciones y ninguna sea exacta, la
pregunta que decide no es cuál acierta más a menudo, sino **cómo se equivoca cada una**. Una
que se pasa de largo cuesta dinero o trabajo y se ve; una que se queda corta deja una
contradicción que nadie marca y que se descubre tarde o nunca. En este proyecto eso zanja la
elección, y conviene proponerlo ya resuelto en esa dirección en vez de presentar las dos
como equivalentes.

Esto no autoriza a decidir por el usuario: la elección se le presenta con el coste de cada
opción. Lo que sí hace es dar una recomendación con un criterio que él ya ha ratificado.
