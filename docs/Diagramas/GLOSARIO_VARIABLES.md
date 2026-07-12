# Glosario de variables y unidades

Este glosario fija unidades propuestas para interpretar los diagramas. El costo de producción se compone de materia prima, energía y mantenimiento: `CMPxL × CTL + CTE + $TM`, donde `CTE = CTPC + CTPN`.

## Tiempo, relojes y franja tarifaria

| Variable | Significado y unidad propuesta | Referencias |
|---|---|---|
| `T` | Reloj global de la simulación, en minutos absolutos. | `init/Init.mermaid`, eventos de `LlegadPedido`, `impresion`, `encuadernacion`, `qa`, `embalaje` y `mantenimiento`. |
| `TPLL`, `TPI[]`, `TPE[]`, `TPQA[]`, `TPEm[]`, `TPD[][]`, `TPM[][]` | Relojes del próximo evento de llegada, impresión, encuadernación, QA, embalaje, desperfecto y mantenimiento. Todos en minutos absolutos o `HV`. | `init/MenorTP*.mermaid`, `init/Init.mermaid` y los eventos de cada etapa. |
| `DI`, `DE`, `DQA`, `DEm` | Duraciones de impresión, encuadernación, QA y embalaje, en minutos. | `impresion/DI.mermaid`, `encuadernacion/DE.mermaid`, `qa/DQA.mermaid`, `embalaje/DEm.mermaid`. |
| `HoraDia` | Hora del día derivada de `T`: número real en horas dentro de `[0,24)`. | Las cuatro funciones de duración. |
| `InicioCaro`, `FinCaro` | Límites de la franja cara, en hora del día. | `Docu.md`, las cuatro funciones de duración. |
| `TAdicional` | Espera agregada para no producir durante la franja cara, en minutos. | Las cuatro funciones de duración. |
| `TConf` | Duración de un cambio de configuración, en minutos. | `EncontrarMejorImpresora.mermaid`, `EncontrarMejorEncuadernadora.mermaid`, `EncontrarMejorEmbaladora.mermaid` y las colas de impresión, encuadernación y embalaje. |

## Costos y métricas

| Variable | Significado y unidad propuesta | Referencias |
|---|---|---|
| `CTC/m` | Costo total de producir durante tiempo caro por minuto, en moneda/minuto. Al multiplicarlo por `TAdicional` produce un ahorro monetario. | Las cuatro funciones de duración. |
| `CostoAhorradoPorTCaro[etapa]` | Ahorro acumulado por evitar la franja cara en cada etapa productiva, en moneda. | `ConfigsIniciales.mermaid`, las cuatro funciones de duración y `Resultados.mermaid`. |
| `CostoAhorradoPorTCaroTotal` | Suma del ahorro por franja cara de todas las etapas, en moneda. | `Resultados.mermaid`. |
| `CTE` | Costo total de energía, en moneda: `CTE = CTPC + CTPN`. | `Resultados.mermaid` y las cuatro funciones de duración. |
| `CTPC` / `CTPN` | Costo de energía de producción en período caro / normal, ambos en moneda. | Las cuatro funciones de duración y `Resultados.mermaid`. |
| `$TM` | Costo total de mantenimiento acumulado, en moneda. Es un componente del costo de producción total. | `ConfigsIniciales.mermaid`, `mantenimiento/mantenimiento.mermaid`, `Resultados.mermaid`. |
| `$M[i]` | Costo de ejecutar un mantenimiento de la etapa mantenible `i`, en moneda/mantenimiento. | `mantenimiento/mantenimiento.mermaid`. |
| `CMPxL` | Costo de materia prima por lote, en moneda/lote. | `Resultados.mermaid`. |
| `CostoPromPedido` | Costo total de producción distribuido por pedido: `((CMPxL × CTL) + CTE + $TM) / CTP`, en moneda/pedido. | `Resultados.mermaid`, `Docu.md`. |
| `CostoPromLote` | Costo de materia prima por lote más energía y mantenimiento distribuidos entre lotes: `CMPxL + (CTE + $TM) / CTL`, en moneda/lote. | `Resultados.mermaid`, `Docu.md`. |

## Mantenimiento y desperfectos

QA no tiene desperfectos ni mantenimiento. Por ello los índices `i_des` e `i_man` recorren solamente las etapas mantenibles: `0` impresión, `1` encuadernación y `2` embalaje; no son los índices generales de las cuatro etapas productivas.

| Variable | Significado y unidad propuesta | Referencias |
|---|---|---|
| `ID` | Intervalo hasta el próximo desperfecto de una máquina mantenible, en minutos. | `mantenimiento/desperfecto.mermaid`, `mantenimiento/mantenimiento.mermaid`. |
| `DD` | Duración de un desperfecto, en minutos. | `mantenimiento/desperfecto.mermaid`. |
| `IM` | Intervalo hasta el próximo mantenimiento programado, en minutos. | `mantenimiento/desperfecto.mermaid`, `mantenimiento/mantenimiento.mermaid`. |
| `DM` | Duración de un mantenimiento, en minutos. | `mantenimiento/mantenimiento.mermaid`. |
| `TR[i]` | Tiempo de reparación/acumulado de indisponibilidad de la etapa mantenible `i`, en minutos. | `mantenimiento/desperfecto.mermaid`, `mantenimiento/mantenimiento.mermaid`. |
| `CantMan` | Cantidad de mantenimientos realizados, en mantenimientos. | `ConfigsIniciales.mermaid`, `mantenimiento/mantenimiento.mermaid`, `Resultados.mermaid`. |
| `DesEv` | Cantidad de desperfectos evitados por mantenimiento, en desperfectos. | `ConfigsIniciales.mermaid`, `mantenimiento/mantenimiento.mermaid`, `Resultados.mermaid`. |

## Funciones de densidad de probabilidad (FDP)

`R`, `R1` y `R2` son números pseudoaleatorios independientes con distribución uniforme continua `U(0,1)`. Toda FDP tiene soporte finito: no puede devolver infinito.

| FDP | Distribución / cálculo | Intervalo de salida | Referencia |
|---|---|---|---|
| `IA` | Uniforme estrecha `U(8,5; 9,5)` min; esperanza `9` min. | De `8,5` a `9,5` min. | `FDPs/IA.mermaid` |
| `TipoConfig` | `Femp_config⁻¹(R)`: distribución discreta de las configuraciones observadas (formato, papel, tapa y color). | Conjunto finito de configuraciones registradas; no es numérico. | `FDPs/TipoConfig.mermaid` |
| `CantLotes` | `Femp_copias⁻¹(R)`: distribución discreta de ejemplares por pedido. Un lote equivale a un ejemplar físico. | Enteros entre la menor y mayor cantidad de ejemplares registrada. | `FDPs/CantLotes.mermaid` |
| `PaginasLibro` | Normal truncada, promedio `350` y desvío `83,33`; se rechaza y vuelve a generar si sale del rango. Se redondea al número par más próximo. | Páginas pares entre `100` y `600`. | `FDPs/PaginasLibro.mermaid` |
| `DI` | Uniforme estrecha centrada en `DuracionBaseDI = CantLibrosLote × CantPaginas / 80`. | Desde `95%` hasta `105%` de `DuracionBaseDI`, en min. | `FDPs/DI.mermaid` |
| `DE` | Uniforme estrecha `U(0,11; 0,13)` min; esperanza `0,12` min. | De `0,11` a `0,13` min/lote. | `FDPs/DE.mermaid` |
| `DQA` | Uniforme estrecha `U(0,35; 0,4192)` min; esperanza `0,3846` min. | De `0,35` a `0,4192` min/lote. | `FDPs/DQA.mermaid` |
| `DEm` | Uniforme estrecha `U(0,05; 0,059)` min; esperanza `0,0545` min. | De `0,05` a `0,059` min/lote. | `FDPs/DEm.mermaid` |
| `AQA` | Bernoulli con `p=0,025`: devuelve `1` si el lote es defectuoso y `0` si se aprueba. | `{0,1}`. | `FDPs/AQA.mermaid` |
| `TConf` | Normal truncada con promedio `0,75` y desvío `0,05` min. | De `0,5` a `1` min. | `FDPs/TConf.mermaid` |
| `ID` | Uniforme estrecha `U(2000; 2209,6)` min; esperanza `2104,8` min. | De `2000` a `2209,6` min. | `FDPs/ID.mermaid` |
| `DD` | `DD = DM + U(125; 137,2)` min. Así `DD > DM` siempre y su esperanza es `153,6` min. | De `145` a `162,2` min. | `FDPs/DD.mermaid` |
| `IM` | Uniforme estrecha `U(1451,4; 1571,4)` min; esperanza `1511,4` min. | De `1451,4` a `1571,4` min. | `FDPs/IM.mermaid` |
| `DM` | Uniforme estrecha `U(20; 25)` min; esperanza `22,5` min. | De `20` a `25` min. | `FDPs/DM.mermaid` |

Los cálculos donde intervienen estas variables están reunidos en [CALCULOS_VARIABLES.md](CALCULOS_VARIABLES.md).
