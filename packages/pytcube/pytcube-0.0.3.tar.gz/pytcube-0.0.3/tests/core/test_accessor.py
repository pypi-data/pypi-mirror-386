"""
Voici les tests à effectuer:
* [x] Test basic
* [x] Test multiple_points
* [x] Test use obs
* [x] Test search_windows
* [x] Test cyclic_dims
* [x] Test prefix
* [x] Test other dimensions
* [x] Test without fast_vindex
* [x] Test sur N dimensions
* [x] Test Indexation sur 2 dimensions sur 3
"""

import dask.array as da
import numpy as np
import pytest
import xarray as xr

from pytcube.testing import generate_grid


def test_colocation_basic():
    """Test that colocation returns a dataset with expected shape."""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(dim0=3.1, dim1=6.9)
    values = result["var0"].values
    expected = np.array([[["(3, 7)"]]], dtype=object)

    assert isinstance(result, xr.Dataset)
    # Should only return one point
    assert result.sizes["dim0_step"] == 1
    assert result.sizes["dim1_step"] == 1
    assert np.array_equal(values, expected)


def test_colocation_multiple_points():
    """Test multiple points selection."""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(
        dim0=[3.1, 7.2],
        dim1=[6.9, 5.5],
    )
    values = result["var0"].values
    expected = np.array([[["(3, 7)"]], [["(7, 6)"]]], dtype=object)

    assert np.array_equal(values, expected)


def test_colocation_use_obs():
    """Test colocation with obs arg."""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(
        obs=[39, 57],
        dim0=[3.1, 7.2],
        dim1=[6.9, 5.5],
    )
    assert 39 in result.obs.values
    assert 57 in result.obs.values


def test_colocation_search_window():
    """Test search_windows"""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(
        dim0=[3.1, 7.2], dim1=[6.9, 5.5], search_window={"dim0": 1, "dim1": 1}
    )
    values = result["var0"].isel(obs=0).values
    expected = np.array(
        [
            ["(2, 6)", "(2, 7)", "(2, 8)"],
            ["(3, 6)", "(3, 7)", "(3, 8)"],
            ["(4, 6)", "(4, 7)", "(4, 8)"],
        ],
        dtype=object,
    )

    assert np.array_equal(values, expected)


def test_colocation_cyclic_dims():
    """Test cyclic_dims"""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(
        dim0=[0.1, 7.2],
        dim1=[6.9, 0.3],
        search_window={"dim0": 1, "dim1": 1},
        cyclic_dims=["dim0"],
    )

    assert 0 in result.obs.values  # cyclic_dims a fonctionné
    assert (
        1 not in result.obs.values
    )  # l'observation est en dehors du domaine, elle n'est donc pas selectionné.


def test_colocation_prefix():
    """Test point & grid prefix"""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
    result = grid.pytcube.colocation(
        dim0=[3.1, 7.2],
        dim1=[6.9, 5.5],
        grid_prefix="GRD_",
        point_prefix="PNT_",
    )

    assert "GRD_dim0" in result.coords
    assert "PNT_dim0" in result.coords


def test_colocation_other_dimensions():
    """Test colocation with other dimension in grid."""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="dindices", chunks=5)
    grid["other_dim"] = ("other_dim", np.arange(20))
    grid["var1"] = ("other_dim", da.random.random(20, chunks=10))

    result = grid.pytcube.colocation(
        dim0=[3.1, 7.2], dim1=[6.9, 5.5], search_window={"dim0": 1, "dim1": 1}
    )
    result = result.compute()
    assert "grid_other_dim" in result.coords
    assert "var1" in result.data_vars


def test_colocation_without_fast_vindex():
    """Test colocation without fast_vindex."""

    grid = generate_grid(nvar=1, shape=(10, 10), fmt="dindices", chunks=5)
    result = grid.pytcube.colocation(
        dim0=[3.1, 7.2],
        dim1=[6.9, 5.5],
        search_window={"dim0": 1, "dim1": 1},
        fast_vindex=False,
    )
    result = result.compute()
    values = result["var0"].isel(obs=0).values
    expected = np.array(
        [
            ["(2, 6)", "(2, 7)", "(2, 8)"],
            ["(3, 6)", "(3, 7)", "(3, 8)"],
            ["(4, 6)", "(4, 7)", "(4, 8)"],
        ],
        dtype=object,
    )
    assert np.array_equal(values, expected)


class TestColocationNDimensions:
    """Test la colocation sur plusieurs dimension"""

    def test_1D(self):
        grid = generate_grid(nvar=1, shape=(10,), fmt="nindices")
        result = grid.pytcube.colocation(
            dim0=[3.1, 7.2],
            search_window={"dim0": 1},
        )
        assert isinstance(result, xr.Dataset)
        assert True  # juste pour expliciter que le test vérifie l’absence d’erreur

    def test_2D(self):
        grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")
        result = grid.pytcube.colocation(
            dim0=[3.1, 7.2],
            dim1=[6.9, 5.5],
            search_window={"dim0": 1, "dim1": 1},
        )
        assert isinstance(result, xr.Dataset)
        assert True

    def test_3D(self):
        grid = generate_grid(nvar=1, shape=(10, 10, 10), fmt="nindices")
        result = grid.pytcube.colocation(
            dim0=[3.1, 7.2],
            dim1=[6.9, 5.5],
            dim2=[4.6, 2.9],
            search_window={"dim0": 1, "dim1": 1, "dim2": 1},
        )
        assert isinstance(result, xr.Dataset)
        assert True

    def test_4D(self):
        grid = generate_grid(nvar=1, shape=(10, 10, 10, 10), fmt="nindices")
        result = grid.pytcube.colocation(
            dim0=[3.1, 7.2],
            dim1=[6.9, 5.5],
            dim2=[4.6, 2.9],
            dim3=[8.3, 3.5],
            search_window={"dim0": 1, "dim1": 1, "dim2": 1, "dim3": 1},
        )
        assert isinstance(result, xr.Dataset)
        assert True


class TestColocationNotAllDimension:
    """Test la colocation sur des dimensions manquantes"""

    def test_with_narray(self):
        """Test avec des variable de type NumPy array"""
        grid = generate_grid(nvar=1, shape=(10, 10), fmt="nindices")

        result = grid.pytcube.colocation(
            dim0=[3.1, 7.2],
            search_window={"dim0": 1},
        )

        assert "grid_dim1" in result.coords

    def test_with_darray(self):
        """Test avec des variable de type Dask array
        Erreur du à Fast-Vindex, nécéssité de faire évoluer la librairie
        """
        grid = generate_grid(nvar=1, shape=(10, 10), fmt="dindices", chunks=5)

        with pytest.raises(ValueError):
            result = grid.pytcube.colocation(
                dim0=[3.1, 7.2],
                search_window={"dim0": 1},
            )
            assert isinstance(result, xr.Dataset)
