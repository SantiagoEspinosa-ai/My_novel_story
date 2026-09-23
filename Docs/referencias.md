# Referencias externas — Spec-Driven Development y verificación formal

2026-09-23 · @Santiago Espinosa Domínguez

**Documento de consulta. No es normativo y nada lo cita.** Recoge material recibido en
clase sobre métodos de *Spec-Driven Development* y lenguajes de especificación formal, más
una lectura propia de cómo se relaciona con este repositorio.

Lo que eso significa en la práctica, y conviene dejarlo escrito porque es justo lo que un
documento así invita a hacer mal:

- **No manda sobre nada.** En lo técnico manda `CLAUDE.md`, en lo de dominio
  `Docs/definitions.md` y en cómo se organiza el código `Docs/architecture.md`. Este
  documento no está en esa cadena de precedencia.
- **Ninguna invariante, fila `VER-xx`, spec ni plan puede citarlo como origen.** Una fila
  `VER-xx` cita el documento normativo del que sale; si lo que la justifica está solo aquí,
  la fila no tiene origen y sobra.
- **Adoptar algo de aquí es un cambio que decide algo nuevo**, así que pasa por las tres
  puertas de `AGENTS.md`: spec aprobada, plan aprobado, código. Aparecer en esta lista no
  es una decisión ni media decisión.
- **Las secciones 1 y 2 son el material tal como se recibió.** No están contrastadas contra
  la documentación oficial de cada proyecto, y los enlaces son los que venían con el
  material. La sección 3 es opinión y está marcada como tal.

---

## Sección 1 · Métodos de Spec-Driven Development

### Open source

| Método | Qué es | Enlace |
| --- | --- | --- |
| **GitHub Spec Kit** | CLI oficial de GitHub en Python. Flujo `constitution` → `specify` → `plan` → `tasks` → `implement`. Funciona con más de 30 agentes de código | https://github.com/github/spec-kit |
| **OpenSpec** | Alternativa más ligera, basada en cambios (`propose`, `apply`, `archive`). Sirve para *brownfield* y *greenfield*, sin Python | https://github.com/Fission-AI/OpenSpec |
| **GSD (Get Shit Done)** | *Meta-prompting* e ingeniería de contexto para Claude Code, Codex, Cursor y otros. Apunta a arreglar el *context rot* | https://github.com/gsd-build/get-shit-done |
| **Superpowers** | Método para agentes de código hecho de *skills* componibles. Extrae la spec de la conversación antes de escribir código | https://github.com/obra/superpowers |
| **BMAD-METHOD** | Framework pesado de ciclo completo con varias personas de agente (analista, PM, arquitecto, dev, QA). Potente y con curva de aprendizaje alta | https://github.com/bmad-code-org/BMAD-METHOD |
| **MUSUBI** | Framework de alto rigor con constitución de 9 artículos. Requisitos en formato EARS, diseño con diagramas C4 y ADRs, y validación de cada *feature* contra la constitución. Modos *greenfield* y *brownfield* separados | https://github.com/nahisaho/MUSUBI |
| **Agent OS** | Lee el código existente, escribe las convenciones que de verdad usa y se las pasa al agente. Bueno para *brownfield* | https://github.com/buildermethods/agent-os |

### Comerciales

| Producto | Qué es | Enlace |
| --- | --- | --- |
| **EasySpecs** | Plataforma SDD para bases de código existentes. Genera documentación técnica y funcional del código real (hasta 98 % de cobertura de líneas) y sobre eso crea specs con *Trust Specs* (validadores, casos límite, pruebas de *rollback*), verificadas por una cascada de comprobaciones deterministas y probabilísticas. No atada a proveedor | https://easyspecs.ai |
| **Kiro** (AWS) | IDE *spec-driven* basado en VS Code. Produce requisitos, documentos de diseño y ficheros de *steering*, pero ata a su IDE | — |
| **Tessl** | Plataforma para desarrollo *AI-native* con las specs como artefacto principal | — |
| **BrainGrid** | Planificación y descomposición de specs, agnóstico de agente | — |
| **CodeMySpec** | Se centra en comprobar que el código coincide con la spec | https://codemyspec.com |
| **Augment Code (Cosmos)** | SDD desde el lado del contexto, con un motor persistente que entiende la arquitectura en bases de código grandes y coordina varios agentes | — |

---

## Sección 2 · Lenguajes de especificación y verificación formal

| Lenguaje | Qué es | Dónde se usa | Tendencia | Enlace |
| --- | --- | --- | --- | --- |
| **TLA+** | Especificación y *model checking* | AWS, Microsoft, Oracle, Intel, bases de datos distribuidas | Crecimiento moderado | https://foundation.tlapl.us |
| **Lean 4** | Asistente de pruebas y lenguaje | Matemáticas, AWS, DeepMind, Harmonic | El que más crece | https://lean-lang.org |
| **Rocq** (antes Coq) | Asistente de pruebas | CompCert, academia, criptografía | Estable, pierde peso frente a Lean | https://rocq-prover.org |
| **Isabelle/HOL** | Asistente de pruebas | seL4, academia | Estable | https://isabelle.in.tum.de |
| **Dafny** | Lenguaje verificable, estilo C#/Python | AWS y *benchmarks* de IA | Creciendo | https://dafny.org |
| **SPARK (Ada)** | Subconjunto verificable de Ada | Aeroespacial, defensa, ferroviario | Nicho regulado | https://www.adacore.com/about-spark |
| **B-Method / Event-B** | Especificación por refinamiento | Metro y ferrocarril (Alstom, Siemens) | Legado | https://www.atelierb.eu · http://www.event-b.org |
| **P** | Modelado de máquinas de estados | AWS (S3, DynamoDB) | Creciendo | https://p-org.github.io/P |
| **Alloy** | Especificación ligera | Academia y modelos de datos | Estable | https://alloytools.org |
| **F\*** | Tipos dependientes | Criptografía (HACL\*, en Firefox, Linux y Windows) | Nicho | https://www.fstar-lang.org |
| **Verus** | Verificación de código Rust | Sistemas en Rust, Microsoft Research | Crece rápido desde base pequeña | https://github.com/verus-lang/verus |
| **Kani** | *Model checker* para Rust | AWS y librería estándar de Rust | Creciendo | https://github.com/model-checking/kani |
| **Quint** | Especificación tipo TLA con sintaxis moderna | *Blockchain* y protocolos de consenso | Crece rápido desde base pequeña | https://quint-lang.org · https://github.com/informalsystems/quint |
| **Agda / Idris 2** | Tipos dependientes | Investigación en teoría de tipos | Académico | https://agda.readthedocs.io · https://www.idris-lang.org |
| **Z, VDM, PVS** | Especificación clásica | NASA (PVS) y sistemas industriales heredados | En declive | https://www.overturetool.org (VDM) · https://pvs.csl.sri.com (PVS). Z no tiene web oficial única: es un estándar ISO |

---

## Sección 3 · Lectura propia

> **Esto es opinión, no material de clase.** Está escrito para situar el repositorio en el
> mapa, no para proponer adoptar nada. Ninguna de estas herramientas se ha instalado ni
> probado aquí: la comparación es entre lo que cada una **dice** que hace y lo que este
> repositorio **hace**, y eso es más débil que una medida.

### El mapa

| Método | En qué se parece a lo que ya hacemos | Qué hace que nosotros no |
| --- | --- | --- |
| **GitHub Spec Kit** | Es casi la misma cadena: su `constitution` son `AGENTS.md` y `CLAUDE.md`, su `specify` es `specs/SPEC-NN`, su `plan` es `specs/plans/PLAN-NN` | Sus fases son **comandos que se ejecutan**. Las nuestras son puertas que abre un campo `estado` que rellena una persona: más barato, y más fácil de saltarse sin que salte nada |
| **OpenSpec** | Su ciclo `propose` → `apply` → `archive` es literalmente nuestro `borrador` → `aprobada` → `aplicada` con `git mv` a `specs/aplicadas/` | Poco. Es la misma idea con herramienta detrás |
| **GSD** | El *context rot* es nuestro problema central, y el presupuesto por niveles de `CLAUDE.md` con su orden de recorte es nuestra respuesta | Ataca el contexto **del agente que escribe código**. El nuestro es el contexto del agente que escribe **la novela**: mismo problema, distinto objeto |
| **Superpowers** | Dos cosas: *skills* componibles versionadas —lo nuestro en `.agents/skills/`— y **extraer la spec de la conversación antes de escribir código**, que es nuestra regla de preguntar antes de escribir una spec | Formaliza esa extracción como paso del método. Aquí depende de que la persona se acuerde de preguntar |
| **BMAD-METHOD** | Tenemos diez agentes con habilidades separadas en `Docs/architecture.md` | Sus personas producen **la spec**; las nuestras producen **la novela**. No tenemos ningún agente cuyo trabajo sea especificar, revisar o hacer QA del propio proyecto |
| **MUSUBI** | Constitución con artículos ≈ las reglas de `AGENTS.md`; ADRs ≈ las decisiones `A-01`…`A-09` con su alternativa descartada | **Valida cada *feature* contra la constitución.** Aquí eso lo hace una persona leyendo, más la *skill* `coherencia-docs`. No hay comprobación automática de que un cambio respete las reglas del proyecto |
| **Agent OS** | — | Va en **dirección contraria**: lee el código y escribe las convenciones que de verdad usa. Nosotros vamos de documento a código, y nada comprueba el viaje de vuelta |
| **EasySpecs** | Su cascada determinista → probabilística es nuestro reparto regla → juez: la regla decide primero y el juez solo desempata lo que la regla no ve (`INV-03`, `INV-11`, `INV-14`) | Mide **cobertura de líneas** de lo que documenta. Nosotros no tenemos ninguna medida de cuánto del sistema está descrito: la tabla de recuentos de `Docs/verification.md` cuenta filas escritas, que no es lo mismo |
| **Kiro** | Sus ficheros de *steering* son `CLAUDE.md` y `AGENTS.md` | Nada que compense atarse a un IDE |
| **CodeMySpec** | — | **Comprueba que el código coincide con la spec.** Es nuestro hueco más claro: `PC-1` dice que ninguna comprobación que no ejecute el sistema ve la ejecución, y lo comparten doce validadores |
| **Augment Code (Cosmos)** | — | Contexto persistente sobre una base de código grande. Aquí no aplica todavía: el código es pequeño y lo grande es la novela |

**Lo que el mapa dice en una frase.** La mitad de estos métodos describe lo que este
repositorio ya hace, lo cual es tranquilizador y poco útil. Lo que varios de ellos tienen y
nosotros no es **la vuelta**: comprobar automáticamente que el código sigue pareciéndose a
lo que la spec dice. Eso ya está diagnosticado aquí como `PC-1`, así que la lista no
descubre el hueco: solo confirma que es el hueco que la industria considera importante.

### EARS: ¿aporta algo que nuestra forma no?

**Poco, y lo poco que aporta ya lo cubrimos por otra vía; lo que nosotros tenemos y EARS no
pide vale más.**

EARS obliga a que cada requisito diga su disparador: *cuando* ocurre X, *mientras* dura el
estado Y, *si* pasa lo indeseado Z. Es una gramática, y sirve para cazar el requisito que no
dice cuándo aplica. Nuestros `RF-xx` ya lo dicen, solo que en prosa: `RF-19` es un
*mientras* —ninguna escena posterior se genera mientras la anterior no esté `consolidada`—,
`RF-26` es un *si* con su consecuencia —si tras agotar el recorte no cabe, el trabajo
falla—, y `RF-14` es un *si* con dos ramas según la severidad. Pasarlos a plantilla los
haría más uniformes, no más verdaderos.

Lo que nuestra forma tiene y EARS no contempla es la **columna de invariante**: cada `RF`
cita por identificador la `INV-xx` o la `VER-xx` que lo gobierna, y esa trazabilidad es la
que permite preguntar *"¿quién comprueba esto?"* y que la respuesta sea un nombre o un
hueco visible. EARS no pide nada de eso.

Y contra el único fallo real de redacción que este repositorio ha tenido, EARS no habría
hecho nada: `F-31` —`INV-03` mirando `revelaciones` donde debía mirar `acciones`— era una
confusión sobre **qué significa** revelar, no sobre cuándo aplica la regla. Una plantilla
bien rellenada con el concepto equivocado sigue estando equivocada.

**Sobre los ADRs el matiz va al revés, y ahí sí falta algo.** Nuestras `A-01`…`A-09` llevan
la alternativa descartada, que es el corazón de un ADR, pero no llevan **fecha ni estado**,
así que no se puede saber cuándo se decidió ni si sigue vigente. `Docs/decisions/` está
reservado en `AGENTS.md` justo para eso y no existe todavía. El hueco es ese, no el formato.

### P: ¿haría más verificables nuestras tres máquinas de estados?

**Hoy es desproporcionado, y el motivo no es el tamaño sino que no cerraría el punto ciego
que importa.**

Las tres máquinas son pequeñas: `estado_de_escena` tiene ocho estados y diez transiciones,
`estado_de_capitulo` tiene dos estados y una transición, y los estados de un trabajo son
siete. Ese espacio cabe entero en una prueba, que es lo que `VER-28` hace: explorar
exhaustivamente que no hay camino de `planificada` a `consolidada` sin pasar por
`en_verificacion`. Para eso, P no añade nada que el código no dé ya.

El problema es que `VER-28` **verifica el modelo, no la implementación** —está escrito en su
propia fila y en `PC-1`—, y un `UPDATE` directo a la base se lo salta. Escribir las mismas
máquinas en P produciría un segundo artefacto con exactamente el mismo punto ciego, y uno
más que puede derivar respecto al código sin que nadie lo note. Es lo que la Regla 2 de
`Docs/verification.md` ya rechaza: un validador cuyo punto ciego es idéntico al de otro no
cubre nada nuevo.

**Dónde dejaría de ser desproporcionado, y merece recordarlo cuando llegue:** P y TLA+ no
brillan enumerando transiciones, sino explorando **entrelazados de concurrencia**, y ahí sí
hay riesgo real en la tabla de trabajos. `abandonado` significa que un worker lo tomó y no
se supo más; `esperando_presupuesto` y `detenido_por_presupuesto` dependen de un techo
global compartido. Dos workers compitiendo por el mismo trabajo o por la misma reserva
producen entrelazados que una prueba exhaustiva escrita a mano no cubre, porque no se
escriben solos. Si algún día hay más de un worker, la máquina que valdría la pena modelar
es **la del trabajo**, no la de la escena.
