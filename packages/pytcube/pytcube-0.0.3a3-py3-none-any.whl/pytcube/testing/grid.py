from itertools import product
from typing import Optional, Tuple

import dask.array as da
import numpy as np
import pandas as pd
import xarray as xr


def _arange_center(start, stop, size):
    """Generate evenly spaced values centered in each interval."""
    step = (stop - start) / size
    return np.arange(start + step / 2, stop + step / 2, step)


def _narray_indices(shape):
    """Generate a NumPy array containing the index values."""
    narray = np.empty(shape, dtype=object)
    for indices in product(*(range(s) for s in shape)):
        narray[indices] = str(indices)
    return narray


def _narray_random(shape, seed=None):
    """Generate a NumPy array with random values."""
    rs = np.random.default_rng(seed)
    return rs.random(shape)


def _darray_indices(shape, chunks=None):
    """Generate a Dask array containing the index values."""
    narray = _narray_indices(shape)
    darray = da.from_array(narray, chunks=chunks)
    return darray


def _darray_random(shape, chunks=None, seed=None):
    """Generate a Dask array with random values."""
    rs = da.random.RandomState(seed=seed)
    return rs.random(shape, chunks=chunks)
    # return da.random.random(shape, chunks=chunks)


def array(shape, chunks=None, fmt="drandom", seed=None):
    """Generate an array of the requested type and format."""
    if fmt == "nrandom":
        return _narray_random(shape, seed)
    elif fmt == "nindices":
        return _narray_indices(shape)
    elif fmt == "drandom":
        return _darray_random(shape, chunks, seed)
    elif fmt == "dindices":
        return _darray_indices(shape, chunks)
    else:
        raise ValueError(
            f"Format '{fmt}' not recognized. Use 'nrandom', 'nindices', 'drandom', or 'dindices'."
        )


def generate_grid(
    nvar: int,
    shape: Tuple[int, ...],
    chunks=None,
    fmt: str = "random",
    seed: Optional[int] = None,
) -> xr.Dataset:
    """Generate an xarray Dataset with coordinates and random variables."""

    ndim = len(shape)
    dims = [f"dim{i}" for i in range(ndim)]

    ds = xr.Dataset()

    # Create simple coordinates
    for i, size in enumerate(shape):
        ds[dims[i]] = np.arange(size)

    # Create random variables
    for n in range(nvar):
        data = array(shape, chunks, fmt, seed)
        ds[f"var{n}"] = (dims, data)

    return ds


def generate_spatio_temporal_grid(
    nvar: int,
    shape: Tuple[int, int, int],
    chunks=None,
    fmt: str = "random",
    seed: Optional[int] = None,
) -> xr.Dataset:
    """Generate a spatio-temporal xarray Dataset with random variables."""

    # Dimensions and coordinates
    ntime, nlon, nlat = shape
    coords = {
        "time": pd.date_range("2000-01-01", periods=ntime),
        "lon": _arange_center(-180, 180, nlon),
        "lat": _arange_center(-90, 90, nlat),
    }

    dims = ("time", "lon", "lat")

    # Create the Dataset
    ds = xr.Dataset(coords=coords)

    # Add random variables
    for n in range(nvar):
        data = array(shape, chunks, fmt, seed)
        ds[f"var{n}"] = (dims, data)

    return ds
