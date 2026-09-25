# presentacion/

Material de la presentación del proyecto. **Idioma elegido: castellano.**

## Contenido

| Fichero | Qué es | De dónde sale |
| --- | --- | --- |
| `anexo-enunciado.pdf` | El enunciado del examen | [`EXAMEN.md`](../EXAMEN.md) |
| `anexo-roadmap-costes.pdf` | El roadmap de reducción de coste por tokens | [`ROADMAP-COSTES.md`](../ROADMAP-COSTES.md) |

Los PDF se generaron el 2026-09-25 desde los `.md` de la raíz. La conversión usa `fpdf2` y la fuente DejaVu que el backend ya lleva para exportar las novelas (`backend/app/features/manuscrito/fuentes/`). Si cambia el `.md`, hay que regenerar su PDF: la fuente de verdad es el `.md`, no el PDF.

Los datos para montar el deck, cada uno con su fuente, están en [`docs/presentacion/datos.md`](../docs/presentacion/datos.md).

## Lo que falta todavía

- **El deck en PDF.**
- **El deck en formato editable** (`.pptx` o equivalente).
- **El vídeo de demo.** `EXAMEN.md` lo pide aquí, en `presentacion/`, o enlazado desde este `README.md` si supera el límite de tamaño de GitHub.
