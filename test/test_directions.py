import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import random
from math import atan2, cos, pi, sin, sqrt

from sc2.position import EPSILON, Point2

P0 = Point2((0, 0))
P1 = Point2((1, 1))
P2 = Point2((3, 1))
P3 = Point2((3, 3))


def rad_diff(a, b):
    r1 = abs(a - b)
    r2 = abs(b - a)
    r3 = min(r1, r2)
    r4 = abs(2 * pi - r3)
    return min(r3, r4)


def test_test_rad_diff():
    assert rad_diff(0, 0) == 0
    assert rad_diff(0, 1) == 1
    assert rad_diff(0, pi) == pi
    assert rad_diff(pi, pi) == 0
    assert rad_diff(2 * pi, 0) == 0
    assert rad_diff(2 * pi + 1, 0) == 1
    assert rad_diff(2 * pi + 1, 1) == 0
    assert rad_diff(pi, -pi) == 0


def test_distance():
    assert P0.distance_to(P1) == sqrt(2)
    assert P1.distance_to(P2) == 2
    assert P0.distance_to(P2) == sqrt(10)


def test_towards():
    assert P0.towards(P1, 1) == Point2((sqrt(2) / 2, sqrt(2) / 2))


def test_random_on_distance():
    random.seed(1)

    def get_points(source, distance, n=1000):
        return {source.random_on_distance(distance) for _ in range(n)}

    def verify_distances(source, distance, n=1000):
        for p in get_points(source, distance, n):
            assert abs(source.distance_to(p) - distance) < 0.000001

    def verify_angles(source, distance, n=1000):
        angles_rad = {atan2(p.y - source.y, p.x - source.x) for p in get_points(source, distance, n)}

        quadrants = {(cos(a) < 0, sin(a) < 0) for a in angles_rad}
        assert len(quadrants) == 4

    verify_distances(P0, 1e2)
    verify_distances(P1, 1e3)
    verify_distances(P2, 1e4)

    verify_angles(P0, 1e2)
    verify_angles(P1, 1e3)
    verify_angles(P2, 1e4)


def test_towards_random_angle():
    random.seed(1)

    def random_points(n=1000):
        rs = lambda: 1 - random.random() * 2
        return {Point2((rs() * 1000, rs() * 1000)) for _ in range(n)}

    def verify(source, target, max_difference=(pi / 4), n=1000):
        d = 1 + random.random() * 100
        points = {source.towards_with_random_angle(target, distance=d, max_difference=max_difference) for _ in range(n)}

        dx, dy = target.x - source.x, target.y - source.y
        src_angle = atan2(dy, dx)

        for p in points:
            angle = atan2(p.y - source.y, p.x - source.x)
            assert rad_diff(src_angle, angle) <= max_difference

            assert abs(source.distance_to(p) - d) <= EPSILON

    verify(P0, P1)
    verify(P1, P2)
    verify(P1, P3)
    verify(P2, P3)

    verify(P1, P0)
    verify(P2, P1)
    verify(P3, P1)
    verify(P3, P2)

    ps = random_points(n=50)
    for p1 in ps:
        for p2 in ps:
            if p1 == p2:
                continue
            verify(p1, p2, n=10)
