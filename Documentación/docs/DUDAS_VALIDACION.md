# Dudas de validacion

Estas dudas salen de comparar `Docu.md` con los diagramas Mermaid. No implican cambios todavia; son decisiones para resolver antes de corregir.

1. Cuantos tipos de recursos/maquinas/colas se quieren modelar exactamente? `Docu.md` usa varios arreglos de tamano 5, los diagramas productivos usan 4 etapas con maquinas, y mantenimiento/desperfecto iteran solo `i < 3`.

2. La llegada de pedidos debe competir como evento con `TPLL`? En `Docu.md` aparece `TPLL`, pero `Init.mermaid` no calcula un menor para llegada y `EsLlegadaMenor.mermaid` compara `TPI`, igual que impresion.

3. Resuelto: `EstadoLote` determina el defecto real con probabilidad `PD`; si el lote es defectuoso, QA lo detecta cuando `AQA < PQA`. Los defectos detectados se reprocesan y los no detectados se penalizan.

4. La variable para despachar es `LRD` o `CPTD`? `Docu.md` define `LRD`, pero la tabla de eventos usa `CLTA >= CPTD`, y no hay diagrama especifico de despacho.

5. `TPE` debe significar tiempo proximo de encuadernacion o tiempo promedio de espera? En `Docu.md` aparece con ambos sentidos.

6. Mantenimiento y desperfectos aplican a que etapas? `Docu.md` habla de cada maquina, pero los diagramas `MenorTPM` y `MenorTPD` recorren solo tres tipos, y usan variables `TMP`, `TMD`, `IM`, `ID` que no estan clasificadas en `Docu.md`.

7. El setup (`TConf`/`TC`) aplica a todas las etapas o solo a impresion? Hay logica de seleccion/configuracion para impresion, pero los otros diagramas tambien suman `TConf` sin definir como se obtiene.

8. La energia por franja horaria debe afectar duracion, costo, o ambas? `DI.mermaid` suma tiempo adicional por franja, pero `CEM[5]` no aparece usado en diagramas ni en una metrica de costo energetico.
