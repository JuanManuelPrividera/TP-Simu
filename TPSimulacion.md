| Descripción de la simulación a realizar |
| ----- |
|  Una empresa editorial industrial se dedica a la producción de libros físicos. La planta funciona como un sistema multietapa donde cada pedido, que se divide en varios lotes, debe recorrer, en orden, las siguientes etapas: impresión, encuadernación, control de calidad (QA), embalaje y despacho. Cada lote puede recorrer un camino diferente, es decir, es independiente de los demás lotes del libro (Política de Secuenciación). La producción se realiza en múltiples líneas con máquinas especializadas, cada una con capacidad limitada y tiempos de preparación (setup). Adicionalmente, el equipamiento puede sufrir fallas aleatorias, cuenta con mantenimiento preventivo planificado y mantenimiento correctivo no planificado. El comportamiento del sistema se ve influenciado por la variabilidad en la llegada de pedidos, restricciones energéticas por franjas horarias, disponibilidad de insumos, reprocesos originados por defectos detectados en QA y limitaciones de capacidad de almacenamiento de lotes terminados, una vez alcanzado dicho limite, se despachan todos los lotes terminados. En este contexto, la empresa presenta dificultades para cumplir consistentemente con los plazos de entrega, sobre todo en picos de demanda o ante fallas críticas, observándose cuellos de botella dinámicos que se desplazan entre etapas, esperas elevadas por setups frecuentes y secuenciación ineficiente, reprocesos relevantes por detección tardía de defectos, acumulación de trabajos en curso por paradas no planificadas y consumo energético ineficiente con picos en horarios de tarifa alta. Las decisiones operativas actuales se toman mayormente por intuición, sin herramientas cuantitativas para comparar alternativas. Dada la complejidad e interacción entre componentes, se propone desarrollar un modelo de simulación de eventos discretos que represente la operación de la planta editorial y permita analizar su desempeño bajo diferentes políticas de gestión. El objetivo del estudio es evaluar el impacto del criterio de secuenciación de lotes a través de las etapas del proceso productivo, mantenimiento (preventivo vs. correctivo), control de calidad y uso de energía por franja horaria, con el fin de reducir el tiempo total de producción, identificar y cuantificar cuellos de botella y analizar el equilibrio entre costo operativo, nivel de servicio y utilización de recursos.  |
| ¿Qué complejidad que extienda los casos vistos durante las clases tiene la simulación propuesta? |
| La simulación propuesta extiende los casos vistos en clase porque deja de modelar un sistema simple (una cola o un stock aislado) y pasa a representar una operación industrial completa como una red **multietapa con múltiples recursos en paralelo**, colas intermedias, donde los tiempos no dependen solo del azar sino también del tipo de pedido y de los setups, y donde las decisiones de secuenciación y prioridades afectan fuertemente el desempeño. Además incorpora fenómenos típicamente no presentes en modelos básicos, como, por ejemplo, restricciones energéticas por franjas horarias, y reprocesos por defectos detectados en control de calidad, generando acumulación de WIP. |

| Análisis previo (opcional) |  |
| :---: | ----- |
| Metodología | Evento a Evento |
| Clasificación de variables |  |
| Datos | IA (Intervalo arrivo), PCP (Prob Cant Páginas), CUL (Cant, Unidades de Libros a Imprimir), PD (Prob Defectos), TEF\[5\] (Tiempo entre fallas de cada máquina), TDR\[5\] (Tiempo de Reparación de cada máquina), TMM\[5\] (Tiempo de mantenimiento por máquina), CEM\[5\] (Consumo Energético de cada tipo de Máquina), TPM\[5\] (Tiempo de configuración por maquina) |
| Control | PS\[3\] (Política de secuenciación \= \[FIFO, Prioridad, Tipo libro\]), FMP (Frecuencia Mantenimiento Preventivo), PQA (Política QA), RHFM\[5\]\[CM\] (Rango horario de funcionamiento de cada Máquina), CPTD (Cantidad de Producto Terminado para Despachar), CLPL (Cantidad de Libros por Lote), CM\[6\] (Cantidad de Maquinas), LRD (Lotes Requeridos para Despachar), SPR\[5\] (Stock mín para reposición)  |
| Resultado | TPPT (Tiempo Promedio de Producción Total), TPPL (Tiempo Promedio de Producción por Lote), CxTP (Costo por Tiempo de Producción), TSP\[5\] (Promedio Tiempo Sin Producción \= TPR (tiempo prom de reparacion \+ TO (tiempo ocioso) \+ TP (Tiempo Preparación)), TPE\[5\] (Tiempo de espera promedio en cola por tipo de máquina), PR (Prom Reproceso)  |
| Estado | CLM\[6\] (Cola de Lotes por Tipo de Máquina), CxM\[5\]\[CM\] (Configuración de cada Maquina), SD\[5\] (Stock disponible de cada materia prima), CLTA (Cant Lotes Terminados Almacenados) |

| TEF | TPLL, TPI\[CM\[0\]\], TPE\[CM\[1\]\],TPQA, TPD, TPDE\[3\]\[CM\[i\]\] |
| :---: | :---: |

| TEI o Clasificación de eventos (según corresponda) |  |  |  |
| :---: | :---: | :---: | :---: |
| Evento | EFNC | EFC | Condición |
| Llega Libro | Llega Libro | Impresión\[CM\[i\]\] | TPI\[CM\[i\]\] \= HV. ^ SD\[0\] \> 0 ^ SD\[1\] \> 0 |
| Impresión\[i\] | \- | Impresión\[i\] | CLM\[0\] \> 0 ^ SD\[0\] \> 0  ^ SD\[1\] \> 0 |
|  |  | Encuadernación\[j\] | TPE\[j\] \= HV |
|  |  | Reposición\[0\] | SD\[0\] \= SPR\[0\] |
|  |  | Reposición\[1\] | SD\[1\] \= SPR\[1\] |
| Encuadernado\[i\] | \- | Encuadernado\[i\] | CLM\[1\] \> 0 ^SD\[2\] \> 0 ^ SD\[3\] \> 0 |
|  |  | QA | TPQA \= HV |
|  |  | Reposición\[2\] | SD\[2\] \= SPR\[2\] |
|  |  | Reposición\[3\] | SD\[3\] \= SPR\[3\] |
| QA | \- | QA | CLM\[3\] \> 0 |
|  |  | Embalaje\[j\] | TPE\[j\] \= HV |
|  |  | Impresión\[j\] | TPI\[j\] \= HV ^ PD \>= PQA |
| Embalaje\[i\] | \- | Embalaje\[i\] | CLM\[3\] \> 0 ^ SD\[4\] \> 0 |
|  |  | Despacho | CLTA \>= CPTD |
|  |  | Reposición\[4\] | SD\[4\] \= SPR\[4\] |
| Despacho | \- | Despacho | CLTA \>= CPTD |
| Desperfecto\[i\]\[CM\[k\]\] | Desperfecto\[i\]\[CM\[k\]\] | \- | \- |
| Mantenimiento \[i\] | Mantenimiento \[i\] | \- | \- |
| Reposición\[n\] | \- | Reposición\[n\] | SD\[n\] \<= SRP\[n\] |
