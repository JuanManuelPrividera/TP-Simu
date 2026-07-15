# Simulación de la Editorial Matriz Pinguino

El programa implementa los flujos de `Diagramas/`: llegadas, cuatro etapas productivas, colas configurables, reproceso desde QA, franja energética, desperfectos y mantenimiento.

## Ejecución

```bash
python3 simulacion.py configuracion.json
python3 simulacion.py configuracion.json --salida resultados.json
```

No requiere dependencias externas. `configuracion.json` contiene todos los parámetros de la corrida:

- `TF`: horizonte de simulación en minutos. Se ejecutan los eventos con instante estrictamente menor que `TF`.
- `CM`: máquinas de impresión, encuadernación, QA y embalaje, en ese orden.
- `configuraciones_iniciales`: configuración inicial de cada máquina en el mismo orden que `CM`; use `null` si no tiene una configuración cargada.
- `ALG`: `FIFO`, `PRIORIDADES` o `POR_CONFIGURACION`.
- `PQA`: umbral de QA. Para cada lote se genera `AQA ~ U(0,1)` y se reprocesa si `AQA > PQA`. Por ejemplo, `0.975` implica aproximadamente 2,5% de reprocesos.
- `cantidad_configuraciones`: cantidad de tipos de configuración posibles. `FDP/TipoConfig.py` genera `config_1..config_N` con probabilidad uniforme.
- `cant_lotes_min` y `cant_lotes_max`: límites enteros de la FDP discreta uniforme de `FDP/CantLotes.py`.
- `semilla`: permite reproducir una corrida; puede eliminarse para usar una semilla no determinística.

Las unidades de tiempos son minutos. Al comienzo se agenda un desperfecto (`ID`) y mantenimiento preventivo (`IM`) para cada máquina mantenible, como fue definido para completar la inicialización. QA queda excluido.

Cada lote equivale a un ejemplar, de modo que se toma `CantLibrosLote = 1`. Las páginas se generan para cada lote con `PaginasLibro`, la FDP definida en los diagramas; ese atributo es el necesario para calcular `DI`.

## FDP

Cada variable aleatoria está aislada en un archivo dentro de `FDP/` (por ejemplo, `FDP/CantLotes.py`, `FDP/AQA.py` y `FDP/DI.py`). Cada archivo ofrece la función `muestrear(rng, ...)`; se puede reemplazar una FDP sin alterar el motor de eventos.

## Nota sobre `TiempoParadoEtapa`

El programa conserva literalmente las asignaciones de `FTO`, `ITO` y la fórmula `FTO - ITO` de `Resultados.mermaid`. Con una corrida que termina mientras una máquina está ocupada, esa fórmula puede producir un valor negativo; es una inconsistencia de los diagramas, no una duración de ociosidad físicamente válida. El resto de los resultados no depende de esa métrica.
