def muestrear(rng, cantidad):
    """Seleccion uniforme entre ``config_1`` y ``config_N``."""
    cantidad = int(cantidad)
    if cantidad <= 0:
        raise ValueError("cantidad debe ser mayor que cero.")
    return f"config_{rng.randint(1, cantidad)}"
