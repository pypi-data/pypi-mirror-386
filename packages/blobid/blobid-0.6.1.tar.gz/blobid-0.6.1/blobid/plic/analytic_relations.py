r"""
Implements the analytical relationships described by Scardovelli and Zaleski[1]_.

.. [1] R. Scardovelli & S. Zaleski, "Analytical Relations Connecting Linear Interfaces and Volume Fractions in
   Rectangular Grids," Journal of Computational Physics, vol. 164, pp. 228-237, 2000.
   [10.1006/jcph.2000.6567](https://doi.org/10.1006/jcph.2000.6567)
"""
import numpy as np


def forward_problem(n1, n2, n3, alpha):
    r"""
    Solve the three-dimensional forward problem, :math:`f = f(\vec{n}, \alpha)`
    """

    # scale the slope and sort in ascending order
    t = abs(n1) + abs(n2) + abs(n3)
    m1, m2, m3 = sorted([abs(n1)/t, abs(n2)/t, abs(n3)/t])

    # rotate so all normals are positive
    if n1 < 0:
        alpha = alpha - n1
    if n2 < 0:
        alpha = alpha - n2
    if n3 < 0:
        alpha = alpha - n3

    # scale alpha
    alpha = alpha / t

    # Interface is outside the cell
    if alpha >= 1:
        return 1
    if alpha <= 0:
        return 0

    # Interface is inside the cell
    if alpha > 0.5:
        return 1.0 - _forward_problem_scaled(m1, m2, m3, 1-alpha)
    return _forward_problem_scaled(m1, m2, m3, alpha)


def _forward_problem_scaled(m1, m2, m3, alpha):
    assert 0 <= alpha <= 0.5
    assert 0 <= m1 <= m2 <= m3

    m12 = m1 + m2
    p = 6*m1*m2*m3

    V1 = (1 if m2 == 0 else m1/m2) * (m1/(6*m3))  # this form avoids the need for approximation

    if alpha < m1:
        return alpha**3 / p
    if alpha < m2:
        return alpha*(alpha-m1) / (2*m2*m3) + V1
    if alpha < min(m12, m3):
        return (alpha**2 * (3*m12 - alpha) + m1**2 * (m1 - 3*alpha) + m2**2 * (m2 - 3*alpha))/p
    if m3 < m12:
        return (alpha**2 * (3 - 2*alpha) + m1**2 * (m1 - 3*alpha) + m2**2 * (m2 - 3*alpha) + m3**2 * (m3 - 3*alpha))/p

    return (2*alpha - m12)/(2*m3)


def inverse_problem(n1, n2, n3, f):
    r"""
    Solve the three-dimensional inverse problem, :math:`\alpha = \alpha(\vec{n}, f)`

    Only valid for :math:`f\in (0, 1)`

    """
    assert 0 < f < 1.0

    # scale the slope and sort in ascending order
    t = abs(n1) + abs(n2) + abs(n3)
    m1, m2, m3 = sorted([abs(n1)/t, abs(n2)/t, abs(n3)/t])

    # calculate the scaled alpha
    if f > 0.5:
        alpha = 1 - _inverse_problem_scaled(m1, m2, m3, 1 - f)
    else:
        alpha = _inverse_problem_scaled(m1, m2, m3, f)

    # unscale alpha
    alpha = alpha * t

    # rotate to original orientation
    if n1 < 0:
        alpha = alpha + n1
    if n2 < 0:
        alpha = alpha + n2
    if n3 < 0:
        alpha = alpha + n3

    return alpha


def _inverse_problem_scaled(m1, m2, m3, V):
    r"""
    Solve the three-dimensional inverse problem
    """

    def cubic_root(c3, c2, c1, c0):
        a0 = c0/c3
        a1 = c1/c3
        a2 = c2/c3

        p = a1/3 - a2**2/9
        q = (a1*a2 - 3*a0)/6 - a2**3/27

        theta = np.arccos(q/np.sqrt(-p**3))/3

        return np.sqrt(-p) * (np.sqrt(3)*np.sin(theta) - np.cos(theta)) - a2/3

    assert 0 <= V <= 0.5
    assert 0 <= m1 <= m2 <= m3

    m12 = m1 + m2
    p = 6*m1*m2*m3

    V1 = (1 if m2 == 0 else m1/m2) * (m1/(6*m3))  # this form avoids the need for approximation
    V2 = V1 + (m2 - m1)/(2 * m3)
    V3 = (m3**2 * (3 * m12-m3) + m1**2 * (m1 - 3 * m3) + m2**2 * (m2 - 3 * m3)) / p if m3 < m12 else 0.5*m12/m3

    if V < V1:
        return (p*V)**(1/3)
    if V < V2:
        return 0.5 * (m1+np.sqrt(m1**2 + 8 * m2 * m3 * (V-V1)))
    if V < V3:
        return cubic_root(
            -1, 3*m12, -3*(m1**2 + m2**2), m1**3 + m2**3 - p*V
        )
    if m3 < m12:
        return cubic_root(
            -2, 3, -3*(m1**2 + m2**2 + m3**2), m1**3 + m2**3 + m3**3 - p*V
        )

    return m3*V + m12/2
