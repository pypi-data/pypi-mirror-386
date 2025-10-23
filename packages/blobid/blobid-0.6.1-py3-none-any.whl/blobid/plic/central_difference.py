"""
Implementation of simple central differencing for interface reconstruction
"""
import numpy as np
import numpy.typing as npt


def get_normals(f: np.ndarray, normals_dtype: npt.DTypeLike) -> np.ndarray:
    """
    Calculate the sign of the interface normal using central difference
    """

    n = np.empty((3, f.shape[0]-2, f.shape[1]-2, f.shape[2]-2), dtype=normals_dtype)

    n[0] = (f[:-2, 1:-1, 1:-1] - f[2:, 1:-1, 1:-1])/2.0
    n[1] = (f[1:-1, :-2, 1:-1] - f[1:-1, 2:, 1:-1])/2.0
    n[2] = (f[1:-1, 1:-1, :-2] - f[1:-1, 1:-1, 2:])/2.0

    return n
