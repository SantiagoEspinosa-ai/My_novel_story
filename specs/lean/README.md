# Verificación formal de la cronología, en Lean 4

2026-09-23 · Lean 4.34.0, Lake 5.0.0, sin Mathlib

Comprueba cuatro invariantes temporales sobre la cronología de una obra, leída
de la misma SQLite que usa el harness. Si alguna falla, el ejecutable devuelve
1 y la versión no se publica.

---

## Lo que esto destapó: no faltaban tablas, el modelado impedía que Lean dijera nada

La primera obra de diez capítulos no pudo ser verificada formalmente, y la
razón no es la que parecía. `evento_cronologico` no existía en su base — pero
**aunque hubiera existido, no habría servido**.

El guion modelaba **una obra por capítulo**: la base tiene diez obras de seis
escenas, `obra='cap-01'`…`obra='cap-10'`. Y la cronología se consulta con
`WHERE obra = ?`. Así que **cada capítulo era su propia cronología y no había
un solo par que comparar** entre capítulos, que es exactamente lo que estas
cuatro invariantes miran.

Dicho de otro modo: con todas las tablas puestas y todos los datos rellenos,
`L-1`…`L-4` habrían devuelto cero violaciones sobre diez cronologías de un
capítulo cada una, y ese cero no habría significado nada.

**Por eso el cambio del guion —una obra con diez capítulos en vez de diez
obras— no es un ajuste: es lo que desbloquea la verificación formal.** Hasta
que los capítulos pertenezcan a la misma obra, la cronología de la fábula no
tiene sobre qué existir. Registrado en `F-52`.

Es también la razón de que `escena.capitulo` esté a `None` en toda esa base:
la identidad del capítulo viajaba en la columna `obra`.

---

| Archivo | Qué es |
| --- | --- |
| `Cronologia/Basic.lean` | El modelo: `Fecha`, `Evento`, `Participacion`, `Personaje`, `Obra` |
| `Cronologia/Invariantes.lean` | Las cuatro invariantes, `L-1`…`L-4` |
| `Cronologia/Fixture.lean` | Dos obras escritas a mano: una limpia y una que viola las cuatro |
| `Cronologia/Generado.lean` | **Generado**, no editar. Lo reescribe `generar_lean.py` desde SQLite |
| `Main.lean` → `verificar` | Corre el fixture. **Tiene que dar 0 siempre** |
| `MainReal.lean` → `verificar-real` | Corre la obra real. **Tres salidas**: `0` limpio, `1` con violaciones, `2` sin veredicto |
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
lake build ; lake exe verificar-real                # la obra: 0, 1 o 2
```

### Las tres salidas, y por qué no son dos

| | Significa | ¿Se publica? |
| --- | --- | --- |
| `0` | Se miró y no hay incoherencias | Sí |
| `1` | Hay incoherencias | No |
| `2` | **Sin veredicto**: no había bastante dato para mirar | No |

El `2` es la Regla 8 aplicada a este validador, y cierra un hueco real
(`F-54`). Antes, una obra que llegaba con cero eventos —porque sus escenas no
declaran `t_fabula`, o porque la tabla estaba vacía— producía cero violaciones
y el programa decía «puede publicarse». **El veredicto era correcto y la
conclusión falsa.**

El caso hermano se midió en `F-52`: allí `evento_cronologico` **no existía** y
el generador murió con `no such table`, lo que evitó el verde falso. Pero lo
evitó **por accidente del caso**: una tabla presente y vacía es un escenario
más probable que una ausente, y ahí no moría nadie. Lo único que avisaba era
el informe de cobertura del generador, que depende de que alguien lo lea — y
una salvaguarda que depende de eso no es una salvaguarda.

Ahora el generador emite una `Cobertura` junto a la obra y **Lean decide con
ella**, así que la negativa a dar veredicto vive en el verificador. Medido en
las dos direcciones:

```
base de demo (5 eventos)     → 3 violaciones               EXIT 1
tablas presentes y vacías    → SIN VEREDICTO: cero eventos EXIT 2
```

Es la misma decisión que la puerta de capítulo tomó con `sin_fecha_legible`.

**Sin Mathlib a propósito.** Estas invariantes son comparaciones sobre listas
finitas: no hacen falta ni reales ni tácticas pesadas. Mathlib son varios GB y
minutos de compilación, y convertiría una verificación de segundos en una que
nadie ejecutaría en CI.

## Las cuatro invariantes

| | Dice | Espejo en Python |
| --- | --- | --- |
| **L-1** | El orden de la fábula se respeta salvo analepsis declarada | `INV-08` — enchufada en `b2f097c` tras `F-47`. **Las dos coinciden**: ver abajo |
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

### `F-47` · No es que Lean viera algo que a los otros se les escapó: es que Lean es lo único que lo mira

El enunciado pide «un caso real donde Lean detecte algo que los otros
validadores no vieron». Lo que apareció es más fuerte que eso, y conviene
decirlo con todas las letras porque es lo que cambia la conclusión:

> **`INV-08` —el orden temporal— está declarada, tiene su consulta escrita,
> tiene pruebas propias que pasan, y no la ejecuta nadie en el pipeline.**

Las tres mitades, para que se vea que no es una omisión por descuido sino algo
que *parece* terminado:

| | Estado |
| --- | --- |
| Declarada | `Docs/definitions.md`: `INV-08`, nivel capítulo, severidad `mayor`, con sus fuentes de datos |
| Implementada | `cronologia/consultas.py` → `orden_temporal()`, que compara fábula con discurso y devuelve las inversiones |
| Probada | Sus propias pruebas la ejercitan y pasan |
| **Enchufada** | **No.** No aparece en `features/verificacion/puertas.py`, y a `orden_temporal()` **solo la llaman sus propias pruebas** |

Es decir: **una invariante con toda la apariencia de estar cubierta, a la que
solo le faltaba estar enchufada.** Desde fuera —leyendo el documento, leyendo
el código, mirando las pruebas en verde— no hay forma de distinguirla de una
que sí se ejecuta. Es el patrón de `F-34` elevado a su versión más engañosa:
allí una invariante se saltaba en silencio por un campo ausente; aquí no se
salta, es que nunca se la llama.

**Por eso el caso vale.** Lean no es más listo que `orden_temporal()` —hacen la
misma comparación—; lo que hace es **ejecutarse**. Y ejecutarse es lo que
destapó que el orden temporal de una obra no se comprueba en ningún punto del
pipeline, cosa que ninguna lectura del repositorio había revelado en semanas.

Registrado como `F-47`, y **cerrado**: la sesión de backend la enchufó en
`b2f097c`, en la puerta de cierre de `features/auditoria/capitulo.py` —es de
nivel capítulo, así que ese y no `verificacion/puertas.py` era su sitio—.

**La medida que lo cierra del todo: la puerta y Lean coinciden.** Sobre la
misma base, `orden_temporal` devuelve `inversiones: [('ev-1','ev-2')]` y `L-1`
levanta esa misma pareja. La redundancia es real: dos caminos independientes
llegando al mismo veredicto, que es lo que la Regla 3 pide de una segunda
fuente. Con una diferencia **medida y no supuesta**: la puerta compara solo
pares adyacentes y Lean todos los pares, así que sobre una obra con varias
inversiones pueden no coincidir en el recuento aunque coincidan en el
veredicto.

#### Al volver a medir la coincidencia, hay que comparar lo mismo

La puerta cambió después de esa medida (`0d7bd8b`): `evaluar_cierre` pedía el
orden temporal de **la obra entera** y filtraba las escenas **por capítulo**,
cosa que coincidía por accidente mientras cada obra tenía un solo capítulo.
Ahora filtra de verdad, e imputa la inversión que cruza dos capítulos **al
posterior**, que es donde el lector la encuentra.

Así que las dos comprobaciones **ya no miran el mismo conjunto**:

| | Qué mira | Cuándo |
| --- | --- | --- |
| La puerta | Las escenas **de un capítulo**, más las inversiones que cruzan, imputadas al posterior | Al cerrar cada capítulo |
| `L-1` | **Todos** los pares de la obra | Cuando la obra está escrita |

No es una discrepancia, es una diferencia de alcance, y por eso hay que
decirla antes de medir: al comparar hay que **agregar los resultados de la
puerta de los diez capítulos** y contrastar esa unión contra el conjunto de
`L-1`. Si se compara un capítulo contra la obra entera, van a salir
diferencias que no significan nada, y peor: si alguna significara algo, ese
ruido la taparía.

**Y la agregación no es una unión cualquiera: el resultado esperado es una
igualdad exacta.** Lo señaló la sesión de backend y cambia la prueba. Una
inversión que cruza del capítulo tres al cuatro aparece **una sola vez**,
imputada al cuatro — que es además el capítulo que `L-1` nombra al describir
el par. Así que agregar los diez capítulos debe dar **exactamente** el
conjunto de `L-1`, sin duplicados y sin huecos:

- si un par sale **dos veces** al agregar, o
- si `L-1` ve un par que **ninguna** puerta levantó,

eso ya no es alcance, es **discrepancia real**, y hay que averiguar cuál de
los dos está mal. Vale la pena plantearlo así porque convierte un
«se parecen» en una igualdad que se puede falsar, que es lo único que sirve
como segunda fuente.

Y queda una decisión abierta que es del autor, no del código (`F-50`):
**`INV-08` dice «salvo analepsis declarada» y no hay dónde declararla.**
`MomentoNarrativo` tiene `t_fabula`, `t_discurso` y `duracion_ficcional`, y
ningún campo de analepsis. Tener los dos ejes no basta, y el motivo es lógico:
una analepsis *es* que la fábula retroceda mientras el discurso avanza, que es
la forma exacta de la violación — deducirla de los dos ejes la haría
indistinguible de lo que la invariante persigue. Hasta que exista una marca
aparte, toda inversión sale, y en terror eso no es un caso raro.

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

- **`L-4` ya dispara sobre datos reales** (`F-46`, cerrado). El generador lee
  `cambios_de_estado_vital` de `delta_de_escena`, donde el delta entero se
  persiste desde el merge de `specs-frontend`. **Solo `muerto` excluye**:
  `desaparecido` no, porque el dominio dice que en terror «no se sabe si sigue
  vivo» es material narrativo y un desaparecido puede volver — tratarlo como
  exclusión convertiría el recurso más común del género en una violación.
  Medido: `per-luis queda excluido en ev-3b y aparece en ev-4`.
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
