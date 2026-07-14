def muestrear(rng):
    while True:
        valor = rng.gauss(0.75, 0.05)
        if 0.5 <= valor <= 1:
            return valor
