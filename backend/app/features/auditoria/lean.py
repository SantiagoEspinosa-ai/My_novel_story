"""El adaptador a Lean de la puerta de publicacion (`SPEC-30` `RF-02`).

Lean se ejecuta **solo**, al llegar a la puerta: nadie lo lanza a mano. Esto lo hace
en cuatro pasos sobre una **copia temporal** de `specs/lean/` —con su `.lake`, para
reutilizar lo compilado—, porque `Cronologia/Generado.lean` esta versionado y el
generador lo sobrescribe: en el sitio, cada puerta ensuciaria el arbol y dos obras a
la vez se pisarian.

  1. `generar_lean.py <base> <obra>`, que convierte la cronologia de SQLite en Lean.
  2. `lake build verificar-real`.
  3. `lake exe verificar-real`, que devuelve 0, 1 o 2.
  4. `interpretar`, que es pura y se prueba sola.

COMO SE LEE, Y POR QUE NUNCA SE DA «LIMPIO» DE MAS
--------------------------------------------------
- Un `0` sin la linea `#COBERTURA` no es limpio: nadie puede distinguirlo de un
  programa que no llego a mirar (`F-54`).
- El `1` del **generador** —cero eventos convertidos— no es el `1` de Lean: no hay
  violacion, no habia nada que comprobar. Es sin veredicto.
- Un codigo desconocido, un tiempo agotado o una base en memoria son sin veredicto.
- Sin `lake`, no se pudo ejecutar (`codigo=None`), que tambien bloquea.

Todos los caminos que no son un `0` con cobertura bloquean la publicacion
(`RF-09`): en la duda, fallar de forma visible.
"""

import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

from app.commons import config
from app.features.auditoria.publicacion import ResultadoLean

LEAN = pathlib.Path(__file__).resolve().parents[4] / "specs" / "lean"


class LeanNoDisponible(RuntimeError):
    pass


def localizar_lake(entorno=None, casa=None) -> str:
    """En Windows `lake` no suele estar en el `PATH` (elan no lo pone ni define
    `ELAN_HOME`), asi que se busca tambien donde elan lo instala."""
    entorno = os.environ if entorno is None else entorno
    casa = casa or os.path.expanduser("~")
    candidatos = [entorno.get("HARNESS_LAKE")]
    if entorno.get("ELAN_HOME"):
        candidatos.append(os.path.join(entorno["ELAN_HOME"], "bin", "lake"))
    candidatos += [shutil.which("lake"), os.path.join(casa, ".elan", "bin", "lake")]
    for c in candidatos:
        for ruta in (c, (c or "") + ".exe"):
            if c and os.path.isfile(ruta):
                return ruta
    raise LeanNoDisponible("no se encuentra `lake`: ni HARNESS_LAKE, ni ELAN_HOME, ni el "
                           "PATH, ni ~/.elan/bin")


def interpretar(codigo_generador, codigo, salida) -> ResultadoLean:
    if codigo_generador == 1:
        return ResultadoLean(2, detalle="el generador convirtio cero eventos: no habia "
                                        "nada que comprobar")
    if codigo_generador not in (0, None):
        return ResultadoLean(None, detalle="el generador fallo con {0}".format(codigo_generador))
    lineas = salida.splitlines()
    violaciones = []
    for l in lineas:
        if l.startswith("#VIOLACION "):
            partes = l.split(" ", 3) + ["", ""]
            violaciones.append({"invariante": partes[1],
                                "eventos": [e for e in partes[2].split(",") if e],
                                "detalle": partes[3]})
    if codigo == 0:
        if not any(l.startswith("#COBERTURA") for l in lineas):
            return ResultadoLean(2, detalle="Lean salio con 0 sin decir que miro")
        return ResultadoLean(0)
    if codigo == 1:
        return ResultadoLean(1, violaciones=violaciones)
    if codigo == 2:
        return ResultadoLean(2, detalle="sin veredicto: no habia dato bastante para mirar")
    return ResultadoLean(2, detalle="codigo desconocido de Lean: {0}".format(codigo))


def ruta_de(con):
    """La ruta de la base principal, o `None` si esta en memoria."""
    for fila in con.execute("PRAGMA database_list"):
        if fila[1] == "main":
            return fila[2] or None
    return None


class VerificadorLean:
    def __init__(self, lake=None, ejecutar=subprocess.run,
                 tiempo=config.TIEMPO_MAXIMO_LEAN_SEGUNDOS, origen=LEAN):
        self.lake, self.ejecutar, self.tiempo, self.origen = lake, ejecutar, tiempo, origen

    def verificar(self, con, obra, version=None) -> ResultadoLean:
        ruta = ruta_de(con)
        if ruta is None:
            return ResultadoLean(2, detalle="la base esta en memoria: no hay nada que "
                                            "darle a Lean")
        try:
            lake = self.lake or localizar_lake()
        except LeanNoDisponible as e:
            return ResultadoLean(None, detalle=str(e))
        tmp = tempfile.mkdtemp(prefix="lean-")
        copia = os.path.join(tmp, "lean")
        try:
            shutil.copytree(self.origen, copia)
            orden = [sys.executable, "generar_lean.py", ruta, obra,
                     "--salida", os.path.join("Cronologia", "Generado.lean")]
            if version is not None:
                orden += ["--version", str(version)]
            gen = self._correr(orden, copia)
            if gen.returncode != 0:
                return interpretar(gen.returncode, None, "")
            build = self._correr([lake, "build", "verificar-real"], copia)
            if build.returncode != 0:
                return ResultadoLean(None, detalle="Lean no compila la cronologia generada")
            r = self._correr([lake, "exe", "verificar-real"], copia)
            return interpretar(0, r.returncode, (r.stdout or b"").decode("utf-8", "replace"))
        except subprocess.TimeoutExpired:
            return ResultadoLean(2, detalle="se agoto el tiempo de Lean ({0} s): sin "
                                            "veredicto".format(self.tiempo))
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def _correr(self, orden, cwd):
        return self.ejecutar(orden, cwd=cwd, capture_output=True, timeout=self.tiempo)
