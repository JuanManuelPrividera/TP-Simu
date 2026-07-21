#!/usr/bin/env python3
"""Genera todos los gráficos a partir de un conjunto de casos ya simulado.

Uso:
    python3 Scripts/generar_graficos.py --casos Scripts/config/casos/all_cm.json --resultados Scripts/resultados/all_cm.json

No requiere paquetes de Python externos. Genera SVG por defecto; con ``--png``
genera PNG mediante ``rsvg-convert``.
"""

from __future__ import annotations

import argparse
import html
import json
import math
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ))
from simulacion import combinar_configuracion, cargar_json  # noqa: E402

COLORES = ("#2563eb", "#dc2626", "#16a34a", "#9333ea", "#ea580c", "#0891b2")
ALGORITMOS = {
    "FIFO": "FIFO",
    "PRIORIDADES": "Prioridades",
    "POR_CONFIGURACION": "Por configuración",
}
ETAPAS = ("impresion", "encuadernacion", "qa", "embalaje")
NOMBRES_ETAPA = ("Impresión", "Encuadernación", "QA", "Embalaje")


def guardar_svg(ruta: Path, cuerpo: list[str], formato: str) -> None:
    ruta.write_text(
        "<svg xmlns='http://www.w3.org/2000/svg' width='1200' height='700' "
        "viewBox='0 0 1200 700'>"
        "<rect width='1200' height='700' fill='white'/>" + "".join(cuerpo) + "</svg>",
        encoding="utf-8",
    )
    if formato == "png":
        conversor = shutil.which("rsvg-convert")
        if not conversor:  # Validado antes de generar, para uso directo de la función.
            raise RuntimeError("No se puede generar PNG: no está instalado rsvg-convert.")
        subprocess.run([conversor, "-f", "png", "-o", str(ruta.with_suffix(".png")), str(ruta)], check=True)
        ruta.unlink()


def texto(x: float, y: float, valor: str, tam: int = 17, ancla: str = "middle", color: str = "#111827") -> str:
    return (f"<text x='{x:.1f}' y='{y:.1f}' text-anchor='{ancla}' fill='{color}' "
            f"font-family='Arial, sans-serif' font-size='{tam}'>{html.escape(valor)}</text>")


def escala(valores: list[float], incluir_cero: bool = False) -> tuple[float, float]:
    """Devuelve un rango con margen para mostrar el detalle de los datos.

    Los gráficos de líneas no incluyen el cero por defecto: así se distinguen
    variaciones pequeñas entre series. Las barras sí lo solicitan para que su
    altura conserve una referencia visual válida.
    """
    minimo, maximo = min(valores), max(valores)
    if minimo == maximo:
        margen = max(1.0, abs(maximo) * 0.1)
        ymin, ymax = minimo - margen, maximo + margen
    else:
        margen = (maximo - minimo) * 0.12
        ymin, ymax = minimo - margen, maximo + margen
    return (min(0.0, ymin), ymax) if incluir_cero else (ymin, ymax)


def etiqueta_numero(valor: float) -> str:
    valor = float(valor)
    if not valor.is_integer() and abs(valor) < 10:
        return f"{valor:.2f}".replace(".", ",")
    return f"{valor:,.0f}".replace(",", ".")


def grafico_lineas(ruta: Path, titulo: str, eje_x: str, eje_y: str,
                    series: dict[str, list[tuple[float, float]]], formato: str = "svg") -> None:
    izq, der, arriba, abajo = 130, 1120, 80, 570
    valores_x = sorted({x for puntos in series.values() for x, _ in puntos})
    valores_y = [y for puntos in series.values() for _, y in puntos]
    ymin, ymax = escala(valores_y)
    if len(valores_x) == 1:
        posicion_x = lambda _x: (izq + der) / 2
    else:
        posicion_x = lambda x: izq + (x - valores_x[0]) * (der - izq) / (valores_x[-1] - valores_x[0])
    posicion_y = lambda y: abajo - (y - ymin) * (abajo - arriba) / (ymax - ymin)
    svg = [texto(600, 38, titulo, 25),
           f"<line x1='{izq}' y1='{abajo}' x2='{der}' y2='{abajo}' stroke='#111827' stroke-width='2'/>",
           f"<line x1='{izq}' y1='{arriba}' x2='{izq}' y2='{abajo}' stroke='#111827' stroke-width='2'/>"]
    for i in range(6):
        valor = ymin + (ymax - ymin) * i / 5
        y = posicion_y(valor)
        svg += [f"<line x1='{izq}' y1='{y:.1f}' x2='{der}' y2='{y:.1f}' stroke='#d1d5db'/>",
                texto(izq - 12, y + 6, etiqueta_numero(valor), 14, "end")]
    for x in valores_x:
        px = posicion_x(x)
        svg += [f"<line x1='{px:.1f}' y1='{abajo}' x2='{px:.1f}' y2='{abajo + 7}' stroke='#111827'/>",
                texto(px, abajo + 30, etiqueta_numero(x), 14)]
    leyenda_en_dos_filas = len(series) > 4
    for indice, (nombre, puntos) in enumerate(series.items()):
        color = COLORES[indice % len(COLORES)]
        puntos = sorted(puntos)
        d = " ".join(("M" if i == 0 else "L") + f" {posicion_x(x):.1f} {posicion_y(y):.1f}" for i, (x, y) in enumerate(puntos))
        svg.append(f"<path d='{d}' fill='none' stroke='{color}' stroke-width='3.5'/>")
        for x, y in puntos:
            svg.append(f"<circle cx='{posicion_x(x):.1f}' cy='{posicion_y(y):.1f}' r='5' fill='{color}'/>")
        columna = indice % 3 if leyenda_en_dos_filas else indice
        fila = indice // 3 if leyenda_en_dos_filas else 0
        lx = 160 + columna * 320
        ly = 610 + fila * 32 if leyenda_en_dos_filas else 625
        svg += [f"<line x1='{lx}' y1='{ly}' x2='{lx + 28}' y2='{ly}' stroke='{color}' stroke-width='4'/>",
                texto(lx + 38, ly + 6, nombre, 15, "start")]
    svg += [texto((izq + der) / 2, 685, eje_x, 18),
            f"<text x='32' y='330' transform='rotate(-90 32 330)' text-anchor='middle' fill='#111827' font-family='Arial, sans-serif' font-size='18'>{html.escape(eje_y)}</text>"]
    guardar_svg(ruta, svg, formato)


def grafico_barras(
    ruta: Path, titulo: str, eje_y: str, etiquetas: list[str], valores: list[float],
    formato: str = "svg", escala_logaritmica: bool = False,
) -> None:
    izq, der, arriba, abajo = 130, 1120, 80, 570
    if escala_logaritmica:
        if any(valor <= 0 for valor in valores):
            raise ValueError("La escala logarítmica requiere valores positivos.")
        ymin = math.floor(math.log10(min(valores)))
        ymax = math.ceil(math.log10(max(valores)))
        if ymin == ymax:
            ymax += 1
        py = lambda y: abajo - (math.log10(y) - ymin) * (abajo - arriba) / (ymax - ymin)
        marcas = [10 ** (ymin + (ymax - ymin) * i / 5) for i in range(6)]
    else:
        ymin, ymax = escala(valores, incluir_cero=True)
        py = lambda y: abajo - (y - ymin) * (abajo - arriba) / (ymax - ymin)
        marcas = [ymin + (ymax - ymin) * i / 5 for i in range(6)]
    svg = [texto(600, 38, titulo, 25), f"<line x1='{izq}' y1='{abajo}' x2='{der}' y2='{abajo}' stroke='#111827' stroke-width='2'/>", f"<line x1='{izq}' y1='{arriba}' x2='{izq}' y2='{abajo}' stroke='#111827' stroke-width='2'/>"]
    for valor in marcas:
        y = py(valor)
        svg += [f"<line x1='{izq}' y1='{y:.1f}' x2='{der}' y2='{y:.1f}' stroke='#d1d5db'/>", texto(izq - 12, y + 6, etiqueta_numero(valor), 14, "end")]
    separacion = 45
    ancho = (der - izq - separacion * (len(valores) - 1)) / len(valores)
    inicio = (izq + der - (len(valores) * ancho + (len(valores) - 1) * separacion)) / 2
    base = abajo if escala_logaritmica else py(0)
    for i, (etiqueta, valor) in enumerate(zip(etiquetas, valores)):
        x, y = inicio + i * (ancho + separacion), py(valor)
        svg += [f"<rect x='{x:.1f}' y='{min(y, base):.1f}' width='{ancho}' height='{abs(base-y):.1f}' fill='{COLORES[i]}'/>", texto(x + ancho / 2, abajo + 30, etiqueta, 15), texto(x + ancho / 2, y - 10, etiqueta_numero(valor), 14)]
    svg.append(f"<text x='32' y='330' transform='rotate(-90 32 330)' text-anchor='middle' fill='#111827' font-family='Arial, sans-serif' font-size='18'>{html.escape(eje_y)}</text>")
    guardar_svg(ruta, svg, formato)


def grafico_doble(ruta: Path, titulo: str, x: list[float], izquierdos: list[float], derechos: list[float], etiqueta_izquierda: str, etiqueta_derecha: str, formato: str = "svg") -> None:
    izq, der, arriba, abajo = 130, 1060, 80, 570
    ly0, ly1 = escala(izquierdos)
    ry0, ry1 = escala(derechos)
    if min(x) == max(x):
        px = lambda _v: (izq + der) / 2
    else:
        px = lambda v: izq + (v - x[0]) * (der - izq) / (x[-1] - x[0])
    pyl = lambda v: abajo - (v - ly0) * (abajo - arriba) / (ly1 - ly0)
    pyr = lambda v: abajo - (v - ry0) * (abajo - arriba) / (ry1 - ry0)
    svg = [texto(600, 38, titulo, 25), f"<line x1='{izq}' y1='{abajo}' x2='{der}' y2='{abajo}' stroke='#111827' stroke-width='2'/>", f"<line x1='{izq}' y1='{arriba}' x2='{izq}' y2='{abajo}' stroke='#2563eb' stroke-width='2'/>", f"<line x1='{der}' y1='{arriba}' x2='{der}' y2='{abajo}' stroke='#dc2626' stroke-width='2'/>"]
    for i in range(6):
        a, b = ly0 + (ly1 - ly0) * i / 5, ry0 + (ry1 - ry0) * i / 5
        y = pyl(a)
        svg += [f"<line x1='{izq}' y1='{y:.1f}' x2='{der}' y2='{y:.1f}' stroke='#d1d5db'/>", texto(izq - 12, y + 6, etiqueta_numero(a), 14, "end", "#2563eb"), texto(der + 12, y + 6, etiqueta_numero(b), 14, "start", "#dc2626")]
    for valor in x:
        svg += [texto(px(valor), abajo + 30, etiqueta_numero(valor), 14), f"<line x1='{px(valor):.1f}' y1='{abajo}' x2='{px(valor):.1f}' y2='{abajo + 7}' stroke='#111827'/>"]
    for valores, pyf, color in ((izquierdos, pyl, COLORES[0]), (derechos, pyr, COLORES[1])):
        d = " ".join(("M" if i == 0 else "L") + f" {px(a):.1f} {pyf(b):.1f}" for i, (a, b) in enumerate(zip(x, valores)))
        svg.append(f"<path d='{d}' fill='none' stroke='{color}' stroke-width='3.5'/>")
        svg.extend(f"<circle cx='{px(a):.1f}' cy='{pyf(b):.1f}' r='5' fill='{color}'/>" for a, b in zip(x, valores))
    svg += [texto(600, 685, "Frecuencia de mantenimiento (horas)", 18), texto(175, 625, etiqueta_izquierda, 16, "start", "#2563eb"), texto(805, 625, etiqueta_derecha, 16, "start", "#dc2626")]
    guardar_svg(ruta, svg, formato)


def cargar_resultados(base: dict[str, Any], archivo_casos: Path, archivo_resultados: Path) -> list[dict[str, Any]]:
    """Une cada salida de simulación con la configuración de su case_id."""
    if not archivo_resultados.is_file():
        raise FileNotFoundError(f"No se encontró el resultado requerido: {archivo_resultados}")
    casos = cargar_json(archivo_casos)["cases"]
    salida = cargar_json(archivo_resultados).get("casos")
    if not isinstance(salida, list):
        raise ValueError(f"{archivo_resultados} debe ser el JSON generado por Scripts/simulacion.py para un archivo de casos.")
    por_id = {caso["case_id"]: caso for caso in salida}
    faltantes = [caso["case_id"] for caso in casos if caso["case_id"] not in por_id]
    if faltantes:
        raise ValueError(f"Faltan {len(faltantes)} casos en {archivo_resultados}: {', '.join(faltantes[:5])}")
    resultado = []
    for caso in casos:
        cambios = {k: v for k, v in caso.items() if k not in {"case_id", "description"}}
        resultado.append({
            "case_id": caso["case_id"],
            "configuracion": combinar_configuracion(base, cambios),
            "resultados": por_id[caso["case_id"]]["resultados"],
        })
    return resultado


def por_algoritmo(casos: list[dict[str, Any]], x: Callable[[dict[str, Any]], float], metrica: str) -> dict[str, list[tuple[float, float]]]:
    resultado: dict[str, list[tuple[float, float]]] = {}
    for caso in casos:
        alg = ALGORITMOS[caso["configuracion"]["ALG"]]
        resultado.setdefault(alg, []).append((x(caso), float(caso["resultados"][metrica])))
    return resultado


def por_pefc_fifo(casos: list[dict[str, Any]], x: Callable[[dict[str, Any]],
                  float], metrica: str) -> dict[str, list[tuple[float, float]]]:
    """Agrupa los casos FIFO según trabajen o no en la franja cara."""
    resultado: dict[str, list[tuple[float, float]]] = {}
    for caso in casos:
        configuracion = caso["configuracion"]
        if configuracion["ALG"] != "FIFO":
            continue
        politica = "PEFC=true" if configuracion["PEFC"] else "PEFC=false"
        resultado.setdefault(politica, []).append(
            (x(caso), float(caso["resultados"][metrica]))
        )
    return resultado


def tiempo_normalizado(caso: dict[str, Any], metrica: str, etapa: int | None = None) -> float:
    """Divide un acumulador temporal por la duración total TFin."""
    resultados = caso["resultados"]
    t_fin = float(resultados["TFin"])
    if not t_fin:
        return 0.0
    if etapa is None:
        acumulado = float(resultados[metrica])
    else:
        acumulado = float(resultados[metrica][ETAPAS[etapa]])
    return acumulado / t_fin


def por_algoritmo_calculado(casos: list[dict[str, Any]], x: Callable[[dict[str, Any]], float], calcular: Callable[[dict[str, Any]], float]) -> dict[str, list[tuple[float, float]]]:
    """Agrupa una métrica derivada por política de secuenciación."""
    resultado: dict[str, list[tuple[float, float]]] = {}
    for caso in casos:
        alg = ALGORITMOS[caso["configuracion"]["ALG"]]
        resultado.setdefault(alg, []).append((x(caso), calcular(caso)))
    return resultado


def limpiar_graficos_anteriores(salida: Path) -> None:
    """Elimina solo los gráficos generados en la carpeta de salida."""
    for extension in ("*.svg", "*.png"):
        for ruta in salida.glob(extension):
            if ruta.is_file():
                ruta.unlink()


def principal(archivo_casos: Path, archivo_resultados: Path, salida: Path, formato: str = "svg") -> None:
    if formato == "png" and not shutil.which("rsvg-convert"):
        raise RuntimeError("No se puede generar PNG: instalá rsvg-convert o usá --svg.")
    salida.mkdir(parents=True, exist_ok=True)
    limpiar_graficos_anteriores(salida)
    base = cargar_json(RAIZ / "config" / "caso_base.json")
    casos = cargar_resultados(base, archivo_casos, archivo_resultados)
    (salida / "resultados_usados.json").write_text(json.dumps(casos, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    conjunto = archivo_casos.stem

    conjuntos_maquinas = {
        "all_cm": (0, None),
        "impresion_cm": (0, "1.1"),
        "encuadernacion_cm": (1, "1.2"),
        "qa_cm": (2, "1.3"),
        "embalaje_cm": (3, "1.4"),
    }
    if conjunto in conjuntos_maquinas:
        indice_caracteristico, numero_costo_etapa = conjuntos_maquinas[conjunto]
        if conjunto == "all_cm":
            etiqueta_x = "Cantidad de máquinas (igual en todas las etapas)"
        else:
            etiqueta_x = f"Cantidad de máquinas de {NOMBRES_ETAPA[indice_caracteristico].lower()}"
        x_caracteristico = lambda c: c["configuracion"]["CM"][indice_caracteristico]

        grafico_lineas(salida / "1.0_costo_maquinas.svg", "Costo promedio por lote", etiqueta_x, "Costo promedio por lote", por_algoritmo(casos, x_caracteristico, "CostoPromLote"), formato)

        ocio_total = lambda c: tiempo_normalizado(c, "TiempoParadoTotal")
        grafico_lineas(salida / "2.0_tiempo_ocioso_total.svg", "Promedio de tiempo ocioso total", etiqueta_x, "Promedio de tiempo ocioso total", por_algoritmo_calculado(casos, x_caracteristico, ocio_total), formato)

        for indice, etapa in enumerate(ETAPAS):
            numero_ocio = f"2.{indice + 1}"
            nombre_etapa = NOMBRES_ETAPA[indice]
            ocio_etapa = lambda c, indice=indice: tiempo_normalizado(c, "TiempoParadoEtapa", indice)
            grafico_lineas(salida / f"{numero_ocio}_tiempo_ocioso_{etapa}.svg", f"Promedio de tiempo ocioso — {nombre_etapa}", etiqueta_x, f"Promedio de tiempo ocioso de {nombre_etapa.lower()}", por_algoritmo_calculado(casos, x_caracteristico, ocio_etapa), formato)

        configuracion_total = lambda c: tiempo_normalizado(c, "SumTConf")
        grafico_lineas(salida / "3.0_tiempo_configuracion_total.svg", "Tiempo de configuración promedio total", etiqueta_x, "Tiempo de configuración promedio total", por_algoritmo_calculado(casos, x_caracteristico, configuracion_total), formato)

        if numero_costo_etapa is not None:
            etapa = ETAPAS[indice_caracteristico]
            nombre_etapa = NOMBRES_ETAPA[indice_caracteristico]
            grafico_lineas(salida / f"{numero_costo_etapa}_costo_maquinas_{etapa}.svg", f"Costo promedio por lote — {nombre_etapa}", etiqueta_x, "Costo promedio por lote", por_algoritmo(casos, x_caracteristico, "CostoPromLote"), formato)

    if conjunto == "configs":
        x_configs = lambda c: c["configuracion"]["cantidad_configuraciones"]
        grafico_lineas(salida / "4.0_costo_configuraciones.svg", "Costo promedio por lote", "Cantidad de configuraciones", "Costo promedio por lote", por_algoritmo(casos, x_configs, "CostoPromLote"), formato)
        configuracion_total = lambda c: tiempo_normalizado(c, "SumTConf")
        grafico_lineas(salida / "4.1_tiempo_configuracion_configuraciones.svg", "Tiempo de configuración promedio total", "Cantidad de configuraciones", "Tiempo de configuración promedio total", por_algoritmo_calculado(casos, x_configs, configuracion_total), formato)

    if conjunto == "casos_im":
        xs = [float(c["configuracion"]["IM"]) for c in casos]
        costos = [float(c["resultados"]["CostoPromLote"]) for c in casos]
        efectividad = [float(c["resultados"]["DesperfectosEvitadosPorMantenimiento"]) for c in casos]
        grafico_lineas(salida / "5.0_costo_mantenimiento.svg", "Costo promedio por lote según intervalo entre mantenimientos", "Intervalo entre mantenimientos (minutos)", "Costo promedio por lote", {"Costo promedio por lote": list(zip(xs, costos))}, formato)
        grafico_lineas(salida / "5.1_desperfectos_evitados_mantenimiento.svg", "Desperfectos evitados por mantenimiento", "Intervalo entre mantenimientos (minutos)", "Desperfectos evitados por mantenimiento", {"Desperfectos evitados por mantenimiento": list(zip(xs, efectividad))}, formato)

    if conjunto == "pefc_all_cm":
        etiqueta_x = "Cantidad de máquinas (igual en todas las etapas)"
        x_maquinas = lambda c: c["configuracion"]["CM"][0]
        grafico_lineas(salida / "6.0_costo_maquinas.svg", "Costo promedio por lote", etiqueta_x,
                        "Costo promedio por lote",
                        por_pefc_fifo(casos, x_maquinas, "CostoPromLote"), formato)

    if conjunto == "rechazos_qa":
        x_pqa = lambda c: float(c["configuracion"]["PQA"])
        tasa_reproceso = lambda c: (
            float(c["resultados"]["CantLotesReProcesados"])
            / float(c["resultados"]["CTLFin"])
            if float(c["resultados"]["CTLFin"]) else 0.0
        )
        tasa_no_detectados = lambda c: (
            float(c["resultados"]["CantLotesDefectuososNoDetectados"])
            / float(c["resultados"]["CTLFin"])
            if float(c["resultados"]["CTLFin"]) else 0.0
        )
        grafico_lineas(
            salida / "7.0_reprocesamiento_qa.svg",
            "Reprocesamientos promedio por lote según detección de QA",
            "Probabilidad de detección de defectos (PQA)",
            "Reprocesamientos por lote terminado",
            {"Reprocesamientos por lote": [(x_pqa(caso), tasa_reproceso(caso)) for caso in casos]},
            formato,
        )
        grafico_lineas(
            salida / "7.1_costo_promedio_lote_qa.svg",
            "Costo promedio por lote según detección de QA",
            "Probabilidad de detección de defectos (PQA)",
            "Costo promedio por lote",
            {"Costo promedio por lote": [
                (x_pqa(caso), float(caso["resultados"]["CostoPromLote"]))
                for caso in casos
            ]},
            formato,
        )
        grafico_lineas(
            salida / "7.2_defectuosos_no_detectados_qa.svg",
            "Defectuosos no detectados según detección de QA",
            "Probabilidad de detección de defectos (PQA)",
            "Defectuosos no detectados por lote terminado",
            {"Defectuosos no detectados por lote": [
                (x_pqa(caso), tasa_no_detectados(caso))
                for caso in casos
            ]},
            formato,
        )

    if conjunto == "escenarios_representativos":
        etiquetas = ["Pesimista", "Equilibrado", "Sobredimensionado", "Costo mínimo"]
        grafico_barras(
            salida / "8.0_tiempo_promedio_lote_escenarios.svg",
            "Tiempo promedio por lote en los escenarios representativos",
            "Tiempo promedio por lote (minutos)",
            etiquetas,
            [float(caso["resultados"]["TPPL"]) for caso in casos],
            formato,
            escala_logaritmica=True,
        )
        grafico_barras(
            salida / "8.1_costo_promedio_lote_escenarios.svg",
            "Costo promedio por lote en los escenarios representativos",
            "Costo promedio por lote (u.m./lote)",
            etiquetas,
            [float(caso["resultados"]["CostoPromLote"]) for caso in casos],
            formato,
        )

    generados = sorted(ruta.name for ruta in salida.glob(f"*.{formato}"))
    listado = "\n".join(f"- `{nombre}`" for nombre in generados) or "No hay gráficos definidos para este conjunto."
    (salida / "README.md").write_text(f"# Gráficos generados\n\nCasos: `{archivo_casos}`\nResultados: `{archivo_resultados}`\nFormato: `{formato.upper()}`\n\n{listado}\n\n`resultados_usados.json` conserva los datos usados.\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", type=Path, required=True, help="Archivo del conjunto de casos usado por la simulación")
    parser.add_argument("--resultados", type=Path, required=True, help="JSON de salida generado por Scripts/simulacion.py para ese conjunto")
    parser.add_argument("--salida", type=Path, default=RAIZ / "resultados" / "graficos", help="Carpeta destino (por defecto: Scripts/resultados/graficos)")
    formato = parser.add_mutually_exclusive_group()
    formato.add_argument("--svg", action="store_const", const="svg", dest="formato", help="Generar gráficos SVG (predeterminado)")
    formato.add_argument("--png", action="store_const", const="png", dest="formato", help="Generar gráficos PNG (requiere rsvg-convert)")
    parser.set_defaults(formato="svg")
    args = parser.parse_args()
    principal(args.casos, args.resultados, args.salida, args.formato)
    print(f"Gráficos generados en: {args.salida.resolve()}")
