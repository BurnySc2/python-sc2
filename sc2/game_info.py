from __future__ import annotations

import heapq
from collections import deque
from dataclasses import dataclass
from functools import cached_property
from typing import Any, Deque, Dict, FrozenSet, Iterable, List, Optional, Set, Tuple

import numpy as np

from sc2.pixel_map import PixelMap
from sc2.player import Player, Race
from sc2.position import Point2, Rect, Size


@dataclass
class Ramp:
    points: FrozenSet[Point2]
    game_info: GameInfo

    @property
    def x_offset(self) -> float:
        # Tested by printing actual building locations vs calculated depot positions
        return 0.5

    @property
    def y_offset(self) -> float:
        # Tested by printing actual building locations vs calculated depot positions
        return 0.5

    @cached_property
    def _height_map(self):
        return self.game_info.terrain_height

    @cached_property
    def size(self) -> int:
        return len(self.points)

    def height_at(self, p: Point2) -> int:
        return self._height_map[p]

    @cached_property
    def upper(self) -> FrozenSet[Point2]:
        """ Returns the upper points of a ramp. """
        current_max = -10000
        result = set()
        for p in self.points:
            height = self.height_at(p)
            if height > current_max:
                current_max = height
                result = {p}
            elif height == current_max:
                result.add(p)
        return frozenset(result)

    @cached_property
    def upper2_for_ramp_wall(self) -> FrozenSet[Point2]:
        """ Returns the 2 upper ramp points of the main base ramp required for the supply depot and barracks placement properties used in this file. """
        # From bottom center, find 2 points that are furthest away (within the same ramp)
        return frozenset(heapq.nlargest(2, self.upper, key=lambda x: x.distance_to_point2(self.bottom_center)))

    @cached_property
    def top_center(self) -> Point2:
        length = len(self.upper)
        pos = Point2((sum(p.x for p in self.upper) / length, sum(p.y for p in self.upper) / length))
        return pos

    @cached_property
    def lower(self) -> FrozenSet[Point2]:
        current_min = 10000
        result = set()
        for p in self.points:
            height = self.height_at(p)
            if height < current_min:
                current_min = height
                result = {p}
            elif height == current_min:
                result.add(p)
        return frozenset(result)

    @cached_property
    def bottom_center(self) -> Point2:
        length = len(self.lower)
        pos = Point2((sum(p.x for p in self.lower) / length, sum(p.y for p in self.lower) / length))
        return pos

    @cached_property
    def barracks_in_middle(self) -> Optional[Point2]:
        """ Barracks position in the middle of the 2 depots """
        if len(self.upper) not in {2, 5}:
            return None
        if len(self.upper2_for_ramp_wall) == 2:
            points = set(self.upper2_for_ramp_wall)
            p1 = points.pop().offset((self.x_offset, self.y_offset))
            p2 = points.pop().offset((self.x_offset, self.y_offset))
            # Offset from top point to barracks center is (2, 1)
            intersects = p1.circle_intersection(p2, 5**0.5)
            any_lower_point = next(iter(self.lower))
            return max(intersects, key=lambda p: p.distance_to_point2(any_lower_point))
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def depot_in_middle(self) -> Optional[Point2]:
        """ Depot in the middle of the 3 depots """
        if len(self.upper) not in {2, 5}:
            return None
        if len(self.upper2_for_ramp_wall) == 2:
            points = set(self.upper2_for_ramp_wall)
            p1 = points.pop().offset((self.x_offset, self.y_offset))
            p2 = points.pop().offset((self.x_offset, self.y_offset))
            # Offset from top point to depot center is (1.5, 0.5)
            try:
                intersects = p1.circle_intersection(p2, 2.5**0.5)
            except AssertionError:
                # Returns None when no placement was found, this is the case on the map Honorgrounds LE with an exceptionally large main base ramp
                return None
            anyLowerPoint = next(iter(self.lower))
            return max(intersects, key=lambda p: p.distance_to_point2(anyLowerPoint))
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def corner_depots(self) -> FrozenSet[Point2]:
        """ Finds the 2 depot positions on the outside """
        if not self.upper2_for_ramp_wall:
            return frozenset()
        if len(self.upper2_for_ramp_wall) == 2:
            points = set(self.upper2_for_ramp_wall)
            p1 = points.pop().offset((self.x_offset, self.y_offset))
            p2 = points.pop().offset((self.x_offset, self.y_offset))
            center = p1.towards(p2, p1.distance_to_point2(p2) / 2)
            depot_position = self.depot_in_middle
            if depot_position is None:
                return frozenset()
            # Offset from middle depot to corner depots is (2, 1)
            intersects = center.circle_intersection(depot_position, 5**0.5)
            return intersects
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def barracks_can_fit_addon(self) -> bool:
        """ Test if a barracks can fit an addon at natural ramp """
        # https://i.imgur.com/4b2cXHZ.png
        if len(self.upper2_for_ramp_wall) == 2:
            return self.barracks_in_middle.x + 1 > max(self.corner_depots, key=lambda depot: depot.x).x
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def barracks_correct_placement(self) -> Optional[Point2]:
        """ Corrected placement so that an addon can fit """
        if self.barracks_in_middle is None:
            return None
        if len(self.upper2_for_ramp_wall) == 2:
            if self.barracks_can_fit_addon:
                return self.barracks_in_middle
            return self.barracks_in_middle.offset((-2, 0))
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def protoss_wall_pylon(self) -> Optional[Point2]:
        """
        Pylon position that powers the two wall buildings and the warpin position.
        """
        if len(self.upper) not in {2, 5}:
            return None
        if len(self.upper2_for_ramp_wall) != 2:
            raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")
        middle = self.depot_in_middle
        # direction up the ramp
        direction = self.barracks_in_middle.negative_offset(middle)
        return middle + 6 * direction

    @cached_property
    def protoss_wall_buildings(self) -> FrozenSet[Point2]:
        """
        List of two positions for 3x3 buildings that form a wall with a spot for a one unit block.
        These buildings can be powered by a pylon on the protoss_wall_pylon position.
        """
        if len(self.upper) not in {2, 5}:
            return frozenset()
        if len(self.upper2_for_ramp_wall) == 2:
            middle = self.depot_in_middle
            # direction up the ramp
            direction = self.barracks_in_middle.negative_offset(middle)
            # sort depots based on distance to start to get wallin orientation
            sorted_depots = sorted(
                self.corner_depots, key=lambda depot: depot.distance_to(self.game_info.player_start_location)
            )
            wall1: Point2 = sorted_depots[1].offset(direction)
            wall2 = middle + direction + (middle - wall1) / 1.5
            return frozenset([wall1, wall2])
        raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")

    @cached_property
    def protoss_wall_warpin(self) -> Optional[Point2]:
        """
        Position for a unit to block the wall created by protoss_wall_buildings.
        Powered by protoss_wall_pylon.
        """
        if len(self.upper) not in {2, 5}:
            return None
        if len(self.upper2_for_ramp_wall) != 2:
            raise Exception("Not implemented. Trying to access a ramp that has a wrong amount of upper points.")
        middle = self.depot_in_middle
        # direction up the ramp
        direction = self.barracks_in_middle.negative_offset(middle)
        # sort depots based on distance to start to get wallin orientation
        sorted_depots = sorted(self.corner_depots, key=lambda x: x.distance_to(self.game_info.player_start_location))
        return sorted_depots[0].negative_offset(direction)


@dataclass
class GameInfo:
    _proto: Any = None

    # Filled later by BotAI._prepare_first_step
    player_start_location: Point2 = None  # type: ignore

    _pathing_grid: PixelMap = None  # type: ignore
    _map_ramps: List[Ramp] = None  # type: ignore
    _vision_blockers: FrozenSet[Point2] = None  # type: ignore

    @cached_property
    def players(self) -> List[Player]:
        return [Player.from_proto(p) for p in self._proto.player_info]

    @property
    def map_name(self) -> str:
        return self._proto.map_name

    @property
    def local_map_path(self) -> str:
        return self._proto.local_map_path

    @cached_property
    def map_size(self) -> Size:
        return Size.from_proto(self._proto.start_raw.map_size)

    @property
    def pathing_grid(self) -> PixelMap:
        # self.pathing_grid[point]: if 0 point is not pathable, if 1 point is pathable
        if self._pathing_grid is None:
            self._pathing_grid: PixelMap = PixelMap(self._proto.start_raw.pathing_grid, in_bits=True)
        return self._pathing_grid

    @cached_property
    def terrain_height(self) -> PixelMap:
        # self.terrain_height[point]: returns the height in range of 0 to 255 at that point
        return PixelMap(self._proto.start_raw.terrain_height)

    @cached_property
    def placement_grid(self) -> PixelMap:
        # self.placement_grid[point]: if 0 point is not placeable, if 1 point is pathable
        return PixelMap(self._proto.start_raw.placement_grid, in_bits=True)

    @cached_property
    def playable_area(self) -> Rect:
        # self.placement_grid[point]: if 0 point is not placeable, if 1 point is pathable
        return Rect.from_proto(self._proto.start_raw.playable_area)

    @cached_property
    def map_center(self) -> Point2:
        # self.placement_grid[point]: if 0 point is not placeable, if 1 point is pathable
        return self.playable_area.center

    def _calc_map_ramps_and_vision_blockers(self):
        self._map_ramps, self._vision_blockers = self._find_ramps_and_vision_blockers()

    @property
    def map_ramps(self) -> List[Ramp]:
        if self._map_ramps is None:
            self._calc_map_ramps_and_vision_blockers()
        return self._map_ramps

    @property
    def vision_blockers(self) -> FrozenSet[Point2]:
        if self._vision_blockers is None:
            self._calc_map_ramps_and_vision_blockers()
        return self._vision_blockers

    @cached_property
    def player_races(self) -> Dict[int, Race]:
        return {p.player_id: p.race_actual or p.race_requested for p in self._proto.player_info}

    @cached_property
    def start_locations(self) -> List[Point2]:
        return [Point2.from_proto(sl) for sl in self._proto.start_raw.start_locations]

    def _find_ramps_and_vision_blockers(self) -> Tuple[List[Ramp], FrozenSet[Point2]]:
        """Calculate points that are pathable but not placeable.
        Then divide them into ramp points if not all points around the points are equal height
        and into vision blockers if they are."""

        def equal_height_around(tile: Point2) -> bool:
            # mask to slice array 1 around tile
            sliced = self.terrain_height.data_numpy[tile[1] - 1:tile[1] + 2, tile[0] - 1:tile[0] + 2]
            return len(np.unique(sliced)) == 1

        # all points in the playable area that are pathable but not placable
        mixed_numpy_array: np.ndarray = self.pathing_grid.data_numpy & (1 - self.placement_grid.data_numpy)
        # ramp points are already inside the playable area, so no need to check that
        points = (Point2((x, y)) for y, x in np.argwhere(mixed_numpy_array == 1))

        # divide points into ramp points and vision blockers
        ramp_points = []
        vision_blockers = []
        for point in points:
            if equal_height_around(point):
                vision_blockers.append(point)
            else:
                ramp_points.append(point)
        ramps = [Ramp(group, self) for group in self._find_groups(ramp_points)]
        return ramps, frozenset(vision_blockers)

    def _find_groups(self, points: Iterable[Point2], minimum_points_per_group: int = 8) -> Iterable[FrozenSet[Point2]]:
        """
        From a set of points, this function will try to group points together by
        painting clusters of points in a rectangular map using flood fill algorithm.
        Returns groups of points as list, like [{p1, p2, p3}, {p4, p5, p6, p7, p8}]
        """
        # TODO do we actually need colors here? the ramps will never touch anyways.
        NOT_COLORED_YET = -1
        map_width = self.pathing_grid.width
        map_height = self.pathing_grid.height
        current_color: int = NOT_COLORED_YET
        picture: List[List[int]] = [[-2 for _ in range(map_width)] for _ in range(map_height)]

        def paint(pt: Point2) -> None:
            picture[pt.y][pt.x] = current_color

        nearby: List[Tuple[int, int]] = [(x, y) for x in [-1, 0, 1] for y in [-1, 0, 1] if x != 0 or y != 0]

        remaining: Set[Point2] = set(points)
        for point_r in remaining:
            paint(point_r)
        current_color = 1
        queue: Deque[Point2] = deque()
        while remaining:
            current_group: Set[Point2] = set()
            if not queue:
                start = remaining.pop()
                paint(start)
                queue.append(start)
                current_group.add(start)
            while queue:
                base: Point2 = queue.popleft()
                for offset in nearby:
                    px, py = base.x + offset[0], base.y + offset[1]
                    # Do we ever reach out of map bounds?
                    if not (0 <= px < map_width and 0 <= py < map_height):
                        continue
                    if picture[py][px] != NOT_COLORED_YET:
                        continue
                    point: Point2 = Point2((px, py))
                    remaining.discard(point)
                    paint(point)
                    queue.append(point)
                    current_group.add(point)
            if len(current_group) >= minimum_points_per_group:
                yield frozenset(current_group)
