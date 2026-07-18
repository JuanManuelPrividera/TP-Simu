#!/usr/bin/env python3
"""Simulacion de eventos discretos de la editorial Matriz Pinguino.

Uso: python3 simulacion.py configuracion.json [--salida resultados.json]
"""

from __future__ import annotations

import argparse
import copy
from concurrent.futures import ProcessPoolExecutor, as_completed
import json
import math
import multiprocessing
import os
import random
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from FDP import AQA, CantLotes, DD, DE, DEm, DI, DM, DQA, IA, ID, PaginasLibro, TConf, TipoConfig

HV = math.inf
ETAPAS = ("impresion", "encuadernacion", "qa", "embalaje")
# Indices de mantenimiento: impresion, encuadernacion y embalaje.
ETAPA_MANTENIBLE = (0, 1, 3)
RESULTADOS_EXPERIMENTO = (
    "CostoPromLote",
    "CTLFin",
    "TFin",
    "TiempoParadoTotal",
    "TiempoParadoEtapa",
    "CTE",
    "CTEEtapa",
    "TPPL",
    "TPPP",
    "PermanenciaPromEtapa",
    "CostoAhorradoPorTCaro",
    "CostoAhorradoPorTCaroTotal",
    "DesperfectosEvitadosPorMantenimiento",
    "CantDesperfectos",
    "CantLotesReProcesados",
    "SumTConf",
    "TiempoProduccionPromLote",
    "DuracionVaciamiento",
    "CantLotesEnColaAlTF",
    "CantLotesEnProduccionAlTF",
    "CantLotesEnColaAlFinal",
    "CantLotesEnProduccionAlFinal",
)


@dataclass
class Lote:
    config: str
    pedido_id: int
    t_inicio: float
    paginas: int
    ts: float = 0.0
    # Instante en que el lote ingresa a la etapa actual, incluyendo su espera
    # en cola, preparación, producción e interrupciones.
    t_entrada_etapa: float = 0.0


@dataclass
class Maquina:
    lote: Lote | None = None
    config: str | None = None


class Simulacion:
    def __init__(self, cfg: dict[str, Any]) -> None:
        self.cfg = cfg
        self.validar_configuracion()
        self.rng = random.Random(cfg.get("semilla"))
        self.tf = float(cfg["TF"])
        self.im = float(cfg["IM"])
        self.cm = [int(x) for x in cfg["CM"]]
        self.ctc_por_min_etapa = self._leer_vector_costos("CTC_por_min_etapa", 4)
        self.ctn_por_min_etapa = self._leer_vector_costos("CTN_por_min_etapa", 4)
        self.ctp_parado_por_min_etapa = self._leer_vector_costos("CTP_parado_por_min_etapa", 4)
        self.costo_fijo_por_min_etapa = self._leer_vector_costos("CFM_por_min_etapa", 4)
        self.costo_mantenimiento_por_etapa = self._leer_vector_costos("mantenimiento_por_etapa", 3)
        self.t = 0.0
        self.tpll = 0.0
        self.recibiendo_pedidos = True
        self.colas_al_tf: dict[str, int] | None = None
        self.produccion_al_tf: dict[str, int] | None = None
        self.tproximo = [[HV] * n for n in self.cm]
        self.tpd = [[HV] * self.cm[e] for e in ETAPA_MANTENIBLE]
        self.tpm = [[HV] * self.cm[e] for e in ETAPA_MANTENIBLE]
        self.maquinas = [
            [Maquina(config=config) for config in configuraciones]
            for configuraciones in cfg["configuraciones_iniciales"]
        ]
        self.colas: list[list[Lote]] = [[] for _ in ETAPAS]
        self.pedidos: dict[int, dict[str, float | int]] = {}
        self.pedido_id_actual = 0

        self.ctp = self.ctl = self.ctl_fin = self.ctp_fin = 0
        self.cant_man = self.des_ev = self.cant_desperfectos = self.reprocesados = 0
        self.ctpc = self.ctpn = self.costo_mantenimiento = 0.0
        self.ctpc_etapa = [0.0] * 4
        self.ctpn_etapa = [0.0] * 4
        self.costo_ahorrado = [0.0] * 4
        self.tr = [0.0] * 3
        self.sum_tconf = self.stpl = self.stpp = self.ttip = self.ttfp = 0.0
        self.tiempo_produccion_total = 0.0
        self.tiempo_produccion_etapa = [0.0] * 4
        self.sum_permanencia_etapa = [0.0] * 4
        self.cant_pasajes_etapa = [0] * 4
        self.inicio_ocio = [[0.0] * n for n in self.cm]
        self.tiempo_ocio_cerrado = [0.0] * 4

        # Correccion acordada: se agenda el primer evento de cada maquina mantenible.
        for mantenible, etapa in enumerate(ETAPA_MANTENIBLE):
            for maquina in range(self.cm[etapa]):
                self.tpd[mantenible][maquina] = ID.muestrear(self.rng)
                self.tpm[mantenible][maquina] = self.im

    def validar_configuracion(self) -> None:
        faltantes = {"TF", "IM", "CM", "PQA", "configuraciones_iniciales", "cantidad_configuraciones", "cant_lotes_media", "cant_lotes_desvio", "costos"} - self.cfg.keys()
        if faltantes:
            raise ValueError(f"Faltan parametros obligatorios: {', '.join(sorted(faltantes))}")
        if len(self.cfg["CM"]) != 4 or any(int(x) <= 0 for x in self.cfg["CM"]):
            raise ValueError("CM debe contener cuatro cantidades positivas: impresion, encuadernacion, QA, embalaje.")
        if (len(self.cfg["configuraciones_iniciales"]) != 4 or
                any(len(configuraciones) != int(self.cfg["CM"][etapa])
                    for etapa, configuraciones in enumerate(self.cfg["configuraciones_iniciales"]))):
            raise ValueError("configuraciones_iniciales debe tener una configuracion (o null) por maquina de cada etapa.")
        if float(self.cfg["TF"]) <= 0:
            raise ValueError("TF debe ser mayor que cero.")
        if not math.isfinite(float(self.cfg["IM"])) or float(self.cfg["IM"]) <= 0:
            raise ValueError("IM debe ser un intervalo finito mayor que cero, expresado en minutos.")
        if not 0 <= float(self.cfg["PQA"]) <= 1:
            raise ValueError("PQA debe estar entre 0 y 1.")
        if self.cfg.get("ALG") not in {"FIFO", "PRIORIDADES", "POR_CONFIGURACION"}:
            raise ValueError("ALG debe ser FIFO, PRIORIDADES o POR_CONFIGURACION.")
        if int(self.cfg["cantidad_configuraciones"]) <= 0:
            raise ValueError("cantidad_configuraciones debe ser mayor que cero.")
        configuraciones_validas = {
            f"config_{numero}"
            for numero in range(1, int(self.cfg["cantidad_configuraciones"]) + 1)
        }
        if self.cfg["ALG"] == "PRIORIDADES" and self.cfg.get("CONFIG_PRIORITARIA") not in configuraciones_validas:
            raise ValueError("CONFIG_PRIORITARIA debe ser una configuración válida cuando ALG es PRIORIDADES.")
        for configuraciones in self.cfg["configuraciones_iniciales"]:
            if any(config is not None and config not in configuraciones_validas for config in configuraciones):
                raise ValueError("Las configuraciones iniciales deben ser null o una configuración válida.")
        if float(self.cfg["cant_lotes_media"]) <= 0 or float(self.cfg["cant_lotes_desvio"]) <= 0:
            raise ValueError("cant_lotes_media y cant_lotes_desvio deben ser positivos.")
        costos = self.cfg["costos"]
        if "CMPxL" not in costos:
            raise ValueError("costos debe incluir CMPxL.")
        if "mantenimiento_por_etapa" not in costos:
            raise ValueError("costos debe incluir mantenimiento_por_etapa.")
        for clave in ("CTC_por_min_etapa", "CTN_por_min_etapa", "CTP_parado_por_min_etapa", "CFM_por_min_etapa"):
            if clave not in costos:
                raise ValueError(f"costos debe incluir {clave}.")

    def _leer_vector_costos(self, clave_vector: str, largo: int) -> list[float]:
        costos = self.cfg["costos"]
        valor = costos.get(clave_vector)
        if valor is None:
            raise ValueError(f"costos debe incluir {clave_vector}.")
        if not isinstance(valor, (list, tuple)):
            raise ValueError(f"{clave_vector} debe ser un vector de longitud {largo}.")
        if len(valor) != largo:
            raise ValueError(f"{clave_vector} debe tener {largo} valores.")
        return [float(x) for x in valor]

    def tipo_config(self) -> str:
        return str(TipoConfig.muestrear(self.rng, self.cfg["cantidad_configuraciones"]))

    def cant_lotes(self) -> int:
        return CantLotes.muestrear(
            self.rng,
            float(self.cfg["cant_lotes_media"]),
            float(self.cfg["cant_lotes_desvio"]),
        )

    def duracion_impresion(self, lote: Lote) -> float:
        return DI.muestrear(self.rng, lote.paginas)

    def _franja_cara_minutos(self) -> tuple[float, float]:
        return float(self.cfg["InicioCaro"]) * 60, float(self.cfg["FinCaro"]) * 60

    def _esta_en_franja_cara(self, instante: float) -> bool:
        inicio, fin = self._franja_cara_minutos()
        minuto_dia = instante % 1440
        if inicio < fin:
            return inicio < minuto_dia <= fin
        return minuto_dia > inicio or minuto_dia <= fin

    def _solape_franja_cara(self, inicio: float, duracion: float) -> float:
        fin = inicio + duracion
        inicio_caro, fin_caro = self._franja_cara_minutos()
        solape = 0.0
        dia_inicio = int(math.floor(inicio / 1440))
        dia_fin = int(math.floor((fin - 1e-12) / 1440))
        for dia in range(dia_inicio, dia_fin + 1):
            base = dia * 1440
            if inicio_caro < fin_caro:
                ventanas = ((base + inicio_caro, base + fin_caro),)
            else:
                ventanas = ((base + inicio_caro, base + 1440), (base, base + fin_caro))
            for ventana_inicio, ventana_fin in ventanas:
                solape += max(0.0, min(fin, ventana_fin) - max(inicio, ventana_inicio))
        return solape

    # Reglas de energia de DI/DE/DQA/DEm.
    def aplicar_energia(self, etapa: int, duracion: float) -> float:
        costo_caro = self.ctc_por_min_etapa[etapa]
        costo_normal = self.ctn_por_min_etapa[etapa]
        inicio_ejecucion = self.t
        demora = 0.0

        if not self.cfg["PEFC"] and self._esta_en_franja_cara(inicio_ejecucion):
            inicio_caro, fin_caro = self._franja_cara_minutos()
            minuto_dia = inicio_ejecucion % 1440
            dia = math.floor(inicio_ejecucion / 1440)
            if inicio_caro < fin_caro:
                fin_caro_abs = dia * 1440 + fin_caro
            elif minuto_dia > inicio_caro:
                fin_caro_abs = (dia + 1) * 1440 + fin_caro
            else:
                fin_caro_abs = dia * 1440 + fin_caro
            demora = max(0.0, fin_caro_abs - inicio_ejecucion)
            self.costo_ahorrado[etapa] += costo_caro * min(duracion, demora)
            inicio_ejecucion += demora

        solape_caro = self._solape_franja_cara(inicio_ejecucion, duracion)
        if solape_caro > 0:
            costo = costo_caro * solape_caro
            self.ctpc += costo
            self.ctpc_etapa[etapa] += costo
        if duracion > solape_caro:
            costo = costo_normal * (duracion - solape_caro)
            self.ctpn += costo
            self.ctpn_etapa[etapa] += costo
        return duracion + demora

    def elegir_libre_configurable(self, etapa: int, lote: Lote) -> tuple[int | None, float]:
        candidata = None
        for i, reloj in enumerate(self.tproximo[etapa]):
            if reloj == HV:
                if self.maquinas[etapa][i].config == lote.config:
                    return i, 0.0
                if candidata is None:
                    candidata = i
        if candidata is None:
            return None, 0.0
        cambio = TConf.muestrear(self.rng)
        self.sum_tconf += cambio
        return candidata, cambio

    def elegir_qa_libre(self) -> int | None:
        return next((i for i, reloj in enumerate(self.tproximo[2]) if reloj == HV), None)

    def iniciar_lote(self, etapa: int, maquina: int, lote: Lote, cambio: float = 0.0) -> None:
        recurso = self.maquinas[etapa][maquina]
        recurso.lote, recurso.config = lote, lote.config
        if etapa == 0:
            duracion_produccion = self.duracion_impresion(lote)
        elif etapa == 1:
            duracion_produccion = DE.muestrear(self.rng)
        elif etapa == 2:
            duracion_produccion = DQA.muestrear(self.rng, lote.paginas)
        else:
            duracion_produccion = DEm.muestrear(self.rng)
        self.tiempo_produccion_total += duracion_produccion
        self.tiempo_produccion_etapa[etapa] += duracion_produccion
        duracion = self.aplicar_energia(etapa, duracion_produccion)
        if self.tproximo[etapa][maquina] == HV:
            inicio_ocio = self.inicio_ocio[etapa][maquina]
            if inicio_ocio != HV:
                self.tiempo_ocio_cerrado[etapa] += self.t - inicio_ocio
            self.inicio_ocio[etapa][maquina] = HV
        self.tproximo[etapa][maquina] = self.t + duracion + cambio

    def enviar_a_etapa(self, etapa: int, lote: Lote) -> None:
        lote.t_entrada_etapa = self.t
        if etapa == 2:
            maquina = self.elegir_qa_libre()
            cambio = 0.0
        else:
            maquina, cambio = self.elegir_libre_configurable(etapa, lote)
        if maquina is None:
            lote.ts = self.t
            self.colas[etapa].append(lote)
        else:
            self.iniciar_lote(etapa, maquina, lote, cambio)

    def sacar_cola(self, etapa: int, maquina: int) -> tuple[Lote, float]:
        cola = self.colas[etapa]
        algoritmo = self.cfg["ALG"]
        indice: int | None = None
        if algoritmo == "POR_CONFIGURACION":
            candidatos = [(i, x) for i, x in enumerate(cola) if x.config == self.maquinas[etapa][maquina].config]
            if candidatos:
                indice = min(candidatos, key=lambda par: par[1].ts)[0]
        elif algoritmo == "PRIORIDADES":
            candidatos = [(i, x) for i, x in enumerate(cola) if x.config == self.cfg["CONFIG_PRIORITARIA"]]
            if candidatos:
                indice = min(candidatos, key=lambda par: par[1].ts)[0]
        elif algoritmo != "FIFO":
            raise ValueError("ALG debe ser FIFO, PRIORIDADES o POR_CONFIGURACION.")
        if indice is None:
            indice = min(range(len(cola)), key=lambda i: cola[i].ts)
        lote = cola.pop(indice)
        cambio = 0.0 if etapa == 2 or self.maquinas[etapa][maquina].config == lote.config else TConf.muestrear(self.rng)
        if cambio:
            self.sum_tconf += cambio
        return lote, cambio

    # Eventos productivos
    def llegada_pedido(self) -> None:
        self.t = self.tpll
        self.tpll = self.t + IA.muestrear(self.rng)
        config, cantidad = self.tipo_config(), self.cant_lotes()
        self.ctp += 1
        self.ctl += cantidad
        self.pedido_id_actual += 1
        pedido_id = self.pedido_id_actual
        self.pedidos[pedido_id] = {"t_inicio": self.t, "cant_lotes": cantidad, "lotes_finalizados": 0}
        self.ttip += self.t * cantidad
        for _ in range(cantidad):
            self.enviar_a_etapa(0, Lote(config, pedido_id, self.t, PaginasLibro.muestrear(self.rng)))

    def terminar_etapa(self, etapa: int, maquina: int) -> None:
        self.t = self.tproximo[etapa][maquina]
        lote = self.maquinas[etapa][maquina].lote
        if lote is None:
            raise RuntimeError("Evento de produccion sin lote asignado.")
        self.sum_permanencia_etapa[etapa] += self.t - lote.t_entrada_etapa
        self.cant_pasajes_etapa[etapa] += 1
        if etapa == 0:
            self.enviar_a_etapa(1, lote)
        elif etapa == 1:
            self.enviar_a_etapa(2, lote)
        elif etapa == 2:
            # AQA es una muestra uniforme U(0,1), generada para cada lote.
            aqa = AQA.muestrear(self.rng)
            if float(self.cfg["PQA"]) < aqa:
                self.reprocesados += 1
                self.enviar_a_etapa(0, lote)
            else:
                self.enviar_a_etapa(3, lote)
        else:
            self.ttfp += self.t
            self.stpl += self.t - lote.t_inicio
            self.ctl_fin += 1
            pedido = self.pedidos[lote.pedido_id]
            pedido["lotes_finalizados"] = int(pedido["lotes_finalizados"]) + 1
            if pedido["lotes_finalizados"] == pedido["cant_lotes"]:
                self.stpp += self.t - float(pedido["t_inicio"])
                self.ctp_fin += 1
        if self.colas[etapa]:
            siguiente, cambio = self.sacar_cola(etapa, maquina)
            self.iniciar_lote(etapa, maquina, siguiente, cambio)
        else:
            self.tproximo[etapa][maquina] = HV
            self.maquinas[etapa][maquina].lote = None
            self.inicio_ocio[etapa][maquina] = self.t

    # Eventos de mantenimiento y desperfecto.
    def desperfecto(self, mantenible: int, maquina: int) -> None:
        self.t = self.tpd[mantenible][maquina]
        self.cant_desperfectos += 1
        duracion = DD.muestrear(self.rng)
        self.tpd[mantenible][maquina] = self.t + ID.muestrear(self.rng)
        self.tpm[mantenible][maquina] = self.t + self.im
        self.tr[mantenible] += duracion
        etapa = ETAPA_MANTENIBLE[mantenible]
        if self.tproximo[etapa][maquina] != HV:
            self.tproximo[etapa][maquina] += duracion

    def mantenimiento(self, mantenible: int, maquina: int) -> None:
        self.t = self.tpm[mantenible][maquina]
        self.cant_man += 1
        self.tpm[mantenible][maquina] = self.t + self.im
        if self.tpd[mantenible][maquina] < self.tpm[mantenible][maquina]:
            self.des_ev += 1
        self.tpd[mantenible][maquina] = self.t + ID.muestrear(self.rng)
        duracion = DM.muestrear(self.rng)
        self.tr[mantenible] += duracion
        etapa = ETAPA_MANTENIBLE[mantenible]
        if self.tproximo[etapa][maquina] != HV:
            self.tproximo[etapa][maquina] += duracion
        self.costo_mantenimiento += self.costo_mantenimiento_por_etapa[mantenible]

    def proximo_evento(self) -> tuple[float, str, int, int]:
        candidatos = []
        if self.recibiendo_pedidos:
            candidatos.append((self.tpll, "llegada", -1, -1))
        for etapa, relojes in enumerate(self.tproximo):
            for maquina, reloj in enumerate(relojes):
                candidatos.append((reloj, "produccion", etapa, maquina))
        for m in range(3):
            for maquina, reloj in enumerate(self.tpd[m]):
                candidatos.append((reloj, "desperfecto", m, maquina))
            for maquina, reloj in enumerate(self.tpm[m]):
                candidatos.append((reloj, "mantenimiento", m, maquina))
        # Diferencia conocida con los diagramas: en empates, Python resuelve por orden
        # de aparicion en la lista de candidatos. Esto ya fue revisado y se acepta asi.
        return min(candidatos, key=lambda x: x[0])

    def conteo_lotes_actual(self) -> tuple[dict[str, int], dict[str, int]]:
        colas = dict(zip(ETAPAS, (len(cola) for cola in self.colas)))
        produccion = {
            etapa: sum(maquina.lote is not None for maquina in maquinas)
            for etapa, maquinas in zip(ETAPAS, self.maquinas)
        }
        return colas, produccion

    def hay_lotes_en_sistema(self) -> bool:
        return any(self.colas) or any(
            maquina.lote is not None
            for maquinas in self.maquinas
            for maquina in maquinas
        )

    def iniciar_vaciamiento(self) -> None:
        """Cierra los arribos y conserva el estado existente en el horizonte."""
        self.t = self.tf
        self.recibiendo_pedidos = False
        self.tpll = HV
        self.colas_al_tf, self.produccion_al_tf = self.conteo_lotes_actual()

    def ejecutar(self) -> dict[str, Any]:
        while True:
            if not self.recibiendo_pedidos and not self.hay_lotes_en_sistema():
                break
            instante, tipo, a, b = self.proximo_evento()
            if self.recibiendo_pedidos and (instante >= self.tf or instante == HV):
                self.iniciar_vaciamiento()
                continue
            if instante == HV:
                raise RuntimeError("Quedaron lotes sin un evento programado durante el vaciamiento.")
            if tipo == "llegada": self.llegada_pedido()
            elif tipo == "produccion": self.terminar_etapa(a, b)
            elif tipo == "desperfecto": self.desperfecto(a, b)
            else: self.mantenimiento(a, b)
        return self.resultados()

    def resultados(self) -> dict[str, Any]:
        colas_al_final, produccion_al_final = self.conteo_lotes_actual()
        colas_al_tf = self.colas_al_tf or dict.fromkeys(ETAPAS, 0)
        produccion_al_tf = self.produccion_al_tf or dict.fromkeys(ETAPAS, 0)
        parado = []
        for etapa in range(4):
            total = self.tiempo_ocio_cerrado[etapa]
            total += sum(self.t - inicio for inicio in self.inicio_ocio[etapa] if inicio != HV)
            parado.append(total)
        cte_prod_etapa = [self.ctpc_etapa[e] + self.ctpn_etapa[e] for e in range(4)]
        cte_prod_caro = sum(self.ctpc_etapa)
        cte_prod_normal = sum(self.ctpn_etapa)
        cte_prod = cte_prod_caro + cte_prod_normal
        cte_parado_etapa = [parado[e] * self.ctp_parado_por_min_etapa[e] for e in range(4)]
        cte_parado = sum(cte_parado_etapa)
        cte_etapa = [cte_prod_etapa[e] + cte_parado_etapa[e] for e in range(4)]
        costo_fijo_etapa = [self.t * self.cm[e] * self.costo_fijo_por_min_etapa[e] for e in range(4)]
        costo_fijo_maquinas = sum(costo_fijo_etapa)
        cte = cte_prod + cte_parado
        costos = self.cfg["costos"]
        costo_total = ((float(costos["CMPxL"]) * self.ctl) + cte + costo_fijo_maquinas + self.costo_mantenimiento)
        return {
            "TF": self.tf, "TFin": self.t, "DuracionVaciamiento": self.t - self.tf,
            "CTP": self.ctp, "CTL": self.ctl,
            "CTPFin": self.ctp_fin, "CTLFin": self.ctl_fin,
            "TiempoProduccionTotal": self.tiempo_produccion_total,
            "TiempoProduccionEtapa": dict(zip(ETAPAS, self.tiempo_produccion_etapa)),
            "TiempoProduccionPromLote": self.tiempo_produccion_total / self.ctl_fin if self.ctl_fin else 0,
            "CTPC": self.ctpc, "CTPN": self.ctpn, "CTEProdCaroEtapa": dict(zip(ETAPAS, self.ctpc_etapa)),
            "CTEProdNormalEtapa": dict(zip(ETAPAS, self.ctpn_etapa)),
            "CTEProdCaro": cte_prod_caro, "CTEProdNormal": cte_prod_normal, "CTEProdEtapa": dict(zip(ETAPAS, cte_prod_etapa)),
            "CTEProd": cte_prod,
            "CTEParadoEtapa": dict(zip(ETAPAS, cte_parado_etapa)),
            "CTEParado": cte_parado,
            "CTEEtapa": dict(zip(ETAPAS, cte_etapa)),
            "CostoFijoMaquinaEtapa": dict(zip(ETAPAS, costo_fijo_etapa)),
            "CostoFijoMaquinas": costo_fijo_maquinas,
            "CTE": cte, "$TM": self.costo_mantenimiento,
            "CostoTotal": costo_total,
            "CostoPromPedido": costo_total / self.ctp_fin if self.ctp_fin else 0,
            "CostoPromLote": costo_total / self.ctl_fin if self.ctl_fin else 0,
            "TPPL": self.stpl / self.ctl_fin if self.ctl_fin else 0,
            "TPPP": self.stpp / self.ctp_fin if self.ctp_fin else 0,
            "TiempoParadoEtapa": dict(zip(ETAPAS, parado)),
            "TiempoParadoTotal": sum(parado),
            "PermanenciaPromEtapa": dict(zip(
                ETAPAS,
                (self.sum_permanencia_etapa[e] / self.cant_pasajes_etapa[e]
                 if self.cant_pasajes_etapa[e] else 0 for e in range(4)),
            )),
            "CantidadPasajesEtapa": dict(zip(ETAPAS, self.cant_pasajes_etapa)),
            "CantMan": self.cant_man, "DesEv": self.des_ev, "CantDesperfectos": self.cant_desperfectos,
            "DesperfectosEvitadosPorMantenimiento": self.des_ev / self.cant_man if self.cant_man else 0,
            "TR": dict(zip(("impresion", "encuadernacion", "embalaje"), self.tr)),
            "SumTConf": self.sum_tconf, "CantLotesReProcesados": self.reprocesados,
            "CostoAhorradoPorTCaro": dict(zip(ETAPAS, self.costo_ahorrado)),
            "CostoAhorradoPorTCaroTotal": sum(self.costo_ahorrado),
            "ColasAlTF": colas_al_tf,
            "ProduccionAlTF": produccion_al_tf,
            "CantLotesEnColaAlTF": sum(colas_al_tf.values()),
            "CantLotesEnProduccionAlTF": sum(produccion_al_tf.values()),
            "ColasAlFinal": colas_al_final,
            "ProduccionAlFinal": produccion_al_final,
            "CantLotesEnColaAlFinal": sum(colas_al_final.values()),
            "CantLotesEnProduccionAlFinal": sum(produccion_al_final.values()),
        }


def combinar_configuracion(base: dict[str, Any], sobrescritura: dict[str, Any]) -> dict[str, Any]:
    """Combina recursivamente una configuración base con los cambios de un caso."""
    resultado = copy.deepcopy(base)
    for clave, valor in sobrescritura.items():
        if isinstance(valor, dict) and isinstance(resultado.get(clave), dict):
            resultado[clave] = combinar_configuracion(resultado[clave], valor)
        else:
            resultado[clave] = copy.deepcopy(valor)
    return resultado


def _ejecutar_caso(configuracion_base: dict[str, Any], caso: dict[str, Any]) -> dict[str, Any]:
    case_id = caso["case_id"]
    sobrescritura = {clave: valor for clave, valor in caso.items() if clave not in {"case_id", "description"}}
    try:
        resultado = Simulacion(combinar_configuracion(configuracion_base, sobrescritura)).ejecutar()
    except (TypeError, ValueError) as error:
        raise ValueError(f"Configuración inválida en el caso '{case_id}': {error}") from error
    return {
        "case_id": case_id,
        "description": caso.get("description", ""),
        "resultados": {clave: resultado[clave] for clave in RESULTADOS_EXPERIMENTO},
    }


def ejecutar_casos(
    configuracion_base: dict[str, Any], definicion_casos: dict[str, Any], trabajadores: int | None = None,
) -> dict[str, Any]:
    casos = definicion_casos.get("cases")
    if not isinstance(casos, list) or not casos:
        raise ValueError("El archivo de casos debe contener una lista no vacía en la clave 'cases'.")

    ids: set[str] = set()
    casos_validados = []
    for indice, caso in enumerate(casos, start=1):
        if not isinstance(caso, dict):
            raise ValueError(f"El caso {indice} debe ser un objeto JSON.")
        case_id = caso.get("case_id")
        if not isinstance(case_id, str) or not case_id.strip():
            raise ValueError(f"El caso {indice} debe incluir un case_id no vacío.")
        if case_id in ids:
            raise ValueError(f"case_id duplicado: {case_id}.")
        ids.add(case_id)
        casos_validados.append(caso)
    total = len(casos_validados)
    cantidad_trabajadores = trabajadores if trabajadores is not None else min(os.cpu_count() or 1, total)
    if cantidad_trabajadores < 1:
        raise ValueError("--trabajadores debe ser un entero mayor o igual a 1.")
    cantidad_trabajadores = min(cantidad_trabajadores, total)

    # stderr mantiene stdout disponible para el JSON cuando no se usa --salida.
    if cantidad_trabajadores == 1:
        resultados = []
        for indice, caso in enumerate(casos_validados, start=1):
            descripcion = caso.get("description", "")
            detalle = f" — {descripcion}" if descripcion else ""
            print(f"Ejecutando caso {indice}/{total}: {caso['case_id']}{detalle}", file=sys.stderr, flush=True)
            resultados.append(_ejecutar_caso(configuracion_base, caso))
        return {"casos": resultados}

    print(
        f"Ejecutando {total} casos con {cantidad_trabajadores} procesos.",
        file=sys.stderr,
        flush=True,
    )
    resultados_ordenados: list[dict[str, Any] | None] = [None] * total
    # Python 3.14 usa ``forkserver`` por defecto en POSIX; ``fork`` evita el
    # proceso servidor adicional y es adecuado aquí porque cada caso recibe
    # una copia independiente de la configuración. En Windows no está disponible.
    contexto = (
        multiprocessing.get_context("fork")
        if "fork" in multiprocessing.get_all_start_methods()
        else None
    )
    with ProcessPoolExecutor(max_workers=cantidad_trabajadores, mp_context=contexto) as executor:
        futuros = {
            executor.submit(_ejecutar_caso, configuracion_base, caso): (indice, caso)
            for indice, caso in enumerate(casos_validados)
        }
        for futuro in as_completed(futuros):
            indice, caso = futuros[futuro]
            try:
                resultados_ordenados[indice] = futuro.result()
            except Exception as error:
                for pendiente in futuros:
                    pendiente.cancel()
                raise RuntimeError(f"Falló el caso '{caso['case_id']}'.") from error
            print(
                f"Caso completado {indice + 1}/{total}: {caso['case_id']}",
                file=sys.stderr,
                flush=True,
            )
    return {"casos": [resultado for resultado in resultados_ordenados if resultado is not None]}


def cargar_json(ruta: Path) -> dict[str, Any]:
    with ruta.open(encoding="utf-8") as archivo:
        contenido = json.load(archivo)
    if not isinstance(contenido, dict):
        raise ValueError(f"{ruta} debe contener un objeto JSON.")
    return contenido


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("configuracion", type=Path, help="Configuración individual o archivo de casos.")
    parser.add_argument("--base", type=Path, help="Configuración base para un archivo con la clave 'cases'.")
    parser.add_argument(
        "--trabajadores",
        type=int,
        help="Procesos simultáneos para ejecutar casos (por defecto: núcleos disponibles).",
    )
    parser.add_argument("--salida", type=Path, help="Archivo JSON de resultados (si se omite, se imprime).")
    args = parser.parse_args()
    configuracion = cargar_json(args.configuracion)
    if "cases" in configuracion:
        ruta_base = args.base or args.configuracion.with_name("caso_base.json")
        if not ruta_base.is_file():
            raise ValueError("No se encontró la configuración base; indique --base.")
        resultados = ejecutar_casos(cargar_json(ruta_base), configuracion, args.trabajadores)
    elif args.base:
        raise ValueError("--base solo se puede usar con un archivo que contenga la clave 'cases'.")
    else:
        resultados = Simulacion(configuracion).ejecutar()
    texto = json.dumps(resultados, indent=2, ensure_ascii=False)
    if args.salida:
        args.salida.write_text(texto + "\n", encoding="utf-8")
    else:
        print(texto)


if __name__ == "__main__":
    main()
