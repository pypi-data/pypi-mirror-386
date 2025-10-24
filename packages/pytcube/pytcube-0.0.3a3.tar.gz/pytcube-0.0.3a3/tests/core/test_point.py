import numpy as np
import pytest
import xarray as xr

from pytcube.core.point import set_points


def test_set_points_with_lists():
    ds = set_points(obs=[0, 1, 2], lat=[10, 20, 30], lon=[1, 2, 3])
    assert isinstance(ds, xr.Dataset)
    assert np.array_equal(ds.coords["obs"].values, [0, 1, 2])
    assert np.array_equal(ds["lat"].values, [10, 20, 30])
    assert np.array_equal(ds["lon"].values, [1, 2, 3])


def test_set_points_with_numpy_arrays():
    obs = np.array([0, 1])
    lat = np.array([45.0, 46.0])
    lon = np.array([-73.0, -74.0])
    ds = set_points(obs=obs, lat=lat, lon=lon)
    assert isinstance(ds, xr.Dataset)
    assert np.array_equal(ds.coords["obs"].values, obs)
    assert np.array_equal(ds["lat"].values, lat)
    assert np.array_equal(ds["lon"].values, lon)


def test_set_points_with_scalars():
    ds = set_points(obs=0, lat=10, lon=20)
    assert isinstance(ds, xr.Dataset)
    # obs et data_vars doivent être convertis en array de longueur 1
    assert ds.sizes["obs"] == 1
    assert np.array_equal(ds.coords["obs"].values, [0])
    assert np.array_equal(ds["lat"].values, [10])
    assert np.array_equal(ds["lon"].values, [20])


def test_set_points_with_xarray():
    obs = xr.DataArray([0, 1, 2])
    lat = xr.DataArray([10, 20, 30])
    ds = set_points(obs=obs, lat=lat)
    assert isinstance(ds, xr.Dataset)
    assert np.array_equal(ds.coords["obs"].values, [0, 1, 2])
    assert np.array_equal(ds["lat"].values, [10, 20, 30])


def test_set_points_without_obs():
    ds = set_points(lat=[1, 2, 3], lon=[4, 5, 6])
    # obs doit être généré automatiquement
    assert np.array_equal(ds.coords["obs"].values, [0, 1, 2])
    assert np.array_equal(ds["lat"].values, [1, 2, 3])
    assert np.array_equal(ds["lon"].values, [4, 5, 6])


def test_set_points_inconsistent_lengths():
    with pytest.raises(ValueError):
        set_points(obs=[0, 1], lat=[10, 20, 30], lon=[1, 2])
