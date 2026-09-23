"""Montar los siete bloques con **texto**, no con numeros.

Hasta `PLAN-01` F5 el contexto era un diccionario de tamaños: el recorte
operaba sobre una ficcion y nunca se acercaba al techo. Esto es lo que lo
convierte en material de verdad, y es lo que hara que `VER-37` se pueda
contestar.

RECIBE EL MATERIAL, NO LO VA A BUSCAR
---------------------------------------
Este modulo **no importa `consolidacion/` ni `escaleta/`**. `A-02` dice que una
feature nunca depende de otra, y en `F3` se aprendio que el acoplamiento
tambien viaja por SQL sin que ningun `import` lo delate (`F-28`, `PC-18`). Asi
que quien reune el material es `orquestacion/`, la unica autorizada a componer,
y aqui solo se monta.

EL ORDEN DE LOS BLOQUES ES EL DE `SPEC-01` 2.4, Y NO SE TOCA AQUI
-------------------------------------------------------------------
Se importa de `bloques.py`. Repetirlo seria dos copias del mismo dato, y el
orden se cambia por spec y nunca por configuracion.
"""

import json

from app.features.contexto.bloques import BLOQUES


def _texto_resumenes(material):
    return "\n".join("[{0}] {1}".format(r["escena"], r["texto"])
                     for r in material.get("resumenes", []))


def _texto_fichas(material):
    return "\n".join("[{0} @{1}] {2}".format(f["entidad"], f["version_en_t"],
                                             f["resumen"])
                     for f in material.get("fichas", []))


def _texto_estado(material):
    """El bloque 4: el que nunca se elimina.

    Lleva el registro de conocimiento **entero**, el grafo de accesos entero,
    quien esta vivo y donde. Es lo que leen `INV-02` e `INV-03`, las dos
    `bloqueante` de escena que miran el contexto.
    """
    mundo = material.get("mundo") or {}
    conocimiento = ["{0} sabe {1} desde {2}".format(s, h, d["desde"])
                    for (s, h), d in sorted((mundo.get("conocimiento") or {}).items())]
    return "\n".join([
        "vivos: " + json.dumps(mundo.get("entidades_vivas") or {}, sort_keys=True),
        "donde: " + json.dumps(mundo.get("ubicaciones") or {}, sort_keys=True),
        "accesos: " + json.dumps(mundo.get("accesos") or {}, sort_keys=True),
        "conocimiento:",
    ] + conocimiento)


def _texto_problemas(material):
    return "\n".join("[{0}] {1}".format(p["invariante"], p["descripcion"])
                     for p in material.get("problemas", []))


CONSTRUCTORES = {
    "condensaciones": _texto_resumenes,
    "fichas_y_setups": _texto_fichas,
    "escena_anterior": lambda m: m.get("escena_anterior") or "",
    "estado_y_conocimiento": _texto_estado,
    "problemas_del_intento_anterior": _texto_problemas,
    "reserva_de_salida": lambda m: "",   # no es texto: es sitio que se aparta
    "inmutable": lambda m: m.get("inmutable") or "",
}


def montar(material: dict) -> dict:
    """Devuelve `{nombre_de_bloque: texto}` en el orden de 2.4."""
    return {b.nombre: CONSTRUCTORES[b.nombre](material) for b in BLOQUES}


def tamanos(bloques: dict, reserva_de_salida=20_000) -> dict:
    """Los tokens estimados de cada bloque.

    Estimacion conservadora, no cuenta exacta: decide **si** hay que recortar,
    no **por cuanto**, y contar exacto en cada vuelta del bucle paga el
    tokenizador sin ganar nada (`SPEC-12` C-3, `tokens_para_recortar`).

    La reserva de salida no tiene texto y ocupa igual: es sitio apartado para
    lo que el modelo va a escribir, y recortarla no es recortar contexto, es
    truncar la escena.
    """
    from app.commons.modelo.presupuesto import estimar_para_recortar

    medidos = {n: estimar_para_recortar(t) for n, t in bloques.items()}
    medidos["reserva_de_salida"] = reserva_de_salida
    return medidos


def aplicar_recorte(bloques: dict, plan) -> dict:
    """Deja los bloques como los dejo el plan: reducidos o fuera.

    La forma reducida de cada bloque la declara `bloques.py`; aqui solo se
    ejecuta. Un bloque **eliminado** queda como cadena vacia y no desaparece
    del diccionario: quien lo lea despues tiene que poder ver que estaba y se
    fue, que es la mitad de lo que hace util una traza de recortes.
    """
    from app.features.contexto.bloques import FRACCION_REDUCIDA, Clase

    fuera = dict(bloques)
    for paso in plan:
        texto = fuera.get(paso.bloque, "")
        if paso.clase is Clase.ELIMINACION:
            fuera[paso.bloque] = ""
        else:
            fuera[paso.bloque] = texto[:max(1, int(len(texto) * FRACCION_REDUCIDA))]
    return fuera
