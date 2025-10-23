"""
Holds information about the input domain
"""
from typing import List, Tuple

import numpy as np


def _pad_array(
        arr: np.ndarray,
        periodic: Tuple[bool, bool, bool],
        periodic_padding: int,
        extra_padding: int
        ) -> np.ndarray:
    """Add appropriate padding to the array"""

    # padding in periodic directions
    width = periodic_padding + extra_padding
    if width != 0:
        arr = np.pad(arr, [(width, width) if p else (0, 0) for p in periodic], 'wrap')

    # padding in non-periodic directions
    width = extra_padding
    if width != 0:
        arr = np.pad(arr, [(0, 0) if p else (width, width) for p in periodic], 'symmetric')

    return arr


class VOFDomain:
    """Holds the vof field and information about periodicity"""

    def __init__(self,
                 void_fraction: np.ndarray,
                 periodic: List[bool],
                 periodic_padding: int,
                 extra_padding: int
                 ):
        # Checks
        assert len(periodic) == void_fraction.ndim

        # Convert original VOF felid into a 3D field
        self.original_shape = void_fraction.shape
        match void_fraction.ndim:
            case 1: self.periodic = (False, periodic[0], False)
            case 2: self.periodic = (periodic[0], periodic[1], False)
            case 3: self.periodic = (periodic[0], periodic[1], periodic[2])
            case _:
                raise ValueError("Unexpected void_fraction.ndim: " + str(void_fraction.ndim))

        self._vof_storage = np.atleast_3d(void_fraction.copy())

        # Add padding
        self.periodic_padding = periodic_padding
        self.extra_padding = extra_padding
        self._vof_storage = _pad_array(self._vof_storage, self.periodic,
                                       periodic_padding=self.periodic_padding,
                                       extra_padding=self.extra_padding)

    def vof(self, padding: int = 0) -> np.ndarray:
        """
        Padding is `periodic_padding + padding` in periodic directions and `padding` in non-periodic directions
        """
        skip = self.extra_padding - padding
        assert skip >= 0, f"requested pad {padding} larger than domain's extra_padding {self.extra_padding}"

        if skip == 0:
            return self._vof_storage
        else:
            return self._vof_storage[skip:-(skip), skip:-(skip), skip:-(skip)]

    def convert_to_original_shape(self, arr: np.ndarray) -> np.ndarray:
        """
        Convert back to input shape of void_fraction
        """
        # remove padding in periodic directions
        if self.periodic_padding != 0:
            if self.periodic[0]:
                arr = arr[self.periodic_padding:-self.periodic_padding, :, :]
            if self.periodic[1]:
                arr = arr[:, self.periodic_padding:-self.periodic_padding, :]
            if self.periodic[2]:
                arr = arr[:, :, self.periodic_padding:-self.periodic_padding]

        return arr.reshape(self.original_shape)
