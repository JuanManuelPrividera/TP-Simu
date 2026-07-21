#!/usr/bin/env python3
"""Genera una tabla CSV a partir del experimento combinatorio de máquinas.

Uso:
    python3 Scripts/generar_tabla_combinaciones.py
    python3 Scripts/generar_tabla_combinaciones.py --resultados ruta/resultados.json

Cada fila representa un caso. Los resultados agrupados por etapa se expanden
en columnas, por ejemplo ``TiempoParadoEtapa.impresion``.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any

from simulacion import cargar_json


RAIZ = Path(__file__).resolve().parent
CASOS_PREDETERMINADOS = RAIZ / "config" / "casos" / "combinaciones_maquinas_algoritmos.json"
RESULTADOS_PREDETERMINADOS = RAIZ / "resultados" / "combinaciones_maquinas_algoritmos.json"
SALIDA_PREDETERMINADA = RAIZ / "resultados" / "tablas" / "combinaciones_maquinas_algoritmos.csv"
ETAPAS = ("impresion", "encuadernacion", "qa", "embalaje")


def aplanar_resultados(resultados: dict[str, Any], prefijo: str = "") -> dict[str, Any]:
    """Convierte diccionarios anidados en columnas separadas por puntos."""
    columnas: dict[str, Any] = {}
    for clave, valor in resultados.items():
        nombre = f"{prefijo}.{clave}" if prefijo else clave
        if isinstance(valor, dict):
            columnas.update(aplanar_resultados(valor, nombre))
        elif isinstance(valor, list):
            columnas[nombre] = json.dumps(valor, ensure_ascii=False, separators=(",", ":"))
        else:
            columnas[nombre] = valor
    return columnas


def construir_filas(definicion_casos: dict[str, Any], salida_simulacion: dict[str, Any]) -> list[dict[str, Any]]:
    casos = definicion_casos.get("cases")
    resultados = salida_simulacion.get("casos")
    if not isinstance(casos, list) or not casos:
        raise ValueError("La definición debe contener una lista no vacía en 'cases'.")
    if not isinstance(resultados, list):
        raise ValueError("El archivo de resultados debe contener una lista en 'casos'.")

    resultados_por_id: dict[str, dict[str, Any]] = {}
    for resultado in resultados:
        if not isinstance(resultado, dict) or not isinstance(resultado.get("case_id"), str):
            raise ValueError("Cada resultado debe contener un case_id válido.")
        case_id = resultado["case_id"]
        if case_id in resultados_por_id:
            raise ValueError(f"case_id duplicado en los resultados: {case_id}.")
        resultados_por_id[case_id] = resultado

    filas = []
    ids_casos = {caso.get("case_id") for caso in casos}
    for caso in casos:
        case_id = caso.get("case_id")
        if case_id not in resultados_por_id:
            raise ValueError(f"Falta el resultado del caso '{case_id}'.")
        cantidades = caso.get("CM")
        if not isinstance(cantidades, list) or len(cantidades) != len(ETAPAS):
            raise ValueError(f"El caso '{case_id}' no contiene cuatro cantidades en CM.")
        resultado = resultados_por_id[case_id].get("resultados")
        if not isinstance(resultado, dict):
            raise ValueError(f"El caso '{case_id}' no contiene un objeto 'resultados'.")

        fila: dict[str, Any] = {
            "case_id": case_id,
            "descripcion": caso.get("description", ""),
            "algoritmo": caso.get("ALG", ""),
        }
        fila.update({f"maquinas_{etapa}": cantidad for etapa, cantidad in zip(ETAPAS, cantidades)})
        fila.update(aplanar_resultados(resultado))
        filas.append(fila)

    sobrantes = set(resultados_por_id) - ids_casos
    if sobrantes:
        ejemplo = ", ".join(sorted(sobrantes)[:5])
        raise ValueError(f"Hay {len(sobrantes)} resultados sin definición de caso: {ejemplo}.")
    return filas


def escribir_csv(filas: list[dict[str, Any]], salida: Path, delimitador: str = ";") -> None:
    if not filas:
        raise ValueError("No hay filas para escribir.")
    columnas = list(dict.fromkeys(clave for fila in filas for clave in fila))
    salida.parent.mkdir(parents=True, exist_ok=True)
    with salida.open("w", encoding="utf-8-sig", newline="") as archivo:
        escritor = csv.DictWriter(archivo, fieldnames=columnas, delimiter=delimitador)
        escritor.writeheader()
        escritor.writerows(filas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", type=Path, default=CASOS_PREDETERMINADOS, help="Definición de casos.")
    parser.add_argument("--resultados", type=Path, default=RESULTADOS_PREDETERMINADOS, help="Resultados de la simulación.")
    parser.add_argument("--salida", type=Path, default=SALIDA_PREDETERMINADA, help="Archivo CSV de salida.")
    parser.add_argument("--delimitador", default=";", help="Separador del CSV (por defecto: punto y coma).")
    args = parser.parse_args()
    if len(args.delimitador) != 1:
        parser.error("--delimitador debe ser un único carácter.")
    if not args.resultados.is_file():
        parser.error(
            f"No se encontró {args.resultados}. Ejecutá primero el conjunto "
            "combinaciones_maquinas_algoritmos."
        )

    filas = construir_filas(cargar_json(args.casos), cargar_json(args.resultados))
    escribir_csv(filas, args.salida, args.delimitador)
    print(f"Tabla generada: {args.salida.resolve()} ({len(filas)} filas)")


if __name__ == "__main__":
    main()
