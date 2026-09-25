"""Los nombres reales no salen hacia los agentes (`SPEC-34`, `PLAN-34` E1 y E2).

POR QUE EXISTE
--------------
`F-146`: las sesiones delegadas anonimizan los nombres de personas por una politica de la
organizacion que esta fuera del repositorio, y en `R4` no hubo novela. El autor decidio no
sortearla, sino que **los nombres reales no salgan**: el modelo trabaja con nombres
inventados y la base guarda los reales. La sustitucion se hace en la frontera, en los dos
sentidos, y la frontera es `SesionPseudonimizada`: todo lo que llega a un agente pasa por
`llamar(prompt) -> dict`.

UNA PAREJA POR PALABRA, NO POR NOMBRE
-------------------------------------
«Olivia Carranza» son dos parejas, `Olivia→Elena` y `Carranza→Robles` (`RF-08`). Asi cada
forma de `formas_de_nombre` sale sustituida sin guardarla aparte. Las parejas se guardan en
`pseudonimo` (`RF-02`): se eligen una vez y despues se leen.

EXACTA O A LA VISTA
-------------------
La sustitucion es exacta: mayusculas y limites de palabra. Un pseudonimo que vuelve con otra
forma («Elenita») no se restituye a medias: queda en `residuos`, y quien llama lo convierte
en un hallazgo `INV-31` o en un aviso (`RF-04`). Para que un resto se pueda reconocer sin
confundirlo con un nombre real, ningun pseudonimo comparte raiz con otra palabra de la tabla.

EL GENERO
---------
Si «Olivia» llega al Escritor como «Bruno», el texto dira «el». La ficha no tiene genero, asi
que se usa la misma lectura que haria el modelo: un nombre de pila terminado en `a` recibe un
pseudonimo femenino. Punto ciego declarado en `docs/verification.md`.
"""

import hashlib
import re

from app.commons.db.migraciones import PSEUDONIMO_SQL
from app.commons.dominio.destinatario import Pseudonimo
from app.commons.dominio.enumeraciones import TitularDePseudonimo as TP
from app.commons.politica.normalizar import sin_acentos

# Listas fijas de nombres inventados. Ninguno es una palabra comun del castellano, porque la
# restitucion cambia toda aparicion con mayuscula: «Nube» al principio de una frase se
# convertiria en el nombre del perro.
PILA_FEMENINA = (
    "Elena", "Marta", "Irene", "Julia", "Nuria", "Silvia", "Teresa", "Begoña", "Celia",
    "Esther", "Fátima", "Inés", "Lidia", "Maite", "Noelia", "Olga", "Raquel", "Susana",
    "Yolanda", "Ainhoa", "Luisa", "Nerea", "Sonia", "Tamara", "Adela", "Beatriz", "Claudia",
    "Diana", "Lorena", "Mónica", "Patricia", "Sandra", "Verónica", "Alicia", "Cristina",
    "Rebeca", "Miriam", "Judit", "Carlota", "Ana")
PILA_MASCULINA = (
    "Bruno", "Tomás", "Rodrigo", "Gonzalo", "Ernesto", "Fermín", "Germán", "Héctor",
    "Ignacio", "Jacinto", "Leandro", "Marcelo", "Nicolás", "Octavio", "Patricio", "Ramiro",
    "Samuel", "Teodoro", "Ulises", "Valentín", "Adrián", "Camilo", "Damián", "Eusebio",
    "Félix", "Gregorio", "Hugo", "Isidro", "Joaquín", "Lorenzo", "Matías", "Norberto",
    "Óscar", "Rafael", "Tobías", "Vicente", "Julián", "Aurelio", "Emilio", "Gerardo")
APELLIDOS = (
    "Galindo", "Iturbe", "Jiménez", "Lozano", "Medina", "Navarro", "Olmedo", "Quintana",
    "Salcedo", "Toledo", "Urrutia", "Valverde", "Zamora", "Bermejo", "Duarte", "Espinar",
    "Gallardo", "Hidalgo", "Montero", "Ortega", "Roldán", "Tejada", "Vidal", "Aguado",
    "Carrasco", "Delgado", "Ferrer", "Mendoza", "Sandoval", "Villalba", "Echeverría",
    "Cifuentes", "Elizondo", "Garrido", "Maldonado", "Pacheco", "Rebollo", "Solano",
    "Arriaga", "Beltrán")
MASCOTAS = (
    "Bartolo", "Toby", "Kiwi", "Frodo", "Gofio", "Kira", "Lolo", "Otto", "Simba", "Zape",
    "Pipo", "Rulo", "Moka", "Tofe", "Dante", "Nilo", "Coco", "Bimba", "Chusco", "Greta",
    "Lupo", "Milo", "Olfo", "Pancho", "Rocky", "Sultán", "Thor", "Yako", "Lua", "Nuka",
    "Balto", "Draco", "Fosca", "Gumer", "Hachi", "Iker", "Jara", "Kuki", "Laika", "Mambo")

# `RF-07`: lo que sale en lugar de un nombre vetado.
MARCA_DE_VETADO = "[nombre vetado]"

PALABRA = re.compile(r"\w+", re.UNICODE)

# Lo que convierte un pseudonimo en una forma derivada: diminutivos y plurales. **No**
# «-ín» ni «-ina»: «Martín» no es un diminutivo de «Marta», es otro personaje, y marcarlo
# provocaria una reescritura pagada en cada escena donde aparezca.
SUFIJOS_DERIVADOS = ("ita", "ito", "itas", "itos", "ica", "ico", "illa", "illo", "cita",
                     "cito", "ucha", "ucho", "s", "es")


def _plano(palabra):
    return sin_acentos(palabra).casefold()


def _raiz(palabra):
    p = _plano(palabra)
    return p[:-1] if len(p) > 3 else p


def comparten_raiz(a, b) -> bool:
    """Si una de las dos empieza por la raiz de la otra (sin acentos ni mayusculas)."""
    pa, pb = _plano(a), _plano(b)
    return pa.startswith(_raiz(b)) or pb.startswith(_raiz(a))


def palabras_del_nombre(nombre) -> list:
    """Las palabras de un nombre que se sustituyen: las que empiezan por mayuscula. «de» y
    «la» en «María de la Paz» no son de nadie."""
    return [p for p in (nombre or "").split() if len(p) >= 2 and p[0].isupper()]


def _lista_para(titular, palabra, es_la_primera):
    if titular is TP.MASCOTA:
        return MASCOTAS
    if not es_la_primera:
        return APELLIDOS
    return PILA_FEMENINA if _plano(palabra).endswith("a") else PILA_MASCULINA


def _inicio(obra, palabra, n):
    huella = hashlib.sha256("{0}\x00{1}".format(obra, palabra).encode("utf-8")).hexdigest()
    return int(huella[:8], 16) % n


def _patron(palabras):
    """Alternativa exacta, la mas larga primero, con limites de palabra de verdad: `\\b`
    falla junto a una letra acentuada en algunos casos, y `(?<!\\w)` no."""
    if not palabras:
        return None
    alternativas = "|".join(re.escape(p) for p in sorted(palabras, key=len, reverse=True))
    return re.compile(r"(?<!\w)(?:{0})(?!\w)".format(alternativas), re.UNICODE)


class Tabla:
    """Las parejas de una obra. `pares` va de la palabra real al pseudonimo."""

    def __init__(self, pares=None, vetados=None):
        self.pares = dict(pares or {})
        self.vetados = list(vetados or [])

    @property
    def inversa(self):
        return {v: k for k, v in self.pares.items()}

    def _sustituir(self, texto, mapa):
        patron = _patron(mapa)
        return patron.sub(lambda m: mapa[m.group()], texto) if patron else texto

    def ocultar_vetados(self, texto):
        """`RF-07`: cada nombre vetado completo sale como `MARCA_DE_VETADO`."""
        patron = _patron([v for v in self.vetados if v.strip()])
        return patron.sub(MARCA_DE_VETADO, texto) if patron else texto

    def pseudonimizar(self, texto):
        """Lo que sale hacia un agente. Primero los nombres vetados enteros y despues las
        palabras de la tabla: un vetado que comparte pila con el destinatario no se parte."""
        if not isinstance(texto, str):
            return texto
        return self._sustituir(self.ocultar_vetados(texto), self.pares)

    def restituir(self, objeto):
        """Lo que vuelve de un agente: cadenas, listas y diccionarios, sin tocar `medidas`,
        que es del sobre y no del modelo."""
        if isinstance(objeto, str):
            return self._sustituir(objeto, self.inversa)
        if isinstance(objeto, list):
            return [self.restituir(x) for x in objeto]
        if isinstance(objeto, dict):
            return {k: (v if k == "medidas" else self.restituir(v)) for k, v in objeto.items()}
        return objeto

    def residuos(self, objeto, conocidos=()) -> list:
        """`RF-04`: palabras con mayuscula que son un pseudonimo con un sufijo de diminutivo
        o de plural («Elenita», «Elenas») y no se restituyeron. Se buscan en lo ya
        restituido. `conocidos` son los nombres de la obra (los personajes que invento el
        Planificador): uno de ellos nunca es un resto."""
        exactas = set(self.pares) | {p for n in conocidos for p in (n or "").split()}
        encontrados = []
        for texto in _cadenas(objeto):
            for m in PALABRA.finditer(texto):
                palabra = m.group()
                if not palabra[0].isupper() or palabra in exactas:
                    continue
                if any(_es_derivada(palabra, p) for p in self.pares.values()):
                    if palabra not in encontrados:
                        encontrados.append(palabra)
        return encontrados


def _es_derivada(palabra, pseudonimo):
    """«Elenita» de «Elena»: la raiz del pseudonimo (sin su ultima vocal) mas un sufijo."""
    plano, base = _plano(palabra), _plano(pseudonimo)
    raices = {base, base[:-1] if base[-1:] in "aeiou" else base}
    return any(plano == r + s for r in raices for s in SUFIJOS_DERIVADOS)


def _cadenas(objeto):
    if isinstance(objeto, str):
        yield objeto
    elif isinstance(objeto, list):
        for x in objeto:
            yield from _cadenas(x)
    elif isinstance(objeto, dict):
        for k, v in objeto.items():
            if k != "medidas":
                yield from _cadenas(v)


def asegurar_tabla(con):
    with con:
        con.executescript(PSEUDONIMO_SQL)


def de_la_obra(con, obra, vetados=None) -> Tabla:
    """Las parejas guardadas de la obra; una tabla vacia si no tiene, que no sustituye nada."""
    asegurar_tabla(con)
    filas = con.execute("SELECT palabra_real, pseudonimo FROM pseudonimo WHERE obra = ?",
                        (obra,)).fetchall()
    return Tabla({r: p for r, p in filas}, vetados)


def asignar(con, obra, nombres, evitar=()) -> Tabla:
    """Da pseudonimo a cada palabra de `nombres` (`[(nombre, TitularDePseudonimo)]`) que no
    lo tenga ya. Las parejas guardadas no cambian nunca (`RF-02`).

    Se salta cualquier candidato que comparta raiz con una palabra real, con un pseudonimo
    ya dado o con algo de `evitar` (las vetadas y los nombres vetados)."""
    tabla = de_la_obra(con, obra)
    pares = dict(tabla.pares)
    reales = [p for nombre, _ in nombres for p in palabras_del_nombre(nombre)]
    prohibidas = set(reales) | set(pares) | {p for e in evitar for p in (e or "").split()}
    nuevas = []
    for nombre, titular in nombres:
        titular = TP(titular)
        for n, palabra in enumerate(palabras_del_nombre(nombre)):
            if palabra in pares:
                continue
            lista = _lista_para(titular, palabra, n == 0)
            inicio = _inicio(obra, palabra, len(lista))
            for i in range(len(lista)):
                candidato = lista[(inicio + i) % len(lista)]
                ocupadas = prohibidas | set(pares.values())
                if not any(comparten_raiz(candidato, o) for o in ocupadas):
                    pares[palabra] = candidato
                    fila = Pseudonimo(obra=obra, palabra_real=palabra, pseudonimo=candidato,
                                      titular=titular)
                    nuevas.append((fila.obra, fila.palabra_real, fila.pseudonimo,
                                   fila.titular.value))
                    break
            else:
                raise ValueError("no queda ningun pseudonimo libre para una palabra de la "
                                 "obra {0}: faltan nombres en las listas".format(obra))
    if nuevas:
        with con:
            con.executemany("INSERT INTO pseudonimo (obra, palabra_real, pseudonimo, titular) "
                            "VALUES (?, ?, ?, ?)", nuevas)
    return Tabla(pares, tabla.vetados)


def nombres_de_la_ficha(ficha) -> list:
    """Todos los nombres reales de una ficha, con su titular."""
    d = ficha.destinatario
    nombres = []
    if d.nombre:
        nombres.append((d.nombre, TP.DESTINATARIO))
    if ficha.regalado_por:
        nombres.append((ficha.regalado_por, TP.QUIEN_REGALA))
    for e in d.elementos:
        if e.nombre and e.tipo.value in ("persona", "mascota"):
            nombres.append((e.nombre, TP(e.tipo.value)))
    return nombres


def asegurar(con, obra, ficha) -> Tabla:
    """La tabla de la obra, completada con lo que declare la ficha. Es lo que usa la
    generacion con una ficha que no paso por la entrevista (un JSON de la CLI o de la
    evaluacion)."""
    tabla = asignar(con, obra, nombres_de_la_ficha(ficha),
                    evitar=list(ficha.vetadas) + list(ficha.nombres_vetados))
    tabla.vetados = list(ficha.nombres_vetados)
    return tabla


def borrar_de_la_obra(con, obra) -> int:
    """`SPEC-25` `RF-21`: las parejas se borran con la ficha. Devuelve cuantas."""
    asegurar_tabla(con)
    with con:
        return con.execute("DELETE FROM pseudonimo WHERE obra = ?", (obra,)).rowcount


_DE_LA_SESION = ("nombre", "agente", "reglas", "entorno", "herramientas", "anotador",
                 "mcp_fijo", "_ejecutar")


class SesionPseudonimizada:
    """La frontera (`RF-03`, `RF-04`, `RF-07`), con la firma de las otras envolturas:
    `llamar(prompt) -> dict`. El prompt sale pseudonimizado y sin nombres vetados, y la
    respuesta vuelve restituida. Lo que no se pudo restituir queda en `residuos`."""

    def __init__(self, sesion, tabla):
        object.__setattr__(self, "_sesion", sesion)
        object.__setattr__(self, "tabla", tabla)
        object.__setattr__(self, "residuos", [])

    def __getattr__(self, nombre):
        return getattr(self._sesion, nombre)

    def __setattr__(self, nombre, valor):
        if nombre in _DE_LA_SESION:
            setattr(self._sesion, nombre, valor)
        else:
            object.__setattr__(self, nombre, valor)

    def llamar(self, prompt):
        r = self._sesion.llamar(self.tabla.pseudonimizar(prompt))
        restituida = self.tabla.restituir(r)
        object.__setattr__(self, "residuos", self.tabla.residuos(restituida))
        return restituida


def envolver(sesion, tabla):
    """Sin parejas no hay nada que sustituir: la sesion se devuelve tal cual."""
    if not tabla.pares and not tabla.vetados:
        return sesion
    return SesionPseudonimizada(sesion, tabla)
