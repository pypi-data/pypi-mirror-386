import numpy as np
import xarray as xr

# def is_array_like(obj):
#     """Vérifie si un objet est de type list, np.ndarray ou xarray.DataArray."""
#     return isinstance(obj, (list, np.ndarray, xr.DataArray))

# def ensure_array_like(x):
#     """Convertit un scalaire en liste d’un élément si besoin."""
#     if is_array_like(x):
#         return x
#     return [x]


def ensure_numpy_array(x):
    """Converts an array-like object into a np.ndarray."""
    if isinstance(x, np.ndarray):
        return x
    elif isinstance(x, xr.DataArray):
        return x.values
    elif isinstance(x, list):
        return np.array(x)
    else:
        return np.array([x])
