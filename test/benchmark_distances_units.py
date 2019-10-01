import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import math
import random

import numpy as np
import scipy as sp

from scipy.spatial.distance import cdist, pdist, squareform

import pytest
from hypothesis import strategies as st, given, settings
from typing import List, Dict, Set, Tuple, Any, Optional, Union


def distance_matrix_scipy_cdist(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "euclidean")


def distance_matrix_scipy_pdist(ps):
    # Calculate distances between each of the points
    return pdist(ps, "euclidean")


def distance_matrix_scipy_cdist_squared(ps):
    # Calculate squared distances between each of the points
    return cdist(ps, ps, "sqeuclidean")


def distance_matrix_scipy_pdist_squared(ps):
    # Calculate squared distances between each of the points
    return pdist(ps, "sqeuclidean")


# Points as numpy arrays
amount = 200
min_value = 0
max_value = 250
points = np.array(
    [np.array([random.uniform(min_value, max_value), random.uniform(min_value, max_value)]) for _ in range(amount)]
)

m1 = distance_matrix_scipy_cdist(points)
m2 = distance_matrix_scipy_pdist(points)
ms1 = distance_matrix_scipy_cdist_squared(points)
ms2 = distance_matrix_scipy_pdist_squared(points)

# print(points)

# print(m1)
# print(m2)

# print(ms1)
# print(ms2)


def calc_row_idx(k, n):
    return int(math.ceil((1 / 2.0) * (-(-8 * k + 4 * n ** 2 - 4 * n - 7) ** 0.5 + 2 * n - 1) - 1))


def elem_in_i_rows(i, n):
    return i * (n - 1 - i) + (i * (i + 1)) // 2


def calc_col_idx(k, i, n):
    return int(n - elem_in_i_rows(i + 1, n) + k)


def condensed_to_square(k, n):
    i = calc_row_idx(k, n)
    j = calc_col_idx(k, i, n)
    return i, j


def square_to_condensed(i, j, amount):
    # Converts indices of a square matrix to condensed matrix
    # 'amount' is the number of points that were used to calculate the distances
    # https://stackoverflow.com/a/36867493/10882657
    assert i != j, "No diagonal elements in condensed matrix! Diagonal elements are zero"
    if i < j:
        i, j = j, i
    return amount * j - j * (j + 1) // 2 + i - 1 - j


# Test if distance in cdist is same as in pdist, and that the indices function is correct
indices = set()
for i1 in range(amount):
    for i2 in range(amount):
        if i1 == i2:
            # Diagonal entries are zero
            continue
        # m1: cdist square matrix
        v1 = m1[i1, i2]
        # m2: pdist condensed matrix vector
        index = square_to_condensed(i1, i2, amount)
        # print(i1, i2, index, len(m2))
        indices.add(index)
        v2 = m2[index]

        # Test if convert indices functions work
        j1, j2 = condensed_to_square(index, amount)
        # Swap if first is bigger than 2nd
        assert j1 == i1 and j2 == i2 or j2 == i1 and j2 == i1, f"{j1} == {i1} and {j2} == {i2}"

        # Assert if the values of cdist is the same as the value of pdist
        assert v1 == v2, f"m1[i1, i2] is {v1}, m2[index] is {v2}"
# Test that all indices were generated using the for loop above
assert max(indices) == len(m2) - 1
assert min(indices) == 0
assert len(indices) == len(m2), f"{len(indices)} == {len(m2)}"


def test_distance_matrix_scipy_cdist(benchmark):
    result = benchmark(distance_matrix_scipy_cdist, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_pdist(benchmark):
    result = benchmark(distance_matrix_scipy_pdist, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_squared(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_squared, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_pdist_squared(benchmark):
    result = benchmark(distance_matrix_scipy_pdist_squared, points)
    # assert check_result(result, correct_result)


# Run this file using
# pipenv run pytest test/test_benchmark_distances_units.py --benchmark-compare
