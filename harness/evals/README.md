# `harness/evals/`

Briefs de prueba y sus resultados esperados. La carpeta la declara
`docs/architecture.md` § "El harness" junto a `documentos/` y `adversarial/`;
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

`eventos_con_exclusion` **ya no es siempre 0** (`F-46`, cerrado): sale de
`cambios_de_estado_vital` del delta persistido, así que `L-4` sí se puede medir
con este brief. Y por eso ese número hay que mirarlo: **si vale 0 en una obra
donde alguien muere, el fallo está en el generador o en el delta, no en la
invariante.** Solo `muerto` excluye; `desaparecido` no, porque en terror puede
volver.

## Cómo se lee un cero, en cualquier ejecución

Vale para este brief y para cualquier generación. **La pregunta al ver un
resultado limpio no es «¿está la obra bien?», sino «¿llegó alguna puerta a
tener algo que rechazar?».** Son dos preguntas distintas y solo la segunda se
puede contestar mirando el resultado.

Ya pasó una vez y está escrito como `F-30`: una ejecución de seis escenas
terminó sin que `INV-03` bloqueara ni una vez, y ese cero **no valía** porque
el mecanismo nunca se ejerció — no hubo una sola revelación que comprobar. Un
validador que no puede dispararse no está midiendo cero.

Así que ante una obra que cierra con cero hallazgos, en este orden:

1. **¿Se ejecutó cada invariante, o se saltó por falta de dato?** Un
   `sin_veredicto` con `dato_ausente` no es un pase.
2. **¿Hubo material que pudiera violarla?** Cero bloqueos de `INV-03` sin
   ninguna acción sobre hechos es un cero vacío; con cuarenta acciones es un
   cero que dice algo.
3. **¿Cuántas escenas llegaron a Lean, y cuántas se quedaron sin
   `t_fabula`?** El informe de cobertura del generador lo dice, y sin él un
   «0 violaciones» puede significar «0 eventos».

Las tres son la misma precaución: **una ausencia no es un cero**, y el
informe tiene que permitir distinguirlas sin volver a ejecutar nada.

## Por qué este brief y no otro

Los cuatro ganchos están puestos a propósito y cada uno apunta a una
invariante distinta; el detalle está en el propio JSON, en
`por_que_provoca_cada_incoherencia`. Lo que los une es que **cada escena, por
separado, es impecable**: la de 1998 es coherente, la de 2019 es coherente, y
el conflicto solo existe en la relación entre las dos. Un brief que rompiera
una escena por dentro lo cazaría `INV-02` en su puerta y no probaría nada sobre
la verificación formal.
