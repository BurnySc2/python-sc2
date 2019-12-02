import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import time
import math
import random

import numpy as np
import scipy as sp

# from scipy.spatial import distance as scipydistance
# from numba import jit, njit, vectorize, float64, int64
from scipy.spatial.distance import cdist, pdist

import pytest
from hypothesis import strategies as st, given, settings
from typing import List, Dict, Set, Tuple, Any, Optional, Union


def distance_matrix_scipy_cdist_braycurtis(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "braycurtis")


def distance_matrix_scipy_cdist_canberra(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "canberra")


def distance_matrix_scipy_cdist_chebyshev(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "chebyshev")


def distance_matrix_scipy_cdist_cityblock(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "cityblock")


def distance_matrix_scipy_cdist_correlation(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "correlation")


def distance_matrix_scipy_cdist_cosine(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "cosine")


def distance_matrix_scipy_cdist_hamming(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "hamming")


def distance_matrix_scipy_cdist_jaccard(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "jaccard")


def distance_matrix_scipy_cdist_jensenshannon(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "jensenshannon")


def distance_matrix_scipy_cdist_kulsinski(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "kulsinski")


def distance_matrix_scipy_cdist_mahalanobis(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "mahalanobis")


def distance_matrix_scipy_cdist_matching(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "matching")


# def distance_matrix_scipy_cdist_minkowski(ps):
#     # Calculate distances between each of the points
#     return cdist(ps, ps, "minkowski")


def distance_matrix_scipy_cdist_rogerstanimoto(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "rogerstanimoto")


def distance_matrix_scipy_cdist_russellrao(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "russellrao")


def distance_matrix_scipy_cdist_seuclidean(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "seuclidean")


def distance_matrix_scipy_cdist_sokalmichener(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "sokalmichener")


def distance_matrix_scipy_cdist_sokalsneath(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "sokalsneath")


# def distance_matrix_scipy_cdist_wminkowski(ps):
#     # Calculate distances between each of the points
#     return cdist(ps, ps, "wminkowski")


def distance_matrix_scipy_cdist_yule(ps):
    # Calculate distances between each of the points
    return cdist(ps, ps, "yule")


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
max_value = 300
points = np.array(
    [np.array([random.uniform(min_value, max_value), random.uniform(min_value, max_value)]) for _ in range(amount)]
)


def test_distance_matrix_scipy_cdist_braycurtis(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_braycurtis, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_canberra(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_canberra, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_chebyshev(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_chebyshev, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_cityblock(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_cityblock, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_correlation(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_correlation, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_cosine(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_cosine, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_hamming(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_hamming, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_jaccard(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_jaccard, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_jensenshannon(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_jensenshannon, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_kulsinski(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_kulsinski, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_mahalanobis(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_mahalanobis, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_matching(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_matching, points)
    # assert check_result(result, correct_result)


# def test_distance_matrix_scipy_cdist_minkowski(benchmark):
#     result = benchmark(distance_matrix_scipy_cdist_minkowski, points)
#     # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_rogerstanimoto(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_rogerstanimoto, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_russellrao(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_russellrao, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_seuclidean(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_seuclidean, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_sokalmichener(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_sokalmichener, points)
    # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_sokalsneath(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_sokalsneath, points)
    # assert check_result(result, correct_result)


# def test_distance_matrix_scipy_cdist_wminkowski(benchmark):
#     result = benchmark(distance_matrix_scipy_cdist_wminkowski, points)
#     # assert check_result(result, correct_result)


def test_distance_matrix_scipy_cdist_yule(benchmark):
    result = benchmark(distance_matrix_scipy_cdist_yule, points)
    # assert check_result(result, correct_result)


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
# pipenv run pytest test/test_benchmark_distances_cdist.py --benchmark-compare
