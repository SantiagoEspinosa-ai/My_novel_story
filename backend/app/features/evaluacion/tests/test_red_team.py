"""`PLAN-31` E8: el red-team log de `harness/adversarial/` (`SPEC-31` `RF-05`, `RF-12`).

Cada caso nombra el validador que lo detecto, o dice «ninguno»: un caso sin detector
declarado se leeria como detectado. Y cada prueba que cita existe: un caso que cita una
prueba inventada es un caso inventado.
"""

import json
import pathlib

from app.features.evaluacion import tabla

RAIZ = pathlib.Path(__file__).resolve().parents[5]
ADVERSARIAL = RAIZ / "harness" / "adversarial"
OTROS_DETECTORES = {"hook.policy", "hook.validar_capitulo"}


def _casos():
    return json.loads((ADVERSARIAL / "casos.json").read_text(encoding="utf-8"))["casos"]


def _definidas():
    nombres = set()
    for py in (RAIZ / "backend").rglob("test_*.py"):
        for linea in py.read_text(encoding="utf-8").splitlines():
            if linea.startswith("def test_"):
                nombres.add(linea[4:].split("(")[0])
    return nombres


def test_cada_caso_del_red_team_nombra_su_validador_o_dice_ninguno():
    casos = _casos()
    assert casos
    validos = set(tabla.columnas()) | OTROS_DETECTORES | {"ninguno"}
    for c in casos:
        assert c["detector"] in validos, (c["id"], c["detector"])
        for campo in ("caso", "como_se_probo", "resultado", "punto_ciego", "resolucion"):
            assert (c.get(campo) or "").strip(), (c["id"], campo)


def test_hay_casos_de_los_tres_que_pide_la_spec_y_alguno_sin_detector():
    """`RF-12`: injection, vetadas por variantes y exfiltracion entre dos novelas. Y el
    log no es de exitos: lo que no detecto nadie esta tambien."""
    casos = _casos()
    temas = {c["tema"] for c in casos}
    assert {"injection", "vetadas_por_variantes", "exfiltracion"} <= temas
    assert any(c["detector"] == "ninguno" for c in casos)


def test_las_pruebas_que_cita_cada_caso_existen():
    definidas = _definidas()
    for c in _casos():
        assert c["pruebas"], c["id"]
        for p in c["pruebas"]:
            assert p in definidas, (c["id"], p)


def test_los_identificadores_de_los_casos_no_se_repiten():
    ids = [c["id"] for c in _casos()]
    assert len(ids) == len(set(ids))


def test_una_derivada_de_una_vetada_no_se_caza():
    """El punto ciego de `RT-04`, escrito como prueba para que no se olvide: la
    normalizacion reduce variantes simples, no derivadas ni conjugaciones. El dia que
    esta prueba falle, el caso ha cambiado y el log tiene que decirlo."""
    from app.commons.politica.vetadas import coincidencias
    assert coincidencias("un pasillo hospitalario", ["hospital"]) == []
    assert coincidencias("un cielo tormentoso", ["tormenta"]) == []
    assert coincidencias("los HOSPITALES", ["hospital"])
