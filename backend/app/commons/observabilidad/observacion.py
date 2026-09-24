"""Una traza abierta y las sesiones que la alimentan (`PLAN-29` E3).

`Observacion` es una traza de Langfuse: emite su `TrazaEnviada` al nacer, y despues spans y
scores asociados a ella. `SesionObservada` envuelve cualquier agente —la `SesionDelegada`
real o un doble— y emite un span por llamada **sin guardar el prompt ni la respuesta**: solo
lee `medidas`, que es lo que declara el sobre.

**La observabilidad no puede tumbar una novela** (`RF-09`): si el exportador revienta, la
perdida se guarda con la clase del error y la llamada devuelve lo mismo que habria devuelto.
"""

import contextlib
import time
import uuid

from app.commons.observabilidad import perdidas
from app.commons.observabilidad.envio import (ScoreEnviado, SpanEnviado, TrazaEnviada,
                                              VersionDePrompt, sesion_de)


def _id():
    return uuid.uuid4().hex


class Observacion:
    def __init__(self, exportador, con=None, obra="", nombre="generacion"):
        self.exportador = exportador
        self.con = con
        self.sesion = sesion_de(obra)
        self.traza = _id()
        self.perdidas = 0
        self._padres = []  # los grupos abiertos, del mas externo al mas interno
        # `RF-06`: el catalogo de vetadas de la obra, `{forma: Vetada}`, para enviar una
        # coincidencia por su nivel y su id sin enviar la forma cuando no es global.
        self.vetadas = {}
        self.emitir("traza", TrazaEnviada(id=self.traza, nombre=nombre, sesion=self.sesion))

    def emitir(self, tipo, objeto):
        """Devuelve si salio: quien lleva la cuenta de lo enviado no marca una perdida."""
        try:
            self.exportador.enviar(tipo, objeto)
            return True
        except Exception as e:  # noqa: BLE001 — cualquier fallo del exportador es una perdida
            self.perdidas += 1
            if self.con is not None:
                perdidas.guardar(self.con, self.sesion, tipo, getattr(objeto, "nombre", None)
                                 or getattr(objeto, "rol", None), e)
            return False

    @property
    def padre(self):
        return self._padres[-1]["id"] if self._padres else None

    @property
    def capitulo(self):
        return self._padres[-1]["capitulo"] if self._padres else None

    def span(self, **campos):
        campos.setdefault("id", _id())
        campos.setdefault("padre", self.padre)
        if self.capitulo is not None:
            campos.setdefault("capitulo", self.capitulo)
        s = SpanEnviado(traza=self.traza, **campos)
        if s.tipo == "rol":
            for g in self._padres:
                g["llamadas"].append(s)
        self.emitir("span", s)
        return s.id

    def score(self, **campos):
        if self.capitulo is not None:
            campos.setdefault("capitulo", self.capitulo)
        self.emitir("score", ScoreEnviado(traza=self.traza, **campos))

    def prompt(self, rol, version, plantilla):
        return self.emitir("prompt", VersionDePrompt(rol=rol, version=version,
                                                     plantilla=plantilla))

    @contextlib.contextmanager
    def grupo(self, nombre, capitulo=None):
        """Un span que agrupa —la novela, `planificacion`, un capitulo con su numero,
        `cierre`— y lleva el agregado de las llamadas que cuelgan de el (`RF-03`). Se
        emite al cerrarse, cuando el agregado ya se conoce."""
        g = {"id": _id(), "nombre": nombre, "padre": self.padre,
             "capitulo": capitulo if capitulo is not None else self.capitulo, "llamadas": []}
        self._padres.append(g)
        try:
            yield g["id"]
        finally:
            self._padres.pop()
            self.emitir("span", SpanEnviado(traza=self.traza, id=g["id"], padre=g["padre"],
                                            nombre=nombre, tipo="grupo",
                                            capitulo=g["capitulo"], **agregado(g["llamadas"])))


def _suma(valores):
    medidos = [v for v in valores if v is not None]
    return sum(medidos) if medidos else None


def agregado(llamadas):
    """Tokens y coste de un grupo. **Lo ausente no suma como cero**: sin ninguna llamada
    con coste, el coste va ausente; con alguna sin coste, el total es un suelo y lo dice."""
    salida = {campo: _suma([getattr(l, campo) for l in llamadas])
              for campo in ("tokens_entrada", "tokens_salida", "tokens_cache_creados",
                            "tokens_cache_leidos", "coste_usd")}
    if salida["coste_usd"] is not None:
        salida["coste_es_suelo"] = any(l.coste_usd is None for l in llamadas)
    return salida


_DE_LA_SESION = ("nombre", "agente", "reglas", "entorno", "herramientas")


class SesionObservada:
    """Misma firma que la sesion que envuelve: `llamar(prompt) -> dict`. Lo que leen los
    hooks y las tools (`reglas`, `entorno`, `herramientas`) pasa a la sesion de dentro."""

    def __init__(self, sesion, observacion, rol, version_de_prompt=None):
        object.__setattr__(self, "_sesion", sesion)
        object.__setattr__(self, "_obs", observacion)
        object.__setattr__(self, "rol", rol)
        object.__setattr__(self, "version_de_prompt", version_de_prompt)
        object.__setattr__(self, "ultimo_span", None)

    def __getattr__(self, nombre):
        return getattr(self._sesion, nombre)

    def __setattr__(self, nombre, valor):
        if nombre in _DE_LA_SESION:
            setattr(self._sesion, nombre, valor)
        else:
            object.__setattr__(self, nombre, valor)

    def llamar(self, prompt):
        inicio = time.monotonic()
        try:
            r = self._sesion.llamar(prompt)
        except Exception as e:
            self._emitir(getattr(e, "medidas", None), inicio, "fallo", type(e).__name__)
            raise
        medidas = (r or {}).get("medidas") if isinstance(r, dict) else None
        self._emitir(medidas, inicio, "ok" if r is not None else "fallo",
                     None if r is not None else "RespuestaNula")
        return r

    def _emitir(self, medidas, inicio, resultado, clase):
        m = medidas or {}
        latencia = m.get("duracion_ms")
        if latencia is None:
            latencia = int((time.monotonic() - inicio) * 1000)
        id_ = self._obs.span(
            nombre=self.rol, tipo="rol",
            tokens_entrada=m.get("tokens_entrada"), tokens_salida=m.get("tokens_salida"),
            tokens_cache_creados=m.get("tokens_cache_creados"),
            tokens_cache_leidos=m.get("tokens_cache_leidos"),
            coste_usd=m.get("coste_usd"), latencia_ms=latencia,
            modelos=m.get("modelos") or None, version_de_prompt=self.version_de_prompt,
            resultado=resultado, clase_de_fallo=clase)
        object.__setattr__(self, "ultimo_span", id_)
