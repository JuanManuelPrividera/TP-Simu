def muestrear(rng, probabilidad_defecto):
    """Devuelve True si el intento productivo genera un lote defectuoso."""
    return rng.random() < probabilidad_defecto
