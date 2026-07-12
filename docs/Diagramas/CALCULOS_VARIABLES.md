# Cálculos de las variables documentadas

Este archivo concentra las fórmulas presentes en los diagramas. Las expresiones marcadas **a validar** reflejan el modelo actual y no implican que su semántica de costos ya esté resuelta.

## Franja cara

Para cada etapa `e` (`0` impresión, `1` encuadernación, `2` QA y `3` embalaje):

```text
HoraDia = Mod(T, 1440) / 60
TAdicional = 0

si InicioCaro < HoraDia <= FinCaro y PEFC == false:
    TAdicional = (FinCaro - HoraDia) × 60
    CostoAhorradoPorTCaro[e] += (CTC/m) × TAdicional
    DuracionEtapa += TAdicional
```

`DuracionEtapa` es respectivamente `DI`, `DE`, `DQA` o `DEm`. La regla se evalúa al inicio de cada operación y difiere la producción hasta el final de la franja cara cuando `PEFC` es falso.

```text
CostoAhorradoPorTCaroTotal = sum(CostoAhorradoPorTCaro[0..3])
```

## Costos de producción y mantenimiento

```text
CTE = CTPC + CTPN
$TM += $M[i_man]    # al terminar la lógica de un mantenimiento
CostoPromLote = CMPxL + ((CTE + $TM) / CTL) si CTL > 0; en otro caso 0
CostoPromPedido = ((CMPxL × CTL) + CTE + $TM) / CTP si CTP > 0; en otro caso 0
```

La expresión por pedido es equivalente a distribuir el costo promedio por lote según la cantidad media de lotes por pedido: `CostoPromPedido = (CTL / CTP) × CostoPromLote`. Esto asume que `CTP` y `CTL` corresponden al mismo alcance temporal de pedidos y lotes.

## Relojes, duraciones y configuración

```text
HoraDia = Mod(T, 1440) / 60
TPI[i]  = T + DI  + TConf
TPE[i]  = T + DE  + TConf
TPQA[i] = T + DQA
TPEm[i] = T + DEm + TConf
```

Cuando la configuración vigente de la máquina coincide con la del lote, `TConf = 0`; en otro caso, `TConf` se obtiene de su procedimiento. Al retirar un lote de una cola, se actualizan conjuntamente `CxM[etapa][máquina].lote` y `.config`.

## Mantenimiento y desperfectos

```text
# Desperfecto
TPD[i_des][j_des] = T + ID
TR[i_des] += DD
TPM[i_des][j_des] = T + IM
reloj_de_la_maquina += DD

# Mantenimiento
CantMan += 1
TPM[i_man][j_man] = T + IM
si TPD[i_man][j_man] < TPM[i_man][j_man]:
    DesEv += 1
TPD[i_man][j_man] = T + ID
TR[i_man] += DM
reloj_de_la_maquina += DM
```

`reloj_de_la_maquina` es `TPI`, `TPE` o `TPEm` según el índice mantenible 0, 1 o 2. QA está excluida de estos cálculos.
