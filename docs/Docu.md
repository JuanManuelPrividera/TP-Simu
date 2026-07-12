| Titulo del trabajo | Editorial Matriz Pinguino |
| :---: | :---: |

| Descripcion de la simulacion a realizar |
| ----- |
| Una empresa editorial industrial se dedica a la produccion de libros fisicos. La planta funciona como un sistema multietapa donde cada pedido, dividido en varios lotes, recorre las etapas de impresion, encuadernacion, control de calidad (QA), embalaje y despacho. Cada lote puede avanzar de forma independiente segun la politica de secuenciacion. La produccion utiliza multiples lineas con maquinas especializadas, capacidad limitada y tiempos de preparacion (setup). El equipamiento puede sufrir fallas aleatorias, mantenimiento preventivo planificado y mantenimiento correctivo no planificado. El comportamiento del sistema se ve influenciado por la variabilidad en la llegada de pedidos, restricciones energeticas por franjas horarias, reprocesos originados por defectos detectados en QA y limitaciones de capacidad de almacenamiento de lotes terminados; una vez alcanzado ese limite, se despachan los lotes acumulados. En este contexto, la empresa presenta dificultades para cumplir consistentemente con los plazos de entrega, sobre todo en picos de demanda o ante fallas criticas, con cuellos de botella dinamicos, esperas por setups frecuentes, secuenciacion ineficiente, reprocesos, acumulacion de trabajos en curso por paradas no planificadas y consumo energetico ineficiente con picos en horarios de tarifa alta. Se propone desarrollar un modelo de simulacion de eventos discretos que represente la operacion de la planta editorial y permita analizar su desempeno bajo diferentes politicas de gestion. El objetivo del estudio es evaluar el impacto del criterio de secuenciacion de lotes, mantenimiento, control de calidad y uso de energia por franja horaria, con el fin de reducir el tiempo total de produccion, identificar cuellos de botella y analizar el equilibrio entre costo operativo, nivel de servicio y utilizacion de recursos. |
| Que complejidad que extienda los casos vistos durante las clases tiene la simulacion propuesta? |
| La simulacion propuesta extiende los casos vistos en clase porque deja de modelar un sistema simple de una unica cola y pasa a representar una operacion industrial completa como una red multietapa con multiples recursos en paralelo, colas intermedias, tiempos dependientes del tipo de pedido y de los setups, y decisiones de secuenciacion y prioridades que afectan el desempeno. Ademas incorpora restricciones energeticas por franjas horarias, mantenimiento preventivo y correctivo, reprocesos por defectos detectados en control de calidad y acumulacion de WIP. |

| Analisis previo (opcional) | |
| :---: | ----- |
| Metodologia | Evento a Evento |
| Clasificacion de variables | |
| Datos | IA (Intervalo arrivo), PCP (Prob Cant Paginas), CUL (Cant. Unidades de Libros a Imprimir), PD (Prob Defectos), TEF[4] (Tiempo entre fallas de cada etapa productiva), TDR[4] (Tiempo de Reparacion de cada etapa productiva), TMM[3] (Tiempo de mantenimiento para impresion, encuadernacion y embalaje), CEM[4] (Consumo Energetico de cada etapa productiva), TC[4] (Tiempo de configuracion por etapa productiva), DI (Duracion Impresion), DE (Duracion Encuadernacion), DQA (Duracion QA), DEm (Duracion Embalaje), AQA (Resultado del analisis de QA) |
| Control | PS[3] (Politica de secuenciacion = [FIFO, Prioridad, Tipo libro]), FMP (Frecuencia Mantenimiento Preventivo), PQA (Politica QA), CLPL (Cantidad de Libros por Lote), CM[4] (Cantidad de Maquinas productivas), LRD (Lotes Requeridos para Despachar), InicioBarato, FinBarato, InicioMedio, FinMedio, InicioCaro, FinCaro, TAB (T adicional barato), TAM (T adicional medio), TAC (T adicional caro) |
| Resultado | CostoPromPedido (Costo promedio de mantenimiento por pedido), CostoPromLote (Costo promedio de mantenimiento por lote), TPPL (Tiempo Promedio de Produccion por Lote), TPPP (Tiempo Promedio de Produccion por Pedido), TiempoParadoEtapa[4] (Tiempo total de maquinas paradas por etapa productiva), DesperfectosEvitadosPorMantenimiento, TiempoCaroEvitado[4], TiempoCaroEvitadoTotal, PR (Prom Reproceso) |
| Estado | CLM[4] (Cola de Lotes por etapa productiva), CxM[4][CM] (Configuracion de cada Maquina), CLTA (Cant Lotes Terminados Almacenados), Pedidos (estado de pedidos en curso), InicioOcio[4][CM] (inicio de ociosidad abierta por maquina) |

| TEF | TPLL, TPI[CM[0]], TPE[CM[1]], TPQA[CM[2]], TPEm[CM[3]], TPD[3][CM[i]], TPM[j]CM[i] |
| :---: | :---: |

| TEI o Clasificacion de eventos (segun corresponda) | | | |
| :---: | :---: | :---: | :---: |
| Evento | EFNC | EFC | Condicion |
| Llega Libro | Llega Libro | Impresion[CM[i]] | TPI[CM[i]] = HV |
| Impresion[i] | - | Impresion[i] | CLM[0] > 0 |
| | | Encuadernacion[j] | TPE[j] = HV |
| Encuadernado[i] | - | Encuadernado[i] | CLM[1] > 0 |
| | | QA[i] | TPQA[i] = HV |
| QA[i] | - | QA[i] | CLM[2] > 0 |
| | | Embalaje[j] | TPEm[j] = HV |
| | | Impresion[j] | TPI[j] = HV y AQA >= PQA |
| Embalaje[i] | - | Embalaje[i] | CLM[3] > 0 |
| | | Despacho | CLTA >= LRD |
| Mantenimiento[i][CM[j]] | Mantenimiento[i][CM[j]] | - | - |

| Mapeo de indices | |
| :---: | ----- |
| Etapas productivas | 0 = impresion, 1 = encuadernacion, 2 = QA, 3 = embalaje |
| Mantenimiento/desperfectos | 0 = impresion, 1 = encuadernacion, 2 = embalaje. QA queda excluido del mantenimiento/desperfectos en los diagramas actuales. |

| Variables resultado y formulas | |
| :---: | ----- |
| CostoPromPedido | Si CTP > 0 entonces $TM / CTP; si no, 0 |
| CostoPromLote | Si CTL > 0 entonces $TM / CTL; si no, 0 |
| TPPL | Si CTLFin > 0 entonces STPL / CTLFin; si no, 0. STPL acumula T - lote.t_inicio al finalizar embalaje. |
| TPPP | Si CTPFin > 0 entonces STPP / CTPFin; si no, 0. STPP acumula T - Pedidos[pedido_id].t_inicio cuando finaliza el ultimo lote del pedido. |
| TiempoParadoEtapa[4] | FTO[i] - ITO[i] mas el tiempo de ociosidad abierta hasta TFin para cada maquina con InicioOcio[i][j] != HV. |
| DesperfectosEvitadosPorMantenimiento | Si CantMan > 0 entonces DesEv / CantMan; si no, 0 |
| TiempoCaroEvitadoTotal | Sumatoria de TiempoCaroEvitado[0..3] |
