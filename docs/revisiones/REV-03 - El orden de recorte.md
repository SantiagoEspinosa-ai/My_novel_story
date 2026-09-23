---
id: REV-03
revisa: "specs/SPEC - Backend.md § 2.4 — Orden de recorte"
estado: revisada
resultado: "A, B, C y G a SPEC-12. E y H a SPEC-11. D, F e I decididos en contra o ya cubiertos"
autor: "@Santiago Espinosa Domínguez"
fecha: 2026-09-22
---

# REV-03 — El orden de recorte, contra lo que `main` aprendió sufriéndolo

## Por qué esta revisión existe

§2.4 de `SPEC-01` fija el orden de recorte del contexto en seis bloques. Está **aprobada**,
y no estaba mal escrita: estaba escrita con lo que sabíamos. La rama `main` contiene un
ensamblador que **se ejecutó durante días**, y al leerlo aparecen nueve decisiones que
nuestro orden no previó.

Tres de ellas no lo matizan: **lo cambian de forma**.

Esto es el ciclo largo de `AGENTS.md` funcionando por primera vez —*"cuando el código
descubre que la spec estaba mal, se para, se corrige la spec, se vuelve a aprobar"*—, con
la variante de que aquí el código no es nuestro: es el de la otra rama, y lo que descubrió
lo descubrió generando novelas de verdad.

**Esta revisión no decide nada.** Inventaría y propone.

---

# Los tres que cambian la forma

## A · Entre «completo» y «ausente» hay «reducido»

**Nuestro §2.4 es binario.** Los seis bloques se recortan en orden, y recortar significa
que el bloque deja de estar.

**El suyo degrada en dos de sus tres pasos:**

| Paso | Qué hace | Tirar o degradar |
| --- | --- | --- |
| 1 | `hechos_efimeros` — fuera los efímeros, los permanentes nunca | Tira, pero solo una parte |
| 2 | `resumenes` — cada resumen se queda en **su primera frase** | **Degrada** |
| 3 | `capitulo_anterior` — el texto completo se sustituye por **su resumen** | **Degrada** |

El tercero es el que más importa: el capítulo anterior **no desaparece**, baja de texto
completo a resumen. En el nuestro, el bloque «escena anterior completa y resumen de las tres
previas» es el 3.º y se va entero.

**Por qué cambia la forma y no es un detalle.** El recorte deja de ser *elegir qué se
pierde* y pasa a ser *elegir cuánto se conserva de cada cosa*. Un orden binario de seis
bloques tiene seis decisiones; uno con degradación tiene, por cada bloque, un escalón
intermedio que hay que definir: qué es «la versión reducida» de las fichas de entidad, del
estado del mundo, de los resúmenes.

**Propuesta:** que cada fila de §2.4 declare **su forma reducida** además de su posición, y
que el recorte agote las formas reducidas antes de empezar a tirar bloques. Los bloques que
no tengan forma reducida lo dicen, y ese es un dato útil por sí solo.

## B · Dentro de un bloque hay cosas de dos clases

Su primer recorte no es un bloque entero: es **la mitad efímera de uno**. Los
`hechos_permanentes` no se tocan nunca; los efímeros se van primero que nada.

Es exactamente la lección de `P-A`. Descubriste que el registro de conocimiento tenía que
salir de `Recuperado` porque `INV-03` sin él no es peor, es **imposible**. Lo mismo, en otro
bloque: dentro de `Estado actual` hay hechos que sostienen la continuidad para siempre y
hechos que solo importan tres escenas.

Nosotros lo descubrimos razonando sobre una invariante; ellos, ejecutando.

**Propuesta:** revisar los seis bloques preguntando por cada uno *"¿hay aquí dos clases de
cosa con distinta durabilidad?"*. `Estado actual` es el candidato obvio. `Recuperado` ya se
partió una vez.

## C · Estimar para decidir no es medir para verificar

Su ensamblador usa `CARACTERES_POR_TOKEN = 4`, con el motivo escrito:

> *"Sin el tokenizador del proveedor no hay cuenta exacta, y no la necesitamos: esto solo
> decide cuándo recortar, y para eso basta una estimación conservadora."*

Nosotros no hacemos esa distinción. El presupuesto de `CLAUDE.md` **suma exactamente
100.000** y `VER-05` exige medir *"con un contador independiente del ensamblador"*. Las dos
cosas son correctas y responden a preguntas distintas:

| Pregunta | Qué necesita |
| --- | --- |
| ¿Recorto ya? | Rápido y conservador. Una estimación basta |
| ¿Me he pasado del límite? | Exacto, y **con una segunda fuente** (`VER-05`, `VER-41`) |

Confundirlas tiene un coste concreto: un ensamblador que cuenta exacto para decidir si
recorta paga el tokenizador en cada iteración del bucle de recorte, y no gana nada — porque
lo que decide es «me paso o no», no «por cuánto».

**Propuesta:** decirlo en §2.4. La estimación que decide el recorte es conservadora y
declara su margen; la medida que verifica el límite es exacta e independiente. Son dos
números distintos y conviene que tengan dos nombres distintos, o alguien los reconciliará
creyendo que son el mismo.

---

# Los seis que lo matizan

| # | Hallazgo | Qué haríamos |
| --- | --- | --- |
| **D** | **No fallan: siguen y lo anotan.** Agotados los recortes, registran *"la ventana sigue por encima del presupuesto"* y generan igual | **Nada.** No es un hueco, es su Regla 1: *"ningún capítulo detiene la generación"*. Nuestro `RF-26` falla antes que generar, y con `SPEC-10` ya decidimos que una `bloqueante` no se rinde. Son dos filosofías y la nuestra está elegida a conciencia |
| **E** | **Los recortes son salida, no efecto secundario.** `Ventana.recortes` es una lista que va al informe, y su tendencia entre capítulos es *"la señal de alarma más importante"* | Que el recorte se registre por llamada y que la **tendencia** se vigile. Es el hueco 8 de `SPEC-11` |
| **F** | **El orden de recorte es configurable** (`contexto.orden_recorte`) | Merece decisión propia. Nuestro orden se eligió razonando y sin medir; configurable es cómo se averigua si acertó. En contra: un orden configurable es un orden que nadie garantiza, y `VER-06` comprueba «el orden declarado» |
| **G** | **Los problemas del intento anterior entran en la ventana del escritor** | Añadirlo. Ninguno de nuestros seis niveles tiene sitio, y es el arreglo del hallazgo 11: allí el aviso de longitud *"lo leía la sesión orquestadora y no el escritor"* |
| **H** | **El ensamblador del manuscrito no corrige nada**, por trazabilidad entre lo auditado y lo entregado | Es el hueco 10 de `SPEC-11`. No toca §2.4 |
| **I** | **La regla del capítulo N-1** mantiene la ventana casi constante sea cual sea N | **Nada: ya lo tenemos.** Es nuestro nivel `Local`. Los dos sistemas llegaron solos a lo mismo, que es la mejor señal de que esa parte está bien |

---

# Qué propongo hacer con esto

**A, B y C piden una spec** que reescriba §2.4, porque cambian la forma del orden y `SPEC-01`
está aprobada. **G** entra con ellas: es un bloque nuevo en la tabla.

**E y H** ya están inventariados como huecos 8 y 10 de `SPEC-11`.

**D e I** no necesitan nada: uno es una divergencia decidida y el otro una convergencia.

**F es la única que no sé dónde poner**, y por eso no propongo: tiene un argumento fuerte a
favor —el orden actual se eligió en diez minutos y el suyo se sufrió tres días— y uno en
contra —`VER-06` comprueba *"el orden declarado"*, y un orden configurable convierte esa
comprobación en «se respetó lo que dijera la configuración», que es mucho más débil—.

# Lo que no revisé

Solo `src/contexto.py` entero y las cabeceras de `src/ensamblador.py` y
`src/orquestacion.py`. Las 1.908 líneas de `orquestacion.py` pueden tener más decisiones de
ensamblado en el bucle de reintentos; no las he leído.
