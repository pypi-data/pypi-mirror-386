from himena.data_wrappers import wrap_array
import numpy as np
import xarray as xr
import pytest

rng = np.random.default_rng(1234)

@pytest.mark.parametrize(
    "arr",
    [
        rng.integers(0, 255, size=(2, 3, 4), dtype=np.uint8),
        xr.DataArray(rng.integers(0, 255, size=(2, 3, 4), dtype=np.uint8)),
    ]
)
def test_arrays(arr):
    ar = wrap_array(arr)
    assert ar.dtype == np.uint8
    assert ar.ndim == 3
    assert ar.shape == (2, 3, 4)
    assert ar.size == 24
