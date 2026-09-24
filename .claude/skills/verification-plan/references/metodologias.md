# Catálogo de metodologías de verificación

Inventario de metodologías de verificación para código generado por IA y
sistemas de agentes, cada una con su definición en una frase y un enlace a la
explicación de la metodología (no a la página de un producto).

Procedencia: *Verification Methodologies — Reference Sheet*,
`https://claude.ai/artifact/Rass3RVfaN5KSJDdG2FQhR`. Los nombres se conservan en
inglés porque es como aparecen en la literatura y en las herramientas; la
definición está traducida.

## Nivel artefacto — ¿es correcto el código?

| Metodología | Definición | Explicación |
| --- | --- | --- |
| **Type checking** | Comprobación automática de que los valores se usan de forma consistente con lo que las operaciones esperan de ellos | [Type system — Wikipedia](https://en.wikipedia.org/wiki/Type_system) |
| **Static analysis / SAST** | Escanear el código fuente sin ejecutarlo, para contrastarlo con patrones conocidos como malos | [Static program analysis — Wikipedia](https://en.wikipedia.org/wiki/Static_program_analysis) |
| **Symbolic execution** | Ejecutar el código con entradas simbólicas para derivar las condiciones exactas de fallo mediante un solucionador SMT | [Symbolic execution — Wikipedia](https://en.wikipedia.org/wiki/Symbolic_execution) |
| **Formal verification / theorem proving** | Demostrar matemáticamente que el código satisface una especificación para todas las entradas posibles | [Formal verification — Wikipedia](https://en.wikipedia.org/wiki/Formal_verification) |
| **Unit / integration testing** | Comprobar el comportamiento contra entradas de ejemplo concretas y sus salidas esperadas | [Unit testing — Wikipedia](https://en.wikipedia.org/wiki/Unit_testing) |
| **Property-based testing** | Especificar una propiedad general y generar muchas entradas buscando una violación | [QuickCheck — Claessen & Hughes, 2000](https://www.cs.tufts.edu/~nr/cs257/archive/john-hughes/quick.pdf) |
| **Mutation testing** | Introducir errores pequeños a propósito para comprobar si la batería de pruebas los caza | [Mutation testing — Wikipedia](https://en.wikipedia.org/wiki/Mutation_testing) |
| **Contract testing** | Verificar que la interfaz entre dos servicios se mantiene consistente, con independencia de sus interioridades | [Contract Test — Martin Fowler](https://martinfowler.com/bliki/ContractTest.html) |

## Nivel proceso — ¿se comporta el agente de forma fiable?

| Metodología | Definición | Explicación |
| --- | --- | --- |
| **Runtime observability / tracing** | Instrumentar un agente para que su trayectoria sea visible y consultable a posteriori | [Observability primer — OpenTelemetry](https://opentelemetry.io/docs/concepts/observability-primer/) |
| **Evals** | Pruebas estructuradas del comportamiento del agente contra un conjunto de datos y un método de puntuación | [HELM — Liang et al., 2022](https://arxiv.org/abs/2211.09110) |
| **Sandboxed execution** | Ejecutar el código del agente en un entorno aislado para que las acciones malas fallen de forma segura | [Sandbox — Wikipedia](https://en.wikipedia.org/wiki/Sandbox_(computer_security)) |
| **Guardrails** | Políticas y filtros que restringen qué acciones puede producir un agente | [AI Risk Management Framework — NIST](https://www.nist.gov/itl/ai-risk-management-framework) |
| **Human-in-the-loop review** | Una persona aprueba, rechaza o edita las acciones de alta consecuencia del agente | [Human-in-the-loop — Wikipedia](https://en.wikipedia.org/wiki/Human-in-the-loop) |
| **Multi-agent verification** | Patrones de crítica, debate, autoconsistencia, reflexión o ensemble que comprueban la salida del modelo | [AI Safety via Debate — Irving, Christiano, Amodei, 2018](https://arxiv.org/abs/1805.00899) |
| **CI/CD integration** | Hacer pasar los cambios generados por el agente por la misma tubería que los escritos por personas | [Continuous integration — Wikipedia](https://en.wikipedia.org/wiki/Continuous_integration) |
| **Progressive rollout** | Desplegar un cambio a un porcentaje pequeño del tráfico detrás de un flag antes del despliegue completo | [Feature toggle — Wikipedia](https://en.wikipedia.org/wiki/Feature_toggle) |
| **Red-teaming / adversarial testing** | Sondear deliberadamente en busca de fallos bajo un modelo de amenaza adversario | [OWASP Top 10 for LLM Applications](https://owasp.org/www-project-top-10-for-large-language-model-applications/) |
| **Model checking** | Explorar exhaustivamente los estados y transiciones alcanzables de un agente para verificar invariantes | [Model checking — Wikipedia](https://en.wikipedia.org/wiki/Model_checking) |

## Marco de clasificación

| Método | Definición | Explicación |
| --- | --- | --- |
| **T / A / I / D / U (Trust Spec)** | Clasificación de cada requisito en Test, Analysis, Inspection, Demonstration o Unverifiable | [Verification and validation — Wikipedia](https://en.wikipedia.org/wiki/Verification_and_validation) |

## Nota de la fuente

El property-based testing y los evals no tienen una referencia fundacional
neutra única como sí la tiene la verificación formal. Los enlaces de arriba
apuntan al artículo que introdujo o formalizó cada metodología —QuickCheck para
el primero, HELM para los segundos—, que no es la única elección posible.

## Cómo elegir: de lo barato a lo caro

Orden de coste creciente dentro del nivel artefacto. Sube un escalón solo
cuando el anterior no alcanza:

```
type checking  →  static analysis  →  unit/integration tests
               →  contract testing (si cruza un límite de servicio)
               →  property-based testing (si el espacio de entradas es grande)
               →  mutation testing (si sospechas de la batería de pruebas)
               →  symbolic execution / formal verification (si el fallo es caro de verdad)
```

En el nivel proceso el orden no es de coste sino de momento: observabilidad y
guardrails son permanentes, los evals son periódicos, el red-teaming es puntual
y el progressive rollout ocurre en el despliegue.
