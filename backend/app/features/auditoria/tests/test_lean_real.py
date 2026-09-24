"""`PLAN-30` E5: Lean dice que eventos implica cada violacion.

Ejecuta `lake` de verdad sobre `specs/lean/`, con el `Generado.lean` versionado
(obra-x, cinco eventos). **Se salta si no encuentra `lake`**, y lo dice: en una
maquina sin la toolchain esta prueba no afirma nada.

`SPEC-30` `RF-03` pide que el fallo vuelva al Editor «con las violaciones concretas y
los eventos implicados». Hasta aqui Lean solo las contaba en prosa, que se reescribe
cualquier dia; una linea con prefijo fijo, no.
"""

import os
import pathlib
import shutil
import subprocess

import pytest

LEAN = pathlib.Path(__file__).resolve().parents[5] / "specs" / "lean"


def _lake():
    candidatos = [os.environ.get("HARNESS_LAKE")]
    if os.environ.get("ELAN_HOME"):
        candidatos.append(os.path.join(os.environ["ELAN_HOME"], "bin", "lake"))
    candidatos += [shutil.which("lake"),
                   os.path.join(os.path.expanduser("~"), ".elan", "bin", "lake")]
    for c in candidatos:
        for ruta in (c, (c or "") + ".exe"):
            if c and os.path.isfile(ruta):
                return ruta
    return None


@pytest.fixture(scope="module")
def salida():
    lake = _lake()
    if lake is None:
        pytest.skip("no se encuentra `lake`: sin toolchain de Lean esta prueba no afirma nada")
    subprocess.run([lake, "build", "verificar-real"], cwd=LEAN, check=True,
                   capture_output=True, timeout=900)
    r = subprocess.run([lake, "exe", "verificar-real"], cwd=LEAN, capture_output=True,
                       timeout=300)
    return r.returncode, r.stdout.decode("utf-8", errors="replace")


def test_verificar_real_emite_una_linea_por_violacion(salida):
    codigo, texto = salida
    assert codigo == 1
    lineas = [l.split(" ", 3) for l in texto.splitlines() if l.startswith("#VIOLACION ")]
    assert {(l[1], l[2]) for l in lineas} == {
        ("L-1", "ev-1,ev-2"), ("L-3", "ev-3a,ev-3b"), ("L-4", "ev-3b,ev-4")}


def test_cada_linea_de_violacion_lleva_su_detalle(salida):
    """Sin la primera asercion, con cero lineas el bucle no comprobaba nada y la
    prueba pasaba antes de existir el formato (Regla 11)."""
    _, texto = salida
    lineas = [l for l in texto.splitlines() if l.startswith("#VIOLACION ")]
    assert lineas
    for l in lineas:
        assert len(l.split(" ", 3)) == 4 and l.split(" ", 3)[3].strip()
