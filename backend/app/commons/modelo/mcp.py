"""Un servidor MCP por stdio, minimo y propio (`PLAN-28` `D-1`).

Solo hace falta `initialize`, `tools/list` y `tools/call` sobre JSON-RPC por lineas, y el
esquema de entrada de cada tool lo da Pydantic. No se usa un SDK: el paquete `mcp` no
esta instalado y el proyecto no añade dependencias sin que una spec lo pida. **El riesgo**
es una version del protocolo que Claude Code no acepte, y solo lo dice una ejecucion real
(`PLAN-28` E10); si pasa, se cambia al SDK oficial con el mismo modulo de tools detras.

Es transporte, como `proveedor.py`: no importa ninguna feature. Recibe el catalogo y una
funcion que atiende.
"""

import json


def _responder(salida, id_, resultado=None, error=None):
    mensaje = {"jsonrpc": "2.0", "id": id_}
    if error is not None:
        mensaje["error"] = error
    else:
        mensaje["result"] = resultado
    salida.write(json.dumps(mensaje, ensure_ascii=False) + "\n")
    salida.flush()


def servir(entrada, salida, catalogo, atender, nombre="story_bible"):
    for linea in entrada:
        if not linea.strip():
            continue
        try:
            mensaje = json.loads(linea)
        except json.JSONDecodeError:
            _responder(salida, None, error={"code": -32700, "message": "JSON invalido"})
            continue
        metodo, id_ = mensaje.get("method"), mensaje.get("id")
        if id_ is None:
            continue  # una notificacion no recibe respuesta
        params = mensaje.get("params") or {}
        if metodo == "initialize":
            _responder(salida, id_, {
                "protocolVersion": params.get("protocolVersion", "2025-06-18"),
                "capabilities": {"tools": {}},
                "serverInfo": {"name": nombre, "version": "1"}})
        elif metodo == "tools/list":
            _responder(salida, id_, {"tools": catalogo})
        elif metodo == "tools/call":
            _responder(salida, id_, atender(params.get("name"), params.get("arguments") or {}))
        else:
            _responder(salida, id_, error={"code": -32601,
                                           "message": "metodo no soportado: {0}".format(metodo)})
