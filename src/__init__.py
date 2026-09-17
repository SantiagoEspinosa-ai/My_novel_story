"""Paquete del harness generador de novelas.

Este archivo esta vacio a proposito: su unica funcion es marcar la carpeta
`src/` como un paquete de Python, para poder escribir `from src.config import
cargar_config` o ejecutar `python -m src.orquestacion`.

Aqui vive solo el codigo de apoyo del harness: configuracion, contratos de
datos, ventanas de contexto y estado en disco. Ninguno de estos modulos sale a
la red. Quien habla con los modelos es Claude Code, delegando en los subagentes
de `.claude/agents/`.
"""
