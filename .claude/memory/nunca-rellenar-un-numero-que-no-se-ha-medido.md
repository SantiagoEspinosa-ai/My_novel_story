---
name: nunca-rellenar-un-numero-que-no-se-ha-medido
description: "En My_novel_story, un número que no se ha medido nunca se rellena ni se estima en silencio; se dice \"sin medir\", y un resultado negativo se informa tal cual."
metadata: 
  node_type: memory
  pinned: true
  originSessionId: e52256e3-d959-4d0f-be48-c48f62092794
  modified: 2026-09-23T17:09:06.426Z
---

# Nunca rellenar un número que no se ha medido

El usuario de `My_novel_story` ha corregido esta misma cosa en tres ocasiones
distintas, así que es una preferencia estable y no un comentario de paso:

- Cuando registré una delegación pasando `--tokens-out 19000` antes de conocer
  la cifra real (que resultó ser 26.134), me hizo corregirlo en `estado.json` y
  contarlo claramente. Un número inventado que queda escrito ya no se distingue
  de uno medido.
- Al diseñar la vista de Consumo, pidió que las delegaciones sin cifras de
  tokens dijeran **"sin medir"** en vez de pintar un cero, porque un cero se lee
  como un dato y un hueco no.
- Al encargar el experimento de auto-mejora del escritor lo dijo de forma
  general: *"Un resultado negativo es un resultado válido; lo que no vale es un
  resultado inventado."*

En la práctica esto significa tres cosas al trabajar en este proyecto:

1. Si una cantidad no se ha medido, la respuesta y el artefacto dicen que no se
   ha medido. No se interpola, no se redondea desde un caso parecido y no se
   deja un cero por defecto.
2. Si una cifra es un **suelo** y no una medida (por ejemplo, un contador que
   solo sumaba cuando el registro tenía éxito), hay que decir que es un suelo
   allí donde se enseña el número, no solo en una nota al pie.
3. Un experimento que sale plano o peor de lo esperado se informa con sus
   números reales. Falsear o maquillar el resultado para que parezca una mejora
   es peor que no haber hecho el experimento.

La regla también aplica a las hipótesis del propio usuario: cuando propuso que
el fallo de `Content-Length` era por contar caracteres en vez de bytes, lo
correcto fue medirlo, comprobar que no era eso y decírselo, en vez de
implementar el arreglo que él sugería.

## Vale para cualquier dato que se afirme, no solo para cifras

Escribiendo un mensaje a otra sesión cité un hash de commit —`1e4e6b6`— que no
había leído: lo inventé con la forma correcta mientras redactaba. El real era
otro. El usuario pidió que quedara anotado, y con este motivo:

> *"Es un número sin medir con otra cara, y la consecuencia era concreta:
> habrían buscado un commit inexistente. Que quede como recordatorio de que la
> regla vale para cualquier dato que se afirme, no solo para umbrales."*

La otra sesión lo confirmó desde el otro lado: habría ido a buscar ese commit,
no lo habría encontrado, y con cuatro sesiones trabajando sobre la misma rama la
duda siguiente habría sido si el commit se perdió en un merge — un rato largo
perdido por un dato que costaba un `git log` comprobar.

Así que **hashes de commit, identificadores, rutas de fichero, nombres de
función y números de línea se leen antes de escribirlos**, siempre, incluso
cuando se está redactando prosa y no código. Un dato con la forma correcta es
más peligroso que uno obviamente ausente, porque nadie lo duda.

## Un negativo también es una afirmación

El usuario pidió añadir esto, que salió de otra sesión del proyecto: afirmaron
que una función no existía porque su `grep` de definiciones se había quedado en
las doce primeras coincidencias, y la función estaba en la línea 170.

> *"Afirmar que algo no existe tras un grep corto es tan inventado como afirmar
> un valor no leído. Un negativo también es una afirmación, y se comprueba
> igual."*

En la práctica: antes de decir *no existe*, *no hay ninguno*, *nadie lo llama* o
*no está implementado*, hay que haber mirado el árbol entero —`grep -rn` sin
truncar, o la herramienta de búsqueda completa— y no la primera pantalla de
resultados. La sensación de haber buscado no es haber buscado.

## El corolario sobre las decisiones, no solo sobre los números

El usuario amplió la regla al revisar un valor por defecto que yo había elegido
por intuición de coste: excluí un tipo de relación del conjunto de la
regeneración selectiva razonando que «arrastraría media novela», sin haberlo
medido nunca. Su respuesta fue tajante:

> *"Lo que no acepto es excluirlo por intuición de coste cuando el coste se
> puede medir gratis en la siguiente generación."*

De ahí salen dos obligaciones al fijar un valor por defecto o un umbral:

1. **Una intuición de coste no es un argumento si el coste es medible barato.**
   Si basta con ejecutar una consulta más sobre la siguiente generación, la
   decisión no se toma antes de tener ese número.
2. **El estado correcto mientras tanto es «pendiente de medida, con la medida
   definida»** — y definida quiere decir ejecutable, no una frase. Deja escrito
   qué se compara, contra qué y qué se hará con el resultado (por ejemplo: si
   crece en dos, entra sin discusión; si crece en veinte, se habla con el número
   delante). Un «pendiente» sin medida definida es un «no» disfrazado.

Es la misma regla de siempre mirando en la otra dirección: no inventar un número
al informar, y no decidir a partir de un número que nunca se tomó.

## Un número medido sobre un sistema roto no es una medida, y sesga hacia lo cómodo

El usuario señaló esto como lo más importante de un informe entero. Una
generación de la novela se había hecho con tres defectos dentro —la memoria
mezclaba obras, la escena anterior cruzaba capítulos y los hechos se pisaban
entre capítulos—, y alguien iba a usar esa base para medir cuánto arrastra un
cambio.

Su formulación:

> *"Un arrastre pequeño medido ahí no dice que arrastre poco, dice que se
> registró poco. Y sesga hacia la salida más cómoda, que es lo que la hace
> peligrosa."*

De ahí salen dos obligaciones al informar cualquier medida:

1. **Decir en qué dirección sesga, no solo que hay incertidumbre.** «Este número
   es aproximado» no sirve. Hay que decir si sale alto o bajo y por qué, porque
   un sesgo conocido y declarado sigue siendo utilizable y uno callado no.
2. **Desconfiar especialmente cuando el sesgo favorece la opción barata.** Un
   defecto que hace que se registre de menos produce números que recomiendan
   justo la salida que menos trabajo cuesta, y esa coincidencia es lo que
   convierte un número malo en un argumento convincente.

Es la misma familia que el cero de `INV-03`: un valor que parece un resultado
y es la huella de que algo no llegó a ejecutarse.
