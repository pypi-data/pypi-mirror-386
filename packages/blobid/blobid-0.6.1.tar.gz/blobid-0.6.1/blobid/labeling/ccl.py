"""
Tools for running connected component labeling
"""

import numpy as np
from .._numba_support import njit
from .database import LabelDatabase, _DatabaseStorage, _merge


def get_temporary_labels(
        is_object: np.ndarray,
        is_connected: np.ndarray,
        label_type
        ) -> tuple[np.ndarray, LabelDatabase]:
    """Perform initial labeling and build the set of label connections"""

    # head cells that have no connections in the negative direction
    is_head = np.logical_and(
        is_object,
        np.logical_not(np.logical_or.reduce(is_connected, axis=3))
    )
    # all other object cells are "tail" cells
    is_tail = np.logical_and(
        is_object,
        np.logical_not(is_head)
    )

    # initialize data types
    label_database = LabelDatabase(label_count=np.count_nonzero(is_head), label_type=label_type)
    labels = np.zeros_like(is_object, dtype=label_database.label_type)

    # First pass: assigning each head cell a label
    labels[is_head] = label_database.get_labels()

    # Second pass : assign labels to "tail" cells and deal with merging
    _tail_pass(labels, label_database.data, is_tail, is_connected)

    return (labels, label_database)


@njit
def _tail_pass(
        labels: np.ndarray,
        data: _DatabaseStorage,
        is_tail: np.ndarray,
        is_connected: np.ndarray
        ):
    """Apply labels to tail cells and deal with merging"""

    neighbor_offsets = [(-1, 0, 0), (0, -1, 0), (0, 0, -1)]
    dummy_label = labels.dtype.type(0)

    for i, j, k in np.ndindex(labels.shape):
        if not is_tail[i, j, k]:
            continue

        new_label = dummy_label

        # look to the connected neighboring cells in the negative directions
        for d, offset in enumerate(neighbor_offsets):
            if is_connected[i, j, k, d]:
                neighbor_label = labels[i+offset[0], j+offset[1], k+offset[2]]

                if new_label == dummy_label:
                    # copy the neighbors label
                    new_label = neighbor_label
                elif new_label != neighbor_label:
                    # merge the two labels
                    new_label = _merge(data, new_label, neighbor_label)

        # set the label
        labels[i, j, k] = new_label
