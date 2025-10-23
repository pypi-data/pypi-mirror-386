"""
Main solver routine for blobid
"""
from typing import List

import numpy as np

from ._domain import VOFDomain

from . import labeling
from . import plic


def get_labels(
        void_fraction: np.ndarray,
        periodic: List[bool] | None = None,
        cutoff: float = 0.0,
        cutoff_method: str = 'local',
        use_normals: bool = True,
        normals_method: str = 'CD',
        label_type=None
        ) -> np.ndarray:
    r"""
    Calculate unique labels for each connected region of `void_fraction` (blob) on a Cartesian grid.

    Parameters
    ----------
    void_fraction : ndarray
        The void fractions for each grid cell. The number of dimensions specifies the dimensionality of the domain.
        This function can handel 1-D, 2-D, or 3-D domains.
    periodic : 1-D array of bools, optional
        Sets the periodicity of the domain. Default is no direction is periodic.
    cutoff : float, optional
        The minimum value of `void_fraction` for a cell to be in region. Defaults to 0.
    cutoff_method : {'local', 'neighbors'}, optional
        How `cutoff` is applied (see Notes). Defaults to 'local'.
    use_normals : bool, optional
        Whether to use interface normals to determine connectedness. Defaults to True.
    normals_method: {'CD', 'WY'}, optional
        Passed to [plic.get_normals()](blobid/plic.html#get_normals) for calculating interface
        normals.
    label_type : dtype, optional
        Determines the integer data-type of `labels`. Defaults to `numpy.uint32`

    Returns
    -------
        labels : ndarray
            An array of type `label_type` with the same shape as `void_fraction`.

    Raises
    ------
        ValueError
            If the dimensions of `void_fraction` is not 1, 2, or 3.

        OverflowError
            If the number of labels exceeds the capacity of `label_type`.
            Note that the number of intermediate labels can exceed the largest label returned in `labels`

    Notes
    =====

    Object Criteria
    ---------------
    - If `cutoff_method` is `'local'`, a grid cell at :math:`{ijk}` will be an object cell if it's `void_fraction`
    :math:`f_{ijk}` is greater than `cutoff` :math:`f_c`.
    .. math::
        f_{ijk}>f_c

    - If `cutoff_method` is `'neighbors'`, a grid cell at :math:`{ijk}` will be an object cell if it's `void_fraction`
    :math:`f_{ijk}` is non-zero and it or any of its neighbors (6 in 3-D) have a `void_fraction` greater than
    `cutoff`.[1]_
    .. math::
        \Big[f_{ijk}>0\Big] \land
        \Big[ [f_{ijk}>f_{c}] \lor [f_{i+1jk}>f_{c}] \lor [f_{i-1jk}>f_{c}] \lor [f_{ij+1k}>f_{c}] \lor \cdots \Big]

    All object cells will be assigned to a blob.

    Connectivity Criteria
    ---------------------
    In 3-D, each cell has 6 neighbor cells it can be connected to.
    The first requirement for two neighbor cells to be connected is that they are both object cells.
    In addition (unless `use_normals` is False), the interface normals of each cell must not be opposed.[2]_
    Interface normals are calculated using the method set by `normals_method`
    (see [reconstruction.get_normals()](blobid/reconstruction.html#get_normals)).

    Labeling
    --------
    Based on this object and connectivity criteria, labels are assigned to each blob (defined as a connected set
    of object cells) with a two-scan labeling algorithm.[3]_

    Examples
    ========
    A simple 1-D example with four cells:

    >>> import numpy as np
    >>> from blobid import get_labels
    >>> f = np.array([1.0,0.25,0.25,1.0])
    >>> labels = get_labels(f)
    >>> labels
    array([1, 1, 2, 2], dtype=uint32)

    The interface normals in the second and third cell are opposed so they are not connected, and two distinct blobs
    are identified.
    If we set `use_normals` to false, only one blob is identified.

    >>> labels = get_labels(f, use_normals=False)
    >>> labels
    array([1, 1, 1, 1], dtype=uint32)

    We also see only one blob is identified if the domain is periodic because the first and last cells are connected.
    >>> labels = get_labels(f, periodic=(True,))
    >>> labels
    array([1, 1, 1, 1], dtype=uint32)

    If we only want to consider areas where the void fraction is larger than 0.5, we can do this with `cutoff`
    >>> labels = get_labels(f, cutoff=0.5)
    >>> labels
    array([1, 0, 0, 2], dtype=uint32)

    Note that a label of 0 indicates a cell was not assigned to a blob.

    References
    ----------
    .. [1] W. H. R. Chan, M. S. Dodd, P. L. Johnson, P. Moin, "Identifying and tracking bubbles and drops in
       simulations: A toolbox for obtaining sizes, lineages, and breakup and coalescence statistics," Journal of
       Computational Physics, vol. 432, pp. 110156, 2021.
       [10.1016/j.jcp.2021.110156](https://doi.org/10.1016/j.jcp.2021.110156)

    .. [2] K. Hendrickson, G. D. Weymouth & D. K.-P. Yue, "Informed component label algorithm for robust identification
       of connected components with volume-of-fluid method," Computers & Fluids, vol. 197, pp. 104373, 2020.
       [10.1016/j.compfluid.2019.104373](https://doi.org/10.1016/j.compfluid.2019.104373)

    """

    # Defaults
    if label_type is None:
        label_type = np.uint32

    # Setup to domain
    domain = VOFDomain(void_fraction=void_fraction,
                       periodic=periodic if periodic is not None else [False] * void_fraction.ndim,
                       periodic_padding=1,
                       extra_padding=1 if (use_normals or (cutoff_method == 'neighbors')) else 0)

    # calculate object cells
    is_object = _calc_object_cells(domain, cutoff, cutoff_method)

    # calculate connectivity
    if use_normals:
        normals = plic.get_normals(domain.vof(padding=1), normals_method)
    else:
        normals = None

    is_connected = _calc_connections(is_object, norm=normals)

    # do the labeling
    labels = labeling.apply_ccl(
        is_object=is_object,
        is_connected=is_connected,
        periodic=domain.periodic,
        label_type=label_type
        )

    # reshape to original dimensions (removes padding in periodic directions)
    return domain.convert_to_original_shape(labels)


def _calc_object_cells(domain: VOFDomain, cutoff: float, cutoff_method: str) -> np.ndarray:
    """returns an array that is true if cell is an object cell"""

    match cutoff_method:
        case 'local':
            return domain.vof() > cutoff
        case 'neighbors':
            large = domain.vof(padding=1) > cutoff

            large_neighbor = np.logical_or.reduce([
                large[1:-1, 1:-1, 1:-1],  # center
                large[2:,   1:-1, 1:-1],  # i+1
                large[:-2,  1:-1, 1:-1],  # i-1
                large[1:-1, 2:,   1:-1],  # j+1
                large[1:-1, :-2,  1:-1],  # j-1
                large[1:-1, 1:-1, 2:],    # k+1
                large[1:-1, 1:-1, :-2],   # k-1
            ])

            return np.logical_and(large_neighbor, domain.vof() > 0)

        case _:
            raise ValueError(f"cutoff_method '{cutoff_method}' is not supported")


def _calc_connections(is_object: np.ndarray, norm: np.ndarray | None) -> np.ndarray:
    """arr[i,j,k,d] is true if cell [i,j,k] is connected to the neighbor in the negative d direction"""

    # by default, false
    arr = np.zeros((3, is_object.shape[0], is_object.shape[1], is_object.shape[2]), dtype=bool)

    # cell and neighbor must be object cells
    arr[0, 1:, :, :] = is_object[:-1, :, :] & is_object[1:, :, :]
    arr[1, :, 1:, :] = is_object[:, :-1, :] & is_object[:, 1:, :]
    arr[2, :, :, 1:] = is_object[:, :, :-1] & is_object[:, :, 1:]

    # If using normals,
    # not connected if adjacent normals look like | --> | <-- |
    if norm is not None:
        arr[0, 1:, :, :] &= np.logical_or(norm[0, :-1, :, :] <= 0, norm[0, 1:, :, :] >= 0)
        arr[1, :, 1:, :] &= np.logical_or(norm[1, :, :-1, :] <= 0, norm[1, :, 1:, :] >= 0)
        arr[2, :, :, 1:] &= np.logical_or(norm[2, :, :, :-1] <= 0, norm[2, :, :, 1:] >= 0)

    return np.moveaxis(arr, 0, 3)
