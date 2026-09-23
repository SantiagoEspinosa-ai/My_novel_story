# `harness/evals/`

Briefs de prueba y sus resultados esperados. La carpeta la declara
`Docs/architecture.md` § "El harness" junto a `documentos/` y `adversarial/`;
esta es la primera que se crea, y se crea con un solo fichero porque hace
falta ya.

| Brief | Qué busca provocar | Estado |
| --- | --- | --- |
| `brief-incoherencia-temporal.json` | Incoherencias de cronología que ninguna puerta escena a escena puede ver | **Listo, sin ejecutar** |

De los cinco briefs que pide el enunciado, este es **el adversario temporal**.
Los otros cuatro —incluido el de inyección en el texto libre— no están escritos.

## Cómo se ejecuta, cuando haya una generación con los arreglos puestos

```powershell
# 1. Generar la obra con este brief (backend)
#    El identificador de obra que salga es el que se usa en el paso 2.

# 2. Volcar su cronología a Lean
cd specs\lean
python generar_lean.py ..\..\backend\<base>.db <id-de-obra>

# 3. Verificar
lake build ; lake exe verificar-real
```

Salida 1 = hay incoherencias temporales y la versión no se publica.

## Lo que hay que mirar **antes** de leer el resultado

El generador imprime un informe de cobertura, y sin él el resultado no
significa nada:

```
eventos_convertidos: N
eventos_sin_fecha_legible: [...]
personajes: N
personajes_sin_fecha_de_nacimiento: [...]
eventos_con_exclusion: 0
```

**Un «cero violaciones» con la mitad de los eventos fuera no es un cero.** Una
escena sin `t_fabula` no produce evento —`extraccion.evento_de_la_escena` no se
lo inventa, y hace bien— así que una obra cuyas escenas no declaren instante
llega a Lean casi vacía y pasa sin haber comprobado nada. Eso es el verde falso
que `F-34` enseñó a no dar por bueno.

`eventos_con_exclusion` vale **0 siempre** hoy, y no porque nadie muera: no hay
de dónde sacar el dato (`F-46`). Mientras siga así, `L-4` no se puede medir con
este brief aunque el brief esté diseñado para dispararla.

## Por qué este brief y no otro

Los cuatro ganchos están puestos a propósito y cada uno apunta a una
invariante distinta; el detalle está en el propio JSON, en
`por_que_provoca_cada_incoherencia`. Lo que los une es que **cada escena, por
separado, es impecable**: la de 1998 es coherente, la de 2019 es coherente, y
el conflicto solo existe en la relación entre las dos. Un brief que rompiera
una escena por dentro lo cazaría `INV-02` en su puerta y no probaría nada sobre
la verificación formal.
