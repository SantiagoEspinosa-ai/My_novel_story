"""Tests de la marca de delegacion en curso.

Que es y por que se prueba aparte
---------------------------------
`estado.json` solo sabia de delegaciones TERMINADAS: una entrada aparece en
`delegaciones_detalle` cuando ya hay una respuesta que registrar. Mientras un
subagente piensa no habia ni una senal en disco, y desde fuera una generacion
trabajando y una abandonada a medias se veian igual.

La clave `delegacion_en_curso` cubre ese hueco. La escribe la sesion ANTES de
delegar y desaparece cuando el resultado se registra. Lo que estos tests
protegen es justo esa propiedad de dos filos:

- que la marca aparezca al empezar, con quien, con que modelo y desde cuando;
- y que **no se quede pegada** despues, porque una marca que no se borra
  miente: diria que algo esta trabajando cuando ya termino, y entonces el
  panel en vivo seria peor que no tener panel.

Ningun test sale a la red ni delega en nadie.
"""

import json
from datetime import datetime, timedelta, timezone

from src import delegaciones
from src import estado as modulo_estado
from src import orquestacion
from tests.ayudas import biblia_valida, veredicto


def _silencio(*args, **kwargs):
    """Sustituye a `print`: los tests no necesitan la charla de los comandos."""


def _archivo(tmp, nombre, contenido):
    ruta = tmp / nombre
    ruta.parent.mkdir(parents=True, exist_ok=True)
    ruta.write_text(contenido, encoding="utf-8")
    return str(ruta)


def _iniciar(entorno):
    config, salida = entorno
    orquestacion.cmd_iniciar(config, salida, escribir=_silencio)
    return config, salida


def _marca_en_disco(salida):
    datos = json.loads(modulo_estado.ruta(salida).read_text(encoding="utf-8"))
    return datos.get(delegaciones.CLAVE_EN_CURSO)


# ---------------------------------------------------------------------------
# El modulo, sin tocar disco
# ---------------------------------------------------------------------------


def test_marcar_guarda_quien_que_y_desde_cuando():
    estado = {}
    marca = delegaciones.marcar_en_curso(
        estado, "escritor", modelo="opus", capitulo=4, intento=2
    )
    assert marca["rol"] == "escritor"
    assert marca["modelo"] == "opus"
    assert marca["capitulo"] == 4
    assert marca["intento"] == 2
    assert marca["inicio"].endswith("Z")
    assert delegaciones.en_curso(estado) == marca


def test_una_marca_nueva_pisa_a_la_anterior():
    """Solo puede haber una delegacion en curso: la ultima es la que vale."""
    estado = {}
    delegaciones.marcar_en_curso(estado, "escritor", modelo="haiku")
    delegaciones.marcar_en_curso(estado, "continuidad", modelo="haiku", capitulo=1)
    assert delegaciones.en_curso(estado)["rol"] == "continuidad"


def test_limpiar_devuelve_la_marca_y_la_quita():
    estado = {}
    delegaciones.marcar_en_curso(estado, "resumidor", capitulo=2)
    quitada = delegaciones.limpiar_en_curso(estado)
    assert quitada["rol"] == "resumidor"
    assert delegaciones.en_curso(estado) is None


def test_limpiar_sin_marca_no_es_un_error():
    """Una sesion que no marque tiene que poder registrar igual."""
    assert delegaciones.limpiar_en_curso({}) is None


def test_los_segundos_se_cuentan_desde_el_inicio():
    estado = {}
    delegaciones.marcar_en_curso(estado, "escritor")
    inicio = datetime.strptime(
        delegaciones.en_curso(estado)["inicio"], "%Y-%m-%dT%H:%M:%SZ"
    ).replace(tzinfo=timezone.utc)
    assert delegaciones.segundos_en_curso(
        estado, ahora=inicio + timedelta(seconds=90)
    ) == 90


def test_sin_marca_o_con_hora_ilegible_no_se_inventa_un_numero():
    assert delegaciones.segundos_en_curso({}) is None
    assert delegaciones.segundos_en_curso(
        {delegaciones.CLAVE_EN_CURSO: {"rol": "escritor", "inicio": "ayer"}}
    ) is None


# ---------------------------------------------------------------------------
# Los comandos, contra un salida/ de juguete
# ---------------------------------------------------------------------------


def test_el_comando_escribe_la_marca_en_disco(entorno):
    config, salida = _iniciar(entorno)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "escritor", modelo="sonnet", capitulo=2, intento=1,
        escribir=_silencio,
    )
    marca = _marca_en_disco(salida)
    assert marca["rol"] == "escritor"
    assert marca["modelo"] == "sonnet"
    assert marca["capitulo"] == 2


def test_cancelar_borra_la_marca(entorno):
    config, salida = _iniciar(entorno)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "arquitecto", modelo="sonnet", escribir=_silencio
    )
    orquestacion.cmd_cancelar_delegacion(config, salida, escribir=_silencio)
    assert _marca_en_disco(salida) is None


def test_cancelar_no_toca_el_contador(entorno):
    """Cancelar es "no llegue a lanzarla", no "la lanze y no devolvio nada".

    Lo segundo se anota con `registrar-delegacion`, que SI cuenta. Si cancelar
    descontara, volveria el problema historico del contador corto.
    """
    config, salida = _iniciar(entorno)
    antes = modulo_estado.cargar(salida).get("delegaciones", 0)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "escritor", escribir=_silencio
    )
    orquestacion.cmd_cancelar_delegacion(config, salida, escribir=_silencio)
    assert modulo_estado.cargar(salida).get("delegaciones", 0) == antes


# ---------------------------------------------------------------------------
# Lo que de verdad importa: que la marca no se quede pegada
# ---------------------------------------------------------------------------


def test_registrar_la_biblia_limpia_la_marca(entorno, tmp_path):
    config, salida = _iniciar(entorno)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "arquitecto", modelo="sonnet", escribir=_silencio
    )
    crudo = json.dumps(biblia_valida(3), ensure_ascii=False)
    orquestacion.cmd_registrar_biblia(
        config, salida, _archivo(tmp_path, "biblia.raw", crudo), escribir=_silencio
    )
    assert _marca_en_disco(salida) is None


def test_registrar_un_intento_limpia_la_marca(entorno, tmp_path):
    config, salida = _iniciar(entorno)
    crudo = json.dumps(biblia_valida(3), ensure_ascii=False)
    orquestacion.cmd_registrar_biblia(
        config, salida, _archivo(tmp_path, "biblia.raw", crudo), escribir=_silencio
    )
    orquestacion.cmd_empezar_delegacion(
        config, salida, "escritor", modelo="haiku", capitulo=1, intento=1,
        escribir=_silencio,
    )
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.raw", "Texto del capitulo 1."),
        escribir=_silencio,
    )
    assert _marca_en_disco(salida) is None


def test_registrar_un_veredicto_limpia_la_marca(entorno, tmp_path):
    config, salida = _iniciar(entorno)
    crudo = json.dumps(biblia_valida(3), ensure_ascii=False)
    orquestacion.cmd_registrar_biblia(
        config, salida, _archivo(tmp_path, "biblia.raw", crudo), escribir=_silencio
    )
    orquestacion.cmd_registrar_intento(
        config, salida, 1, _archivo(tmp_path, "cap.raw", "Texto del capitulo 1."),
        escribir=_silencio,
    )
    # Los tres validadores van a la vez, asi que la marca es del conjunto.
    orquestacion.cmd_empezar_delegacion(
        config, salida, "validadores", modelo="haiku", capitulo=1, intento=1,
        escribir=_silencio,
    )
    orquestacion.cmd_registrar_veredicto(
        config, salida, 1, "estilo",
        _archivo(tmp_path, "v.raw", json.dumps(veredicto("estilo", 1))),
        escribir=_silencio,
    )
    assert _marca_en_disco(salida) is None


def test_registrar_una_delegacion_sin_resultado_limpia_la_marca(entorno):
    """El caso de la respuesta vacia: se paga, se anota y la marca se va."""
    config, salida = _iniciar(entorno)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "escritor", modelo="opus", capitulo=1, intento=1,
        escribir=_silencio,
    )
    orquestacion.cmd_registrar_delegacion(
        config, salida, "escritor", modelo="opus", capitulo=1, intento=1,
        nota="devolvio vacio", escribir=_silencio,
    )
    assert _marca_en_disco(salida) is None
    assert modulo_estado.cargar(salida)["delegaciones"] >= 1


def test_el_informe_de_estado_ensena_la_delegacion_en_curso(entorno):
    config, salida = _iniciar(entorno)
    orquestacion.cmd_empezar_delegacion(
        config, salida, "escritor", modelo="opus", capitulo=3, intento=2,
        escribir=_silencio,
    )
    lineas = []
    orquestacion.informe_de_estado(config, salida, escribir=lineas.append)
    texto = "\n".join(str(x) for x in lineas)
    assert "EN CURSO AHORA" in texto
    assert "escritor" in texto and "opus" in texto and "capitulo 3" in texto


def test_un_estado_viejo_sin_la_clave_se_sigue_leyendo(entorno):
    """La clave es opcional: los estados de generaciones anteriores valen."""
    config, salida = _iniciar(entorno)
    datos = json.loads(modulo_estado.ruta(salida).read_text(encoding="utf-8"))
    datos.pop(delegaciones.CLAVE_EN_CURSO, None)
    modulo_estado.ruta(salida).write_text(
        json.dumps(datos, ensure_ascii=False), encoding="utf-8"
    )
    estado = orquestacion.cargar_estado(config, salida)
    assert delegaciones.en_curso(estado) is None
