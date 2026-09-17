"""Tests del resumidor y del ensamblado: las dos piezas que cierran la novela.

Se apoyan en las ayudas de `tests/test_orquestacion.py` para no reescribir el
camino feliz (escribir, validar, resolver, resumir) en cada test. Es el mismo
patron que ya usaban los tests de la arquitectura anterior.

Ningun test delega en un subagente ni sale a la red: donde la ejecucion real
pondria la respuesta de un modelo, aqui hay un archivo de juguete.
"""

import pytest

from src import estado as modulo_estado
from src import orquestacion
from tests.ayudas import problema, veredicto
from tests.test_orquestacion import (
    _archivo,
    _cerrar_capitulo,
    _fallar_capitulo,
    _preparar,
    _resumir,
    _silencio,
    _validar_intento,
)


# ---------------------------------------------------------------------------
# Resumenes
# ---------------------------------------------------------------------------


def test_el_resumidor_trabaja_sobre_el_texto_cerrado_no_sobre_un_intento(
    entorno, tmp_path
):
    """Resumir un texto que todavia puede reescribirse describiria una version muerta."""
    config, salida = _preparar(entorno, tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 1, ["media"])
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "LA VERSION BUENA."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    lineas = []
    orquestacion.cmd_ventana(config, salida, "resumidor", 1, escribir=lineas.append)
    texto = "\n".join(lineas)
    assert "LA VERSION BUENA." in texto
    assert "Intento numero 1." not in texto


def test_la_ventana_del_resumidor_no_lleva_el_outline(entorno, tmp_path):
    """Levanta acta de lo escrito, no del plan.

    Si recibiera el outline, resumiria el outline: es mas facil de resumir y
    suena mejor. Y entonces el escritor del capitulo siguiente creeria que pasa
    lo que estaba previsto, no lo que de verdad pasa en la novela.
    """
    config, salida = _preparar(entorno, tmp_path)
    _cerrar_capitulo(config, salida, tmp_path, 1, "Texto del capitulo uno.")

    lineas = []
    orquestacion.cmd_ventana(config, salida, "resumidor", 1, escribir=lineas.append)
    texto = "\n".join(lineas)
    assert "Sinopsis del capitulo 1." not in texto
    assert "OUTLINE" not in texto
    assert "BIBLIA" not in texto


def test_el_ultimo_capitulo_no_se_resume(entorno, tmp_path):
    """Nadie leeria ese resumen: despues del ultimo capitulo no hay ninguno."""
    config, salida = _preparar(entorno, tmp_path)
    for capitulo in (1, 2, 3):
        _cerrar_capitulo(
            config, salida, tmp_path, capitulo, "Capitulo {0}.".format(capitulo)
        )

    pendientes = orquestacion.capitulos_sin_resumen(
        config, salida, modulo_estado.cargar(salida)
    )
    assert pendientes == []
    assert not orquestacion.ruta_resumen(salida, 3).is_file()
    assert orquestacion.siguiente_paso(config, salida)["paso"] == "ensamblar"


def test_un_resumen_ilegible_se_rechaza_y_ofrece_la_valvula_de_escape(
    entorno, tmp_path
):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    with pytest.raises(orquestacion.ErrorDeOrquestacion) as error:
        orquestacion.cmd_registrar_resumen(
            config, salida, 1, _archivo(tmp_path, "r.raw", "un resumen suelto"),
            escribir=_silencio,
        )
    assert "--usar-sinopsis" in str(error.value)


def test_la_valvula_de_escape_cae_a_la_sinopsis_sin_delegar(entorno, tmp_path):
    """Regla 1: la novela no se para por un resumen de tres frases."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    antes = modulo_estado.cargar(salida)["delegaciones"]
    orquestacion.cmd_registrar_resumen(
        config, salida, 1, usar_sinopsis=True, escribir=_silencio
    )

    guardado = orquestacion.ruta_resumen(salida, 1).read_text(encoding="utf-8").strip()
    assert guardado == "Sinopsis del capitulo 1."
    assert modulo_estado.cargar(salida)["delegaciones"] == antes


def test_un_resumen_envuelto_en_vallas_se_acepta(entorno, tmp_path):
    valla = chr(96) * 3
    config, salida = _preparar(entorno, tmp_path)
    _cerrar_capitulo(config, salida, tmp_path, 1, "Texto.")

    crudo = (
        valla + 'json\n'
        '{"capitulo": 1, "resumen": "Marta entra en la casa."}\n'
        + valla
    )
    orquestacion.cmd_registrar_resumen(
        config, salida, 1, _archivo(tmp_path, "r.raw", crudo), escribir=_silencio
    )
    guardado = orquestacion.ruta_resumen(salida, 1).read_text(encoding="utf-8")
    assert "Marta entra en la casa." in guardado


def test_un_resumen_sin_contenido_se_rechaza(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    _cerrar_capitulo(config, salida, tmp_path, 1, "Texto.")
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_registrar_resumen(
            config, salida, 1,
            _archivo(tmp_path, "r.raw", '{"capitulo": 1, "resumen": "   "}'),
            escribir=_silencio,
        )


# ---------------------------------------------------------------------------
# Ensamblado
# ---------------------------------------------------------------------------


def _novela_completa(entorno, tmp_path):
    """Tres capitulos cerrados limpiamente, con sus ventanas medidas."""
    config, salida = _preparar(entorno, tmp_path)
    for capitulo in (1, 2, 3):
        # Pedir la ventana es lo que deja el apunte de tokens para el informe.
        orquestacion.cmd_ventana(config, salida, "escritor", capitulo, escribir=_silencio)
        _cerrar_capitulo(
            config, salida, tmp_path, capitulo,
            "# Capitulo {0} — Titulo\n\nTexto del capitulo {0}.".format(capitulo),
        )
    return config, salida


def test_el_manuscrito_lleva_portada_y_los_capitulos_en_orden(entorno, tmp_path):
    config, salida = _novela_completa(entorno, tmp_path)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)

    texto = orquestacion.ruta_manuscrito(salida).read_text(encoding="utf-8")
    assert texto.startswith("# La casa de la calle Duero")
    assert "*Terror*" in texto
    assert texto.index("Texto del capitulo 1.") < texto.index("Texto del capitulo 2.")
    assert texto.index("Texto del capitulo 2.") < texto.index("Texto del capitulo 3.")


def test_la_portada_no_destripa_la_trama(entorno, tmp_path):
    """Quien abre el manuscrito por arriba no quiere leer la premisa."""
    config, salida = _novela_completa(entorno, tmp_path)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    portada = orquestacion.ruta_manuscrito(salida).read_text(
        encoding="utf-8"
    ).split("---")[0]
    assert "restauradora" not in portada          # la premisa
    assert "Ya estuvo en esa casa" not in portada  # un secreto


def test_el_informe_cuenta_lo_que_paso_en_cada_capitulo(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_ventana(config, salida, "escritor", 1, escribir=_silencio)
    _fallar_capitulo(config, salida, tmp_path, 1, 2, ["alta", "media"])
    _cerrar_capitulo(config, salida, tmp_path, 1, "Capitulo uno.")
    for capitulo in (2, 3):
        orquestacion.cmd_ventana(
            config, salida, "escritor", capitulo, escribir=_silencio
        )
        _cerrar_capitulo(
            config, salida, tmp_path, capitulo, "Capitulo {0}.".format(capitulo)
        )

    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")

    assert "Informe de validacion — La casa de la calle Duero" in informe
    assert "Capitulo 1 — APROBADO" in informe
    assert "Recorrido de los intentos" in informe   # fueron tres, y se ven
    assert "sonnet" in informe                      # la escalera subio y consta
    assert "Presupuesto de contexto" in informe


def test_el_informe_lista_los_problemas_que_siguen_en_el_texto(entorno, tmp_path):
    """"Sigue estando en lo que vas a leer" no es lo mismo que "se detecto"."""
    config, salida = _preparar(entorno, tmp_path)
    crudo = veredicto(
        "estilo", 1, "FALLO", [problema("alta", "Repites la palabra sombra.")]
    )
    for numero in range(6):
        orquestacion.cmd_registrar_intento(
            config, salida, 1,
            _archivo(tmp_path, "cap.md", "Intento {0}.".format(numero)),
            escribir=_silencio,
        )
        _validar_intento(config, salida, tmp_path, 1, {"estilo": crudo})
        orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    _resumir(config, salida, tmp_path, 1)
    for capitulo in (2, 3):
        _cerrar_capitulo(
            config, salida, tmp_path, capitulo, "Capitulo {0}.".format(capitulo)
        )

    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")

    assert "ACEPTADO_POR_PUNTUACION" in informe
    assert "Repites la palabra sombra." in informe
    assert "Evidencia:" in informe


def test_el_informe_avisa_de_los_validadores_que_no_devolvieron_json(
    entorno, tmp_path
):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {"genero": "hoy no contesto"})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    _cerrar_capitulo(config, salida, tmp_path, 1, "Segundo intento, este si.")

    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")
    assert "INDETERMINADO" in informe
    assert "modelos.validadores" in informe


def test_el_informe_mide_las_ventanas_del_escritor(entorno, tmp_path):
    """Criterio de aceptacion 9 del spec, convertido en una tabla."""
    config, salida = _novela_completa(entorno, tmp_path)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")
    assert "Tokens estimados de la ventana del escritor" in informe
    # Con tres capitulos solo hay uno comparable (el 3), asi que el informe dice
    # que no se puede medir en vez de dar una alarma falsa.
    assert "demasiado corta para medir" in informe


def test_el_informe_avisa_si_la_ventana_crece_con_el_numero_de_capitulo(entorno):
    """La senal de alarma mas importante del informe, en un caso de laboratorio."""
    from src import ensamblador

    config, _ = entorno
    capitulos = [
        {"numero": 3, "estado": "APROBADO", "intentos": [],
         "ventana": {"tokens": 1000, "recortes": []}},
        {"numero": 12, "estado": "APROBADO", "intentos": [],
         "ventana": {"tokens": 4000, "recortes": ["resumenes acortados"]}},
    ]
    texto = ensamblador.informe({"titulo": "X"}, config, "2026-01-01", capitulos, {})
    assert "ALARMA" in texto
    assert "creciendo con N" in texto


def test_sin_alarma_cuando_la_ventana_se_mantiene(entorno):
    from src import ensamblador

    config, _ = entorno
    capitulos = [
        {"numero": 3, "estado": "APROBADO", "intentos": [],
         "ventana": {"tokens": 4000, "recortes": []}},
        {"numero": 12, "estado": "APROBADO", "intentos": [],
         "ventana": {"tokens": 3900, "recortes": []}},
    ]
    texto = ensamblador.informe({"titulo": "X"}, config, "2026-01-01", capitulos, {})
    assert "ALARMA" not in texto
    assert "el presupuesto de contexto aguanta" in texto


def test_ensamblar_borra_los_temporales(entorno, tmp_path):
    config, salida = _novela_completa(entorno, tmp_path)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    assert not orquestacion._tmp(salida).exists()


def test_conservar_intentos_deja_los_temporales(entorno, tmp_path):
    config, salida = _novela_completa(entorno, tmp_path)
    config["runtime"]["conservar_intentos"] = True
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    assert orquestacion._tmp(salida).exists()


def test_el_informe_se_escribe_antes_de_borrar_los_temporales(entorno, tmp_path):
    """Si se borrara primero, el informe saldria vacio y el dato ya no existiria."""
    config, salida = _novela_completa(entorno, tmp_path)
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")
    assert "| 1 | APROBADO | 1 | haiku |" in informe


def test_un_capitulo_sin_generar_no_se_inventa_en_el_manuscrito(entorno, tmp_path):
    """Un manuscrito con un capitulo vacio seria un manuscrito que miente."""
    config, salida = _preparar(entorno, tmp_path)
    _cerrar_capitulo(config, salida, tmp_path, 1, "Capitulo uno.")
    orquestacion.cmd_ensamblar(config, salida, escribir=_silencio)

    manuscrito = orquestacion.ruta_manuscrito(salida).read_text(encoding="utf-8")
    informe = orquestacion.ruta_informe(salida).read_text(encoding="utf-8")
    assert "Capitulo uno." in manuscrito
    assert "SIN_GENERAR" in informe
    assert "no llegó a generarse" in informe
