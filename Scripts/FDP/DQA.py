from .constantes import LIBROS_POR_LOTE


def muestrear(rng, paginas):
    """Inspecciona todos los libros y páginas del lote."""
    factor_volumen = LIBROS_POR_LOTE * (paginas / 100)
    return factor_volumen * rng.triangular(0.35, 0.4192, 0.3846)
