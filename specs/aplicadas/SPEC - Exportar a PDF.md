---
id: SPEC-27
titulo: Exportar la novela a PDF
estado: aplicada
aprobada_por: "autor del proyecto, en sesión"
fecha_aprobacion: 2026-09-23
fecha: 2026-09-23
version: 2
fecha_aplicacion: 2026-09-24
commit_de_aplicacion: bd13e36
---

> **Historial.** v1: redactada con la respuesta del autor sobre el PDF por versión
> (2026-09-23), con tres propuestas. v2: el autor confirma `P-1`, `P-2` y `P-3`, que
> pasan a requisitos conservando su identificador de origen. Sin cuestiones abiertas.

# SPEC-27 — Exportar la novela a PDF

## Qué problema resuelve

`EXAMEN.md` exige el PDF de una novela completa en `/ejemplos/novela-ejemplo.pdf`,
y añade: *«Si el formato de lectura elegido es web, se incluye igualmente el PDF
exportado.»* `SPEC-22` §1.2 lo excluía en su tabla **No entra**, con la fila
*«Publicar la obra a un formato de libro»*. Es `EX-09` de
`docs/cobertura-examen.md`.

**Esta spec corrige esa fila en vez de reabrir `SPEC-22`**, que está aprobada y
no cambia en nada más. Al aplicarse, la fila pasa a decir que la interfaz de
lectura no exporta y que la exportación la cubre `SPEC-27`.

## Qué tiene que ser verdad al terminar

- **RF-01.** Se puede exportar a PDF **una versión publicada** de la novela, y
  solo una publicada: la que ha pasado la puerta de `SPEC-30`.
- **RF-02.** El texto de cada capítulo en el PDF es **byte a byte** el del
  borrador que se auditó (`VER-60`). La exportación pone la maquetación y nada
  más: no corrige, no recorta y no une párrafos (`docs/architecture.md` § "El
  ensamblador del manuscrito no corrige nada").
- **RF-03.** Existe `/ejemplos/novela-ejemplo.pdf`, generado con el brief de
  ejemplo del README, y commiteado.
- **RF-04.** **PDF por versión solo si sale gratis del diseño.** El enunciado solo
  pide el de ejemplo y que se conserve la versión anterior; un PDF por versión es
  más de lo pedido. Si no sale gratis, basta el de la última versión.

### Confirmado por el autor (v2)

- **RF-05 (antes `P-1`). El PDF lleva lo que el enunciado pide en los dos formatos**: portada con
  dedicatoria, índice con enlaces internos a cada capítulo, y fichas de
  personajes y lugares con enlaces a los capítulos donde aparecen. *Aparecer*
  significa lo mismo que en la web (`SPEC-22` `RF-44`: `participa_en` y
  `ocurre_en`) y lo calcula el backend.
- **RF-06 (antes `P-2`). El PDF no muestra estados ni hallazgos.** La regla de `CLAUDE.md` —una
  escena se muestra siempre con su estado y sus hallazgos— gobierna la interfaz
  de React, donde alguien decide si da un texto por bueno. El PDF es el regalo,
  no una herramienta de revisión, y como solo se exportan versiones que pasaron
  la puerta (`RF-01`), no puede llevar un capítulo rendido ni una `bloqueante`
  abierta.
- **RF-07 (antes `P-3`). Lo genera el backend** desde el dominio, no la impresión de la página
  web. No depende del frontend, que todavía no existe (`EX-13`), y mantiene fuera
  del navegador el cálculo de qué va en cada ficha.

## Qué queda explícitamente fuera

- La página de «novedades» con enlaces a los capítulos modificados: el enunciado
  la pide solo si el formato de lectura es PDF, y aquí es web.
- Tipografía cuidada, impresión física e ilustraciones (fuera de alcance según el
  enunciado).
- Versiones y regeneración: `SPEC-23`.

## Lo que la gobierna

`EXAMEN.md` § "Novela de ejemplo generada" y §2; `SPEC-22` §1.2 y `RF-44`;
`SPEC-30`; `VER-60`; `CLAUDE.md` § "React".
