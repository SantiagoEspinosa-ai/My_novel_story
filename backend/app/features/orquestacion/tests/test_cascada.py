"""`PLAN-23` Parte B, rama `S-1`: la salida fijada por la medida y la cascada.

Ningun paso llama al modelo real: los agentes son dobles con la misma forma que los de
`novela_regalo.agentes` (un `llamar(prompt)` que devuelve un diccionario). Datos
inventados.
"""

import json
import os

from app.features.orquestacion import arrastre, regeneracion

RAIZ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.dirname(os.path.abspath(__file__)))))))
MEDIDA = os.path.join(RAIZ, "harness", "evals", "arrastre-SPEC-23.json")


# --- B2 · la salida, fijada con el numero y no con una opinion ---------------------

def test_la_salida_fijada_es_la_que_da_la_regla_con_el_numero_guardado():
    """Si alguien cambia `SALIDA` sin cambiar la medida -o la medida sin `SALIDA`-,
    falla. El numero es el de B1, guardado en el repositorio."""
    with open(MEDIDA, encoding="utf-8") as f:
        medida = json.load(f)
    assert medida["medido"] is True, "sin medida no se elige salida (`SPEC-23` v2)"
    assert medida["umbral"] == arrastre.UMBRAL_DE_CAPITULOS
    assert regeneracion.SALIDA == arrastre.salida_para(medida["arrastre_medio"])
    assert regeneracion.SALIDA == medida["salida"]
