"""
Tools for keeping track of blob labels
"""
from collections import namedtuple

import numpy as np

from .._numba_support import njit

_DatabaseStorage = namedtuple('_DatabaseStorage', 'r, n, t')
_END_OF_SET = 0


def _root(data: _DatabaseStorage, x) -> np.uint32 | np.integer:
    return data.r[x]


@njit
def _merge(data: _DatabaseStorage, x, y) -> np.uint32 | np.integer:
    # root of each set
    x_root = data.r[x]
    y_root = data.r[y]

    # do nothing if they have the same roots
    if x_root == y_root:
        return x_root

    # combine the larger labeled set into the smaller one
    if x_root < y_root:
        u = x_root
        v = y_root
    else:
        u = y_root
        v = x_root

    i = v
    while i != _END_OF_SET:
        data.r[i] = u
        i = data.n[i]

    data.n[data.t[u]] = v
    data.t[u] = data.t[v]

    return u


class LabelDatabase:
    """
    Keeps track of which labels have been assigned and can combine the labels into connected sets.

    Reference: [He, Chao and Suzuki 2007.
    *A Linear-Time Two-Scan Labeling Algorithm*](https://doi.org/10.1109/ICIP.2007.4379810).
    """

    def __init__(self, label_count, label_type: type = np.uint32):
        """Create an empty LabelDatabase"""

        assert np.issubdtype(label_type, np.integer), 'label type must be an integer'
        self.label_type = label_type
        """The type used for labels, set by `__init__`"""

        # make sure we wont overflow
        if label_count > np.iinfo(self.label_type).max:
            raise OverflowError(
                "Number of labels exceeds capacity of label_type " + self.label_type.__name__)

        # initialize the database with unconnected labels up to label_count
        self.data = _DatabaseStorage(
            np.arange(label_count+1, dtype=self.label_type),
            np.full(label_count+1, _END_OF_SET, dtype=self.label_type),
            np.arange(label_count+1, dtype=self.label_type)
        )

    def get_labels(self) -> np.ndarray:
        """Return a list of all the labels in the database"""
        return np.arange(1, len(self.data.r), dtype=self.label_type)

    def merge(self, x, y) -> np.integer:
        """
        Join the set containing label `x` and the set containing label `y`

        Returns: the root of the combined set

        """
        return _merge(self.data, x, y)

    def root(self, x) -> np.uint32 | np.integer:
        """Returns the smallest label in the set containing label `x`"""
        return _root(self.data, x)

    def get_sequential_lookup_table(self) -> np.ndarray:
        """
        Get a lookup table for consecutive final labels
        """

        lookup = np.empty_like(self.data.r)

        # for roots, r[i] == i
        root_indices = np.flatnonzero(self.data.r == np.arange(len(self.data.r)))

        # label roots with new consecutive labels
        lookup[root_indices] = np.arange(len(root_indices))

        # For all labels (root and non-root), their root is r[i].
        lookup = lookup[self.data.r]

        return lookup
