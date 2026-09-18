"""Tests de la carga por red de `panel.html`.

Que se prueba aqui, y por que asi
---------------------------------
El panel es una sola pagina sin dependencias y sin compilacion. La unica forma
honesta de comprobar que un capitulo que esta en disco acaba llegando a la
pantalla es ejecutar su JavaScript de verdad contra un servidor de verdad. Por
eso estos tests:

1. montan un `salida/` de juguete en una carpeta temporal,
2. lo sirven con el servidor estatico de la libreria estandar,
3. ejecutan el script real de `panel.html` con `tests/panel_sonda.js`,
4. y comprueban que todos los capitulos del disco han llegado.

No tocan la red de fuera (el servidor escucha en 127.0.0.1 con puerto que elige
el sistema) ni el `salida/` real del proyecto.

Si no hay `node` instalado, los tests se saltan en vez de fallar: node no es un
requisito del harness, que es Python, y el panel se puede seguir usando sin el.

El caso que motivo estos tests
------------------------------
La vista Libro salia vacia con los capitulos delante. La causa no era la ruta
del fetch, que respondia 200, sino que el numero de capitulos que la pagina
pedia salia de `config-efectiva.json`: si ese archivo faltaba o estaba
desfasado, los capitulos de disco que quedaban fuera de esa cuenta no se
llegaban a pedir. Y un archivo que no se pide no da 404: no da nada. Por eso el
test mira los capitulos del DISCO y exige que todos aparezcan, en vez de
comprobar codigos de respuesta.
"""

import json
import shutil
import subprocess
import threading
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

RAIZ = Path(__file__).resolve().parent.parent
PANEL = RAIZ / "panel.html"
SONDA = Path(__file__).resolve().parent / "panel_sonda.js"

CAPITULO = "# Capítulo {0} — Titulo de prueba\n\nUn parrafo cualquiera.\n"


def hay_node():
    return shutil.which("node") is not None


requiere_node = pytest.mark.skipif(
    not hay_node(), reason="hace falta node para ejecutar el JavaScript del panel"
)


def escribir_salida(carpeta, capitulos, config=None, estado=None):
    """Monta un `salida/` de juguete y devuelve la carpeta que se va a servir.

    `capitulos` es la lista de numeros que SI existen en disco. Se pueden dejar
    huecos a proposito: un capitulo que falta en medio es un caso real durante
    una generacion a medias.
    """
    salida = carpeta / "salida"
    (salida / "capitulos").mkdir(parents=True)
    for n in capitulos:
        (salida / "capitulos" / "cap-{0:02d}.md".format(n)).write_text(
            CAPITULO.format(n), encoding="utf-8"
        )
    if config is not None:
        (salida / "config-efectiva.json").write_text(
            json.dumps(config, ensure_ascii=False), encoding="utf-8"
        )
    if estado is not None:
        (salida / "estado.json").write_text(
            json.dumps(estado, ensure_ascii=False), encoding="utf-8"
        )
    shutil.copy(PANEL, carpeta / "panel.html")
    return carpeta


def sondar(carpeta):
    """Sirve `carpeta` y devuelve lo que el panel consigue cargar de ella."""
    manejador = partial(SimpleHTTPRequestHandler, directory=str(carpeta))
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), manejador)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    try:
        base = "http://127.0.0.1:{0}/".format(servidor.server_address[1])
        proceso = subprocess.run(
            ["node", str(SONDA), str(carpeta / "panel.html"), base],
            capture_output=True, text=True, timeout=120,
        )
    finally:
        servidor.shutdown()
        servidor.server_close()

    if proceso.returncode != 0:
        raise AssertionError(
            "la sonda del panel fallo ({0}):\n{1}".format(
                proceso.returncode, proceso.stderr
            )
        )
    return json.loads(proceso.stdout)


def capitulos_en_disco(carpeta):
    return sorted(
        int(p.stem.split("-")[1])
        for p in (carpeta / "salida" / "capitulos").glob("cap-*.md")
    )


# ---------------------------------------------------------------------------
# El contrato: lo que esta en disco tiene que llegar a la pagina
# ---------------------------------------------------------------------------


@requiere_node
def test_un_capitulo_en_disco_siempre_llega_a_la_pagina(tmp_path):
    """El caso normal: la cuenta de la configuracion coincide con el disco."""
    carpeta = escribir_salida(
        tmp_path, [1, 2, 3], config={"estructura": {"num_capitulos": 3}, "modelos": {}}
    )
    res = sondar(carpeta)
    assert res["capitulos"] == capitulos_en_disco(carpeta)


@requiere_node
def test_la_configuracion_desfasada_no_esconde_capitulos(tmp_path):
    """`config-efectiva.json` se queda corto y en disco hay mas capitulos.

    Este es el fallo que se arreglo: la pagina pedia tantos capitulos como
    dijera la configuracion, asi que el 2 y el 3 no se pedian siquiera.
    """
    carpeta = escribir_salida(
        tmp_path, [1, 2, 3], config={"estructura": {"num_capitulos": 1}, "modelos": {}}
    )
    res = sondar(carpeta)
    assert res["capitulos"] == capitulos_en_disco(carpeta) == [1, 2, 3]


@requiere_node
def test_sin_configuracion_los_capitulos_siguen_apareciendo(tmp_path):
    """Sin `config-efectiva.json` no hay cuenta de la que fiarse.

    Ademas falta el capitulo 1, que es lo que hacia que la vista saliera
    completamente vacia en vez de incompleta: la pagina pedia solo el 1, no
    estaba, y se quedaba sin nada que ensenar.
    """
    carpeta = escribir_salida(tmp_path, [2, 3, 4])
    res = sondar(carpeta)
    assert res["capitulos"] == capitulos_en_disco(carpeta) == [2, 3, 4]


@requiere_node
def test_el_estado_tambien_sirve_para_saber_cuantos_buscar(tmp_path):
    """Con `estado.json` y sin configuracion, el suelo sale de los capitulos
    que el estado da por hechos."""
    carpeta = escribir_salida(
        tmp_path,
        [1, 2, 3, 4],
        estado={"capitulos_aprobados": [1, 3], "capitulos_marcados": [2, 4],
                "delegaciones": 0},
    )
    res = sondar(carpeta)
    assert res["capitulos"] == capitulos_en_disco(carpeta) == [1, 2, 3, 4]


@requiere_node
def test_una_novela_sin_capitulos_no_inventa_ninguno(tmp_path):
    """El otro lado del contrato: si no hay nada en disco, no aparece nada.

    Sin esto, un test que solo exigiera "que aparezcan los del disco" pasaria
    con una pagina que se inventara capitulos.
    """
    carpeta = escribir_salida(
        tmp_path, [], config={"estructura": {"num_capitulos": 3}, "modelos": {}}
    )
    res = sondar(carpeta)
    assert res["capitulos"] == []
