import hashlib

import numpy as np
import blobid as bi


def test_base(fs_vof):
    labels = bi.get_labels(fs_vof, periodic=[True, True, False],
                           use_normals=True)

    hash_object = hashlib.md5(labels.tobytes(order='C'))
    assert hash_object.hexdigest() == 'a8f17199d3bce93bba21ff1196cfe44c'


def test_WY_norm(fs_vof):
    labels = bi.get_labels(fs_vof.astype(np.float32), periodic=[True, True, False],
                           use_normals=True, normals_method='WY')

    hash_object = hashlib.md5(labels.tobytes(order='C'))
    assert hash_object.hexdigest() == 'e315fed4b5074c66a1a98cb65507e724'


def test_no_norm(fs_vof):
    labels = bi.get_labels(fs_vof, periodic=[True, True, False],
                           use_normals=False)

    hash_object = hashlib.md5(labels.tobytes(order='C'))
    assert hash_object.hexdigest() == '57eff32351abdf1640b77c08dfc5f9b0'


def test_cutoff(fs_vof):
    labels = bi.get_labels(fs_vof, periodic=[True, True, False],
                           use_normals=False,
                           cutoff=0.5,
                           cutoff_method='local')

    print(np.unique(labels).size)

    hash_object = hashlib.md5(labels.tobytes(order='C'))
    assert hash_object.hexdigest() == 'ee74eb206e28ec95c8466073b9f06dd6'


def test_Chan(fs_vof):
    labels = bi.get_labels(fs_vof, periodic=[True, True, False],
                           use_normals=False,
                           cutoff=0.5,
                           cutoff_method='neighbors')

    hash_object = hashlib.md5(labels.tobytes(order='C'))
    assert hash_object.hexdigest() == '7045d3492877ca9744e5064267bc20a5'
