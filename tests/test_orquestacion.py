"""Tests de src/orquestacion.py: la maquina de estados de la generacion.

Lo que de verdad se comprueba aqui no es que cada funcion devuelva lo suyo, sino
la propiedad de la que depende el proyecto entero: **que el estado esta en los
archivos y no en la memoria de nadie**. Por eso casi todos los tests preguntan
`siguiente_paso` partiendo de cero, con lo unico que hay en disco. Si el
resultado dependiera de algo recordado, una sesion nueva no podria reanudar.

Ningun test delega en un subagente ni sale a la red: donde la ejecucion real
pondria la respuesta de un modelo, aqui hay un archivo de juguete.
"""

import json

import pytest

from src import biblia as modulo_biblia
from src import estado as modulo_estado
from src import orquestacion
from tests.ayudas import biblia_valida, config_minima, problema, veredicto


# ---------------------------------------------------------------------------
# Montaje
# ---------------------------------------------------------------------------


# La fixture `entorno` (config de juguete + salida en carpeta temporal) vive en
# tests/conftest.py, para que tests/test_ensamblador.py use exactamente la misma.


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


def _validar_intento(config, salida, tmp_path, capitulo, estados):
    """Registra los tres veredictos del ultimo intento de un capitulo.

    `estados` es un diccionario {validador: "PASA" | "FALLO" | texto crudo}.
    """
    for validador in ("continuidad", "genero", "estilo"):
        valor = estados.get(validador, "PASA")
        if valor in ("PASA", "FALLO"):
            problemas = [problema("media")] if valor == "FALLO" else []
            crudo = veredicto(validador, capitulo, valor, problemas)
        else:
            crudo = valor
        orquestacion.cmd_registrar_veredicto(
            config, salida, capitulo, validador,
            _archivo(tmp_path, "v-{0}.raw".format(validador), crudo),
            escribir=_silencio,
        )


def _resumir(config, salida, tmp_path, capitulo, texto=None):
    """Registra el resumen de un capitulo cerrado, como haria el resumidor."""
    crudo = json.dumps(
        {"capitulo": capitulo, "resumen": texto or "Pasa algo en el {0}.".format(capitulo)},
        ensure_ascii=False,
    )
    orquestacion.cmd_registrar_resumen(
        config, salida, capitulo,
        _archivo(tmp_path, "r.raw", crudo), escribir=_silencio,
    )


def _cerrar_capitulo(config, salida, tmp_path, capitulo, texto):
    """Escribe, valida con tres PASA, resuelve y resume. El camino feliz."""
    orquestacion.cmd_registrar_intento(
        config, salida, capitulo, _archivo(tmp_path, "cap.md", texto),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, capitulo, {})
    orquestacion.cmd_resolver(config, salida, capitulo, escribir=_silencio)
    if capitulo < config["estructura"]["num_capitulos"]:
        _resumir(config, salida, tmp_path, capitulo)


# ---------------------------------------------------------------------------
# La escalera
# ---------------------------------------------------------------------------


def test_la_escalera_sube_cada_dos_intentos(entorno):
    config, _ = entorno
    escalones = [orquestacion.escalon_de_intento(config, 0, n) for n in range(1, 7)]
    assert escalones == [0, 0, 1, 1, 2, 2]


def test_el_ultimo_escalon_absorbe_los_intentos_de_mas(entorno):
    """Por si alguien sube intentos_por_modelo a mitad de generacion."""
    config, _ = entorno
    assert orquestacion.escalon_de_intento(config, 0, 99) == 2
    assert orquestacion.modelo_de_escalon(config, 99) == "opus"


def test_arrancar_en_un_escalon_alto_deja_menos_intentos(entorno):
    """La escalera empieza donde se quedo; no vuelve al principio.

    Es la contrapartida de `mantener_voz_ganadora`: se gana coherencia de voz y
    se pierden los intentos de los escalones que se saltan.
    """
    config, _ = entorno
    assert orquestacion.intentos_maximos(config, 0) == 6
    assert orquestacion.intentos_maximos(config, 1) == 4
    assert orquestacion.intentos_maximos(config, 2) == 2


# ---------------------------------------------------------------------------
# La maquina de estados
# ---------------------------------------------------------------------------


def test_sin_estado_el_primer_paso_es_iniciar(entorno):
    config, salida = entorno
    assert orquestacion.siguiente_paso(config, salida)["paso"] == "iniciar"


def test_recien_iniciado_toca_el_arquitecto(entorno):
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["paso"] == "arquitecto"
    assert paso["modelo"] == "sonnet"


def test_con_biblia_toca_escribir_el_capitulo_1(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["paso"] == "escribir"
    assert (paso["capitulo"], paso["intento"], paso["modelo"]) == (1, 1, "haiku")


def test_con_un_intento_escrito_toca_validar_los_tres(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto del capitulo."),
        escribir=_silencio,
    )
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["paso"] == "validar"
    assert paso["faltan"] == ["continuidad", "genero", "estilo"]
    assert paso["modelo"] == "haiku"


def test_con_dos_veredictos_solo_falta_el_tercero(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    for validador in ("continuidad", "genero"):
        orquestacion.cmd_registrar_veredicto(
            config, salida, 1, validador,
            _archivo(tmp_path, "v.raw", veredicto(validador, 1, "PASA")),
            escribir=_silencio,
        )
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["faltan"] == ["estilo"]


def test_con_los_tres_veredictos_toca_resolver(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    assert orquestacion.siguiente_paso(config, salida)["paso"] == "resolver"


def test_el_paso_se_deduce_del_disco_y_no_de_la_memoria(entorno, tmp_path):
    """El test que justifica el diseno del modulo.

    Se pregunta el siguiente paso dos veces sin compartir nada entre las dos
    llamadas. Si el resultado dependiera de algo recordado en memoria, una
    sesion nueva no podria reanudar una novela a medias.
    """
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    primero = orquestacion.siguiente_paso(config, salida)
    segundo = orquestacion.siguiente_paso(config_minima(
        3, runtime={"directorio_salida": str(salida)}
    ), salida)
    assert primero == segundo


# ---------------------------------------------------------------------------
# Resolver: aprobar
# ---------------------------------------------------------------------------


def test_tres_pasa_aprueban_el_capitulo_y_escriben_el_texto(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "El texto bueno."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    assert orquestacion.ruta_capitulo(salida, 1).read_text(encoding="utf-8") == (
        "El texto bueno."
    )
    # El resumen todavia NO existe: lo escribe el paso siguiente, no `resolver`.
    assert not orquestacion.ruta_resumen(salida, 1).is_file()
    estado = modulo_estado.cargar(salida)
    assert estado["capitulos_aprobados"] == [1]
    assert estado["capitulos_marcados"] == []

    # Entre aprobar un capitulo y escribir el siguiente va el resumen: el texto
    # completo vive en .tmp/, que se borra al ensamblar.
    paso = orquestacion.siguiente_paso(config, salida)
    assert (paso["paso"], paso["capitulo"], paso["modelo"]) == ("resumir", 1, "haiku")
    _resumir(config, salida, tmp_path, 1)
    assert orquestacion.siguiente_paso(config, salida)["capitulo"] == 2


def test_un_solo_fallo_manda_reescribir(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto flojo."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {"estilo": "FALLO"})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    assert not orquestacion.ruta_capitulo(salida, 1).is_file()
    paso = orquestacion.siguiente_paso(config, salida)
    assert (paso["paso"], paso["capitulo"], paso["intento"]) == ("escribir", 1, 2)


def test_un_validador_ilegible_impide_aprobar(entorno, tmp_path):
    """Regla 2 vista desde el flujo, no desde el parseo."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    _validar_intento(
        config, salida, tmp_path, 1, {"genero": "lo siento, hoy no contesto en JSON"}
    )
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    assert not orquestacion.ruta_capitulo(salida, 1).is_file()


def test_no_se_puede_resolver_con_validaciones_a_medias(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    orquestacion.cmd_registrar_veredicto(
        config, salida, 1, "continuidad",
        _archivo(tmp_path, "v.raw", veredicto("continuidad", 1, "PASA")),
        escribir=_silencio,
    )
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)


def test_no_se_puede_abrir_un_intento_con_otro_sin_resolver(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap1.md", "Texto."), escribir=_silencio
    )
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_registrar_intento(
            config, salida, 1, _archivo(tmp_path, "cap1b.md", "Otro."),
            escribir=_silencio,
        )


# ---------------------------------------------------------------------------
# Resolver: escalera agotada
# ---------------------------------------------------------------------------


def _fallar_capitulo(config, salida, tmp_path, capitulo, veces, gravedades):
    """Escribe y suspende `veces` intentos, con la gravedad que se indique."""
    for numero in range(veces):
        orquestacion.cmd_registrar_intento(
            config, salida, capitulo,
            _archivo(tmp_path, "cap.md", "Intento numero {0}.".format(numero + 1)),
            escribir=_silencio,
        )
        crudo = veredicto(
            "estilo", capitulo, "FALLO",
            [problema(gravedades[numero], "Pega del intento {0}.".format(numero + 1))],
        )
        _validar_intento(config, salida, tmp_path, capitulo, {"estilo": crudo})
        orquestacion.cmd_resolver(config, salida, capitulo, escribir=_silencio)


def test_agotada_la_escalera_gana_la_puntuacion_mas_baja(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    # Seis intentos; el cuarto es el menos malo (gravedad baja = 1 punto).
    _fallar_capitulo(
        config, salida, tmp_path, 1, 6,
        ["alta", "alta", "media", "baja", "media", "alta"],
    )
    texto = orquestacion.ruta_capitulo(salida, 1).read_text(encoding="utf-8")
    assert texto == "Intento numero 4."

    estado = modulo_estado.cargar(salida)
    assert estado["capitulos_marcados"] == [1]
    assert estado["capitulos_aprobados"] == []
    _resumir(config, salida, tmp_path, 1)
    assert orquestacion.siguiente_paso(config, salida)["capitulo"] == 2


def test_en_empate_gana_el_intento_mas_tardio(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 6, ["baja"] * 6)
    texto = orquestacion.ruta_capitulo(salida, 1).read_text(encoding="utf-8")
    assert texto == "Intento numero 6."


def test_un_capitulo_aceptado_por_puntuacion_no_se_regenera(entorno, tmp_path):
    """Ya esta escrito: reanudar no puede volver a intentarlo en bucle."""
    config, salida = _preparar(entorno, tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 6, ["media"] * 6)
    pendientes = modulo_estado.capitulos_pendientes(modulo_estado.cargar(salida), 3)
    assert pendientes == [2, 3]


# ---------------------------------------------------------------------------
# Mantener la voz ganadora
# ---------------------------------------------------------------------------


def test_el_capitulo_siguiente_arranca_en_el_escalon_que_gano(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    # Dos intentos fallidos suben al escalon 1 (sonnet); el tercero aprueba.
    _fallar_capitulo(config, salida, tmp_path, 1, 2, ["media", "media"])
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Ya vale."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    _resumir(config, salida, tmp_path, 1)

    paso = orquestacion.siguiente_paso(config, salida)
    assert (paso["capitulo"], paso["modelo"], paso["de"]) == (2, "sonnet", 4)


def test_sin_mantener_voz_ganadora_se_vuelve_al_primer_escalon(tmp_path):
    config = config_minima(
        3,
        runtime={"directorio_salida": str(tmp_path / "salida")},
        modelos={"mantener_voz_ganadora": False},
        # Mismo motivo que en la fixture `entorno`: aqui se mide la escalera, no
        # la longitud, y los capitulos de juguete son frases sueltas.
        estructura={"palabras_min": 1, "palabras_max": 100000},
    )
    salida = orquestacion.directorio_salida(config)
    _preparar((config, salida), tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 2, ["media", "media"])
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Ya vale."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    _resumir(config, salida, tmp_path, 1)

    paso = orquestacion.siguiente_paso(config, salida)
    assert (paso["modelo"], paso["de"]) == ("haiku", 6)


def test_aceptar_por_puntuacion_no_conserva_ninguna_voz(entorno, tmp_path):
    """No gano nadie, asi que el capitulo siguiente empieza por abajo."""
    config, salida = _preparar(entorno, tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 6, ["media"] * 6)
    _resumir(config, salida, tmp_path, 1)
    paso = orquestacion.siguiente_paso(config, salida)
    assert (paso["capitulo"], paso["modelo"]) == (2, "haiku")


# ---------------------------------------------------------------------------
# Memoria larga y contadores
# ---------------------------------------------------------------------------


def test_la_memoria_de_estilo_acumula_apariciones(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    for capitulo in (1, 2):
        orquestacion.cmd_registrar_intento(
            config, salida, capitulo,
            _archivo(tmp_path, "cap.md", "Texto del {0}.".format(capitulo)),
            escribir=_silencio,
        )
        crudo = veredicto(
            "estilo", capitulo, "PASA", [],
            nuevas_frases_recurrentes=["la luz mortecina"],
        )
        _validar_intento(config, salida, tmp_path, capitulo, {"estilo": crudo})
        orquestacion.cmd_resolver(config, salida, capitulo, escribir=_silencio)

    memoria = orquestacion.cargar_memoria_estilo(salida)
    assert memoria["frases_recurrentes"] == [
        {"frase": "la luz mortecina", "apariciones": 2, "capitulos": [1, 2]}
    ]


def test_una_memoria_de_estilo_corrupta_no_detiene_la_generacion(entorno, tmp_path):
    """Regla 1: perder la deteccion entre capitulos es menos grave que abortar."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.ruta_memoria_estilo(salida).write_text("{roto", encoding="utf-8")
    memoria = orquestacion.cargar_memoria_estilo(salida)
    assert memoria == {"frases_recurrentes": [], "muletillas": []}


def test_cada_delegacion_registrada_suma_al_contador(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    assert modulo_estado.cargar(salida)["delegaciones"] == 1  # el arquitecto

    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    # 1 arquitecto + 1 escritor + 3 validadores
    assert modulo_estado.cargar(salida)["delegaciones"] == 5


def test_al_llegar_al_limite_el_siguiente_paso_es_parar(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    config["limites"]["delegaciones_max_totales"] = 1
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["paso"] == "limite"


def test_el_limite_se_puede_desactivar(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    config["limites"]["delegaciones_max_totales"] = 1
    config["limites"]["abortar_si_supera_delegaciones"] = False
    assert orquestacion.siguiente_paso(config, salida)["paso"] == "escribir"


# ---------------------------------------------------------------------------
# Ventanas
# ---------------------------------------------------------------------------


def test_la_ventana_del_escritor_arrastra_los_problemas_acumulados(entorno, tmp_path):
    """Los problemas viajan con la reescritura sin que nadie los copie a mano."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    crudo = veredicto(
        "estilo", 1, "FALLO", [problema("alta", "Repites la palabra sombra.")]
    )
    _validar_intento(config, salida, tmp_path, 1, {"estilo": crudo})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    lineas = []
    orquestacion.cmd_ventana(config, salida, "escritor", 1, escribir=lineas.append)
    texto = "\n".join(lineas)
    assert "Repites la palabra sombra." in texto
    assert "[alta]" in texto


def test_la_ventana_de_genero_pasa_la_ruta_y_no_el_contenido(entorno, tmp_path):
    """Decision 8: la referencia la lee el subagente, en su propio contexto."""
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Texto."), escribir=_silencio
    )
    lineas = []
    orquestacion.cmd_ventana(config, salida, "genero", 1, escribir=lineas.append)
    texto = "\n".join(lineas)
    assert "prompts/referencias/terror.md" in texto
    assert len(texto) < 4000, "si la referencia se hubiera copiado, seria mas larga"


def test_los_validadores_auditan_el_ultimo_intento(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    _fallar_capitulo(config, salida, tmp_path, 1, 1, ["media"])
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "La version nueva."),
        escribir=_silencio,
    )
    lineas = []
    orquestacion.cmd_ventana(config, salida, "estilo", 1, escribir=lineas.append)
    assert "La version nueva." in "\n".join(lineas)


def test_no_se_puede_validar_un_capitulo_sin_intentos(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_ventana(config, salida, "continuidad", 1, escribir=_silencio)


# ---------------------------------------------------------------------------
# Registrar la biblia
# ---------------------------------------------------------------------------


def test_una_biblia_que_no_parsea_se_rechaza_con_un_mensaje_util(entorno, tmp_path):
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    with pytest.raises(orquestacion.ErrorDeOrquestacion) as error:
        orquestacion.cmd_registrar_biblia(
            config, salida, _archivo(tmp_path, "b.raw", "no es JSON"),
            escribir=_silencio,
        )
    assert "arquitecto" in str(error.value)


def test_una_biblia_con_el_outline_incompleto_se_rechaza(entorno, tmp_path):
    """El error que el arquitecto comete mas a menudo."""
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    datos = biblia_valida(2)                      # la config pide 3 capitulos
    with pytest.raises(orquestacion.ErrorDeOrquestacion):
        orquestacion.cmd_registrar_biblia(
            config, salida,
            _archivo(tmp_path, "b.raw", json.dumps(datos, ensure_ascii=False)),
            escribir=_silencio,
        )
    assert not modulo_biblia.existe(salida)


def test_la_biblia_se_acepta_aunque_venga_con_vallas(entorno, tmp_path):
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    crudo = "```json\n" + json.dumps(biblia_valida(3), ensure_ascii=False) + "\n```"
    orquestacion.cmd_registrar_biblia(
        config, salida, _archivo(tmp_path, "b.raw", crudo), escribir=_silencio
    )
    assert modulo_biblia.existe(salida)


# ---------------------------------------------------------------------------
# Reanudacion
# ---------------------------------------------------------------------------


def test_reanudar_no_regenera_los_capitulos_aprobados(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Capitulo uno."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)
    _resumir(config, salida, tmp_path, 1)

    # Segunda "sesion": se vuelve a lanzar iniciar, como haria quien reanuda.
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    paso = orquestacion.siguiente_paso(config, salida)
    assert paso["capitulo"] == 2
    assert orquestacion.ruta_capitulo(salida, 1).read_text(encoding="utf-8") == (
        "Capitulo uno."
    )


def test_desde_cero_borra_el_progreso(entorno, tmp_path):
    config, salida = _preparar(entorno, tmp_path)
    orquestacion.cmd_iniciar(config, salida, desde_cero=True, escribir=_silencio)
    estado = modulo_estado.cargar(salida)
    assert estado["capitulos_aprobados"] == []
    assert estado["delegaciones"] == 0


def test_el_capitulo_anterior_entra_entero_y_los_previos_no(entorno, tmp_path):
    """La regla del N-1: lo que mantiene la ventana constante sea cual sea N."""
    config, salida = _preparar(entorno, tmp_path)
    for capitulo in (1, 2):
        _cerrar_capitulo(
            config, salida, tmp_path, capitulo,
            "MARCA-DEL-CAPITULO-{0}".format(capitulo),
        )

    lineas = []
    orquestacion.cmd_ventana(config, salida, "escritor", 3, escribir=lineas.append)
    texto = "\n".join(lineas)
    # El capitulo 2 entra entero; del 1 solo entra su resumen.
    assert "MARCA-DEL-CAPITULO-2" in texto
    assert "MARCA-DEL-CAPITULO-1" not in texto
    assert "Pasa algo en el 1." in texto


# ---------------------------------------------------------------------------
# Comprobacion del entorno
# ---------------------------------------------------------------------------


def test_se_lee_la_version_del_cli():
    assert orquestacion.parsear_version("2.1.274 (Claude Code)") == (2, 1, 274)


def test_una_version_ilegible_no_se_inventa():
    """Mejor decir que no se sabe que dar por buena una version falsa.

    Si esto devolviera un valor por defecto, `comprobar` aprobaria un CLI
    antiguo en el que `omitClaudeMd` se ignora sin avisar.
    """
    assert orquestacion.parsear_version("claude") is None
    assert orquestacion.parsear_version("") is None


def test_la_version_minima_es_la_que_activa_omitclaudemd():
    assert orquestacion.VERSION_MINIMA_CLAUDE == (2, 1, 271)
    assert orquestacion.parsear_version("2.1.263") < orquestacion.VERSION_MINIMA_CLAUDE


# ---------------------------------------------------------------------------
# La longitud, que no la juzga ningun modelo
# ---------------------------------------------------------------------------


def _entorno_con_rango(tmp_path, minimo, maximo):
    """Un entorno de juguete con un rango de palabras estrecho y explicito."""
    config = config_minima(
        3,
        runtime={"directorio_salida": str(tmp_path / "salida")},
        estructura={"palabras_min": minimo, "palabras_max": maximo},
    )
    return config, orquestacion.directorio_salida(config)


def test_un_intento_corto_nace_ya_con_un_veredicto_de_longitud(tmp_path):
    """El contador contesta al registrar el intento, sin delegar en nadie."""
    config, salida = _preparar(_entorno_con_rango(tmp_path, 5, 50), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Dos palabras."),
        escribir=_silencio,
    )

    intento = orquestacion.intentos_de_capitulo(salida, 1)[-1]
    assert [v["validador"] for v in intento["veredictos"]] == ["longitud"]
    assert intento["veredictos"][0]["veredicto"] == "FALLO"


def test_un_intento_en_rango_nace_sin_veredictos(tmp_path):
    config, salida = _preparar(_entorno_con_rango(tmp_path, 1, 50), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Dos palabras."),
        escribir=_silencio,
    )

    assert orquestacion.intentos_de_capitulo(salida, 1)[-1]["veredictos"] == []


def test_la_longitud_tumba_un_capitulo_que_los_tres_validadores_aprueban(tmp_path):
    """El agujero que se encontro en ejecucion: tres PASA sobre un texto corto.

    Antes de esta comprobacion el capitulo se aprobaba y entraba corto en el
    manuscrito, con un aviso por pantalla que solo leia la sesion.
    """
    config, salida = _preparar(_entorno_con_rango(tmp_path, 5, 50), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Dos palabras."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    intento = orquestacion.intentos_de_capitulo(salida, 1)[-1]
    assert intento["resultado"] == "REINTENTAR"
    assert intento["puntuacion"] == 2          # una pega de gravedad media
    assert not orquestacion.ruta_capitulo(salida, 1).exists()


def test_registrar_los_veredictos_no_borra_el_de_longitud(tmp_path):
    """`registrar-veredicto` reemplaza por nombre; `longitud` no es ninguno."""
    config, salida = _preparar(_entorno_con_rango(tmp_path, 5, 50), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Dos palabras."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})

    nombres = [
        v["validador"]
        for v in orquestacion.intentos_de_capitulo(salida, 1)[-1]["veredictos"]
    ]
    assert sorted(nombres) == ["continuidad", "estilo", "genero", "longitud"]


def test_el_escritor_recibe_la_longitud_entre_los_problemas(tmp_path):
    """El objetivo del cambio: que la pega llegue sola a la ventana del escritor."""
    config, salida = _preparar(_entorno_con_rango(tmp_path, 5, 50), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Dos palabras."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    lineas = []
    orquestacion.cmd_ventana(config, salida, "escritor", 1, escribir=lineas.append)
    texto = "\n".join(lineas)
    assert "(longitud)" in texto
    assert "el minimo configurado son 5" in texto


def test_un_capitulo_largo_tambien_se_reescribe(tmp_path):
    config, salida = _preparar(_entorno_con_rango(tmp_path, 1, 2), tmp_path)
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.md", "Una frase de cinco palabras."),
        escribir=_silencio,
    )
    _validar_intento(config, salida, tmp_path, 1, {})
    orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    assert orquestacion.intentos_de_capitulo(salida, 1)[-1]["resultado"] == "REINTENTAR"


def test_la_longitud_no_impide_aceptar_por_puntuacion(tmp_path):
    """Regla 1: ningun capitulo detiene la generacion, tampoco por corto.

    Agotada la escalera, un capitulo fuera de rango sigue entrando en el
    manuscrito y queda marcado en el informe. Es preferible a un hueco.
    """
    config, salida = _preparar(_entorno_con_rango(tmp_path, 5, 50), tmp_path)
    for numero in range(6):
        orquestacion.cmd_registrar_intento(
            config, salida, 1,
            _archivo(tmp_path, "cap.md", "Corto {0}.".format(numero)),
            escribir=_silencio,
        )
        _validar_intento(config, salida, tmp_path, 1, {})
        orquestacion.cmd_resolver(config, salida, 1, escribir=_silencio)

    assert orquestacion.ruta_capitulo(salida, 1).exists()
    estado_final = modulo_estado.cargar(salida)
    assert 1 in estado_final["capitulos_marcados"]
