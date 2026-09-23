# Varias sesiones escribiendo identificadores a la vez

Detalle de la regla que `AGENTS.md` § "Varias sesiones a la vez" resume. Se movió aquí para mantener aquel archivo por debajo de su tope de líneas; la regla sigue siendo obligatoria.

**Mirar el último identificador usado no basta con tres sesiones escribiendo.** Entre leer cuál es el último y commitear el propio hay una ventana, y otra sesión publica en ella: es la Regla 6 de `docs/verification.md` aplicada a la numeración. Pasó con `F-39` y `F-40`, que acabaron duplicados con contenidos distintos —exactamente lo que la regla de no renumerar existe para impedir—. Vale cualquiera de las dos disciplinas, y hace falta una:

- **Reservar antes de escribir**: anunciar el identificador a las otras sesiones y dejarlo escrito en su documento antes de desarrollar el contenido, para que quede ocupado.
- **Comprobar al commitear**: volver a mirar los publicados justo antes del commit, no al empezar a redactar.

**Si la colisión ya ocurrió**, el criterio es el mismo que para las specs y aplica a todo identificador publicado (`F-xx`, `MF-xx`, `VER-xx`, `INV-xx`):

1. **El que se publicó primero conserva el número**, y eso lo decide el historial de git, no cuál parezca más importante.
2. **El segundo pasa al siguiente libre.** No se fusionan ni se borra ninguno: son dos hallazgos distintos.
3. **Las referencias cruzadas se actualizan en el mismo commit.** Un identificador movido sin sus citas deja el documento apuntando a otra cosa, que es peor que la colisión.
4. **Lo hace una sola sesión, acordado antes.** Dos renumerando a la vez reproducen el problema que están arreglando.
