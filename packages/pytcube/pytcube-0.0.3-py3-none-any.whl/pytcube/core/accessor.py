from typing import Any, Dict, List, Optional

import xarray as xr
from fast_vindex import patched_vindex

from pytcube.core.point import set_points


@xr.register_dataset_accessor("pytcube")
class PytCubeAccessor:
    def __init__(self, xarray_obj: xr.Dataset):
        """Initialize the PytCube accessor with an xarray Dataset."""
        self._obj = xarray_obj

    def _colocation(
        self,
        point: xr.Dataset,
        search_window: Optional[Dict[str, int]] = None,
        cyclic_dims: List[str] = [],
        grid_prefix: str = "grid_",
        point_prefix: str = "point_",
        fast_vindex: bool = True,
    ):
        """Internal method .colocation()."""
        grid, point = self._obj, point

        grid_dims = grid.dims
        point_dims = (
            point.data_vars
        )  # Permet de connaitre les dimensions de points (avant que soit ajouter les idim, idim_array, ...)

        # On part du postulat que point_dims ne contient que les dimensions à extraire (vérifié dans .colocation())
        # Ajouter des tests pour vérifier que grid et points respecte les specs

        # Default search window: nearest point only
        if search_window is None:
            search_window = {dim: 0 for dim in grid_dims}

        # Check that all point dimensions exist in the grid
        missing_keys = [k for k in point_dims if k not in grid_dims]
        if missing_keys:
            raise ValueError(f"Missing keys in grid dataset: {missing_keys}")

        # Format the point and grid datasets
        point = point.point._format(prefix=point_prefix)
        grid = grid.grid._format(prefix=grid_prefix)

        # Find nearest indices for each point dimension
        for dim in point_dims:
            point[f"{point_prefix}i{dim}"] = point.point._find_nearest_indices(
                grid, dim, grid_prefix, point_prefix
            )

        # Check if the mini-cube is within domain
        for dim in point_dims:
            _min = search_window[dim]
            _max = grid.sizes[f"{grid_prefix}{dim}"] - search_window[dim]

            point[f"{point_prefix}i{dim}_in_domain"] = point.point._in_domain(
                point[f"{point_prefix}i{dim}"], _min, _max
            )

        # Filter points outside the domain
        non_cyclic_dims = [dim for dim in point_dims if dim not in cyclic_dims]
        condition = point[f"{point_prefix}i{non_cyclic_dims[0]}_in_domain"]  # == True
        for dim in non_cyclic_dims[1:]:
            condition &= point[f"{point_prefix}i{dim}_in_domain"]  # == True

        point = point.where(condition, drop=True)

        # Create the i_arrays for indexing
        for dim in point_dims:
            point[f"{point_prefix}i{dim}_array"] = point.point._array(
                point[f"{point_prefix}i{dim}"], f"{dim}_step", search_window[dim]
            )

        # Apply modulo for cyclic dimensions
        for dim in cyclic_dims:

            def modulo(x):
                return x % grid.sizes[f"{grid_prefix}{dim}"]

            # modulo = lambda x: x % grid.sizes[f"{grid_prefix}{dim}"]
            point[f"{point_prefix}i{dim}_array"] = modulo(
                point[f"{point_prefix}i{dim}_array"].astype("int32")
            )

        # Build the indexers dictionary
        indexers = {
            f"{grid_prefix}{dim}": point[f"{point_prefix}i{dim}_array"].astype("int32")
            for dim in point_dims
        }

        # Select data using either fast_vindex or standard indexing
        if fast_vindex:
            with patched_vindex():
                result = grid.isel(**indexers)
        else:
            result = grid.isel(**indexers)

        return result

    def colocation(
        self,
        obs: Optional[Any] = None,
        search_window: Optional[Dict[str, int]] = None,
        cyclic_dims: List[str] = [],
        grid_prefix: str = "grid_",
        point_prefix: str = "point_",
        fast_vindex: bool = True,
        **indexers_kwargs: Any,
    ):
        """
        Select grid data based on provided indices or points.

        Parameters
        ----------
        obs : array-like or None
            Observation indices.
        search_window : dict, optional
            Window size to extract around each point.
        cyclic_dims : list of str
            Dimensions that are cyclic.
        grid_prefix : str
            Prefix used for grid coordinates.
        point_prefix : str
            Prefix used for point coordinates.
        fast_vindex : bool
            Whether to use fast_vindex for indexing.
        **indexers_kwargs : array-like
            Coordinates or indexers to select along each dimension.

        Returns
        -------
        xr.Dataset
            Subset of the grid corresponding to the selected points.
        """

        indexers = indexers_kwargs

        # Check that all indexers exist in the dataset
        for dim in indexers:
            if dim not in self._obj.dims:
                raise ValueError(
                    f"Dimension '{dim}' non présente dans le dataset {list(self._obj.dims)}"
                )

        # Create a points Dataset
        point = set_points(obs=obs, **indexers)

        return self._colocation(
            point,
            search_window=search_window,
            cyclic_dims=cyclic_dims,
            grid_prefix=grid_prefix,
            point_prefix=point_prefix,
            fast_vindex=fast_vindex,
        )
