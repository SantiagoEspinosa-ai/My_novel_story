# Fixture roto a proposito

Tabla de transiciones con un atajo: `generada` va directa a `aceptada` sin pasar
por `en_verificacion`. Sirve para demostrar que VER-28 lo caza.

| Transicion | Quien la dispara | Condicion |
| --- | --- | --- |
| `planificada` → `generada` | Worker | El Escritor devuelve borrador y delta |
| `generada` → `en_verificacion` | Orquestador | Automatica |
| `generada` → `aceptada` | Orquestador | ATAJO: no deberia existir |
| `en_verificacion` → `rechazada` | Verificador de reglas | Falla una bloqueante |
| `en_verificacion` → `aceptada` | Orquestador | Pasa todas las puertas |
| `rechazada` → `generada` | Cliente de la API | Regeneracion |
| `aceptada` → `consolidada` | Consolidador | Delta aplicado sin conflicto |
