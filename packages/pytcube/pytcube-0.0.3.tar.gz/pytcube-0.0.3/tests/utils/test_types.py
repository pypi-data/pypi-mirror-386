import numpy as np
import xarray as xr

from pytcube.utils.types import ensure_numpy_array


def test_ensure_numpy_array_from_numpy():
    arr = np.array([1, 2, 3])
    result = ensure_numpy_array(arr)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, arr)


def test_ensure_numpy_array_from_list():
    data = [1, 2, 3]
    result = ensure_numpy_array(data)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, np.array(data))


def test_ensure_numpy_array_from_scalar():
    data = 42
    result = ensure_numpy_array(data)
    assert isinstance(result, np.ndarray)
    assert result.shape == (1,)
    assert result[0] == 42


def test_ensure_numpy_array_from_xarray():
    da = xr.DataArray([1, 2, 3])
    result = ensure_numpy_array(da)
    assert isinstance(result, np.ndarray)
    assert np.array_equal(result, da.values)


def test_ensure_numpy_array_from_nested_list():
    data = [[1, 2], [3, 4]]
    result = ensure_numpy_array(data)
    assert isinstance(result, np.ndarray)
    assert result.shape == (2, 2)
    assert np.array_equal(result, np.array(data))


def test_ensure_numpy_array_from_empty_list():
    data = []
    result = ensure_numpy_array(data)
    assert isinstance(result, np.ndarray)
    assert result.size == 0
