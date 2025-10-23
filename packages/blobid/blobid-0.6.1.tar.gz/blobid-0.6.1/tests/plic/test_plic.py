import hashlib

import pytest

import numpy as np
import blobid.plic as plic


def test_undefined_normals():
    """Tests where normal should be all zeros (undefined)"""

    def assert_undefined(norm):
        n = norm.squeeze()
        assert n[0] == 0
        assert n[1] == 0
        assert n[2] == 0

    # all zeros
    f = np.zeros((3, 3, 3))
    for method in plic.SUPPORTED_METHODS:
        assert_undefined(plic.get_normals(f, method))

    # all ones
    f = np.ones((3, 3, 3))
    for method in plic.SUPPORTED_METHODS:
        assert_undefined(plic.get_normals(f, method))

    # any value in a range between 0 and 1
    for _ in range(1000):
        f = np.ones((3, 3, 3)) * np.random.rand()
        for method in plic.SUPPORTED_METHODS:
            assert_undefined(plic.get_normals(f, method))


def test_end_to_end(fs_vof):
    expected_result = [
        ['CD', '599820a35d442746d95e8cd2f06fbc61'],
        ['WY', '2aeb743728db4ecefda7ce7527d836b4']
    ]

    for method, normals_signature in expected_result:
        normals = plic.get_normals(fs_vof.astype(np.float32), method)

        hash_object = hashlib.md5(normals.tobytes(order='C'))
        assert hash_object.hexdigest() == normals_signature


def test_round_trip(fs_vof_medium):
    normals = plic.get_normals(fs_vof_medium.astype(np.float64), 'CD')
    undefined_normal = np.all(normals == 0, axis=0)

    void_fraction = fs_vof_medium[1:-1, 1:-1, 1:-1].astype(np.float64)

    alpha = plic.get_alpha(void_fraction, normals)
    void_fraction_test = plic.get_void_fraction(alpha, normals)

    with np.nditer([void_fraction, void_fraction_test, undefined_normal]) as itr:
        for f, f_test, undef in itr:
            if np.isnan(f_test):
                assert undef or f == 0 or f == 1
            else:
                assert f_test == pytest.approx(f)


def test_bench_get_alpha(benchmark, fs_vof_small):
    normals = plic.get_normals(fs_vof_small.astype(np.float32), 'WY')
    void_fraction = fs_vof_small[1:-1, 1:-1, 1:-1].astype(np.float32)

    benchmark(plic.get_alpha,
              void_fraction=void_fraction,
              normals=normals)


def test_bench_get_void_fraction(benchmark, fs_vof_small):
    normals = plic.get_normals(fs_vof_small.astype(np.float32), 'WY')
    void_fraction = fs_vof_small[1:-1, 1:-1, 1:-1].astype(np.float32)
    alpha = plic.get_alpha(void_fraction, normals)

    benchmark(plic.get_void_fraction,
              alpha=alpha,
              normals=normals)
