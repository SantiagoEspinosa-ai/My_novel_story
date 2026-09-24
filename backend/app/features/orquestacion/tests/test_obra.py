"""F6 — El bucle de escenas, contra dobles.

Lo que se comprueba aqui es el **encadenado**: que el material de la escena N
incluya lo que dejo la N-1, que el contexto crezca, y que una `bloqueante`
detenga la obra en vez de saltarsela.
"""

import sqlite3

import pytest

from app.commons.modelo.doble import DobleDelModelo
from app.features.consolidacion import aplicar, memoria, mundo
from app.features.escaleta import repository as repo
from app.features.orquestacion import obra


class Devuelve:
    def __init__(self, respuesta, nombre="doble"):
        self.nombre, self._r = nombre, respuesta

    def llamar(self, prompt):
        return dict(self._r, medidas={"modelos": ["doble-1"], "tokens_entrada": 5,
                                      "tokens_salida": 5})


@pytest.fixture
def con():
    c = sqlite3.connect(":memory:")
    repo.asegurar_tablas(c)
    aplicar.asegurar_tablas(c)
    memoria.asegurar_tablas(c)
    aplicar.sembrar(c, {"per-marta": ("vivo", "lug-salon")})
    mundo.sembrar_lugares(c, {"lug-salon": ["lug-sotano"], "lug-sotano": ["lug-salon"]})
    repo.guardar_escaleta(c, "cap-1", [
        {"id": "e{0}".format(i), "orden": i,
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
         "pov": "per-marta", "lugar": "lug-salon",
         "beats": ["b"], "longitud_objetivo": [10, 5000]} for i in (1, 2, 3)])
    return c


def _agentes():
    return (DobleDelModelo(),
            Devuelve({"veredicto": "PASA", "problemas": []}),
            Devuelve({"texto": "Resumen de la escena. " * 10,
                      "hechos_clave": ["hec-llave"]}))


def test_genera_las_tres_escenas_en_orden(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1", "e2", "e3"]
    assert g.llego_al_final


def test_el_material_de_la_escena_2_incluye_lo_que_dejo_la_1(con):
    """El encadenado: sin esto la 2 genera contra el mundo de la 1."""
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    material = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert material["resumenes"], "el resumen de la 1 esta disponible en la 2"
    assert material["escena_anterior"], "y el texto de la 1 tambien"


def test_el_contexto_crece_escena_a_escena(con):
    """El criterio de terminacion de la Fase F, y el unico que importa."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    totales = [m["total"] for m in g.medidas]
    assert totales == sorted(totales), "no decrece: {0}".format(totales)
    assert totales[-1] > totales[0], "tiene que crecer solo: {0}".format(totales)


def test_una_bloqueante_detiene_la_obra_y_deja_el_dato(con):
    """No se rinde y no se salta. Y la parada **es la medida** (`VER-64`)."""
    with con:
        con.execute("UPDATE escena SET cambio_de_valor='null' WHERE id='e2'")
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.escenas_hechas == ["e1"]
    assert g.parada["escena"] == "e2"
    assert any(inv == "INV-01" for inv, _ in g.parada["hallazgos"])
    assert "INV-01" in obra.informe(g)


def test_rf26_detiene_la_obra_sin_llamar_al_modelo(con):
    """Con un techo imposible no se genera: se falla antes."""
    escritor = DobleDelModelo()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1)
    assert g.parada["motivo"] == "no_cabe"
    assert escritor.llamadas == []


def test_el_informe_dice_si_el_contexto_crece(con):
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert "CRECE" in obra.informe(g)


# --- SPEC-15: los hechos los declara el plan, y el prompt los lleva --------

class Revela:
    """Un doble que **revela**, que es lo que el de serie nunca hace.

    Regla 3 aplicada a las pruebas: un doble que solo sabe portarse bien pasa
    contra si mismo. Sin este, el marcado de `escena_de_establecimiento` no
    tendria ningun caso que lo ejercite.
    """

    nombre = "doble-que-revela"

    def __init__(self):
        self.llamadas = []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return {"texto": " ".join(["palabra"] * 1500),
                "pov_usado": "per-marta",
                "delta": {"cambio_de_valor": {"eje": "cordura",
                                              "signo": "negativo"},
                          "movimientos": [],
                          "revelaciones": [{"sujeto": "per-marta",
                                            "hecho": "hec-llave",
                                            "grado": "sabe"}]},
                "usage": {"total_tokens": 2100}}


def test_los_hechos_declarados_llegan_al_prompt(con):
    """El punto muerto de `F-29`: la lista salia del registro de conocimiento,
    que solo crecia con revelaciones, que necesitaban la lista."""
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert "hec-llave" in escritor.llamadas[0]


def test_sin_hechos_declarados_el_prompt_no_inventa_ninguno(con):
    """El caso negativo: que aparezca uno aqui seria el prompt fabricandolo."""
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert "hec-" not in escritor.llamadas[0]


def test_una_revelacion_marca_donde_el_texto_establece_el_hecho(con):
    """`SPEC-15` C-1: `escena_de_establecimiento` es donde lo establece el
    TEXTO, no donde nacio el hecho. Y `SPEC-16` C-4: establecer un hecho **es**
    su primera revelacion.

    Esta prueba estuvo marcada `xfail(strict)` mientras `F-31` estuvo abierto:
    la obra paraba en `e1` y no se llegaba a marcar nada. Se retira la marca
    porque el fallo esta corregido, no porque la prueba se haya ablandado.
    """
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    obra.generar_obra(con, "cap-1", Revela(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    hechos = repo.hechos_declarados(con, "cap-1")
    assert hechos[0]["establecido_en"] == "e1"


def test_el_material_de_una_escena_lleva_los_hechos_de_su_obra(con):
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano se perdio"}])
    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    material = obra.reunir_material(con, repo.escena(con, "e1"), "cap-1")
    assert [h["id"] for h in material["hechos"]] == ["hec-llave"]


def test_una_accion_sin_conocimiento_detiene_la_obra(con):
    """El circuito entero contra el doble, y el caso que `F-24` cazo en real.

    El doble tiene que poder producirlo: si solo sabe portarse bien, el bucle
    pasa contra el doble y falla contra el proveedor (`F-18`, Regla 3).
    """
    from app.commons.modelo.doble import Guion

    escritor = DobleDelModelo(Guion(["actua_sin_saber"]))
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000)
    assert g.escenas_hechas == []
    assert g.parada["escena"] == "e1"
    assert any(inv == "INV-03" for inv, _ in g.parada["hallazgos"])


# --- Los intentos, la rendicion y el tope global --------------------------

class SiempreCorto:
    """Produce siempre una escena fuera de rango: `INV-17`, `mayor`.

    Molesta y no corrompe, asi que es exactamente lo que se rinde.
    """

    nombre = "doble-corto"

    def __init__(self):
        self.llamadas = []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return {"texto": " ".join(["palabra"] * 3), "pov_usado": "per-marta",
                "delta": {"cambio_de_valor": {"eje": "cordura", "signo": "negativo"}},
                "usage": {"total_tokens": 100}}


def test_una_escena_con_un_mayor_se_reintenta_y_acaba_rindiendose(con):
    """`RF-24`: los intentos se agotan y la escena pasa a
    `aceptada_por_rendicion`, no a `aceptada`. Quien lea el manuscrito tiene
    que poder distinguirlas."""
    escritor = SiempreCorto()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000, hasta=1, tope_intentos=3)
    assert len(escritor.llamadas) == 3, "se agotan los intentos antes de rendirse"
    assert g.escenas_hechas == ["e1"]
    # `SPEC-30` v4 `RF-11` (`C-3`): se queda en `aceptada_por_rendicion` tambien
    # despues de consolidar. Antes acababa en `consolidada` y la rendicion solo la
    # delataban `rendidas`, que vive en memoria, y los hallazgos abiertos; eso
    # contradecia a `docs/definitions.md`, que la define como estado.
    assert repo.escena(con, "e1")["estado"] == "aceptada_por_rendicion"
    assert repo.escena(con, "e1")["borrador_aceptado"] is not None
    # Los tres intentos empatan -el doble falla siempre igual-, y a igualdad
    # gana el primero: la rendicion tiene que ser reproducible.
    assert g.rendidas == [("e1", 1, 3)]


def test_los_problemas_del_intento_anterior_llegan_al_siguiente(con):
    """Si no, el escritor no sabe nada del fallo y vuelve a cometerlo. Es lo
    que le paso a la otra rama con el aviso de longitud."""
    escritor = SiempreCorto()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1, tope_intentos=2)
    assert "INV-17" in escritor.llamadas[1], "el segundo intento ve el problema"
    assert "INV-17" not in escritor.llamadas[0], "y el primero no, porque no habia"


def test_una_bloqueante_no_se_rinde_por_muchos_intentos_que_queden(con):
    """La falsedad entraria al canon y la heredarian todas las siguientes."""
    from app.commons.modelo.doble import Guion

    escritor = DobleDelModelo(Guion(["actua_sin_saber"]))
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000, tope_intentos=3)
    assert g.parada["escena"] == "e1"
    assert repo.escena(con, "e1")["estado"] != "aceptada_por_rendicion"


def test_el_tope_global_de_delegaciones_detiene_la_obra(con):
    """Acota el gasto, no el error: la parada dice cuantas llevaba."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000,
                          tope_delegaciones=2)
    assert g.parada["motivo"] == "tope_delegaciones"
    assert g.parada["delegaciones"] >= 2
    assert len(g.escenas_hechas) < 3, "no llego al final"


# --- La puerta de capitulo, al terminar la obra ---------------------------

def test_al_terminar_se_evalua_el_cierre_pero_no_se_firma(con):
    """La firma es **humana** y la dispara el cliente de la API, nunca el
    worker (`docs/architecture.md`). Lo que hace el bucle al terminar es decir
    si el capitulo **podria** cerrarse, que es distinto de cerrarlo."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000)
    assert g.llego_al_final
    assert g.cierre["puede_cerrarse"] is True
    assert g.cierre["firmado"] is False, "el bucle no firma"


def test_una_escena_rendida_deja_el_capitulo_sin_poder_cerrarse(con):
    """El control no desaparecio al dejar pasar un `mayor`: se movio aqui."""
    g = obra.generar_obra(con, "cap-1", SiempreCorto(), *_agentes()[1:],
                          techo=1_000_000, tope_intentos=2)
    assert g.rendidas, "las tres escenas se rindieron"
    assert g.cierre["puede_cerrarse"] is False
    assert "INV-17" in g.cierre["motivo"] or "mayor" in g.cierre["motivo"]


def test_si_la_obra_se_detiene_no_se_evalua_el_cierre(con):
    """Un capitulo con escenas a medias no es un capitulo, y preguntarselo a
    la puerta seria pedirle que juzgue algo que no ha terminado."""
    from app.commons.modelo.doble import Guion

    g = obra.generar_obra(con, "cap-1", DobleDelModelo(Guion(["actua_sin_saber"])),
                          *_agentes()[1:], techo=1_000_000)
    assert g.parada is not None
    assert g.cierre is None


def test_la_generacion_acumula_el_coste_y_dice_que_delegaciones_no_lo_traen(con):
    """El coste **se lee, no se deduce** (`F-25`): el volumen no lo predice,
    porque el precio del modelo pesa mas que la cantidad de tokens.

    Y las delegaciones sin cifra se cuentan aparte en vez de sumar cero: un
    cero se lee como un dato y un hueco no.
    """
    class ConCoste(Devuelve):
        def llamar(self, prompt):
            r = dict(self._r)
            r["medidas"] = {"modelos": ["m"], "tokens_entrada": 5,
                            "tokens_salida": 5, "coste_usd": 0.01}
            return r

    agentes = (DobleDelModelo(),
               ConCoste({"veredicto": "PASA", "problemas": []}),
               ConCoste({"texto": "R. " * 10, "hechos_clave": []}))
    g = obra.generar_obra(con, "cap-1", *agentes, techo=1_000_000, hasta=1)
    assert g.coste["usd"] == pytest.approx(0.02), "las dos que lo traen"
    assert g.coste["sin_coste"] == 1, "el escritor doble no lo trae"
    assert g.coste["delegaciones"] == 3


# --- F-38: reanudar sin regenerar ni degradar lo que iba bien -------------

def test_relanzar_salta_lo_consolidado_y_no_lo_toca(con):
    """`F-38`: la segunda pasada regeneraba `e1` ya consolidada, pagaba la
    delegacion, le guardaba un borrador 2 y **la degradaba a `generada`**. Cada
    parada devolvia al principio y estropeaba lo que iba bien."""
    from app.commons.modelo.doble import Guion

    obra.generar_obra(con, "cap-1", DobleDelModelo(Guion(["bien", "actua_sin_saber"])),
                      *_agentes()[1:], techo=1_000_000)
    assert repo.escena(con, "e1")["estado"] == "consolidada"

    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1_000_000)
    assert repo.escena(con, "e1")["estado"] == "consolidada", "no se degrada"
    assert repo.intentos_de(con, "e1") == 1, "no se regenera: no se paga dos veces"


def test_relanzar_continua_por_la_escena_que_fallo(con):
    from app.commons.modelo.doble import Guion

    g1 = obra.generar_obra(con, "cap-1", DobleDelModelo(Guion(["bien", "actua_sin_saber"])),
                           *_agentes()[1:], techo=1_000_000)
    assert g1.parada["escena"] == "e2"

    g2 = obra.generar_obra(con, "cap-1", DobleDelModelo(), *_agentes()[1:],
                           techo=1_000_000)
    assert g2.escenas_hechas == ["e2", "e3"], "sigue donde lo dejo"
    assert g2.llego_al_final


def test_lo_saltado_se_dice_para_que_el_informe_no_mienta(con):
    """Un informe que dice "2 escenas" cuando la obra tiene 3 induce a pensar
    que falta una. Saltar no es lo mismo que no hacer."""
    from app.commons.modelo.doble import Guion

    obra.generar_obra(con, "cap-1", DobleDelModelo(Guion(["bien", "actua_sin_saber"])),
                      *_agentes()[1:], techo=1_000_000)
    g = obra.generar_obra(con, "cap-1", DobleDelModelo(), *_agentes()[1:],
                          techo=1_000_000)
    assert g.saltadas == ["e1"]
    assert "saltadas" in obra.informe(g) or "e1" in obra.informe(g)


def test_una_instruccion_humana_entra_en_el_prompt_del_reintento(con):
    """`F-38`, tercera pieza. El canal ya existia -los problemas del intento
    anterior- y **no habia forma de escribir en el desde fuera**. Sin esto,
    desatascar obliga a replanificar la escena aunque lo unico que falte sea
    decirle al modelo lo que hizo mal."""
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1_000_000,
                      hasta=1,
                      instrucciones=["Marta ya sabe que el sotano esta cerrado: "
                                     "declara la revelacion en el delta"])
    assert "declara la revelacion en el delta" in escritor.llamadas[0]


def test_sin_instruccion_el_prompt_no_lleva_ninguna(con):
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1_000_000,
                      hasta=1)
    assert "INSTRUCCION" not in escritor.llamadas[0].upper()


def test_la_instruccion_se_distingue_de_un_hallazgo_en_el_prompt(con):
    """Un hallazgo lo levanto una regla; una instruccion la escribio una
    persona. Mezclarlos haria que el modelo no supiera cual es cual, y que
    quien lea la traza no pueda saber de donde salio cada cosa."""
    escritor = DobleDelModelo()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:], techo=1_000_000,
                      hasta=1, instrucciones=["haz esto otro"])
    prompt = escritor.llamadas[0]
    assert "haz esto otro" in prompt
    assert "PERSONA" in prompt.upper() or "HUMANA" in prompt.upper()


# --- SPEC-19 de punta a punta: prometer, pedirlo y comprobarlo ------------

def test_lo_que_el_beat_promete_llega_al_prompt_y_se_comprueba(con):
    """`F-37` completo: sin las dos mitades esto no funciona. Si solo se
    comprueba, es un rechazo merecido e inutil (Regla 4); si solo se pide, no
    hay nada que detecte que no se hizo."""
    with con:
        con.execute("""UPDATE escena SET beats='[{"id": "b1", "establece":
                       ["hec-sotano"]}]' WHERE id='e1'""")
    escritor = DobleDelModelo()
    g = obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                          techo=1_000_000, hasta=1, tope_intentos=1)
    assert "hec-sotano" in escritor.llamadas[0], "el plan se lo pide"
    abiertos = repo.hallazgos_abiertos(con, "e1")
    assert any(h["invariante"] == "INV-18" for h in abiertos), (
        "y el doble no lo declara, asi que se detecta en la misma escena")
    assert g.rendidas, "un mayor no detiene: se rinde tras agotar intentos"


# --- SPEC-20: quien usa que, calculado por quien puede componer -----------

def test_quien_usa_un_hecho_son_las_escenas_consolidadas_que_lo_revelaron(con):
    """`A-02`: `edicion/` no consulta tablas ajenas, las recibe. Componer es
    cosa de `orquestacion/`, y el acoplamiento por SQL tambien cuenta
    (`F-28`)."""
    obra.generar_obra(con, "cap-1", Revela(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert obra.escenas_que_usan(con, "hecho", "hec-llave") == ["e1"]
    assert obra.escenas_que_usan(con, "hecho", "hec-que-nadie-toco") == []


def test_una_escena_sin_consolidar_no_cuenta_como_uso(con):
    """Lo que no esta en el canon no sostiene nada, asi que no bloquea nada."""
    assert obra.escenas_que_usan(con, "escena", "e1") == []


def test_una_escena_consolidada_se_usa_a_si_misma(con):
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    assert obra.escenas_que_usan(con, "escena", "e1") == ["e1"]


# --- `SPEC-21`: el acta de cada escena, poblada al consolidar ---------------


def _con_hechos_y_capitulo(con):
    """Una obra con hechos declarados, capitulo y momento narrativo."""
    from app.features.cronologia import repository as cron
    cron.asegurar_tablas(con)
    repo.declarar_hechos(con, "cap-1", [
        {"id": "hec-llave", "enunciado": "La llave del sotano esta en el costurero"},
        {"id": "hec-pozo", "enunciado": "El pozo del patio no tiene fondo"},
    ])
    with con:
        for i, t in ((1, "1897-11-03T21:00"), (2, "1897-11-04T10:00"),
                     (3, "1897-11-05T10:00")):
            con.execute(
                "UPDATE escena SET capitulo='cap-1', t_fabula=?, "
                "duracion_ficcional=60, personajes_presentes='[\"per-marta\"]' "
                "WHERE id=?", (t, "e{0}".format(i)))


def test_consolidar_una_escena_deja_escrito_donde_se_usa_cada_hecho(con):
    """`SPEC-21` C-4. Esto es lo que estaba pendiente: nadie poblaba la tabla.

    El doble del modelo devuelve un delta; de el salen `establece` y `depende`,
    y `menciona` lo calcula el codigo sobre el texto ya escrito.
    """
    from app.features.cronologia import consultas, repository as cron
    _con_hechos_y_capitulo(con)
    obra.generar_obra(con, "cap-1", Revela(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    usos = cron.usos_de_hecho(con, "hec-llave")
    assert usos, "la tabla de usos sigue vacia: nadie la puebla"
    assert consultas.capitulos_donde_se_usa(con, "hec-llave") == ["cap-1"]


def test_consolidar_una_escena_deja_su_evento_en_la_cronologia(con):
    from app.features.cronologia import repository as cron
    _con_hechos_y_capitulo(con)
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    eventos = cron.eventos_de(con, "cap-1")
    assert [e["escena"] for e in eventos] == ["e1"]
    assert eventos[0]["lugar"] == "lug-salon"
    assert cron.participantes_de(con, eventos[0]["id"]) == ["per-marta"]


class RevelaYRompe(Revela):
    """Revela un hecho **y** mueve a alguien que no existe, en el mismo delta.

    Hace falta que haga las dos cosas a la vez: un doble que solo rompiera no
    tendria acta que escribir, y la prueba pasaria sin comprobar nada. Es la
    regla 3 otra vez — un doble demasiado limpio no caza lo que el real hace
    mal — aplicada al caso de la transaccion.
    """

    nombre = "doble-que-revela-y-rompe"

    def llamar(self, prompt):
        r = super().llamar(prompt)
        r["delta"]["movimientos"] = [
            {"personaje": "per-nadie", "de": "lug-salon", "a": "lug-sotano"}]
        return r


def test_si_el_delta_no_entra_el_acta_tampoco(con):
    """La otra mitad de C-4, y la que justifica que vaya en la transaccion.

    Una escena cuyo delta es incompatible **no ocurrio**. Si su acta quedara
    escrita, «en que capitulos se usa este hecho» contestaria citando una
    escena que no esta en el manuscrito, y la regeneracion selectiva mandaria
    reescribir un capitulo por un uso que nunca llego a existir.
    """
    from app.features.cronologia import repository as cron
    _con_hechos_y_capitulo(con)
    g = obra.generar_obra(con, "cap-1", RevelaYRompe(), *_agentes()[1:],
                          techo=1_000_000, hasta=1)
    assert g.parada is not None, "el delta tenia que ser incompatible"
    assert cron.usos_de_hecho(con, "hec-llave") == []
    assert cron.eventos_de(con, "cap-1") == []


def test_una_escena_sin_resumen_se_dice_en_vez_de_callarse(con):
    """`F-41`: cinco escenas de doce se quedaron sin resumen en la obra de diez
    capitulos y **nadie lo dijo**. Las escenas siguientes leen un contexto al
    que le falta esa, y desde fuera es indistinguible de una escena que no
    tenia nada que resumir."""
    class Mudo:
        """Se porta como el proveedor real cuando no puede leer la respuesta:
        lanza `RespuestaIlegible`. Un doble que devuelve `None` donde el real
        lanza no es un doble, es otra cosa (Regla 3)."""

        nombre = "resumidor-mudo"

        def llamar(self, prompt):
            from app.commons.modelo.proveedor import RespuestaIlegible
            raise RespuestaIlegible("no se pudo leer la respuesta")

    g = obra.generar_obra(con, "cap-1", DobleDelModelo(),
                          _agentes()[1], Mudo(), techo=1_000_000, hasta=1)
    assert g.escenas_hechas == ["e1"], "la escena se hace igual"
    assert g.sin_resumen == ["e1"], "pero consta que se quedo sin memoria"


def test_la_escena_anterior_no_puede_venir_de_otra_obra(con):
    """`F-40` seguia vivo aqui, y es el bloque que mas pesa del contexto.

    La consulta buscaba `orden - 1` **sin acotar por nada**, con `LIMIT 1`: con
    dos obras en la misma base, `orden - 1` casa con una escena de cada una y
    gana la que salga. El Escritor arrancaba leyendo **entera** una escena de
    otra obra, y nadie lo notaba porque llega texto plausible. Es peor que lo
    de los resumenes, que llegaban desordenados o vacios.
    """
    repo.guardar_escaleta(con, "otra-obra", [
        {"id": "otra-e1", "orden": 1, "pov": "per-marta", "lugar": "lug-salon",
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"},
         "beats": ["b"], "longitud_objetivo": [10, 5000]}])
    # Dos borradores: la version 2 gana el `ORDER BY b.version DESC LIMIT 1`.
    # Es lo que pasa en cuanto una escena de otra obra se reintenta una vez, y
    # con un solo intento el empate lo resolvia el azar del rowid.
    repo.guardar_borrador(con, "otra-e1", texto="PRIMERA DE LA OTRA OBRA",
                          modelo="x", prompt_hash="h")
    repo.guardar_borrador(con, "otra-e1", texto="TEXTO DE LA OTRA OBRA",
                          modelo="x", prompt_hash="h")

    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    material = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert "OTRA OBRA" not in material["escena_anterior"]
    assert material["escena_anterior"], "y si trae la de su propia obra"


def test_la_escena_anterior_no_cruza_el_corte_de_capitulo(con):
    """El alcance de la escena anterior es el **capitulo**, no la obra.

    Los resumenes si cruzan el corte -una novela no olvida el capitulo uno al
    empezar el dos- pero la escena anterior no: **eso es exactamente lo que un
    corte de capitulo significa**. Son dos bloques con dos alcances distintos,
    y tratarlos igual es lo que hace que un solo filtro no sirva para los dos.
    """
    repo.guardar_escaleta(con, "cap-1", [
        {"id": "c2-e1", "orden": 4, "capitulo": "cap-2", "pov": "per-marta",
         "lugar": "lug-salon", "beats": ["b"], "longitud_objetivo": [10, 5000],
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"}},
        {"id": "c2-e2", "orden": 5, "capitulo": "cap-2", "pov": "per-marta",
         "lugar": "lug-salon", "beats": ["b"], "longitud_objetivo": [10, 5000],
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"}}])
    with con:
        con.execute("UPDATE escena SET capitulo='cap-1' WHERE id IN ('e1','e2','e3')")
    # Dos borradores, para que el `ORDER BY version DESC` elija de verdad y no
    # gane nadie por el azar del rowid.
    for texto in ("primera", "ULTIMA DEL CAPITULO UNO"):
        repo.guardar_borrador(con, "e3", texto=texto, modelo="x", prompt_hash="h")

    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    material = obra.reunir_material(con, repo.escena(con, "c2-e1"), "cap-1")
    assert "CAPITULO UNO" not in material["escena_anterior"], (
        "la primera escena de un capitulo no continua desde el anterior")


def test_dentro_del_capitulo_la_escena_anterior_si_llega(con):
    """El caso positivo: sin el, un filtro que devolviera siempre vacio pasaria
    la prueba de arriba sin hacer nada."""
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    material = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert material["escena_anterior"], "dentro del capitulo si continua"


def test_la_primera_escena_de_un_capitulo_no_es_lo_mismo_que_una_sin_anterior(con):
    """Regla 8 aplicada al corte de capitulo, y lo aviso la sesion de SPEC-21.

    Que la escena 1 de un capitulo reciba vacio **es correcto**: eso es lo que
    un corte significa. Que la escena 4 lo reciba es un fallo. Si las dos
    producen la misma cadena vacia, la segunda no la ve nadie.
    """
    with con:
        con.execute("UPDATE escena SET capitulo='cap-1'")
    repo.asignar_t_discurso(con, "cap-1", {"cap-1": 1, "cap-2": 2})
    primera = obra.reunir_material(con, repo.escena(con, "e1"), "cap-1")
    assert primera["escena_anterior"] == ""
    assert primera["falta_escena_anterior"] is False, "la 1 no tiene anterior y esta bien"

    cuarta = obra.reunir_material(con, repo.escena(con, "e2"), "cap-1")
    assert cuarta["escena_anterior"] == ""
    assert cuarta["falta_escena_anterior"] is True, "la 2 deberia tenerla y no esta"


def test_el_capitulo_dos_arranca_con_la_memoria_del_capitulo_uno(con):
    """`F-45` de punta a punta, que es donde importa.

    Es el defecto que mas de cerca toca lo que el proyecto existe para hacer:
    una novela que **olvida el capitulo uno al empezar el dos**. Con `orden`
    -local al capitulo- la escena 1 del capitulo dos preguntaba por «lo anterior
    a 1» y recibia cero resumenes. Con `t_discurso`, que numera la obra entera,
    recibe los del capitulo anterior.

    Y la otra mitad de la decision sigue en pie: la escena anterior **no** cruza
    el corte, porque eso es lo que un corte de capitulo significa. Son dos
    alcances distintos sobre el mismo material.
    """
    # Los capitulos registrados, que es lo que tiene una obra de verdad. Sin
    # ellos `generar_obra` **se para en vez de adivinar** el orden de lectura:
    # colocar los capitulos a ojo seria inventarse el orden de una novela.
    from app.features.brief import repository as brief
    brief.asegurar_tablas(con)
    with con:
        con.execute("UPDATE escena SET capitulo='cap-1'")
        con.execute("INSERT INTO obra (id, titulo, premisa) VALUES ('cap-1', 't', 'p')")
        for id_cap, orden in (("cap-1", 1), ("cap-2", 2)):
            con.execute("INSERT INTO capitulo (id, obra, orden) VALUES (?, ?, ?)",
                        (id_cap, "cap-1", orden))
    repo.guardar_escaleta(con, "cap-1", [
        {"id": "c2-e1", "orden": 1, "capitulo": "cap-2", "pov": "per-marta",
         "lugar": "lug-salon", "beats": ["b"], "longitud_objetivo": [10, 5000],
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"}}])
    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=2)

    material = obra.reunir_material(con, repo.escena(con, "c2-e1"), "cap-1")
    assert material["resumenes"], (
        "la primera escena del capitulo dos arranca sin memoria del uno")
    assert not material["escena_anterior"], (
        "pero la escena anterior si se queda en su capitulo")


def test_las_trazas_de_la_obra_sobreviven_al_proceso(con):
    """`F-49`: la traza se construia en memoria y **nadie la escribia**, asi
    que la contencion de `PC-9` -saber que bloques quedaron fuera cuando un
    agente inventa- solo valia dentro de la misma ejecucion. Y el diagnostico
    siempre se hace despues."""
    from app.features.observabilidad import repository as obs

    obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000, hasta=1)
    trazas = obs.trazas_de(con, "e1")
    assert {t["agente"] for t in trazas} == {"escritor", "juez", "resumidor"}, (
        "las tres delegaciones del ciclo, no solo la del Escritor")


def test_generar_un_capitulo_dentro_de_una_obra_no_toca_los_demas(con):
    """Una obra con diez capitulos, no diez obras.

    El guion de la obra larga generaba **una obra por capitulo**, y con eso nada
    de lo construido significaba nada: `escena.capitulo` no tenia a que apuntar,
    el cierre de capitulo evaluaba una obra entera, la cronologia no cruzaba
    ningun corte y los hechos de los diez capitulos colisionaban en la misma
    clave (`F-39`).

    Con una sola obra hace falta poder generar **capitulo a capitulo**, que es
    lo que permite reintentar uno sin tocar los demas.
    """
    from app.features.brief import repository as brief
    brief.asegurar_tablas(con)
    with con:
        con.execute("UPDATE escena SET capitulo='cap-1'")
        con.execute("INSERT INTO obra (id, titulo, premisa) VALUES ('cap-1','t','p')")
        for id_cap, orden in (("cap-1", 1), ("cap-2", 2)):
            con.execute("INSERT INTO capitulo (id, obra, orden) VALUES (?, ?, ?)",
                        (id_cap, "cap-1", orden))
    repo.guardar_escaleta(con, "cap-1", [
        {"id": "c2-e1", "orden": 1, "capitulo": "cap-2", "pov": "per-marta",
         "lugar": "lug-salon", "beats": ["b"], "longitud_objetivo": [10, 5000],
         "cambio_de_valor": {"eje": "cordura", "signo": "negativo"}}])

    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000,
                          capitulo="cap-2")
    assert g.escenas_hechas == ["c2-e1"], (
        "generar el capitulo dos ha tocado escenas de otro capitulo")
    assert repo.escena(con, "e1")["estado"] == "planificada"


def test_cerrar_un_capitulo_no_mira_el_orden_temporal_de_los_demas(con):
    """El patron que predijo la sesion de frontend: una consulta que recibe un
    capitulo y filtra por obra **pasa mientras los dos identificadores
    coincidan**. `evaluar_cierre` filtraba las escenas por capitulo y pedia el
    orden temporal de la obra entera, asi que una inversion en el capitulo
    siete habria impedido cerrar el tres.

    Dos capitulos, por la Regla 9: con uno solo, la consulta equivocada sigue
    devolviendo lo correcto.
    """
    inversiones = {"inversiones": [("ev-c7-a", "ev-c7-b")], "sin_fecha_legible": []}
    de_otro = obra.inversiones_del_capitulo(inversiones, {"ev-c7-a": "cap-7",
                                                          "ev-c7-b": "cap-7"},
                                            "cap-3")
    assert de_otro["inversiones"] == [], "las del siete no bloquean el tres"

    del_mismo = obra.inversiones_del_capitulo(inversiones, {"ev-c7-a": "cap-7",
                                                            "ev-c7-b": "cap-7"},
                                              "cap-7")
    assert del_mismo["inversiones"] == [("ev-c7-a", "ev-c7-b")]


def test_una_inversion_que_cruza_dos_capitulos_bloquea_el_posterior(con):
    """Si el tiempo retrocede al pasar del capitulo tres al cuatro, el defecto
    es del cuatro: es donde el lector lo encuentra."""
    inv = {"inversiones": [("ev-c3", "ev-c4")], "sin_fecha_legible": []}
    caps = {"ev-c3": "cap-3", "ev-c4": "cap-4"}
    assert obra.inversiones_del_capitulo(inv, caps, "cap-4")["inversiones"]
    assert not obra.inversiones_del_capitulo(inv, caps, "cap-3")["inversiones"]


def test_sin_capitulo_se_mira_la_obra_entera(con):
    """Cerrar la obra si pregunta por todo, que es otra pregunta."""
    inv = {"inversiones": [("a", "b")], "sin_fecha_legible": []}
    assert obra.inversiones_del_capitulo(inv, {}, None) is inv


# --- `SPEC-26` `RF-20`: lo que no aplica se dice ----------------------------


def test_el_informe_dice_que_invariantes_estan_obsoletas(con):
    """`SPEC-26` v3 `RF-20`: lo retirado se dice, no se calla."""
    g = obra.generar_obra(con, "cap-1", *_agentes(), techo=1_000_000,
                          genero="aventura")
    assert "obsoletas: INV-10, INV-11, INV-12, INV-16" in obra.informe(g)



# --- `SPEC-30` v4 `RF-11`: la rendicion sobrevive a la consolidacion -------------

def _consolidada(con, escena):
    return con.execute("SELECT 1 FROM escena_consolidada WHERE escena = ?",
                       (escena,)).fetchone() is not None


def test_una_escena_rendida_sigue_rendida_despues_de_consolidar(con):
    """El estado dice que se rindio; que esta consolidada lo dice
    `escena_consolidada`. Son dos preguntas distintas y ya no se pisan."""
    obra.generar_obra(con, "cap-1", SiempreCorto(), *_agentes()[1:],
                      techo=1_000_000, hasta=1, tope_intentos=3)
    assert repo.escena(con, "e1")["estado"] == "aceptada_por_rendicion"
    assert _consolidada(con, "e1"), "el delta esta aplicado igual"


def test_una_escena_limpia_queda_consolidada(con):
    obra.generar_obra(con, "cap-1", DobleDelModelo(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert repo.escena(con, "e1")["estado"] == "consolidada"
    assert _consolidada(con, "e1")


def test_relanzar_salta_una_escena_rendida_y_consolidada(con):
    obra.generar_obra(con, "cap-1", SiempreCorto(), *_agentes()[1:],
                      techo=1_000_000, hasta=1, tope_intentos=3)
    escritor = SiempreCorto()
    obra.generar_obra(con, "cap-1", escritor, *_agentes()[1:],
                      techo=1_000_000, hasta=1, tope_intentos=3)
    assert escritor.llamadas == [], "no se reescribe lo que ya esta hecho"
    assert repo.escena(con, "e1")["estado"] == "aceptada_por_rendicion"


# --- `SPEC-30` v4 `RF-10` (`C-1`): reescribir a delta fijo ------------------------

from app.features.consolidacion import deltas as deltas_de_escena  # noqa: E402

EDITOR_BIEN = Devuelve({"valoraciones": [
    {"criterio": c, "nota": 4, "justificacion": "bien"} for c in
    ("continuidad", "tono", "arco", "coherencia_de_personajes", "ritmo", "personalizacion")]})


class Reescribe:
    """Devuelve otro texto con el delta que se le diga."""

    nombre = "doble-reescritura"

    def __init__(self, texto, delta):
        self.texto, self.delta, self.llamadas = texto, delta, []

    def llamar(self, prompt):
        self.llamadas.append(prompt)
        return {"texto": self.texto, "pov_usado": "per-marta", "delta": self.delta,
                "usage": {"total_tokens": 100}}


def _consolidada_e1(con):
    obra.generar_obra(con, "cap-1", DobleDelModelo(), *_agentes()[1:],
                      techo=1_000_000, hasta=1)
    assert repo.escena(con, "e1")["estado"] == "consolidada"
    return deltas_de_escena.ultimo(con, "e1")["delta"]


def _reescribir(con, escritor, **kw):
    return obra.reescribir_capitulo(con, "cap-1", "e1", escritor, EDITOR_BIEN,
                                    _agentes()[2], instrucciones=["cierra la puerta"],
                                    techo=1_000_000, **kw)


def test_reescribir_no_aplica_el_delta_otra_vez(con):
    delta = _consolidada_e1(con)
    r = _reescribir(con, Reescribe("Marta cierra la puerta del salon despacio y escucha la casa entera respirar.", delta))
    assert r["aceptada"], r
    assert len(deltas_de_escena.leer(con, "e1")) == 1, "el canon no se mueve"
    assert con.execute("SELECT COUNT(*) FROM escena_consolidada WHERE escena='e1'"
                       ).fetchone()[0] == 1


def test_una_reescritura_con_el_mismo_delta_cambia_el_texto_aceptado(con):
    delta = _consolidada_e1(con)
    r = _reescribir(con, Reescribe("Marta cierra la puerta del salon despacio y escucha la casa entera respirar.", delta))
    e = repo.escena(con, "e1")
    assert e["borrador_aceptado"] == r["version"] and e["estado"] == "consolidada"
    assert obra._texto_elegido(con, e) == "Marta cierra la puerta del salon despacio y escucha la casa entera respirar."


def test_la_instruccion_del_editor_llega_al_escritor(con):
    delta = _consolidada_e1(con)
    escritor = Reescribe("Marta cierra la puerta del salon despacio y escucha la casa entera respirar.", delta)
    _reescribir(con, escritor)
    assert "cierra la puerta" in escritor.llamadas[0]


def test_una_reescritura_que_cambia_el_delta_se_rechaza(con):
    """`C-1`: solo se acepta si los hechos no cambian. Un delta distinto no es una
    correccion local, y aceptarlo moveria el canon debajo de lo ya escrito."""
    delta = _consolidada_e1(con)
    texto_antes = obra._texto_elegido(con, repo.escena(con, "e1"))
    otro = dict(delta, cambio_de_valor={"eje": "cordura", "signo": "positivo"})
    r = _reescribir(con, Reescribe("Marta sale del salon aliviada y deja atras el sotano y su silencio.", otro))
    assert not r["aceptada"] and "el delta cambio" in r["motivo"]
    e = repo.escena(con, "e1")
    # Si la escena no tenia `borrador_aceptado`, el texto elegido es el ultimo: el
    # borrador rechazado se habria convertido en el texto de la novela sin que nadie
    # lo aceptara. Tambien el estado: guardar un borrador degradaba a `generada`.
    assert obra._texto_elegido(con, e) == texto_antes
    assert e["estado"] == "consolidada"


def test_una_reescritura_con_una_vetada_no_se_acepta(con):
    delta = _consolidada_e1(con)
    texto_antes = obra._texto_elegido(con, repo.escena(con, "e1"))
    r = _reescribir(con, Reescribe("Marta cierra la puerta del hospital y se queda quieta en el pasillo largo.", delta),
                    vetadas=["hospital"])
    assert not r["aceptada"]
    assert obra._texto_elegido(con, repo.escena(con, "e1")) == texto_antes
