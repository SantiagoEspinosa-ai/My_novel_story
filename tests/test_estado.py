"""Tests del gestor de estado y de la reanudacion. Ninguno toca la red."""

import pytest

from src import estado as modulo
from tests.ayudas import config_minima


# ---------------------------------------------------------------------------
# Serializacion ida y vuelta
# ---------------------------------------------------------------------------


def test_estado_nuevo_tiene_todas_las_claves_del_contrato():
    estado = modulo.nuevo("proveedor/barato")

    for clave in modulo.CLAVES:
        assert clave in estado
    assert estado["capitulo_actual"] == 1
    assert estado["capitulos_aprobados"] == []


def test_guardar_y_cargar_devuelve_lo_mismo(tmp_path):
    estado = modulo.nuevo("proveedor/barato")
    modulo.aprobar_capitulo(estado, 1)
    modulo.aprobar_capitulo(estado, 2)
    modulo.marcar_capitulo(estado, 3)

    modulo.guardar(estado, tmp_path)

    assert modulo.cargar(tmp_path) == estado


def test_cargar_estado_inexistente_falla_con_mensaje_claro(tmp_path):
    with pytest.raises(modulo.ErrorDeEstado) as error:
        modulo.cargar(tmp_path)

    assert "No encuentro" in str(error.value)


def test_cargar_estado_roto_falla_con_mensaje_claro(tmp_path):
    (tmp_path / "estado.json").write_text("{roto", encoding="utf-8")

    with pytest.raises(modulo.ErrorDeEstado) as error:
        modulo.cargar(tmp_path)

    assert "no es JSON valido" in str(error.value)


def test_cargar_estado_incompleto_dice_que_claves_faltan(tmp_path):
    (tmp_path / "estado.json").write_text('{"capitulo_actual": 3}', encoding="utf-8")

    with pytest.raises(modulo.ErrorDeEstado) as error:
        modulo.cargar(tmp_path)

    assert "capitulos_aprobados" in str(error.value)


def test_guardar_no_deja_el_archivo_temporal(tmp_path):
    modulo.guardar(modulo.nuevo(), tmp_path)

    assert (tmp_path / "estado.json").is_file()
    assert not (tmp_path / "estado.json.tmp").exists()


# ---------------------------------------------------------------------------
# Transiciones
# ---------------------------------------------------------------------------


def test_aprobar_capitulo_no_duplica_y_ordena():
    estado = modulo.nuevo()
    modulo.aprobar_capitulo(estado, 2)
    modulo.aprobar_capitulo(estado, 1)
    modulo.aprobar_capitulo(estado, 2)

    assert estado["capitulos_aprobados"] == [1, 2]


def test_aprobar_un_capitulo_marcado_lo_desmarca():
    estado = modulo.nuevo()
    modulo.marcar_capitulo(estado, 4)

    modulo.aprobar_capitulo(estado, 4)

    assert estado["capitulos_marcados"] == []
    assert estado["capitulos_aprobados"] == [4]


def test_registrar_intento_suma_y_puede_cambiar_el_modelo():
    estado = modulo.nuevo("proveedor/barato")
    modulo.empezar_capitulo(estado, 3, "proveedor/barato")

    modulo.registrar_intento(estado)
    modulo.registrar_intento(estado, "proveedor/medio")

    assert estado["intento_actual"] == 2
    assert estado["modelo_actual"] == "proveedor/medio"
    assert estado["capitulo_actual"] == 3


def test_empezar_capitulo_pone_el_contador_de_intentos_a_cero():
    estado = modulo.nuevo()
    modulo.registrar_intento(estado)

    modulo.empezar_capitulo(estado, 2, "proveedor/barato")

    assert estado["intento_actual"] == 0


# ---------------------------------------------------------------------------
# Reanudacion
# ---------------------------------------------------------------------------


def test_capitulos_pendientes_salta_los_aprobados_y_los_marcados():
    estado = modulo.nuevo()
    modulo.aprobar_capitulo(estado, 1)
    modulo.aprobar_capitulo(estado, 2)
    modulo.marcar_capitulo(estado, 3)

    assert modulo.capitulos_pendientes(estado, 6) == [4, 5, 6]


def test_capitulos_pendientes_de_una_ejecucion_nueva_son_todos():
    assert modulo.capitulos_pendientes(modulo.nuevo(), 3) == [1, 2, 3]


def test_debe_reanudar_solo_si_hay_estado_y_la_config_lo_permite(tmp_path):
    config = config_minima()

    assert modulo.debe_reanudar(config, tmp_path) is False

    modulo.guardar(modulo.nuevo(), tmp_path)
    assert modulo.debe_reanudar(config, tmp_path) is True

    config["runtime"]["reanudar_si_existe_estado"] = False
    assert modulo.debe_reanudar(config, tmp_path) is False


def test_reanudar_continua_desde_el_capitulo_5(tmp_path):
    """Matar el proceso en el 5 y relanzar tiene que retomar en el 5, no en el 1."""
    config = config_minima(num_capitulos=12)
    primera = modulo.nuevo("proveedor/barato")
    for numero in (1, 2, 3, 4):
        modulo.aprobar_capitulo(primera, numero)
    modulo.empezar_capitulo(primera, 5, "proveedor/barato")
    modulo.registrar_intento(primera)
    modulo.guardar(primera, tmp_path)

    segunda, reanudado = modulo.cargar_o_nuevo(config, tmp_path)

    assert reanudado is True
    assert modulo.capitulos_pendientes(segunda, 12)[0] == 5
    assert segunda["capitulos_aprobados"] == [1, 2, 3, 4]


def test_sin_estado_previo_se_empieza_de_cero(tmp_path):
    config = config_minima()

    estado, reanudado = modulo.cargar_o_nuevo(config, tmp_path, "proveedor/barato")

    assert reanudado is False
    assert estado["capitulos_aprobados"] == []


def test_borrar_deja_el_directorio_sin_estado(tmp_path):
    modulo.guardar(modulo.nuevo(), tmp_path)

    modulo.borrar(tmp_path)

    assert modulo.existe(tmp_path) is False
