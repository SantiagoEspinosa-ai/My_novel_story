# Repositorios gigantes — inventario e informe por categoría

2026-09-24 · Fases 1 a 3 del método de acordeón. La contracción (fase 4) está en
`RECOMENDACION.md`, en esta misma carpeta.

**Cómo leer las cifras.**

- **Estrellas, último push, licencia y archivado:** se leyeron de la API de GitHub el
  2026-09-24.
- **Ahorro de tokens:** ninguna cifra de ahorro está medida por nosotros. Donde aparece una,
  es **la que declara el autor**, y en general sale de su propio benchmark.
- **"Supuesto":** no se pudo comprobar.
- **Sesgo de las cifras declaradas:** todas sesgan hacia arriba, porque el autor elige el
  caso que le favorece. Solo valen para ordenar qué pilotar, no para decidir.

**Criterio de fondo, propio del caso.** El código es de clientes. Por eso, antes que el ahorro
de tokens, mandan dos preguntas:

1. ¿Sale código de la máquina?
2. ¿La licencia permite el uso en empresa?

## Inventario comprobado

| Herramienta | Tipo | Estrellas / último push | Licencia | ¿Sale código? |
| --- | --- | --- | --- | --- |
| Graphify | skill + CLI + MCP | 121.120 / 2026-09-23 | Apache-2.0 | Código no; documentación y PDF sí, al LLM |
| RepoWise | MCP + CLI + plugin | 7.003 / 2026-09-24 | AGPL-3.0 o comercial | No en el núcleo; sí si se activa la wiki con LLM |
| Serena | MCP (LSP) | 29.771 / 2026-09-24 | GPL-3.0 (SolidLSP, MIT) | No |
| codebase-memory-mcp | MCP | 44.806 / 2026-09-24 | MIT | Supuesto que no (README sin leer) |
| GitNexus | MCP + CLI | 47.560 / 2026-09-24 | **PolyForm Noncommercial** | Supuesto que no |
| code-graph-rag | MCP + CLI | 5.176 / 2026-09-24 | MIT | Depende del LLM que se configure |
| claude-context | MCP (embeddings) | 12.566 / 2026-07-14 | MIT | Sí, salvo con Milvus local |
| Octocode | MCP | 943 / 2026-09-18 | MIT | Local más la API de GitHub |
| ast-grep y ast-grep-mcp | CLI / MCP | 16.021 / 2026-09-24 y 467 / 2026-09-21 | MIT | No |
| mcp-server-tree-sitter | MCP | 309 / 2026-05-21 | MIT | No. **Archivado** |
| mcp-language-server | MCP (LSP) | 1.599 / 2026-03-01 | BSD-3 | No. 7 meses sin push |
| universal-ctags | CLI | 7.290 / 2026-09-22 | GPL-2.0 | No |
| zoekt | búsqueda por trigramas | 1.925 / 2026-09-23 | Apache-2.0 | No |
| Sourcegraph MCP, Greptile, DeepWiki | remotos | sin medir | comerciales | **Sí** (DeepWiki, solo repos públicos) |
| Aider repo-map | estrategia | 49.151 / 2026-05-22 | Apache-2.0 | Al LLM |
| repomix, code2prompt, gitingest | empaquetadores | 28.480 / 7.695 / 15.613 | MIT | No (la web de gitingest, sí) |
| RTK | CLI + hook | 81.639 / 2026-09-24 | Apache-2.0 | No |
| context7 | MCP | 62.392 / 2026-09-24 | MIT | Solo consultas: es documentación de librerías, otro caso |

Lo nativo de Claude Code (subagentes, `CLAUDE.md` por directorio, skills que se cargan por
partes, hooks, `/compact`) se da por **supuesto**: no se leyó su documentación en esta ronda,
aunque los subagentes, los hooks y el `@import` se usan ya en este repositorio.

## Informe por categoría

### 1. Grafo del código con contexto para el agente

**Qué hay.** Graphify, RepoWise, codebase-memory-mcp, GitNexus, code-graph-rag y Octocode.

**Qué ahorro da.**

- Sustituyen la cadena grep → leer fichero por una consulta que devuelve el trozo del grafo
  que hace falta.
- RepoWise declara 393 tokens frente a 13.984 en una recuperación de `get_context`, y el
  propio autor aclara que no es el ahorro total. Declara también un 31,6 % menos de salida
  del agente sobre django.
- Graphify **no declara** ninguna cifra de ahorro.

**Esfuerzo.**

- **Medio.** Se instala en una tarde, pero en millones de líneas el índice inicial tarda y
  hay que decidir qué se indexa.
- Graphify y RepoWise instalan también hooks y secciones en `CLAUDE.md`, que cambian cómo se
  comporta el agente.

**Riesgos.**

- Graphify:
  - está en versión 0.x;
  - `--strict` bloquea la lectura directa de ficheros;
  - registra cada consulta en `~/.cache/graphify-queries.log`;
  - empuja una plataforma de pago.
- RepoWise:
  - es AGPL;
  - `repowise init` escribe en `~/.claude/settings.json`, que es **global** y no del proyecto.
- GitNexus prohíbe el uso comercial.
- **El índice envejece.** Un grafo desfasado da respuestas seguras y falsas.

**Prioridad.** **Alta** para Graphify y RepoWise, pero en piloto. GitNexus **queda fuera**
por la licencia. Las demás, **baja**.

### 2. Navegación estructural por símbolos

**Qué hay.** Serena, ast-grep y su MCP, universal-ctags, mcp-language-server y
mcp-server-tree-sitter.

**Qué ahorro da.**

- Lee un símbolo en vez de un fichero entero, y busca por estructura en vez de por texto:
  menos falsos positivos que un grep.
- Sin cifra declarada que se haya leído.

**Esfuerzo.**

- **Bajo** para ast-grep y ctags: un binario.
- **Medio** para Serena: necesita el servidor de lenguaje de cada lenguaje del cliente, y en
  un monorepo grande ese servidor puede tardar en arrancar.

**Riesgos.**

- Serena es GPL-3: vale como herramienta interna y no contamina el código del cliente, pero
  conviene que lo vea legal.
- tree-sitter MCP está archivado.
- mcp-language-server está parado.

**Prioridad.** **Alta** para ast-grep y Serena, **media** para ctags; las otras dos,
**descartar**.

### 3. Indexación y búsqueda

**Qué hay.** zoekt, claude-context, Sourcegraph MCP y Greptile.

**Qué ahorro da.**

- zoekt da búsqueda instantánea en millones de líneas, donde ripgrep empieza a tardar. Ahorra
  tiempo más que tokens.
- claude-context devuelve fragmentos por similitud.

**Esfuerzo.** Alto: zoekt es un servidor que se autoaloja, y claude-context necesita
embeddings y una base vectorial.

**Riesgos.**

- Greptile y Sourcegraph en la nube **suben el código**.
- La búsqueda semántica falla en silencio: devuelve algo parecido aunque no sea lo correcto.

**Prioridad.** **Media** para zoekt si el repositorio del cliente es un monorepo en el que
ripgrep ya no sirve; **baja** para claude-context en local; **descartar** lo que sube código.

### 4. Resumen jerárquico

**Qué hay.** El repo-map de Aider, la wiki de RepoWise, el `GRAPH_REPORT.md` de Graphify, un
`CLAUDE.md` por directorio y DeepWiki.

**Qué ahorro da.** Un mapa de cabecera en vez de explorar a ciegas. Es la estrategia de este
repositorio a escala: un `AGENTS.md` que dice dónde está cada cosa.

**Esfuerzo.**

- **Bajo** para los `CLAUDE.md` por directorio: se escriben a mano y por partes.
- **Medio** para las wikis generadas, que cuestan llamadas al LLM.

**Riesgos.**

- Un resumen generado que envejece miente sin avisar.
- DeepWiki solo sirve para repositorios públicos.

**Prioridad.** **Alta** para los `CLAUDE.md` por directorio; **media** para la wiki de RepoWise;
**descartar** DeepWiki para código de cliente.

### 5. Reducir la salida de comandos

**Qué hay.** RTK, `repowise distill` y hooks propios.

**Qué ahorro da.**

- RTK declara hasta un 90 % menos de salida de bash, y avisa de que eso no es un 90 % menos de
  factura.
- `repowise distill` declara un 61 % en `pytest` y un 89 % en `git log -50`.

**Esfuerzo.** **Bajo**: un binario y un hook.

**Riesgos.** Un filtro que resume la salida de los tests puede **esconder justo el error** que
hacía falta leer. Hay que comprobar que las líneas de fallo pasan íntegras.

**Prioridad.** **Alta**. Es independiente del tamaño del repositorio y es la que menos cuesta.

### 6. Lo nativo de Claude Code

**Qué hay.**

- subagentes (`Explore`) que devuelven solo la conclusión;
- skills cuyo cuerpo se carga solo cuando hacen falta;
- `CLAUDE.md` por directorio;
- hooks;
- `/compact`.

**Qué ahorro da.** El contexto principal solo recibe conclusiones. Sin cifra.

**Esfuerzo.** Ninguno: ya viene con Claude Code. Solo hay que usarlo con disciplina.

**Riesgos.** Un subagente mal delegado vuelve con un resumen sin la prueba que lo sostiene.

**Prioridad.** **Alta, y la primera.**

### 7. Propio del caso: código de clientes

No es una herramienta, es un filtro que se aplica a todas las demás:

1. **Solo lo que corre en local.**
2. **Licencias revisadas.** AGPL y GPL, con legal; las no comerciales, fuera.
3. **Nada que escriba en la configuración global** sin revisarlo antes.

Descartables a priori, por hacer lo contrario de lo que se busca: repomix, code2prompt y
gitingest, que empaquetan el repositorio entero. Solo valen para trozos pequeños.
