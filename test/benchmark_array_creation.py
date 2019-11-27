import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import math
import random

import numpy as np
import scipy as sp

import pytest
from hypothesis import strategies as st, given, settings
from typing import List, Dict, Set, Tuple, Any, Optional, Union

"""
Testing what the fastest way is to create a 1D Array with 2 values
"""
x, y = random.uniform(0, 300), random.uniform(0, 300)


def numpy_array(x, y):
    # Calculate distances between each of the points
    return np.array((x, y), dtype=np.float)


def numpy_array_tuple(my_tuple):
    # Calculate distances between each of the points
    return np.array(my_tuple, dtype=np.float)


def numpy_asarray(x, y):
    # Calculate distances between each of the points
    return np.asarray((x, y), dtype=np.float)


def numpy_asarray_tuple(my_tuple):
    # Calculate distances between each of the points
    return np.asarray(my_tuple, dtype=np.float)


def numpy_asanyarray(x, y):
    # Calculate distances between each of the points
    return np.asanyarray((x, y), dtype=np.float)


def numpy_asanyarray_tuple(my_tuple):
    # Calculate distances between each of the points
    return np.asanyarray(my_tuple, dtype=np.float)


def numpy_fromiter(x, y):
    # Calculate distances between each of the points
    return np.fromiter((x, y), dtype=float, count=2)


def numpy_fromiter_tuple(my_tuple):
    # Calculate distances between each of the points
    return np.fromiter(my_tuple, dtype=float, count=2)


def numpy_fromiter_np_float(x, y):
    # Calculate distances between each of the points
    return np.fromiter((x, y), dtype=np.float, count=2)


def numpy_fromiter_np_float_tuple(my_tuple):
    # Calculate distances between each of the points
    return np.fromiter(my_tuple, dtype=np.float, count=2)


def numpy_zeros(x, y):
    # Calculate distances between each of the points
    a = np.zeros(2, dtype=np.float)
    a[0] = x
    a[1] = y
    return a


def numpy_ones(x, y):
    # Calculate distances between each of the points
    a = np.ones(2, dtype=np.float)
    a[0] = x
    a[1] = y
    return a


numpy_array(x, y)
correct_array = np.array([x, y])


def test_numpy_array(benchmark):
    result = benchmark(numpy_array, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_array_tuple(benchmark):
    result = benchmark(numpy_array_tuple, (x, y))
    assert np.array_equal(result, correct_array)


def test_numpy_asarray(benchmark):
    result = benchmark(numpy_asarray, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_asarray_tuple(benchmark):
    result = benchmark(numpy_asarray_tuple, (x, y))
    assert np.array_equal(result, correct_array)


def test_numpy_asanyarray(benchmark):
    result = benchmark(numpy_asanyarray, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_asanyarray_tuple(benchmark):
    result = benchmark(numpy_asanyarray_tuple, (x, y))
    assert np.array_equal(result, correct_array)


def test_numpy_fromiter(benchmark):
    result = benchmark(numpy_fromiter, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_fromiter_tuple(benchmark):
    result = benchmark(numpy_fromiter_tuple, (x, y))
    assert np.array_equal(result, correct_array)


def test_numpy_fromiter_np_float(benchmark):
    result = benchmark(numpy_fromiter_np_float, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_fromiter_np_float_tuple(benchmark):
    result = benchmark(numpy_fromiter_np_float_tuple, (x, y))
    assert np.array_equal(result, correct_array)


def test_numpy_zeros(benchmark):
    result = benchmark(numpy_zeros, x, y)
    assert np.array_equal(result, correct_array)


def test_numpy_ones(benchmark):
    result = benchmark(numpy_ones, x, y)
    assert np.array_equal(result, correct_array)


# Run this file using
# pipenv run pytest test/test_benchmark_array_creation.py --benchmark-compare
