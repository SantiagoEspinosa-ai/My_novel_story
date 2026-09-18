"""Tests de los endpoints de configuración del servidor (paso 2).

Qué se protege aquí
-------------------
`PUT /api/config` es el primer endpoint que **escribe en el disco** a partir de
algo que llega del navegador. La regla es que el cuerpo de la petición no es la
configuración nueva, sino una lista de cambios sobre la que ya hay, y que nada
se escribe hasta pasar cuatro puertas:

1. no hay una generación en marcha,
2. las claves existen y los tipos encajan,
3. la configuración resultante entera pasa por `src/config.py`,
4. y solo entonces se escribe, de forma atómica.

Casi todos los tests de este archivo comprueban lo mismo desde ángulos
distintos: **cuando algo se rechaza, `config.json` tiene que quedar byte a byte
como estaba**. Un rechazo que deja el archivo a medias sería peor que no
validar nada.

Ninguno toca el `config.json` real del proyecto: cada test monta el suyo en una
carpeta temporal.
"""

import json

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import redaccion, servidor  # noqa: E402


CONFIG_DE_JUGUETE = {
    "_meta": {"version": "4.0", "descripcion": "config de juguete"},
    "novela": {
        "titulo": None,
        "genero": "terror",
        "tono": "sobrio",
        "punto_de_vista": "tercera persona limitada",
        "idioma": "es",
        "semilla_tematica": None,
    },
    "estructura": {"num_capitulos": 3, "palabras_min": 1200, "palabras_max": 2200},
    "modelos": {
        "escalera_escritor": ["haiku", "sonnet", "opus"],
        "intentos_por_modelo": 2,
        "mantener_voz_ganadora": True,
        "arquitecto": "sonnet",
        "validadores": "haiku",
        "resumidor": "haiku",
    },
    "runtime": {"directorio_salida": "./salida", "conservar_intentos": False},
    "limites": {"delegaciones_max_totales": 300, "abortar_si_supera_delegaciones": True},
}


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>panel</html>", encoding="utf-8")
    (tmp_path / "salida").mkdir()
    (tmp_path / "config.json").write_text(
        json.dumps(CONFIG_DE_JUGUETE, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


@pytest.fixture
def cliente(proyecto):
    return TestClient(servidor.crear_app(proyecto))


def leer(proyecto):
    return json.loads((proyecto / "config.json").read_text(encoding="utf-8"))


def poner_generacion_en_curso(proyecto):
    (proyecto / "salida" / "estado.json").write_text(json.dumps({
        "capitulo_actual": 2, "intento_actual": 1, "modelo_actual": "opus",
        "capitulos_aprobados": [1], "capitulos_marcados": [],
        "iniciado": "2026-09-18T10:00:00Z",
        "delegacion_en_curso": {
            "rol": "escritor", "modelo": "opus", "capitulo": 2, "intento": 1,
            "inicio": "2026-09-18T10:05:00Z",
        },
    }), encoding="utf-8")


# ---------------------------------------------------------------------------
# GET
# ---------------------------------------------------------------------------


def test_devuelve_el_archivo_y_la_efectiva(cliente):
    """Las dos, porque responden a preguntas distintas: una se edita y la otra
    es la que el harness usará de verdad."""
    r = cliente.get("/api/config")
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["archivo"]["estructura"]["num_capitulos"] == 3
    assert cuerpo["efectiva"]["estructura"]["num_capitulos"] == 3
    # La efectiva trae ajustes que el archivo no nombra, por los valores por defecto.
    assert "contexto" in cuerpo["efectiva"]
    assert "contexto" not in cuerpo["archivo"]
    assert cuerpo["editable"] is True
    assert cuerpo["generacion_en_curso"] is None


def test_dice_cuando_no_es_editable(cliente, proyecto):
    poner_generacion_en_curso(proyecto)
    cuerpo = cliente.get("/api/config").json()
    assert cuerpo["editable"] is False
    assert cuerpo["generacion_en_curso"]["rol"] == "escritor"


def test_una_configuracion_rota_se_puede_seguir_leyendo(cliente, proyecto):
    """Es justo cuando más falta hace poder verla y arreglarla."""
    malo = dict(CONFIG_DE_JUGUETE)
    malo["estructura"] = {"num_capitulos": 0, "palabras_min": 1200, "palabras_max": 2200}
    (proyecto / "config.json").write_text(json.dumps(malo), encoding="utf-8")
    cuerpo = cliente.get("/api/config").json()
    assert cuerpo["archivo"]["estructura"]["num_capitulos"] == 0
    assert cuerpo["efectiva"] is None
    assert cuerpo["errores"] and "num_capitulos" in cuerpo["errores"][0]


def test_lo_que_sale_va_redactado(cliente, proyecto):
    """Lo que viaja al navegador pasa por el filtro de redacción, igual que el
    volcado de la configuración efectiva."""
    con_secreto = json.loads(json.dumps(CONFIG_DE_JUGUETE))
    con_secreto["limites"]["api_key"] = "valor-que-no-debe-salir"
    (proyecto / "config.json").write_text(json.dumps(con_secreto), encoding="utf-8")
    texto = cliente.get("/api/config").text
    assert "valor-que-no-debe-salir" not in texto
    assert redaccion.MARCA in texto


# ---------------------------------------------------------------------------
# PUT: el camino que sí escribe
# ---------------------------------------------------------------------------


def test_cambia_un_ajuste_y_lo_escribe(cliente, proyecto):
    r = cliente.put("/api/config", json={"estructura": {"num_capitulos": 5}})
    assert r.status_code == 200, r.text
    cuerpo = r.json()
    assert cuerpo["escrito"] is True
    assert cuerpo["cambios"] == [
        {"clave": "estructura.num_capitulos", "antes": 3, "despues": 5}
    ]
    assert leer(proyecto)["estructura"]["num_capitulos"] == 5


def test_lo_que_no_se_envia_no_se_toca(cliente, proyecto):
    """El cuerpo es una lista de cambios, no la configuración entera."""
    cliente.put("/api/config", json={"novela": {"genero": "romance"}})
    despues = leer(proyecto)
    assert despues["novela"]["genero"] == "romance"
    assert despues["novela"]["punto_de_vista"] == "tercera persona limitada"
    assert despues["modelos"]["escalera_escritor"] == ["haiku", "sonnet", "opus"]
    assert despues["_meta"]["version"] == "4.0"


def test_un_nulo_acepta_un_valor_por_primera_vez(cliente, proyecto):
    """`semilla_tematica` empieza en null: no hay tipo previo del que fiarse."""
    r = cliente.put("/api/config", json={"novela": {"semilla_tematica": "una casa"}})
    assert r.status_code == 200, r.text
    assert leer(proyecto)["novela"]["semilla_tematica"] == "una casa"


def test_una_lista_se_puede_cambiar_entera(cliente, proyecto):
    r = cliente.put("/api/config", json={"modelos": {"escalera_escritor": ["sonnet", "opus"]}})
    assert r.status_code == 200, r.text
    assert leer(proyecto)["modelos"]["escalera_escritor"] == ["sonnet", "opus"]


def test_enviar_lo_mismo_no_reescribe_el_archivo(cliente, proyecto):
    antes = (proyecto / "config.json").read_bytes()
    r = cliente.put("/api/config", json={"estructura": {"num_capitulos": 3}})
    assert r.status_code == 200
    assert r.json()["escrito"] is False
    assert (proyecto / "config.json").read_bytes() == antes


# ---------------------------------------------------------------------------
# PUT: todo lo que tiene que rechazar, sin escribir nada
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("cuerpo,pista", [
    ({"inventada": 1}, "no existe"),
    ({"estructura": {"capitulos": 5}}, "no existe"),
    ({"estructura": {"num_capitulos": "cinco"}}, "numero entero"),
    ({"estructura": {"num_capitulos": True}}, "numero entero"),
    ({"modelos": {"mantener_voz_ganadora": "si"}}, "booleano"),
    ({"modelos": {"escalera_escritor": "opus"}}, "lista"),
    ({"modelos": {"escalera_escritor": ["opus", 3]}}, "tiene que ser de texto"),
    ({"novela": {"genero": {"a": 1}}}, "se esperaba"),
    ({"estructura": "entera"}, "se esperaba"),
    ({"_meta": {"version": "9"}}, "metadatos"),
])
def test_rechaza_y_no_escribe(cliente, proyecto, cuerpo, pista):
    antes = (proyecto / "config.json").read_bytes()
    r = cliente.put("/api/config", json=cuerpo)
    assert r.status_code == 400, r.text
    errores = r.json()["detail"]["errores"]
    assert any(pista in e for e in errores), errores
    assert (proyecto / "config.json").read_bytes() == antes


def test_acumula_todos_los_errores_de_una_vez(cliente):
    """Como el validador de la biblia: se arreglan de una vez, no de uno en uno."""
    r = cliente.put("/api/config", json={
        "inventada": 1,
        "estructura": {"num_capitulos": "cinco", "palabras_min": "mil"},
    })
    assert r.status_code == 400
    assert len(r.json()["detail"]["errores"]) == 3


def test_rechaza_lo_que_config_py_considera_invalido(cliente, proyecto):
    """Las claves existen y los tipos encajan, pero el valor no vale.

    Esta es la tercera puerta: la validación de `src/config.py` sobre la
    configuración entera, no sobre el cambio suelto.
    """
    antes = (proyecto / "config.json").read_bytes()
    r = cliente.put("/api/config", json={"estructura": {"num_capitulos": 0}})
    assert r.status_code == 400
    assert "num_capitulos" in " ".join(r.json()["detail"]["errores"])
    assert (proyecto / "config.json").read_bytes() == antes


def test_rechaza_un_rango_de_palabras_imposible(cliente, proyecto):
    antes = (proyecto / "config.json").read_bytes()
    r = cliente.put("/api/config", json={
        "estructura": {"palabras_min": 3000, "palabras_max": 1000}
    })
    assert r.status_code == 400
    assert (proyecto / "config.json").read_bytes() == antes


def test_rechaza_un_modelo_que_no_existe(cliente, proyecto):
    r = cliente.put("/api/config", json={"modelos": {"arquitecto": "gpt-5"}})
    assert r.status_code == 400
    assert leer(proyecto)["modelos"]["arquitecto"] == "sonnet"


def test_no_se_puede_guardar_de_vuelta_un_valor_redactado(cliente, proyecto):
    """El panel enseña `[REDACTADO]`; si el usuario le da a guardar sin tocarlo,
    no se puede escribir esa palabra como si fuera el valor."""
    r = cliente.put("/api/config", json={"novela": {"tono": redaccion.MARCA}})
    assert r.status_code == 400
    assert "redactado" in " ".join(r.json()["detail"]["errores"]).lower()
    assert leer(proyecto)["novela"]["tono"] == "sobrio"


def test_no_escribe_mientras_hay_una_generacion_en_marcha(cliente, proyecto):
    poner_generacion_en_curso(proyecto)
    antes = (proyecto / "config.json").read_bytes()
    r = cliente.put("/api/config", json={"estructura": {"num_capitulos": 9}})
    assert r.status_code == 409
    assert r.json()["detail"]["generacion_en_curso"]["rol"] == "escritor"
    assert (proyecto / "config.json").read_bytes() == antes


def test_al_terminar_la_generacion_se_vuelve_a_poder_escribir(cliente, proyecto):
    poner_generacion_en_curso(proyecto)
    assert cliente.put("/api/config", json={"estructura": {"num_capitulos": 9}}).status_code == 409
    # El harness borra la marca al registrar el resultado.
    datos = json.loads((proyecto / "salida" / "estado.json").read_text(encoding="utf-8"))
    datos.pop("delegacion_en_curso")
    (proyecto / "salida" / "estado.json").write_text(json.dumps(datos), encoding="utf-8")
    assert cliente.put("/api/config", json={"estructura": {"num_capitulos": 9}}).status_code == 200
    assert leer(proyecto)["estructura"]["num_capitulos"] == 9


def test_un_cuerpo_que_no_es_objeto_se_rechaza(cliente, proyecto):
    antes = (proyecto / "config.json").read_bytes()
    for cuerpo in ([1, 2, 3], "texto", 5):
        r = cliente.put("/api/config", json=cuerpo)
        assert r.status_code in (400, 422), (cuerpo, r.status_code)
    assert (proyecto / "config.json").read_bytes() == antes


def test_el_archivo_queda_bien_formado_y_legible(cliente, proyecto):
    """Se reescribe con sangría y sin escapar los acentos: alguien lo va a abrir."""
    cliente.put("/api/config", json={"novela": {"semilla_tematica": "una canción"}})
    texto = (proyecto / "config.json").read_text(encoding="utf-8")
    assert "canción" in texto
    assert texto.endswith("\n")
    assert json.loads(texto)["novela"]["semilla_tematica"] == "una canción"


def test_no_deja_archivos_temporales(cliente, proyecto):
    cliente.put("/api/config", json={"estructura": {"num_capitulos": 6}})
    assert not list(proyecto.glob("*.tmp"))


# ---------------------------------------------------------------------------
# El servidor sigue sin servir lo que no debe
# ---------------------------------------------------------------------------


def test_config_json_sigue_sin_poder_descargarse_como_archivo(cliente):
    """Se lee por su endpoint, que lo redacta. Por HTTP directo, no."""
    assert cliente.get("/config.json").status_code == 404


def test_la_salud_declara_que_ya_escribe(cliente):
    assert "config.json" in cliente.get("/api/salud").json()["escribe"]
