# Respaldo económico · Novel-IAs

Documento de apoyo para las preguntas posteriores a la presentación. Cada cifra dice **de dónde sale** y si está **medida** o **estimada**. Lo medido se puede enseñar; lo estimado se justifica.

---

## 1 · La única cifra medida: el coste de tokens

| Novela publicada | USD | Delegaciones | Fuente |
| --- | --- | --- | --- |
| Novela A | 5,45 | 43 | Libro de gasto en SQLite · `gasto_de_delegacion` |
| Novela B | 6,18 | 41 | Ídem |
| **Media usada** | **5,80** | | |

**Cómo se mide.** Cada llamada a un agente escribe una fila con su coste en dólares. El total de una novela es la suma de sus filas. Una llamada sin coste se guarda como nulo, nunca como cero, y entonces el total se marca como **suelo** — es decir, el coste real puede ser algo mayor, nunca menor.

**Reconciliación.** En las dos ejecuciones donde se comparó, el libro de gasto y Langfuse dan la misma cifra al céntimo y a la delegación. Son dos fuentes independientes.

### Desglose por agente (novela A)

| Agente | USD | % |
| --- | --- | --- |
| Escritor | 3,91 | 72% |
| Editor | 0,78 | 14% |
| Resumidor | 0,43 | 8% |
| Planificador | 0,20 | 4% |
| Revisor del plan | 0,12 | 2% |

**Lectura:** el Escritor es casi tres cuartas partes del coste. Es donde está la palanca y también donde está el riesgo — abaratarlo se paga en reescrituras.

### El rango de 3,8 veces

Con un reparto de modelos distinto, una novela equivalente costó **20,56 USD en 36 delegaciones**. La configuración barata hizo **más** trabajo (43 delegaciones) y costó **3,8 veces menos**.

**Conclusión defendible:** el coste lo decide el reparto de modelos, no el volumen de llamadas. Es un parámetro de configuración, no una propiedad del sistema.

---

## 2 · El coste completo por novela

| Partida | USD | Medido o estimado | Justificación |
| --- | --- | --- | --- |
| Tokens | 5,80 | **Medido** | Media de dos novelas publicadas, reconciliada con Langfuse |
| Infraestructura | ~1,00 | Estimado | Servidor, almacenamiento y observabilidad, repartidos por novela a volumen medio |
| Reserva de revisiones | ~2,00 | Estimado | Cubre un tercio de una revisión completa (5,80). Con la política de 3 revisiones incluidas, asume que la mayoría no las agota |
| Comisión de pago | ~1,50 | Estimado | 3% + 0,30 sobre 39 USD = 1,47. Tarifa estándar de pasarela |
| **Total** | **≈ 10,30** | | |

**Lo que hay que decir si preguntan:** de las cuatro partidas, solo una está medida. Las otras tres son estimaciones razonadas y están marcadas como tal en la slide. Ninguna es crítica: incluso duplicando las tres estimadas, el margen sigue por encima del 50%.

---

## 3 · Precio y margen

| Escenario | Precio | Margen USD | Margen % |
| --- | --- | --- | --- |
| Accesible | 29 | 18,70 | 64% |
| **Propuesto** | **39** | **28,70** | **74%** |
| Premium | 49 | 38,70 | 79% |

**Por qué 39.** Tres razones, en orden de peso:

1. **Es el precio de un regalo, no de un libro.** El comparable no es una novela de 15 euros, es un regalo personalizado —una joya grabada, un álbum encuadernado, un retrato por encargo—, que vive entre 30 y 60.
2. **Deja margen para la promesa de revisiones.** A 39, tres revisiones completas caben dentro del margen sin entrar en pérdidas.
3. **Está por debajo del umbral psicológico de 40.** Convención comercial, no cálculo.

**El coste marginal de una novela extra es de 10,30 USD.** Eso permite absorber errores, reintentos y capítulos rechazados sin que el margen se resienta.

---

## 4 · Coste de desarrollo y recuperación

| Fase | Horas |
| --- | --- |
| Diseño | 6 |
| Desarrollo | 20 |
| Validación | 10 |
| Despliegue | 4 |
| **Total** | **40** |

**40 h × 70 USD/h = 2.800 USD.**

**Recuperación:** 2.800 ÷ 28,70 de margen por novela = **98 novelas**. A 200 novelas al mes, se recupera en la primera quincena.

**Si preguntan por la tarifa:** 70 USD/hora es una tarifa de consultoría técnica de gama media para este tipo de trabajo. Es una estimación a validar con el cliente y no cambia la estructura de la propuesta — a 100 USD/h la recuperación sube a 140 novelas, que sigue siendo menos de un mes a volumen medio.

---

## 5 · Escenarios de volumen

| Novelas/mes | Ingresos | Coste | Margen |
| --- | --- | --- | --- |
| 50 | 1.950 | 515 | **1.435** |
| 200 | 7.800 | 2.060 | **5.740** |
| 1.000 | 39.000 | 10.300 | **28.700** |

Precio 39 USD · coste completo 10,30 USD por novela.

**Lo que el modelo asume:** que el coste por novela es lineal. Es razonable porque el grueso es el coste de tokens, que escala con el uso. La infraestructura sí tiene economías de escala, así que a 1.000 novelas el margen real sería algo **mayor** que el de la tabla.

**Lo que el modelo no incluye:** atención al cliente, marketing y adquisición. Son costes de negocio, no de producto, y dependen del canal de venta del cliente.

---

## 6 · Análisis de sensibilidad

### Si el precio de los tokens sube un 50%

| | Antes | Después |
| --- | --- | --- |
| Tokens por novela | 5,80 | 8,70 |
| Coste completo | 10,30 | 13,20 |
| Margen a 39 USD | 28,70 (74%) | 25,80 (**66%**) |

**Por qué aguanta:** los tokens son el 56% del coste, pero solo el 15% del precio. Una subida del 50% en la partida mayor cuesta ocho puntos de margen.

**Y hay palanca:** el rango medido de 3,8 veces significa que una subida de precios se puede compensar ajustando el reparto de modelos, sin tocar el precio al cliente.

### Si el cliente pide más de tres revisiones

Cada revisión adicional cuesta como máximo **5,80 USD** — el precio de regenerar una novela entera. En la práctica cuesta menos, porque un cambio del lector solo regenera los capítulos afectados: en la demo medida, siete de diez.

| Revisiones extra | Coste completo | Margen |
| --- | --- | --- |
| 0 (política) | 10,30 | 74% |
| 1 | 16,10 | **59%** |
| 2 | 21,90 | 44% |
| 3 | 27,70 | 29% |

**Umbral:** el negocio deja de tener sentido a partir de **cinco revisiones extra**, donde el margen cae por debajo del 10%. La política de tres revisiones incluidas deja un colchón de dos.

**Mitigación propuesta:** a partir de la cuarta revisión, cobrarla aparte a 9 USD. Cubre el coste con margen y desincentiva el uso abusivo sin cerrar la puerta.

---

## 7 · Preguntas que probablemente hagan

**«¿El coste de 5,80 incluye los fallos y reintentos?»**
Sí. Es el coste total de todas las delegaciones de la novela, incluidos los capítulos rechazados y reescritos. En la novela A fueron 16 intentos para 10 capítulos.

**«¿Qué pasa si una novela se atasca y no termina?»**
Se para y no se cobra. El sistema tiene topes de reintentos y un techo de gasto por novela: no puede gastar indefinidamente. Una novela parada cuesta lo gastado hasta ahí, que es menor que una completa.

**«¿Por qué el Escritor es tan caro comparado con el resto?»**
Porque genera texto largo diez veces, y porque cada delegación paga su propio contexto. El Editor juzga y devuelve seis notas; el Escritor escribe 1.300 palabras.

**«¿Se puede bajar de 5,80?»**
Sí, y hay margen medido. Pero bajar el modelo del Escritor se paga en reescrituras, que son delegaciones completas. La próxima medida pendiente es exactamente esa: cuánto sube la tasa de rechazo al bajar el modelo.

**«¿De dónde sale el 1,00 de infraestructura?»**
Es una estimación de servidor, base de datos y observabilidad repartida por novela a volumen medio. A volúmenes altos baja; a volúmenes muy bajos sube. No es una cifra medida y está marcada así.

**«¿Habéis vendido alguna?»**
No. Es una propuesta con coste de producción medido sobre ejecuciones reales, no un negocio en marcha. El precio y el margen son propuestas a validar con el cliente; el coste no.

---

## 8 · Lo que se declara

- **Medido:** el coste de tokens por novela, su desglose por agente, el rango entre configuraciones, y el coste de una regeneración.
- **Estimado y justificado:** infraestructura, reserva de revisiones, comisión de pago, tarifa hora y horas por fase.
- **Propuesto a validar:** el precio de venta y la política de revisiones.
- **Fuera del modelo:** adquisición, marketing y atención al cliente.
