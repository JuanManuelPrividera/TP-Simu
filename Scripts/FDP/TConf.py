MEDIA = 5.0
DESVIO = 1 / 3
MINIMO = 10 / 3
MAXIMO = 20 / 3


def muestrear(rng):
    while True:
        valor = rng.gauss(MEDIA, DESVIO)
        if MINIMO <= valor <= MAXIMO:
            return valor * 10
