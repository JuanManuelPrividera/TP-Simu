def muestrear(rng):
    while True:
        paginas = rng.gauss(350, 83.33)
        if 100 <= paginas <= 600:
            return int(2 * round(paginas / 2))
