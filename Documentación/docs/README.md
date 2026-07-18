# Simulación de la Editorial Matriz Pinguino

El programa implementa los flujos de `Diagramas/`: llegadas, cuatro etapas productivas, colas configurables, reproceso desde QA, franja energética, desperfectos y mantenimiento.

## Ejecución

```bash
python3 Scripts/simulacion.py Scripts/config/caso_base.json
python3 Scripts/simulacion.py Scripts/config/caso_base.json --salida Scripts/resultados/resultados.json
python3 Scripts/simulacion.py Scripts/config/casos.json --base Scripts/config/caso_base.json --salida Scripts/resultados/resultados-casos.json
```

Desde la raíz del repositorio también se puede ejecutar la simulación y crear
los gráficos de forma integrada:

```bash
# Ejecuta todos los conjuntos de casos y genera sus gráficos.
python3 Scripts/ejecutar_experimentos.py

# Ejecuta únicamente los conjuntos solicitados.
python3 Scripts/ejecutar_experimentos.py --casos all_cm impresion_cm im

# Limita cada conjunto a cuatro procesos de simulación en paralelo.
python3 Scripts/ejecutar_experimentos.py --trabajadores 4

# Consulta los nombres válidos para --casos.
python3 Scripts/ejecutar_experimentos.py --listar-casos
```

Cada conjunto produce `Scripts/resultados/<conjunto>.json` y sus gráficos en
`Scripts/resultados/graficos/<conjunto>/`. Los conjuntos disponibles son `all_cm`,
`impresion_cm`, `encuadernacion_cm`, `qa_cm`, `embalaje_cm`, `configs`,
`pefc_all_cm` e `im`.

Cada conjunto genera todos los gráficos disponibles. Para las variables que
no aparecen en sus casos se usa el valor de `caso_base.json`; por eso algunos
gráficos pueden tener un único valor en el eje X o dos barras iguales.

Los casos de un conjunto se ejecutan en procesos independientes. Por defecto
se usan los núcleos disponibles; use `--trabajadores 1` para ejecutar en serie
o para limitar el uso de CPU.

No requiere dependencias externas. `configuracion.json` contiene todos los parámetros de la corrida:

- `TF`: horizonte de recepción de pedidos en minutos. Al alcanzarlo no se reciben nuevos pedidos y se vacían las colas y operaciones ya iniciadas hasta terminar todos los lotes.
- `IM`: intervalo fijo entre mantenimientos preventivos, en minutos. Es un parámetro de la configuración de cada caso, no una FDP.
- `CM`: máquinas de impresión, encuadernación, QA y embalaje, en ese orden.
- `configuraciones_iniciales`: configuración inicial de cada máquina en el mismo orden que `CM`; use `null` si no tiene una configuración cargada.
- `ALG`: `FIFO`, `PRIORIDADES` o `POR_CONFIGURACION`.
- `PQA`: umbral de QA. Para cada lote se genera `AQA ~ U(0,1)` y se reprocesa si `AQA > PQA`. Por ejemplo, `0.975` implica aproximadamente 2,5% de reprocesos.
- `cantidad_configuraciones`: cantidad de tipos de configuración posibles. `FDP/TipoConfig.py` genera `config_1..config_N` con probabilidad uniforme.
- `cant_lotes_media` y `cant_lotes_desvio`: media y desvío de la FDP normal discreta truncada de `FDP/CantLotes.py`.
- `costos.CMO_configuracion_por_min_etapa`: costo de mano de obra por minuto de cambio de configuración para impresión, encuadernación, QA y embalaje. QA usa cero porque no requiere configuración.
- `semilla`: permite reproducir una corrida; puede eliminarse para usar una semilla no determinística.

Para ejecutar un experimento, el archivo de casos debe contener una lista `cases`. Cada elemento incluye
`case_id`, una `description` opcional y únicamente los parámetros que sobrescriben a `caso_base.json`, incluido `IM` cuando se quiera evaluar otra frecuencia de mantenimiento.
El programa combina ambas configuraciones, valida el resultado de cada caso y produce un único JSON con
`casos`, donde cada elemento contiene su identificador, descripción y las métricas del experimento.
Si `caso_base.json` está en el mismo directorio que el archivo de casos, `--base` es opcional.

Las unidades de tiempos son minutos. Los cambios de configuración consumen energía con las tarifas normal/cara de su etapa y suman mano de obra. Cuando `PEFC=false`, tanto la configuración como la producción se interrumpen durante la franja cara. Al comienzo se agenda un desperfecto (`ID`) y mantenimiento preventivo a `IM` minutos para cada máquina mantenible; cada mantenimiento posterior conserva ese mismo intervalo configurado. QA queda excluido.

Cada lote equivale siempre a 100 ejemplares (`FDP/constantes.py`). Las páginas se generan una vez por lote con `PaginasLibro`, la FDP definida en los diagramas; los 100 ejemplares del lote se consideran homogéneos y usan esa misma cantidad de páginas. Las duraciones de impresión y QA escalan con las páginas; encuadernación y embalaje escalan con los 100 ejemplares.

## FDP

Cada variable aleatoria está aislada en un archivo dentro de `FDP/` (por ejemplo, `FDP/CantLotes.py`, `FDP/AQA.py` y `FDP/DI.py`). Cada archivo ofrece la función `muestrear(rng, ...)`; se puede reemplazar una FDP sin alterar el motor de eventos.

## Nota sobre `TiempoParadoEtapa`

La ociosidad se acumula por intervalos reales de cada máquina, incluyendo el tramo que permanezca abierto
hasta `TFin`. Por eso `TiempoParadoEtapa` y `TiempoParadoTotal` no pueden resultar negativos.
