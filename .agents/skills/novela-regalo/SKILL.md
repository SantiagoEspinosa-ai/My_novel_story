---
name: novela-regalo
description: Lanzar una generacion de la novela regalo e inspeccionar lo que hizo de verdad -base, hooks, tools y Langfuse- sin fiarse del codigo de salida. Usala antes y despues de cualquier ejecucion real de novela_regalo.py o evaluar.py.
---

# Lanzar e inspeccionar una novela regalo

Una ejecucion que termina con codigo 0 **no dice que los validadores hayan juzgado nada**. La
primera ejecucion real aceptada lo demostro: el capitulo paso, y el Editor habia salido
`sin_veredicto` (`F-76`) y el Resumidor habia fallado (`F-77`). Esta skill es el recorrido que
separa «termino» de «funciono».

## Antes de gastar

1. La ficha valida como `FichaDeEntrevista` y es de **datos inventados** (`ejemplos/brief-ejemplo.json`).
2. `backend/config/sistema.json` tiene los modelos del Planificador, el Revisor, el Escritor, el
   Editor y el Resumidor. `claude` esta en el `PATH`.
3. `backend/.env` tiene las tres claves de Langfuse si se quiere enviar. En un worktree nuevo
   **no esta**: lo ignorado no viaja y hay que copiarlo.
4. La suite entera pasa: `cd backend && python -m pytest app -q`. Entera, no la de la carpeta
   que se toco.
5. Una base por obra (`--base`), y nunca una base con datos de una persona real.

## Lanzar

```
cd backend
python -X utf8 novela_regalo.py FICHA.json --capitulos 1 --base prueba.db --obra obra-prueba
```

`--capitulos 1` primero: un capitulo cuesta del orden de lo medido en `harness/evals/medidas.md`
§ R0, y una novela entera no se lanza sin haber visto uno pasar. Guarda la salida entera: el
informe se imprime al final.

## Inspeccionar: lo que el informe no dice

Con la base en modo lectura (`sqlite3.connect("file:prueba.db?mode=ro", uri=True)`):

| Pregunta | Consulta | Lo que delata un fallo callado |
| --- | --- | --- |
| ¿Juzgo el Editor? | `SELECT invariante, estado, descripcion FROM hallazgo` | Un `INV-26` en `sin_veredicto`: el capitulo paso sin juicio |
| ¿Resumio el Resumidor? | `SELECT agente, resultado, clase_de_fallo FROM traza_de_delegacion`, y `SELECT COUNT(*) FROM resumen` | `resultado = 'fallo'` y cero resumenes: el capitulo siguiente arranca sin memoria |
| ¿Se consolido? | `SELECT id, estado, borrador_aceptado FROM escena` | `consolidada` es lo esperado; `generada` o `en_revision` es una parada |
| ¿Hay cronologia y usos? | `SELECT COUNT(*) FROM evento_cronologico`, `... FROM uso_de_hecho` | Cero filas: Lean y la regeneracion no tendran nada que mirar |
| ¿Se llamaron las tools? | `SELECT agente, herramienta, validacion FROM llamada_a_herramienta` | Muchas `no_existe`: el agente pide cosas que la story bible no tiene |
| ¿Actuo el policy engine? | `SELECT tipo, COUNT(*) FROM decision_de_politica GROUP BY tipo` | Una vetada que dispara sobre una preposicion (`F-59`) |
| ¿Con que codigo? | `SELECT * FROM procedencia` | El commit que se cite en un informe **se lee de aqui**, no se recuerda |

**Hooks.** El registro esta en `%TEMP%/hooks-<obra>.jsonl`. Una fila `validar_capitulo` sobre el
Planificador o el Revisor sale por la rama que no comprueba nada: solo cuentan las del Escritor.

**Langfuse.** La lectura de trazas antigua no existe para organizaciones posteriores al
16-09-2026: las observaciones se leen de `GET /api/public/v2/observations` (con `fromStartTime` y
`toStartTime`) y los scores de `GET /api/public/v3/scores`, con autenticacion basica de las dos
claves. La sesion de una obra es `observacion.sesion_de(obra)`. Hay que comprobar que la suma de
`totalCost` de la sesion coincide con el coste del informe, y que ninguna observacion lleva
`input`, `output` ni `model`.

## Despues

- Cada fallo callado que aparezca es un `F-xx` en `docs/verification.md`, con su prueba roja
  antes del arreglo (el doble tiene que tener la forma de lo real).
- Las cifras van a `harness/evals/medidas.md` **con su direccion de sesgo**, y lo que no se midio
  dice «sin medir».
- El PDF, solo si la puerta publico: `python -X utf8 leer_obra.py --base prueba.db --obra obra-prueba --pdf RUTA`.
