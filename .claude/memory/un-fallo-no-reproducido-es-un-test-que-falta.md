---
name: un-fallo-no-reproducido-es-un-test-que-falta
description: "En My_novel_story, ante un fallo en ejecución el usuario exige reproducirlo con un test nuevo si los existentes no lo cazan, y que el doble de prueba tenga la misma forma que lo real."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: e52256e3-d959-4d0f-be48-c48f62092794
  modified: 2026-09-18T18:55:17.411Z
---

# Un fallo que los tests no cazan es un test que falta

El usuario de `My_novel_story` fijó esta regla al reportar un error del
servidor, y la formuló así: **«Diagnostica y arregla la causa. Si no la
reproduces con los tests que ya tienes, es que falta un test: añádelo.»**

No basta, por tanto, con arreglar el error y comprobar a mano que ya funciona.
El arreglo va acompañado de un test que **falle sin él**, y ese test hay que
escribirlo recorriendo el camino real, no uno parecido.

## El corolario, que el usuario considera lo más valioso

El caso concreto fue un `500` al ampliar una novela: en Windows, `claude`
instalado con npm es un `claude.CMD`, y `subprocess` sin shell no puede
arrancarlo por el nombre suelto porque `CreateProcess` no aplica `PATHEXT`.
Los tests que ya existían no lo cazaron porque **inyectaban un comando de
mentira construido con `sys.executable`**, que es un `.exe` de verdad: el
camino que fallaba —resolver un nombre contra el `PATH`— no lo recorría
ninguno.

Al pedir que eso se documentara, el usuario dijo que esa lección **«es más
útil que el hallazgo en sí»**. La regla general que se deduce, y que conviene
aplicar siempre en este proyecto:

> Un doble de prueba tiene que tener **la misma forma que lo real**, no solo la
> misma interfaz. Si en producción se lanza un script `.cmd` del `PATH`, el
> doble tiene que ser un script `.cmd` del `PATH`, no un ejecutable cómodo.
> Un doble más limpio que la realidad deja sin probar justo el tramo que rompe.

Esto vale más allá de los ejecutables: sirve para rutas con espacios o
acentos, archivos con BOM o finales de línea de Windows, y cualquier sitio
donde el entorno real sea más áspero que el de laboratorio.

## Cómo encaja con lo demás que pide

Es la misma exigencia que ya aplica al diagnóstico —reproducir y enseñar la
evidencia antes de arreglar— llevada al otro extremo del trabajo: dejar la
reproducción escrita en un test para que el fallo no pueda volver en silencio.
