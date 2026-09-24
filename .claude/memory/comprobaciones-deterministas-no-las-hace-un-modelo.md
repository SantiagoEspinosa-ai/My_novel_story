---
name: comprobaciones-deterministas-no-las-hace-un-modelo
description: "En el harness de novelas, lo que se puede comprobar con código no se delega a un validador; se inyecta como problema en la puntuación."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 65f7895f-2247-4fd0-9710-fe6b077485de
  modified: 2026-09-17T18:35:38.086Z
---

# Lo determinista lo comprueba el código, no un validador

En el proyecto `My_novel_story` (harness generador de novelas) el usuario
estableció un principio de diseño al encontrarse con que un capítulo de 944
palabras, por debajo del mínimo configurado de 1200, había sido aprobado por los
tres validadores mientras el harness se limitaba a imprimir un aviso por
pantalla.

Su corrección fue explícita y general, no limitada a ese capítulo: **"la longitud
es determinista y no necesita un modelo"**. Lo trató como un fallo del diseño.

De ahí se sigue la regla de trabajo:

- Cualquier criterio que se pueda evaluar con código (recuentos, rangos,
  presencia de campos obligatorios, formato) se evalúa en Python, no se delega a
  un subagente validador. Delegarlo cuesta una llamada, es no determinista y
  puede fallar, como falló aquí.
- El resultado de esa comprobación **no se imprime como aviso**: se inyecta en la
  lista de problemas del intento con exactamente la misma forma que los
  problemas de los validadores (gravedad, descripción, evidencia, corrección
  sugerida), de modo que puntúe, bloquee la aprobación igual que un `FALLO` y
  viaje solo hasta la ventana del escritor en la reescritura.
- El motivo de esto último es que un aviso por pantalla lo lee la sesión
  orquestadora, no el escritor. El usuario quiere explícitamente **no tener que
  añadir texto suelto a la ventana del escritor** para comunicarle una pega: el
  canal para eso es la lista de problemas acumulados que ya existe.

La implementación concreta de este caso es `puntuacion.veredicto_longitud`, que
devuelve un veredicto del pseudo-validador `longitud`, y su llamada desde
`cmd_registrar_intento`. Si en el futuro aparece otro criterio comprobable por
código, el patrón a seguir es ese.
