"""El bucle de escenas: la unica pieza que las encadena.

Reune el material de cada escena, lo monta, ejecuta su ciclo y pasa a la
siguiente. **Solo si la anterior esta consolidada** (`INV-05`): hasta que el
delta no esta aplicado, el estado del mundo no ha cambiado y la escena
siguiente generaria contra un mundo que ya no es.

POR QUE EL MATERIAL LO REUNE ESTE MODULO
------------------------------------------
Porque es el unico autorizado a componer (`A-02`). `features/contexto/` monta
los bloques pero **no va a buscarlos**: no importa `consolidacion/` ni
`escaleta/`. Reunir es acoplar, y acoplar es cosa de `orquestacion/`.

En `F3` se aprendio que el acoplamiento tambien viaja por SQL sin que ningun
`import` lo delate (`F-28`), asi que aqui se hace explicito: este modulo lee de
las dos features y les pasa el resultado a la tercera.

QUE PASA CUANDO UNA `bloqueante` DETIENE LA OBRA
--------------------------------------------------
Se para. No se rinde y no se salta: rendirse ante `INV-03` meteria un hecho
falso en el registro de conocimiento y **todas las escenas siguientes se
generarian encima**. Con sesenta escenas eso es peor, no mejor.

Lo que si se hace es **dejar el dato**: en que escena paro, que invariante y
con que descripcion. Con que frecuencia `INV-03` bloquea una generacion larga
no se sabe (`VER-64`), y una parada en la tercera escena **no es un fracaso: es
la medida**.
"""

import json
import sqlite3
from dataclasses import dataclass, field

from app.commons import config
from app.commons.dominio.enumeraciones import EstadoDeEscena as EE
from app.commons.dominio.enumeraciones import TipoDeDecisionDePolitica as TD
from app.commons.dominio.enumeraciones import OrigenDeUso, TipoDeUsoDeHecho
from app.commons.invariantes import registro
from app.commons.politica.personalizacion import claves_ausentes
from app.features.auditoria import capitulo as puerta_capitulo
from app.features.cronologia import consultas

# Una escena en estos estados ya paso por todo: su delta esta aplicado y su
# texto elegido. Son los mismos que `auditoria/` llama `COMPLETAS` para decidir
# si un capitulo puede cerrarse, y por el mismo motivo.
YA_HECHAS = {EE.CONSOLIDADA, EE.ACEPTADA_POR_RENDICION}
from app.features.consolidacion import memoria, mundo as modulo_mundo
from app.features.cronologia import extraccion
from app.features.cronologia import repository as cronologia
from app.features.contexto import ensamblado, recorte
from app.features.escaleta import repository as repo
from app.features.orquestacion import ciclo, rendicion
from app.commons.politica import auditoria
from app.features.politica import repository as politica
from app.commons.politica.vetadas import coincidencias


@dataclass
class Generacion:
    escenas_hechas: list = field(default_factory=list)
    parada: dict | None = None
    medidas: list = field(default_factory=list)
    rendidas: list = field(default_factory=list)
    delegaciones: int = 0
    cierre: dict | None = None
    saltadas: list = field(default_factory=list)
    sin_resumen: list = field(default_factory=list)
    trazas_no_guardadas: list = field(default_factory=list)
    # `False` no es "sin vetadas encontradas": es que nadie las busco porque no
    # se dio ninguna lista. El informe lo dice, porque un dato ausente no es
    # un verde.
    vetadas_comprobadas: bool = False
    genero: str | None = None
    coste: dict = field(default_factory=lambda: {
        "usd": 0.0, "delegaciones": 0, "sin_coste": 0})

    @property
    def llego_al_final(self):
        return self.parada is None


def _orden_de_capitulos(con, obra):
    """`{id_capitulo: posicion}` segun `brief/`, o vacio si no consta.

    Vacio no es un problema cuando la obra tiene un solo capitulo: entonces el
    orden de lectura **es** el `orden` de la escena y no hay nada que declarar.
    Con varios y sin este dato, las escenas se quedan sin situar y
    `asignar_t_discurso` lo dice en vez de colocarlas a ojo.
    """
    try:
        filas = con.execute(
            "SELECT id, orden FROM capitulo WHERE obra = ? ORDER BY orden", (obra,))
        return {f[0]: f[1] for f in filas}
    except sqlite3.OperationalError:
        # La tabla la crea `brief/` cuando se da de alta una obra. Si no existe,
        # es que nadie la dio de alta por esa via.
        return {}


def reunir_material(con, escena, obra_id, inmutable=""):
    """Lo que hay disponible para montar el contexto de esta escena."""
    orden = escena["orden"]
    t_discurso = escena.get("t_discurso")
    if t_discurso is None:
        raise memoria.SinPosicionEnElDiscurso(
            "la escena {0} no tiene `t_discurso`, asi que no se puede saber que "
            "resumenes van antes que ella. Arreglo: `asignar_t_discurso` antes "
            "de reunir material".format(escena["id"]))
    # Acotada a la obra, como los resumenes y las fichas (`F-40`). Esta era la
    # que quedaba fuera, y es **el bloque que mas pesa del contexto**: el
    # bloque Local, que lleva la escena anterior entera. Sin el filtro,
    # `orden - 1` casaba con una escena de cada obra y `LIMIT 1` se quedaba con
    # la que saliera — el Escritor arrancaba leyendo una escena de otra obra y
    # **nadie lo notaba, porque llega texto plausible**. Peor que lo de los
    # resumenes, que llegaban desordenados o vacios.
    # **El alcance de la escena anterior es el capitulo, no la obra.** Los
    # resumenes si cruzan el corte -una novela no olvida el capitulo uno al
    # empezar el dos- pero esta no: eso es exactamente lo que un corte de
    # capitulo significa. Dos alcances distintos, y un solo filtro no sirve
    # para los dos.
    #
    # `IS` y no `=` porque compara bien contra NULL: una escaleta anterior a
    # `SPEC-21` no trae capitulo, y entonces todas las de la obra caen en el
    # mismo grupo, que es el comportamiento que habia.
    anterior = con.execute(
        "SELECT b.texto FROM borrador b JOIN escena e ON e.id = b.escena "
        "WHERE e.orden = ? AND e.obra = ? AND e.capitulo IS ? "
        "ORDER BY b.version DESC LIMIT 1",
        (orden - 1, obra_id, escena.get("capitulo"))).fetchone()
    return {
        # Acotados a la obra: el `orden` va del 1 al N **dentro** de ella, asi
        # que sin el filtro dos obras en la misma base se mezclan (`F-40`).
        # `F-45`: por `t_discurso` y no por `orden`. El `orden` es local al
        # capitulo, asi que la escena 1 del capitulo dos preguntaba por "lo
        # anterior a 1" y recibia cero: arrancaba sin memoria de todo lo
        # anterior. Los resumenes **tienen** que cruzar el corte de capitulo;
        # la escena anterior no. Son dos alcances distintos y por eso no puede
        # servir el mismo campo para los dos.
        "resumenes": memoria.resumenes_hasta(con, t_discurso, obra=obra_id),
        "fichas": memoria.fichas_en(con, t_discurso, obra=obra_id),
        "escena_anterior": anterior[0] if anterior else "",
        # Vacio legitimo y vacio por fallo **no pueden verse igual** (Regla 8).
        # Que la escena 1 de un capitulo no tenga anterior es lo correcto; que
        # no la tenga la 4 es un defecto, y con la misma cadena vacia nadie lo
        # veria.
        "falta_escena_anterior": orden > 1 and anterior is None,
        "mundo": modulo_mundo.leer(con),
        "problemas": repo.hallazgos_abiertos(con, escena["id"]),
        "hechos": repo.hechos_declarados(con, obra_id),
        "inmutable": inmutable,
    }


def generar_obra(con, obra, escritor, juez, resumidor, inmutable="",
                 techo=100_000, hasta=None, tope_intentos=None,
                 tope_delegaciones=None, instrucciones=None, capitulo=None,
                 vetadas=None, tope_vetadas=None, genero=None, nombres=None,
                 imprescindibles=None, editor=False):
    """Genera las escenas en orden. Se detiene en la primera `bloqueante`.

    Cada escena tiene hasta `tope_intentos` (`TOPE_INTENTOS_ESCENA`), y los
    problemas de un intento entran en el prompt del siguiente: si no, el
    escritor no sabe nada del fallo y vuelve a cometerlo, que es lo que le pasó
    a la otra rama con el aviso de longitud.

    Y la obra entera tiene `tope_delegaciones` (`TOPE_DELEGACIONES_OBRA`), que
    **acota el gasto y no el error**.
    """
    tope_intentos = tope_intentos or config.TOPE_INTENTOS_ESCENA
    tope_delegaciones = tope_delegaciones or config.TOPE_DELEGACIONES_OBRA
    # `is None` y no `or`: un tope de 0 reescrituras es un valor legitimo (parar
    # a la primera) y `or` lo convertiria en el de por defecto.
    tope_vetadas = (config.TOPE_REESCRITURAS_POR_VETADA if tope_vetadas is None
                    else tope_vetadas)
    # Las tablas del acta se aseguran **aqui y no al levantarla**: crearlas
    # abre su propia transaccion, y el acta corre dentro de la del delta.
    # Anidar transacciones en SQLite hace commit del bloque interno, que es
    # justo la atomicidad que `SPEC-21` C-4 existe para sostener.
    cronologia.asegurar_tablas(con)
    # `F-45`: sin esto la memoria no se puede ordenar a lo largo de la obra.
    # El orden de los capitulos sale de `brief/`, que es otra feature: se lee
    # aqui porque componer entre features es de `orquestacion/` (`A-02`), y se
    # le pasa a `escaleta/` como valor.
    repo.asignar_t_discurso(con, obra, _orden_de_capitulos(con, obra))
    g = Generacion(vetadas_comprobadas=bool(vetadas), genero=genero)
    if vetadas:
        politica.asegurar_tablas(con)
    # Una obra son **diez capitulos, no diez obras**. Generar de capitulo en
    # capitulo es lo que permite reintentar uno sin tocar los demas, que es como
    # el guion de la obra larga se desatasca. Sin `capitulo` se genera la obra
    # entera, que es lo que quiere una ejecucion de un tiron.
    escenas = (repo.escenas_de_capitulo(con, capitulo) if capitulo
               else repo.escenas_de(con, obra))
    for escena in escenas:
        if hasta is not None and escena["orden"] > hasta:
            break

        # `F-38`: lo que ya esta hecho **no se vuelve a hacer**. Antes el bucle
        # recorria desde el principio sin mirar el estado, asi que relanzar
        # tras una parada regeneraba las escenas consolidadas, pagaba su
        # delegacion, les guardaba otro borrador y **las degradaba a
        # `generada`** antes de morir con `YaConsolidada`. Cada parada devolvia
        # al principio y estropeaba lo que iba bien.
        if EE(escena["estado"]) in YA_HECHAS:
            g.saltadas.append(escena["id"])
            continue

        if not rendicion.queda_presupuesto(g.delegaciones, tope_delegaciones):
            g.parada = {"escena": escena["id"], "motivo": "tope_delegaciones",
                        "delegaciones": g.delegaciones,
                        "detalle": "acota el gasto, no el error: lo decide una "
                                   "persona y no un bucle"}
            return g

        material = reunir_material(con, escena, obra, inmutable)
        bloques = ensamblado.montar(material)
        tamanos = ensamblado.tamanos(bloques)

        try:
            plan = recorte.planificar(tamanos, techo=techo)
        except recorte.NoCabe as e:
            g.parada = {"escena": escena["id"], "motivo": "no_cabe",
                        "detalle": "RF-26: agotadas las formas reducidas"}
            g.medidas.append(_medida(escena, tamanos, e.plan))
            return g
        g.medidas.append(_medida(escena, tamanos, plan))
        # `F-58`: lo que llega al Escritor es el **texto** de los bloques, ya
        # recortado. Antes llegaban los tamanos, en todas las escenas: el bloque
        # inmutable era `66` en vez de la premisa. `aplicar_recorte` existia y
        # nadie la llamaba.
        textos = ensamblado.aplicar_recorte(bloques, plan)

        c, intentos = _intentar(con, escena, tamanos, escritor, juez, resumidor,
                                material, obra, techo, tope_intentos, g,
                                instrucciones, vetadas=vetadas,
                                tope_vetadas=tope_vetadas, nombres=nombres,
                                imprescindibles=(imprescindibles or {}).get(escena["id"]),
                                es_editor=editor, textos=textos)

        if c.fallo:
            g.parada = {"escena": escena["id"], "motivo": c.fallo,
                        "intentos": len(intentos),
                        "hallazgos": [(h.invariante, h.descripcion)
                                      for h in (c.generacion.hallazgos
                                                if c.generacion else [])]}
            return g

        if c.generacion.hallazgos:
            # Se agotaron los intentos y lo que queda no corrompe el canon:
            # `RF-24`. La escena pasa a `aceptada_por_rendicion` y **no** a
            # `aceptada`, para que quien lea el manuscrito pueda distinguirlas.
            version = rendicion.menos_malo([(v, h) for v, h, _ in intentos])
            elegido = next(c2 for v, _, c2 in intentos if v == version)
            repo.rendir_escena(con, escena["id"], version)
            texto_rendido = ciclo.texto_de(con, escena["id"], version)
            c = ciclo.consolidar_y_resumir(
                elegido, con, escena["id"], texto_rendido, resumidor,
                "obra-{0}-rendicion".format(escena["orden"]),
                # Una escena rendida **entra igual al canon**, asi que su acta
                # se levanta igual. Olvidarla aqui dejaria sin registrar los
                # usos justo de las escenas que mas falta hace poder revisar.
                al_consolidar=ciclo._acta_de(
                    _acta_de_la_escena(escena, obra, material["hechos"]),
                    texto_rendido, elegido))
            g.rendidas.append((escena["id"], version, len(intentos)))
            if c.fallo:
                g.parada = {"escena": escena["id"], "motivo": c.fallo,
                            "intentos": len(intentos), "hallazgos": []}
                return g

        if c.resumen:
            memoria.guardar_resumen(
                con, escena["id"], escena["t_discurso"],
                str(c.resumen.get("texto") or ""),
                [h for h in (c.resumen.get("hechos_clave") or [])
                 if memoria.IDENTIFICADOR.match(str(h))],
                obra=obra)
        else:
            # `F-41`: el Resumidor no contesto y la escena se quedaba **sin
            # memoria** sin que nadie lo dijera. Un dato ausente no es un
            # verde: las escenas siguientes leen un contexto al que le falta
            # esta, y desde fuera eso es indistinguible de una escena que no
            # tenia nada que resumir.
            g.sin_resumen.append(escena["id"])
        _registrar_imprescindibles(con, escena, (imprescindibles or {}).get(escena["id"]))
        _marcar_establecidos(con, escena, c, obra)
        _actualizar_fichas(con, escena, c, obra)
        g.escenas_hechas.append(escena["id"])

    g.cierre = evaluar_cierre(con, obra, capitulo, vetadas=vetadas)
    return g


def escenas_que_usan(con, clase, objeto):
    """Las escenas **consolidadas** que dependen de un objeto (`SPEC-20` C-3).

    Vive aqui y no en `edicion/` porque cruza las tablas de `escaleta` y de
    `consolidacion`, y `A-02` deja componer solo a `orquestacion/`. La primera
    version lo hacia dentro de `edicion/` con SQL directo, que es `A-02` roto
    por la via que ningun comprobador de importaciones ve (`F-28`, `PC-18`).

    Es una consulta y no un juicio: devuelve **quien** lo usa, no un si o un
    no. Un "no se puede" sin decir quien lo impide obliga a buscarlo a mano.
    """
    completas = tuple(e.value for e in YA_HECHAS)
    if clase == "escena":
        fila = con.execute("SELECT estado FROM escena WHERE id = ?",
                           (objeto,)).fetchone()
        return [objeto] if fila and fila[0] in completas else []
    if clase == "hecho":
        filas = con.execute(
            "SELECT DISTINCT c.desde_escena FROM conocimiento c "
            "JOIN escena e ON e.id = c.desde_escena "
            "WHERE c.hecho = ? AND e.estado IN (?, ?) "
            "ORDER BY c.desde_escena", (objeto,) + completas)
        return [f[0] for f in filas if f[0]]
    return []


def inversiones_del_capitulo(temporal, capitulo_de_cada_evento, capitulo):
    """Deja solo las inversiones que **este** capitulo tiene que responder.

    `orden_temporal` mira la obra entera, que es lo correcto para lo que hace.
    Pero `INV-08` es de **nivel capitulo**, asi que evaluarla al cerrar el tres
    con las inversiones del siete impediria firmar un capitulo por un defecto
    que no esta en el.

    Hoy no se notaba porque el guion creaba una obra por capitulo y los dos
    identificadores coincidian: **pasaba por accidente**. Lo predijo la sesion
    de frontend al arreglar el mismo patron en el endpoint de cierre, y su
    apuesta era que la coincidencia tapaba mas de un sitio. Tapaba este.

    Una inversion que **cruza** dos capitulos se le imputa al posterior: es
    donde el lector la encuentra, porque es al llegar ahi cuando el tiempo
    retrocede.
    """
    if not capitulo or not temporal:
        return temporal
    del_capitulo = [
        (a, b) for a, b in temporal.get("inversiones") or []
        if capitulo_de_cada_evento.get(b) == capitulo
    ]
    return dict(temporal, inversiones=del_capitulo)


def evaluar_cierre(con, obra, capitulo=None, vetadas=None):
    """Dice si el capitulo **podria** cerrarse. No lo cierra.

    La firma es humana y la dispara el cliente de la API, nunca el worker
    (`Docs/architecture.md`): al decidir que un `mayor` no detiene la escena, el
    control no desaparecio, **se movio aqui**, que es donde una persona puede
    juzgar si el conjunto se sostiene. Un bucle que firmara solo devolveria ese
    control a la maquina y dejaria la puerta de adorno.

    Lo que si hace el bucle es dejar el veredicto preparado, porque tener que
    ir a buscarlo a mano es la forma mas facil de no mirarlo nunca.
    """
    # La puerta es **de capitulo**: evaluarla sobre la obra entera preguntaria
    # si se puede firmar la novela, que es otra pregunta y siempre diria que no
    # mientras quede un capitulo por escribir.
    escenas = (repo.escenas_de_capitulo(con, capitulo) if capitulo
               else repo.escenas_de(con, obra))
    estados = [EE(e["estado"]) for e in escenas]
    # `INV-21`, segunda linea: cada escena ya se comprobo antes de consolidarse,
    # pero un texto puede llegar por otro camino -una edicion a mano- y el
    # capitulo es lo que no puede aceptarse con una vetada (`SPEC-25` `RF-18`).
    if vetadas:
        con_vetada = sorted({e["id"] for e in escenas
                             if coincidencias(_texto_elegido(con, e) or "", vetadas)})
        if con_vetada:
            return {"puede_cerrarse": False, "firmado": False,
                    "motivo": "hay palabras vetadas en {0} [INV-21]".format(
                        ", ".join(con_vetada))}
    hallazgos = [dict(h, severidad=h["severidad"], estado=h["estado"])
                 for e in escenas for h in repo.hallazgos_abiertos(con, e["id"])]
    # `INV-08` es de nivel capitulo y su dato vive en `cronologia/`, que
    # `auditoria/` no puede importar (`A-02`). Componer es de aqui, asi que el
    # orden temporal se consulta aqui y se le pasa ya resuelto (`F-47`).
    try:
        temporal = inversiones_del_capitulo(
            consultas.orden_temporal(con, obra),
            {e["id"]: e.get("capitulo")
             for e in consultas.repo.eventos_de(con, obra)},
            capitulo)
    except Exception:
        # La cronologia puede no estar poblada en una obra que no la use. Que
        # falte el dato no es lo mismo que estar en orden, pero tampoco puede
        # tumbar el cierre por un error de infraestructura: se pasa `None`, que
        # es "no se consulto", y la puerta no afirma nada sobre `INV-08`.
        temporal = None
    try:
        cierre = puerta_capitulo.cerrar(estados, hallazgos, orden_temporal=temporal)
    except puerta_capitulo.NoSePuedeCerrar as e:
        detalle = "; ".join(sorted({h["invariante"] for h in hallazgos})) or ""
        return {"puede_cerrarse": False, "firmado": False,
                "motivo": "{0} [{1}]".format(e, detalle)}
    return {"puede_cerrarse": True, "firmado": False,
            "menores_que_se_dejan_pasar": cierre.menores_que_se_dejan_pasar}


def _intentar(con, escena, tamanos, escritor, juez, resumidor, material, obra_id,
              techo, tope, g, instrucciones=None, vetadas=None, tope_vetadas=0,
              nombres=None, imprescindibles=None, es_editor=False, textos=None):
    """Hasta `tope` intentos, y los problemas de uno entran en el siguiente.

    Se para en cuanto sale limpia, y **tambien en cuanto una `bloqueante`
    aparece**: reintentar ante una `bloqueante` no es mas seguro, es mas caro.
    Lo que no se puede rendir tampoco se puede arreglar insistiendo, porque el
    modelo no sabe cual de las quince reglas ha roto — solo lo que le digamos.

    **La excepcion es `INV-21`** (`SPEC-25` `RF-18`): una palabra vetada si se
    arregla insistiendo, porque aqui si se le dice al modelo exactamente que
    escribio. Tiene su propio contador, `tope_vetadas`, que no gasta `tope`: si
    compartieran contador, una escena podria agotar sus intentos en vetadas y
    rendirse con un problema de calidad que nadie llego a mirar. Y una version
    con una vetada **nunca entra en `intentos`**, que es de donde sale la
    rendicion: el menos malo de tres textos con el nombre de una expareja sigue
    llevando el nombre de la expareja.
    """
    intentos = []
    c = None
    numero = 0
    reescrituras = 0
    problemas_de_vetadas = None
    while numero < tope:
        c = ciclo.ejecutar(con, escena["id"], tamanos, escritor, juez, resumidor,
                           material["mundo"], techo=techo,
                           trabajo="obra-{0}-i{1}-r{2}".format(
                               escena["orden"], numero + 1, reescrituras),
                           hechos=material["hechos"],
                           problemas=problemas_de_vetadas or _problemas_de(intentos),
                           instrucciones=instrucciones,
                           acta=_acta_de_la_escena(escena, obra_id,
                                                   material["hechos"]),
                           vetadas=vetadas, nombres=nombres,
                           imprescindibles=imprescindibles, es_editor=es_editor,
                           textos=textos)
        g.delegaciones += ciclo.coste_total(c.trazas)["delegaciones"]
        # `F-49`: la traza sobrevive al proceso. Es lo que hace que la
        # contencion de `PC-9` -saber que bloques quedaron fuera- valga
        # tambien para el diagnostico de despues, que es cuando se hace.
        g.trazas_no_guardadas.extend(ciclo.guardar_trazas(con, c))
        _acumular_coste(g, c.trazas)
        if c.fallo == "palabra_vetada":
            for co in c.vetadas_encontradas:
                auditoria.registrar_decision(
                    con, TD.COINCIDENCIA_VETADA, obra_id,
                    {"vetada": co.vetada, "fragmento": co.fragmento,
                     "escena": escena["id"], "reescritura": reescrituras})
            if reescrituras >= tope_vetadas:
                auditoria.registrar_decision(
                    con, TD.PARADA_POR_VETADA, obra_id,
                    {"escena": escena["id"], "reescrituras": reescrituras})
                break
            reescrituras += 1
            auditoria.registrar_decision(
                con, TD.REESCRITURA_PEDIDA, obra_id,
                {"escena": escena["id"], "reescritura": reescrituras})
            problemas_de_vetadas = [
                {"invariante": "INV-21",
                 "descripcion": "escribiste «{0}», que no puede aparecer "
                                "(vetada: {1})".format(co.fragmento, co.vetada)}
                for co in c.vetadas_encontradas]
            continue
        if c.fallo == "nombre_mal_escrito":
            # `SPEC-26` `O-2`: el mismo contador y el mismo tope que `INV-21`.
            if reescrituras >= tope_vetadas:
                break
            reescrituras += 1
            problemas_de_vetadas = [
                {"invariante": "INV-22",
                 "descripcion": "escribiste «{0}»: el nombre es «{1}»".format(
                     m.escrito, m.correcto)}
                for m in c.nombres_encontrados]
            continue
        problemas_de_vetadas = None
        if c.generacion is not None and c.generacion.version is not None:
            intentos.append((c.generacion.version, c.generacion.hallazgos, c))
        if c.fallo or not c.generacion.hallazgos:
            break
        numero += 1
    return c, intentos


def _registrar_imprescindibles(con, escena, imprescindibles):
    """`INV-24` lee de aqui: un imprescindible cuyas palabras clave aparecen en el
    texto aceptado **se usa** en esta escena. Lo mide el codigo (`menciona`,
    origen `regla`), no lo declara el modelo."""
    if not imprescindibles:
        return
    texto = _texto_elegido(con, repo.escena(con, escena["id"])) or ""
    cronologia.registrar_usos(con, [
        {"hecho": i["id"], "escena": escena["id"], "capitulo": escena.get("capitulo"),
         "tipo": TipoDeUsoDeHecho.MENCIONA, "origen": OrigenDeUso.REGLA}
        for i in imprescindibles if not claves_ausentes(texto, [i])])


def _texto_elegido(con, escena):
    """El borrador aceptado de la escena, o el ultimo si nadie eligio."""
    if escena.get("borrador_aceptado") is not None:
        fila = con.execute("SELECT texto FROM borrador WHERE escena = ? AND version = ?",
                           (escena["id"], escena["borrador_aceptado"])).fetchone()
        if fila:
            return fila[0]
    fila = con.execute("SELECT texto FROM borrador WHERE escena = ? "
                       "ORDER BY version DESC LIMIT 1", (escena["id"],)).fetchone()
    return fila[0] if fila else None


def _acumular_coste(g, trazas):
    """Lo que se ha pagado, **leido y no deducido**.

    `F-25`: el volumen no predice el coste. El Resumidor gasto 1.872 tokens y
    costo 0,0294 $; el Juez gasto 1.567 y costo 0,0689 — mas del doble con
    menos volumen, porque el precio del modelo pesa mas que la cantidad.

    Las delegaciones que no traen cifra **se cuentan aparte** en vez de sumar
    cero: un cero se lee como un dato y un hueco no.
    """
    for t in trazas:
        if t is None:
            continue
        g.coste["delegaciones"] += 1
        usd = (getattr(t, "medidas", None) or {}).get("coste_usd")
        if usd is None:
            g.coste["sin_coste"] += 1
        else:
            g.coste["usd"] += usd


def _problemas_de(intentos):
    """Lo que fallo en el ultimo intento, en la forma que espera el prompt."""
    if not intentos:
        return None
    return [{"invariante": h.invariante, "descripcion": h.descripcion}
            for h in intentos[-1][1]]


def _acta_de_la_escena(escena, obra_id, hechos):
    """Lo que esta escena deja escrito ademas de su delta (`SPEC-21` C-4).

    ESTO ES LO QUE FALTABA, Y FALTABA ENTERO
    ------------------------------------------
    La tabla de usos de un hecho no estaba a medias: **no la poblaba nadie**.
    `escena_de_establecimiento` decia donde nace un hecho y no habia forma de
    preguntar donde se vuelve a usar, que es lo que necesitan los enlaces de
    una ficha, la regeneracion selectiva, el validador de elementos
    personalizados y el fichero Lean. Las cuatro colgaban del mismo hueco.

    POR QUE COMPONE ESTE MODULO Y NO `cronologia/`
    ------------------------------------------------
    Porque hay que cruzar tres features: la escena y los hechos son de
    `escaleta/`, el delta viene del ciclo y las tablas son de `cronologia/`.
    Cruzar es acoplar y acoplar es de `orquestacion/` (`A-02`). `cronologia/`
    recibe valores y no consulta ninguna tabla ajena.

    Devuelve una funcion `(con, texto, delta)` que se ejecuta **dentro** de la
    transaccion del delta: si el delta no entra, el acta tampoco, porque una
    escena que no ocurrio no puede constar como el capitulo donde algo se usa.
    """
    def _levantar(con, texto, delta):
        usos = extraccion.usos_de_la_escena(
            delta=delta, texto=texto, hechos=hechos,
            escena=escena["id"], capitulo=escena.get("capitulo"))
        if usos:
            cronologia.registrar_usos(con, usos, dentro_de_transaccion=True)

        # La escena sin `t_fabula` no aporta evento, y no se le inventa uno:
        # una cronologia completa y falsa es peor que una incompleta.
        situada = extraccion.evento_de_la_escena(escena, obra_id)
        if situada is not None:
            evento, participantes = situada
            cronologia.registrar_evento(con, evento, participantes,
                                        dentro_de_transaccion=True)

    return _levantar


def _marcar_establecidos(con, escena, c, obra):
    """`SPEC-15`: `escena_de_establecimiento` dice donde lo establece el TEXTO.

    Un hecho que el plan no previo puede establecerse igual, y **se marca**:
    prohibirlo obligaria a replanificar por cada hallazgo del texto, y no
    marcarlo perderia la diferencia entre lo planificado y lo improvisado.
    """
    delta = (c.generacion.leida_delta if c.generacion else None) or {}
    for rev in delta.get("revelaciones", []):
        # La obra acota: el mismo identificador en dos obras son dos hechos
        # (`F-39`), y establecerlo aqui no dice nada de los demas capitulos.
        repo.establecer_hecho(con, rev["hecho"], escena["id"], obra=obra)


def _actualizar_fichas(con, escena, c, obra):
    """Una ficha por entidad que el delta toco. Sin modelo: es un extracto."""
    delta = (c.generacion.leida_delta if c.generacion else None) or {}
    tocadas = {m["personaje"] for m in delta.get("movimientos", [])}
    tocadas |= {r["sujeto"] for r in delta.get("revelaciones", [])}
    if not tocadas:
        return
    m = modulo_mundo.leer(con)
    memoria.actualizar_fichas(con, escena["id"], escena["t_discurso"], obra=obra, entidades={
        e: "en {0}, {1}".format(m["ubicaciones"].get(e, "?"),
                                m["entidades_vivas"].get(e, "?"))
        for e in sorted(tocadas)})


def _medida(escena, tamanos, plan):
    """Lo que la Fase F existe para medir: cuanto ocupa cada bloque y si se
    recorto. El criterio de terminacion no es una prueba verde: es que esto
    crezca."""
    return {"escena": escena["id"], "orden": escena["orden"],
            "total": sum(tamanos.values()), "bloques": dict(tamanos),
            "recortes": [(p.bloque, p.clase.value) for p in plan]}


def informe(g: Generacion) -> str:
    lineas = []
    if g.saltadas:
        # Saltar no es lo mismo que no hacer, y un informe que las omitiera
        # induciria a pensar que faltan escenas.
        lineas.append("ya estaban hechas y se saltaron: {0}".format(
            ", ".join(g.saltadas)))
    lineas.append("escena  total   recortes")
    for m in g.medidas:
        lineas.append("{0:6}  {1:6}  {2}".format(
            m["escena"], m["total"], m["recortes"] or "-"))
    if g.medidas:
        crecio = g.medidas[-1]["total"] > g.medidas[0]["total"]
        lineas.append("el contexto {0}".format("CRECE" if crecio else "NO crece"))
    # `SPEC-26` `RF-20`: lo que no aplica se dice, y lo que no se sabe tambien.
    if g.genero is None:
        lineas.append("genero no declarado: no se sabe si aplican las "
                      "invariantes del plano Terror")
    for inv in registro.no_aplican(g.genero) if g.genero else []:
        lineas.append("{0} no aplica: la obra no es de terror".format(inv))
    if not g.vetadas_comprobadas:
        lineas.append("INV-21 no se comprobo: no se dio ninguna lista de "
                      "palabras vetadas")
    if g.parada:
        lineas.append("PARADA en {0}: {1}".format(
            g.parada["escena"], g.parada["motivo"]))
        for inv, desc in g.parada.get("hallazgos", []):
            lineas.append("   [{0}] {1}".format(inv, desc))
    return "\n".join(lineas)
