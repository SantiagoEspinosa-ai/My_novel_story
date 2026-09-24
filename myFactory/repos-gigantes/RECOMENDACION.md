# Repositorios gigantes: qué instalar, qué evaluar y qué descartar

2026-09-24 · Contracción del informe `informe-por-categoria.md`. Las cifras, las fuentes y los
supuestos están allí.

**Punto de partida.** El código es de clientes, así que todo tiene que correr en local, con una
licencia apta para empresa y sin tocar la configuración global a ciegas. **Ningún ahorro de
tokens de este documento está medido por nosotros**: los que aparecen los declara su autor.

## Instalar ya

Son baratas, corren en local y no dependen de la forma del repositorio del cliente.

| Qué | Por qué | Dependencias |
| --- | --- | --- |
| **Lo nativo de Claude Code**: subagentes `Explore`, un `CLAUDE.md` por directorio grande, skills que se cargan por partes | No cuesta nada y es la mayor palanca: al contexto principal solo llegan conclusiones | Ninguna |
| **RTK** | Filtra la salida de tests, git y logs antes de que la lea el agente. Declara hasta un 90 % menos de salida de bash | Un binario y un hook `PreToolUse`. Apache-2.0 |
| **ast-grep** (+ `ast-grep-mcp`) | Busca por estructura del código y no por texto: menos ruido que grep | Un binario. MIT |
| **Serena** | Lee y edita por símbolo mediante LSP, sin abrir el fichero entero | Python y el servidor de lenguaje de cada lenguaje del cliente. GPL-3: uso interno, **con visto bueno de legal** |

**Condición para RTK.** Antes de dejarlo activo hay que comprobar que las líneas de un test que
falla llegan íntegras: se provoca un fallo y se mira qué ve el agente. Un filtro que se come el
error ahorra tokens a costa de esconder justo lo que hacía falta leer.

## Evaluar después, con piloto y medida definida

**Cómo se mide en todos los pilotos.** Se eligen cinco tareas reales sobre un repositorio del
cliente: localizar un fallo, explicar un módulo, cambiar una firma y sus llamadas, y otras dos
de ese estilo. Cada una se hace dos veces, **con y sin** la herramienta, en sesiones nuevas.
Se comparan dos cosas:

- los tokens de entrada que da el uso de la sesión;
- si la tarea quedó bien hecha.

La regla de decisión, **con un umbral del 30 % que es una propuesta mía, no sale de ninguna medida: ajústalo**:

- **Entra** si ahorra al menos un 30 % sin empeorar ninguna tarea.
- **No entra** si empeora alguna, ahorre lo que ahorre.
- Entre el 0 y el 30 %, se habla con los números delante.

| Qué | Cuándo tiene sentido | Dependencias |
| --- | --- | --- |
| **Graphify** | Primer piloto. Ver su recomendación abajo | Python ≥3.10, paquete `graphifyy` |
| **RepoWise** | Segundo piloto, después de Graphify. Ver abajo | Python ≥3.11. LanceDB y embeddings solo si se usa la búsqueda semántica |
| **zoekt** | Solo si el cliente tiene un monorepo en el que ripgrep ya tarda | Un servidor Go que se autoaloja. Apache-2.0 |
| **codebase-memory-mcp**, **code-graph-rag** | Si Graphify no convence: son la misma categoría con licencia MIT | Sin leer su README: **supuesto** |
| **claude-context en local** | Si hace falta búsqueda semántica y se puede montar Milvus local | Embeddings locales y Milvus |
| **universal-ctags** | Si Serena no arranca en el lenguaje del cliente | Un binario. GPL-2.0 |

## Descartar

| Qué | Por qué |
| --- | --- |
| GitNexus | Licencia PolyForm **no comercial**: no se puede usar con clientes |
| Greptile, Sourcegraph en la nube, DeepWiki | **Suben el código** a un tercero. DeepWiki, además, solo sirve para repositorios públicos |
| mcp-server-tree-sitter, snapshot de Sourcegraph | Archivados |
| mcp-language-server | Siete meses sin push, y Serena cubre lo mismo |
| repomix, code2prompt, gitingest | Empaquetan el repositorio entero, que es lo contrario de lo que se busca. Solo valen para trozos pequeños |
| Octocode | Pequeño y centrado en la API de GitHub; no aporta sobre lo anterior |
| context7 | Es otro problema: documentación de librerías, no el código del cliente. Se puede instalar aparte |

## Graphify: evaluar primero, en piloto y solo con código

**Recomendación: primer piloto, con `--code-only` y sin `--strict`.** No se instala en global
hasta pasar la medida.

- **A favor:**
  - el grafo del código se construye en local, sin LLM ni embeddings, y se reconstruye en cada
    commit sin coste;
  - licencia Apache-2.0;
  - trae skill, MCP y hooks para Claude Code.
- **En contra:**
  - versión 0.x;
  - **no declara ninguna cifra de ahorro de tokens**, así que no hay ni una promesa que
    contrastar;
  - lo que no es código (documentación, PDF) sale hacia el LLM;
  - `--strict` impide leer ficheros directamente, algo que hay que poder hacer en un cliente;
  - apunta cada consulta en `~/.cache/graphify-queries.log`, fuera del proyecto;
  - la empresa empuja una plataforma de pago.
- **Qué vigilar en el piloto:**
  - si el grafo aguanta millones de líneas y cuánto tarda el primer índice;
  - si las aristas marcadas `INFERRED` confunden al agente.

## RepoWise: evaluar después, y separar las dos cosas que hace

**Recomendación: segundo piloto, con `--no-llm`, en una máquina o perfil de usuario de
prueba.** Es donde menos se solapa con Graphify.

RepoWise hace dos cosas distintas y conviene decidirlas por separado:

- **Contexto para el agente** (`get_context`, 10 herramientas MCP). Compite con Graphify.
  Declara 393 tokens frente a 13.984 en una recuperación y un 31,6 % menos de salida sobre
  django, según su autor.
- **Auditoría del código del cliente**: señales de git (hotspots, co-change, bus factor),
  código muerto, 51 detectores de salud y documentación desfasada. Esto **no lo da Graphify**,
  y es lo que puede justificarlo por sí solo en un encargo de consultoría.

Hay que tener en cuenta tres cosas:

- **La licencia es AGPL-3.0 o comercial.** Para uso interno como herramienta suele bastar, pero
  lo tiene que ver legal antes de usarlo con un cliente.
- **`repowise init` escribe en `~/.claude/settings.json`**, que es la configuración global, no
  la del proyecto. Hay que hacerlo en un perfil de prueba y revisar el diff.
- **La wiki con prosa manda código al proveedor del LLM.** Se deja apagada.
- `repowise distill` solapa con RTK. Se queda RTK, que ya está en "instalar ya", y `distill` no
  se activa.

**Si solo cabe una de las dos:** Graphify para navegar, RepoWise si el encargo incluye
auditar la salud del código.

## Orden y dependencias

1. Lo nativo, RTK (tras comprobar que no se come los fallos), ast-grep y Serena (tras el visto
   bueno de legal). No dependen entre sí.
2. El piloto de Graphify, con la medida de arriba.
3. El piloto de RepoWise. Su parte de contexto se compara con el resultado de Graphify; su parte
   de auditoría se evalúa aparte.
4. zoekt y el resto, solo si el piloto de un cliente concreto lo pide.
