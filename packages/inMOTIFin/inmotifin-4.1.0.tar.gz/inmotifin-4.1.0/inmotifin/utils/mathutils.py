"""Utility functions related to calculations"""
from typing import List
import numpy as np


def normalize_1d_array(my_array: np.ndarray) -> np.ndarray:
    """ Normalize the values in an array to sum to 1"""
    # 1-D array
    if sum(my_array) == 0:
        # if all zeros, return uniform distribution
        motif_base_freq = np.full(len(my_array), 1/len(my_array))
        return motif_base_freq
    motif_base_freq = my_array / sum(my_array)
    return motif_base_freq


def normalize_2d_array(my_array: np.ndarray) -> np.ndarray:
    """ Normalize the values in a 2-D array to sum to 1"""
    if len(my_array.shape) != 2:
        raise ValueError("Input array is not 2-D")
    norm_array = []
    for row in my_array:
        norm_array.append(normalize_1d_array(row))
    return np.array(norm_array)


def sample_lengths(
        len_min: int,
        len_max: int,
        num_len: int,
        rng: np.random.Generator) -> List[int]:
    """
    Sample a list of lengths given min and max values (uniform)

    Parameters
    ----------
    len_seq_min: int
        Minimum length to be sampled
    len_seq_max: int
        Maximum length to be sampled (included in range)
    num_seq: int
        Number of lengths to generate
    rng: np.random.Generator
        Random generator for length

    Return
    ------
    _: List[int]
        A list of uniformly sampled lengths
    """
    return rng.integers(
        low=len_min,
        high=len_max,
        endpoint=True,
        size=num_len)
