# Plan corregido: Variables resultado del proyecto

## Objetivo

Implementar y documentar las variables resultado necesarias para medir costos, tiempos de produccion, tiempos de maquinas paradas, efectividad del mantenimiento preventivo y ahorro energetico. Este plan corrige el plan anterior segun la revision del estado actual de los diagramas y las decisiones tomadas.

## Decisiones y correcciones respecto del plan anterior

- Energia: se ignora por ahora la inconsistencia detectada entre "ahorro en $" y "tiempo caro evitado". Se mantiene la linea del plan anterior salvo nueva decision posterior.
- Tiempo promedio de lote: no usar `TTFP - TTIP` como mecanismo principal si se va a guardar `lote.t_inicio`. La forma mas directa y menos ambigua sera acumular `STPL += T - lote.t_inicio` cuando termina embalaje, y calcular `TPPL = STPL / CTLFin`.
- Tiempo promedio de pedido: requiere estado por pedido. No alcanza con `TTIP/TTFP`, porque un pedido contiene varios lotes y finaliza cuando termina el ultimo lote. Se debe agregar una estructura explicita para rastrear inicio, cantidad de lotes y lotes terminados por pedido.
- Inicializacion: agregar la inicializacion de todas las variables resultado y acumuladores que hoy se usan o se agregaran.
- Maquinas paradas: mantener el patron existente `ITO[]`/`FTO[]`, pero agregar al cierre de la simulacion el ajuste para maquinas que quedan ociosas hasta el fin.
- Indices de etapas: confirmar y documentar que las etapas productivas son `0..3`: impresion, encuadernacion, QA y embalaje.
- Bug `ITO[4]`: corregirlo a `ITO[3]`. En el estado actual, embalaje usa `CLM[3]`, `CM[3]`, `TPEm` y `FTO[3]`; por lo tanto `ITO[4]` es inconsistente con el resto del modelo.
- Documentacion: actualizar `Docu.md` porque actualmente conserva referencias a arreglos de 5 etapas (`CM[5]`, `CLM[5]`, `TSP[5]`, `TPE[5]`) aunque los diagramas productivos usan 4 etapas.
- Mantenimiento/desperfectos: aclarar que sus indices actuales no coinciden con todos los indices productivos. Mantenimiento usa 3 grupos: `0 = impresion`, `1 = encuadernacion`, `2 = embalaje`. QA queda fuera de mantenimiento/desperfectos en los diagramas actuales.
- Configuracion de maquina: corregir asignaciones de `CxM` que usan el indice de etapa equivocado al pasar lotes entre etapas.

## Variables a agregar o consolidar

### Contadores y costos

- `CTP`: cantidad total de pedidos llegados.
- `CTL`: cantidad total de lotes creados.
- `$TM`: costo total de mantenimiento.
- `CantMan`: cantidad de mantenimientos preventivos.
- `DesEv`: cantidad de desperfectos evitados.

### Tiempos de lotes y pedidos

- `STPL`: sumatoria del tiempo total de produccion de lotes finalizados.
- `CTLFin`: cantidad de lotes finalizados.
- `TPPL`: tiempo promedio de produccion por lote.
- `pedido_id_actual`: identificador incremental de pedidos.
- `Pedidos[pedido_id].t_inicio`: tiempo de llegada del pedido.
- `Pedidos[pedido_id].cant_lotes`: cantidad de lotes del pedido.
- `Pedidos[pedido_id].lotes_finalizados`: cantidad de lotes del pedido que terminaron embalaje.
- `STPP`: sumatoria del tiempo total de produccion de pedidos finalizados.
- `CTPFin`: cantidad de pedidos finalizados.
- `TPPP`: tiempo promedio de produccion por pedido.

### Maquinas paradas

- `ITO[4]`: sumatoria de instantes en los que una maquina productiva pasa a estar ociosa.
- `FTO[4]`: sumatoria de instantes en los que una maquina productiva deja de estar ociosa para volver a producir.
- `InicioOcio[4][CM]`: instante de inicio de ociosidad abierta por maquina productiva. Si vale `HV`, la maquina no esta ociosa.
- `TiempoParadoEtapa[4]`: tiempo total parado por etapa productiva.

### Energia

- `TiempoCaroEvitado[4]`: tiempo evitado en horario caro por etapa productiva, si se conserva la decision del plan anterior.
- `TiempoCaroEvitadoTotal`: sumatoria de `TiempoCaroEvitado`.

## Archivos a modificar

### `docs/Diagramas/ConfigsIniciales.mermaid`

Agregar inicializacion explicita de:

```text
CTP = 0
CTL = 0
$TM = 0
CantMan = 0
DesEv = 0
STPL = 0
CTLFin = 0
STPP = 0
CTPFin = 0
pedido_id_actual = 0
Pedidos = {}
ITO = {0,0,0,0}
FTO = {0,0,0,0}
InicioOcio[etapa][maquina] = 0 para toda maquina productiva
TiempoParadoEtapa = {0,0,0,0}
TiempoCaroEvitado = {0,0,0,0}
```

Tambien revisar si conviene inicializar `TTIP` y `TTFP` en cero para compatibilidad con nombres ya usados, aunque el calculo recomendado para tiempo promedio por lote sera `STPL`.

### `docs/Diagramas/LlegadPedido/LlegadaPedido.mermaid`

- Mantener `CTP++` y `CTL += CantLotes`.
- Agregar `pedido_id_actual++`.
- Crear `Pedidos[pedido_id]` con:
  - `t_inicio = T`
  - `cant_lotes = CantLotes`
  - `lotes_finalizados = 0`
- Crear cada lote con:
  - `config = TipoConfig`
  - `pedido_id = pedido_id_actual`
  - `t_inicio = T`
- Si se mantiene `TTIP`, conservar `TTIP += T * CantLotes` solo como acumulador alternativo/documentado, no como base principal del promedio por lote.

### `docs/Diagramas/embalaje/Embalaje.mermaid`

- Al terminar un lote, antes de liberar o reasignar la embaladora:
  - `lote = CxM[3][i_emb].lote`
  - `STPL += T - lote.t_inicio`
  - `CTLFin++`
  - `Pedidos[lote.pedido_id].lotes_finalizados++`
- Si `Pedidos[lote.pedido_id].lotes_finalizados == Pedidos[lote.pedido_id].cant_lotes`:
  - `STPP += T - Pedidos[lote.pedido_id].t_inicio`
  - `CTPFin++`
- Corregir `ITO[4] += T` a `ITO[3] += T`.
- Mantener, si se desea compatibilidad, `TTFP += T`, pero documentarlo como acumulador alternativo.

### Diagramas de duracion por etapa: `DI`, `DE`, `DQA`, `DEm`

- Si se conserva la metrica de tiempo caro evitado:
  - acumular `TiempoCaroEvitado[etapa] += TAdicional` cuando la etapa cae en horario caro.
  - usar indices productivos:
    - `0 = impresion`
    - `1 = encuadernacion`
    - `2 = QA`
    - `3 = embalaje`

### Diagramas de transicion entre etapas

Corregir asignaciones de configuracion de maquina que apuntan a la etapa equivocada:

- `docs/Diagramas/impresion/Impresion.mermaid`
  - Cambiar `CxM[0][i_enc].config = lote.config` por `CxM[1][i_enc].config = lote.config`.
- `docs/Diagramas/encuadernacion/Encuadernacion.mermaid`
  - Cambiar `CxM[0][i_qa].config = lote.config` por `CxM[2][i_qa].config = lote.config`.
- `docs/Diagramas/qa/QA.mermaid`
  - En paso a embalaje, cambiar `CxM[0][i_emb].config = lote.config` por `CxM[3][i_emb].config = lote.config`.
  - En reproceso a impresion, `CxM[0][i_imp].config = lote.config` es correcto.

### `docs/Diagramas/Resultados.mermaid`

Agregar calculo final con proteccion de division por cero:

```text
CostoPromPedido = CTP > 0 ? $TM / CTP : 0
CostoPromLote = CTL > 0 ? $TM / CTL : 0
TPPL = CTLFin > 0 ? STPL / CTLFin : 0
TPPP = CTPFin > 0 ? STPP / CTPFin : 0
DesperfectosEvitadosPorMantenimiento = CantMan > 0 ? DesEv / CantMan : 0
TiempoCaroEvitadoTotal = sum(TiempoCaroEvitado)
```

Antes de calcular `TiempoParadoEtapa[i]`, cerrar ociosidades abiertas al final:

```text
para cada etapa i:
  TiempoParadoEtapa[i] = FTO[i] - ITO[i]
  para cada maquina j de la etapa i:
    si InicioOcio[i][j] != HV:
      TiempoParadoEtapa[i] += TFin - InicioOcio[i][j]
```

Nota: si no se quiere agregar estructuras nuevas para ociosidades abiertas, al menos documentar que `FTO[i] - ITO[i]` subestima el tiempo parado cuando la simulacion termina con maquinas ociosas.

### `docs/Docu.md`

- Actualizar variables de control/estado para reflejar 4 etapas productivas:
  - `CM[4]`, `CLM[4]`, `CxM[4][CM]`.
- Evitar usar `TPE[5]` como nombre generico de espera porque ya existe `TPE` para encuadernacion. Renombrar esa metrica documentada o aclararla.
- Documentar variables resultado nuevas:
  - `CostoPromPedido`
  - `CostoPromLote`
  - `TPPL`
  - `TPPP`
  - `TiempoParadoEtapa[4]`
  - `DesperfectosEvitadosPorMantenimiento`
  - `TiempoCaroEvitado[4]`
  - `TiempoCaroEvitadoTotal`
- Aclarar mapeo de indices:
  - Productivo: `0 impresion`, `1 encuadernacion`, `2 QA`, `3 embalaje`.
  - Mantenimiento/desperfectos: `0 impresion`, `1 encuadernacion`, `2 embalaje`; QA excluido en el modelo actual.

## Formulas finales

```text
CostoPromPedido = $TM / CTP
CostoPromLote = $TM / CTL
TPPL = STPL / CTLFin
TPPP = STPP / CTPFin
TiempoParadoEtapa[i] = tiempo ocioso cerrado de la etapa i + tiempo ocioso abierto hasta TFin
DesperfectosEvitadosPorMantenimiento = DesEv / CantMan
TiempoCaroEvitadoTotal = sum(TiempoCaroEvitado)
```

Todas las divisiones deben protegerse contra denominador cero.

## Validaciones antes de cerrar implementacion

- Buscar con `rg` que todas las variables nuevas esten inicializadas y usadas.
- Verificar que no queden referencias a `ITO[4]` ni usos de `FTO[4]` para etapas productivas.
- Verificar que las asignaciones `CxM[etapa][i].config` usen la etapa correcta.
- Validar caso minimo: 1 pedido, 1 lote, sin fallas ni mantenimiento.
- Validar pedido con varios lotes: el pedido debe finalizar solo cuando finaliza el ultimo lote.
- Validar reproceso QA: el lote debe conservar `pedido_id` y `t_inicio`.
- Validar mantenimiento con `CantMan > 0`, `$TM > 0` y `DesEv >= 0`.
- Validar simulacion que termina con maquinas ociosas: el tiempo parado debe incluir el tramo hasta `TFin`.

## Dudas pendientes antes de implementar

- Confirmar si la metrica energetica final debe quedar como tiempo evitado o volver al pedido original de ahorro en pesos.
- La implementacion usa `InicioOcio[etapa][maquina]` para representar ociosidades abiertas.

---

# Listado 
Variables de resultado implementadas:

CostoPromPedido: representa cuánto costo de mantenimiento corresponde, en promedio, a cada pedido
recibido durante la simulación. Se calcula distribuyendo el costo total de mantenimiento $TM sobre
la cantidad total de pedidos CTP.

CostoPromLote: representa cuánto costo de mantenimiento corresponde, en promedio, a cada lote
creado. Se calcula distribuyendo $TM sobre la cantidad total de lotes CTL.

TPPL: tiempo promedio de producción por lote. Mide cuánto tarda un lote desde que se crea con su
pedido hasta que termina embalaje. Se calcula con los lotes efectivamente finalizados: STPL /
CTLFin.

TPPP: tiempo promedio de producción por pedido. Mide cuánto tarda un pedido completo desde su
llegada hasta que termina el último lote de ese pedido. Se calcula con los pedidos efectivamente
finalizados: STPP / CTPFin.

TiempoParadoEtapa[4]: tiempo total que las máquinas estuvieron paradas, separado por etapa
productiva. Los índices son: 0 impresión, 1 encuadernación, 2 QA, 3 embalaje. Incluye ociosidades
cerradas durante la simulación y ociosidades que siguen abiertas al finalizar.

DesperfectosEvitadosPorMantenimiento: promedio de desperfectos evitados por cada mantenimiento
preventivo. Representa la efectividad del mantenimiento preventivo. Se calcula como DesEv / CantMan.

TiempoCaroEvitado[4]: tiempo adicional evitado o contabilizado por etapa asociado a operar en
horario de alto costo energético, según la lógica actual de franjas caras. Los índices son los
mismos que en TiempoParadoEtapa.

TiempoCaroEvitadoTotal: suma total del tiempo caro evitado en todas las etapas productivas. Resume
en una sola métrica el impacto energético total medido como tiempo, no como dinero.