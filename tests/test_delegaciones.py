"""Tests de src/delegaciones.py: el registro local de delegaciones y tokens.

Lo que se comprueba aqui es la propiedad que hace util al registro: que **toda
delegacion emitida queda anotada**, incluidas las que no dejaron nada
aprovechable, y que despues se puede separar el gasto que acabo en el
manuscrito del que se fue en intentos descartados.

Ningun test sale a la red ni delega en nadie: el modulo solo manipula
diccionarios.
"""

import json

import pytest

from src import delegaciones
from src import estado as modulo_estado
from src import orquestacion
from tests.ayudas import biblia_valida, veredicto


def _silencio(*args, **kwargs):
    """Sustituye a `print` en los comandos: los tests no necesitan la charla."""


def _archivo(tmp, nombre, contenido):
    ruta = tmp / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


def _preparar(entorno, tmp_path):
    """Generacion iniciada y con biblia guardada, lista para el capitulo 1."""
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    crudo = json.dumps(biblia_valida(3), ensure_ascii=False)
    orquestacion.cmd_registrar_biblia(
        config, salida, _archivo(tmp_path, "biblia.raw", crudo), escribir=_silencio
    )
    return config, salida


# ---------------------------------------------------------------------------
# El modulo, aislado
# ---------------------------------------------------------------------------


def test_anotar_suma_al_contador_y_deja_entrada():
    estado = {}
    entrada = delegaciones.anotar(
        estado, "escritor", modelo="sonnet", capitulo=2, intento=1,
        tokens_in=1000, tokens_out=800,
    )
    assert entrada["n"] == 1
    assert estado["delegaciones"] == 1
    assert delegaciones.listar(estado)[0]["rol"] == "escritor"
    assert entrada["en_manuscrito"] is None


def test_una_delegacion_sin_tokens_cuenta_igual():
    """Vale mas un recuento de delegaciones exacto que uno de tokens exigente."""
    estado = {}
    delegaciones.anotar(estado, "estilo", modelo="haiku", capitulo=1, intento=1)
    suma = delegaciones.totales(estado)
    assert suma["delegaciones"] == 1
    assert suma["tokens_in"] == 0
    assert suma["sin_tokens"] == 1


def test_los_tokens_ilegibles_no_tumban_la_anotacion():
    estado = {}
    entrada = delegaciones.anotar(
        estado, "genero", tokens_in="muchos", tokens_out=None
    )
    assert entrada["tokens_in"] is None
    assert estado["delegaciones"] == 1


def test_marcar_en_manuscrito_separa_el_intento_ganador():
    estado = {}
    delegaciones.anotar(estado, "escritor", capitulo=1, intento=1, tokens_out=500)
    delegaciones.anotar(estado, "estilo", capitulo=1, intento=1, tokens_out=100)
    delegaciones.anotar(estado, "escritor", capitulo=1, intento=2, tokens_out=600)
    delegaciones.anotar(estado, "resumidor", capitulo=1, tokens_out=50)

    delegaciones.marcar_en_manuscrito(estado, 1, 2)

    reparto = delegaciones.reparto_manuscrito(estado)
    assert reparto["en_manuscrito"]["tokens_out"] == 600
    assert reparto["descartado"]["tokens_out"] == 600  # 500 del intento 1 + 100
    # El resumidor no tiene numero de intento: la pregunta no le aplica.
    assert reparto["no_aplica"]["tokens_out"] == 50


def test_marcar_en_manuscrito_no_toca_otros_capitulos():
    estado = {}
    delegaciones.anotar(estado, "escritor", capitulo=1, intento=1)
    delegaciones.anotar(estado, "escritor", capitulo=2, intento=1)
    delegaciones.marcar_en_manuscrito(estado, 1, 1)
    entradas = delegaciones.listar(estado)
    assert entradas[0]["en_manuscrito"] is True
    assert entradas[1]["en_manuscrito"] is None


def test_por_rol_sigue_el_orden_de_actuacion():
    estado = {}
    delegaciones.anotar(estado, "resumidor")
    delegaciones.anotar(estado, "escritor")
    delegaciones.anotar(estado, "arquitecto")
    assert [rol for rol, _ in delegaciones.por_rol(estado)] == [
        "arquitecto", "escritor", "resumidor"
    ]


def test_un_estado_antiguo_sin_detalle_no_es_coherente():
    """Una generacion anterior al registro tiene contador pero no desglose."""
    assert delegaciones.coherente({"delegaciones": 59}) is False
    assert delegaciones.coherente({"delegaciones": 0}) is True


# ---------------------------------------------------------------------------
# Integrado con la orquestacion
# ---------------------------------------------------------------------------


def test_los_comandos_de_registro_anotan_rol_modelo_y_tokens(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."),
        tokens_in=9000, tokens_out=1500, escribir=_silencio,
    )
    orquestacion.cmd_registrar_veredicto(
        config, salida, 1, "estilo",
        _archivo(tmp_path, "v.raw", veredicto("estilo", 1, "PASA", [])),
        tokens_in=4000, tokens_out=300, escribir=_silencio,
    )

    entradas = delegaciones.listar(modulo_estado.cargar(salida))
    assert [e["rol"] for e in entradas] == ["arquitecto", "escritor", "estilo"]
    assert entradas[0]["modelo"] == config["modelos"]["arquitecto"]
    assert entradas[1]["modelo"] == config["modelos"]["escalera_escritor"][0]
    assert entradas[1]["tokens_in"] == 9000
    assert entradas[2]["modelo"] == config["modelos"]["validadores"]
    assert entradas[2]["intento"] == 1


def test_una_respuesta_ilegible_tambien_gasta_delegacion(entorno, tmp_path):
    """El fallo que hacia que el contador dijera 59 donde fueron 61.

    Antes, una respuesta que no parseaba hacia fallar el comando ANTES de sumar,
    asi que el reintento se contaba una sola vez. Ahora la delegacion se anota
    en cuanto hay respuesta en disco, y solo despues se intenta interpretar.
    """
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    for validador in ("continuidad", "genero", "estilo"):
        orquestacion.cmd_registrar_veredicto(
            config, salida, 1, validador,
            _archivo(tmp_path, "v.raw", veredicto(validador, 1, "PASA", [])),
            escribir=_silencio,
        )
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    antes = modulo_estado.cargar(salida)["delegaciones"]

    # El resumidor devuelve algo que no es JSON: la delegacion se gasto igual.
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_registrar_resumen(
            config, salida, 1, _archivo(tmp_path, "r.raw", "lo siento, no puedo"),
            tokens_in=2000, tokens_out=40, escribir=_silencio,
        )
    assert modulo_estado.cargar(salida)["delegaciones"] == antes + 1

    # Y el reintento que viene detras se paga otra vez.
    orquestacion.cmd_registrar_resumen(
        config, salida, 1,
        _archivo(tmp_path, "r2.raw", json.dumps({"resumen": "Pasan cosas."})),
        tokens_in=2000, tokens_out=60, escribir=_silencio,
    )
    assert modulo_estado.cargar(salida)["delegaciones"] == antes + 2


def test_resolver_marca_que_intento_acabo_en_el_manuscrito(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."),
        tokens_out=500, escribir=_silencio,
    )
    for validador in ("continuidad", "genero", "estilo"):
        orquestacion.cmd_registrar_veredicto(
            config, salida, 1, validador,
            _archivo(tmp_path, "v.raw", veredicto(validador, 1, "PASA", [])),
            tokens_out=100, escribir=_silencio,
        )
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    reparto = delegaciones.reparto_manuscrito(modulo_estado.cargar(salida))
    assert reparto["en_manuscrito"]["delegaciones"] == 4  # escritor + 3 validadores
    assert reparto["descartado"]["delegaciones"] == 0


def test_registrar_delegacion_anota_lo_que_no_dejo_resultado(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    antes = modulo_estado.cargar(salida)["delegaciones"]
    orquestacion.cmd_registrar_delegacion(
        config, salida, "escritor", modelo="opus", capitulo=2, intento=1,
        tokens_in=8000, tokens_out=0, nota="devolvio vacio", escribir=_silencio,
    )
    estado = modulo_estado.cargar(salida)
    assert estado["delegaciones"] == antes + 1
    assert delegaciones.listar(estado)[-1]["nota"] == "devolvio vacio"


def test_el_informe_se_regenera_sin_la_sesion_que_genero(entorno, tmp_path):
    """El registro vive en estado.json, no en .tmp/, y sobrevive al ensamblado."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."),
        tokens_in=9000, tokens_out=1500, escribir=_silencio,
    )
    for validador in ("continuidad", "genero", "estilo"):
        orquestacion.cmd_registrar_veredicto(
            config, salida, 1, validador,
            _archivo(tmp_path, "v.raw", veredicto(validador, 1, "PASA", [])),
            tokens_in=4000, tokens_out=300, escribir=_silencio,
        )
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)

    # `ensamblar` borro .tmp/. El informe se vuelve a sacar igualmente.
    orquestacion.cmd_informe(config, salida, escribir=_silencio)
    texto = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")
    assert "Coste: delegaciones y tokens" in texto
    assert "escritor" in texto
    assert "9.000" in texto  # los tokens de entrada del escritor, con miles
