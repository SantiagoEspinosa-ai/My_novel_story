---
name: la-configuracion-fuera-del-codigo-y-con-huella
description: "En My_novel_story la forma de la obra y la del sistema viven en ficheros validados fuera del código, y cada artefacto registra con qué código, qué brief y qué máquina se generó."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-23T17:33:23.870Z
---

# La configuración vive fuera del código, y cada artefacto dice con qué se hizo

El usuario lo pidió con estas palabras: *"La configuración fuera del guion, en
dos ficheros separados: el del sistema —modelos por agente, topes, presupuesto,
ruta de la base— y el brief de la obra —premisa, género, tono, número de
capítulos, escenas por capítulo, palabras por escena—. Los dos validados con
schema. Quiero cambiar la forma de una novela sin tocar código."*

## Por qué son dos ficheros y no uno

Cambian por motivos distintos. El del sistema cambia cuando cambia la máquina;
el brief cuando cambia la novela. Juntarlos obligaría a tocar la novela para
cambiar de modelo, y a revisar la máquina para escribir otra historia.

## La razón de fondo, que el usuario formuló y conviene no olvidar

> *"Que la forma de la obra viviera dentro del guion es lo que hizo que nadie
> notara durante diez capítulos que estábamos modelando diez obras. Un fichero
> de configuración lo habría hecho visible el primer día."*

No es una cuestión de comodidad: **una forma que no se puede leer en un sitio no
se puede discutir, y lo que no se discute nadie lo corrige**. Las consecuencias
de aquel modelado se descubrieron de una en una durante días y ninguna apuntaba
a la causa.

## Las tres huellas

Todo artefacto generado registra con qué se hizo, y son tres ejes porque faltando
cualquiera una comparación entre dos obras atribuye mal la diferencia:

- **el commit** — con qué código se escribieron las filas;
- **la huella del brief** — qué novela se pidió;
- **la huella del sistema** — con qué modelos y topes.

Sin la tercera, dos tandas de la misma novela con el mismo código dan números
distintos al cambiar de modelo y **se le atribuye a la obra lo que hizo la
máquina**.

Las tres siguen las mismas reglas del proyecto: no se pisan (se guarda la de
creación), lo indeterminable se dice en vez de rellenarse con un valor
plausible, y una ausencia de marca no cuenta como conformidad.

## Cómo se evita que la configuración y el código diverjan

El brief dice **cuántas** piezas tiene la obra y el plan concreto trae **cuáles**
son. Si los dos pueden decir cosas distintas, la forma vuelve a estar en dos
sitios y uno acabará mintiendo. Por eso se comprueba que cuadren **al arrancar**
y no al generar: descubrirlo en la escena treinta y siete cuesta una tanda
entera, y el fallo que sale ahí no menciona el fichero de configuración.
