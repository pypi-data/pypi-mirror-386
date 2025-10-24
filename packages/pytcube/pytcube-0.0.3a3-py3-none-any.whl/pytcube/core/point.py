from typing import Optional, Union

import numpy as np
import xarray as xr

from pytcube.utils.core import find_nearest_indices
from pytcube.utils.types import ensure_numpy_array

ArrayLike = Union[xr.DataArray, np.ndarray, list, int, float]


def func_array(values, **kwargs):
    """Generates an array of ranges centered around each value with a specified buffer."""
    return np.array(
        [
            np.arange(value - kwargs["buffer"], value + kwargs["buffer"] + 1)
            for value in values
        ]
    )


def func_in_domain(values, **kwargs):
    """Checks if values are within a specified range."""
    return np.array(
        [((value >= kwargs["min"]) and (value < kwargs["max"])) for value in values]
    )


@xr.register_dataset_accessor("point")
class PointAccessor:
    def __init__(self, xarray_obj: xr.Dataset):
        self._obj = xarray_obj

    def _format(self, prefix):
        vars_renamed = {dim: f"{prefix}{dim}" for dim in self._obj.data_vars}
        _obj = self._obj.rename_vars(vars_renamed)  # rename vars
        return _obj.assign_coords(
            {f"{prefix}{dim}": _obj[f"{prefix}{dim}"] for dim in self._obj.data_vars}
        )

    def _find_nearest_indices(
        self, grid: xr.Dataset, dim: str, grid_prefix: str, point_prefix
    ) -> xr.Dataset:
        """Finds the nearest indices in the grid for the given dimension."""
        coord_array = grid[f"{grid_prefix}{dim}"].values
        random_coords = self._obj[f"{point_prefix}{dim}"].values

        idx_nearest = find_nearest_indices(coord_array, random_coords)

        return xr.DataArray(
            idx_nearest.astype("int32"), dims=["obs"], coords={"obs": self._obj["obs"]}
        )

    def _in_domain(self, dataarray: xr.DataArray, _min: int, _max: int):
        """Checks if the values in a DataArray are within specified minimum and maximum bounds."""
        return xr.apply_ufunc(
            func_in_domain,
            dataarray,
            input_core_dims=[[]],
            output_core_dims=[[]],
            output_dtypes=[bool],
            dask="parallelized",
            kwargs={"min": _min, "max": _max},
        )

    def _array(
        self, dataarray: xr.DataArray, output_core_dims: str, buffer: dict[str, int]
    ):
        """Generates an array of ranges centered around each value with a specified buffer."""
        return xr.apply_ufunc(
            func_array,
            dataarray,
            input_core_dims=[[]],
            output_core_dims=[[output_core_dims]],
            output_dtypes=[int],
            dask_gufunc_kwargs=dict(output_sizes={output_core_dims: 2 * buffer + 1}),
            dask="allowed",
            kwargs={"buffer": buffer},
        ).astype("int32")


def set_points(obs: Optional[ArrayLike] = None, **indexers: ArrayLike) -> xr.Dataset:
    """Create a point Dataset conforming to PytCube specifications.

    The Dataset will have:
        * A coordinate 'obs'
        * Data variables corresponding to the dimensions to index in the datacube
        * No extra data variables beyond the indexed dimensions
    """

    # Convert all indexers to numpy arrays
    indexers = {k: ensure_numpy_array(v) for k, v in indexers.items()}
    if obs is not None:
        obs = ensure_numpy_array(obs)

    # Verify that all indexers have the same length
    lengths = [len(v) for v in indexers.values()]
    if obs is not None:
        lengths.append(len(obs))

    if len(set(lengths)) > 1:
        raise ValueError(f"The lengths of lists/arrays are not identical: {lengths}")

    # Create obs if it is not provided
    n = lengths[0] if lengths else 0
    if obs is None:
        obs = np.arange(n)

    return xr.Dataset(
        coords={"obs": obs}, data_vars={k: ("obs", v) for k, v in indexers.items()}
    )
