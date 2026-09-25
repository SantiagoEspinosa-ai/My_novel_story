---
id: SPEC-45
titulo: El cambio del lector se aplica desde la web, y su error se entiende
estado: aprobada
aprobada_por: "autor del proyecto, en sesión: «La petición de cambio desde la web falla con NoSePuedeRegenerar: es F-126 […] Arréglalo […] Dale al worker los mismos agentes que usa pedir_cambio.py. Y el mensaje de error que ve el lector es de programador. Que diga algo que se entienda, con el detalle técnico solo en /admin.»"
fecha_aprobacion: 2026-09-25
fecha: 2026-09-25
version: 1
---

# SPEC-45 — El cambio del lector desde la web

## Qué problema resuelve

`F-126`: `POST /obras/{id}/cambios` encola la cascada de `SPEC-23`, pero el worker de la API la lanza sin agentes. La cascada se niega antes de escribir nada, con `NoSePuedeRegenerar`. El cambio propagado solo funciona desde la terminal (`backend/pedir_cambio.py`).

`EXAMEN.md` pide la demo de ese cambio como evidencia, y en la web el lector ve el motivo tal cual lo escribió el código: «NoSePuedeRegenerar: sin agentes no se puede escribir: el worker de la API…».

`F-126` dejaba abierta una pregunta: quién confirma el gasto desde la web. La respuesta la dio `SPEC-33` para la generación, y vale igual aquí: el aviso de la propuesta más el techo de gasto de la web.

## Qué tiene que ser verdad al terminar

- **RF-01 · El worker de la API aplica el cambio con los mismos agentes que `pedir_cambio.py`:**
  - los cinco de la novela regalo (`regalo.agentes`), con su coste anotado en el libro de la base (`SPEC-33` `RF-18`);
  - Lean para la puerta;
  - la ficha de la base;
  - el `sistema.json` de la web.
- **RF-02 · Con lo gastado en el techo, no se encola.** Pedir el cambio responde `409` y el lector ve por qué, como al lanzar una novela (`SPEC-33` `RF-13`).
- **RF-03 · El lector ve un mensaje que se entiende.** Si el cambio no se pudo aplicar, se le dice:
  - que no se aplicó;
  - que la novela sigue como estaba (`D-2`: la versión anterior sigue vigente);
  - que quien administra la web tiene el detalle.

  Nunca ve el nombre de una excepción ni un identificador interno.
- **RF-04 · El detalle técnico está en la administración.** La página de cada novela en `/admin` lista los cambios pedidos, cada uno con:
  - el texto del lector;
  - cuándo se pidió;
  - el estado de su trabajo;
  - el motivo técnico, si falló.

## Qué queda explícitamente fuera

- Regenerar una novela entregada sin ficha (`F-91`).
- Otra salida que no sea la `cascada`.

## Lo que la gobierna

`SPEC-23` (`D-2`, `RF-51`…`RF-55`), `SPEC-33` `RF-12`, `RF-13`, `RF-18`, `SPEC-43` (la lectura es para el lector), `F-126`.
