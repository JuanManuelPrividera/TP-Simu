from .DM import muestrear as muestrear_dm


def muestrear(rng):
    return muestrear_dm(rng) + rng.uniform(125, 137.2)
