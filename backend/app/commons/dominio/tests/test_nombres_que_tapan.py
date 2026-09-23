"""Ningun parametro tapa un modulo que su fichero importa.

POR QUE EXISTE
--------------
`obra.py` importaba `capitulo` de `auditoria/` y una funcion gano un parametro
llamado `capitulo`. Dentro de ella, `capitulo.cerrar` dejo de ser el modulo y
paso a ser el argumento —`None`—, asi que la llamada reventaba con
`'NoneType' object has no attribute 'NoSePuedeCerrar'`.

**Y el error salia dentro del `except`**, al evaluar `except capitulo.NoSePuedeCerrar`,
de modo que el mensaje no mencionaba ni el modulo tapado ni la funcion que lo
tapaba. Tumbo 29 pruebas diciendo algo que no era lo que pasaba. Es la Regla 8
en su peor forma: no solo no dice que no se comprobo, es que **ni siquiera dice
que se rompio**.

POR QUE UNA PRUEBA Y NO UNA REVISION
--------------------------------------
Porque se repone solo. El nombre natural del parametro es el mismo que el nombre
natural del modulo -`capitulo`, `memoria`, `mundo`- asi que quien escriba la
siguiente funcion volvera a elegirlo, y en revision no se ve: las dos lineas son
correctas por separado y solo chocan cuando estan en el mismo ambito.

Es el mismo tipo de comprobador barato que `VER-63`: diez lineas que recorren
carpetas valen mas que una intencion.

QUE NO VE
---------
Solo mira parametros y asignaciones locales contra los modulos que **ese
fichero** importa. Un nombre que tape algo importado dentro de una funcion, o un
atributo de clase, se le escapan. Se declara aqui porque un validador sin punto
ciego declarado no entra (Regla 1).
"""

import ast
import pathlib

RAIZ = pathlib.Path(__file__).resolve().parents[3]


def _importados(arbol):
    """Los nombres que el fichero liga a nivel superior con un `import`."""
    nombres = set()
    for nodo in arbol.body:
        if isinstance(nodo, (ast.Import, ast.ImportFrom)):
            for alias in nodo.names:
                nombres.add(alias.asname or alias.name.split(".")[0])
    return nombres


def _parametros(funcion):
    args = funcion.args
    nombres = [a.arg for a in args.posonlyargs + args.args + args.kwonlyargs]
    if args.vararg:
        nombres.append(args.vararg.arg)
    if args.kwarg:
        nombres.append(args.kwarg.arg)
    return nombres


def _asignaciones(funcion):
    """Variables locales que se ligan por asignacion o por `for`."""
    nombres = []
    for nodo in ast.walk(funcion):
        if isinstance(nodo, ast.Name) and isinstance(nodo.ctx, ast.Store):
            nombres.append(nodo.id)
    return nombres


def _corto(py):
    """La ruta relativa al arbol, o el nombre si el fichero vive fuera de el.

    El caso negativo escribe en un temporal, que no cuelga de `RAIZ`: sin esto
    el propio comprobador reventaba al intentar describir lo que encontraba.
    """
    try:
        return py.relative_to(RAIZ)
    except ValueError:
        return py.name


def _choques(py):
    arbol = ast.parse(py.read_text(encoding="utf-8"), filename=str(py))
    importados = _importados(arbol)
    if not importados:
        return []
    choques = []
    for nodo in ast.walk(arbol):
        if not isinstance(nodo, (ast.FunctionDef, ast.AsyncFunctionDef)):
            continue
        for nombre in set(_parametros(nodo)) | set(_asignaciones(nodo)):
            if nombre in importados:
                choques.append("{0}:{1} `{2}` tapa el modulo `{3}`".format(
                    _corto(py), nodo.lineno, nodo.name, nombre))
    return choques


def _ficheros():
    for py in sorted(RAIZ.rglob("*.py")):
        if "__pycache__" in py.parts:
            continue
        yield py


def test_ningun_nombre_local_tapa_un_modulo_importado():
    choques = [c for py in _ficheros() for c in _choques(py)]
    assert not choques, (
        "un nombre local tapa un modulo importado, y cuando eso pasa el error "
        "no dice que ha pasado:\n  " + "\n  ".join(choques))


def test_el_comprobador_sabe_encontrar_el_caso_que_lo_motivo(tmp_path):
    """El caso negativo, y aqui no es opcional.

    Un comprobador que recorre el arbol y no encuentra nada es indistinguible de
    uno roto que no encuentra nada: las dos veces la prueba pasa. Esto reintroduce
    el defecto exacto de `obra.py` y exige que lo vea.
    """
    fichero = tmp_path / "con_choque.py"
    fichero.write_text(
        "from app.features.auditoria import capitulo\n"
        "\n"
        "def evaluar_cierre(con, obra, capitulo=None):\n"
        "    return capitulo.cerrar([], [])\n",
        encoding="utf-8")
    choques = _choques(fichero)
    assert len(choques) == 1, choques
    assert "`capitulo`" in choques[0]
