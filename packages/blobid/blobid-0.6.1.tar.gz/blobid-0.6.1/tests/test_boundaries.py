import pytest
import numpy as np

from blobid import plic

from blobid._domain import _pad_array
from blobid.labeling.database import LabelDatabase
from blobid.labeling.labeling import _stitch_boundaries


@pytest.fixture
def vof_3d() -> np.ndarray:
    """Create a dummy VOF array"""
    return np.random.rand(8*7*4).reshape((8, 7, 4))


def check_periodicity(arr, periodicity, depth):
    if periodicity[0] and depth != 0:
        assert np.all(arr[:depth, :, :] == arr[-2*depth:-depth, :, :])
        assert np.all(arr[depth:2*depth, :, :] == arr[-depth:, :, :])

    if periodicity[1] and depth != 0:
        assert np.all(arr[:, :depth, :] == arr[:, -2*depth:-depth, :])
        assert np.all(arr[:, depth:2*depth, :] == arr[:, -depth:, :])

    if periodicity[2] and depth != 0:
        assert np.all(arr[:, :, :depth] == arr[:, :, -2*depth:-depth])
        assert np.all(arr[:, :, depth:2*depth] == arr[:, :, -depth:])


def check_symmetry(arr, symmetry, depth):
    if symmetry[0] and depth != 0:
        assert np.all(arr[:depth, :, :] == np.flip(arr[depth:2*depth, :, :], axis=0))
        assert np.all(arr[-depth:, :, :] == np.flip(arr[-2*depth:-depth, :, :], axis=0))

    if symmetry[1] and depth != 0:
        assert np.all(arr[:, :depth, :] == np.flip(arr[:, depth:2*depth, :], axis=1))
        assert np.all(arr[:, -depth:, :] == np.flip(arr[:, -2*depth:-depth, :], axis=1))

    if symmetry[2] and depth != 0:
        assert np.all(arr[:, :, :depth] == np.flip(arr[:, :, depth:2*depth], axis=2))
        assert np.all(arr[:, :, -depth:] == np.flip(arr[:, :, -2*depth:-depth], axis=2))


def test_pad_array(vof_3d):
    for periodic_size in range(3):
        for extra in range(3):
            for n in range(8):
                per = [bool(n % 2), bool((n//2) % 2), bool((n//4) % 2)]

                arr = _pad_array(vof_3d.copy(), per, periodic_size, extra)

                # make sure dimensions are right
                for d in range(3):
                    assert arr.shape[d] == vof_3d.shape[d]+2*per[d]*periodic_size+2*extra

                # make sure nothing else has changed
                unchanged_range = arr[
                    (per[0]*periodic_size+extra):arr.shape[0]-(per[0]*periodic_size+extra),
                    (per[1]*periodic_size+extra):arr.shape[1]-(per[1]*periodic_size+extra),
                    (per[2]*periodic_size+extra):arr.shape[2]-(per[2]*periodic_size+extra)
                ]
                assert np.all(unchanged_range == vof_3d)

                # check edges
                check_periodicity(arr, per, extra+periodic_size)
                if extra != 0:
                    check_symmetry(arr, [not p for p in per], extra)


def test_stitch_boundaries():  # noqa: C901
    def create_label_field(n):
        sets = LabelDatabase(n[0]*n[1]*n[2])
        labels = np.zeros(n[0]*n[1]*n[2], dtype=sets.label_type)

        labels.flat = sets.get_labels()

        return (labels.reshape(n), sets)

    def check_periodicity(labels, sets, periodicity):
        if periodicity[0]:
            for a, b in zip(labels[1, :, :].flat, labels[-2, :, :].flat):
                assert sets.root(a) == sets.root(b)
        else:
            for a, b in zip(labels[0, :, :].flat, labels[-1, :, :].flat):
                assert sets.root(a) != sets.root(b)

        if periodicity[1]:
            for a, b in zip(labels[:, 1, :].flat, labels[:, -2, :].flat):
                assert sets.root(a) == sets.root(b)
        else:
            for a, b in zip(labels[:, 0, :].flat, labels[:, -1, :].flat):
                assert sets.root(a) != sets.root(b)

        if periodicity[2]:
            for a, b in zip(labels[:, :, 1].flat, labels[:, :, -2].flat):
                assert sets.root(a) == sets.root(b)
        else:
            for a, b in zip(labels[:, :, 0].flat, labels[:, :, -1].flat):
                assert sets.root(a) != sets.root(b)

    for n in range(8):
        per = [bool(n % 2), bool((n//2) % 2), bool((n//4) % 2)]

        (labels, sets) = create_label_field((5+2*per[0], 3+2*per[1], 4+2*per[2]))

        # link
        if per[0]:
            for a, b in zip(labels[0, :, :].flat, labels[1, :, :].flat):
                sets.merge(a, b)
            for a, b in zip(labels[-1, :, :].flat, labels[-2, :, :].flat):
                sets.merge(a, b)

        if per[1]:
            for a, b in zip(labels[:, 0, :].flat, labels[:, 1, :].flat):
                sets.merge(a, b)
            for a, b in zip(labels[:, -1, :].flat, labels[:, -2, :].flat):
                sets.merge(a, b)

        if per[2]:
            for a, b in zip(labels[:, :, 0].flat, labels[:, :, 1].flat):
                sets.merge(a, b)
            for a, b in zip(labels[:, :, -1].flat, labels[:, :, -2].flat):
                sets.merge(a, b)

        sets = _stitch_boundaries(labels, sets, per)

        # make sure the size is right
        assert labels.shape[0] == 5 + 2 * per[0]
        assert labels.shape[1] == 3 + 2 * per[1]
        assert labels.shape[2] == 4 + 2 * per[2]

        check_periodicity(labels, sets, per)


def test_normal_calculation_at_boundaries(vof_3d):
    for n in range(8):
        per = [bool(n % 2), bool((n//2) % 2), bool((n//4) % 2)]
        f = _pad_array(vof_3d.copy(), per, 1, 1)

        # normals should be the same on periodic sides
        n = plic.get_normals(f, normals_method='CD')
        check_periodicity(np.moveaxis(n, 0, 3), per, 1)

        n = plic.get_normals(f, normals_method='WY')
        check_periodicity(np.moveaxis(n, 0, 3), per, 1)
