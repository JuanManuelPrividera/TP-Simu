def muestrear(rng, media, desvio):
    """Normal discreta truncada a tres desvíos estándar de su media."""
    minimo = max(1, round(media - 3 * desvio))
    maximo = round(media + 3 * desvio)
    while True:
        cantidad = round(rng.gauss(media, desvio))
        if minimo <= cantidad <= maximo:
            return cantidad
