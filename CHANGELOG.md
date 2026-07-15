# Changelog

## 2026-07-14

### Changed

- Se actualizaron las FDP del dominio editorial en `docs/FDP`, reemplazando varios mocks por distribuciones conocidas y más realistas.
- Se agregó la propuesta formal en [docs/PROPUESTA_FDP.md](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/PROPUESTA_FDP.md).
- Se corrigió la contabilización del costo de energía en `docs/simulacion.py` para que una operación se mida por el solapamiento real con la franja cara y normal.
- Se ajustó el ahorro por franja cara para registrar únicamente el tiempo caro efectivamente evitado cuando `PEFC` es `false`.
- Se incorporó el nuevo esquema de costos configurable por etapa: energía cara, energía normal, energía en parada y costo fijo por máquina-etapa.
- Se agregó el cálculo del costo total de producción incluyendo energía productiva, energía en paro, costo fijo por etapa y mantenimiento.
- Se cambió la base de los costos promedio para usar lotes y pedidos efectivamente finalizados (`CTLFin` y `CTPFin`).
- Se actualizó la documentación para reflejar que `CostoPromPedido` y `CostoPromLote` se calculan sobre finalizados, no sobre ingresos.
- Se eliminó la compatibilidad con costos energéticos unificados: ahora `CTC/CTN/CTP_parado/CFM` deben configurarse por etapa.
- Se cambió `TipoConfig` para que dependa de `cantidad_configuraciones` y genere `config_1..config_N` con probabilidad uniforme.
- Se actualizaron `docs/README.md` y `config/casos.json` al nuevo esquema de configuración.
- Se renombró la parametrización de `CantLotes` de `mock_cant_lotes_*` a `cant_lotes_*`.
- Se sincronizó la documentación operativa en [docs/Diagramas/CALCULOS_VARIABLES.md](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Diagramas/CALCULOS_VARIABLES.md) y [docs/Docu.md](/home/asmot/DATA/_universidad/5to_anio/simu_tp/TP-Simu/docs/Docu.md).

### Notes

- La lógica de energía ahora separa el costo entre `CTPC` y `CTPN` según el tramo horario real de ejecución.
- La operación sigue pudiendo diferirse al final de la franja cara cuando corresponde, pero ese diferimiento ya no sobreestima el ahorro.
- El reproceso de QA no agrega un costo independiente: al volver a impresión, el lote vuelve a acumular los mismos costos del flujo normal.
