# Dudas de validacion

Estas dudas salen de comparar `Docu.md` con los diagramas Mermaid. No implican cambios todavia; son decisiones para resolver antes de corregir.

1. Cuantos tipos de recursos/maquinas/colas/stock se quieren modelar exactamente? `Docu.md` usa varios arreglos de tamano 5, los diagramas productivos usan 4 etapas con maquinas, las reposiciones parecen ser 3, y mantenimiento/desperfecto iteran solo `i < 3`.

2. La llegada de pedidos debe competir como evento con `TPLL`? En `Docu.md` aparece `TPLL`, pero `Init.mermaid` no calcula un menor para llegada y `EsLlegadaMenor.mermaid` compara `TPI`, igual que impresion.

3. Como se decide si un lote reprueba QA? `Docu.md` define `PD` como probabilidad de defectos, `PQA` como politica QA y `AQA` como resultado del analisis; en `qa.mermaid` se usa `PQA < AQA` como condicion de reproceso.

4. La variable para despachar es `LRD` o `CPTD`? `Docu.md` define `LRD`, pero la tabla de eventos usa `CLTA >= CPTD`, y no hay diagrama especifico de despacho.

5. Como se debe consumir y reponer stock? Los diagramas chequean `SD[i]`, pero no se ve decremento de stock al iniciar una operacion ni programacion explicita de `TPRep[i] = T + DR[i]` cuando se cruza `SPR[i]`.

6. `TPE` debe significar tiempo proximo de encuadernacion o tiempo promedio de espera? En `Docu.md` aparece con ambos sentidos.

7. Mantenimiento y desperfectos aplican a que etapas? `Docu.md` habla de cada maquina, pero los diagramas `MenorTPM` y `MenorTPD` recorren solo tres tipos, y usan variables `TMP`, `TMD`, `IM`, `ID` que no estan clasificadas en `Docu.md`.

8. El setup (`TConf`/`TC`) aplica a todas las etapas o solo a impresion? Hay logica de seleccion/configuracion para impresion, pero los otros diagramas tambien suman `TConf` sin definir como se obtiene.

9. La energia por franja horaria debe afectar duracion, costo, o ambas? `DI.mermaid` suma tiempo adicional por franja, pero `CEM[5]` no aparece usado en diagramas ni en una metrica de costo energetico.
