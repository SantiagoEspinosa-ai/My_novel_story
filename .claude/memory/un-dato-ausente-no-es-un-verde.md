---
name: un-dato-ausente-no-es-un-verde
description: "En My_novel_story una comprobación que se salta por falta de un dato tiene que decirlo, no callarse, y al encontrar un caso hay que barrer el patrón entero."
metadata: 
  node_type: memory
  pinned: false
  originSessionId: 2eabcf0f-cd25-4d1c-93b5-491cc4cee37b
  modified: 2026-09-23T15:19:47.553Z
---

# Una comprobación sin su dato está ausente, no en verde

El usuario lo formuló así al revisar por qué `INV-04` no detectó que el modelo
había escrito una escena sobre otro personaje del planificado:

> "Una invariante que se salta en silencio cuando le falta un campo está
> ausente, no en verde, y desde fuera se ven igual. `INV-04` tiene que fallar si
> el campo que necesita no está, no callarse."

Esto va más allá de las invariantes del harness: cualquier comprobación cuyo
cuerpo esté guardado por un `if campo:` pasa en verde cuando el campo falta, y
un informe que dice "sin hallazgos" no distingue entre *se comprobó y está bien*
y *no se comprobó*.

## Cómo se implementa aquí

El proyecto ya tenía el mecanismo para el caso vecino —un juez que devuelve una
salida ilegible produce un `Hallazgo` en estado `sin_veredicto`, no un pase— y
la regla es reutilizarlo en vez de inventar otro: **un verificador que no
contesta es un agujero en la validación, y da igual que la causa sea una salida
ilegible o un campo que nadie rellenó.**

El criterio de qué campo es imprescindible **no lo decide el código de la
comprobación**: lo decide el documento de dominio, que marca en negrita los
atributos obligatorios. Un campo opcional ausente es legítimo y no debe producir
nada, o el mecanismo se convierte en ruido y se aprende a ignorarlo.

## Y hay que barrer el patrón, no arreglar el caso

El usuario añadió: *"Mira si hay más invariantes condicionales al mismo patrón —
sospecho que no es la única."* Tenía razón: había tres. Cuando aparece un defecto
de esta clase, el encargo no es corregir la instancia que se vio, sino recorrer
todo el módulo buscando la misma forma. Es la misma exigencia que su regla de
elevar la causa de fondo a principio en vez de parchear el caso.
