"""VER-63 — Ningun modulo se queda sin que ninguna prueba lo importe.

POR QUE EXISTE
--------------
`prompt.py` se quedo con un error de sintaxis y **nada fallo**, porque ningun
test lo importaba. Un modulo sin prueba **no esta verificado: esta sin
ejecutar**, y la diferencia importa — un modulo que nadie importa puede estar
roto desde hace semanas y la suite seguira en verde.

Es el mismo tipo de comprobador barato que cazo la violacion de `A-02`, que
hasta ahora es el unico que ha encontrado algo que nadie habia visto. Diez
lineas que recorren carpetas valen mas que una intencion.

SE MIRA LA ALCANZABILIDAD, NO LA IMPORTACION DIRECTA
------------------------------------------------------
La primera version comparaba contra lo que los tests importan **a mano**, y
marco cinco modulos que si se ejecutan: `features/brief/*` y el router del
ciclo entran por `app.main` cuando una prueba levanta el cliente HTTP. Marcar
codigo que se ejecuta seria cobertura falsa al reves — ruido que acaba
enseñando a ignorar al validador.

Lo que se comprueba es **alcanzable desde alguna prueba**, siguiendo las
importaciones en cadena. Eso es literalmente "alguien lo ejecuta", y sigue
cazando el caso que lo motivo: `prompt.py` no era alcanzable desde ninguna
prueba, ni directa ni indirectamente.

QUE NO VE
---------
Que sea alcanzable **no significa que lo prueben**. Un modulo que se importa
para usar una constante queda contado y sin ejercitar. Esto comprueba que nadie
sea codigo muerto, no que nadie se quede sin probar: eso lo dice la cobertura,
que es otra medida y hoy no se mide.
"""

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[3]

# Ficheros que no son modulos que probar.
EXENTOS = {"__init__.py"}


def _modulos_de_produccion():
    for py in sorted(RAIZ.rglob("*.py")):
        if "tests" in py.parts or py.name in EXENTOS:
            continue
        yield py


def _importa(py):
    """Los modulos `app.*` que importa un fichero."""
    arbol = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    fuera = set()
    for nodo in ast.walk(arbol):
        if isinstance(nodo, ast.ImportFrom) and (nodo.module or "").startswith("app"):
            fuera.add(nodo.module)
            for alias in nodo.names:
                fuera.add(nodo.module + "." + alias.name)
        elif isinstance(nodo, ast.Import):
            for alias in nodo.names:
                if alias.name.startswith("app"):
                    fuera.add(alias.name)
    return fuera


def _alcanzables_desde_las_pruebas():
    """Cierre transitivo: lo que una prueba importa, y lo que eso importa."""
    por_nombre = {_nombre_de_modulo(py): py for py in _modulos_de_produccion()}
    pendientes = set()
    for py in sorted(RAIZ.rglob("*.py")):
        if "tests" in py.parts:
            pendientes |= _importa(py)
    vistos = set()
    while pendientes:
        nombre = pendientes.pop()
        if nombre in vistos:
            continue
        vistos.add(nombre)
        if nombre in por_nombre:
            pendientes |= _importa(por_nombre[nombre])
    return vistos


def _nombre_de_modulo(py):
    return "app." + ".".join(py.relative_to(RAIZ).with_suffix("").parts)


def test_todo_modulo_es_alcanzable_desde_alguna_prueba():
    alcanzables = _alcanzables_desde_las_pruebas()
    huerfanos = [_nombre_de_modulo(py) for py in _modulos_de_produccion()
                 if _nombre_de_modulo(py) not in alcanzables]
    assert huerfanos == [], (
        "estos modulos no los alcanza ninguna prueba, ni directa ni "
        "indirectamente, asi que nadie los ejecuta y pueden estar rotos sin "
        "que la suite se entere: {0}".format(huerfanos))


def test_el_comprobador_cazaria_un_modulo_huerfano():
    """El caso negativo: si no cazara nada, estaria en verde por construccion."""
    assert "app.features.generacion.prompt" in _alcanzables_desde_las_pruebas()
    assert "app.commons.modelo.inventado" not in _alcanzables_desde_las_pruebas()
