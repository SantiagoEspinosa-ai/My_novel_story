"""Tests de que lo que se declara y lo que se manda es lo mismo.

El fallo
--------
El servidor reventaba con:

    h11._util.LocalProtocolError: Too much data for declared Content-Length

La sospecha razonable era que el `Content-Length` se calculara sobre
**caracteres** y se mandaran **bytes**: en UTF-8 cada tilde y cada eñe ocupan
dos bytes y cuentan como un carácter, así que un manuscrito en castellano
sobraría un byte por cada acento. Se midió, y no era eso: `FileResponse` saca
la longitud de `st_size`, que ya son bytes, y cuadraba exacto incluso en un
capítulo con 278 bytes de acentos.

La causa real era otra frontera: `FileResponse` declara la longitud con un
`stat()` y **después** lee el archivo por trozos. Si el archivo **crece entre
esas dos cosas**, manda más de lo prometido. Y hay un archivo que crece
constantemente, `salida/.log-generacion.txt`, al que la generación va añadiendo
su salida — y que el panel anuncia en pantalla, así que abrirlo en el navegador
mientras se genera es lo natural.

Por qué los tests que había no lo cazaron
------------------------------------------
Dos motivos, y los dos son el mismo patrón del hallazgo 13: fixtures más
limpios que la realidad.

1. Los archivos de prueba eran **ASCII o casi**, así que no habrían cazado un
   fallo de bytes aunque hubiera sido esa la causa.
2. Los archivos de prueba estaban **quietos**. Ninguno crecía mientras se
   servía, que es la condición que hace fallar al servidor.

De ahí estos tests: uno mide los bytes de verdad sobre texto con acentos y
eñes, y otro sirve un archivo mientras otro hilo lo hace crecer.
"""

import io
import json
import threading
import time

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402


# Texto con todo lo que en UTF-8 ocupa más de un byte y este proyecto usa a
# diario: tildes, eñes, apertura de interrogación, comillas latinas y rayas de
# diálogo. Un fixture en ASCII no probaría nada de esto.
TEXTO_CON_ACENTOS = (
    "# Capítulo 5 — La niña de la señal\n\n"
    "—¿Qué más da? —dijo Mara—. Está aquí, y aquí se queda.\n\n"
    "El pequeño añadió: «Mañana será otro día», con una sonrisa rarísima.\n"
    "Ñandú, ünicode, ©, €, …, “comillas”, ‘simples’.\n"
)


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>p</html>", encoding="utf-8")
    salida = tmp_path / "salida"
    (salida / "capitulos").mkdir(parents=True)
    (salida / "capitulos" / "cap-05.md").write_text(TEXTO_CON_ACENTOS, encoding="utf-8")
    (salida / "manuscrito.md").write_text(TEXTO_CON_ACENTOS * 40, encoding="utf-8")
    (salida / "estado.json").write_text(
        json.dumps({"capitulos_aprobados": [1], "nota": "añadió una señal"},
                   ensure_ascii=False), encoding="utf-8")
    (tmp_path / "config.json").write_text('{"novela": {"genero": "terror"}}', encoding="utf-8")
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


@pytest.fixture
def cliente(proyecto):
    return TestClient(servidor.crear_app(proyecto))


# ---------------------------------------------------------------------------
# Bytes, no caracteres
# ---------------------------------------------------------------------------


def test_el_fixture_tiene_acentos_de_verdad():
    """Si el texto de prueba fuera ASCII, los tests de abajo no probarían nada.

    Se comprueba que hay diferencia real entre caracteres y bytes, que es la
    condición sin la cual todo esto pasaría por casualidad.
    """
    caracteres = len(TEXTO_CON_ACENTOS)
    octetos = len(TEXTO_CON_ACENTOS.encode("utf-8"))
    assert octetos > caracteres, "el texto de prueba no tiene nada multibyte"
    assert octetos - caracteres >= 15


@pytest.mark.parametrize("ruta", [
    "/salida/capitulos/cap-05.md",
    "/salida/manuscrito.md",
    "/salida/estado.json",
])
def test_el_content_length_son_los_bytes_reales(cliente, proyecto, ruta):
    respuesta = cliente.get(ruta)
    assert respuesta.status_code == 200
    en_disco = (proyecto / ruta.lstrip("/")).read_bytes()
    assert int(respuesta.headers["content-length"]) == len(en_disco)
    assert respuesta.content == en_disco


def test_el_texto_llega_entero_y_bien_descodificado(cliente, proyecto):
    """Lo que llega es exactamente lo que hay en disco, byte a byte.

    Se compara contra el disco y no contra la constante de arriba porque en
    Windows `write_text` traduce los saltos de línea a CRLF: el archivo real
    tiene dos bytes donde la constante tiene uno. Que el servidor devuelva lo
    del disco es justo lo correcto; comparar contra la constante mediría la
    traducción de Python, no el servidor.
    """
    respuesta = cliente.get("/salida/capitulos/cap-05.md")
    en_disco = (proyecto / "salida" / "capitulos" / "cap-05.md").read_bytes()
    assert respuesta.content == en_disco
    for trozo in ("Capítulo", "niña", "señal", "—¿Qué", "«Mañana", "Ñandú"):
        assert trozo in respuesta.text
    assert "utf-8" in respuesta.headers["content-type"].lower()


def test_no_se_corta_ni_sobra_un_solo_byte(cliente, proyecto):
    """El manuscrito repetido cuarenta veces: si faltara o sobrara un byte por
    acento, aquí se vería multiplicado."""
    respuesta = cliente.get("/salida/manuscrito.md")
    esperado = (proyecto / "salida" / "manuscrito.md").read_bytes()
    assert len(respuesta.content) == len(esperado)
    assert respuesta.content == esperado


# ---------------------------------------------------------------------------
# La causa de verdad: un archivo que crece mientras se sirve
# ---------------------------------------------------------------------------


def test_un_archivo_que_crece_mientras_se_sirve_no_rompe_la_conexion(proyecto):
    """El caso que reventaba el servidor.

    `salida/.log-generacion.txt` crece sin parar mientras se genera, y el panel
    dice en pantalla dónde está, así que abrirlo en el navegador durante una
    generación es lo natural. Con `FileResponse`, 150 de 150 peticiones
    fallaban con `Too much data for declared Content-Length`.
    """
    ruta = proyecto / "salida" / ".log-generacion.txt"
    ruta.write_text("===== GENERACION LANZADA =====\n", encoding="utf-8")

    parar = threading.Event()

    def ir_anadiendo():
        while not parar.is_set():
            with io.open(ruta, "a", encoding="utf-8") as f:
                f.write("El escritor está redactando el capítulo 5… " * 20 + "\n")
            time.sleep(0.001)

    hilo = threading.Thread(target=ir_anadiendo, daemon=True)
    hilo.start()
    try:
        cliente = TestClient(proyecto_app(proyecto))
        for _ in range(40):
            respuesta = cliente.get("/salida/.log-generacion.txt")
            assert respuesta.status_code == 200
            # Lo que se declara y lo que llega salen de la misma lectura.
            assert int(respuesta.headers["content-length"]) == len(respuesta.content)
    finally:
        parar.set()
        hilo.join(timeout=2)


def proyecto_app(proyecto):
    return servidor.crear_app(proyecto)


def test_un_archivo_enorme_se_rechaza_con_un_motivo(proyecto, monkeypatch):
    """Leerlo entero tiene un límite, y cuando se pasa se dice por qué."""
    monkeypatch.setattr(servidor, "MAXIMO_A_SERVIR", 100)
    cliente = TestClient(servidor.crear_app(proyecto))
    respuesta = cliente.get("/salida/manuscrito.md")
    assert respuesta.status_code == 413
    assert "demasiado grande" in respuesta.json()["detail"]["mensaje"]
