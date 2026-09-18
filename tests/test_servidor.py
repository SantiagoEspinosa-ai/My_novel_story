"""Tests del servidor local (paso 1: solo lectura).

Que se protege aqui
-------------------
Este servidor es la primera pieza del proyecto que abre un puerto, y va a
crecer hasta escribir `config.json` y arrancar procesos. Asi que lo que mas se
prueba no es que sirva archivos —eso es facil— sino que **no sirva los que no
debe**:

- que solo se lleguen a leer `panel.html` y lo de dentro de `salida/`;
- que no haya forma de salirse del proyecto con `..`, con rutas absolutas, con
  la ruta codificada en porcentajes ni con un enlace simbolico;
- y, en concreto, que el `.env` de la raiz no se pueda descargar.

Ninguno de estos tests abre un puerto de verdad: el cliente de pruebas de
FastAPI habla con la aplicacion en memoria. Tampoco tocan el `salida/` real, que
es donde vive el trabajo del usuario: cada test monta un proyecto de juguete en
una carpeta temporal.
"""

import json

import pytest

# FastAPI no es un requisito del harness: las novelas se generan sin el
# servidor. Si no esta instalado, estos tests se saltan en vez de romper la
# suite entera, igual que hacen los del panel cuando falta `node`. El salto va
# antes de importar `src.servidor`, que tambien importa FastAPI.
pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402


PANEL_FALSO = "<!DOCTYPE html><html><body>panel de juguete</body></html>"


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    """Un proyecto de juguete con panel.html y un salida/ poblado."""
    (tmp_path / "panel.html").write_text(PANEL_FALSO, encoding="utf-8")
    salida = tmp_path / "salida"
    (salida / "capitulos").mkdir(parents=True)
    (salida / ".tmp").mkdir()
    (salida / "estado.json").write_text(
        json.dumps({"capitulos_aprobados": [1], "delegaciones": 3}), encoding="utf-8"
    )
    (salida / "manuscrito.md").write_text("# Capítulo 1 — Acentúa\n\nTexto.\n", encoding="utf-8")
    (salida / "capitulos" / "cap-01.md").write_text("# Capítulo 1 — Uno\n\nTexto.\n", encoding="utf-8")
    (salida / ".tmp" / "cap-01-intento-1.json").write_text('{"intento": 1}', encoding="utf-8")

    # Un secreto en la raiz, como el .env real del proyecto: si el servidor lo
    # sirviera, estos tests lo tienen que cazar.
    (tmp_path / ".env").write_text("UNA_CLAVE=no-debe-salir-de-aqui\n", encoding="utf-8")
    (tmp_path / "config.json").write_text('{"novela": {"genero": "terror"}}', encoding="utf-8")

    # `directorio_salida` consulta la configuracion real del proyecto; aqui se
    # fuerza a la del juguete para que los tests no dependan de ella.
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


@pytest.fixture
def cliente(proyecto):
    return TestClient(servidor.crear_app(proyecto))


# ---------------------------------------------------------------------------
# Lo que si se sirve
# ---------------------------------------------------------------------------


def test_la_raiz_devuelve_el_panel(cliente):
    r = cliente.get("/")
    assert r.status_code == 200
    assert "panel de juguete" in r.text


def test_el_panel_tambien_por_su_nombre(cliente):
    assert cliente.get("/panel.html").status_code == 200


def test_sirve_el_estado(cliente):
    r = cliente.get("/salida/estado.json")
    assert r.status_code == 200
    assert r.json()["delegaciones"] == 3


def test_sirve_un_capitulo_con_sus_acentos(cliente):
    """El charset va declarado: un manuscrito con acentos no puede llegar roto."""
    r = cliente.get("/salida/capitulos/cap-01.md")
    assert r.status_code == 200
    assert "utf-8" in r.headers["content-type"].lower()
    assert "Capítulo" in r.text


def test_sirve_los_intentos_de_tmp(cliente):
    """`.tmp/` empieza por punto y aun asi el panel lo necesita."""
    assert cliente.get("/salida/.tmp/cap-01-intento-1.json").status_code == 200


def test_el_estado_no_se_cachea(cliente):
    """El panel repregunta cada pocos segundos: una respuesta cacheada seria
    seguimiento en vivo de datos viejos."""
    r = cliente.get("/salida/estado.json")
    assert "no-store" in r.headers.get("cache-control", "")


def test_un_archivo_que_no_existe_es_404(cliente):
    assert cliente.get("/salida/capitulos/cap-99.md").status_code == 404


def test_la_salud_dice_donde_mira_y_que_escribe(cliente, proyecto):
    """`escribe` lista lo que este servidor puede tocar, y nada mas.

    Es una declaracion, no un adorno: cada vez que el servidor gane permiso
    para escribir algo nuevo, esta lista crece y este test hay que cambiarlo a
    mano. Esa friccion es intencionada.
    """
    r = cliente.get("/api/salud")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["ok"] is True
    assert cuerpo["panel_existe"] is True
    assert cuerpo["salida_existe"] is True
    assert cuerpo["escucha_en"] == "127.0.0.1"
    assert "config.json" in cuerpo["escribe"]
    assert any("salida-novela" in x for x in cuerpo["escribe"])
    # Y declara que lanza procesos, y cual. Es la linea que convierte este
    # servidor en algo que hay que mirar con cuidado.
    assert cuerpo["lanza_procesos"] == ["claude"]


# ---------------------------------------------------------------------------
# Lo que NO se sirve. Esta es la parte que importa.
# ---------------------------------------------------------------------------


def test_el_env_de_la_raiz_no_se_puede_descargar(cliente):
    """El caso concreto que motiva la lista blanca."""
    for intento in ["/.env", "/salida/../.env", "/salida/%2e%2e/.env"]:
        r = cliente.get(intento)
        assert r.status_code == 404, intento
        assert "no-debe-salir-de-aqui" not in r.text, intento


def test_el_codigo_del_proyecto_no_se_sirve(cliente):
    for intento in ["/config.json", "/src/servidor.py", "/CLAUDE.md", "/panel.html.bak"]:
        assert cliente.get(intento).status_code == 404, intento


@pytest.mark.parametrize("intento", [
    "/salida/../config.json",
    "/salida/../../config.json",
    "/salida/%2e%2e/config.json",
    "/salida/..%2fconfig.json",
    "/salida/....//config.json",
    "/salida/subir/../../config.json",
])
def test_no_se_puede_salir_de_salida(cliente, intento):
    """Ni con `..`, ni codificado, ni con el truco de los cuatro puntos."""
    r = cliente.get(intento)
    assert r.status_code == 404, intento
    assert "terror" not in r.text, intento


def test_una_ruta_absoluta_no_sirve_de_atajo(cliente):
    for intento in ["//etc/passwd", "/C:/Windows/win.ini", "/salida//etc/passwd"]:
        assert cliente.get(intento).status_code == 404, intento


def test_un_enlace_simbolico_que_apunta_fuera_no_vale(proyecto, cliente):
    """La comprobacion se hace sobre la ruta YA resuelta, asi que un enlace
    dentro de salida/ que apunte fuera tampoco abre la puerta.

    En Windows crear enlaces simbolicos necesita permisos, asi que si no se
    puede crear, el test se salta en vez de dar un falso verde.
    """
    destino = proyecto / ".env"
    enlace = proyecto / "salida" / "fuga.env"
    try:
        enlace.symlink_to(destino)
    except (OSError, NotImplementedError):
        pytest.skip("este sistema no deja crear enlaces simbolicos sin permisos")
    r = cliente.get("/salida/fuga.env")
    assert r.status_code == 404
    assert "no-debe-salir-de-aqui" not in r.text


def test_un_directorio_no_se_sirve_como_archivo(cliente):
    assert cliente.get("/salida/capitulos").status_code == 404


# ---------------------------------------------------------------------------
# La direccion de escucha
# ---------------------------------------------------------------------------


def test_la_direccion_es_localhost_y_es_constante():
    """No se toma de la linea de comandos: un servidor que va a escribir
    config.json y a arrancar procesos no puede acabar en 0.0.0.0 por un
    descuido al lanzarlo."""
    assert servidor.DIRECCION == "127.0.0.1"
    assert "0.0.0.0" not in (servidor.__doc__ or "")


def test_el_modulo_no_importa_ningun_cliente_http_de_salida():
    """El servidor escucha; no pide nada a nadie. La regla del proyecto es que
    ningun modulo del harness sale a la red."""
    fuente = (servidor.RAIZ_PROYECTO / "src" / "servidor.py").read_text(encoding="utf-8")
    for prohibido in ("import requests", "import urllib.request", "import aiohttp",
                      "httpx.get", "requests.get"):
        assert prohibido not in fuente, prohibido


def test_una_salida_fuera_del_proyecto_no_arranca(tmp_path, monkeypatch):
    """Si `runtime.directorio_salida` apuntara fuera, el servidor se niega."""
    (tmp_path / "panel.html").write_text(PANEL_FALSO, encoding="utf-8")
    monkeypatch.setattr(
        servidor.modulo_config, "cargar_config", lambda volcar=True: {"runtime": {}}
    )
    monkeypatch.setattr(
        servidor.modulo_config, "ruta_salida", lambda config: tmp_path.parent / "otra-cosa"
    )
    with pytest.raises(servidor.ErrorDeServidor):
        servidor.crear_app(tmp_path)
