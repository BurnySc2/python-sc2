import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import math
import random

# from sc2.position import Point2

import numpy as np
import scipy as sp

from scipy.spatial.distance import cdist
from scipy.spatial import KDTree

# from numba import njit, jit

import pytest
from hypothesis import strategies as st, given, settings
from typing import List, Dict, Set, Tuple, Any, Optional, Union


def distance_matrix_scipy_cdist_squared(ps, p1):
    # Calculate squared distances between multiple points and target point
    flat_units = (item for sublist in ps for item in sublist)
    units_np = np.fromiter(flat_units, dtype=float, count=2 * len(ps)).reshape((-1, 2))
    point_np = np.fromiter(p1, dtype=float, count=2).reshape((-1, 2))
    return cdist(units_np, point_np, "sqeuclidean")


def distance_numpy_basic_1(ps, p1):
    """ Distance calculation using numpy """
    flat_units = (item for sublist in ps for item in sublist)
    units_np = np.fromiter(flat_units, dtype=float, count=2 * len(ps)).reshape((-1, 2))
    point_np = np.fromiter(p1, dtype=float, count=2).reshape((-1, 2))
    # Subtract and then square the values
    nppoints = (units_np - point_np) ** 2
    # Calc the sum of each vector
    nppoints = nppoints.sum(axis=1)
    return nppoints


def distance_numpy_basic_2(ps, p1):
    """ Distance calculation using numpy """
    flat_units = (item for sublist in ps for item in sublist)
    units_np = np.fromiter(flat_units, dtype=float, count=2 * len(ps)).reshape((-1, 2))
    point_np = np.fromiter(p1, dtype=float, count=2).reshape((-1, 2))
    dist_2 = np.sum((units_np - point_np) ** 2, axis=1)
    return dist_2


def distance_numpy_einsum(ps, p1):
    """ Distance calculation using numpy einstein sum """
    flat_units = (item for sublist in ps for item in sublist)
    units_np = np.fromiter(flat_units, dtype=float, count=2 * len(ps)).reshape((-1, 2))
    point_np = np.fromiter(p1, dtype=float, count=2).reshape((-1, 2))
    deltas = units_np - point_np
    dist_2 = np.einsum("ij,ij->i", deltas, deltas)
    return dist_2


def distance_numpy_einsum_pre_converted(ps, p1):
    """ Distance calculation using numpy einstein sum """
    deltas = ps - p1
    dist_2 = np.einsum("ij,ij->i", deltas, deltas)
    return dist_2


# @njit("float64[:](float64[:, :], float64[:, :])")
# def distance_numpy_basic_1_numba(ps, p1):
#     """ Distance calculation using numpy with njit """
#     # Subtract and then square the values
#     nppoints = (ps - p1) ** 2
#     # Calc the sum of each vector
#     nppoints = nppoints.sum(axis=1)
#     return nppoints


# @njit("float64[:](float64[:, :], float64[:, :])")
# def distance_numpy_basic_2_numba(ps, p1):
#     """ Distance calculation using numpy with njit """
#     distances = np.sum((ps - p1) ** 2, axis=1)
#     return distances


# # @njit("float64[:](float64[:], float64[:])")
# @jit(nopython=True)
# def distance_numba(ps, p1, amount):
#     """ Distance calculation using numpy with jit(nopython=True) """
#     distances = []
#     x1 = p1[0]
#     y1 = p1[1]
#     for index in range(amount):
#         x0 = ps[2 * index]
#         y0 = ps[2 * index + 1]
#         distance_squared = (x0 - x1) ** 2 + (y0 - y1) ** 2
#         distances.append(distance_squared)
#     return distances


def distance_pure_python(ps, p1):
    """ Distance calculation using numpy with jit(nopython=True) """
    distances = []
    x1 = p1[0]
    y1 = p1[1]
    for x0, y0 in ps:
        distance_squared = (x0 - x1) ** 2 + (y0 - y1) ** 2
        distances.append(distance_squared)
    return distances


def distance_math_hypot(ps, p1):
    """ Distance calculation using math.hypot """
    distances = []
    x1 = p1[0]
    y1 = p1[1]
    # for x0, y0 in ps:
    #     distance = math.hypot(x0 - x1, y0 - y1)
    #     distances.append(distance)
    # return distances
    return [math.hypot(x0 - x1, y0 - y1) for x0, y0 in ps]


# Points as numpy arrays
amount = 50
min_value = 0
max_value = 250

point: Tuple[float, float] = (random.uniform(min_value, max_value), random.uniform(min_value, max_value))
units: List[Tuple[float, float]] = [
    (random.uniform(min_value, max_value), random.uniform(min_value, max_value)) for _ in range(amount)
]

# Pre convert points to numpy array
flat_units = [item for sublist in units for item in sublist]
units_np = np.fromiter(flat_units, dtype=float, count=2 * len(units)).reshape((-1, 2))
point_np = np.fromiter(point, dtype=float, count=2).reshape((-1, 2))


r1 = distance_matrix_scipy_cdist_squared(units, point).flatten()
r2 = distance_numpy_basic_1(units, point)
r3 = distance_numpy_basic_2(units, point)
r4 = distance_numpy_einsum(units, point)
# r5 = distance_numpy_basic_1_numba(units_np, point_np)
# r6 = distance_numpy_basic_2_numba(units_np, point_np)
# r10 = distance_numba(flat_units, point_np, len(flat_units) // 2)

assert np.array_equal(r1, r2)
assert np.array_equal(r1, r3)
assert np.array_equal(r1, r4)
# assert np.array_equal(r1, r5)
# assert np.array_equal(r1, r6)

# print(r10)


def test_distance_matrix_scipy_cdist_squared(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_squared, units, point)


def test_distance_numpy_basic_1(benchmark):
    result = benchmark(distance_numpy_basic_1, units, point)


def test_distance_numpy_basic_2(benchmark):
    result = benchmark(distance_numpy_basic_2, units, point)


def test_distance_numpy_einsum(benchmark):
    result = benchmark(distance_numpy_einsum, units, point)


def test_distance_numpy_einsum_pre_converted(benchmark):
    result = benchmark(distance_numpy_einsum_pre_converted, units_np, point_np)


# def test_distance_numpy_basic_1_numba(benchmark):
#     result = benchmark(distance_numpy_basic_1_numba, units_np, point_np)


# def test_distance_numpy_basic_2_numba(benchmark):
#     result = benchmark(distance_numpy_basic_2_numba, units_np, point_np)


# def test_distance_numba(benchmark):
#     result = benchmark(distance_numba, flat_units, point, len(flat_units) // 2)


def test_distance_pure_python(benchmark):
    result = benchmark(distance_pure_python, units, point)


def test_distance_math_hypot(benchmark):
    result = benchmark(distance_math_hypot, units, point)


# Run this file using
# pipenv run pytest test/test_benchmark_distances_points_to_point.py --benchmark-compare
