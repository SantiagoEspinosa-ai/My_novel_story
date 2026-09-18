"""Tests de la comprobación previa: ¿puede la sesión ejecutar el harness?

Qué pasó, y por qué existe esta comprobación
--------------------------------------------
Se pulsó generar. El servidor comprobó que `claude` estaba instalado, copió la
novela a `salida-novela-2/` y lanzó la sesión. La sesión **no tenía permiso
para ejecutar `python`**, así que no pudo dar ni un paso del contrato —todo el
flujo son comandos de Python— y, al ser headless, tampoco podía pedir ese
permiso: el diálogo no tiene dónde aparecer.

Lo explicó impecablemente en su log y salió con **código 0**. Resultado: una
carpeta de copia nueva, ni una línea escrita, y un panel diciendo que la
generación «terminó bien».

De ahí las dos cosas que se prueban aquí:

1. Antes de copiar nada y antes de delegar, se comprueba que la sesión puede
   ejecutar los comandos del harness. Si no puede, no se arranca y se dice por
   qué, con lo que la propia sesión contestó.
2. Esa comprobación va **antes de la copia**, por el mismo motivo que la de
   `claude`: no tiene sentido dejar una carpeta suelta por algo que no iba a
   funcionar.

Ninguno de estos tests lanza una sesión de verdad: el comprobador se inyecta.
"""

import json

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402
from tests.ayudas import biblia_valida  # noqa: E402


PUEDE = lambda: {"puede": True, "respuesta": "LISTO"}
NO_PUEDE = lambda: {
    "puede": False,
    "codigo_salida": 0,
    "respuesta": "ERROR: no tengo permiso para ejecutar python en esta sesion",
    "salida_de_la_sesion": "",
}


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>p</html>", encoding="utf-8")
    salida = tmp_path / "salida"
    (salida / "capitulos").mkdir(parents=True)
    (salida / "resumenes").mkdir()
    for n in (1, 2, 3):
        (salida / "capitulos" / "cap-{0:02d}.md".format(n)).write_text(
            "# Capítulo {0} — Uno\n\nTexto.\n".format(n), encoding="utf-8")
    (salida / "manuscrito.md").write_text("# Capítulo 1 — Uno\n\nTexto.\n", encoding="utf-8")
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
    monkeypatch.setattr(servidor, "resolver_ejecutable", lambda nombre: "claude-de-mentira")
    return tmp_path


def cliente(proyecto, comprobador):
    return TestClient(servidor.crear_app(proyecto, comprobador_sesion=comprobador))


# ---------------------------------------------------------------------------
# Generar
# ---------------------------------------------------------------------------


def test_si_la_sesion_no_puede_ejecutar_el_harness_no_se_genera(proyecto):
    r = cliente(proyecto, NO_PUEDE).post("/api/generar")
    assert r.status_code == 503
    detalle = r.json()["detail"]
    assert "no puede ejecutar los comandos del harness" in detalle["mensaje"]
    # Y se cuenta lo que la propia sesión contestó, que es el diagnóstico.
    assert "no tengo permiso" in detalle["respuesta"]


def test_el_error_dice_como_arreglarlo(proyecto):
    detalle = cliente(proyecto, NO_PUEDE).post("/api/generar").json()["detail"]
    assert "permissions" in detalle["pista"]
    assert "src.orquestacion" in detalle["pista"]
    assert "interactiva" in detalle["pista"]


def test_no_copia_nada_si_la_sesion_no_puede(proyecto):
    """Igual que con el ejecutable: primero se comprueba, después se copia."""
    cliente(proyecto, NO_PUEDE).post("/api/generar")
    assert not list(proyecto.glob("salida-novela-*"))


def test_no_deja_ninguna_generacion_en_marcha(proyecto):
    cli = cliente(proyecto, NO_PUEDE)
    cli.post("/api/generar")
    estado = cli.get("/api/generacion").json()
    assert estado["viva"] is False
    assert estado["estado"] == "sin_datos"


# ---------------------------------------------------------------------------
# Ampliar
# ---------------------------------------------------------------------------


def test_ampliar_tampoco_arranca_si_la_sesion_no_puede(proyecto):
    antes = (proyecto / "salida" / "biblia.json").read_bytes()
    r = cliente(proyecto, NO_PUEDE).post("/api/ampliar", json={"capitulos": 1})
    assert r.status_code == 503
    assert "no puede ejecutar los comandos del harness" in r.json()["detail"]["mensaje"]
    assert not list(proyecto.glob("salida-novela-*"))
    assert (proyecto / "salida" / "biblia.json").read_bytes() == antes


# ---------------------------------------------------------------------------
# El prompt de la comprobación
# ---------------------------------------------------------------------------


def test_el_prompt_pide_ejecutar_un_comando_del_harness_y_nada_mas():
    prompt = servidor.PROMPT_COMPROBAR_SESION
    assert "python -m src.orquestacion --help" in prompt
    assert "LISTO" in prompt and "ERROR:" in prompt
    # Que no haga nada más: es una comprobación, no un trabajo.
    assert "No hagas nada mas" in prompt


def test_una_respuesta_afirmativa_se_reconoce(monkeypatch):
    monkeypatch.setattr(servidor, "ejecutar_claude",
                        lambda raiz, prompt, segundos: (0, "LISTO", ""))
    assert servidor.comprobar_que_la_sesion_puede(".")["puede"] is True


def test_una_respuesta_con_error_no_se_toma_por_buena(monkeypatch):
    """Aunque la palabra LISTO aparezca por algún lado."""
    monkeypatch.setattr(
        servidor, "ejecutar_claude",
        lambda raiz, prompt, segundos: (0, "ERROR: no puedo. Estaría LISTO si pudiera.", ""))
    resultado = servidor.comprobar_que_la_sesion_puede(".")
    assert resultado["puede"] is False
    assert "no puedo" in resultado["respuesta"]


def test_una_respuesta_vacia_tampoco(monkeypatch):
    monkeypatch.setattr(servidor, "ejecutar_claude",
                        lambda raiz, prompt, segundos: (1, "", "se cayo"))
    resultado = servidor.comprobar_que_la_sesion_puede(".")
    assert resultado["puede"] is False
    assert "se cayo" in resultado["salida_de_la_sesion"]
