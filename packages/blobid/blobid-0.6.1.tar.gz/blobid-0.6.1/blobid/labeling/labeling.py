from typing import Tuple

import numpy as np

from .database import LabelDatabase
from .ccl import get_temporary_labels


def apply_ccl(
        is_object: np.ndarray,
        is_connected: np.ndarray,
        periodic: Tuple[bool, bool, bool],
        label_type
) -> np.ndarray:
    r"""
    Given connectedness, calculate unique labels for each connected region of object cells.

    Parameters
    ----------
    is_object : ndarray[ni, nj, nk]
        `is_object[i, j, k]` is true if cell `[i,j,k]` is an object cell
    is_connected : ndarray[ni, nj, nk, 3]
        `is_connected[i, j, k, d]` is true if cell `[i,j,k]` us connected to the neighbor in the negative d direction.
        For example, `is_connected[i, j, k, 0]` is true if cell `[i,j,k]` is connected to cell `[i-1,j,k]`
    periodic: (bool, bool, bool)
        If `periodic[d]`, then cells on each edge in direction `d` are considered the same cell.
        For example, cell `[0,j,k]` is the same as cell `[-1,j,k]` if `periodic[0]` is true.
    label_type : dtype
        Determines the integer data-type of `labels`

    Returns
    -------
        labels : ndarray[ni, nj, nk]
            An array of type `label_type` with the same shape as `is_object`.

    Notes
    -----
    The labeling algorithm used is based on work by He, Chao & Suzuki.[1]_


    .. [1] L. He, Y. Chao & K. Suzuki, "A Linear-Time Two-Scan Labeling Algorithm," IEEE International Conference
       on Image Processing, 2007. [10.1109/ICIP.2007.4379810](https://doi.org/10.1109/ICIP.2007.4379810)

    """
    # checks
    assert is_object.ndim == 3
    assert is_connected.ndim == 4
    assert np.all(is_object.shape == is_connected.shape[:-1])
    assert not np.any(is_connected[0, :, :, 0])
    assert not np.any(is_connected[:, 0, :, 1])
    assert not np.any(is_connected[:, :, 0, 2])

    # do initial labeling
    (labels, label_database) = get_temporary_labels(is_object, is_connected, label_type)

    # stitch together periodic boundaries
    label_database = _stitch_boundaries(labels, label_database, periodic)

    # do final labeling with sequential labels
    labels = label_database.get_sequential_lookup_table()[labels]

    return labels


def _stitch_boundaries(
        labels: np.ndarray,
        sets: LabelDatabase,
        periodic: Tuple[bool, bool, bool]
        ) -> LabelDatabase:
    """Stitch together periodic boundaries and remove padding"""

    if periodic[0]:
        for a, b in zip(labels[0, :, :].flat, labels[-2, :, :].flat):
            sets.merge(a, b)

    if periodic[1]:
        for a, b in zip(labels[:, 0, :].flat, labels[:, -2, :].flat):
            sets.merge(a, b)

    if periodic[2]:
        for a, b in zip(labels[:, :, 0].flat, labels[:, :, -2].flat):
            sets.merge(a, b)

    return sets
