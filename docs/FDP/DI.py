def muestrear(rng, paginas, cant_libros_lote=1):
    base = cant_libros_lote * (paginas / 80)
    return rng.uniform(0.95 * base, 1.05 * base)
