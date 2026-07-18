from .constantes import LIBROS_POR_LOTE


def muestrear(rng):
    """Duración de embalar los 100 libros que componen un lote."""
    return LIBROS_POR_LOTE * rng.triangular(0.05, 0.059, 0.0545)
