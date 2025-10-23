import pytest as pt
import numpy as np

from blobid.labeling.database import LabelDatabase


def test_label_sets():
    s = LabelDatabase(7)

    # create 7 sets
    for i in range(7):
        assert i+1 == s.get_labels()[i]

    # check they return the right labels
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 4 == s.root(4)
    assert 5 == s.root(5)
    assert 6 == s.root(6)

    # merge two
    assert s.merge(1, 6) == 1
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 4 == s.root(4)
    assert 5 == s.root(5)
    assert 1 == s.root(6)

    # merging the same should not break anything
    assert s.merge(3, 3) == 3
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 4 == s.root(4)
    assert 5 == s.root(5)
    assert 1 == s.root(6)

    # merge two others
    assert s.merge(4, 5) == 4
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 4 == s.root(4)
    assert 4 == s.root(5)
    assert 1 == s.root(6)

    # merge group
    assert s.merge(6, 4) == 1
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 1 == s.root(4)
    assert 1 == s.root(5)
    assert 1 == s.root(6)

    # merge within same group should have no effect
    assert s.merge(5, 1) == 1
    assert 1 == s.root(1)
    assert 2 == s.root(2)
    assert 3 == s.root(3)
    assert 1 == s.root(4)
    assert 1 == s.root(5)
    assert 1 == s.root(6)

    # merge everything
    assert s.merge(2, 3) == 2
    assert s.merge(3, 1) == 1
    assert 1 == s.root(1)
    assert 1 == s.root(2)
    assert 1 == s.root(3)
    assert 1 == s.root(4)
    assert 1 == s.root(5)
    assert 1 == s.root(6)

    assert s.merge(2, 2) == 1


def test_label_sets_failures():
    # cant create labels with a non-integer type
    with pt.raises(AssertionError):
        s = LabelDatabase(20, float)  # noqa: F841

    # test running out of space
    s = LabelDatabase(255, np.uint8)  # noqa: F841

    with pt.raises(OverflowError):
        s = LabelDatabase(256, np.uint8)  # noqa: F841


def test_sequential_labels():
    s = LabelDatabase(20)

    # merge pairs
    for d in range(10):
        assert s.merge(2*d+1, 2*d+2) == 2*d+1

    lookup = s.get_sequential_lookup_table()

    assert lookup[0] == 0
    assert np.unique(lookup[1:]).size == 10

    for lab in range(1, 21):
        assert s.root(lab) == lab if lab % 2 else lab-1
        assert lookup[lab] == (lab-1)//2 + 1


def test_label_sets_types():
    for label_type in [np.uint32, int, np.int16]:
        s = LabelDatabase(20, label_type)

        assert s.label_type == label_type

        for i in range(20):
            new_label = s.get_labels()[i]
            assert i+1 == new_label
            assert np.dtype(label_type) == type(new_label)

        root_label = s.root(4)
        assert np.dtype(label_type) == type(root_label)
