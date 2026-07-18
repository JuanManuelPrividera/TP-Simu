# Simulación de eventos discretos de una línea editorial multietapa con reproceso, mantenimiento y política energética



*Universidad Tecnológica Nacional, Facultad Regional Buenos Aires*

> **Nota para versión ciega.** El bloque de autores se deja intencionalmente en blanco, conforme al formato de presentación. En la versión camera ready se incorporarán apellido(s), nombre(s), institución, dirección postal y correo electrónico de cada autor.

## Abstract

Se presenta el modelo conceptual y operativo de una simulación de eventos discretos para una planta editorial industrial que produce libros físicos por pedido. Cada pedido se descompone en lotes independientes que atraviesan, de manera secuencial, impresión, encuadernación, control de calidad (QA) y embalaje. El modelo representa recursos múltiples, colas intermedias, configuraciones de máquina, reglas alternativas de secuenciación, reproceso originado por no conformidades de calidad, fallas y mantenimiento preventivo en las etapas mantenibles, y una política de operación frente a una franja horaria de energía costosa. Se adopta un enfoque evento a evento, con tiempo expresado en minutos y un calendario de próximos eventos. Las entradas estocásticas incluyen arribos, tamaños de pedido, configuraciones, duraciones de proceso, resultado de QA, cambios de configuración e intervalos y duraciones de mantenimiento y desperfectos. Se definen métricas de tiempo de producción, utilización indirecta mediante ociosidad, costo promedio, mantenimiento y ahorro energético. El trabajo documenta el alcance efectivo del modelo, las reglas de transición y las fórmulas de salida para que el experimento pueda reproducirse y validarse. Dado que aún no se realizaron corridas experimentales consolidadas, no se reportan resultados numéricos ni se infieren mejoras: se propone en cambio un protocolo de análisis de escenarios y de validación para transformar el modelo en una herramienta de apoyo a decisiones de capacidad, secuenciación y política energética.

**Palabras clave:** simulación de eventos discretos; sistemas productivos; industria editorial; control de calidad; mantenimiento preventivo; costos energéticos.

## Introducción

Las decisiones de operación en sistemas productivos rara vez dependen de un único recurso o de una sola cola. Una planta real combina llegadas inciertas, estaciones con capacidad limitada, tiempos de proceso variables, cambios de preparación, interrupciones, controles de calidad y reglas de prioridad. Estas relaciones producen comportamientos no lineales: una modificación local puede trasladar un cuello de botella, aumentar el inventario en proceso o reducir un costo energético a cambio de una demora mayor. En tales casos, la resolución analítica suele exigir simplificaciones que eliminan justamente las interacciones de interés. La simulación permite construir una representación abstracta del sistema y experimentar sobre ella para estimar el comportamiento bajo distintas decisiones [1], [2].

El presente trabajo aborda el caso de una editorial industrial, denominada **Matriz Pingüino**, que recibe pedidos de libros físicos y los transforma mediante cuatro etapas: impresión, encuadernación, control de calidad (QA) y embalaje. Cada pedido se divide en lotes —en el modelo, un lote representa un ejemplar físico— y sus lotes pueden competir por recursos y avanzar a ritmos diferentes. El flujo no es estrictamente lineal: un lote que no aprueba QA vuelve a impresión y recorre nuevamente las etapas previas. Además, impresión, encuadernación y embalaje pueden verse afectadas por desperfectos y por mantenimiento preventivo; QA no participa de ese subsistema de mantenimiento. La diversidad de configuraciones de producto agrega otro componente relevante, porque seleccionar una máquina cuya configuración vigente coincide con el lote evita o reduce el tiempo de preparación.

El problema se complejiza por una decisión de política energética. En una franja horaria de mayor costo, la organización puede permitir el inicio de una operación y asumir el costo correspondiente, o bien postergar el inicio hasta el final de la franja. Esta decisión no sólo modifica el costo: también altera los relojes de finalización, las colas y la disponibilidad futura de las máquinas. Por ello resulta inadecuado evaluar la energía en forma aislada del resto del flujo.

El objetivo general es documentar, con un nivel de detalle reproducible, una simulación de eventos discretos de la línea editorial que permita comparar configuraciones operativas y medir sus consecuencias sobre el tiempo, la ociosidad, los costos, el mantenimiento y la exposición a la franja cara. Los objetivos específicos son: (i) delimitar el sistema representado y sus supuestos; (ii) formalizar entidades, recursos, variables, eventos y distribuciones; (iii) describir la lógica de asignación y reproceso; (iv) definir indicadores coherentes con el alcance del modelo; y (v) establecer una estrategia de verificación, validación y experimentación.

La contribución principal no consiste en afirmar, sin evidencia experimental, cuál política es óptima. Consiste en dejar especificado el instrumento que permitirá contestar esa pregunta. Esta distinción es esencial: la simulación produce información útil cuando el modelo representa correctamente lo que se pretende estudiar y cuando los resultados de réplicas comparables se interpretan con cautela [3], [4]. En consecuencia, este artículo describe los resultados que el modelo calcula y el análisis que se realizará una vez ejecutadas las corridas, pero reserva los valores cuantitativos para la etapa experimental.

> **[Lugar previsto para Figura 1 — Flujo general del sistema.]** Insertar un diagrama en blanco y negro que muestre: llegada de pedido → división en lotes → impresión → encuadernación → QA → embalaje; incluir una flecha de reproceso desde QA hacia impresión y, con líneas laterales, los eventos de mantenimiento/desperfecto aplicados a impresión, encuadernación y embalaje. La figura debe dejar visible que el proceso modelado termina en embalaje.

## Elementos del trabajo y metodología

### Enfoque de modelización y alcance

El estudio utiliza simulación de eventos discretos con avance de reloj **evento a evento**. En este enfoque, el tiempo no se incrementa con pasos fijos; el reloj global `T` salta al instante del próximo evento programado. Esta elección es adecuada para procesos donde los cambios de estado ocurren en instantes identificables, tales como la llegada de un pedido, la terminación de una operación, una falla o el comienzo de un mantenimiento [2], [5]. Todos los relojes y duraciones del modelo se expresan en minutos.

El límite del sistema comprende la recepción de pedidos, su división en lotes, las cuatro etapas de producción, las colas entre etapas, la selección de lotes, el reproceso por QA, la configuración de recursos, los desperfectos, el mantenimiento preventivo y el cálculo de indicadores al finalizar la corrida. El proceso concluye cuando un lote termina embalaje. No se representa, en el flujo operativo vigente, el almacenamiento de productos terminados, la consolidación física de pedidos, el despacho ni la distribución al cliente. Por lo tanto, los tiempos por pedido informados por la simulación significan el tiempo hasta la finalización del último lote en embalaje; no deben interpretarse como lead time comercial completo.

La abstracción empleada conserva los elementos que pueden incidir en las decisiones bajo estudio y omite actividades ajenas a ese propósito. Esta simplificación es deliberada: un modelo útil debe equilibrar realismo con comprensibilidad y capacidad de análisis [1]. En particular, la ausencia de despacho no es una omisión que pueda compensarse al interpretar resultados: es una frontera explícita del modelo.

### Entidades, atributos, recursos y estado

Las entidades dinámicas son los pedidos y los lotes. Al llegar un pedido se asigna un identificador incremental y se registra su instante de llegada, su cantidad total de lotes y el número de lotes ya finalizados. Cada lote conserva, como mínimo, el identificador del pedido al que pertenece, el instante de inicio heredado de la llegada y la configuración del producto. Mantener esos atributos durante todo el recorrido, incluso si el lote se reprocesa, permite medir correctamente el tiempo de producción desde la creación del lote y el tiempo total del pedido.

Los recursos son las máquinas de las cuatro etapas productivas. La cantidad de máquinas es una variable de control `CM[4]`, con el mapeo: `0` impresión, `1` encuadernación, `2` QA y `3` embalaje. Cada etapa posee una cola `CLM[e]` y cada máquina `CxM[e][m]` conserva el lote que está procesando y su configuración vigente. Esta última información permite distinguir entre asignar un lote a una máquina compatible y asignarlo a una máquina que exige preparación previa.

La cola de cada etapa representa los lotes que llegaron y no pudieron iniciar inmediatamente su operación. El sistema puede aplicar tres alternativas de extracción: FIFO, prioridad por configuración y preferencia por conservar la configuración vigente. Cuando una política no identifica un candidato elegible, se utiliza el lote con menor instante de entrada a la cola. Así, la regla no deja una máquina disponible sin asignación por falta de coincidencia de configuración.

El estado también incorpora los relojes de próximos eventos. Se utilizan `TPLL` para la próxima llegada; `TPI[]`, `TPE[]`, `TPQA[]` y `TPEm[]` para las finalizaciones de impresión, encuadernación, QA y embalaje; `TPD[][]` para desperfectos; y `TPM[][]` para mantenimiento. Un valor `HV` representa un reloj no activo. La selección del siguiente evento compara la próxima llegada, la menor finalización de cada familia productiva, el desperfecto más próximo y el mantenimiento más próximo. Las comparaciones son estrictas y la especificación vigente no define una regla adicional de desempate cuando dos eventos coinciden exactamente en tiempo. Esta condición debe documentarse en cualquier implementación porque puede afectar casos límite y reproducibilidad entre plataformas.

### Variables de entrada y generación aleatoria

El modelo es estocástico: parte de sus entradas se generan con números pseudoaleatorios uniformes y funciones de distribución asociadas. La Tabla 1 resume las variables principales y sus parámetros actualmente documentados. Las distribuciones empíricas se emplean cuando el atributo deriva de observaciones de pedidos —por ejemplo, configuración o cantidad de ejemplares—, mientras que varias duraciones se modelan mediante uniformes estrechas o normales truncadas. Esta combinación busca representar variabilidad sin generar valores físicamente imposibles.

**Tabla 1. Variables estocásticas de entrada y especificación vigente**

| Variable | Interpretación | Distribución o regla | Unidad / rango relevante |
|---|---|---|---|
| `IA` | intervalo entre arribos | normal truncada positiva, media 1440 y desvío 504 | min; media 1 día y desvío 0,35 días |
| `CantLotes` | lotes por pedido | inversa de distribución empírica de copias | entero observado |
| `TipoConfig` | formato/configuración de producto | inversa de distribución empírica | categoría |
| `PaginasLibro` | páginas del libro | normal truncada, media 350 y desvío 83,33; redondeo par | 100 a 600 páginas |
| `DI` | duración de impresión | uniforme ±5 % sobre `CantLibrosLote × CantPaginas / 100` | min |
| `DE` | duración de encuadernación | `U(0,11; 0,13)` | min/lote |
| `DQA` | duración de control de calidad | `U(0,35; 0,4192)` | min/lote |
| `DEm` | duración de embalaje | `U(0,05; 0,059)` | min/lote |
| `AQA` | resultado de QA | Bernoulli con `p = 0,025` de defecto | 0 aprueba; 1 defectuoso |
| `TConf` | preparación por cambio de configuración | normal truncada, media 5 y desvío 0,333 | 3,333 a 6,667 min |
| `ID` / `DD` | intervalo y duración de desperfecto | `U(2000; 2209,6)` / `DM + U(125; 137,2)` | min |
| `IM` | intervalo entre mantenimientos preventivos | parámetro fijo de configuración por caso | min |
| `DM` | duración de mantenimiento | `U(20;25)` | min |

La definición de `DD` garantiza que el desperfecto dure más que el mantenimiento, lo cual hace consistente la hipótesis operativa de que una intervención preventiva es más breve que una reparación correctiva. La probabilidad de defecto se modela por `AQA`; el umbral `PQA` se conserva como parámetro de control de la regla de aceptación. En la lógica vigente, un resultado superior a ese umbral dispara el reproceso. Para la Bernoulli documentada, el resultado 1 representa defecto y 0 aprobación, por lo que con `PQA = 0,025` el caso defectuoso se reenvía a impresión.

Las distribuciones y sus parámetros deben considerarse supuestos iniciales, no verdades universales sobre la planta. Antes de utilizar la simulación para tomar decisiones de inversión, corresponde contrastarlas con registros reales, analizar valores atípicos y verificar independencia, estabilidad temporal y unidad de medida. La generación de variables aleatorias y la validación de datos de entrada son componentes centrales de un estudio de simulación [4], [5].

> **[Lugar previsto para Figura 2 — Calendario de eventos.]** Incluir un esquema del reloj global y de los vectores `TPLL`, `TPI`, `TPE`, `TPQA`, `TPEm`, `TPD` y `TPM`, indicando que se selecciona el menor valor distinto de `HV`. Señalar con una nota que falta formalizar una regla de desempate para instantes iguales.

### Lógica del flujo productivo

Una llegada crea un pedido y sus lotes. Cada lote intenta asignarse a una impresora libre; si no hay disponibilidad, se incorpora a `CLM[0]`. La asignación intenta primero encontrar una máquina libre con configuración coincidente. Si existe, el tiempo de configuración es cero. Si no, se selecciona una máquina candidata libre, se genera `TConf` y se programa la finalización de impresión. La misma lógica de compatibilidad se aplica en impresión, encuadernación y embalaje. QA recibe y conserva el atributo de configuración del lote, pero su duración no incluye un tiempo de cambio de configuración.

Al concluir impresión, el lote se ofrece a encuadernación. Si hay una encuadernadora disponible se programa `TPE`; de lo contrario, ingresa a la cola de encuadernación. La terminación de encuadernación análogamente intenta asignar una máquina de QA o deposita el lote en `CLM[2]`. Una vez que termina el control, se genera `AQA`. Si el lote aprueba, avanza a embalaje; si no aprueba, vuelve a impresión. El retorno no crea una entidad nueva ni reinicia sus atributos temporales: el mismo lote conserva su `pedido_id` y `t_inicio`. Esta condición evita subestimar el tiempo de los lotes reprocesados y evita contabilizar dos veces un pedido.

La terminación de embalaje materializa el fin productivo del lote. En ese instante se acumula `T - lote.t_inicio` en `STPL`, se incrementa el conteo de lotes terminados y se actualiza el pedido correspondiente. Si la cantidad de lotes finalizados coincide con la cantidad total de ese pedido, se acumula `T - Pedidos[pedido_id].t_inicio` en `STPP`. Por lo tanto, el indicador de pedido captura el efecto de que sus lotes recorran caminos temporales diferentes y finalice recién el último.

**Tabla 2. Reglas de transición entre etapas**

| Evento de terminación | Acción principal | Destino posible | Consecuencia de estado |
|---|---|---|---|
| Llegada de pedido | crear pedido y lotes | impresión o cola de impresión | incrementa `CTP` y `CTL` |
| Impresión | liberar impresora y ofrecer lote | encuadernación o `CLM[1]` | programa `TPE` si hay recurso |
| Encuadernación | liberar encuadernadora y ofrecer lote | QA o `CLM[2]` | programa `TPQA` si hay recurso |
| QA aprobado | liberar recurso de QA | embalaje o `CLM[3]` | programa `TPEm` si hay recurso |
| QA rechazado | liberar recurso de QA | impresión o `CLM[0]` | conserva atributos del lote |
| Embalaje | liberar embaladora y registrar salida | fin productivo del lote | actualiza `STPL`, `CTLFin` y, si corresponde, `STPP`, `CTPFin` |

> **[Lugar previsto para Figura 3 — Diagrama detallado de la lógica de un lote.]** Insertar un diagrama de flujo que incluya decisión de máquina libre, elección por configuración, cola, preparación, terminación de etapa y bifurcación de QA. Debe destacarse con una flecha gruesa el lazo QA → impresión.

### Política energética y formación de costos

La regla energética se evalúa al comienzo de cada operación de impresión, encuadernación, QA o embalaje. A partir del reloj global se calcula `HoraDia = Mod(T,1440) / 60`. Si una operación comienza dentro de la franja delimitada por `InicioCaro` y `FinCaro`, existen dos alternativas. Cuando `PEFC` permite producir durante la franja cara, se ejecuta la operación y se acumula el costo energético caro. Cuando `PEFC` es falso, se calcula `TAdicional = (FinCaro - HoraDia) × 60`, se agrega esa espera a la duración de la operación y se acumula el ahorro monetario asociado a evitar minutos caros. La regla se decide al inicio: una operación iniciada fuera de la franja no se fracciona aunque continúe dentro de ella, y una operación diferida se programa al final de la ventana cara.

El costo de energía total se define como `CTE = CTPC + CTPN`. Al finalizar la corrida, el modelo calcula:

`CostoPromPedido = ((CMPxL × CTL) + CTE + $TM) / CTP`, si `CTP > 0`;

`CostoPromLote = CMPxL + (CTE + $TM) / CTL`, si `CTL > 0`.

Estas expresiones distribuyen el costo de materia prima, energía y mantenimiento sobre los pedidos o lotes del alcance temporal de la corrida. Son equivalentes entre sí cuando `CTP` y `CTL` corresponden al mismo universo de llegadas. Es importante subrayar que no constituyen todavía un costo unitario de venta ni incorporan costos de despacho, almacenamiento, mano de obra, merma fuera del reproceso o capital inmovilizado, pues tales conceptos no pertenecen al alcance modelado.

El indicador `CostoAhorradoPorTCaro[e]` acumula, por etapa, `(CTC/m) × TAdicional`; su suma es `CostoAhorradoPorTCaroTotal`. Es un ahorro **potencial de costo caro evitado** según la regla programada; debe analizarse junto con el tiempo adicional y las colas, porque diferir una operación puede generar un efecto adverso sobre el lead time. Por ello, una política energética no debe evaluarse sólo por el ahorro monetario.

> **[Lugar previsto para Figura 4 — Política de franja cara.]** Incorporar una línea de tiempo de 24 horas con `InicioCaro`, `FinCaro`, un ejemplo de operación que inicia dentro de la franja y dos ramas: producir (`PEFC = verdadero`) o diferir hasta `FinCaro` (`PEFC = falso`). Señalar el costo o la espera agregada en cada rama.

### Desperfectos y mantenimiento preventivo

Los desperfectos y mantenimientos afectan exclusivamente impresión, encuadernación y embalaje. Para este subsistema, los índices no coinciden con los de las cuatro etapas productivas: `0` representa impresión, `1` encuadernación y `2` embalaje. QA queda deliberadamente excluida. Esta diferencia de índices debe preservarse en la implementación para evitar aplicar mantenimiento a QA o asociar eventos a una máquina incorrecta.

Cuando ocurre un desperfecto en una máquina mantenible, se programa el próximo desperfecto, se agenda el mantenimiento asociado, se acumula la indisponibilidad y se incrementa en `DD` el reloj de finalización de la máquina afectada. El mantenimiento preventivo incrementa `CantMan`, acumula su costo en `$TM`, reprograma su próxima ocurrencia y extiende el reloj de la máquina en `DM`. Si el mantenimiento ocurre antes que el desperfecto que estaba programado, se incrementa `DesEv`, que representa desperfectos evitados. Al finalizar se informa `DesperfectosEvitadosPorMantenimiento = DesEv / CantMan`, con protección ante `CantMan = 0`.

Este indicador no reemplaza una evaluación económica completa del mantenimiento: un valor alto puede coexistir con excesiva frecuencia preventiva o con costos que superen los beneficios. En cambio, funciona como señal de efectividad relativa, que debe complementarse con `$TM`, tiempo de indisponibilidad, producción terminada y costo promedio.

### Indicadores de desempeño

La Tabla 3 reúne las variables de resultado que definen el conjunto mínimo de observación. Las divisiones por cero se protegen explícitamente, de modo que una corrida corta o un escenario sin eventos de cierta clase entregue cero y no un valor indefinido.

**Tabla 3. Indicadores de salida y definición operativa**

| Indicador | Definición | Interpretación |
|---|---|---|
| `TPPL` | `STPL / CTLFin` | tiempo promedio desde creación de lote hasta fin de embalaje |
| `TPPP` | `STPP / CTPFin` | tiempo promedio desde llegada de pedido hasta su último lote embalado |
| `TiempoParadoEtapa[e]` | ociosidad cerrada más ociosidad abierta hasta `TFin` | indisponibilidad por falta de trabajo, por etapa |
| `CostoPromLote` | materia prima por lote más energía y mantenimiento distribuidos | costo productivo medio por lote creado |
| `CostoPromPedido` | costo productivo total distribuido sobre pedidos | costo productivo medio por pedido llegado |
| `DesperfectosEvitadosPorMantenimiento` | `DesEv / CantMan` | efectividad relativa del mantenimiento preventivo |
| `CostoAhorradoPorTCaro[e]` | suma de `CTC/m × TAdicional` | ahorro potencial por evitar franja cara en una etapa |
| `CostoAhorradoPorTCaroTotal` | suma de los cuatro ahorros por etapa | impacto energético agregado |
| `SumTConf` | acumulación de preparaciones | carga temporal por cambios de configuración |
| `CantLotesReProcesados` | conteo de retornos QA → impresión | impacto de no conformidades |

El tiempo parado se calcula para cada etapa como `FTO[e] - ITO[e]`, más el tramo que permanezca abierto al finalizar la simulación para toda máquina cuyo `InicioOcio[e][m]` no sea `HV`. Incluir esta corrección final es necesario: si una máquina queda desocupada antes del fin de la corrida, omitir el tramo abierto subestimaría la ociosidad y sesgaría la comparación entre escenarios.

### Diseño de experimentos, verificación y validación

Una vez implementado el modelo, el experimento debe avanzar en tres niveles. Primero, la **verificación** responde si la lógica programada implementa el modelo conceptual; por ejemplo, si un lote rechazado conserva su pedido y su instante inicial, si las configuraciones se asignan en la etapa correcta y si una máquina ociosa se contabiliza hasta `TFin`. Segundo, la **validación** responde si el modelo es suficientemente representativo para el uso previsto; requiere confrontar sus entradas y salidas con conocimiento experto y, cuando sea posible, con registros históricos [4], [5]. Tercero, la experimentación compara alternativas bajo condiciones controladas.

Los casos de verificación propuestos son: un pedido con un lote y sin interrupciones; un pedido con múltiples lotes; un lote que reprocesa desde QA; una corrida que termina con máquinas ociosas; y escenarios con mantenimiento y desperfecto. Para cada caso se debe disponer de una traza de eventos que permita seguir el reloj, la ubicación del lote, los cambios de cola y las actualizaciones de los contadores. También deben buscarse referencias residuales a índices de etapas inconsistentes y comprobar que QA no reciba relojes de mantenimiento o desperfecto.

Para el análisis estadístico se recomienda realizar múltiples réplicas independientes por escenario, usando semillas controladas y reportando media, desvío estándar e intervalo de confianza de los indicadores principales. El número de réplicas y la longitud de corrida deben determinarse de acuerdo con el objetivo: si se estudia un período finito de planificación, conviene una simulación terminante; si se busca régimen permanente, será necesario analizar período transitorio y condiciones iniciales [5]. En comparaciones pareadas entre políticas, el uso de números aleatorios comunes puede reducir la variabilidad de la diferencia, siempre que se controle cuidadosamente la correspondencia entre las corridas.

**Tabla 4. Escenarios iniciales para la experimentación**

| Escenario | Factores modificados | Hipótesis a contrastar | Indicadores prioritarios |
|---|---|---|---|
| Base | parámetros vigentes | establecer referencia comparable | todos |
| Secuenciación | FIFO, prioridad, por configuración | la menor preparación puede reducir esperas, pero afectar equidad | `TPPL`, `TPPP`, `SumTConf`, ociosidad |
| Capacidad | número de máquinas por etapa | capacidad adicional desplaza o reduce el cuello de botella | colas, `TPPP`, `TiempoParadoEtapa` |
| Energía | `PEFC` verdadero/falso y franjas | ahorrar energía puede aumentar tiempos y acumulación de cola | ahorro, costos, `TPPL`, `TPPP` |
| Mantenimiento | intervalo y costo preventivo | un mantenimiento oportuno reduce fallas costosas | `DesEv/CantMan`, `$TM`, tiempos, costos |
| Calidad | probabilidad de defecto o umbral | más reproceso aumenta carga aguas arriba | reprocesos, `TPPL`, costo y utilización |

> **[Lugar previsto para Figura 5 — Diseño experimental.]** Incluir un diagrama de bloques que relacione los factores controlables (política de cola, cantidad de máquinas, energía, mantenimiento y QA) con las métricas de salida. Se recomienda usar flechas hacia `TPPL`, `TPPP`, costos, ociosidad, reprocesos y ahorro energético.

## Resultados

Al momento de elaboración de este artículo, el modelo posee definidas sus variables de salida y sus fórmulas, pero no se cuenta con una batería de corridas validada ni con resultados numéricos consolidados. En consecuencia, sería metodológicamente incorrecto presentar medias, mejoras porcentuales, gráficos de utilización o conclusiones de superioridad entre políticas. Esta sección establece qué resultados producirá la simulación y cómo deben presentarse cuando se ejecute el diseño experimental de la Tabla 4.

Para cada escenario y réplica se registrarán, como mínimo, los costos promedio por lote y pedido, el tiempo promedio de producción por lote y pedido, el tiempo parado de cada etapa, los desperfectos evitados por mantenimiento, el ahorro por franja cara, el tiempo de preparación acumulado y los lotes reprocesados. La información debe almacenarse además por réplica, no solamente como un promedio global, para poder estimar dispersión e intervalos de confianza. Si la corrida finaliza antes de que todos los pedidos terminen, se deberán informar por separado `CTP` y `CTPFin`, así como `CTL` y `CTLFin`, puesto que los promedios de tiempo se calculan sobre entidades finalizadas mientras algunos costos se distribuyen según entidades llegadas o creadas.

La primera salida a examinar será la evolución temporal de las colas. Una acumulación creciente y persistente en una etapa sugiere que su capacidad efectiva es insuficiente bajo el escenario analizado, aunque no prueba por sí sola que agregar una máquina sea óptimo. La causa puede estar en una duración de proceso, un cambio de configuración frecuente, un mantenimiento programado, una falla, la retención por la franja cara o el reproceso desde QA. Por ello la curva de cola debe acompañarse con los estados de recursos y con los contadores de reproceso y preparación.

> **[Lugar previsto para Figura 6 — Evolución de colas.]** Gráfico de líneas, una curva por cola (`CLM[0]` a `CLM[3]`) contra tiempo de simulación. Para legibilidad, se recomienda un panel por etapa o líneas con patrón distinto en escala de grises. Insertar las bandas o marcas temporales de mantenimiento y de franja cara.

La segunda familia de resultados será el tiempo de producción. `TPPL` muestra la experiencia de un lote individual desde que se crea hasta que termina embalaje, incluyendo esperas, preparaciones, interrupciones y reprocesos. `TPPP`, en cambio, muestra la experiencia del pedido completo y será especialmente sensible a la dispersión entre sus lotes: aunque la mayoría termine rápido, un lote demorado puede prolongar el pedido entero. La diferencia entre ambos indicadores debe analizarse junto con la distribución del tamaño de los pedidos y no como un error del modelo.

> **[Lugar previsto para Figura 7 — Comparación de tiempos por política.]** Diagrama de barras o cajas para `TPPL` y `TPPP` por escenario de secuenciación. Incluir intervalos de confianza o barras de error; no usar sólo promedios si hay varias réplicas.

Los resultados de ociosidad deben leerse por etapa. Un alto `TiempoParadoEtapa` puede significar capacidad ociosa por falta de lotes, pero también puede reflejar que la etapa está aguas abajo de un recurso restrictivo. No debe confundirse con indisponibilidad técnica por falla, ya que el indicador documentado se construye a partir de los intervalos de ociosidad de máquina. El análisis conjunto con la longitud de cola permite distinguir situaciones: cola grande y baja ociosidad apuntan a una estación exigida; cola pequeña y alta ociosidad pueden señalar una restricción previa o sobredimensionamiento local.

> **[Lugar previsto para Figura 8 — Perfil de ociosidad.]** Barras agrupadas con el tiempo parado de impresión, encuadernación, QA y embalaje para cada escenario. Añadir una nota que aclare la definición del indicador y que el mantenimiento se analiza como factor complementario.

La evaluación energética comparará al menos dos políticas: permitir producir en la franja cara y diferir operaciones que comiencen en ella. El resultado no se limitará a `CostoAhorradoPorTCaroTotal`. Deben presentarse simultáneamente el ahorro potencial, `TPPL`, `TPPP`, costo promedio y, cuando sea posible, la cantidad de operaciones diferidas. Si diferir permite ahorro pero desplaza masivamente el inicio de trabajos, podría incrementar las colas y el tiempo de pedido más de lo aceptable. La decisión requiere una frontera de compromiso, no una métrica aislada.

> **[Lugar previsto para Figura 9 — Compromiso energía–servicio.]** Gráfico de dispersión donde el eje horizontal sea `TPPP` y el vertical el costo o ahorro energético. Usar símbolos distintos para `PEFC = verdadero` y `PEFC = falso`; marcar los intervalos de confianza o una región de variabilidad por réplica.

Finalmente, los resultados de mantenimiento deben relacionar la cantidad de intervenciones, su costo, los desperfectos evitados y el desempeño del flujo. Un intervalo preventivo demasiado corto puede incrementar `$TM` y extender relojes con frecuencia; uno demasiado largo puede permitir reparaciones correctivas más extensas. La métrica `DesperfectosEvitadosPorMantenimiento` es útil para detectar el efecto preventivo, pero no decide por sí sola cuál intervalo conviene. La comparación deberá mostrar la combinación de costo, tiempo y producción finalizada.

**Tabla 5. Plantilla de reporte cuantitativo para completar con corridas**

| Escenario | Réplicas | `TPPL` (media ± IC) | `TPPP` (media ± IC) | Costo prom. lote | Ahorro energía | Reprocesos | Ociosidad crítica |
|---|---:|---:|---:|---:|---:|---:|---:|
| Base | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| FIFO | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| Por configuración | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| Franja cara diferida | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |
| Mantenimiento alternativo | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente | pendiente |

La tabla queda intencionalmente sin valores para evitar convertir supuestos de diseño en evidencia empírica. Al completarla, cada resultado debe indicar longitud de corrida, condición inicial, semillas o mecanismo de generación, número de réplicas y criterio de intervalo de confianza.

## Discusión

El modelo propuesto es más rico que los casos elementales de una única cola porque integra una red de recursos, configuraciones, realimentación y eventos de disponibilidad. Esta estructura permite representar interacciones que, de otro modo, se ocultarían. Por ejemplo, una política que favorece conservar la configuración puede disminuir `SumTConf`, pero también demorar lotes con otra configuración y empeorar el tiempo de ciertos pedidos. Una política FIFO puede ser transparente y equitativa en el orden de llegada, pero exigir cambios de configuración más frecuentes. La simulación es particularmente valiosa para estudiar estos intercambios sin interrumpir la operación real [2], [3].

El lazo de reproceso introduce una fuente de carga adicional dependiente de calidad. Aunque la probabilidad de defecto de la especificación actual sea baja, cada lote rechazado vuelve a competir por impresión y puede amplificar las demoras de otros lotes. Por ende, el efecto de calidad no debe medirse sólo como cantidad de defectos; debe observarse cómo modifica la ocupación de los recursos, las colas y el tiempo del último lote de cada pedido. En un escenario con mayor volumen o capacidad ajustada, un cambio pequeño en la tasa de reproceso podría tener una consecuencia desproporcionada.

También es relevante la distinción entre el tiempo promedio por lote y por pedido. El primer indicador es adecuado para describir la circulación de una unidad productiva. El segundo representa mejor una promesa de finalización de un pedido, ya que depende del lote más tardío. Si se tomara el promedio de los tiempos de lote como sustituto del tiempo de pedido, se perdería el efecto de sincronización que aparece cuando los lotes de un mismo pedido terminan en instantes distintos. La estructura `Pedidos[]` incorporada al modelo responde precisamente a este requisito.

La política de energía ilustra una tensión usual entre eficiencia de costo y nivel de servicio. Evitar una franja cara puede ser favorable en términos monetarios, pero la espera agregada se propaga al calendario de eventos. Ese efecto puede ser pequeño si hay holgura de capacidad, o significativo si ocurre cerca de un cuello de botella. La decisión dependerá del valor relativo del ahorro, de la sensibilidad del cliente al plazo y del costo de las colas no representado directamente. Una posible extensión futura es incorporar una función de penalización por demora o compromisos de fecha de entrega, siempre que se recolecten los datos necesarios.

El subsistema de mantenimiento debe interpretarse como una primera aproximación a la confiabilidad de recursos. La regla actual extiende el reloj de finalización de la máquina afectada, con lo cual representa el impacto inmediato de la indisponibilidad. Sin embargo, no distingue entre fallas según carga de trabajo, edad de la máquina, tipo de configuración o severidad, ni modela cuadrillas de mantenimiento como recursos con capacidad limitada. Estas simplificaciones son razonables para el alcance inicial, pero condicionan la validez de recomendaciones sobre políticas de mantenimiento. Antes de trasladar resultados a la planta, será necesario contrastar los intervalos `ID` e `IM`, las duraciones `DD` y `DM` y el modo real en que una interrupción afecta operaciones ya iniciadas.

La calidad de las conclusiones dependerá además de aspectos experimentales. Los números pseudoaleatorios permiten explorar la variabilidad, pero una única corrida no es evidencia suficiente. Las réplicas independientes, la fijación de condiciones iniciales y la cuantificación de incertidumbre son necesarias para distinguir diferencias reales de fluctuaciones muestrales [4], [5]. Cuando los escenarios se comparen con los mismos flujos aleatorios, deberá justificarse el uso de números aleatorios comunes y verificarse que no introduzcan sesgos de implementación.

Existen limitaciones explícitas que deben acompañar cualquier lectura de resultados. El modelo termina en embalaje y no representa inventario de terminados ni despacho; por ello no estima nivel de servicio de distribución. No existe una regla explícita de desempate de eventos simultáneos; esta omisión puede afectar trazas puntuales. Las distribuciones empíricas y paramétricas documentadas requieren validación con datos de operación. QA no posee fallas ni mantenimiento, lo que simplifica el modelo pero puede subestimar sus interrupciones si en la realidad el control utiliza recursos limitados o susceptibles de detención. Identificar estas limitaciones no debilita el estudio: delimita los usos legítimos del modelo y orienta su evolución [1].

## Conclusión

Se documentó una simulación de eventos discretos para una línea editorial multietapa, con pedidos divididos en lotes, recursos múltiples, colas, configuraciones, reproceso por control de calidad, mantenimiento, desperfectos y una política de franja energética cara. El enfoque evento a evento y la explicitación de relojes, entidades, atributos y reglas de transición ofrecen una base reproducible para la implementación y el análisis de escenarios.

El modelo permite medir, dentro de sus límites, tiempo promedio de producción por lote y por pedido, ociosidad por etapa, costos medios de producción, efectividad del mantenimiento, reprocesos, preparación y ahorro potencial por evitar la franja cara. La definición del fin del flujo en embalaje y la conservación de los atributos de pedido durante el reproceso son condiciones centrales para interpretar correctamente los indicadores.

No se presentan conclusiones numéricas porque aún no se ejecutó un conjunto de corridas validado. El siguiente paso es verificar casos controlados, validar entradas y comportamiento con referentes de la operación, y ejecutar réplicas independientes de los escenarios propuestos. Sólo entonces será posible determinar, con intervalos de confianza, qué combinación de secuenciación, capacidad, energía y mantenimiento proporciona el mejor compromiso entre costo, tiempo y desempeño productivo.

## Agradecimientos

Se agradece a la cátedra de Simulación de Sistemas de la Universidad Tecnológica Nacional, Facultad Regional Buenos Aires, por el marco metodológico del trabajo, y a quienes aporten datos operativos de la editorial para la futura validación del modelo.

## Referencias

[1] Alfiero, G. *Modelos y simulación*. Material de cátedra, 2020.

[2] García Sánchez, Á. y Ortega Mier, M. *Introducción a la simulación de sistemas discretos*. Noviembre de 2006.

[3] Schmitt, J. E. *Simulación*. Universidad Tecnológica Nacional, Facultad Regional Buenos Aires, 2003.

[4] Soto Mejía, J. A. *Fundamentos teóricos de simulación discreta*. Universidad Tecnológica de Pereira, 2011.

[5] Urquía Moraleda, A. *Simulación: texto base de teoría*. Universidad Nacional de Educación a Distancia, 2010.

[6] Sandoval Paéz, L. I. *Cuadernillo de simulación*. 2012.

[7] Caselles Moncho, A. *Modelización y simulación de sistemas complejos*. Publicacions de la Universitat de València, 2008. ISBN 978-84-370-7198-5.

[8] Documentación interna del proyecto. *Editorial Matriz Pingüino: descripción de la simulación, variables, eventos y alcance del flujo*. `docs/Docu.md`, consultado en julio de 2026.

[9] Documentación interna del proyecto. *Reporte conceptual del modelo operativo*. `docs/REPORTE_MODELO_OPERATIVO.md`, consultado en julio de 2026.

[10] Documentación interna del proyecto. *Glosario de variables y unidades; cálculos de variables; diagramas de resultados*. `docs/Diagramas/GLOSARIO_VARIABLES.md`, `CALCULOS_VARIABLES.md` y `Resultados.mermaid`, consultados en julio de 2026.

## Datos de contacto

*Pendiente de completar en la versión final: Nombre y Apellido. Universidad Tecnológica Nacional, Facultad Regional Buenos Aires. Dirección postal. E-mail.*

---

### Nota de maquetación para la entrega

El contenido de este archivo está preparado para trasladarse a un documento A4 de dos columnas, márgenes de 2,5 cm y separación entre columnas de 1 cm. Aplicar Times New Roman: título en 16 pt negrita; autores en 14 pt negrita; afiliación en 12 pt negrita cursiva; cuerpo y títulos de secciones en 12 pt según el formato; abstract, palabras clave, agradecimientos, referencias y datos de contacto en 10 pt; notas al pie, si se agregaran, en 9 pt. Mantener las nueve posiciones de figura como notas hasta disponer de las gráficas finales; al incorporarlas, numerarlas secuencialmente de Figura 1 a Figura 9 y conservar títulos descriptivos en 10 pt cursiva.
