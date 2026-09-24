"""El contrato congelado entre el backend y el frontend (`SPEC-22` `RF-31`..`RF-35`, `RF-57`).

QUE HACE
--------
Genera el esquema OpenAPI que FastAPI deriva de `backend/app/main.py`, con las claves
ordenadas, y lo compara con `contrato/openapi.json`, que es **el contrato**: lo que el
frontend puede suponer del backend es lo que ahi esta escrito, y nada mas (`RF-31`).

    python harness/documentos/contrato.py              # compara; sale con 1 si difiere
    python harness/documentos/contrato.py --escribir   # regenera el congelado

POR QUE UNA DIFERENCIA ES UN FALLO Y NO UN AVISO
-------------------------------------------------
Un aviso que nadie lee deja el contrato moverse de un lado sin que el otro se entere
(`MF-29`). Cada diferencia sale con **operacion**, **campo** (puntero JSON) y
**direccion** —anadido, quitado o cambiado— (`RF-32`), porque "el esquema cambio" no dice
que arreglar. Regenerar es un acto deliberado y va en el mismo commit que el cambio de la
API (`RF-33`).

POR QUE VIVE EN `harness/documentos/`
--------------------------------------
Cruza la frontera: no es una prueba del backend ni del frontend (`SPEC-22` §3.2.1,
`PLAN-22` DP-1). Corre en local, porque no hay CI (`PCF-6`).
"""

import copy
import json
import sys
from dataclasses import dataclass
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent.parent
RUTA_CONGELADO = RAIZ / "contrato" / "openapi.json"
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

ANADIDO = "anadido"
QUITADO = "quitado"
CAMBIADO = "cambiado"
_METODOS = ("get", "put", "post", "delete", "patch", "options", "head", "trace")


@dataclass(frozen=True)
class Diferencia:
    operacion: str
    campo: str
    direccion: str
    antes: object = None
    despues: object = None

    def __str__(self):
        detalle = ""
        if self.direccion == CAMBIADO:
            detalle = ": {0!r} -> {1!r}".format(self.antes, self.despues)
        return "[{0}] {1} {2}{3}".format(self.direccion, self.operacion, self.campo, detalle)


def generar():
    """El esquema del backend de hoy. Copia profunda: FastAPI cachea el suyo."""
    from app.main import app
    app.openapi_schema = None
    return copy.deepcopy(app.openapi())


def serializar(esquema) -> str:
    """Claves ordenadas y fin de linea fijo: dos generaciones son identicas byte a byte."""
    return json.dumps(esquema, sort_keys=True, indent=2, ensure_ascii=False) + "\n"


def leer_congelado():
    return json.loads(RUTA_CONGELADO.read_text(encoding="utf-8"))


def escribir_congelado(esquema=None):
    esquema = generar() if esquema is None else esquema
    RUTA_CONGELADO.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_CONGELADO, "w", encoding="utf-8", newline="\n") as f:
        f.write(serializar(esquema))


def _escapar(clave):
    return str(clave).replace("~", "~0").replace("/", "~1")


def _refs(nodo, vistos):
    if isinstance(nodo, dict):
        ref = nodo.get("$ref")
        if isinstance(ref, str) and ref.startswith("#/components/schemas/"):
            vistos.add(ref.rsplit("/", 1)[1])
        for v in nodo.values():
            _refs(v, vistos)
    elif isinstance(nodo, list):
        for v in nodo:
            _refs(v, vistos)
    return vistos


def _usos_de_esquemas(esquema):
    """`{nombre_de_esquema: {operaciones que lo usan}}`, siguiendo las referencias."""
    componentes = (esquema.get("components") or {}).get("schemas") or {}
    usos = {}
    for ruta, metodos in (esquema.get("paths") or {}).items():
        for metodo, op in metodos.items():
            if metodo not in _METODOS:
                continue
            nombre_op = "{0} {1}".format(metodo.upper(), ruta)
            pendientes, vistos = list(_refs(op, set())), set()
            while pendientes:
                n = pendientes.pop()
                if n in vistos:
                    continue
                vistos.add(n)
                pendientes.extend(_refs(componentes.get(n, {}), set()) - vistos)
            for n in vistos:
                usos.setdefault(n, set()).add(nombre_op)
    return usos


def _operacion(puntero, usos):
    partes = puntero.split("/")[1:]
    if len(partes) >= 3 and partes[0] == "paths" and partes[2] in _METODOS:
        ruta = partes[1].replace("~1", "/").replace("~0", "~")
        return "{0} {1}".format(partes[2].upper(), ruta)
    if len(partes) >= 2 and partes[0] == "paths":
        return "* " + partes[1].replace("~1", "/").replace("~0", "~")
    if len(partes) >= 3 and partes[:2] == ["components", "schemas"]:
        ops = sorted(usos.get(partes[2], ()))
        return ", ".join(ops) if ops else "(esquema {0}, sin operacion)".format(partes[2])
    return "(documento)"


def _recorrer(a, b, puntero, salida):
    if isinstance(a, dict) and isinstance(b, dict):
        for k in sorted(set(a) | set(b), key=str):
            hijo = "{0}/{1}".format(puntero, _escapar(k))
            if k not in b:
                salida.append((hijo, QUITADO, a[k], None))
            elif k not in a:
                salida.append((hijo, ANADIDO, None, b[k]))
            else:
                _recorrer(a[k], b[k], hijo, salida)
    elif a != b:
        salida.append((puntero, CAMBIADO, a, b))


def comparar(congelado, actual):
    """Todas las diferencias, del congelado (antes) al backend de hoy (despues)."""
    crudas = []
    _recorrer(congelado, actual, "", crudas)
    # Una ruta entera anadida o quitada se dice operacion a operacion: "cambio /cosas"
    # no dice si lo que aparecio es un GET o un POST.
    expandidas = []
    for p, d, a, b in crudas:
        valor = a if d == QUITADO else b
        partes = p.split("/")[1:]
        if d != CAMBIADO and len(partes) == 2 and partes[0] == "paths" and isinstance(valor, dict):
            for metodo in sorted(m for m in valor if m in _METODOS):
                expandidas.append(("{0}/{1}".format(p, metodo), d,
                                   valor[metodo] if d == QUITADO else None,
                                   valor[metodo] if d == ANADIDO else None))
        else:
            expandidas.append((p, d, a, b))
    crudas = expandidas
    usos = _usos_de_esquemas(congelado)
    for n, ops in _usos_de_esquemas(actual).items():
        usos.setdefault(n, set()).update(ops)
    return [Diferencia(_operacion(p, usos), p, d, a, b) for p, d, a, b in crudas]


# --- Lo que el contrato significa (`RF-34`, `RF-35`, `RF-57`) -----------------------------

RUTA_DEFINICIONES = RAIZ / "docs" / "definitions.md"
RUTA_ARQUITECTURA = RAIZ / "docs" / "architecture.md"
# El unico vocabulario que no es dominio: se declara donde vive su infraestructura, y
# `docs/definitions.md` lo avisa (`PLAN-22` E14).
SECCION_DE_TRABAJOS = "### Los estados de un trabajo"
RUTA_SISTEMA = RAIZ / "backend" / "config" / "sistema.json"
_NUMERICOS = {"integer", "number"}


def vocabularios_de_definitions(ruta=RUTA_DEFINICIONES):
    """`{nombre_de_la_enumeracion: [literales]}`, leidos de la tabla de `definitions.md`.

    Se leen del documento y no de `commons/dominio/enumeraciones.py`: comparar el
    congelado con los `Enum` del backend seria comparar el backend consigo mismo
    (Regla 3). Las filas tachadas son obsoletas y no cuentan.
    """
    vocabularios = {}
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if not linea.startswith("| `"):
            continue
        celdas = [c.strip() for c in linea.strip().strip("|").split("|")]
        if len(celdas) != 3:
            continue
        nombre = celdas[0].strip("`")
        valores = celdas[2].split("(")[0].replace("\\_", "_")
        vocabularios[nombre] = [v.strip() for v in valores.split(",") if v.strip()]
    if ruta == RUTA_DEFINICIONES:
        vocabularios["estado_de_trabajo"] = estados_de_trabajo()
    return vocabularios


def estados_de_trabajo(ruta=RUTA_ARQUITECTURA):
    """Los literales de `estado_de_trabajo`, de la **primera** tabla de
    `docs/architecture.md` § "Los estados de un trabajo" (la de estados; la de
    transiciones va despues): la primera celda de cada fila, en su orden."""
    literales, dentro = [], False
    for linea in ruta.read_text(encoding="utf-8").splitlines():
        if linea.startswith("#"):
            dentro = linea.strip() == SECCION_DE_TRABAJOS
            continue
        if not dentro:
            continue
        if linea.startswith("| `"):
            literales.append(linea.split("|")[1].strip().strip("`"))
        elif literales and not linea.startswith("|"):
            break
    return literales


def _snake(nombre):
    salida = []
    for i, c in enumerate(nombre):
        if c.isupper() and i:
            salida.append("_")
        salida.append(c.lower())
    return "".join(salida)


def nombres_de_configuracion(ruta=RUTA_SISTEMA):
    """Los nombres de `config/sistema.json` que no pueden cruzar el contrato (`RF-57`).

    Las secciones y las claves de sus topes, presupuesto y umbrales. **No** los nombres de
    agente de `modelos` ni las opciones de `extensiones`, que son palabras del dominio
    (`corta` es un literal de `extension_de_capitulo`); tampoco las claves de cada franja
    (`nombre`, `desde`, `hasta`), demasiado genericas para decir nada.
    """
    sistema = json.loads(ruta.read_text(encoding="utf-8"))
    nombres = set(sistema)
    for seccion in ("topes", "presupuesto", "edicion", "contradicciones"):
        if isinstance(sistema.get(seccion), dict):
            nombres.update(sistema[seccion])
    return nombres


def _propiedades(esquema):
    """`(donde, nombre, subesquema)` de cada propiedad de cada esquema, con anidados."""
    def bajar(nodo, donde):
        if isinstance(nodo, dict):
            for nombre, sub in (nodo.get("properties") or {}).items():
                yield donde, nombre, sub
                yield from bajar(sub, "{0}.{1}".format(donde, nombre))
            for clave in ("items", "additionalProperties"):
                if isinstance(nodo.get(clave), dict):
                    yield from bajar(nodo[clave], donde)
            for clave in ("anyOf", "oneOf", "allOf"):
                for sub in nodo.get(clave) or []:
                    yield from bajar(sub, donde)
    for n, sc in ((esquema.get("components") or {}).get("schemas") or {}).items():
        yield from bajar(sc, n)
    for ruta, metodos in (esquema.get("paths") or {}).items():
        for metodo, op in metodos.items():
            if metodo not in _METODOS:
                continue
            for codigo, r in (op.get("responses") or {}).items():
                for tipo in (r.get("content") or {}).values():
                    yield from bajar(tipo.get("schema") or {},
                                     "{0} {1} {2}".format(metodo.upper(), ruta, codigo))


def _alternativas(sub):
    for clave in ("anyOf", "oneOf"):
        if sub.get(clave):
            return list(sub[clave])
    return [sub]


def _tipos(sub, componentes):
    tipos = set()
    for alt in _alternativas(sub):
        ref = alt.get("$ref", "")
        if ref:
            alt = componentes.get(ref.rsplit("/", 1)[1], {})
        t = alt.get("type")
        tipos.update(t if isinstance(t, list) else [t] if t else [])
    return tipos


def _es_enumeracion(sub, componentes):
    alts = [a for a in _alternativas(sub) if a.get("type") != "null"]
    if not alts:
        return False
    for a in alts:
        ref = a.get("$ref", "")
        destino = componentes.get(ref.rsplit("/", 1)[1], {}) if ref else a
        if "enum" not in destino and "const" not in destino:
            return False
    return True


def _debe_ser_enumeracion(nombre):
    return nombre == "severidad" or nombre.startswith("estado")


def comprobar_significado(esquema, vocabularios=None, configuracion=None):
    """Lo que el congelado tiene que **decir**, ademas de coincidir. Devuelve los fallos.

    1. Todo `estado*` y toda `severidad` viajan como enumeracion, no como cadena libre, y
       cada enumeracion lleva **exactamente** los literales de su tabla en
       `docs/definitions.md` (`RF-34`).
    2. Ningun campo admite a la vez un numero y una cadena: si los admite, la interfaz
       acierta pintando lo que le llega y el dato miente (`RF-35`).
    3. Ninguna propiedad se llama como la configuracion del sistema (`RF-57`).

    **Punto ciego:** mira nombres y tipos, no sentido. Un campo `modelo_usado` con el
    nombre del modelo dentro pasa, porque no se llama como ninguna clave de
    `sistema.json`.
    """
    vocabularios = vocabularios_de_definitions() if vocabularios is None else vocabularios
    configuracion = nombres_de_configuracion() if configuracion is None else configuracion
    componentes = (esquema.get("components") or {}).get("schemas") or {}
    fallos = []
    for donde, nombre, sub in _propiedades(esquema):
        if _debe_ser_enumeracion(nombre) and not _es_enumeracion(sub, componentes):
            fallos.append("{0}.{1}: un estado viaja como enumeracion con los literales de "
                          "definitions, no como cadena libre (RF-34)".format(donde, nombre))
        tipos = _tipos(sub, componentes)
        if tipos & _NUMERICOS and "string" in tipos:
            fallos.append("{0}.{1}: admite numero y cadena a la vez, dos lecturas para el "
                          "mismo campo (RF-35)".format(donde, nombre))
        if nombre in configuracion:
            fallos.append("{0}.{1}: se llama como la configuracion de config/sistema.json, "
                          "que no cruza el contrato (RF-57)".format(donde, nombre))
    for n, sc in componentes.items():
        if "enum" not in sc:
            continue
        literales = vocabularios.get(_snake(n))
        if literales is None:
            fallos.append("{0}: enumeracion sin vocabulario en docs/definitions.md "
                          "(RF-34)".format(n))
            continue
        sobran = [v for v in sc["enum"] if v not in literales]
        faltan = [v for v in literales if v not in sc["enum"]]
        if sobran or faltan:
            fallos.append("{0}: los literales no son los de `{1}` en definitions; sobran {2}, "
                          "faltan {3} (RF-34)".format(n, _snake(n), sobran, faltan))
    return sorted(set(fallos))


def codigo_de_salida(diferencias):
    return 1 if diferencias else 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if "--escribir" in argv:
        escribir_congelado()
        print("congelado escrito en {0}".format(RUTA_CONGELADO.relative_to(RAIZ)))
        return 0
    if not RUTA_CONGELADO.exists():
        print("no existe {0}: genera el congelado con --escribir".format(RUTA_CONGELADO))
        return 1
    diferencias = comparar(leer_congelado(), generar())
    for d in diferencias:
        print(d)
    if diferencias:
        print("{0} diferencias entre el congelado y el backend. Si el cambio es "
              "deliberado, regenera con --escribir en el mismo commit (RF-33)".format(
                  len(diferencias)))
    else:
        print("el congelado coincide con el backend")
    fallos = comprobar_significado(leer_congelado())
    for f in fallos:
        print("[significado] " + f)
    return 1 if diferencias or fallos else 0


if __name__ == "__main__":
    sys.exit(main())
