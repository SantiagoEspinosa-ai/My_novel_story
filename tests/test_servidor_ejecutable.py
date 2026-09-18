"""Tests de cómo se arranca Claude Code. El fallo que estos tests existen para
que no vuelva.

Qué pasó
--------
`POST /api/ampliar` devolvía un `500` pelado. La traza del servidor decía:

    FileNotFoundError: [WinError 2] The system cannot find the file specified
      ... subprocess.run(["claude", "-p", prompt])

Y sin embargo `claude --version` funcionaba perfectamente en la terminal, y
`shutil.which("claude")` lo encontraba sin problema.

La causa: en Windows, `claude` instalado con npm **no es un `.exe`**, es un
`claude.CMD`. `shutil.which()` lo encuentra porque aplica `PATHEXT`, pero
`CreateProcess` —que es lo que hay debajo de `subprocess` cuando no se usa
shell— **no aplica PATHEXT**: busca el nombre literal y solo ejecuta binarios.
Así que la comprobación previa pasaba y el arranque fallaba justo después.

Por qué los tests que ya había no lo cazaron
--------------------------------------------
Porque inyectaban un comando de mentira construido con `sys.executable`, que es
un `.exe` de verdad. El camino que fallaba —resolver un nombre suelto contra el
`PATH`— no lo recorría ningún test. De ahí estos: montan un `claude` postizo
**con la misma forma que el real**, un script de shell en el `PATH`, y exigen
que se pueda arrancar.
"""

import json
import subprocess
import sys

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402
from tests.ayudas import biblia_valida  # noqa: E402


ES_WINDOWS = sys.platform == "win32"


def crear_claude_postizo(carpeta, texto_que_imprime):
    """Un `claude` con la misma forma que el de npm: un script, no un binario.

    En Windows es un `.cmd`, que es exactamente el caso que fallaba. En el
    resto, un script con almohadilla-admiración. Se devuelve la carpeta para
    ponerla en el `PATH`.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    if ES_WINDOWS:
        guion = carpeta / "claude.cmd"
        guion.write_text("@echo off\r\necho {0}\r\n".format(texto_que_imprime),
                         encoding="utf-8")
    else:
        guion = carpeta / "claude"
        guion.write_text("#!/bin/sh\necho '{0}'\n".format(texto_que_imprime),
                         encoding="utf-8")
        guion.chmod(0o755)
    return carpeta


@pytest.fixture
def con_claude_postizo(tmp_path, monkeypatch):
    carpeta = crear_claude_postizo(tmp_path / "bin", "hola desde el claude postizo")
    monkeypatch.setenv("PATH", str(carpeta) + ";" + "" if False else
                       str(carpeta) + (";" if ES_WINDOWS else ":") + "")
    return carpeta


# ---------------------------------------------------------------------------
# La causa, aislada
# ---------------------------------------------------------------------------


def test_el_nombre_suelto_no_arranca_un_script_en_windows(tmp_path, monkeypatch):
    """Reproduce el fallo original en su forma más pequeña.

    No es un test de nuestro código: es la comprobación de que la causa que
    diagnosticamos es la que es. Si algún día Python cambiara este
    comportamiento, este test lo diría y podríamos simplificar el arreglo.
    """
    if not ES_WINDOWS:
        pytest.skip("el fallo es propio de CreateProcess en Windows")
    carpeta = crear_claude_postizo(tmp_path / "bin", "hola")
    monkeypatch.setenv("PATH", str(carpeta))
    with pytest.raises(FileNotFoundError):
        subprocess.run(["claude"], capture_output=True, shell=False)


def test_la_ruta_resuelta_si_arranca(tmp_path, monkeypatch):
    """Y la cura: resolver con `which` y pasar la ruta completa."""
    carpeta = crear_claude_postizo(tmp_path / "bin", "hola")
    monkeypatch.setenv("PATH", str(carpeta))
    ruta = servidor.resolver_ejecutable("claude")
    assert ruta.lower().endswith(("claude.cmd", "claude"))
    proceso = subprocess.run([ruta], capture_output=True, text=True, shell=False)
    assert proceso.returncode == 0
    assert "hola" in proceso.stdout


def test_resolver_ejecutable_da_un_error_claro_si_no_esta(tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "vacia"))
    with pytest.raises(Exception) as fallo:
        servidor.resolver_ejecutable("claude")
    detalle = getattr(fallo.value, "detail", {})
    assert getattr(fallo.value, "status_code", None) == 503
    assert "no encuentro el ejecutable" in detalle["mensaje"].lower()
    assert "--version" in detalle["pista"]


# ---------------------------------------------------------------------------
# El camino completo, con un claude postizo en el PATH
# ---------------------------------------------------------------------------


RESPUESTA_BUENA = {"biblia": None, "resumen_del_antiguo_ultimo": None}


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>panel</html>", encoding="utf-8")
    salida = tmp_path / "salida"
    (salida / "capitulos").mkdir(parents=True)
    (salida / "resumenes").mkdir()
    for n in (1, 2, 3):
        (salida / "capitulos" / "cap-{0:02d}.md".format(n)).write_text(
            "# Capítulo {0} — Uno\n\nTexto.\n".format(n), encoding="utf-8")
    (salida / "biblia.json").write_text(
        json.dumps(biblia_valida(3), ensure_ascii=False), encoding="utf-8")
    (salida / "estado.json").write_text(json.dumps({
        "capitulo_actual": 3, "intento_actual": 0, "modelo_actual": "opus",
        "capitulos_aprobados": [1, 2, 3], "capitulos_marcados": [],
        "iniciado": "2026-09-18T10:00:00Z", "delegaciones": 20,
    }), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps({
        "novela": {"genero": "terror"},
        "estructura": {"num_capitulos": 3, "palabras_min": 100, "palabras_max": 9000},
        "runtime": {"directorio_salida": "./salida"},
    }), encoding="utf-8")
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


def test_ampliar_llega_a_arrancar_el_claude_postizo(proyecto, tmp_path, monkeypatch):
    """El test que faltaba: recorre el camino real de arranque.

    El `claude` postizo imprime algo que no es JSON, así que la ampliación
    termina en `502`. Eso es justo lo que se quiere comprobar: que **llegó a
    arrancar**. Antes del arreglo, esto daba `500` con `WinError 2`.
    """
    carpeta = crear_claude_postizo(tmp_path / "bin", "no soy json")
    monkeypatch.setenv("PATH", str(carpeta))
    cliente = TestClient(servidor.crear_app(proyecto))
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 502, r.text
    detalle = r.json()["detail"]
    assert "no devolvio json" in detalle["mensaje"].lower()
    assert "no soy json" in detalle["respuesta"]


def test_generar_tambien_arranca_un_claude_que_es_un_script(proyecto, tmp_path, monkeypatch):
    """`generar` tenía exactamente el mismo fallo, sin haberse disparado aún.

    Se lanzaba con el nombre suelto igual que ampliar, así que habría muerto
    con el mismo `WinError 2` la primera vez que se pulsara el botón.
    """
    carpeta = crear_claude_postizo(tmp_path / "bin", "generando")
    monkeypatch.setenv("PATH", str(carpeta))
    cliente = TestClient(servidor.crear_app(proyecto))
    r = cliente.post("/api/generar")
    assert r.status_code == 200, r.text
    assert r.json()["viva"] in (True, False)   # puede haber terminado ya
    for _ in range(100):
        cuerpo = cliente.get("/api/generacion").json()
        if not cuerpo["viva"]:
            break
    assert "generando" in "\n".join(cuerpo["log"])


def test_si_claude_no_esta_ampliar_da_503_y_no_copia(proyecto, tmp_path, monkeypatch):
    monkeypatch.setenv("PATH", str(tmp_path / "vacia"))
    cliente = TestClient(servidor.crear_app(proyecto))
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 503
    assert not list(proyecto.glob("salida-novela-*"))


# ---------------------------------------------------------------------------
# Ningún 500 vuelve a salir desnudo
# ---------------------------------------------------------------------------


def test_un_fallo_de_arranque_se_explica_en_vez_de_dar_un_500_pelado(proyecto, monkeypatch):
    """Aunque el arranque falle por otro motivo, el cuerpo tiene que explicarlo.

    El panel solo puede enseñar lo que el servidor le mande: si la respuesta no
    trae cuerpo, lo único que puede decir es «el servidor respondió 500», que
    no le sirve a nadie.
    """
    def revienta(*args, **kwargs):
        raise OSError(2, "El sistema no puede encontrar el archivo especificado")
    monkeypatch.setattr(servidor.subprocess, "run", revienta)
    monkeypatch.setattr(servidor, "resolver_ejecutable", lambda nombre: "C:/falso/claude.cmd")

    cliente = TestClient(servidor.crear_app(proyecto))
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 500
    detalle = r.json()["detail"]
    assert "no se ha podido arrancar" in detalle["mensaje"].lower()
    # `OSError(2, ...)` lo convierte Python en `FileNotFoundError`, que es
    # literalmente el nombre que salía en la traza del fallo original.
    assert any("FileNotFoundError" in e for e in detalle["errores"]), detalle["errores"]
    assert any("no puede encontrar el archivo" in e for e in detalle["errores"])
    assert detalle["ejecutable"] == "C:/falso/claude.cmd"


def test_una_excepcion_imprevista_llega_al_navegador_explicada(proyecto, monkeypatch):
    """La red de seguridad: cualquier fallo no previsto sale como JSON."""
    def revienta(*args, **kwargs):
        raise RuntimeError("algo que nadie penso")
    monkeypatch.setattr(servidor, "novela_completa", revienta)

    cliente = TestClient(servidor.crear_app(proyecto), raise_server_exceptions=False)
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 500
    detalle = r.json()["detail"]
    assert "no estaba prevista" in detalle["mensaje"]
    assert any("RuntimeError: algo que nadie penso" in e for e in detalle["errores"])
    # La traza no viaja al navegador; se queda en la terminal del servidor.
    assert "Traceback" not in json.dumps(detalle)


def test_si_la_sesion_muere_sin_decir_nada_se_ve_su_stderr(proyecto):
    """Cuando el error viene de la sesión de Claude Code, se enseña su salida."""
    def sesion_que_falla(prompt):
        return 1, "", "Error: no se pudo iniciar la sesion"
    cliente = TestClient(servidor.crear_app(proyecto, ejecutor_ampliar=sesion_que_falla))
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 502
    detalle = r.json()["detail"]
    assert detalle["codigo_salida"] == 1
    assert "no se pudo iniciar la sesion" in detalle["salida_de_la_sesion"]
