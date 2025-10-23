"""
Implementation of No Inversion VOF Interface Reconstruction Algorithm (NIVIRA)

Reference
---------

G. D. Weymouth & D. K.-P. Yue, "Conservative Volume-of-Fluid method for free-surface simulations on
Cartesian-grids," Journal of Computational Physics, vol. 229, pp. 2853--2865, 2010.
[10.1016/j.jcp.2009.12.018](https://doi.org/10.1016/j.jcp.2009.12.018)
"""
import warnings
import numpy as np
import numpy.typing as npt

from . import central_difference

from .._numba_support import njit, numba_availible


def get_normals(f: np.ndarray, normals_dtype: npt.DTypeLike) -> np.ndarray:
    """
    Calculate the sign of the interface normal using NIVIRA
    """

    # Numba only supports float32 and float64
    if numba_availible and (f.dtype not in (np.float32, np.float64)):
        warnings.warn(f"void_fraction type {f.dtype.name} not supported, using float32")
        f = f.astype(np.float32)

    if numba_availible and (np.dtype(normals_dtype) not in (np.float32, np.float64)):
        warnings.warn(f"normals_dtype {np.dtype(normals_dtype).name} not supported, using float32")
        normals_dtype = np.float32

    # estimate dominant direction
    d_dom = _get_dominant_direction(f)

    # calculate normals using 3x3x3 stencil described by Weymouth and Yue
    n = np.empty((3, f.shape[0]-2, f.shape[1]-2, f.shape[2]-2), dtype=normals_dtype)

    for d in range(3):
        n[d] = _normals_WY(f, d_dom, d, normals_dtype)

    return n


def _get_dominant_direction(f):
    # estimate the normal using central difference
    n_approx = central_difference.get_normals(f, normals_dtype=f.dtype)

    # cells do not have a normal if empty, full, or undefined CD
    invalid = (f[1:-1, 1:-1, 1:-1] == 0) | (f[1:-1, 1:-1, 1:-1] == 1) | np.all(n_approx == 0, axis=0)

    # calculate the dominant direction, use d_dom=-1 to indicate no valid normal
    d_dom = np.where(invalid, -1, np.argmax(np.abs(n_approx), axis=0))

    return d_dom


@njit
def _normals_WY(f, d_dom, d, dtype) -> np.ndarray:
    n = np.zeros(d_dom.shape, dtype=dtype)

    for i, j, k in np.argwhere(d_dom != -1):
        if d_dom[i, j, k] == d:
            # extract column in direction d
            block = np.swapaxes(f[i:i+3, j:j+3, k:k+3], 0, d)

            # use central difference
            n[i, j, k] = (block[0, 1, 1] - block[2, 1, 1])/2.0

        else:
            # skip the dimension we don't care about
            d_drop = 3 - d - d_dom[i, j, k]
            block = np.take(f[i:i+3, j:j+3, k:k+3], indices=1, axis=d_drop)

            # sum over d_dom
            height = np.sum(block, axis=1 if (d_dom[i, j, k] > d) else 0)

            # central difference of summed columns
            n_tmp = (height[0] - height[2])/2.0

            if abs(n_tmp) < 0.5:
                n[i, j, k] = n_tmp
            else:
                # for steep interface, use one-sided differences
                if n_tmp * f[i+1, j+1, k+1] >= 0:
                    n[i, j, k] = (height[1] - height[2])/1.0
                else:
                    n[i, j, k] = (height[0] - height[1])/1.0

    return n
