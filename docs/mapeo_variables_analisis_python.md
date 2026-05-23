# Mapeo de variables: análisis previo vs. implementación Python

| Variable del análisis previo | Variable/s en Python | Qué es |
| --- | --- | --- |
| `IA` | `config.arrival.rate`, `st.prng.exponential("IA", ia)` | Intervalo entre arribos de pedidos. En config se guarda como tasa y en la simulación se samplea el tiempo entre llegadas. |
| `PCP` | `config.order.page_count`, `st.prng.discrete("PCP", ...)`, `order.page_count` | Cantidad de páginas del pedido/libro. |
| `CUL` | `config.order.units`, `st.prng.uniform_int("CUL", ...)`, `order.unit_count` | Cantidad de unidades de libros por pedido. |
| `PD` | `config.stages.qa.defect_probability`, `st.prng.random("PD")` | Probabilidad de defecto usada en QA para decidir reproceso. |
| `TEF[i]` | `config.stages.<stage>.failure.mtbf`, `st.prng.exponential(f"TEF_{i}", ...)` | Tiempo entre fallas por tipo de etapa/máquina. |
| `TDR[i]` | `config.stages.<stage>.failure.repair_time`, `st.prng.exponential(f"TDR_{i}", ...)` | Tiempo de reparación correctiva por etapa. |
| `TMM[i]` | `config.maintenance.durations.<stage>`, `st.prng.normal(f"TMM_{i}", ...)` | Duración del mantenimiento preventivo por etapa. |
| `CEM[i]` | `config.stages.<stage>.energy_rate`, `machine.energy_rate` | Consumo/costo energético por hora de máquina en cada etapa. |
| `TPM[i]` | `config.stages.<stage>.setup_time` | Tiempo de setup cuando cambia el tipo de libro procesado por una máquina. |
| `TR[i]` | `config.materials[i].lead_time`, `_sample_lead_time()` | Tiempo de reposición de cada material. En código es el lead time hasta el evento `STOCK_REPLENISHMENT`. |
| `PS[3]` | `config.sequencing.policy`, `make_policy(...)` | Política de secuenciación de lotes: `FIFO`, `PRIORITY`, `BOOK_TYPE`. |
| `FMP` | `config.maintenance.frequency` | Frecuencia del mantenimiento preventivo. |
| `PQA` | `config.stages.qa.defect_threshold` | Umbral/política de QA definido en config. Existe en el esquema, pero hoy la lógica operativa usa `defect_probability` (`PD`) para decidir el rechazo. |
| `RHFM[i][CM]` | `config.stages.<stage>.operating_windows`, `machine.operating_windows`, `machine.in_window()` | Franjas horarias habilitadas para operar por tipo de máquina/etapa. |
| `CPTD` | `config.stages.dispatch.threshold` | Cantidad de lotes terminados almacenados a partir de la cual se dispara el despacho. |
| `CLPL` | `config.lots.books_per_lot` | Cantidad de libros por lote. |
| `CM[i]` | `config.stages.<stage>.machines`, `st.machines[stage_idx]` | Cantidad de máquinas por etapa. |
| `LRD` | No existe variable explícita | En la implementación no se modela como variable independiente; el despacho se activa por `CLTA >= CPTD`. |
| `SPR[i]` | `config.materials[i].reorder_point`, `stock.reorder_point` | Punto de reposición mínimo de cada material. |
| `TPPT` | `report["metrics"]["TPPT"]`, `collector.tppt_samples` | Tiempo promedio de producción total por pedido. |
| `TPPL` | `report["metrics"]["TPPL"]`, `collector.tppl_samples` | Tiempo promedio de producción por lote. |
| `CxTP` | `report["metrics"]["CxTP"]` | Costo energético total dividido por `TPPT`. |
| `TSP[i]` | `report["metrics"]["TSP"]`, `collector.tsp` | Tiempo sin producción por etapa. En código acumula downtime por fallas y mantenimiento; no separa explícitamente ocio y setup. |
| `TPE[i]` | `report["metrics"]["TPE"]`, `collector.tpe_samples`, `collector.record_queue_wait(...)` | Tiempo de espera promedio en cola por etapa. |
| `PR` | `report["metrics"]["PR"]`, `collector.rework_count / collector.total_lots` | Proporción promedio de reproceso. |
| `CLM[i]` | `st.queues[i]`, `StageQueue` | Cola de lotes por etapa (`printing`, `binding`, `qa`, `packaging`). |
| `CxM[i][CM]` | `st.machines[stage_idx][machine_id]`, `Machine` | Estado/configuración de cada máquina: `status`, `current_lot`, `last_lot_type`, `pending_maintenance`, etc. |
| `SD[i]` | `st.stocks[i]`, `MaterialStock.quantity` | Stock disponible de cada materia prima. |
| `CLTA` | `st.clta` | Cantidad de lotes terminados almacenados pendientes de despacho. |
| `TPLL` | `t_arrive`, `EventType.ORDER_ARRIVAL`, `st.push(t + prng.exponential("IA", ...), ORDER_ARRIVAL)` | Próximo tiempo de llegada de pedido. No existe como variable persistente única; queda representado por eventos en la cola. |
| `TPI[CM[0]]` | `config.stages.printing.processing_time`, `_sample_processing_time(0, ...)` | Tiempo de procesamiento de impresión por lote. |
| `TPE[CM[1]]` | `config.stages.binding.processing_time`, `_sample_processing_time(1, ...)` | Tiempo de procesamiento de encuadernación por lote. |
| `TPQA` | `config.stages.qa.processing_time`, `_sample_processing_time(2, ...)` | Tiempo de procesamiento/inspección de QA por lote. |
| `TPD` / `TPDE[3][CM[i]]` | `config.stages.packaging.processing_time`, `_sample_processing_time(3, ...)` | Tiempo de procesamiento de embalaje por lote. |
| `Trace` / registro de eventos | `collector.event_log`, `trace_enabled`, `write_trace_jsonl(...)` | Log detallado de eventos de la simulación cuando se habilita traza. |

