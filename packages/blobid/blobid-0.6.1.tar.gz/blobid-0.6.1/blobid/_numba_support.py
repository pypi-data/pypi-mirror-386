"""Setup Numba if available"""

numba_availible = True
try:
    from numba import njit
except ImportError:
    numba_availible = False

    # create a dummy njit decorator
    def njit(func): return func
