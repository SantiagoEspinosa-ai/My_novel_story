---
name: indice-de-git-limpio-con-varias-sesiones
description: En My_novel_story hay varias sesiones commiteando sobre el mismo índice; hay que comprobar que está limpio antes de empezar y después de cualquier error.
metadata:
    pinned: false
---

# El índice de git con varias sesiones sobre el mismo repositorio

En `My_novel_story` trabajan a la vez varias sesiones de Claude Code sobre el
mismo directorio y, por tanto, sobre **el mismo índice de git**. El proyecto ya
prohíbe `git add -A` y `git commit -a` y pide añadir por ruta, y aun así se
pierde trabajo.

## Lo que no basta

`git add <ruta> && git commit -- <ruta>` **en un solo comando** parecía
suficiente y no lo es. El usuario lo formuló así:

> *"add && commit en un solo comando protege del comando que no se lanza, no
> del que se lanza y falla a mitad, y ahí el índice queda cargado toda la
> depuración."*

Pasó exactamente así: el `git add` se ejecutó, el `git commit` abortó por un
error de sintaxis —`-m` colocado después de `--`, que git lee como ruta— y el
fichero quedó preparado en el índice compartido durante toda la depuración del
error. Otra sesión commiteó en esa ventana y se llevó el fichero dentro de un
commit sobre otro asunto. El contenido sobrevivió; se perdió el mensaje que
explicaba el porqué.

## El remedio que el usuario pide

**Comprobar que el índice está limpio antes de empezar y después de cualquier
error.** Es decir, `git status` antes de preparar nada, y otra vez en cuanto un
comando de git falle, en lugar de pasar directamente a corregir la sintaxis.
Si quedó algo preparado, desprepararlo o completarlo antes de seguir.

Ayuda además pasar el mensaje por la entrada estándar con `git commit -F -` y
un heredoc: evita los errores de comillas y de orden de argumentos que son los
que abren la ventana.
