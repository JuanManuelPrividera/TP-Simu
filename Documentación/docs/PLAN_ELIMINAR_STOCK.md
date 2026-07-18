# Plan para eliminar manejo de stock

Este documento registra el analisis de referencias a stock y la propuesta de refactorizacion. La implementacion ya fue aplicada, pero el archivo queda como registro del plan ejecutado.

Objetivo: no debe quedar ningun registro de manejo de stock en el proyecto, excepto este documento historico del plan.

## Alcance detectado

Referencias directas o relacionadas encontradas:

- `SD[]` / `sd[]`: stock disponible, chequeos y decrementos.
- `SPR[]`: umbral minimo para disparar reposicion.
- `SAR[]`: cantidad repuesta.
- `TPRep[]`: tiempo/evento de reposicion.
- `TPRE`: menor tiempo de reposicion dentro del selector de eventos.
- `i_rep` / `i_repo`: indice de reposicion seleccionada.
- `TOxST[]`: tiempo ocioso por stock/reposicion.
- `FTOxST[]`: no aparece con ese nombre exacto, pero debe verificarse igual antes de cerrar el refactor.
- `Reposicion(i)` / `ActualizarStock[i]`: eventos/procesos de stock.
- `$TRep += $MP[i]`: acumulador/costo asociado a materia prima o reposicion.
- `SI[]`, `$SI`, `$MP[]`: inicializacion/costo de insumos.
- `initial_stock`: configuracion inicial de stock en YAML.
- `materials`: modelo completo de materiales en YAML, tanto por etapa como en seccion global.
- `reorder_point`: punto de reposicion en YAML.
- `replenishment_quantity`: cantidad de reposicion en YAML.
- `consumption_per_lot`: consumo por lote en YAML.
- `lead_time`: tiempo de entrega/reposicion en YAML.
- Texto conceptual: `stock`, `insumos`, `materia prima`, `reposicion`.

## Orden recomendado

1. Sacar el evento de reposicion del ciclo principal.
2. Eliminar los diagramas dedicados a stock/reposicion.
3. Limpiar condiciones y consumos de stock en los diagramas productivos.
4. Limpiar variables, documentacion y configuracion.
5. Verificar con busquedas globales que no quede ningun rastro fuera de este archivo.

## 1. Ciclo principal de eventos

### `docs/Diagramas/init/Init.mermaid`

Referencias actuales:

- Incluye `Repo{{Menor TPRE}}` en la inicializacion de eventos.
- Despues de mantenimiento evalua `EsRepoMenor`.
- Si `EsRepoMenor` devuelve true, llama `ActualizarStock[i_rep]`.

Refactor propuesto:

- Quitar `Repo{{Menor TPRE}}` de la cadena inicial.
- Eliminar el bloque `EsRepoMenor -> if9 -> ActualizarStock[i_rep]`.
- El flujo debe terminar si no hay llegada, impresion, encuadernacion, QA, embalaje, desperfecto ni mantenimiento pendientes.
- Si el diagrama necesita cierre explicito, conectar el `no` de mantenimiento a `fin`.

### `docs/Diagramas/init/EsRepoMenor.mermaid` APROBADO

Referencia actual:

- `EsRepoMenor` siempre devuelve `bool = true`.

Refactor propuesto:

- Eliminar el archivo completo, porque representa exclusivamente seleccion de evento de reposicion.

### `docs/Diagramas/init/MenorTPRE.mermaid` APROBADO

Referencias actuales:

- Calcula `TPRE` recorriendo `TPRep[i]`.
- Setea `i_repo`.

Refactor propuesto:

- Eliminar el archivo completo.
- Eliminar cualquier mencion a `TPRE`, `TPRep`, `i_rep` e `i_repo` en otros diagramas.

### `docs/Diagramas/init/Es*Menor.mermaid` APROBADO

Archivos afectados:

- `EsLlegadaMenor.mermaid`
- `EsImpresionMenor.mermaid`
- `EsEncuadernadoMenor.mermaid`
- `EsQAMenor.mermaid`
- `EsEmbalajeMenor.mermaid`
- `EsDesperfectoMenor.mermaid`
- `EsMantenimientoMenor.mermaid`

Referencias actuales:

- Comparan eventos contra `TPRE`, por ejemplo `TPLL < ... && TPLL < TPRE`.

Refactor propuesto:

- Sacar `&& ... < TPRE` de todas las comparaciones.
- Dejar `EsMantenimientoMenor` con una condicion concreta, porque actualmente solo compara `TPM < TPRE`.
- Como mantenimiento queda ultimo en la cadena de seleccion, `EsMantenimientoMenor` debe devolver true si hay un mantenimiento pendiente, por ejemplo `TPM < HV` o `TPM != HV`.
- En `Init.mermaid`, si `EsMantenimientoMenor` devuelve false, el flujo debe ir a `fin` de forma explicita.

## 2. Diagramas dedicados a stock APROBADO

### `docs/Diagramas/stock/ActualizarStock.mermaid`

Referencias actuales:

- `ActualizarStock[i]`
- `T = TPRep[i]`
- `SD[i] += SAR[i]`
- Chequeos `SD[x] > 0`
- Consumos `SD[x] -= 1`
- Chequeo `SD[i] <= SPR[i]`
- Agenda `TPRep[i] = T + TR` o `TPRep[i] = HV`

Refactor propuesto:

- Eliminar el archivo completo.
- No hay una version util sin stock, porque su responsabilidad completa es reponer insumos y desbloquear colas por stock.

### `docs/Diagramas/stock/reposicion.mermaid` APROBADO

Referencias actuales:

- `Reposicion[i]`
- `TPRep[i]`
- `TOxST[i]`

Refactor propuesto:

- Eliminar el archivo completo.
- `TOxST[]` desaparece junto con el evento de reposicion.
- Si aparece `FTOxST[]` en una busqueda posterior, eliminarlo bajo el mismo criterio.

## 3. Diagramas productivos

### `docs/Diagramas/LlegadPedido/EncontrarMejorImpresora.mermaid` APROBADO

Actual:

- `TPI[i_imp] == HV && SD[0] > 0`

Refactor:

- Dejar solo disponibilidad de maquina: `TPI[i_imp] == HV`.

### `docs/Diagramas/LlegadPedido/LlegadaPedido.mermaid` APROBADO

Actual:

- Al iniciar impresion consume `SD[0] -= 1`.
- Acumula `$TRep += $MP[0]`.
- Chequea `SD[0] <= SPR[0]`.
- Llama `Reposicion(0)`.

Refactor:

- Quitar el nodo de consumo/costo de materia prima.
- Conectar directamente `DI` con la asignacion de `TPI[i_imp]`.
- Eliminar el bloque de chequeo `SD[0] <= SPR[0]` y llamada `Reposicion(0)`.
- Si `$TRep` era costo de reposicion o materia prima, eliminarlo. Si era costo total general mal nombrado, renombrarlo en un refactor separado.

### `docs/Diagramas/impresion/EncontrarMejorEncuadernadora.mermaid` APROBADO

Actual:

- `TPE[i_enc] == HV && SD[1] > 0`

Refactor:

- Dejar `TPE[i_enc] == HV`.

### `docs/Diagramas/impresion/Impresion.mermaid` APROBADO

Actual:

- Consume `SD[1]` al pasar a encuadernacion.
- Acumula `$TRep += $MP[1]`.
- Condicion `CLM[0].size() > 0 && SD[0] > 0`.
- Consume `SD[0]`.
- Subgraph `Reponer stock`.
- Chequea `SPR[0]`, `SPR[1]`.
- Llama `Reposicion(0)` y `Reposicion(1)`.

Refactor:

- Quitar nodos de consumo/costo de materia prima.
- Cambiar la condicion a `CLM[0].size() > 0`.
- Eliminar el subgraph `Reponer stock` completo.
- La transicion de impresion a encuadernacion debe depender solo de cola, disponibilidad de encuadernadora y tiempos.

### `docs/Diagramas/encuadernacion/Encuadernacion.mermaid` APROBADO

Actual:

- `CLM[1].size() > 0 && SD[1] > 0`.
- Consume `sd[1] -= 1`.
- Acumula `$TRep += $MP[1]` duplicado.
- Subgraph `Reponer stock`.
- Chequea `SPR[1]`.
- Llama `Reposicion(1)`.

Refactor:

- Cambiar la condicion a `CLM[1].size() > 0`.
- Quitar el nodo de consumo/costo.
- Eliminar el subgraph `Reponer stock` completo.
- La inconsistencia `sd` minuscula desaparece al eliminar la referencia.

### `docs/Diagramas/qa/EncontrarMejorEmbaladora.mermaid` APROBADO

Actual:

- `TPEm[i_emb] == HV && SD[2] > 0`

Refactor:

- Dejar `TPEm[i_emb] == HV`.

### `docs/Diagramas/qa/QA.mermaid` APROBADO

Actual:

- Reproceso a impresion consume `SD[0]`.
- Acumula `$TRep += $MP[0]`.
- Paso a embalaje consume `sd[2]`.
- Acumula `$TRep += $MP[2]`.
- Subgraph `Reponer stock`.
- Chequea `SPR[0]`, `SPR[2]`.
- Llama `Reposicion(0)`, `Reposicion(2)`.

Refactor:

- Quitar consumos/costos de materia prima.
- El reproceso debe agendar impresion sin depender de insumos.
- Conectar `DEm` directo con asignacion de `TPEm`.
- Eliminar el subgraph `Reponer stock` completo.

### `docs/Diagramas/embalaje/Embalaje.mermaid` APROBADO

Actual:

- `CLM[3].size() > 0 && SD[2] > 0`.
- Consume `sd[2]`.
- Acumula `$TRep += $MP[2]`.
- Subgraph `Reponer stock`.
- Chequea `SPR[2]`.
- Llama `Reposicion(2)`.

Refactor:

- Cambiar la condicion a `CLM[3].size() > 0`.
- Quitar consumo/costo.
- Conectar `DEm` directo con la asignacion de `TPEm[i_emb]`.
- Eliminar el subgraph `Reponer stock` completo.

## 4. Configuracion inicial y costos de insumos

### `docs/Diagramas/ConfigsIniciales.mermaid` APROBADO

Actual:

- `SI[3] = {10,10,10}`
- `$SI = SI[0].$MP[0] + SI[1].$MP[1] + SI[2].$MP[2]`

Refactor:

- Eliminar `SI`, `$SI` y `$MP` si estan ligados a materia prima/stock.
- Mantener solo inicializacion de variables no relacionadas con insumos.

## 5. Documentacion APROBADO

### `docs/Docu.md`

Referencias actuales:

- Menciona `disponibilidad de insumos`.
- Menciona `stock aislado`.
- Define `DR[3]`.
- Define `SAR[3]`.
- Define `SPR[5]`.
- Define `SD[5]`.
- Incluye `TPRep[4]`.
- La tabla de eventos tiene condiciones con `SD[]`, `SPR[]` y filas de `Reposicion`.

Refactor:

- Reescribir la descripcion para que la simulacion no dependa de insumos ni abastecimiento.
- Quitar la comparacion con `stock aislado` o reemplazarla por otra complejidad no relacionada.
- Eliminar `DR[3]`, `SAR[3]`, `SPR[5]`, `SD[5]` y `TPRep[4]`.
- Sacar todas las condiciones `SD[x] > 0`.
- Eliminar filas `Reposicion[0]`, `Reposicion[1]`, `Reposicion[2]`, `Reposicion[n]`.
- Ajustar condiciones de impresion, encuadernacion y embalaje para depender solo de colas, maquinas libres y reglas de proceso.
- Reescribir las tablas de transicion para que no queden eventos de reposicion ni condiciones por insumos.
- Revisar que no queden menciones conceptuales a disponibilidad de insumos, materia prima, abastecimiento, stock o reposicion.

### `docs/DUDAS_VALIDACION.md`

Referencias actuales:

- Pregunta por cantidad de recursos/maquinas/colas/stock.
- Pregunta como consumir y reponer stock.

Refactor:

- Quitar la parte de stock de la primera duda o eliminar la duda si ya no aplica.
- Eliminar la duda sobre consumo y reposicion de stock.

## 6. Config YAML APROBADO

Archivos afectados:

- `config/default.yaml`
- `config/fifo.yaml`
- `config/priority.yaml`
- `config/booktype.yaml`
- `config/8h-windows.yaml`
- `config/template.yaml`

Actual:

- Cada config tiene claves `initial_stock` dentro del modelo de materiales.
- Cada config tiene claves `materials` dentro de etapas o maquinas, por ejemplo listas de materiales consumidos por etapa.
- Cada config tiene una seccion global `materials` con campos de stock/reposicion.
- Los campos asociados incluyen `reorder_point`, `replenishment_quantity`, `consumption_per_lot` y `lead_time`.

Refactor:

- Eliminar todas las claves `initial_stock`.
- Eliminar todas las claves `materials` dentro de etapas, maquinas o procesos.
- Eliminar la seccion global `materials` completa.
- Eliminar todos los campos asociados al modelo de stock: `reorder_point`, `replenishment_quantity`, `consumption_per_lot` y `lead_time`.
- Si existe luego codigo lector de config o schema, ajustarlo para que no espere ninguna estructura de materiales.

## 7. Verificacion final propuesta

Despues de aplicar cambios, correr:

```powershell
rg -n -i "stock|reposicion|reposición|SD\[|sd\[|SPR\[|SAR\[|TPRep\[|TPRE|i_rep|i_repo|TOxST\[|FTOxST\[|ActualizarStock|initial_stock|materials|reorder_point|replenishment_quantity|consumption_per_lot|lead_time|insumo|insumos|materia prima|\$TRep|\$MP|SI\[" . -g "!docs/PLAN_ELIMINAR_STOCK.md"
```

La meta es que esta busqueda no devuelva referencias de manejo de stock fuera de este plan. Si aparecen falsos positivos en historial, nombres no relacionados o comentarios necesarios, se deben revisar manualmente antes de considerar cerrada la eliminacion.

## Nota sobre estado del repositorio

Al momento del analisis el worktree ya tenia cambios previos:

- Archivos eliminados bajo `docs/Diagramas`.
- `docs/Diagramas/impresion/Impresion.mermaid` modificado.
- Nuevas carpetas bajo `docs/Diagramas/mantenimiento/` y `docs/Diagramas/stock/`.

La implementacion futura debe trabajar con esos cambios existentes y no revertirlos sin autorizacion explicita.
