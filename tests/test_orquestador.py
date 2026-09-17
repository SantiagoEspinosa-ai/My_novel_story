"""Prueba de humo del pipeline minimo, de extremo a extremo y SIN red.

Se sustituye el cliente de modelos por uno falso que devuelve respuestas
preparadas. Asi se comprueba que las piezas encajan (config, biblia, contexto,
estado y escritura de archivos) sin gastar una sola llamada real.
"""

import json

import pytest

from src import agentes, estado as modulo_estado, orquestador
from tests.ayudas import biblia_valida, config_minima
from tests.test_agentes import ClienteFalso, ENTORNO


# Referencia a la clase de verdad, guardada ANTES de que ningun test la
# sustituya por el doble. Sin esto, la segunda llamada a `preparar` dentro de un
# mismo test construiria el cliente a traves del nombre ya parcheado y
# devolveria el cliente de la primera ejecucion.
CLIENTE_REAL = agentes.ClienteModelos


class _Modelo:
    def __init__(self, identificador):
        self.id = identificador


class _Catalogo:
    def __init__(self, identificadores):
        self.data = [_Modelo(i) for i in identificadores]


class ClienteFalsoConCatalogo(ClienteFalso):
    """Como el cliente falso de test_agentes, mas el catalogo de modelos."""

    def __init__(self, respuestas, slugs):
        super().__init__(respuestas)
        cliente = self

        class _Modelos:
            def list(self):
                return _Catalogo(slugs)

        self.models = _Modelos()


def preparar(tmp_path, respuestas, monkeypatch, num_capitulos=2, slugs=None):
    """Monta una configuracion de juguete y engancha el cliente falso."""
    config = config_minima(num_capitulos=num_capitulos)
    config["runtime"]["directorio_salida"] = str(tmp_path)
    if slugs is None:
        slugs = agentes.slugs_configurados(config)

    falso = ClienteFalsoConCatalogo(respuestas, slugs)
    cliente = CLIENTE_REAL(
        config, entorno=dict(ENTORNO), cliente=falso, dormir=lambda s: None
    )
    monkeypatch.setattr(
        orquestador.agentes, "ClienteModelos", lambda *a, **k: cliente
    )
    return config, cliente


def respuestas_completas(num_capitulos=2):
    """Biblia valida mas un capitulo por cada numero pedido."""
    respuestas = [json.dumps(biblia_valida(num_capitulos))]
    for numero in range(1, num_capitulos + 1):
        respuestas.append(
            "# Capitulo {0} — Titulo\n\nTexto del capitulo {0}.".format(numero)
        )
    return respuestas


# ---------------------------------------------------------------------------
# Camino feliz
# ---------------------------------------------------------------------------


def test_el_pipeline_genera_biblia_y_capitulos(tmp_path, monkeypatch):
    config, cliente = preparar(tmp_path, respuestas_completas(2), monkeypatch)

    estado = orquestador.ejecutar(config)

    assert (tmp_path / "biblia.json").is_file()
    assert (tmp_path / "capitulos" / "cap-01.md").is_file()
    assert (tmp_path / "capitulos" / "cap-02.md").is_file()
    assert estado["capitulos_aprobados"] == [1, 2]
    assert cliente.llamadas == 3          # arquitecto + dos capitulos


def test_el_escritor_recibe_el_capitulo_anterior_completo(tmp_path, monkeypatch):
    config, cliente = preparar(tmp_path, respuestas_completas(2), monkeypatch)

    orquestador.ejecutar(config)

    mensaje_del_segundo = cliente._cliente.peticiones[2]["messages"][1]["content"]
    assert "CAPITULO_ANTERIOR:" in mensaje_del_segundo
    assert "Texto del capitulo 1." in mensaje_del_segundo


def test_el_estado_queda_escrito_tras_cada_capitulo(tmp_path, monkeypatch):
    config, _ = preparar(tmp_path, respuestas_completas(2), monkeypatch)

    orquestador.ejecutar(config)

    estado = json.loads((tmp_path / "estado.json").read_text(encoding="utf-8"))
    assert estado["capitulos_aprobados"] == [1, 2]
    assert estado["modelo_actual"] == "proveedor/barato"   # primer peldano


# ---------------------------------------------------------------------------
# Reanudacion
# ---------------------------------------------------------------------------


def test_al_reanudar_no_se_regenera_lo_ya_hecho(tmp_path, monkeypatch):
    config, _ = preparar(tmp_path, respuestas_completas(2), monkeypatch)
    orquestador.ejecutar(config)

    # Segunda ejecucion: si pidiera algo al modelo, el cliente falso no tiene
    # mas respuestas y el test fallaria.
    config, cliente = preparar(tmp_path, [], monkeypatch)
    orquestador.ejecutar(config)

    assert cliente.llamadas == 0


def test_al_reanudar_continua_por_el_capitulo_pendiente(tmp_path, monkeypatch):
    config, _ = preparar(tmp_path, respuestas_completas(2)[:2], monkeypatch, 2)
    orquestador.ejecutar(config)            # solo llega al capitulo 1
    assert not (tmp_path / "capitulos" / "cap-02.md").exists()

    config, cliente = preparar(
        tmp_path, ["# Capitulo 2 — Titulo\n\nTexto del capitulo 2."], monkeypatch, 2
    )
    orquestador.ejecutar(config)

    assert (tmp_path / "capitulos" / "cap-02.md").is_file()
    assert cliente.llamadas == 1            # no se repitio ni la biblia ni el 1


# ---------------------------------------------------------------------------
# Reglas inviolables
# ---------------------------------------------------------------------------


def test_un_capitulo_fallido_no_detiene_la_generacion(tmp_path, monkeypatch):
    """Regla 1: ningun capitulo detiene la generacion.

    Y ademas: el capitulo que no llego a generarse se queda PENDIENTE, no
    marcado como hecho. Un fallo de red pasajero no puede dejar un agujero
    permanente en el manuscrito.
    """
    respuestas = [
        json.dumps(biblia_valida(2)),
        ConnectionError("cae la red"),      # el capitulo 1 falla del todo
        ConnectionError("cae la red"),
        ConnectionError("cae la red"),
        "# Capitulo 2 — Titulo\n\nTexto del capitulo 2.",
    ]
    config, _ = preparar(tmp_path, respuestas, monkeypatch)

    estado = orquestador.ejecutar(config)

    assert estado["capitulos_aprobados"] == [2]
    assert (tmp_path / "capitulos" / "cap-02.md").is_file()
    assert modulo_estado.capitulos_pendientes(estado, 2) == [1]


def test_al_superar_el_limite_de_llamadas_se_para_de_forma_ordenada(tmp_path, monkeypatch):
    config, cliente = preparar(tmp_path, respuestas_completas(2), monkeypatch)
    cliente.llamadas_max_totales = 2        # arquitecto + un capitulo

    estado = orquestador.ejecutar(config)

    assert estado["capitulos_aprobados"] == [1]
    assert (tmp_path / "estado.json").is_file()   # el progreso queda guardado


def test_una_biblia_invalida_aborta_tras_el_reintento(tmp_path, monkeypatch):
    """Sin biblia no hay novela: esta es una de las dos excepciones al no abortar."""
    mala = biblia_valida(2)
    mala["outline"] = mala["outline"][:1]   # un capitulo de menos
    config, _ = preparar(tmp_path, [json.dumps(mala), json.dumps(mala)], monkeypatch)

    with pytest.raises(SystemExit) as error:
        orquestador.ejecutar(config)

    assert "ABORTADO" in str(error.value)


def test_un_slug_inexistente_aborta_antes_de_gastar_nada(tmp_path, monkeypatch):
    config, cliente = preparar(
        tmp_path, respuestas_completas(2), monkeypatch, slugs=["otro/modelo"]
    )

    with pytest.raises(SystemExit) as error:
        orquestador.ejecutar(config)

    assert "no existen en OpenRouter" in str(error.value)
    assert cliente.llamadas == 0


def test_la_biblia_se_reintenta_con_el_error_delante(tmp_path, monkeypatch):
    mala = biblia_valida(2)
    mala["outline"] = mala["outline"][:1]
    config, cliente = preparar(
        tmp_path,
        [json.dumps(mala)] + respuestas_completas(2),
        monkeypatch,
    )

    orquestador.ejecutar(config)

    segundo_mensaje = cliente._cliente.peticiones[1]["messages"][1]["content"]
    assert "ERROR_ANTERIOR" in segundo_mensaje
    assert "outline tiene 1 entradas" in segundo_mensaje
