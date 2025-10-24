import datetime

import numpy as np
import pandas as pd
import xarray as xr


def _narray_datetime(t_min, t_max, size):
    """Generate a NumPy array of random datetime values between t_min and t_max."""
    total_seconds = (t_max - t_min).total_seconds()
    return np.array(
        [
            t_min + datetime.timedelta(seconds=np.random.randint(0, int(total_seconds)))
            for _ in range(size)
        ]
    )


def generate_spatio_temporal_point(
    nobs: int, grid: xr.Dataset, padding: int = 0
) -> xr.Dataset:
    """Generate a spatio-temporal point Dataset with random coordinates within the grid limits."""

    obs = np.arange(nobs)
    coords = {"obs": ("obs", obs)}

    # For each dimension in the grid, generate random values within its limits
    for dim in ["time", "lon", "lat"]:
        d_min = np.sort(grid[dim].values)[padding]
        d_max = np.sort(grid[dim].values)[-(padding + 1)]
        if dim == "time":
            # Convert min and max to datetime
            t_min = pd.to_datetime(d_min)
            t_max = pd.to_datetime(d_max)
            coords["time"] = ("obs", _narray_datetime(t_min, t_max, nobs))
        else:
            coords[dim] = ("obs", np.random.uniform(d_min, d_max, nobs))

    return xr.Dataset(coords=coords)


def generate_point(nobs: int, grid: xr.Dataset, padding: int = 0) -> xr.Dataset:
    """Generate a point Dataset with random coordinates for each grid dimension."""

    obs = np.arange(nobs)
    coords = {"obs": ("obs", obs)}

    # For each grid dimension, generate random coordinates within its limits
    for dim in grid.dims:
        d_min = np.sort(grid[dim].values)[padding]
        d_max = np.sort(grid[dim].values)[-(padding + 1)]
        coords[dim] = ("obs", np.random.uniform(d_min, d_max, nobs))

    return xr.Dataset(coords=coords)
