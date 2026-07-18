MEDIA_MINUTOS = 6 * 60
DESVIO_MINUTOS = 0.35 * MEDIA_MINUTOS


def muestrear(rng):
    while True:
        intervalo = rng.gauss(MEDIA_MINUTOS, DESVIO_MINUTOS)
        if intervalo > 0:
            return intervalo
