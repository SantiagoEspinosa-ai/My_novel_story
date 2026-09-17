# archivo/ — Código de la arquitectura anterior

**Nada de lo que hay aquí se ejecuta.** No lo importa ningún módulo vivo, no lo
recoge `pytest` y no forma parte del harness. Está congelado tal como quedó el
2026-09-17, justo antes del cambio de arquitectura.

## Qué hay

| Archivo | Qué era |
|---|---|
| `agentes.py` | La capa de modelos: el único módulo que salía a la red. Cliente de OpenRouter sobre el SDK de OpenAI, lector de `.env`, carga de prompts, parseo defensivo de JSON, reintentos con espera creciente, contador de coste y la prueba de conexión |
| `orquestador.py` | El bucle principal en Python: arquitecto → biblia → escritor capítulo a capítulo. Pipeline mínimo, sin validadores |
| `tests/test_agentes.py` | Sus tests (cliente falso, sin red) |
| `tests/test_orquestador.py` | Sus tests del pipeline mínimo |

## Por qué está aquí y no borrado

El proyecto pasó de "un programa Python que llama a OpenRouter" a "Claude Code
orquestando cinco subagentes". Con ese cambio, estos dos módulos se quedaron sin
trabajo: ya no hay una capa de modelos propia, porque quien habla con el modelo
es Claude Code, y ya no hay un bucle principal en Python, porque el bucle lo
lleva la sesión.

Se conservan por tres motivos concretos:

1. **Hay lógica reutilizable si algún día hace falta.** `extraer_json`
   (quitar vallas ```` ``` ````, extraer el primer bloque `{...}` equilibrado) y
   `cargar_referencia_genero` resolvieron problemas que no han desaparecido: el
   parseo defensivo de los veredictos sigue siendo obligatorio por la regla 2 de
   `EJECUCION.md` §4. Si se vuelve a necesitar, es más rápido copiar de aquí que
   reescribirlo.
2. **Documentan decisiones que siguen vigentes.** El porqué del parseo
   defensivo y de los reintentos está escrito en sus docstrings, y esos
   docstrings son la mejor explicación que existe de por qué el contrato exige
   tratar un JSON no parseable como `FALLO`.
3. **Borrar código que costó una tarde no ahorra nada.** Una carpeta con una
   nota al lado cuesta cero y evita la pregunta "¿cómo lo hacíamos antes?".

## Por qué no se pueden ejecutar

`agentes.py` importa el SDK de OpenAI y `from src.config import RAIZ_PROYECTO`;
`orquestador.py` importa `from src import agentes, ...`. Desde su nueva
ubicación esos imports ya no resuelven, y no se han arreglado **a propósito**:
arreglarlos daría a entender que este código es una alternativa viable, y no lo
es. Depende de una clave de API que el proyecto ya no tiene y de una cuenta de
OpenRouter que ya no hace falta.

Por el mismo motivo, `pytest.ini` excluye esta carpeta de la recogida de tests.
Sus dos archivos de test son historia, no una suite que deba pasar.

## Qué leer en su lugar

| Si buscas | Ve a |
|---|---|
| Cómo se ejecuta el harness hoy | `EJECUCION.md` |
| Por qué se cambió de arquitectura | `DECISIONES.md` |
| La arquitectura anterior, explicada entera | `ADENDA-openrouter-vscode.md` (también deprecada) |
