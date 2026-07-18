#!/usr/bin/env python3
"""Genera todos los gráficos a partir de un conjunto de casos ya simulado.

Uso:
    python3 generar_graficos.py --casos config/casos/all_cm.json --resultados resultados/all_cm.json

No requiere paquetes de Python externos. Genera SVG por defecto; con ``--png``
genera PNG mediante ``rsvg-convert``.
"""

from __future__ import annotations

import argparse
import html
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Callable

RAIZ = Path(__file__).resolve().parent
sys.path.insert(0, str(RAIZ / "docs"))
from simulacion import combinar_configuracion, cargar_json  # noqa: E402

COLORES = ("#2563eb", "#dc2626", "#16a34a", "#9333ea")
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
    for indice, (nombre, puntos) in enumerate(series.items()):
        color = COLORES[indice % len(COLORES)]
        puntos = sorted(puntos)
        d = " ".join(("M" if i == 0 else "L") + f" {posicion_x(x):.1f} {posicion_y(y):.1f}" for i, (x, y) in enumerate(puntos))
        svg.append(f"<path d='{d}' fill='none' stroke='{color}' stroke-width='3.5'/>")
        for x, y in puntos:
            svg.append(f"<circle cx='{posicion_x(x):.1f}' cy='{posicion_y(y):.1f}' r='5' fill='{color}'/>")
        lx = 160 + indice * 260
        svg += [f"<line x1='{lx}' y1='625' x2='{lx + 28}' y2='625' stroke='{color}' stroke-width='4'/>",
                texto(lx + 38, 631, nombre, 15, "start")]
    svg += [texto((izq + der) / 2, 685, eje_x, 18),
            f"<text x='32' y='330' transform='rotate(-90 32 330)' text-anchor='middle' fill='#111827' font-family='Arial, sans-serif' font-size='18'>{html.escape(eje_y)}</text>"]
    guardar_svg(ruta, svg, formato)


def grafico_barras(ruta: Path, titulo: str, eje_y: str, etiquetas: list[str], valores: list[float], formato: str = "svg") -> None:
    izq, der, arriba, abajo = 130, 1120, 80, 570
    ymin, ymax = escala(valores, incluir_cero=True)
    py = lambda y: abajo - (y - ymin) * (abajo - arriba) / (ymax - ymin)
    svg = [texto(600, 38, titulo, 25), f"<line x1='{izq}' y1='{abajo}' x2='{der}' y2='{abajo}' stroke='#111827' stroke-width='2'/>", f"<line x1='{izq}' y1='{arriba}' x2='{izq}' y2='{abajo}' stroke='#111827' stroke-width='2'/>"]
    for i in range(6):
        valor = ymin + (ymax - ymin) * i / 5
        y = py(valor)
        svg += [f"<line x1='{izq}' y1='{y:.1f}' x2='{der}' y2='{y:.1f}' stroke='#d1d5db'/>", texto(izq - 12, y + 6, etiqueta_numero(valor), 14, "end")]
    ancho, separacion = 210, 180
    inicio = (izq + der - (len(valores) * ancho + (len(valores) - 1) * separacion)) / 2
    base = py(0)
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
        raise ValueError(f"{archivo_resultados} debe ser el JSON generado por docs/simulacion.py para un archivo de casos.")
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


def tiempo_promedio_configuracion_por_lote(caso: dict[str, Any]) -> float:
    """Tiempo de configuración por lote finalizado, expresado en horas."""
    lotes_finalizados = float(caso["resultados"]["CTLFin"])
    return float(caso["resultados"]["SumTConf"]) / lotes_finalizados / 60 if lotes_finalizados else 0.0


def tiempo_ocio_promedio_maquina_dias(caso: dict[str, Any], etapa: int | None = None) -> float:
    """Ocio medio por máquina hasta TFin, en días; incluye el vaciamiento."""
    resultados, cm = caso["resultados"], caso["configuracion"]["CM"]
    if etapa is None:
        minutos = float(resultados["TiempoParadoTotal"])
        maquinas = sum(cm)
    else:
        minutos = float(resultados["TiempoParadoEtapa"][ETAPAS[etapa]])
        maquinas = cm[etapa]
    return minutos / maquinas / 1440 if maquinas else 0.0


def desperfectos_promedio_maquina_dia(caso: dict[str, Any]) -> float:
    """Desperfectos medios por máquina mantenible y día hasta TFin."""
    maquinas_mantenibles = sum(caso["configuracion"]["CM"][etapa] for etapa in (0, 1, 3))
    dias = float(caso["resultados"]["TFin"]) / 1440
    return float(caso["resultados"]["CantDesperfectos"]) / maquinas_mantenibles / dias if maquinas_mantenibles and dias else 0.0


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

    # Todos los gráficos se emiten para cualquier conjunto. Las claves que un
    # caso no declara ya fueron completadas con ``caso_base.json`` arriba; por
    # eso algunos gráficos pueden tener un único punto o curvas superpuestas.
    x_todas = lambda c: c["configuracion"]["CM"][0]
    grafico_lineas(salida / "01_costo_maquinas_todas.svg", "Costo promedio por lote — todas las etapas", "Cantidad de máquinas", "Costo promedio por lote", por_algoritmo(casos, x_todas, "CostoPromLote"), formato)
    grafico_lineas(salida / "06_tiempo_ocio_maquinas_todas.svg", "Tiempo ocioso promedio por máquina — todas las etapas", "Cantidad de máquinas", "Tiempo ocioso promedio por máquina (días)", por_algoritmo_calculado(casos, x_todas, tiempo_ocio_promedio_maquina_dias), formato)
    grafico_lineas(salida / "14_tiempo_promedio_configuracion_maquinas.svg", "Tiempo promedio de configuración por lote — todas las etapas", "Cantidad de máquinas", "Tiempo promedio de configuración por lote (minutos)", por_algoritmo_calculado(casos, x_todas, tiempo_promedio_configuracion_por_lote), formato)
    tiempo_produccion_horas = lambda c: float(c["resultados"]["TiempoProduccionPromLote"]) / 60
    grafico_lineas(salida / "15_tiempo_promedio_produccion_maquinas.svg", "Tiempo promedio de producción por lote — todas las etapas", "Cantidad de máquinas", "Tiempo promedio de producción por lote (horas)", por_algoritmo_calculado(casos, x_todas, tiempo_produccion_horas), formato)

    for indice, etapa in enumerate(ETAPAS):
        x_etapa = lambda c, indice=indice: c["configuracion"]["CM"][indice]
        grafico_lineas(salida / f"costo_maquinas_{etapa}.svg", f"Costo promedio por lote — {NOMBRES_ETAPA[indice]}", "Cantidad de máquinas", "Costo promedio por lote", por_algoritmo(casos, x_etapa, "CostoPromLote"), formato)
        ocio_etapa = lambda c, indice=indice: tiempo_ocio_promedio_maquina_dias(c, indice)
        grafico_lineas(salida / f"tiempo_ocio_maquinas_{etapa}.svg", f"Tiempo ocioso promedio por máquina — {NOMBRES_ETAPA[indice]}", "Cantidad de máquinas", "Tiempo ocioso promedio por máquina (días)", por_algoritmo_calculado(casos, x_etapa, ocio_etapa), formato)

    x_configs = lambda c: c["configuracion"]["cantidad_configuraciones"]
    grafico_lineas(salida / "07_costo_configuraciones.svg", "Costo promedio por lote", "Cantidad de configuraciones", "Costo promedio por lote", por_algoritmo(casos, x_configs, "CostoPromLote"), formato)
    grafico_lineas(salida / "08_tiempo_configuracion.svg", "Tiempo promedio de configuración por lote", "Cantidad de configuraciones", "Tiempo promedio de configuración por lote (horas)", por_algoritmo_calculado(casos, x_configs, tiempo_promedio_configuracion_por_lote), formato)

    referencia = next((c for c in casos if c["configuracion"]["ALG"] == "FIFO"), casos[0])
    por_pefc = {c["configuracion"]["PEFC"]: c for c in casos if c["configuracion"]["ALG"] == "FIFO"}
    sin_caro, con_caro = por_pefc.get(False, referencia), por_pefc.get(True, referencia)
    etiquetas = ["No producir en horario caro", "Producir en horario caro"]
    grafico_barras(salida / "09_costo_horario_caro.svg", "Costo promedio por lote según política energética", "Costo promedio por lote", etiquetas, [sin_caro["resultados"]["CostoPromLote"], con_caro["resultados"]["CostoPromLote"]], formato)
    grafico_barras(salida / "10_tiempo_ocio_horario_caro.svg", "Tiempo ocioso promedio por máquina según política energética", "Tiempo ocioso promedio por máquina (días)", etiquetas, [tiempo_ocio_promedio_maquina_dias(sin_caro), tiempo_ocio_promedio_maquina_dias(con_caro)], formato)

    xs = [c["configuracion"]["IM"] / 60 for c in casos]
    desperfectos = [desperfectos_promedio_maquina_dia(c) for c in casos]
    costos = [c["resultados"]["CostoPromLote"] for c in casos]
    grafico_lineas(salida / "11_desperfectos_mantenimiento.svg", "Desperfectos promedio según frecuencia de mantenimiento", "Frecuencia de mantenimiento (horas)", "Desperfectos promedio por máquina mantenible y día", {"Desperfectos": list(zip(xs, desperfectos))}, formato)
    grafico_lineas(salida / "12_costo_mantenimiento.svg", "Costo según frecuencia de mantenimiento", "Frecuencia de mantenimiento (horas)", "Costo promedio por lote", {"Costo promedio por lote": list(zip(xs, costos))}, formato)
    grafico_doble(salida / "13_desperfectos_y_costo_mantenimiento.svg", "Desperfectos promedio y costo según frecuencia de mantenimiento", xs, desperfectos, costos, "Desperfectos promedio por máquina y día", "Costo promedio por lote", formato)
    (salida / "README.md").write_text(f"# Gráficos generados\n\nCasos: `{archivo_casos}`\nResultados: `{archivo_resultados}`\nFormato: `{formato.upper()}`\n\nSe generan todos los gráficos definidos. Los parámetros ausentes de cada caso se completan desde `config/caso_base.json`, por lo que un gráfico puede contener un único punto o barras iguales si el conjunto no varía esa variable. `resultados_usados.json` conserva los datos usados.\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--casos", type=Path, required=True, help="Archivo del conjunto de casos usado por la simulación")
    parser.add_argument("--resultados", type=Path, required=True, help="JSON de salida generado por docs/simulacion.py para ese conjunto")
    parser.add_argument("--salida", type=Path, default=RAIZ / "graficos", help="Carpeta destino (por defecto: ./graficos)")
    formato = parser.add_mutually_exclusive_group()
    formato.add_argument("--svg", action="store_const", const="svg", dest="formato", help="Generar gráficos SVG (predeterminado)")
    formato.add_argument("--png", action="store_const", const="png", dest="formato", help="Generar gráficos PNG (requiere rsvg-convert)")
    parser.set_defaults(formato="svg")
    args = parser.parse_args()
    principal(args.casos, args.resultados, args.salida, args.formato)
    print(f"Gráficos generados en: {args.salida.resolve()}")
