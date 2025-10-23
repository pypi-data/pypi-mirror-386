r"""
Implements piecewise linear interface calculation (PLIC), where the interface in each cell can be represented by
:math:`\vec{n}\cdot\vec{x}=\alpha`
"""

from .plic import get_normals, get_alpha, get_void_fraction, SUPPORTED_METHODS

from . import analytic_relations

__all__ = ['get_normals', 'get_alpha', 'get_void_fraction', 'SUPPORTED_METHODS', 'analytic_relations']
