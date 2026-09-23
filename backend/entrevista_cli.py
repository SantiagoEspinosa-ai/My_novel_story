"""La entrevista desde la terminal: una CLI fina sobre la API (`SPEC-25` `RF-06`).

    uvicorn app.main:app                      # en otra terminal
    python -X utf8 entrevista_cli.py          # contra http://127.0.0.1:8000
    python -X utf8 entrevista_cli.py --api http://otra:8000

**No tiene logica propia**: no importa nada de `app`, solo habla HTTP. Lo que
falta, lo que se contradice y si se puede cerrar lo decide la API; esto solo
pregunta, espera el trabajo y enseña lo que vuelve. Una prueba comprueba que no
importa `app` (`test_cli.py`).

ORDENES
-------
    :texto     pegar un texto libre (carta, anecdota); se termina con una linea
               que solo tenga un punto
    :confirmar <id>   /   :descartar <id>    un hecho propuesto del texto libre
    :cerrar    confirmar la ficha y obtener el brief
    :salir     salir sin cerrar

**Llama al modelo de verdad** si la API esta configurada con sesiones delegadas,
asi que cada turno cuesta dinero. `-X utf8` porque la consola de Windows no es
UTF-8 por defecto.
"""

import argparse
import json
import sys
import time

import httpx


def esperar(cliente, id_trabajo, espera=1.0, tope=600):
    """Consulta el trabajo hasta que termina o falla. `tope` son consultas."""
    for _ in range(tope):
        t = cliente.get("/trabajos/" + id_trabajo).json()
        if t["estado"] in ("terminado", "fallido", "abandonado"):
            return t
        time.sleep(espera)
    raise TimeoutError("el trabajo {0} no termino".format(id_trabajo))


def _mostrar_estado(r, salida):
    for c in r.get("contradicciones") or []:
        salida("  ! contradiccion: " + c["descripcion"])
    for a in r.get("avisos") or []:
        salida("  ! aviso: " + a)
    for h in (r.get("ficha") or {}).get("hechos_propuestos") or []:
        if h["estado"] == "propuesto":
            salida("  ? hecho propuesto [{0}]: {1}".format(h["id"], h["texto"]))
    if r.get("falta"):
        salida("  (falta: {0})".format(", ".join(r["falta"])))


def _leer_texto(entrada):
    lineas = []
    while True:
        linea = entrada("... ")
        if linea.strip() == ".":
            return "\n".join(lineas)
        lineas.append(linea)


def dialogar(cliente, entrada=input, salida=print, espera=1.0):
    """Devuelve el brief si se cierra, o `None` si se sale."""
    e = cliente.post("/entrevistas").json()
    salida(e["pregunta"])
    while True:
        respuesta = entrada("> ").strip()
        if not respuesta:
            continue
        if respuesta == ":salir":
            salida("Entrevista {0} sin cerrar.".format(e["id"]))
            return None
        if respuesta == ":cerrar":
            r = cliente.post("/entrevistas/{0}/cerrar".format(e["id"]))
            if r.status_code == 200:
                salida("Ficha confirmada.")
                return r.json()
            salida("Todavia no se puede cerrar: " + str(r.json()["detail"]["motivo"]))
            continue
        orden, _, argumento = respuesta.partition(" ")
        if orden in (":confirmar", ":descartar"):
            r = cliente.post("/entrevistas/{0}/hechos/{1}/{2}".format(
                e["id"], argumento.strip(), orden[1:]))
            salida("Hecho {0}.".format("confirmado" if orden == ":confirmar"
                                       else "descartado") if r.status_code == 200
                   else "No se pudo: " + str(r.json().get("detail")))
            continue
        if orden == ":texto":
            r = cliente.post("/entrevistas/{0}/texto-libre".format(e["id"]),
                             json={"texto": _leer_texto(entrada)})
        else:
            r = cliente.post("/entrevistas/{0}/turnos".format(e["id"]),
                             json={"respuesta": respuesta})
        if r.status_code != 202:
            salida("Error {0}: {1}".format(r.status_code, r.json().get("detail")))
            continue
        t = esperar(cliente, r.json()["id_trabajo"], espera=espera)
        if t["estado"] != "terminado":
            salida("El turno fallo ({0}): {1}".format(t["estado"], t.get("motivo")))
            continue
        resultado = t["resultado"]
        if "pregunta" in resultado:
            salida(resultado["pregunta"])
            _mostrar_estado(resultado, salida)
        else:
            salida("Hechos propuestos: {0}".format(len(resultado["hechos"])))
            for h in resultado["hechos"]:
                salida("  ? [{0}] {1}".format(h["id"], h["texto"]))
            if resultado.get("instrucciones_detectadas"):
                salida("  ! el texto traia instrucciones y se ha descartado")


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--api", default="http://127.0.0.1:8000")
    args = p.parse_args(argv)
    with httpx.Client(base_url=args.api, timeout=30) as cliente:
        brief = dialogar(cliente)
    if brief is not None:
        print(json.dumps(brief, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
