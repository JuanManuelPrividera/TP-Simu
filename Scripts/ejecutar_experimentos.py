#!/usr/bin/env python3
"""Ejecuta conjuntos de casos de la simulación y genera sus gráficos.

Uso:
    python3 Scripts/ejecutar_experimentos.py
    python3 Scripts/ejecutar_experimentos.py --casos all_cm impresion_cm im
    python3 Scripts/ejecutar_experimentos.py --listar-casos

Sin ``--casos`` se ejecutan todos los conjuntos definidos. Los resultados se
guardan en ``Scripts/resultados/<conjunto>.json`` y los gráficos en
``Scripts/resultados/graficos/<conjunto>/``. No requiere dependencias de Python externas.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


RAIZ = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Conjunto:
    """Definición de un experimento disponible para la línea de comandos."""

    archivo: Path
    descripcion: str


CONJUNTOS = {
    "all_cm": Conjunto(Path("config/casos/all_cm.json"), "Máquinas en todas las etapas."),
    "impresion_cm": Conjunto(Path("config/casos/impresion_cm.json"), "Máquinas de impresión."),
    "encuadernacion_cm": Conjunto(Path("config/casos/encuadernacion_cm.json"), "Máquinas de encuadernación."),
    "qa_cm": Conjunto(Path("config/casos/qa_cm.json"), "Máquinas de QA."),
    "embalaje_cm": Conjunto(Path("config/casos/embalaje_cm.json"), "Máquinas de embalaje."),
    "configs": Conjunto(Path("config/casos/configs.json"), "Cantidad de configuraciones."),
    "pefc_all_cm": Conjunto(Path("config/casos/pefc_all_cm.json"), "Política energética."),
    "im": Conjunto(Path("config/casos_im.json"), "Frecuencia de mantenimiento."),
}


def ejecutar(comando: list[str]) -> None:
    """Muestra y ejecuta un comando, deteniéndose ante el primer error."""
    print("+", " ".join(str(parte) for parte in comando), flush=True)
    subprocess.run(comando, cwd=RAIZ, check=True)


def listar_casos() -> None:
    print("Conjuntos disponibles:")
    for nombre, conjunto in CONJUNTOS.items():
        print(f"  {nombre:<18} {conjunto.descripcion}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--casos",
        nargs="+",
        metavar="CONJUNTO",
        help="Conjuntos a ejecutar. Si se omite, se ejecutan todos.",
    )
    parser.add_argument("--listar-casos", action="store_true", help="Muestra los conjuntos disponibles y termina.")
    parser.add_argument(
        "--trabajadores",
        type=int,
        help="Procesos simultáneos por conjunto (por defecto: núcleos disponibles).",
    )
    parser.add_argument("--resultados", type=Path, default=RAIZ / "resultados", help="Carpeta de JSON de salida.")
    parser.add_argument("--graficos", type=Path, default=RAIZ / "resultados" / "graficos", help="Carpeta de gráficos de salida.")
    args = parser.parse_args()

    if args.listar_casos:
        listar_casos()
        return

    nombres = args.casos or list(CONJUNTOS)
    desconocidos = [nombre for nombre in nombres if nombre not in CONJUNTOS]
    if desconocidos:
        parser.error(
            f"Conjunto(s) desconocido(s): {', '.join(desconocidos)}. "
            f"Disponibles: {', '.join(CONJUNTOS)}."
        )

    # Conservar el orden indicado y no repetir trabajo si un nombre se repite.
    nombres = list(dict.fromkeys(nombres))
    resultados = args.resultados.resolve()
    graficos = args.graficos.resolve()
    resultados.mkdir(parents=True, exist_ok=True)
    graficos.mkdir(parents=True, exist_ok=True)

    for nombre in nombres:
        conjunto = CONJUNTOS[nombre]
        archivo_casos = RAIZ / conjunto.archivo
        if not archivo_casos.is_file():
            raise FileNotFoundError(f"No se encontró el archivo de casos: {archivo_casos}")
        salida_resultados = resultados / f"{nombre}.json"
        salida_graficos = graficos / nombre
        print(f"\n== {nombre}: {conjunto.descripcion} ==", flush=True)
        comando_simulacion = [
            sys.executable, str(RAIZ / "simulacion.py"), str(archivo_casos),
            "--base", str(RAIZ / "config" / "caso_base.json"),
            "--salida", str(salida_resultados),
        ]
        if args.trabajadores is not None:
            comando_simulacion += ["--trabajadores", str(args.trabajadores)]
        ejecutar(comando_simulacion)
        ejecutar([
            sys.executable, str(RAIZ / "generar_graficos.py"), "--casos", str(archivo_casos),
            "--resultados", str(salida_resultados), "--salida", str(salida_graficos),
        ])

    print(f"\nProceso terminado. Resultados: {resultados}; gráficos: {graficos}")


if __name__ == "__main__":
    main()
