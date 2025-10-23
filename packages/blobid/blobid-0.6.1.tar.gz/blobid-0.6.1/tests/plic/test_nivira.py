import warnings

import pytest
import numpy as np
import blobid.plic.nivira as nivira

from blobid._numba_support import numba_availible


def test_WY_Fig2():
    """Figure 2 from Weymouth and Yue"""

    f = np.empty((3, 3, 3))
    for k in range(3):
        f[:, :, k] = np.array([[1.0, 1.0, 0.95],
                               [1.0, 0.9, 0.3],
                               [0.7, 0.15, 0.0]])

    assert nivira._get_dominant_direction(f)[0, 0, 0] == 0

    n = nivira.get_normals(f, f.dtype).squeeze()
    assert n[0] == pytest.approx((1.0-0.15)/2.0)
    assert n[1] == pytest.approx(2.05-1.25)
    assert n[2] == 0


def test_vof_type():
    f = np.random.rand(3, 3, 3)

    # float16 should give a warning
    if numba_availible:
        with pytest.warns():
            nivira.get_normals(f.astype(np.float16), np.float32)

        with pytest.warns():
            nivira.get_normals(f.astype(np.float32), np.float16)

    # float32 and float64 should work without warning
    with warnings.catch_warnings():
        warnings.simplefilter("error")
        nivira.get_normals(f.astype(np.float32), np.float32)
        nivira.get_normals(f.astype(np.float64), np.float32)
