"""El harness tiene que generar novelas sin FastAPI instalado.

Por que existe este archivo
---------------------------
Al añadir el servidor del panel, el proyecto pasó de tener una sola dependencia
(pytest, y solo para los tests) a tener cuatro. La promesa que se hizo al
añadirlas es que **el harness sigue siendo independiente**: FastAPI, uvicorn y
httpx son del panel, y quien solo quiera generar novelas no debería necesitar
instalarlas.

Una promesa así se rompe sola con el tiempo. Basta con que alguien añada un
`from fastapi import ...` en un módulo compartido, o con que un módulo del
harness importe el servidor «para reutilizar una función», y de pronto
`python -m src.orquestacion` no arranca en una máquina sin FastAPI. Estos tests
convierten la promesa en algo comprobable.

Se comprueba de dos maneras, porque una sola no basta:

1. **Estática**: ningún archivo de `src/` menciona esas librerías, salvo
   `servidor.py`. Es rápida y señala el archivo culpable.
2. **De verdad**: se lanza un intérprete nuevo con esas tres librerías
   **bloqueadas**, y se comprueba que todos los módulos del harness se importan
   y que su línea de comandos arranca. Esta es la que de verdad prueba la
   promesa: la estática se puede burlar con un import dentro de una función.

Estos tests NO se saltan cuando falta FastAPI: justamente en esa máquina es
donde más falta hacen.
"""

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
SRC = RAIZ / "src"

# Las librerías que son del servidor y de nadie más.
DEL_SERVIDOR = ("fastapi", "uvicorn", "httpx", "starlette")

# El único archivo de src/ que puede nombrarlas.
UNICO_PERMITIDO = "servidor.py"

# Los módulos del harness: todo lo que hace falta para generar una novela.
MODULOS_DEL_HARNESS = [
    "biblia", "config", "contexto", "delegaciones", "ensamblador",
    "estado", "orquestacion", "puntuacion", "redaccion",
]


def modulos_de_src():
    return sorted(p for p in SRC.glob("*.py") if p.name != "__init__.py")


# ---------------------------------------------------------------------------
# 1. Comprobación estática
# ---------------------------------------------------------------------------


def test_solo_el_servidor_nombra_las_librerias_del_servidor():
    culpables = []
    for archivo in modulos_de_src():
        if archivo.name == UNICO_PERMITIDO:
            continue
        texto = archivo.read_text(encoding="utf-8")
        for libreria in DEL_SERVIDOR:
            # Se busca la forma de importar, no la palabra suelta: un comentario
            # que mencione FastAPI para explicar algo es perfectamente legítimo.
            for forma in ("import " + libreria, "from " + libreria):
                if forma in texto:
                    culpables.append("{0} contiene «{1}»".format(archivo.name, forma))
    assert not culpables, (
        "Estos módulos del harness importan librerías que son solo del panel, "
        "así que el harness ha dejado de funcionar sin ellas:\n  - "
        + "\n  - ".join(culpables)
    )


def test_ningun_modulo_del_harness_importa_el_servidor():
    """Al revés también cuenta: el servidor puede usar el harness, nunca al revés.

    Si un módulo del harness importara `src.servidor`, arrastraría FastAPI por
    la puerta de atrás aunque no lo nombrara.
    """
    culpables = []
    for archivo in modulos_de_src():
        if archivo.name == UNICO_PERMITIDO:
            continue
        texto = archivo.read_text(encoding="utf-8")
        if "import servidor" in texto or "from src.servidor" in texto:
            culpables.append(archivo.name)
    assert not culpables, culpables


# ---------------------------------------------------------------------------
# 2. Comprobación de verdad: un intérprete sin esas librerías
# ---------------------------------------------------------------------------


def _carpeta_de_bloqueo(tmp_path):
    """Crea paquetes falsos que fingen no estar instalados.

    Cada uno lanza `ModuleNotFoundError`, que es exactamente lo que lanza Python
    cuando una librería no está. Puestos primero en `PYTHONPATH`, ganan a los
    reales, así que el intérprete hijo se comporta como una máquina donde nunca
    se instaló nada de esto.
    """
    bloqueo = tmp_path / "bloqueo"
    for libreria in DEL_SERVIDOR:
        paquete = bloqueo / libreria
        paquete.mkdir(parents=True)
        (paquete / "__init__.py").write_text(
            'raise ModuleNotFoundError("No module named {0!r}", name="{0}")\n'.format(
                libreria
            ),
            encoding="utf-8",
        )
    return bloqueo


def _correr_sin_servidor(tmp_path, codigo):
    """Ejecuta `codigo` en un intérprete nuevo con las librerías bloqueadas.

    El `PYTHONPATH` lleva primero la carpeta de bloqueo y después la raíz del
    proyecto, en ese orden: el bloqueo tiene que ganar a la instalación real, y
    la raíz hace que `src` sea importable.
    """
    ruta_busqueda = os.pathsep.join([str(_carpeta_de_bloqueo(tmp_path)), str(RAIZ)])
    # Se hereda el entorno y solo se cambia lo necesario. Construir uno desde
    # cero obliga a acertar con las variables que Windows necesita para arrancar
    # un proceso, y un fallo ahí se leería como «el harness no funciona» cuando
    # lo que no funciona es el test.
    entorno = dict(os.environ)
    entorno["PYTHONPATH"] = ruta_busqueda
    entorno["PYTHONIOENCODING"] = "utf-8"
    return subprocess.run(
        [sys.executable, "-c", textwrap.dedent(codigo)],
        cwd=str(RAIZ), env=entorno, capture_output=True, text=True, timeout=120,
    )


def test_el_bloqueo_funciona(tmp_path):
    """Antes de concluir nada, comprobar que el bloqueo bloquea de verdad.

    Sin este test, los dos siguientes podrían pasar simplemente porque el
    montaje no hace nada, y darían un verde que no significa nada.
    """
    r = _correr_sin_servidor(tmp_path, """
        try:
            import fastapi
        except ModuleNotFoundError:
            print("BLOQUEADO")
        else:
            print("NO BLOQUEADO")
    """)
    assert r.returncode == 0, r.stderr
    assert "BLOQUEADO" in r.stdout and "NO BLOQUEADO" not in r.stdout


def test_todos_los_modulos_del_harness_se_importan_sin_fastapi(tmp_path):
    r = _correr_sin_servidor(tmp_path, """
        from src import {0}
        print("IMPORTADOS")
    """.format(", ".join(MODULOS_DEL_HARNESS)))
    assert r.returncode == 0, (
        "El harness ya no se puede importar sin las librerías del panel:\n" + r.stderr
    )
    assert "IMPORTADOS" in r.stdout


def test_la_linea_de_comandos_del_harness_arranca_sin_fastapi(tmp_path):
    """La prueba que le importa a quien solo quiere generar novelas."""
    r = _correr_sin_servidor(tmp_path, """
        import sys
        from src import orquestacion
        parser = orquestacion.construir_parser()
        args = parser.parse_args(["estado"])
        print("CLI OK:", args.comando)
    """)
    assert r.returncode == 0, r.stderr
    assert "CLI OK: estado" in r.stdout


def test_la_configuracion_se_carga_sin_fastapi(tmp_path):
    """Cargar y validar la configuración es el paso 1 de cualquier generación."""
    r = _correr_sin_servidor(tmp_path, """
        from src.config import cargar_config
        c = cargar_config(volcar=False)
        print("GENERO:", c["novela"]["genero"])
    """)
    assert r.returncode == 0, r.stderr
    assert "GENERO:" in r.stdout


def test_el_servidor_si_necesita_fastapi_y_lo_dice(tmp_path):
    """El otro lado: `src.servidor` sin FastAPI falla, y falla claro.

    No se trata de que el servidor funcione sin FastAPI —no puede—, sino de que
    la separación sea real y esté en el sitio esperado.
    """
    r = _correr_sin_servidor(tmp_path, """
        try:
            from src import servidor
        except ModuleNotFoundError as e:
            print("FALLA COMO DEBE:", e.name)
        else:
            print("NO FALLO")
    """)
    assert r.returncode == 0, r.stderr
    assert "FALLA COMO DEBE: fastapi" in r.stdout
