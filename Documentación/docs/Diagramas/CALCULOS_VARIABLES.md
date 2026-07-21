# Cálculos de las variables documentadas

Este archivo concentra las fórmulas presentes en los diagramas. Las expresiones marcadas **a validar** reflejan el modelo actual y no implican que su semántica de costos ya esté resuelta.

## Franja cara

Para cada etapa `e` (`0` impresión, `1` encuadernación, `2` QA y `3` embalaje):

```text
si PEFC == true:
    la actividad avanza continuamente
    cada tramo usa la tarifa normal o cara correspondiente
si PEFC == false:
    la actividad solo avanza fuera de la franja cara
    cualquier tramo caro agrega espera calendario
```

`DuracionEtapa` puede ser una preparación `TConf` o una operación `DI`, `DE`, `DQA` o `DEm`. Cuando `PEFC` es falso, ninguna preparación ni producción avanza dentro de la franja cara; una actividad se pausa y continúa fuera de ella.

Cuando una operación se ejecuta, el costo de energía se separa por solapamiento con la franja cara:

```text
SolapeCaro = minutos de la operación que caen dentro de la franja cara
CTPC += (CTC/m) × SolapeCaro
CTPN += (CTN/m) × (DuracionEtapa - SolapeCaro)
```

Si `PEFC` es falso, los minutos bloqueados no consumen energía de producción o configuración ni generan mano de obra de configuración.

```text
CostoAhorradoPorTCaroTotal = sum(CostoAhorradoPorTCaro[0..3])
```

## Costos de producción y mantenimiento

```text
CTEProd = CTPC + CTPN
CTEConfiguracion = energía normal y cara consumida durante TConf
CostoManoObraConfiguracion = sum(TConfEtapa[e] × CMO_configuracion_por_min_etapa[e])
CostoConfiguracion = CTEConfiguracion + CostoManoObraConfiguracion
CTEParado = sum(CTP_parado_por_min_etapa[e] × TiempoParadoEtapa[e] para e en 0..3)
$Fijo = TFin × sum(CFM[e] × CM[e] para e en 0..3)
$TM += $M[i_man]    # al terminar la lógica de un mantenimiento
CostoBase = (CMPxL × CTL) + CTEProd + CTEConfiguracion + CostoManoObraConfiguracion + CTEParado + $Fijo + $TM
CostoDefectosNoDetectados = 3 × CantLotesDefectuososNoDetectados × (CostoBase / CTLFin) si CTLFin > 0; en otro caso 0
CostoTotal = CostoBase + CostoDefectosNoDetectados
CostoPromLote = CostoTotal / CTLFin si CTLFin > 0; en otro caso 0
CostoPromPedido = CostoTotal / CTPFin si CTPFin > 0; en otro caso 0
```

`CTP_parado_por_min_etapa[e]` es el costo de energía en tiempo ocioso por minuto de la etapa `e`. `CFM[e]` es el costo fijo por minuto de una máquina de la etapa `e`. `TiempoParadoEtapa[e]` es el tiempo ocioso total de la etapa `e`, excluyendo mantenimiento y desperfectos.

## Relojes, duraciones y configuración

```text
HoraDia = Mod(T, 1440) / 60
TPI[i]  = T + DI  + TConf
TPE[i]  = T + DE  + TConf
TPQA[i] = T + DQA
TPEm[i] = T + DEm + TConf
```

Cuando la configuración vigente de la máquina coincide con la del lote, `TConf = 0`; en otro caso, `TConf` se obtiene de su procedimiento. La preparación ocurre antes de la producción, consume energía, suma mano de obra y respeta el bloqueo de la franja cara. Al retirar un lote de una cola, se actualizan conjuntamente `CxM[etapa][máquina].lote` y `.config`.

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
