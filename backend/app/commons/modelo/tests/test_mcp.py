"""`PLAN-28` E4: el bucle JSON-RPC por stdio del servidor MCP, en memoria.

Lo que no prueban estas pruebas: que Claude Code acepte este `initialize`. Eso lo
comprueba la ejecucion real de `PLAN-28` E10.
"""

import io
import json

from app.commons.modelo.mcp import servir

CATALOGO = [{"name": "eco", "description": "devuelve lo que recibe",
             "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}}}]


def _conversar(*mensajes):
    entrada = io.StringIO("".join(json.dumps(m) + "\n" for m in mensajes))
    salida = io.StringIO()
    llamadas = []

    def atender(nombre, argumentos):
        llamadas.append((nombre, argumentos))
        return {"content": [{"type": "text", "text": argumentos.get("x", "")}], "isError": False}

    servir(entrada, salida, CATALOGO, atender)
    return [json.loads(l) for l in salida.getvalue().splitlines() if l.strip()], llamadas


def test_initialize_tools_list_y_tools_call_en_memoria():
    respuestas, llamadas = _conversar(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize",
         "params": {"protocolVersion": "2025-06-18"}},
        {"jsonrpc": "2.0", "method": "notifications/initialized"},
        {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
        {"jsonrpc": "2.0", "id": 3, "method": "tools/call",
         "params": {"name": "eco", "arguments": {"x": "hola"}}})
    assert [r["id"] for r in respuestas] == [1, 2, 3]
    assert respuestas[0]["result"]["protocolVersion"] == "2025-06-18"
    assert "tools" in respuestas[0]["result"]["capabilities"]
    assert respuestas[2]["result"]["content"][0]["text"] == "hola"
    assert llamadas == [("eco", {"x": "hola"})]


def test_tools_list_publica_el_esquema_de_entrada():
    respuestas, _ = _conversar({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
    assert respuestas[0]["result"]["tools"] == CATALOGO


def test_una_notificacion_no_recibe_respuesta():
    respuestas, _ = _conversar({"jsonrpc": "2.0", "method": "notifications/initialized"})
    assert respuestas == []


def test_un_metodo_desconocido_es_un_error_jsonrpc():
    respuestas, _ = _conversar({"jsonrpc": "2.0", "id": 9, "method": "resources/list"})
    assert respuestas[0]["error"]["code"] == -32601
