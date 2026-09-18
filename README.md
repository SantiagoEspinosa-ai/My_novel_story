# My_novel_story

Harness generador de novelas de romance, drama y terror, con validación
automática. El orquestador es **Claude Code**: un arquitecto diseña la
estructura, un escritor redacta cada capítulo, tres validadores en paralelo lo
auditan antes de aprobarlo y un resumidor comprime cada capítulo aprobado para
los siguientes.

- **Cómo se ejecuta:** `EJECUCION.md` (el contrato de ejecución).
- **Por qué es así:** `SPEC-generador-novelas-v3.md` y `DECISIONES.md`.
- **Qué se puede ajustar:** `config.json`.

---

## El panel de control (`panel.html`)

`panel.html` es una página de una sola pieza —sin dependencias, sin compilar—
que lee lo que el harness dejó en `salida/` y lo enseña en cinco vistas:

| Vista | Qué contesta |
|---|---|
| 1. Recorrido | Cuántos intentos costó cada capítulo, qué dijo cada validador y qué problemas siguen en el texto entregado |
| 2. Arquitectura | El flujo del harness, con el número real de reintentos de esta generación |
| 3. Estructura | Qué archivo hace qué en el repositorio |
| 4. Tokens | En qué se gastó: por rol, por modelo, por capítulo, y qué parte acabó en el manuscrito |
| 5. Libro | El manuscrito, para leerlo |

El panel vive en la raíz y se versiona. **No va en `salida/`**, que está en
`.gitignore`: ahí dentro se perdería con cada limpieza y no llegaría a nadie.

### Las dos formas de abrirlo

Hay dos, y la página detecta sola en cuál está. Solo enseña los controles del
modo en el que se encuentra, nunca los dos a la vez.

**1. Servida por un servidor local (recomendada).** Así la página lee `salida/`
ella sola, sin que haya que darle nada. Desde la raíz del proyecto:

```powershell
python -m http.server 8765 --bind 127.0.0.1
```

y abre <http://127.0.0.1:8765/panel.html>. El botón «Volver a leer salida/»
recarga los datos sin recargar la página, que es lo cómodo mientras una
generación está en marcha.

Si algún archivo no está donde debería, **lo dice en pantalla con la ruta
exacta y el código HTTP**. Una vista vacía porque no hay novela y una vista
vacía porque el servidor devolvió 404 se ven igual, y son problemas distintos:
por eso el panel nunca se calla.

Para pararlo, `Ctrl+C` en esa terminal.

**2. Abriendo el archivo directamente (`file://`).** Doble clic en
`panel.html`. Por seguridad, el navegador prohíbe que una página abierta así
lea archivos del disco por su cuenta, de modo que aparece un selector: arrastra
la carpeta `salida/` entera sobre el recuadro, o elige los archivos a mano.
Nada sale del navegador.

Es la vía para mirar una generación en una máquina donde no apetece levantar un
servidor, o para enviarle a alguien el HTML y su `salida/` por separado.

### Dónde puede estar el panel

La página busca `salida/` primero a su lado y después un nivel más arriba, así
que funciona igual en la raíz del proyecto o dentro de una carpeta `docs/`.

---

## Comandos

- Tests: `python -m pytest`
- Estado de una generación: `python -m src.orquestacion estado`
- El resto, en `EJECUCION.md` sección 2.
