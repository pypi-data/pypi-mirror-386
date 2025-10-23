import pytest

import numpy as np
import blobid.plic.analytic_relations as analytic_relations

COUNT = 20000


@pytest.fixture
def slopes() -> np.ndarray:
    """
    List of slopes where 0 <= m1 <= m2 <= m2 < 1
    """
    m = np.random.rand(COUNT, 3)

    m[:, 1] = m[:, 1] * m[:, 2]
    m[:, 0] = m[:, 0] * m[:, 1]
    m = m / np.sum(m, 1, keepdims=True)

    return m


@pytest.fixture
def normals() -> np.ndarray:
    """
    List of normals
    """
    return (np.random.rand(COUNT, 3) * 3) - 1.5


def test_round_trip(normals):
    for n1, n2, n3, f in zip(normals[:, 0], normals[:, 1], normals[:, 2], np.random.rand(COUNT)*0.5):
        alpha = analytic_relations.inverse_problem(n1, n2, n3, f)
        f_test = analytic_relations.forward_problem(n1, n2, n3, alpha)

        assert f_test == pytest.approx(f)


def test_scaled_round_trip_forward(slopes):
    for m1, m2, m3, V in zip(slopes[:, 0], slopes[:, 1], slopes[:, 2], np.random.rand(COUNT)*0.5):
        alpha = analytic_relations._inverse_problem_scaled(m1, m2, m3, V)
        V_test = analytic_relations._forward_problem_scaled(m1, m2, m3, alpha)

        assert V_test == pytest.approx(V)


def test_scaled_round_trip_backward(slopes):
    for m1, m2, m3, alpha in zip(slopes[:, 0], slopes[:, 1], slopes[:, 2], np.random.rand(COUNT)*0.5):
        V = analytic_relations._forward_problem_scaled(m1, m2, m3, alpha)
        alpha_test = analytic_relations._inverse_problem_scaled(m1, m2, m3, V)

        assert alpha_test == pytest.approx(alpha)


def test_scaled_empty(slopes):
    for m1, m2, m3 in zip(slopes[:, 0], slopes[:, 1], slopes[:, 2]):
        assert analytic_relations._forward_problem_scaled(m1, m2, m3, 0.0) == 0
        assert analytic_relations._inverse_problem_scaled(m1, m2, m3, 0.0) == 0


def test_scaled_half_full(slopes):
    for m1, m2, m3 in zip(slopes[:, 0], slopes[:, 1], slopes[:, 2]):
        assert analytic_relations._forward_problem_scaled(m1, m2, m3, 0.5) == pytest.approx(0.5)
        assert analytic_relations._inverse_problem_scaled(m1, m2, m3, 0.5) == pytest.approx(0.5)
