# Fixture roto a proposito

Reproduce los dos defectos reales de literales: los estados en PascalCase, que
es como estaba el diagrama de ciclo de vida, y un valor con tilde donde la tabla
lo tiene sin ella.

```mermaid
stateDiagram-v2
  [*] --> Planificada
  Planificada --> Generada: modelo escribe
  Generada --> EnVerificacion: puerta
  EnVerificacion --> EnRevision: juez marca
  EnVerificacion --> Aceptada: pasa todo
```

Y la fuente del miedo de esta obra es `pérdida_de_control`, escrita con tilde.
