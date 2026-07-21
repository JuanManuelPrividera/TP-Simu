# Propuesta de sustitución de FDP mockeadas

Este documento reúne la propuesta para reemplazar las FDP mockeadas de `docs/FDP` por distribuciones conocidas y razonables para el dominio de una planta editorial industrial.

La base funcional del modelo se toma de:

- [docs/simulacion.py](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/simulacion.py)
- [docs/REPORTE_MODELO_OPERATIVO.md](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/REPORTE_MODELO_OPERATIVO.md)
- [docs/Diagramas/CALCULOS_VARIABLES.md](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/CALCULOS_VARIABLES.md)

## Criterio general

- Para variables de conteo o mezcla de producto, conviene usar distribución empírica o categórica calibrada con datos reales.
- Para duraciones con un valor central claro y rango físico acotado, conviene usar `Triangular(min, moda, max)` o `Normal truncada`.
- Para tiempos entre eventos de falla, la primera aproximación estándar es `Exponencial(mean)` si no hay evidencia de otra forma del hazard.
- Cuando ya existe una distribución razonable y contextualizada, no se propone cambiarla.

## Propuesta

| FDP | Propuesta | Motivo | Bibliografía / base |
|---|---|---|---|
| `IA` | `Exponencial(mean=9 min)` | Los arribos de pedidos se modelan bien como llegadas aleatorias con tasa aproximadamente constante en primera aproximación. La uniforme actual conserva la media, pero no representa colas largas ni variabilidad realista. | Base local en [docs/Diagramas/FDPs/IA.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/IA.mermaid). El promedio de 9 min ya aparece en el modelo. La elección exponencial es una inferencia de modelado estándar. |
| `CantLotes` | `EmpiricalDiscrete` con CDF inversa sobre `CopiasPedido` reales | Es una variable discreta de negocio y depende del mix comercial. La mejor opción es usar frecuencias observadas. | Base local en [docs/Diagramas/FDPs/CantLotes.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/CantLotes.mermaid) y contexto de producción on-demand en [BQ-300 PDF](https://www.horizon.co.jp/products/catalog/e_pdf/e002bi/01bq1_pdf/BQ300_e.pdf). |
| `TipoConfig` | `UniformDiscrete(config_1..config_N)` | El modelo necesita una cantidad cerrada de configuraciones posibles y el pedido debe poder tomar cualquiera de ellas con la misma probabilidad. | Base local en [docs/Diagramas/FDPs/TipoConfig.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/TipoConfig.mermaid). |
| `PaginasLibro` | Mantener `Normal truncada(350, 83.33; [100, 600])` y redondeo a par | Ya es una distribución conocida, positiva y acotada, coherente con el rango físico del modelo. | Base local en [docs/Diagramas/FDPs/PaginasLibro.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/PaginasLibro.mermaid). |
| `DI` | `Triangular(0.95*base, base, 1.05*base)` con `base = 100 × paginas / 100` min | La duración depende del volumen del lote y de una velocidad nominal calibrada de 100 páginas/minuto. La triangular preserva el valor central y acota extremos. | Base local en [docs/Diagramas/FDPs/DI.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DI.mermaid). |
| `DE` | `Triangular(0.11, 0.12, 0.13)` min | La fuente documenta 500 ciclos/h, equivalente a 0.12 min por lote. Triangular modela un tiempo nominal con variación pequeña. | [docs/Diagramas/FDPs/DE.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DE.mermaid), [BQ-300 PDF](https://www.horizon.co.jp/products/catalog/e_pdf/e002bi/01bq1_pdf/BQ300_e.pdf). |
| `DQA` | `Triangular(0.35, 0.3846, 0.4192)` min | La referencia de escaneo da 260 imágenes/min, o 0.3846 min por lote. La triangular concentra masa en el valor central y mantiene el rango operativo. | [docs/Diagramas/FDPs/DQA.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DQA.mermaid), [Ricoh fi-8930](https://www.ricoh-usa.com/en/products/pd/equipment/scanners/fi-8930-production-scanner). |
| `DEm` | `Triangular(0.05, 0.0545, 0.059)` min | La referencia de packaging da 1100 cajas/h, equivalente a 0.0545 min por caja. Triangular es preferible a una uniforme estrecha. | [docs/Diagramas/FDPs/DEm.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DEm.mermaid), [Sparck books & media](https://sparcktechnologies.com/industries/books-and-media/). |
| `EstadoLote` | `Bernoulli(PD=0.025)` configurable | Separa el estado real del lote de la capacidad de detección de QA y permite remuestrear cada intento productivo. | Base local en `docs/Diagramas/FDPs/EstadoLote.mermaid`. |
| `AQA` | Mantener `U(0,1)` y comparar con `PQA` | Representa la detección de un defecto real; no determina por sí sola si el lote es defectuoso. | Base local en `docs/Diagramas/FDPs/AQA.mermaid`. |
| `TConf` | Normal truncada con media `5`, desvío `0,333` y rango `[3,333; 6,667]` min | Calibración del modelo para representar una preparación promedio de cinco minutos y conservar la variabilidad relativa anterior. | [docs/Diagramas/FDPs/TConf.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/TConf.mermaid). |
| `ID` | `Exponencial truncada(λ=0.0004590417; [30, 10000]) min` | Para tiempo entre fallas se conserva la forma exponencial (tasa de falla constante), pero se impone un soporte finito y positivo. La tasa está calibrada para mantener el MTBF publicado como esperanza. | [docs/Diagramas/FDPs/ID.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/ID.mermaid), artículo citado allí sobre MTBF de Heidelberg SM 102 ZP. |
| `DD` | `Triangular(145, 153.6, 162.2)` min, o equivalente `DM + Triangular(125, 131.1, 137.2)` | Mantiene `DD > DM` por construcción y respeta el MTTR publicado. La forma triangular encaja con una reparación acotada. | [docs/Diagramas/FDPs/DD.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DD.mermaid), mismo artículo MTBF/MTTR citado en `ID.mermaid` y `DD.mermaid`. |
| `DM` | `Triangular(20, 22.5, 25)` min | Es un mantenimiento/limpieza breve con rango acotado. Triangular describe mejor la concentración alrededor del tiempo medio que una uniforme. | [docs/Diagramas/FDPs/DM.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/DM.mermaid), PDF de mantenimiento de Komori citado allí. |

## Lectura operativa

- Las variables más sensibles a recalibración son `IA`, `CantLotes`, `TipoConfig` y las duraciones de proceso `DI`, `DE`, `DQA`, `DEm`.
- Las variables aleatorias de mantenimiento (`ID`, `DD`, `DM`) quedan mejor representadas con distribuciones acotadas o exponenciales según el rol operativo. `IM` es un parámetro fijo configurable por caso.
- `PaginasLibro`, `EstadoLote` y `AQA` ya son consistentes con el objetivo del modelo y no requieren cambios urgentes.

## Fuentes principales

- [Horizon BQ-300 PDF](https://www.horizon.co.jp/products/catalog/e_pdf/e002bi/01bq1_pdf/BQ300_e.pdf)
- [Xerox Versant 280 PDF](https://download.support.xerox.com/pub/docs/VERSANT_280/userdocs/any-os/en_GB/Xerox_Versant_280_press_ug_en-US.pdf)
- [Ricoh fi-8930](https://www.ricoh-usa.com/en/products/pd/equipment/scanners/fi-8930-production-scanner)
- [Sparck Technologies: Books & Media](https://sparcktechnologies.com/industries/books-and-media/)
- DOI citado en [AQA.mermaid](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/FDPs/AQA.mermaid): `https://doi.org/10.71456/sur.v4i2.1713`
- Artículos y reportes citados dentro de los archivos `docs/Diagramas/FDPs/ID.mermaid`, `DD.mermaid` y `DM.mermaid`

## Nota metodológica

Algunas de estas selecciones son inferencias de modelado y no mediciones directas del proceso editorial de este proyecto. En particular:

- `Exponencial` para `IA` e `ID` es una aproximación estándar cuando se asume tasa aproximadamente constante.
- `Triangular` se usa cuando la documentación entrega un valor central y un rango operativo, pero no una muestra empírica completa.
- `EmpiricalDiscrete` sigue siendo útil para variables de mezcla comercial como `CantLotes`; `TipoConfig` en este proyecto pasa a ser una uniforme discreta por diseño.
