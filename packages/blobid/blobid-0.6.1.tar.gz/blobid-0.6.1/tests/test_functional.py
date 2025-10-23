import numpy as np

import blobid as bi


def test_1d_gap():
    """Make sure that a region of f=0 causes separate blobs"""
    vof = np.array([1.0, 0.75, 0.0, 1.0, 1.0])

    lab_with_normals = bi.get_labels(vof, use_normals=True)
    assert np.all(lab_with_normals == [1, 1, 0, 2, 2])

    lab_with_normals = bi.get_labels(vof, use_normals=True, cutoff=0.8)
    assert np.all(lab_with_normals == [1, 0, 0, 2, 2])

    lab_without_normals = bi.get_labels(vof, use_normals=False)
    assert np.all(lab_without_normals == [1, 1, 0, 2, 2])

    lab_without_normals = bi.get_labels(vof, use_normals=False, cutoff=0.8)
    assert np.all(lab_without_normals == [1, 0, 0, 2, 2])


def test_1d_normals():
    """Test that normals correctly distinguish close blobs in 1D"""
    vof = np.array([1.0, 1.0, 0.25, 0.25, 1.0, 1.0])

    lab_with_normals = bi.get_labels(vof, use_normals=True)
    assert np.all(lab_with_normals == [1, 1, 1, 2, 2, 2])

    lab_without_normals = bi.get_labels(vof, use_normals=False)
    assert np.all(lab_without_normals == [1, 1, 1, 1, 1, 1])


def test_1d_cutoff():
    """Test that cutoff prevents bridging"""
    vof = np.array([0.1, 1.0, 1.0, 0.25, 0.25, 1.0, 1.0, 0.1])

    lab_without_normals = bi.get_labels(vof, use_normals=False, cutoff=0.8, cutoff_method='local')
    assert np.all(lab_without_normals == [0, 1, 1, 0, 0, 2, 2, 0])

    lab_without_normals = bi.get_labels(vof, use_normals=False, cutoff=0.8, cutoff_method='neighbors')
    assert np.all(lab_without_normals == [1, 1, 1, 1, 1, 1, 1, 1])

    vof = np.array([0.1, 0.1, 1.0, 1.0, 0.25, 0.25, 0.25, 1.0, 1.0, 0.1, 0.1])

    lab_without_normals = bi.get_labels(vof, use_normals=False, cutoff=0.8, cutoff_method='local')
    assert np.all(lab_without_normals == [0, 0, 1, 1, 0, 0, 0, 2, 2, 0, 0])

    lab_without_normals = bi.get_labels(vof, use_normals=False, cutoff=0.8, cutoff_method='neighbors')
    assert np.all(lab_without_normals == [0, 1, 1, 1, 1, 0, 2, 2, 2, 2, 0])


def test_neighbors_cutoff():
    """Test some special cases for neighbors-based cutoffs"""

    # make sure zeros aren't considered object cells
    vof = np.array([1, 0])
    lab = bi.get_labels(vof, use_normals=False, cutoff=0.5, cutoff_method='neighbors')
    assert np.all(lab == [1, 0])

    # make sure periodicity works
    vof = np.array([1, 0, 1, 0.25, 0.25])
    lab = bi.get_labels(vof, periodic=(True,), use_normals=False, cutoff=0.5, cutoff_method='neighbors')
    assert np.all(lab == [1, 0, 1, 1, 1])

    vof = np.array([0.25, 1, 0, 1, 0.25])
    lab = bi.get_labels(vof, periodic=(True,), use_normals=False, cutoff=0.5, cutoff_method='neighbors')
    assert np.all(lab == [1, 1, 0, 1, 1])

    vof = np.array([0.25, 0.25, 1, 0, 1])
    lab = bi.get_labels(vof, periodic=(True,), use_normals=False, cutoff=0.5, cutoff_method='neighbors')
    assert np.all(lab == [1, 1, 1, 0, 1])


def test_1d_periodic():
    """Test that a single periodic boundary works in 1D"""
    vof = np.array([1, 0, 1, 0, 1])

    # without periodicity (default behavior)
    labels = bi.get_labels(vof, use_normals=False)
    assert np.all(labels == [1, 0, 2, 0, 3])

    # with periodicity
    labels = bi.get_labels(vof, periodic=(True,), use_normals=False)
    assert np.all(labels == [1, 0, 2, 0, 1])


def test_2d_periodic():
    """Test that periodic boundaries work"""
    vof = np.array(
        [
            [0, 0, 1, 0, 0],
            [1, 0, 0, 0, 1],
            [0, 0, 1, 0, 0],
        ]
    )

    # without periodicity (default behavior)
    labels = bi.get_labels(vof, use_normals=False)
    assert np.all(labels == np.array(
        [
            [0, 0, 1, 0, 0],
            [2, 0, 0, 0, 3],
            [0, 0, 4, 0, 0],
        ]
    ))

    # periodic in x
    labels = bi.get_labels(
        vof, periodic=[True, False], use_normals=False
    )
    assert np.all(labels == np.array(
        [
            [0, 0, 1, 0, 0],
            [2, 0, 0, 0, 3],
            [0, 0, 1, 0, 0],
        ]
    ))

    # periodic in y
    labels = bi.get_labels(
        vof, periodic=[False, True], use_normals=False
    )
    assert np.all(labels == np.array(
        [
            [0, 0, 1, 0, 0],
            [2, 0, 0, 0, 2],
            [0, 0, 3, 0, 0],
        ]
    ))

    # periodic in x and y
    labels = bi.get_labels(
        vof, periodic=[True, True], use_normals=False
    )
    assert np.all(labels == np.array(
        [
            [0, 0, 1, 0, 0],
            [2, 0, 0, 0, 2],
            [0, 0, 1, 0, 0],
        ]
    ))


def test_u_shape():
    """Test of a more complex 2D shape"""
    vof = np.array([[1, 0, 1], [1, 0, 1], [1, 1, 1]])

    for i in range(4):
        lab = bi.get_labels(np.rot90(vof, i), use_normals=True)
        assert np.all(np.rot90(lab, -i) == vof)


def test_odd_label_type():
    vof = np.array([1.0, 0.0, 1.0])

    for label_type in [np.uint32, np.int16]:
        lab = bi.get_labels(vof, use_normals=False, label_type=label_type)

        assert np.all(lab == [1, 0, 2])
        assert lab.dtype == label_type
