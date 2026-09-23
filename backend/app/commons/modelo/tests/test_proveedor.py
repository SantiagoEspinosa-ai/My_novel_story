"""E3 — La delegacion, probada sin arrancar ningun proceso.

El ejecutor se inyecta, asi que **ninguna prueba sale de la maquina** ni gasta
nada. Lo que se prueba es lo que la rama `main` pago descubriendo:

    - el prompt va por stdin y no como argumento;
    - las vallas de bloque de codigo las anade la sesion intermedia;
    - una respuesta ilegible es fallo de contrato, no de transporte.
"""

import pytest

from app.commons.modelo import proveedor
from app.commons.modelo.doble import DobleDelModelo

RESPUESTA_OK = '{"texto": "La puerta estaba abierta.", "delta": {"cambio_de_valor": {}}}'


@pytest.fixture
def entorno(monkeypatch):
    monkeypatch.setenv(proveedor.VARIABLES["modelo_escritor"], "modelo-de-prueba")
    monkeypatch.setenv(proveedor.VARIABLES["ejecutable"], "claude-de-mentira")


def test_sin_la_variable_del_modelo_falla_al_construir(monkeypatch):
    monkeypatch.delenv(proveedor.VARIABLES["modelo_escritor"], raising=False)
    with pytest.raises(proveedor.FaltaEntorno) as e:
        proveedor.SesionDelegada()
    assert proveedor.VARIABLES["modelo_escritor"] in str(e.value)


def test_el_prompt_va_por_stdin_y_no_como_argumento(entorno):
    """Hallazgo 14. `cmd.exe` termina el comando en el primer salto de linea."""
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None):
        visto["orden_entera"] = (ejecutable, modelo, agente)
        visto["prompt"] = prompt
        return RESPUESTA_OK

    c = proveedor.SesionDelegada(ejecutar=ejecutar)
    prompt = "primera linea\nsegunda linea que cmd.exe se comeria"
    c.llamar(prompt)
    assert visto["prompt"] == prompt, "el prompt entero, por stdin"
    assert "segunda linea" not in str(visto["orden_entera"])


def test_las_vallas_de_bloque_de_codigo_no_pierden_la_escena(entorno):
    """Hallazgo 7: las anade la sesion intermedia, no el modelo."""
    con_vallas = "```json\n" + RESPUESTA_OK + "\n```"
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: con_vallas)
    assert c.llamar("x")["texto"].startswith("La puerta")


def test_se_rescata_el_primer_objeto_equilibrado_con_preambulo(entorno):
    """Un modelo que saluda antes del JSON no cuesta una escena entera."""
    ruidosa = "Claro, aqui tienes la escena:\n" + RESPUESTA_OK + "\nEspero que te sirva."
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: ruidosa)
    assert c.llamar("x")["delta"] == {"cambio_de_valor": {}}


def test_las_llaves_anidadas_no_cortan_en_la_primera_de_cierre(entorno):
    anidado = '{"texto": "x", "delta": {"cambio_de_valor": {"eje": "vida"}}}'
    assert proveedor.primer_objeto_equilibrado("ruido " + anidado + " mas ruido") == anidado


def test_una_respuesta_ilegible_es_fallo_de_contrato_no_de_transporte(entorno):
    """Por `O-3` no se reintenta: repetirlo repite el error."""
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: "lo siento, no puedo ayudarte")
    with pytest.raises(proveedor.RespuestaIlegible):
        c.llamar("x")


def test_un_proceso_que_no_arranca_es_fallo_de_transporte(entorno):
    def revienta(*a, **k):
        raise OSError("WinError 2")
    c = proveedor.SesionDelegada(ejecutar=revienta)
    with pytest.raises(proveedor.FalloDeTransporte):
        c.llamar("x")


def test_no_hay_usage_y_el_campo_no_se_rellena_con_cero(entorno):
    """`SPEC-14` C-3: los tokens los reporta la sesion, no vienen aqui."""
    c = proveedor.SesionDelegada(ejecutar=lambda *a, **k: RESPUESTA_OK)
    assert "usage" not in c.llamar("x")


def test_la_firma_es_la_misma_que_la_del_doble(entorno):
    """Lo que hace que el bucle probado en E2 sea el mismo que correra en E5."""
    real = proveedor.SesionDelegada(ejecutar=lambda *a, **k: RESPUESTA_OK)
    for atributo in ("nombre", "llamar"):
        assert hasattr(real, atributo) and hasattr(DobleDelModelo(), atributo)


def test_el_cwd_viaja_al_ejecutor_porque_es_lo_que_aisla(entorno):
    """`omitClaudeMd` se ignora en silencio en 2.1.274; lo que aisla es el cwd.

    Comprobado con un control: con la opcion a `false` y a `true` el agente
    enumero los seis niveles del presupuesto; desde un directorio vacio
    respondio NO LO SE. El cuerpo del agente si se aplica, asi que la
    definicion se carga y **la opcion se ignora**.
    """
    visto = {}

    def ejecutar(ejecutable, modelo, agente, prompt, cwd=None):
        visto["cwd"] = cwd
        return RESPUESTA_OK

    proveedor.SesionDelegada(ejecutar=ejecutar, cwd="/un/directorio/vacio").llamar("x")
    assert visto["cwd"] == "/un/directorio/vacio"
