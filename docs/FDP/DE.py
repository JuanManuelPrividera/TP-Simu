from .constantes import LIBROS_POR_LOTE


def muestrear(rng):
    """Duración de encuadernar los 100 libros que componen un lote."""
    return LIBROS_POR_LOTE * rng.triangular(0.11, 0.13, 0.12)
