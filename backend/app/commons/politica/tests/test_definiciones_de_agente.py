"""`PLAN-40` Q3 (`SPEC-40` `RF-02`): las definiciones de los agentes del pipeline no hablan del
regalo. Se excluye al inspector visual, que no escribe la novela: mira la web."""

import pathlib

from app.commons.politica.vista_de_agentes import PALABRAS_DEL_REGALO

AGENTES = pathlib.Path(__file__).resolve().parents[5] / ".claude" / "agents"
FUERA = {"inspector_visual.md"}


def test_ninguna_definicion_de_agente_habla_del_regalo():
    culpables = []
    for f in sorted(AGENTES.glob("*.md")):
        if f.name in FUERA:
            continue
        for n, linea in enumerate(f.read_text(encoding="utf-8").splitlines(), 1):
            m = PALABRAS_DEL_REGALO.search(linea)
            if m:
                culpables.append("{0}:{1}: {2}".format(f.name, n, m.group()))
    assert culpables == []
