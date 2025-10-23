"""
Calculate the sign of the interface normal based on a 3x3(x3) stencil
"""
import numpy as np
import numpy.typing as npt

from . import analytic_relations

from .central_difference import get_normals as get_normals_CD
from .nivira import get_normals as get_normals_WY


SUPPORTED_METHODS = ['CD', 'WY']
"""Supported methods for calculating interface normals"""


def get_normals(
        void_fraction: np.ndarray,
        normals_method: str = 'CD',
        normals_type: npt.DTypeLike | None = None
) -> np.ndarray:
    r"""
    Calculate the the interface normals :math:`\vec{n}=\vec{n}(f)` using the method specified by `normals_method`

    Parameters
    ----------
    void_fraction : ndarray[ni+2, nj+2, nk+2]
        The void fractions :math:`f` for each grid cell.
    normals_method: {'CD', 'WY'}, optional
        Method used to calculate interface normals. Defaults to 'CD'.
    normals_type: DTypeLike
        Determines the data-type of `normals`. Defaults to same type as `void_fraction`

    Returns
    -------
        normals : ndarray[3, ni, nj, nk]
            `normals[:,i,j,k]` contains :math:`\vec{n}=\langle n_x, n_y, n_z\rangle` for cell `[i,j,k]`.
            :math:`\vec{n}=\langle 0, 0, 0\rangle` indicates the interface in the cell is undefined.

    Methods
    -------
    - If `normals_method` is `CD`, central differencing is used. For example
    .. math::
        n_x = - \frac{f_{i+1} - f_{i-1}}{2}

    - If `normals_method` is `WY`, normals are calculated using the No Inversion VOF Interface Reconstruction Algorithm
    (NIVIRA) described by Weymouth and Yue.[1]_ `WY` is more accurate than `CD` but can be slower
    (especially if not using Numba).

    For simplicity, all methods assume constant grid spacing.


    .. [1] G. D. Weymouth & D. K.-P. Yue, "Conservative Volume-of-Fluid method for free-surface simulations on
       Cartesian-grids," Journal of Computational Physics, vol. 229, pp. 2853--2865, 2010.
       [10.1016/j.jcp.2009.12.018](https://doi.org/10.1016/j.jcp.2009.12.018)

    """
    if normals_type is None:
        normals_type = void_fraction.dtype

    # checks
    assert void_fraction.ndim == 3
    assert all(dim > 2 for dim in void_fraction.shape)

    match normals_method:
        case 'CD':
            return get_normals_CD(void_fraction, normals_type)
        case 'WY':
            return get_normals_WY(void_fraction, normals_type)
        case _:
            raise ValueError(f"normals_method '{normals_method}' is not supported")


def get_alpha(
        void_fraction: np.ndarray,
        normals: np.ndarray
) -> np.ndarray:
    r"""
    Calculate the the interface intercept :math:`\alpha=\alpha(f, \vec{n})` using
    `blobid.plic.analytic_relations`

    Parameters
    ----------
    void_fraction : ndarray[ni, nj, nk]
        The void fractions :math:`f` for each grid cell.
    normals : ndarray[3, ni, nj, nk]
        The interface normals for each cell.

    Returns
    -------
        alpha : ndarray[ni, nj, nk]
            `alpha[i,j,k]` contains :math:`\alpha` for cell `[i,j,k]`.
            If there is no interface or `normals` is undefined in the cell, :math:`\alpha=\text{NaN}`.
    """

    with np.nditer([void_fraction, normals[0, :, :, :], normals[1, :, :, :], normals[2, :, :, :], None],
                   flags=['common_dtype'], op_dtypes=void_fraction.dtype) as itr:
        for f, n1, n2, n3, a in itr:
            if f <= 0 or f >= 1 or (n1 == 0 and n2 == 0 and n3 == 0):
                # alpha is undefined
                a[...] = np.nan
            else:
                a[...] = analytic_relations.inverse_problem(n1, n2, n3, f)

        return itr.operands[-1]


def get_void_fraction(
        alpha: np.ndarray,
        normals: np.ndarray
) -> np.ndarray:
    r"""
    Calculate the the void fraction :math:`f=f(\alpha, \vec{n})` using
    `blobid.plic.analytic_relations`

    Parameters
    ----------
    alpha : ndarray[ni, nj, nk]
        The interface intercept :math:`\alpha` for each grid cell.
    normals : ndarray[3, ni, nj, nk]
        The interface normals for each cell.

    Returns
    -------
        void_fraction : ndarray[ni, nj, nk]
            `void_fraction[i,j,k]` contains :math:`f` for cell `[i,j,k]`.
            If `normals` is undefined in the cell, :math:`f=\text{NaN}`.
    """

    with np.nditer([alpha, normals[0, :, :, :], normals[1, :, :, :], normals[2, :, :, :], None],
                   flags=['common_dtype'], op_dtypes=alpha.dtype) as itr:
        for a, n1, n2, n3, f in itr:
            if np.isnan(a) or (n1 == 0 and n2 == 0 and n3 == 0):
                # void fraction is undefined
                f[...] = np.nan
            else:
                f[...] = analytic_relations.forward_problem(n1, n2, n3, a)

        return itr.operands[-1]
