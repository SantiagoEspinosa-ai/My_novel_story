"""Tests de generar, detener y el log (paso 3).

Cómo se prueba sin gastar una sola delegación
---------------------------------------------
`crear_app` acepta un constructor de comando. En producción devuelve
`["claude", "-p", <prompt fijo>]`; aquí se le pasa un intérprete de Python que
hace lo que el test necesite: escribir en su salida, dormir, o morir con un
código de error. Ese parámetro es de **Python, no de HTTP**: desde el navegador
no hay forma de influir en lo que se lanza, y hay un test que lo comprueba.

Lo que más se protege aquí
--------------------------
1. **Que nunca se genere sin copia.** Si la copia de seguridad falla, no se
   lanza nada: generar encima de una novela terminada la pierde para siempre.
2. **Que una muerte no pase en silencio.** Si el proceso se cae, tiene que
   quedar escrito en el log, el panel tiene que poder decirlo, y la marca
   `delegacion_en_curso` **no puede quedarse pegada**: si se queda, el panel
   enseñaría «escritor, trabajando» para siempre y además bloquearía la
   configuración.
"""

import json
import sys
import time

import pytest

pytest.importorskip("fastapi", reason="el servidor del panel necesita FastAPI")

from fastapi.testclient import TestClient  # noqa: E402

from src import servidor  # noqa: E402


CONFIG = {
    "novela": {"genero": "terror"},
    "estructura": {"num_capitulos": 2, "palabras_min": 100, "palabras_max": 9000},
    "runtime": {"directorio_salida": "./salida"},
}


def comando_falso(*trozos_de_codigo):
    """Un «claude» de mentira: un Python que hace lo que diga el test."""
    codigo = "\n".join(trozos_de_codigo)
    return lambda: [sys.executable, "-c", codigo]


CODIGO_QUE_TERMINA_BIEN = comando_falso(
    "print('empiezo a generar')", "print('he terminado')"
)
CODIGO_QUE_SE_CAE = comando_falso(
    "import sys", "print('empiezo a generar')",
    "print('algo va mal', file=sys.stderr)", "sys.exit(3)",
)
CODIGO_QUE_NO_TERMINA = comando_falso("import time", "print('trabajando')", "time.sleep(120)")


@pytest.fixture
def proyecto(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html>panel</html>", encoding="utf-8")
    salida = tmp_path / "salida"
    (salida / "capitulos").mkdir(parents=True)
    (salida / "manuscrito.md").write_text("# Capítulo 1 — Uno\n\nTexto.\n", encoding="utf-8")
    (salida / "estado.json").write_text(json.dumps({
        "capitulo_actual": 1, "intento_actual": 0, "modelo_actual": "haiku",
        "capitulos_aprobados": [1], "capitulos_marcados": [],
        "iniciado": "2026-09-18T10:00:00Z", "delegaciones": 4,
    }), encoding="utf-8")
    (tmp_path / "config.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    return tmp_path


def hacer_cliente(proyecto, comando):
    return TestClient(servidor.crear_app(proyecto, comando=comando))


def esperar_a_que_acabe(cliente, intentos=100):
    """Repregunta hasta que el estado deje de ser «viva». Sin dormir a ciegas."""
    for _ in range(intentos):
        cuerpo = cliente.get("/api/generacion").json()
        if not cuerpo["viva"]:
            return cuerpo
        time.sleep(0.1)
    raise AssertionError("la generacion de prueba no termino")


def poner_delegacion_en_curso(proyecto):
    archivo = proyecto / "salida" / "estado.json"
    datos = json.loads(archivo.read_text(encoding="utf-8"))
    datos["delegacion_en_curso"] = {
        "rol": "escritor", "modelo": "opus", "capitulo": 2, "intento": 1,
        "inicio": "2026-09-18T10:05:00Z",
    }
    archivo.write_text(json.dumps(datos), encoding="utf-8")


def marca_en_estado(proyecto):
    datos = json.loads((proyecto / "salida" / "estado.json").read_text(encoding="utf-8"))
    return datos.get("delegacion_en_curso")


# ---------------------------------------------------------------------------
# Antes de lanzar: la copia
# ---------------------------------------------------------------------------


def test_copia_la_novela_antes_de_generar_y_lo_dice(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cuerpo = cliente.post("/api/generar").json()
    assert cuerpo["copia"]["copiado"] is True
    assert cuerpo["copia"]["destino"] == "salida-novela-1"
    copia = proyecto / "salida-novela-1"
    assert (copia / "manuscrito.md").read_text(encoding="utf-8").startswith("# Capítulo 1")
    esperar_a_que_acabe(cliente)


def test_la_segunda_copia_no_pisa_la_primera(proyecto):
    (proyecto / "salida-novela-1").mkdir()
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cuerpo = cliente.post("/api/generar").json()
    assert cuerpo["copia"]["destino"] == "salida-novela-2"
    esperar_a_que_acabe(cliente)


def test_si_la_copia_falla_no_se_lanza_nada(proyecto, monkeypatch):
    """La regla que no se negocia: sin copia, no se genera."""
    def copia_rota(raiz, salida):
        raise OSError("disco lleno de mentira")
    monkeypatch.setattr(servidor, "copiar_novela", copia_rota)
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    r = cliente.post("/api/generar")
    assert r.status_code == 500
    assert "no he podido copiar" in r.json()["detail"]["mensaje"].lower()
    assert cliente.get("/api/generacion").json()["viva"] is False


def test_sin_novela_previa_no_hay_copia_pero_si_generacion(tmp_path, monkeypatch):
    (tmp_path / "panel.html").write_text("<html></html>", encoding="utf-8")
    (tmp_path / "salida").mkdir()
    (tmp_path / "config.json").write_text(json.dumps(CONFIG), encoding="utf-8")
    monkeypatch.setattr(servidor, "directorio_salida", lambda raiz: (raiz / "salida").resolve())
    cliente = hacer_cliente(tmp_path, CODIGO_QUE_TERMINA_BIEN)
    cuerpo = cliente.post("/api/generar").json()
    assert cuerpo["copia"]["copiado"] is False
    assert "no habia ninguna novela" in cuerpo["copia"]["motivo"]
    esperar_a_que_acabe(cliente)


def test_si_no_esta_el_ejecutable_no_copia_ni_lanza(proyecto):
    """Se comprueba antes de copiar: si no se va a poder generar, no tiene
    sentido dejar una carpeta de copia suelta."""
    cliente = hacer_cliente(proyecto, lambda: ["no-existe-este-programa-xyz", "-p", "hola"])
    r = cliente.post("/api/generar")
    assert r.status_code == 503
    assert "no encuentro el ejecutable" in r.json()["detail"]["mensaje"].lower()
    assert not (proyecto / "salida-novela-1").exists()


# ---------------------------------------------------------------------------
# El ciclo normal
# ---------------------------------------------------------------------------


def test_la_peticion_vuelve_enseguida_con_el_proceso_aun_vivo(proyecto):
    """Una generación son minutos: la petición no puede esperar a que acabe."""
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    cuerpo = cliente.post("/api/generar").json()
    assert cuerpo["viva"] is True
    assert cuerpo["estado"] == "en_marcha"
    assert cuerpo["pid"]
    cliente.post("/api/detener")


def test_el_log_recoge_lo_que_escribe_el_proceso(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    texto = "\n".join(final["log"])
    assert "GENERACION LANZADA" in texto
    assert "empiezo a generar" in texto
    assert "he terminado" in texto
    assert (proyecto / "salida" / servidor.NOMBRE_LOG).is_file()


def test_al_terminar_bien_lo_dice(proyecto):
    """Terminar bien es terminar con código 0 **y habiendo hecho algo**."""
    cliente = hacer_cliente(proyecto, comando_que_escribe_un_capitulo(proyecto))
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    assert final["estado"] == "terminada"
    assert final["codigo_salida"] == 0
    assert "termino bien" in final["mensaje"]


# ---------------------------------------------------------------------------
# Terminar con código 0 sin hacer nada NO es un éxito
# ---------------------------------------------------------------------------
#
# Pasó de verdad: la sesión no podía ejecutar los comandos del harness por
# permisos, lo explicó impecablemente en su log y salió con código 0. El panel
# dijo «terminó bien» sobre una novela que nadie había tocado. Un fallo
# silencioso con aspecto de acierto es el peor de los fallos.


def comando_que_escribe_un_capitulo(proyecto):
    """Un «claude» de mentira que sí deja trabajo hecho."""
    destino = (proyecto / "salida" / "capitulos" / "cap-02.md").as_posix()
    texto = "# Capitulo 2" + chr(10) + chr(10) + "Texto." + chr(10)
    return comando_falso(
        "print('escribiendo el capitulo 2')",
        "open(r'" + destino + "', 'w', encoding='utf-8').write(" + repr(texto) + ")")


def test_terminar_con_codigo_cero_sin_escribir_nada_no_es_un_exito(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    assert final["codigo_salida"] == 0          # salió limpiamente...
    assert final["estado"] == "sin_efecto"      # ...y aun así no es un éxito
    assert "no es un exito" in final["mensaje"].lower()
    assert "sin escribir nada" in final["mensaje"]


def test_el_log_dice_que_no_hizo_nada(proyecto):
    """Y remite a lo que la propia sesión dejó escrito, que es el diagnóstico."""
    cliente = hacer_cliente(proyecto, comando_falso(
        "print('No puedo ejecutar python: me falta permiso.')"))
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    texto = "\n".join(final["log"])
    assert "TERMINADA SIN HACER NADA" in texto
    assert "no cambio nada" in texto
    # Lo que dijo la sesión sigue ahí, que es donde está el motivo.
    assert "me falta permiso" in texto


def test_una_generacion_que_si_escribe_no_se_marca_como_vacia(proyecto):
    """El otro lado: si tocó algo, es un éxito y se dice como tal."""
    cliente = hacer_cliente(proyecto, comando_que_escribe_un_capitulo(proyecto))
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    assert final["estado"] == "terminada"
    assert (proyecto / "salida" / "capitulos" / "cap-02.md").is_file()


def test_detenerla_no_se_confunde_con_no_haber_hecho_nada(proyecto):
    """Pararla a mano tiene su propio estado, aunque tampoco haya hecho nada."""
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    cliente.post("/api/generar")
    cliente.post("/api/detener")
    final = cliente.get("/api/generacion").json()
    assert final["estado"] == "detenida"


def test_no_se_pueden_lanzar_dos_a_la_vez(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    assert cliente.post("/api/generar").status_code == 200
    r = cliente.post("/api/generar")
    assert r.status_code == 409
    cliente.post("/api/detener")


def test_detener_para_el_proceso_y_lo_anota(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    cliente.post("/api/generar")
    cuerpo = cliente.post("/api/detener").json()
    assert cuerpo["paro"] is True
    final = cliente.get("/api/generacion").json()
    assert final["viva"] is False
    assert final["estado"] == "detenida"
    assert "DETENIDA A MANO" in "\n".join(final["log"])


def test_detener_sin_nada_en_marcha_no_es_un_error(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cuerpo = cliente.post("/api/detener").json()
    assert cuerpo["paro"] is False
    assert "no habia ninguna" in cuerpo["mensaje"].lower()


def test_sin_haber_generado_nunca_lo_dice_sin_inventar(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    cuerpo = cliente.get("/api/generacion").json()
    assert cuerpo["viva"] is False
    assert cuerpo["estado"] == "sin_datos"
    assert cuerpo["log"] == []


# ---------------------------------------------------------------------------
# Cuando el proceso se cae. Esta es la parte importante.
# ---------------------------------------------------------------------------


def test_una_caida_queda_escrita_en_el_log(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_SE_CAE)
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    texto = "\n".join(final["log"])
    assert "CAIDA" in texto
    assert "codigo 3" in texto
    assert "sin llegar al final" in texto
    # Y lo que el propio proceso escribió antes de morir sigue ahí.
    assert "algo va mal" in texto


def test_una_caida_se_declara_en_el_estado(proyecto):
    cliente = hacer_cliente(proyecto, CODIGO_QUE_SE_CAE)
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)
    assert final["estado"] == "caida"
    assert final["codigo_salida"] == 3
    assert "se cayo" in final["mensaje"]


def test_una_caida_no_deja_la_delegacion_pegada(proyecto):
    """El caso que no puede pasar.

    Si el proceso muere a media delegación, `delegacion_en_curso` se queda
    puesta. Sin limpiarla, el panel enseñaría «escritor, trabajando» para
    siempre —una mentira— y además la configuración quedaría bloqueada sin que
    nada estuviera generando.
    """
    poner_delegacion_en_curso(proyecto)
    assert marca_en_estado(proyecto) is not None

    cliente = hacer_cliente(proyecto, CODIGO_QUE_SE_CAE)
    cliente.post("/api/generar")
    final = esperar_a_que_acabe(cliente)

    assert marca_en_estado(proyecto) is None
    # Y no se pierde la información: se cuenta con qué murió.
    assert final["delegacion_colgada"]["rol"] == "escritor"
    assert "escritor" in final["mensaje"]
    assert "capitulo 2" in final["mensaje"]


def test_detenerla_a_mano_tampoco_deja_la_delegacion_pegada(proyecto):
    poner_delegacion_en_curso(proyecto)
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    cliente.post("/api/generar")
    cliente.post("/api/detener")
    assert marca_en_estado(proyecto) is None


def test_tras_una_caida_la_configuracion_se_puede_volver_a_editar(proyecto):
    """La consecuencia práctica de limpiar la marca."""
    poner_delegacion_en_curso(proyecto)
    cliente = hacer_cliente(proyecto, CODIGO_QUE_SE_CAE)
    assert cliente.put("/api/config", json={"estructura": {"num_capitulos": 3}}).status_code == 409
    cliente.post("/api/generar")
    esperar_a_que_acabe(cliente)
    assert cliente.put("/api/config", json={"estructura": {"num_capitulos": 3}}).status_code == 200


# ---------------------------------------------------------------------------
# Mientras genera
# ---------------------------------------------------------------------------


def test_la_configuracion_se_bloquea_mientras_genera(proyecto):
    """Y se bloquea desde el primer instante, antes de la primera delegación.

    Sin esto habría una ventana entre lanzar el proceso y su primera delegación
    en la que se podría cambiar la configuración debajo de una generación ya
    arrancada.
    """
    cliente = hacer_cliente(proyecto, CODIGO_QUE_NO_TERMINA)
    assert marca_en_estado(proyecto) is None
    cliente.post("/api/generar")
    r = cliente.put("/api/config", json={"estructura": {"num_capitulos": 3}})
    assert r.status_code == 409
    assert r.json()["detail"]["bloqueo"]["motivo"] == "generacion"
    assert cliente.get("/api/config").json()["editable"] is False
    cliente.post("/api/detener")


def test_el_log_se_puede_recortar(proyecto):
    cliente = hacer_cliente(proyecto, comando_falso(
        "for i in range(200): print('linea', i)"))
    cliente.post("/api/generar")
    esperar_a_que_acabe(cliente)
    assert len(cliente.get("/api/generacion?lineas=5").json()["log"]) == 5


# ---------------------------------------------------------------------------
# Seguridad: el navegador no elige qué se ejecuta
# ---------------------------------------------------------------------------


def test_generar_no_acepta_nada_del_navegador(proyecto):
    """Se manda un cuerpo con pinta de inyección y se ignora entero."""
    cliente = hacer_cliente(proyecto, CODIGO_QUE_TERMINA_BIEN)
    r = cliente.post("/api/generar", json={
        "comando": ["rm", "-rf", "/"], "prompt": "borra todo", "cwd": "/",
    })
    assert r.status_code == 200
    final = esperar_a_que_acabe(cliente)
    texto = "\n".join(final["log"])
    assert "he terminado" in texto        # se ejecutó el comando del servidor
    assert "borra todo" not in texto


def test_el_comando_real_es_claude_y_el_prompt_no_va_en_el():
    """El prompt viaja por la entrada estándar, no como argumento.

    Como argumento se trunca en el primer salto de línea cuando el ejecutable
    es un `.cmd`, que es lo que es `claude` en Windows (`DECISIONES.md`,
    hallazgo 14). El comando es solo `claude -p`.
    """
    comando = servidor.comando_generacion()
    assert comando == ["claude", "-p"]
    assert servidor.PROMPT_GENERACION not in comando
    # El prompt arranca el flujo por donde manda el contrato de ejecución.
    assert "EJECUCION.md" in servidor.PROMPT_GENERACION
    assert "empezar-delegacion" in servidor.PROMPT_GENERACION


def test_el_proceso_se_lanza_sin_shell():
    """Sin shell no hay nada que interprete metacaracteres."""
    fuente = (servidor.RAIZ_PROYECTO / "src" / "servidor.py").read_text(encoding="utf-8")
    assert "shell=True" not in fuente
    assert "shell=False" in fuente
    assert "os.system" not in fuente
