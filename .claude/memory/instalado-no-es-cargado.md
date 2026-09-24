---
name: instalado-no-es-cargado
description: "En My_novel_story, una skill (o cualquier herramienta) solo cuenta como instalada si la herramienta que debe usarla la carga de verdad; estar en el repo no basta."
metadata:
  node_type: memory
  pinned: false
  originSessionId: 5b65bfd1-7e60-4579-98c4-163aa58c9e24
  modified: 2026-09-24T15:35:22.675Z
---

# Instalado no es cargado

Las ocho skills del proyecto llevaban días en `.agents/skills/`, versionadas, con
su contenido real y su README, y los documentos afirmaban que "Claude Code lee
esa carpeta directamente". Era falso: Claude Code solo carga skills de
`.claude/skills/`, y esa carpeta estaba en `.gitignore`. Ninguna sesión las
cargaba. Al descubrirlo, el usuario lo zanjó con esta frase:

> *"Ocho skills que nadie carga no son ocho skills."*

En la práctica:

1. Al instalar o mover una skill, un hook, un MCP o un subagente, se comprueba
   que **la herramienta que tiene que usarlo lo carga**: que aparece en la lista
   de skills de una sesión, que el hook se dispara, que el MCP responde. Que el
   fichero exista en el repositorio no demuestra nada.
2. Una afirmación del tipo "X lee esta carpeta" en un documento se trata como un
   dato que hay que comprobar, no como contexto de fondo.
3. Donde el enlace no es fiable (este repo tiene `core.symlinks=false`), se
   copia desde una única fuente con un guion que falla si las copias divergen:
   `myFactory/sincronizar_skills.py --comprobar`.
