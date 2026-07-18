MEDIA_MINUTOS = 24 * 60
DESVIO_MINUTOS = 0.35 * 24 * 60


def muestrear(rng):
    while True:
        intervalo = rng.gauss(MEDIA_MINUTOS, DESVIO_MINUTOS)
        if intervalo > 0:
            return intervalo
