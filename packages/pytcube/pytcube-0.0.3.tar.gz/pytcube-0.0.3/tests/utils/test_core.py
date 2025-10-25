import numpy as np

from pytcube.utils.core import find_nearest_indices


def test_find_nearest_indices():
    """Test the function to find the nearest indices in a coordinate array for given observation points."""

    coord_array = np.arange(-179, 181, 2)
    obs_array = np.array([23.12, 46.89, -78.62, -121.97, -179.97, 179.97])

    idx = find_nearest_indices(coord_array, obs_array)
    idx_expected = np.array([101, 113, 50, 29, 0, 179])

    assert np.array_equal(idx, idx_expected)
