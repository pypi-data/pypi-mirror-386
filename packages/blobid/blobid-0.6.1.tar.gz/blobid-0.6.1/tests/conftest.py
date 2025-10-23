import pytest
import numpy as np


@pytest.fixture
def fs_vof() -> np.ndarray:
    return 1.0 - np.load("tests/resources/fs_vof.npy")


@pytest.fixture
def fs_vof_small(fs_vof) -> np.ndarray:
    return fs_vof[
        :fs_vof.shape[0]//8,
        :fs_vof.shape[1]//8,
        fs_vof.shape[2]//3:-fs_vof.shape[2]//3]


@pytest.fixture
def fs_vof_medium(fs_vof) -> np.ndarray:
    return fs_vof[
        :fs_vof.shape[0]//2,
        :fs_vof.shape[1]//2,
        fs_vof.shape[2]//4:-fs_vof.shape[2]//4]


@pytest.fixture
def fs_vof_full(fs_vof) -> np.ndarray:
    return fs_vof
