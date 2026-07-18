from .constantes import LIBROS_POR_LOTE

PAGINAS_POR_MINUTO = 100


def muestrear(rng, paginas):
    base = LIBROS_POR_LOTE * (paginas / PAGINAS_POR_MINUTO)
    return rng.triangular(0.95 * base, 1.05 * base, base)
