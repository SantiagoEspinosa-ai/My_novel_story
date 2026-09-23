# Verificación formal de la cronología, en Lean 4

2026-09-23 · Lean 4.34.0, Lake 5.0.0, sin Mathlib

Comprueba cuatro invariantes temporales sobre la cronología de una obra, leída
de la misma SQLite que usa el harness. Si alguna falla, el ejecutable devuelve
1 y la versión no se publica.

| Archivo | Qué es |
| --- | --- |
| `Cronologia/Basic.lean` | El modelo: `Fecha`, `Evento`, `Participacion`, `Personaje`, `Obra` |
| `Cronologia/Invariantes.lean` | Las cuatro invariantes, `L-1`…`L-4` |
| `Cronologia/Fixture.lean` | Dos obras escritas a mano: una limpia y una que viola las cuatro |
| `Cronologia/Generado.lean` | **Generado**, no editar. Lo reescribe `generar_lean.py` desde SQLite |
| `Main.lean` → `verificar` | Corre el fixture. **Tiene que dar 0 siempre** |
| `MainReal.lean` → `verificar-real` | Corre la obra real. **Puede dar 1**, y eso es su trabajo |
| `generar_lean.py` | SQLite → Lean, con informe de cobertura |

## Cómo se ejecuta

Lean se instala con `elan`, que no necesita permisos de administrador:

```powershell
Invoke-WebRequest "https://github.com/leanprover/elan/releases/latest/download/elan-x86_64-pc-windows-msvc.zip" -OutFile elan.zip
Expand-Archive elan.zip -DestinationPath elan-init
.\elan-init\elan-init.exe -y --default-toolchain leanprover/lean4:stable
```

Y desde `specs/lean/`:

```powershell
lake build
lake exe verificar                                  # el fixture: debe dar 0
python generar_lean.py ..\..\backend\f6.db obra-x   # SQLite -> Generado.lean
lake build ; lake exe verificar-real                # la obra: 0 o 1
```

**Sin Mathlib a propósito.** Estas invariantes son comparaciones sobre listas
finitas: no hacen falta ni reales ni tácticas pesadas. Mathlib son varios GB y
minutos de compilación, y convertiría una verificación de segundos en una que
nadie ejecutaría en CI.

## Las cuatro invariantes

| | Dice | Espejo en Python |
| --- | --- | --- |
| **L-1** | El orden de la fábula se respeta salvo analepsis declarada | `INV-08` — **declarada y nunca ejecutada**: ver abajo |
| **L-2** | Nadie está presente en un evento anterior a su nacimiento | Nada. `consultas.edades` existe y no la llama ninguna puerta |
| **L-3** | Nadie está en dos lugares en el mismo momento | La mitad de accesibilidad de `INV-02`, pero escena a escena |
| **L-4** | Nadie aparece después de un evento que lo excluye | La mitad de `estado_vital` de `INV-02`, también escena a escena |

### Qué aporta Lean si dos de estas reglas ya están en Python

`INV-02` mira **una escena en el momento de su puerta**. Lean mira **la obra
entera cuando ya está escrita**. La diferencia no es de potencia, es de
alcance: una incoherencia entre el capítulo 2 y el capítulo 9 no es visible
desde la puerta del capítulo 9, porque cada escena por separado es impecable.
Es la Regla 6 en otro eje — *lo que solo existe entre dos cosas no lo ve nada
que mire una cosa*.

## El caso real: Lean detecta lo que nadie más mira

Ejecutado contra una base con el esquema real del backend, sembrada con una
obra de cuatro eventos:

```
== obra-x ==
violaciones: 2 · sin datos: 1
  [L-1] ev-2 se lee despues de ev-1 (discurso 1 -> 2) pero ocurre antes en la
        fabula (2019-6-8 10:0 < 2019-6-10 21:0) y no declara analepsis
  [L-3] per-marta esta presente en ev-3a (lug-faro) y en ev-3b (lug-bosque) a la vez
no comprobado por falta de dato:
  - per-luis no tiene fecha de nacimiento: su edad no se comprueba

Hay incoherencias temporales: la version NO se publica.   EXIT = 1
```

**`L-1` es el caso que más vale, y no porque Lean sea más listo: es que hoy no
lo mira nadie.** `INV-08` está declarada en `Docs/definitions.md` con severidad
`mayor`, tiene su consulta escrita en `cronologia/consultas.py`
(`orden_temporal`) — y **no aparece en `features/verificacion/puertas.py`, y a
`orden_temporal` solo la llaman sus propias pruebas**. El orden temporal de una
obra no se comprueba en ningún punto del pipeline. Registrado como `F-46`.

Es exactamente el patrón de `F-34`: una invariante que no se ejecuta y una que
está en verde **se ven igual desde fuera**.

### Lo que este caso todavía no es

**La obra de arriba está sembrada, no generada.** Reproduce la incoherencia que
el brief adversario busca provocar, con el esquema real y por el camino real
—SQLite → generador → Lean—, pero no sale de una generación pagada. El caso
plenamente real necesita ejecutar el brief adversario contra el harness y
apuntar Lean a esa base. Decir que ya lo es sería contar como medido algo que
no se ha medido.

## Cobertura: lo que no se comprueba, y se dice

Cada invariante devuelve **dos** listas: `violaciones` y `sinDatos`. Un informe
con cero violaciones y tres «sin datos» no dice que la obra sea coherente: dice
que hay tres cosas que no se han podido mirar. Separarlas es lo único que
impide leer una ausencia como un cero.

Hoy hay dos huecos declarados:

- **`L-4` no puede disparar sobre datos reales.** `Evento.excluye` llega
  siempre vacía porque **no hay de dónde sacarla**: `entidad` guarda el estado
  vital *actual* y no en qué evento cambió, y `cambios_de_estado_vital` del
  delta se aplica y no se conserva. Registrado como `F-45`. La invariante está
  escrita y probada contra el fixture: lo que falta es el dato, no la
  comprobación.
- **`L-2` se salta a quien no tiene fecha de nacimiento.** Es opcional a
  propósito (`SPEC-21` C-3): exigirla rompería todas las obras generadas hasta
  hoy. El informe lo cuenta aparte.

## Cada invariante tiene su caso negativo

Una invariante que nunca ha fallado no está verificada, solo declarada. Por eso
`verificar` no se limita a comprobar que la obra limpia pasa: **exige también
que la obra adversaria falle en las cuatro**, y devuelve 1 si alguna no
dispara. Si alguien deja una invariante siempre satisfecha, la obra limpia
seguiría pasando y la avería saldría en la primera ejecución.

```
== obra limpia ==          violaciones: 0 · sin datos: 0
== obra adversaria ==      violaciones: 4 · sin datos: 3
                           [L-1] ... [L-2] ... [L-3] ... [L-4] ...
```

## Decisiones de modelado que conviene conocer

- **El tiempo se representa dos veces.** `tFabula` como fecha, para comparar y
  calcular edades; `inicioMin` como entero, para sumar duraciones. Un
  calendario de verdad necesita saber cuántos días tiene febrero: eso lo hace
  Python con `datetime` y Lean recibe minutos ya calculados. Inventar aquí un
  `mes = 30 días` daría un orden que parece correcto y falla justo donde una
  novela pone «la noche del 31».
- **Los intervalos son medio abiertos**, `[inicio, inicio+duración)`, y dos
  eventos instantáneos en el mismo minuto sí solapan. Es la misma regla que
  `consultas.py`, y las dos mitades hacen falta: sin la primera, quien sale de
  una habitación y entra en otra da falso positivo; sin la segunda, dos cosas
  simultáneas con duración cero se cuelan.
- **`mencionado` no es `presente`.** Solo los presentes cuentan para `L-3`. Si
  un personaje nombrado contara, cada vez que dos personajes se acordaran del
  mismo ausente el validador diría que ese ausente está en dos sitios
  (`SPEC-21` C-3).
- **El generador lee SQL directamente** en vez de llamar a
  `features/cronologia/consultas.py`, porque esto vive fuera de `backend/` y
  llamar a una feature desde aquí sería el acoplamiento que `A-02` prohíbe. El
  riesgo, dicho en voz alta: si la semántica de `consultas.py` cambia, este
  fichero no se entera. Lo que protege es que Lean y Python comprueban lo mismo
  por caminos distintos, así que una divergencia aparece como desacuerdo entre
  los dos y no como silencio.
