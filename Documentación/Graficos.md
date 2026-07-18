# Gráficos requeridos

Los gráficos 1.x, 2.x, 3.x y 4.x incluyen una curva por algoritmo. Los gráficos 5.x incluyen una sola curva y el algoritmo queda implícito en el conjunto de casos ejecutado.

En `all_cm`, el eje X de 1.0, 2.0–2.4 y 3.0 es la cantidad común de máquinas de todas las etapas. En los conjuntos `impresion_cm`, `encuadernacion_cm`, `qa_cm` y `embalaje_cm`, el eje X de esos gráficos es la cantidad de máquinas de la etapa característica del conjunto actual. Estos gráficos comunes no se generan para `configs`, `pefc_all_cm` ni `casos_im`.

| Número | Eje X | Eje Y |
|---|---|---|
| 1.0 | Cantidad de máquinas de la etapa característica del conjunto | Costo promedio por lote |
| 1.1 | Cantidad de máquinas de impresión | Costo promedio por lote |
| 1.2 | Cantidad de máquinas de encuadernación | Costo promedio por lote |
| 1.3 | Cantidad de máquinas de QA | Costo promedio por lote |
| 1.4 | Cantidad de máquinas de embalaje | Costo promedio por lote |
| 2.0 | Cantidad de máquinas de la etapa característica del conjunto | `TiempoParadoTotal / TFin` |
| 2.1 | Cantidad de máquinas de la etapa característica del conjunto | `TiempoParadoEtapa[impresion] / TFin` |
| 2.2 | Cantidad de máquinas de la etapa característica del conjunto | `TiempoParadoEtapa[encuadernacion] / TFin` |
| 2.3 | Cantidad de máquinas de la etapa característica del conjunto | `TiempoParadoEtapa[qa] / TFin` |
| 2.4 | Cantidad de máquinas de la etapa característica del conjunto | `TiempoParadoEtapa[embalaje] / TFin` |
| 3.0 | Cantidad de máquinas de la etapa característica del conjunto | `SumTConf / TFin` |
| 4.0 | Cantidad de configuraciones | Costo promedio por lote |
| 4.1 | Cantidad de configuraciones | `SumTConf / TFin` |
| 5.0 | Intervalo entre mantenimientos, en minutos | Costo promedio por lote |
| 5.1 | Intervalo entre mantenimientos, en minutos | `DesperfectosEvitadosPorMantenimiento` |

Los cocientes temporales no indican una unidad en el eje Y. `TFin` incluye el período de recepción de pedidos y el vaciamiento posterior del sistema.

El gráfico 6.0 sobre PEFC queda pendiente de definición y no se genera.
