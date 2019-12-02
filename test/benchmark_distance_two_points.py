import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import math
import random
import numpy as np
import scipy as sp
from scipy.spatial import distance as scipydistance

# from numba import jit, njit, vectorize, float64, int64
from sc2.position import Point2

import pytest
from hypothesis import strategies as st, given, settings
from typing import List, Dict, Set, Tuple, Any, Optional, Union

import platform

PYTHON_VERSION = platform.python_version_tuple()
USING_PYTHON_3_8: bool = ("3", "8") <= PYTHON_VERSION


def distance_to_python_raw(s, p):
    return ((s[0] - p[0]) ** 2 + (s[1] - p[1]) ** 2) ** 0.5


def distance_to_squared_python_raw(s, p):
    return (s[0] - p[0]) ** 2 + (s[1] - p[1]) ** 2


if USING_PYTHON_3_8:

    def distance_to_math_dist(s, p):
        return math.dist(s, p)


def distance_to_math_hypot(s, p):
    return math.hypot((s[0] - p[0]), (s[1] - p[1]))


def distance_scipy_euclidean(p1, p2) -> Union[int, float]:
    """ Distance calculation using scipy """
    dist = scipydistance.euclidean(p1, p2)
    # dist = distance.cdist(p1.T, p2.T, "euclidean")
    return dist


def distance_numpy_linalg_norm(p1, p2):
    """ Distance calculation using numpy """
    return np.linalg.norm(p1 - p2)


def distance_sum_squared_sqrt(p1, p2) -> Union[int, float]:
    """ Distance calculation using numpy """
    return np.sqrt(np.sum((p1 - p2) ** 2))


def distance_sum_squared(p1, p2) -> Union[int, float]:
    """ Distance calculation using numpy """
    return np.sum((p1 - p2) ** 2, axis=0)


# @njit
# def distance_python_raw_njit(p1: Point2, p2: Point2) -> Union[int, float]:
#     """ The built in Point2 distance function rewritten differently with njit, same structure as distance02 """
#     return ((p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2) ** 0.5


# @njit
# def distance_python_raw_square_njit(p1: Point2, p2: Point2) -> Union[int, float]:
#     """ The built in Point2 distance function rewritten differently with njit, same structure as distance02 """
#     return (p1[0] - p2[0]) ** 2 + (p1[1] - p2[1]) ** 2


# @njit("float64(float64[:], float64[:])")
# def distance_numpy_linalg_norm_njit(p1, p2):
#     """ Distance calculation using numpy + numba, same structure as distance12 """
#     return np.linalg.norm(p1 - p2)


# @njit("float64(float64[:], float64[:])")
# def distance_numpy_square_sum_sqrt_njit(p1, p2) -> Union[int, float]:
#     """ Distance calculation using numpy + numba, same structure as distance13 """
#     return np.sqrt(np.sum((p1 - p2) ** 2))


# @njit("float64(float64[:], float64[:])")
# def distance_numpy_square_sum_njit(p1, p2) -> Union[int, float]:
#     """ Distance calculation using numpy + numba, same structure as distance13 """
#     return np.sum((p1 - p2) ** 2, axis=0)


# Points as Point2 object
p1 = Point2((random.uniform(0, 300), random.uniform(0, 300)))
p2 = Point2((random.uniform(0, 300), random.uniform(0, 300)))
# Points as numpy array to get most accuracy if all points do not need to be converted before calculation
p1_np = np.asarray(p1)
p2_np = np.asarray(p2)

# Correct result to ensure that in the functions the correct result is calculated
correct_result = distance_to_math_hypot(p1, p2)

# print(p1, p1_np)
# print(p2, p2_np)
# print(np.sum((p1_np - p2_np)**2))

# Do one call to jit to precompile once to get more accurate results
# distance_python_raw_njit(p1_np, p2_np)
# distance_python_raw_square_njit(p1_np, p2_np)
# distance_numpy_linalg_norm_njit(p1_np, p2_np)
# distance_numpy_square_sum_sqrt_njit(p1_np, p2_np)
# distance_numpy_square_sum_njit(p1_np, p2_np)


def check_result(result1, result2, accuracy=1e-5):
    if abs(result1 - result2) <= accuracy:
        return True
    return False


if USING_PYTHON_3_8:

    def test_distance_to_math_dist(benchmark):
        result = benchmark(distance_to_math_dist, p1, p2)
        assert check_result(result, correct_result)


def test_distance_to_math_hypot(benchmark):
    result = benchmark(distance_to_math_hypot, p1, p2)
    assert check_result(result, correct_result)


def test_distance_to_python_raw(benchmark):
    result = benchmark(distance_to_python_raw, p1, p2)
    assert check_result(result, correct_result)


def test_distance_to_squared_python_raw(benchmark):
    result = benchmark(distance_to_squared_python_raw, p1, p2)
    assert check_result(result, correct_result ** 2)


def test_distance_scipy_euclidean(benchmark):
    result = benchmark(distance_scipy_euclidean, p1_np, p2_np)
    assert check_result(result, correct_result)


def test_distance_numpy_linalg_norm(benchmark):
    result = benchmark(distance_numpy_linalg_norm, p1_np, p2_np)
    assert check_result(result, correct_result)


def test_distance_sum_squared_sqrt(benchmark):
    result = benchmark(distance_sum_squared_sqrt, p1_np, p2_np)
    assert check_result(result, correct_result)


def test_distance_sum_squared(benchmark):
    result = benchmark(distance_sum_squared, p1_np, p2_np)
    assert check_result(result, correct_result ** 2)


# def test_distance_python_raw_njit(benchmark):
#     result = benchmark(distance_python_raw_njit, p1_np, p2_np)
#     assert check_result(result, correct_result)


# def test_distance_python_raw_square_njit(benchmark):
#     result = benchmark(distance_python_raw_square_njit, p1_np, p2_np)
#     assert check_result(re`sult, correct_result ** 2)
#
#
# def test_distance_numpy_linalg_norm_njit(benchmark):
#     result = benchmark(distance_numpy_linalg_norm_njit, p1_np, p2_np)
#     assert check_result(result, correct_result)
#
#
# def test_distance_numpy_square_sum_sqrt_njit(benchmark):
#     result = benchmark(distance_numpy_square_sum_sqrt_njit, p1_np, p2_np)
#     assert check_result(result, correct_result)
#
#
# def test_distance_numpy_square_sum_njit(benchmark):
#     result = benchmark(distance_numpy_square_sum_njit, p1_np, p2_np)
#     assert check_result(result, correct_result ** 2)


# Run this file using
# pipenv run pytest test/test_benchmark_distance_two_points.py --benchmark-compare
