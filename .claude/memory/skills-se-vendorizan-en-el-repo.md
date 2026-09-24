---
name: skills-se-vendorizan-en-el-repo
description: "En My_novel_story las skills se versionan con su contenido real en .agents/skills/, porque un lockfile no protege de que el upstream borre el contenido."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-21T17:02:13.193Z
---

# Las skills se vendorizan en el repositorio, no se confía en el lockfile

El usuario fijó esta regla después de que una skill que pidió instalar
(`sqlite-vec`) resultara haber sido **borrada por su autor** del repositorio
original, aunque el marketplace seguía anunciándola. Hubo que recuperarla del
historial de git.

Su razonamiento, literal: *"un lockfile fija una versión, pero si el upstream
borra el contenido no hay nada que reinstalar. La única garantía es que el
contenido esté en el repo."*

## Cómo queda montado

- **El contenido real vive en `.agents/skills/`** y se versiona con el
  proyecto. Es la carpeta donde `npx skills add` deja las cosas.
- **`.claude/skills/` está en `.gitignore`** porque solo contiene enlaces. El
  usuario señaló el motivo técnico: *git en Windows no guarda los symlinks como
  enlaces, los convierte en ficheros de texto con la ruta dentro*, que no
  sirven para nada.
- **`scripts/link-skills.mjs`** recrea esos enlaces con un comando después de
  clonar. En Windows usa `junction` en vez de `symlink`, porque el primero no
  exige permisos de administrador.
- `skills-lock.json` se conserva, pero como anotación de procedencia, no como
  garantía de poder reinstalar.

## La consecuencia para trabajar

Si en una sesión futura hay que instalar una skill en este proyecto, no basta
con ejecutar el instalador: hay que comprobar que el contenido real queda bajo
`.agents/skills/` y entra en el commit.

Una skill vendorizada de un upstream abandonado lleva además un
`PROCEDENCIA.md` con **fecha de revisión explícita**, porque —y esto también lo
señaló el usuario— una skill congelada que describe una librería viva envejece
en silencio: con el tiempo afirma cosas que ya no son ciertas y nada avisa. Esa
fecha se actualiza cada vez que se contrasta con la documentación oficial,
aunque el resultado sea que todo sigue bien.
