---
name: los-entregables-se-versionan-fuera-de-salida
description: "En My_novel_story, todo lo que sea entregable va a la raíz o a docs/ y se versiona; salida/ está en .gitignore y no conserva nada."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: c821224a-44f3-4e23-842c-755732370526
  modified: 2026-09-18T17:17:36.355Z
---

# Los entregables se versionan fuera de `salida/`

En el proyecto `My_novel_story`, la carpeta `salida/` está en `.gitignore` y el
`CLAUDE.md` del proyecto prohíbe expresamente hacer commit de ella. El usuario
dejó claro que eso tiene una consecuencia que no es obvia: **cualquier artefacto
que forme parte del entregable no puede vivir ahí dentro**, porque se perdería en
la siguiente limpieza y nunca llegaría a nadie más.

El caso concreto fue el panel de control de la generación (`panel.html`). El
usuario pidió explícitamente que estuviera «a la raíz o a `docs/`, fuera de
`salida/`, que está en `.gitignore`», y añadió que «es parte del entregable y
tiene que versionarse».

La regla general que se deduce, y que conviene aplicar sin que haga falta
pedirla otra vez: `salida/` es resultado desechable y reproducible de una
generación (manuscrito, biblia, estado, informes, intentos). Todo lo demás
—herramientas de visualización, informes de proyecto, documentación, scripts de
diagnóstico— va al repositorio, en la raíz o en su carpeta correspondiente, y
entra en el commit.

Corolario práctico para páginas o herramientas que lean `salida/`: tienen que
funcionar desde fuera de esa carpeta, con rutas relativas que la busquen al lado
o un nivel por encima, en vez de asumir que están dentro de ella.

## Un volcado de trabajo no es un entregable

La regla anterior no convierte en entregable a cualquier cosa que esté fuera de
`salida/`. Al copiar `salida/` entera a `salida-novela-1/` para salvar una
novela terminada antes de lanzar otra generación, pregunté si versionarla o
ignorarla, y el usuario respondió: **a `.gitignore`**, porque «es un volcado de
trabajo, no un entregable», y añadió el criterio que lo resuelve en general:
«cuando quiera enseñar una novela la copio a `docs/` con nombre propio».

Es decir, hay tres categorías y no dos:

- `salida/` y sus copias de seguridad (`salida-novela-1/` y similares): estado
  de trabajo, desechable, **ignorado por git**.
- Herramientas y documentación del proyecto: versionadas en la raíz o en su
  carpeta.
- Una novela concreta que se quiere enseñar: se copia a `docs/` **con un nombre
  propio elegido por el usuario**, y entonces sí se versiona.

Lo que decide la categoría es la intención de enseñarla, no la ubicación. Ante
una copia de respaldo, la opción por defecto es ignorarla y proponerlo, nunca
versionarla por iniciativa propia.
