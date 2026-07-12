| Titulo del trabajo | Editorial Matriz Pinguino |
| :---: | :---: |

| Descripcion de la simulacion a realizar |
| ----- |
| Una empresa editorial industrial produce libros fisicos mediante un sistema multietapa de eventos discretos. Cada pedido se divide en lotes independientes y estos recorren, en forma secuencial, impresion, encuadernacion, control de calidad (QA) y embalaje. Las etapas disponen de multiples maquinas, colas intermedias y configuraciones que pueden requerir tiempo de preparacion. La seleccion de lotes puede responder a FIFO, prioridad por configuracion o preferencia por conservar la configuracion vigente. Un lote que no supera QA se reprocesa desde impresion. La simulacion incorpora fallas y mantenimiento preventivo en impresion, encuadernacion y embalaje; QA queda excluido de dichos mecanismos. Asimismo, las duraciones de produccion consideran la franja horaria: segun la politica energetica, una operacion que comienza en horario caro puede ejecutarse con costo caro o diferirse hasta el fin de esa franja. El modelo permite analizar tiempos de produccion, ociosidad, costos, efecto del mantenimiento y ahorro asociado a evitar la franja cara. |

| Que complejidad que extienda los casos vistos durante las clases tiene la simulacion propuesta? |
| ----- |
| La simulacion extiende los casos de una unica cola o recurso porque representa una red con cuatro etapas productivas, multiples maquinas por etapa, colas intermedias, configuraciones de maquina y politicas de secuenciacion. Ademas, incluye una realimentacion desde QA hacia impresion, eventos de desperfecto y mantenimiento preventivo sobre recursos productivos, y una regla temporal de energia que modifica la duracion o el costo de las operaciones. Estas interacciones hacen que los cuellos de botella y los tiempos de espera dependan del estado simultaneo de las colas, las maquinas y los eventos futuros. |

| Analisis previo (opcional) | |
| :---: | ----- |
| Metodologia | Evento a Evento |
| Clasificacion de variables | |
| Datos | IA (intervalo de arribo), CantLotes (cantidad de lotes por pedido), TipoConfig (configuracion del pedido), PD (probabilidad de defectos), DI (duracion de impresion), DE (duracion de encuadernacion), DQA (duracion de QA), DEm (duracion de embalaje), AQA (resultado del analisis de QA), TConf (tiempo de configuracion), ID (intervalo entre desperfectos), DD (duracion de desperfecto), IM (intervalo de mantenimiento), DM (duracion de mantenimiento) |
| Control | ALG (politica de secuenciacion: FIFO, PRIORIDADES o POR_CONFIGURACION), CONFIG_PRIORITARIA, PQA (umbral de QA), PEFC (permite producir en franja cara), CM[4] (cantidad de maquinas por etapa), InicioCaro, FinCaro, CTN/m (costo de produccion fuera de franja cara), CTC/m (costo por minuto de franja cara), CMPxL (costo de materia prima por lote), $M[3] (costo de mantenimiento por etapa mantenible) |
| Resultado | CostoPromPedido, CostoPromLote, TPPL (tiempo promedio de produccion por lote), TPPP (tiempo promedio de produccion por pedido), TiempoParadoEtapa[4], DesperfectosEvitadosPorMantenimiento, CostoAhorradoPorTCaro[4], CostoAhorradoPorTCaroTotal, SumTConf, CantLotesReProcesados |
| Estado | CLM[4], CxM[4][CM] (maquina con atributos lote y config)|

| TEF | TPLL, TPI[CM[0]], TPE[CM[1]], TPQA[CM[2]], TPEm[CM[3]], TPD[3][CM[i]], TPM[3][CM[i]] |
| :---: | :---: |


| TEI o Clasificación de eventos (según corresponda) |  |  |  |
| :---: | :---: | :---: | :---: |
| Evento | EFNC | EFC | Condición |
| Llega Pedido | Llega Pedido | Impresión\[i\] | TPI\[i\] \= HV. ^ SD\[0\] \> 0 |
| Impresión\[i\] | \- | Impresión\[i\] | CLM\[0\].size() \> 0 ^ SD\[0\] \> 0  |
|  |  | Encuadernación\[j\] | TPE\[j\] \= HV ^ SD\[1\] \> 0  |
| Encuadernado\[i\] | \- | Encuadernado\[i\] | CLM\[1\].size() \> 0 ^ SD\[1\] \> 0  |
|  |  | QA\[j\] | TPQA\[j\] \= HV |
| QA\[i\] | \- | QA\[i\] | CLM\[2\].size() \> 0 |
|  |  | Embalaje\[j\] | TPEM\[j\] \= HV ^ SD\[2\] \> 0 |
|  |  | Impresión\[j\] | TPI\[j\] \= HV ^  AQA \> PQA |
| Embalaje\[i\] | \- | Embalaje\[i\] | CLM\[3\].size() \> 0 ^ SD\[2\] \> 0 |
|  |  | Despacho | CLTA \>= CPTD |
| Mantenimiento\[i\]\[CM\[j\]\] | Mantenimiento\[i\]\[CM\[j\]\] | \- | \- |




| Mapeo de indices | |
| :---: | ----- |
| Etapas productivas | 0 = impresion, 1 = encuadernacion, 2 = QA, 3 = embalaje |
| Mantenimiento/desperfectos | 0 = impresion, 1 = encuadernacion, 2 = embalaje. QA queda excluido del mantenimiento y de los desperfectos. |

| Variables resultado y formulas | |
| :---: | ----- |
| CostoPromPedido | Si CTP > 0 entonces `((CMPxL x CTL) + CTE + $TM) / CTP`; si no, 0. |
| CostoPromLote | Si CTL > 0 entonces `CMPxL + ((CTE + $TM) / CTL)`; si no, 0. |
| TPPL | Si CTLFin > 0 entonces `STPL / CTLFin`; si no, 0. STPL acumula `T - lote.t_inicio` al finalizar embalaje. |
| TPPP | Si CTPFin > 0 entonces `STPP / CTPFin`; si no, 0. STPP acumula `T - Pedidos[pedido_id].t_inicio` al finalizar el ultimo lote del pedido. |
| TiempoParadoEtapa[4] | Para cada etapa, `FTO[i] - ITO[i]`, mas el tiempo de ociosidad abierto hasta TFin para cada maquina cuyo InicioOcio sea distinto de HV. |
| DesperfectosEvitadosPorMantenimiento | Si CantMan > 0 entonces `DesEv / CantMan`; si no, 0. |
| CostoAhorradoPorTCaroTotal | Sumatoria de `CostoAhorradoPorTCaro[0..3]`. |

| Alcance del flujo vigente | |
| :---: | ----- |
| Fin del proceso | El lote y el pedido se contabilizan como finalizados al concluir embalaje. Los diagramas vigentes no definen un evento de despacho ni una operacion de almacenamiento de lotes terminados. |
| Regla energetica | Se evalua al inicio de cada operacion mediante `HoraDia = Mod(T,1440)/60`. Si la operacion comienza en la franja cara y PEFC es falso, su duracion se difiere hasta FinCaro; si PEFC es verdadero, se ejecuta y acumula CTPC. Fuera de la franja cara, acumula CTPN. |
