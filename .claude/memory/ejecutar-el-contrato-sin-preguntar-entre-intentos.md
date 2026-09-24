---
name: ejecutar-el-contrato-sin-preguntar-entre-intentos
description: "Al generar una novela, hay que seguir EJECUCION.md hasta el final sin pedir confirmación entre intentos ni entre capítulos."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 65f7895f-2247-4fd0-9710-fe6b077485de
  modified: 2026-09-17T20:29:28.308Z
---

# Generar la novela entera sin consultar entre intentos

En el proyecto `My_novel_story`, cuando el usuario pide generar una novela, la
expectativa por defecto es que la sesión **ejecute el contrato de `EJECUCION.md`
hasta el final sin detenerse a preguntar**. El usuario lo formuló así: «a partir
de ahora no me preguntes entre intentos: sigue el contrato hasta el final».

En concreto, eso significa aplicar sin consultar el bucle que ya describe el
contrato:

- si un intento no pasa la validación, reescribir;
- al agotar los intentos de un modelo, subir al siguiente escalón de la escalera;
- si se agota la escalera entera, aceptar la mejor versión por puntuación,
  marcarla como `ACEPTADO_POR_PUNTUACION` y pasar al capítulo siguiente;
- avisar solo al terminar la novela entera, con el ensamblado hecho.

El motivo es que el contrato ya prevé todos esos casos, incluida la regla 1
(ningún capítulo detiene la generación). Preguntar entre intentos no añade
información que el usuario no pueda leer después en
`salida/informe-validacion.md`, y en cambio interrumpe una ejecución que puede
durar decenas de delegaciones.

El usuario puede pedir puntos de parada concretos para una ejecución concreta
(por ejemplo, «si un capítulo llega al tercer intento, para y dime qué dicen los
validadores»). Eso es una excepción explícita y temporal para esa ejecución; en
cuanto la levanta, o si no la pide, vuelve a regir el comportamiento por defecto
de no interrumpir.
