# Reporte de revisión de diagramas

Fecha de revisión: 2026-07-12. Este documento registra la disposición final de los hallazgos y los cambios hechos en los diagramas. El alcance es `docs/Diagramas` y sus subdirectorios.

## Hallazgos corregidos

| ID | Corrección aplicada | Archivos afectados |
|---|---|---|
| H03 | Las decisiones de disponibilidad ahora comparan los relojes contra `HV` con `==`; las asignaciones se conservan únicamente en las actualizaciones del estado. | `LlegadPedido/LlegadaPedido.mermaid`, `impresion/Impresion.mermaid`, `encuadernacion/Encuadernacion.mermaid`, `qa/QA.mermaid`, `embalaje/Embalaje.mermaid` |
| H04 | Se conserva la metodología vigente: se calcula `HoraDia = Mod(T,1440)/60` y, si se evita producir durante la franja cara, se difiere hasta `FinCaro`. La espera ahora usa unidades compatibles: `TAdicional = (FinCaro - HoraDia) × 60` minutos. | `impresion/DI.mermaid`, `encuadernacion/DE.mermaid`, `qa/DQA.mermaid`, `embalaje/DEm.mermaid` |
| H07 | Se normalizó el atributo de configuración como `config`. Las búsquedas y las políticas de cola comparan la configuración vigente de la máquina (`CxM[..].config`) con la del lote. | Procedimientos `EncontrarMejor...` y `SacarDeLaCola...` de las cuatro etapas configurables; `ConfigsIniciales.mermaid` |
| H09 | Al extraer un lote de la cola, se actualizan juntos `CxM[etapa][máquina].lote` y `.config`, incluidos los flujos de QA. | Los cuatro `SacarDeLaColaDe*.mermaid` |
| H10 | Se unificó la métrica monetaria: `CostoAhorradoPorTCaro[4]` se inicializa y `Resultados` informa `CostoAhorradoPorTCaroTotal`. | `ConfigsIniciales.mermaid`, `Resultados.mermaid` y las cuatro funciones de duración |

## Hallazgos documentados para resolución funcional

| ID | Estado | Resolución |
|---|---|---|
| H11 | Documentado y resuelto para los resultados. | Se creó [GLOSARIO_VARIABLES.md](GLOSARIO_VARIABLES.md), con significado, unidad propuesta y referencias de `CTE`, `CTPC`, `CTPN`, `CTC/m`, `$TM` y las variables relacionadas. `Resultados` usa `CTE = CTPC + CTPN` como definición de energía total e incorpora energía, mantenimiento y materia prima en ambos promedios. [CALCULOS_VARIABLES.md](CALCULOS_VARIABLES.md) concentra las fórmulas. |
| H13 | Incorporado al glosario. | `ID`, `DD`, `IM` y `DM` quedaron definidos con unidad y referencias. La semántica propuesta es intervalo/duración de desperfecto e intervalo/duración de mantenimiento, respectivamente. |
| H14 | Incorporado al glosario. | Se documentan los relojes y duraciones en minutos, `HoraDia` y los límites de franja en horas del día, y las conversiones usadas. |
| H16 | Incorporado al glosario. | Se documentan `$TM`, `CMPxL`, `CostoPromPedido` y `CostoPromLote`, incluyendo las fórmulas de costo de producción por lote y por pedido. |

## Hallazgos descartados tras la revisión

| ID | Motivo |
|---|---|
| H01 | Descartado. La reutilización de los identificadores en los diagramas de mínimos se interpreta como la actualización del reloj mínimo de cada familia, no como una ambigüedad que exija cambiar los nombres. |
| H02 | Descartado. La política de desempate no forma parte del cambio solicitado y los predicados actuales se mantienen como la especificación vigente. |
| H05 | Descartado. El flujo de llegada conserva su conexión de retorno al bucle mediante el nodo intermedio `j`; no se modifica en esta revisión. |
| H06 | Descartado. QA no tiene desperfectos ni mantenimientos. Por esa ausencia de etapa, la numeración de los índices de mantenimiento/desperfecto es distinta de la de las cuatro etapas productivas: `0` impresión, `1` encuadernación y `2` embalaje. |
| H08 | Descartado. QA se mantiene como un flujo deliberadamente diferente de las demás etapas; no se le impone el contrato de cambio de configuración propuesto originalmente. |
| H12 | Descartado tras reanálisis. La política implementada se decide al iniciar la operación: si empieza en la franja cara y `PEFC` es falso, se agrega el tiempo necesario hasta `FinCaro`; no se busca prorratear una operación ya iniciada contra cambios tarifarios posteriores. Esa es la regla vigente en las cuatro funciones de duración. |
| H15 | Descartado. `CTC/m` es el costo total de tiempo caro por minuto; al multiplicarlo por `TiempoCaroEvitado`/`TAdicional` (minutos), el resultado es correctamente un costo monetario. La métrica se denomina ahora `CostoAhorradoPorTCaro`. |

## Supuesto de los promedios de costo

Las fórmulas distribuyen el total de lotes `CTL` y pedidos `CTP` del mismo alcance temporal. Bajo ese supuesto, el costo por pedido equivale a multiplicar el costo promedio por lote por `CTL / CTP`. El detalle está en [CALCULOS_VARIABLES.md](CALCULOS_VARIABLES.md).
