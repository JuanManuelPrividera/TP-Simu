import math


MINIMO = 30.0
MAXIMO = 10_000.0
# Tasa calibrada para que la exponencial truncada tenga E(ID) = 2104.8 min.
TASA = 0.0004590416961886812


def muestrear(rng):
    """Devuelve un intervalo entre fallas en [MINIMO, MAXIMO] minutos."""
    ancho = MAXIMO - MINIMO
    return MINIMO - math.log1p(-rng.random() * -math.expm1(-TASA * ancho)) / TASA
