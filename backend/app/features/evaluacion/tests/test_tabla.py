"""`PLAN-31` E6: la tabla por brief, `harness/evals/resultados.md` (`SPEC-31` `RF-02`)."""

from app.commons.dominio.enumeraciones import CriterioDeEdicion
from app.commons.invariantes import registro
from app.features.evaluacion import tabla
from app.features.evaluacion.tabla import Celda
from app.features.evaluacion.tabla import Resultado as R


def test_las_columnas_son_el_registro_mas_los_validadores_que_no_son_invariantes():
    cols = tabla.columnas()
    assert [c for c in cols if c in registro.TODAS] == sorted(
        registro.TODAS, key=lambda i: int(i.split("-")[1]))
    for criterio in CriterioDeEdicion:
        assert "INV-26.{0}".format(criterio.value) in cols
    for otro in ("schema.plan", "entrevista.instrucciones", "entrevista.contradicciones",
                 "publicacion"):
        assert otro in cols


def test_un_brief_sin_ejecutar_dice_sin_ejecutar_en_todas_sus_columnas():
    fila = tabla.fila_sin_ejecutar()
    for col, celda in fila.items():
        if col in registro.obsoletas():
            assert celda.resultado is R.NO_APLICA
        elif col == "INV-06":
            assert celda.resultado is R.NO_EJECUTADO
        else:
            assert celda.resultado is R.SIN_EJECUTAR, col


def test_inv06_sale_como_no_ejecutado_en_todas_las_filas():
    ejecutada = {c: Celda(R.PASO) for c in tabla.columnas()}
    ejecutada["INV-06"] = Celda(R.NO_EJECUTADO, motivo="SPEC-30 RF-12")
    texto = tabla.generar([
        tabla.Fila("brief-base", "antes", ejecutada, ejecucion="e-1"),
        tabla.Fila("brief-injection", "antes", None)])
    filas = [l for l in texto.splitlines() if l.startswith("| brief-")]
    assert len(filas) == 10, "cinco briefs por dos pasadas"
    columna = tabla.columnas().index("INV-06") + 2
    for linea in filas:
        assert linea.split("|")[columna].strip() == "no ejecutado"


def test_la_tabla_tiene_una_fila_por_cada_brief_y_pasada_aunque_no_se_haya_ejecutado():
    texto = tabla.generar([])
    for brief in ("brief-base", "brief-injection", "brief-incoherencia-temporal",
                  "brief-contradicciones", "brief-vetadas-por-variantes"):
        filas = [l for l in texto.splitlines() if l.startswith("| {0} |".format(brief))]
        assert len(filas) == 2, brief
    assert "sin ejecutar" in texto and "Ningun brief se ha ejecutado" in texto


def test_una_celda_con_disparos_los_dice():
    assert Celda(R.PASO, disparos=1).texto == "pasó (1 disparo)"
    assert Celda(R.PASO).texto == "pasó"
    assert Celda(R.FALLO, disparos=3).texto == "falló (3 disparos)"
