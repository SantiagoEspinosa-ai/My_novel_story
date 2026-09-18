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
import time

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402
from tests.ayudas import biblia_valida  # noqa: E402


# Estos tests prueban CÓMO se arranca el ejecutable, no la comprobación previa
# de permisos, que tiene sus propios tests. Se da por buena para no lanzar una
# sesión de verdad en cada uno.
SESION_QUE_PUEDE = lambda: {"puede": True}


def app(proyecto, **extra):
    extra.setdefault("comprobador_sesion", SESION_QUE_PUEDE)
    return servidor.crear_app(proyecto, **extra)


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


def esperar_ampliacion(cliente, intentos=300):
    """La ampliacion es asincrona: se sondea hasta que la tuberia termina."""
    for _ in range(intentos):
        estado = cliente.get("/api/generacion").json()
        amp = estado.get("ampliacion") or {}
        if amp.get("estado") in ("fallida", "detenida", "generando"):
            return estado
        time.sleep(0.05)
    raise AssertionError("la ampliacion de prueba no termino")


def error_de_ampliacion(cliente, cuantos=1):
    r = cliente.post("/api/ampliar", json={"capitulos": cuantos})
    assert r.status_code == 200, r.text
    final = esperar_ampliacion(cliente)
    assert final["ampliacion"]["estado"] == "fallida", final["ampliacion"]
    return final["ampliacion"]["error"] or {}


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
    cliente = TestClient(app(proyecto))
    detalle = error_de_ampliacion(cliente)
    assert "no devolvio json" in detalle["mensaje"].lower()
    assert "no soy json" in detalle["respuesta"]


def test_generar_tambien_arranca_un_claude_que_es_un_script(proyecto, tmp_path, monkeypatch):
    """`generar` tenía exactamente el mismo fallo, sin haberse disparado aún.

    Se lanzaba con el nombre suelto igual que ampliar, así que habría muerto
    con el mismo `WinError 2` la primera vez que se pulsara el botón.
    """
    carpeta = crear_claude_postizo(tmp_path / "bin", "generando")
    monkeypatch.setenv("PATH", str(carpeta))
    cliente = TestClient(app(proyecto))
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
    cliente = TestClient(app(proyecto))
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
    # Se apunta a un ejecutable que no existe y se deja que el sistema operativo
    # falle de verdad. Antes este test simulaba `subprocess.run`, pero desde que
    # el arquitecto se lanza con `Popen` —para que `detener` pueda matarlo— esa
    # simulación probaba una rama que ya no se recorre. Dejar que reviente de
    # verdad es además más fiel: el mensaje que se enseña es el del sistema.
    monkeypatch.setattr(servidor, "resolver_ejecutable", lambda nombre: "C:/falso/claude.cmd")

    cliente = TestClient(app(proyecto))
    detalle = error_de_ampliacion(cliente)
    assert "no se ha podido arrancar" in detalle["mensaje"].lower()
    # `FileNotFoundError` es literalmente el nombre que salía en la traza del
    # fallo original, y el mensaje del sistema viaja con él.
    assert any("FileNotFoundError" in e for e in detalle["errores"]), detalle["errores"]
    assert detalle["ejecutable"] == "C:/falso/claude.cmd"


def test_una_excepcion_imprevista_llega_al_navegador_explicada(proyecto, monkeypatch):
    """La red de seguridad: cualquier fallo no previsto sale como JSON."""
    def revienta(*args, **kwargs):
        raise RuntimeError("algo que nadie penso")
    monkeypatch.setattr(servidor, "novela_completa", revienta)

    cliente = TestClient(app(proyecto), raise_server_exceptions=False)
    r = cliente.post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 500
    detalle = r.json()["detail"]
    assert "no estaba prevista" in detalle["mensaje"]
    assert any("RuntimeError: algo que nadie penso" in e for e in detalle["errores"])
    # La traza no viaja al navegador; se queda en la terminal del servidor.
    assert "Traceback" not in json.dumps(detalle)


# ---------------------------------------------------------------------------
# El prompt tiene que LLEGAR entero, no solo construirse bien
# ---------------------------------------------------------------------------
#
# El segundo mordisco del mismo `.CMD`. El prompt se pasaba como argumento, y
# `cmd.exe` termina la línea de comandos en el primer salto de línea: de un
# prompt de 2303 caracteres y 46 líneas llegaban 60, su primera línea. La
# sesión recibía un encargo truncado, no podía saberlo, y pedía el dato que le
# faltaba. Desde fuera parecía «el modelo no devolvió JSON».
#
# Los tests que había validaban que el número fuera un entero y que apareciera
# en lo que devuelve `prompt_ampliar`. Ninguno comprobaba que **llegara al otro
# lado**: probaban la interfaz, no el recorrido. Es exactamente el patrón del
# hallazgo 13.


def crear_claude_que_guarda_lo_que_recibe(carpeta, destino):
    """Un `claude` postizo que escribe en un archivo TODO lo que le llega.

    Tiene la forma del real —un script del `PATH`— y además captura sus
    argumentos y su entrada estándar, que es lo que permite comprobar por
    dónde y cómo llega el prompt.
    """
    carpeta.mkdir(parents=True, exist_ok=True)
    espia = carpeta / "espia.py"
    # Sin `.format()`: el propio código del espía lleva llaves y chocarían.
    fuente = (
        "import sys, json\n"
        "datos = {'args': sys.argv[1:], 'stdin': sys.stdin.read()}\n"
        "open(r'RUTA_DESTINO', 'w', encoding='utf-8').write("
        "json.dumps(datos, ensure_ascii=False))\n"
        "print('capturado')\n"
    ).replace("RUTA_DESTINO", str(destino))
    espia.write_text(fuente, encoding="utf-8")
    if ES_WINDOWS:
        guion = carpeta / "claude.cmd"
        guion.write_text('@echo off\r\n"{0}" "{1}" %*\r\n'.format(
            sys.executable, espia), encoding="utf-8")
    else:
        guion = carpeta / "claude"
        guion.write_text('#!/bin/sh\nexec "{0}" "{1}" "$@"\n'.format(
            sys.executable, espia), encoding="utf-8")
        guion.chmod(0o755)
    return carpeta


def test_el_numero_que_entra_por_http_llega_al_subproceso(proyecto, tmp_path, monkeypatch):
    """EL test que faltaba. Recorre HTTP → endpoint → prompt → proceso.

    Antes del arreglo, lo que llegaba al proceso era la primera línea del
    prompt y el número no aparecía por ninguna parte, que es justo el fallo
    que se vio en la práctica.
    """
    capturado = tmp_path / "recibido.json"
    carpeta = crear_claude_que_guarda_lo_que_recibe(tmp_path / "bin", capturado)
    monkeypatch.setenv("PATH", str(carpeta))

    cliente = TestClient(app(proyecto))
    cliente.post("/api/ampliar", json={"capitulos": 7})
    esperar_ampliacion(cliente)

    assert capturado.is_file(), "el subproceso no llegó a arrancar"
    recibido = json.loads(capturado.read_text(encoding="utf-8"))
    # El prompt viaja por la entrada estándar, no como argumento.
    llegado = recibido["stdin"]

    assert "7" in llegado, "el número no llegó al subproceso"
    assert "anadirle 7" in llegado
    assert "los 7 capitulos nuevos" in llegado


def test_el_prompt_llega_entero_y_no_solo_su_primera_linea(proyecto, tmp_path, monkeypatch):
    """La causa del truncado, comprobada sobre lo que de verdad recibe."""
    capturado = tmp_path / "recibido.json"
    carpeta = crear_claude_que_guarda_lo_que_recibe(tmp_path / "bin", capturado)
    monkeypatch.setenv("PATH", str(carpeta))

    cliente = TestClient(app(proyecto))
    cliente.post("/api/ampliar", json={"capitulos": 2})
    esperar_ampliacion(cliente)

    esperado = servidor.prompt_ampliar(2)
    llegado = json.loads(capturado.read_text(encoding="utf-8"))["stdin"]

    assert llegado.strip() == esperado.strip(), (
        "llegaron {0} caracteres de {1}".format(len(llegado), len(esperado)))
    # Y las tres cosas que el prompt tiene que decir y que iban detrás del
    # primer salto de línea, que era justo lo que se perdía.
    assert "LA NOVELA ESTABA CERRADA Y SE REABRE" in llegado
    assert "resumidor" in llegado
    assert llegado.count("\n") > 20


def test_el_prompt_de_generar_tambien_llega_por_stdin(proyecto, tmp_path, monkeypatch):
    """`generar` hoy se salva porque su prompt es de una sola línea.

    Eso es suerte, no diseño: bastaría con que alguien le añadiera un salto de
    línea para que empezara a truncarse en silencio. Va por stdin igual.
    """
    capturado = tmp_path / "recibido.json"
    carpeta = crear_claude_que_guarda_lo_que_recibe(tmp_path / "bin", capturado)
    monkeypatch.setenv("PATH", str(carpeta))

    cliente = TestClient(app(proyecto))
    cliente.post("/api/generar")
    for _ in range(100):
        if not cliente.get("/api/generacion").json()["viva"]:
            break

    recibido = json.loads(capturado.read_text(encoding="utf-8"))
    assert recibido["stdin"].strip() == servidor.PROMPT_GENERACION.strip()
    assert "EJECUCION.md" in recibido["stdin"]
    # El prompt no va como argumento: el comando es solo `claude -p`.
    assert recibido["args"] == ["-p"]


def test_una_respuesta_que_pide_datos_se_dice_con_esas_palabras(proyecto):
    """Lo que pasó de verdad: la sesión pidió el número que no le llegó.

    Su respuesta ES el diagnóstico. Tratarla como «no devolvió JSON» la
    entierra bajo un problema de formato que no existe.
    """
    def sesion_que_pregunta(prompt):
        return 0, "Dime cuantos capitulos anadir, un entero entre 1 y 20.", ""
    cliente = TestClient(app(proyecto, ejecutor_ampliar=sesion_que_pregunta))
    detalle = error_de_ampliacion(cliente, 2)
    assert detalle["pidio_datos"] is True
    assert "pidio informacion que no se le dio" in detalle["mensaje"]
    assert "el encargo le llego incompleto" in detalle["mensaje"].replace("ó", "o")
    assert "Dime cuantos capitulos" in detalle["respuesta"]


def test_una_respuesta_que_no_es_json_pero_tampoco_pregunta_se_dice_distinto(proyecto):
    """No todo lo que no es JSON es una pregunta: el mensaje se separa."""
    def sesion_charlatana(prompt):
        return 0, "He ampliado la novela correctamente y he guardado todo.", ""
    cliente = TestClient(app(proyecto, ejecutor_ampliar=sesion_charlatana))
    detalle = error_de_ampliacion(cliente, 2)
    assert detalle["pidio_datos"] is False
    assert "no devolvio json" in detalle["mensaje"].lower()


def test_si_la_sesion_muere_sin_decir_nada_se_ve_su_stderr(proyecto):
    """Cuando el error viene de la sesión de Claude Code, se enseña su salida."""
    def sesion_que_falla(prompt):
        return 1, "", "Error: no se pudo iniciar la sesion"
    cliente = TestClient(app(proyecto, ejecutor_ampliar=sesion_que_falla))
    detalle = error_de_ampliacion(cliente)
    assert detalle["codigo_salida"] == 1
    assert "no se pudo iniciar la sesion" in detalle["salida_de_la_sesion"]
