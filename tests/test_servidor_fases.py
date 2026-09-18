"""Tests de ampliar-y-generar como una sola operación, y de sus fases.

Qué cambió
----------
Ampliar y generar eran dos pasos con una confirmación humana en medio. Ahora
son uno: al confirmar, el servidor copia, pide el outline al arquitecto, lo
valida, lo guarda, sube `num_capitulos` y **arranca la escritura solo**. La
petición ya no espera: devuelve en cuanto la operación arranca.

Lo que no se puede perder al juntarlas
--------------------------------------
Juntarlas quita un punto de control humano, así que lo que lo sustituye tiene
que funcionar de verdad. Estos tests protegen las tres cosas que lo sustituyen:

1. **El outline se puede leer en cuanto existe**, antes de que haya un solo
   capítulo escrito. Es lo que permite juzgar si la continuación vale.
2. **Se puede detener en cualquier fase**, incluida la del arquitecto. Parar
   al leer el outline cuesta las delegaciones del arquitecto, no las de la
   novela entera.
3. **Si el arquitecto falla o la biblia no valida, no se genera nada** y la
   novela queda como estaba, igual que cuando eran dos pasos.

Ninguno gasta delegaciones: el arquitecto y la generación son dobles.
"""

import json
import sys
import threading
import time

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import narracion  # noqa: E402
from src import servidor  # noqa: E402
from tests.ayudas import biblia_valida  # noqa: E402


GENERACION_FALSA = lambda: [sys.executable, "-c", "print('escribiendo')"]
GENERACION_LARGA = lambda: [sys.executable, "-c", "import time; time.sleep(60)"]


def entrada(n):
    return {"capitulo": n, "sinopsis": "Sinopsis del capitulo {0}.".format(n),
            "cambio": "Cambia algo en el {0}.".format(n)}


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>p</html>", encoding="utf-8")
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
        "modelos": {"escalera_escritor": ["haiku", "sonnet", "opus"],
                    "intentos_por_modelo": 2},
        "runtime": {"directorio_salida": "./salida"},
    }), encoding="utf-8")
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


def arquitecto(hasta=5, espera=None, avisar=None):
    """Arquitecto de mentira. Puede bloquearse para observar su fase."""
    def ejecutor(prompt):
        if avisar is not None:
            avisar.set()
        if espera is not None:
            espera.wait(timeout=20)
        b = biblia_valida(3)
        b["outline"] = b["outline"] + [entrada(n) for n in range(4, hasta + 1)]
        b["timeline"] = b.get("timeline", []) + [
            {"capitulo": n, "momento": "Despues"} for n in range(4, hasta + 1)]
        return 0, json.dumps({"biblia": b, "resumen_del_antiguo_ultimo": None},
                             ensure_ascii=False), ""
    return ejecutor


def cliente(proyecto, ejecutor, comando=GENERACION_FALSA):
    return TestClient(servidor.crear_app(
        proyecto, comando=comando, ejecutor_ampliar=ejecutor))


def esperar(cliente_, condicion, intentos=300):
    for _ in range(intentos):
        estado = cliente_.get("/api/generacion").json()
        if condicion(estado):
            return estado
        time.sleep(0.05)
    raise AssertionError("no se cumplió la condición esperada")


# ---------------------------------------------------------------------------
# Una sola operación
# ---------------------------------------------------------------------------


def test_la_peticion_vuelve_enseguida_y_no_espera_al_arquitecto(proyecto):
    """Antes se quedaba esperando minutos; ahora devuelve al arrancar."""
    sigue = threading.Event()
    arrancado = threading.Event()
    cli = cliente(proyecto, arquitecto(espera=sigue, avisar=arrancado), GENERACION_LARGA)
    try:
        r = cli.post("/api/ampliar", json={"capitulos": 2})
        assert r.status_code == 200
        assert r.json()["arrancada"] is True
        assert r.json()["capitulos_nuevos"] == [4, 5]
        # Y el arquitecto sigue trabajando cuando la respuesta ya volvió.
        assert arrancado.wait(timeout=10)
    finally:
        sigue.set()
        cli.post("/api/detener")


def test_amplia_y_arranca_la_escritura_sin_pedir_confirmacion(proyecto):
    cli = cliente(proyecto, arquitecto(5))
    cli.post("/api/ampliar", json={"capitulos": 2})
    final = esperar(cli, lambda e: (e.get("ampliacion") or {}).get("estado") == "generando")
    assert final["ampliacion"]["estado"] == "generando"
    biblia = json.loads((proyecto / "salida" / "biblia.json").read_text(encoding="utf-8"))
    config = json.loads((proyecto / "config.json").read_text(encoding="utf-8"))
    assert len(biblia["outline"]) == 5
    assert config["estructura"]["num_capitulos"] == 5


# ---------------------------------------------------------------------------
# 1. El outline se puede leer en cuanto existe
# ---------------------------------------------------------------------------


def test_el_outline_aparece_antes_de_que_haya_ningun_capitulo_escrito(proyecto):
    """Lo que sustituye a la confirmación humana que se quitó."""
    cli = cliente(proyecto, arquitecto(5), GENERACION_LARGA)
    try:
        cli.post("/api/ampliar", json={"capitulos": 2})
        estado = esperar(cli, lambda e: e.get("outline_nuevo"))
        nuevas = estado["outline_nuevo"]
        assert [e["capitulo"] for e in nuevas] == [4, 5]
        assert all(e.get("sinopsis") for e in nuevas)
        # Y todavía no hay ni un capítulo nuevo escrito.
        assert not (proyecto / "salida" / "capitulos" / "cap-04.md").exists()
    finally:
        cli.post("/api/detener")


def test_el_historico_anuncia_que_el_plan_ya_se_puede_leer(proyecto):
    cli = cliente(proyecto, arquitecto(5), GENERACION_LARGA)
    try:
        cli.post("/api/ampliar", json={"capitulos": 2})
        estado = esperar(cli, lambda e: any(
            "Ya se puede leer" in h["frase"] for h in e.get("historial", [])))
        assert any("Plan nuevo listo y validado" in h["frase"]
                   for h in estado["historial"])
    finally:
        cli.post("/api/detener")


# ---------------------------------------------------------------------------
# 2. Se puede detener en cualquier fase
# ---------------------------------------------------------------------------


def test_se_puede_detener_mientras_trabaja_el_arquitecto(proyecto):
    """El caso que hace que juntar las dos operaciones no sea un salto al vacío."""
    sigue = threading.Event()
    arrancado = threading.Event()
    cli = cliente(proyecto, arquitecto(espera=sigue, avisar=arrancado))
    antes = (proyecto / "salida" / "biblia.json").read_bytes()

    cli.post("/api/ampliar", json={"capitulos": 2})
    assert arrancado.wait(timeout=10)
    r = cli.post("/api/detener")
    sigue.set()

    assert r.json()["paro"] is True
    estado = esperar(cli, lambda e: (e.get("ampliacion") or {}).get("estado") == "detenida")
    assert estado["ampliacion"]["estado"] == "detenida"
    # No se generó nada y la novela quedó como estaba.
    assert (proyecto / "salida" / "biblia.json").read_bytes() == antes
    assert not (proyecto / "salida" / "capitulos" / "cap-04.md").exists()


def test_detener_despues_del_outline_no_escribe_capitulos(proyecto):
    """Leer el plan, no convencer, y parar: cuesta el arquitecto, no la novela."""
    cli = cliente(proyecto, arquitecto(5), GENERACION_LARGA)
    cli.post("/api/ampliar", json={"capitulos": 2})
    esperar(cli, lambda e: e.get("outline_nuevo"))
    cli.post("/api/detener")
    estado = cli.get("/api/generacion").json()
    assert estado["viva"] is False
    assert not (proyecto / "salida" / "capitulos" / "cap-04.md").exists()


# ---------------------------------------------------------------------------
# 3. Si algo falla, no se genera nada
# ---------------------------------------------------------------------------


def test_si_el_arquitecto_falla_no_se_lanza_la_generacion(proyecto):
    antes = (proyecto / "salida" / "biblia.json").read_bytes()
    cli = cliente(proyecto, lambda prompt: (0, "no soy json", ""))
    cli.post("/api/ampliar", json={"capitulos": 2})
    estado = esperar(cli, lambda e: (e.get("ampliacion") or {}).get("estado") == "fallida")
    assert estado["viva"] is False
    assert estado["ampliacion"]["error"]["mensaje"]
    assert (proyecto / "salida" / "biblia.json").read_bytes() == antes
    assert json.loads((proyecto / "config.json").read_text(
        encoding="utf-8"))["estructura"]["num_capitulos"] == 3


def test_un_fallo_de_ampliacion_se_cuenta_en_lenguaje_llano(proyecto):
    cli = cliente(proyecto, lambda prompt: (0, "no soy json", ""))
    cli.post("/api/ampliar", json={"capitulos": 2})
    estado = esperar(cli, lambda e: (e.get("ampliacion") or {}).get("estado") == "fallida")
    assert "La ampliación no salió adelante" in " ".join(
        h["frase"] for h in estado["historial"])


# ---------------------------------------------------------------------------
# El indicador de fases
# ---------------------------------------------------------------------------


def test_durante_la_fase_del_arquitecto_no_dice_sin_actividad(proyecto):
    """El motivo de todo el indicador: aquí `estado.json` no cambia y antes
    la pantalla decía «sin actividad» mientras el servidor trabajaba."""
    sigue = threading.Event()
    arrancado = threading.Event()
    cli = cliente(proyecto, arquitecto(espera=sigue, avisar=arrancado))
    try:
        cli.post("/api/ampliar", json={"capitulos": 2})
        assert arrancado.wait(timeout=10)
        estado = esperar(cli, lambda e: e.get("fase") == narracion.FASE_ARQUITECTO)
        assert estado["hay_algo_en_marcha"] is True
        assert "El arquitecto está diseñando qué pasa en los capítulos 4 y 5" == estado["frase"]
        assert estado["segundos_en_fase"] is not None
        assert "sin actividad" not in (estado["frase"] or "").lower()
    finally:
        sigue.set()
        cli.post("/api/detener")


def test_el_historico_guarda_las_fases_por_las_que_se_ha_pasado(proyecto):
    cli = cliente(proyecto, arquitecto(5))
    cli.post("/api/ampliar", json={"capitulos": 2})
    estado = esperar(cli, lambda e: (e.get("ampliacion") or {}).get("estado") == "generando")
    frases = " | ".join(h["frase"] for h in estado["historial"])
    assert "Copiando la novela actual" in frases
    assert "El arquitecto está diseñando" in frases
    assert "Plan nuevo listo" in frases


def test_sin_nada_en_marcha_lo_dice_con_lo_ultimo_que_paso(proyecto):
    cli = cliente(proyecto, arquitecto(5))
    estado = cli.get("/api/generacion").json()
    assert estado["hay_algo_en_marcha"] is False
    assert "No hay nada en marcha" in estado["frase"]


def test_la_primera_lectura_no_anuncia_capitulos_viejos_como_recien_hechos(proyecto):
    """Al abrir el panel sobre una novela terminada hace días, el histórico no
    puede llenarse de «Capítulo 1 aprobado limpio»."""
    cli = cliente(proyecto, arquitecto(5))
    primera = cli.get("/api/generacion").json()
    segunda = cli.get("/api/generacion").json()
    for estado in (primera, segunda):
        assert not any("aprobado limpio" in h["frase"] for h in estado["historial"])


def test_el_historico_no_repite_la_misma_frase(proyecto):
    """El panel pregunta cada pocos segundos; un histórico con la misma línea
    cuarenta veces no deja seguir nada."""
    sigue = threading.Event()
    arrancado = threading.Event()
    cli = cliente(proyecto, arquitecto(espera=sigue, avisar=arrancado))
    try:
        cli.post("/api/ampliar", json={"capitulos": 2})
        assert arrancado.wait(timeout=10)
        for _ in range(5):
            estado = cli.get("/api/generacion").json()
        frases = [h["frase"] for h in estado["historial"]]
        assert len(frases) == len(set(frases))
    finally:
        sigue.set()
        cli.post("/api/detener")


def test_generar_suelto_sigue_existiendo(proyecto):
    """Se mantiene para regenerar sin ampliar."""
    cli = cliente(proyecto, arquitecto(5))
    r = cli.post("/api/generar")
    assert r.status_code == 200
    esperar(cli, lambda e: not e["viva"])
