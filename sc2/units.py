import random
import warnings
import math
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from .ids.unit_typeid import UnitTypeId
from .position import Point2, Point3
from .unit import Unit
import numpy as np

from .cache import property_immutable_cache

warnings.simplefilter("once")


class Units(list):
    """A collection of Unit objects. Makes it easy to select units by selectors."""

    @classmethod
    def from_proto(cls, units, bot_object: "BotAI"):
        return cls((Unit(u, bot_object=bot_object) for u in units))

    def __init__(self, units, bot_object: "BotAI"):
        super().__init__(units)
        self._bot_object = bot_object

    def __call__(self, *args, **kwargs):
        return UnitSelection(self, *args, **kwargs)

    def select(self, *args, **kwargs):
        return UnitSelection(self, *args, **kwargs)

    def copy(self):
        return self.subgroup(self)

    def __or__(self, other: "Units") -> "Units":
        return Units(
            chain(
                iter(self),
                (other_unit for other_unit in other if other_unit.tag not in (self_unit.tag for self_unit in self)),
            ),
            self._bot_object,
        )

    def __add__(self, other: "Units") -> "Units":
        return Units(
            chain(
                iter(self),
                (other_unit for other_unit in other if other_unit.tag not in (self_unit.tag for self_unit in self)),
            ),
            self._bot_object,
        )

    def __and__(self, other: "Units") -> "Units":
        return Units(
            (other_unit for other_unit in other if other_unit.tag in (self_unit.tag for self_unit in self)),
            self._bot_object,
        )

    def __sub__(self, other: "Units") -> "Units":
        return Units(
            (self_unit for self_unit in self if self_unit.tag not in (other_unit.tag for other_unit in other)),
            self._bot_object,
        )

    def __hash__(self):
        return hash(unit.tag for unit in self)

    @property
    def amount(self) -> int:
        return len(self)

    @property
    def empty(self) -> bool:
        return not bool(self)

    @property
    def exists(self) -> bool:
        return bool(self)

    def find_by_tag(self, tag) -> Optional[Unit]:
        for unit in self:
            if unit.tag == tag:
                return unit
        return None

    def by_tag(self, tag):
        unit = self.find_by_tag(tag)
        if unit is None:
            raise KeyError("Unit not found")
        return unit

    @property
    def first(self) -> Unit:
        assert self, "Units object is empty"
        return self[0]

    def take(self, n: int) -> "Units":
        if n >= self.amount:
            return self
        else:
            return self.subgroup(self[:n])

    @property
    def random(self) -> Unit:
        assert self, "Units object is empty"
        return random.choice(self)

    def random_or(self, other: any) -> Unit:
        return random.choice(self) if self.exists else other

    def random_group_of(self, n: int) -> "Units":
        """ Returns self if n >= self.amount. """
        if n < 1:
            return Units([], self._bot_object)
        elif n >= self.amount:
            return self
        else:
            return self.subgroup(random.sample(self, n))

    # TODO: append, remove, extend and pop functions should reset the cache for Units.positions because the number of units in the list has changed
    # @property_immutable_cache
    # def positions(self) -> np.ndarray:
    #     flat_units_positions = (coord for unit in self for coord in unit.position)
    #     unit_positions_np = np.fromiter(flat_units_positions, dtype=float, count=2 * len(self)).reshape((len(self), 2))
    #     return unit_positions_np

    def in_attack_range_of(self, unit: Unit, bonus_distance: Union[int, float] = 0) -> "Units":
        """ Filters units that are in attack range of the unit in parameter """
        return self.filter(lambda x: unit.target_in_range(x, bonus_distance=bonus_distance))

    def closest_distance_to(self, position: Union[Unit, Point2, Point3]) -> float:
        """ Returns the distance between the closest unit from this group to the target unit """
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            return min(self._bot_object._distance_squared_unit_to_unit(unit, position) for unit in self) ** 0.5
        # TODO: improve using numpy to calculate closest to the target if target is point
        return min(self._bot_object._distance_units_to_pos(self, position))

    def furthest_distance_to(self, position: Union[Unit, Point2, Point3]) -> float:
        """ Returns the distance between the furthest unit from this group to the target unit """
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            return max(self._bot_object._distance_squared_unit_to_unit(unit, position) for unit in self) ** 0.5
        return max(self._bot_object._distance_units_to_pos(self, position))

    def closest_to(self, position: Union[Unit, Point2, Point3]) -> Unit:
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            return min(
                (unit1 for unit1 in self),
                key=lambda unit2: self._bot_object._distance_squared_unit_to_unit(unit2, position),
            )

        distances = self._bot_object._distance_units_to_pos(self, position)
        return min(((unit, dist) for unit, dist in zip(self, distances)), key=lambda my_tuple: my_tuple[1])[0]

    def furthest_to(self, position: Union[Unit, Point2, Point3]) -> Unit:
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            return max(
                (unit1 for unit1 in self),
                key=lambda unit2: self._bot_object._distance_squared_unit_to_unit(unit2, position),
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        return max(((unit, dist) for unit, dist in zip(self, distances)), key=lambda my_tuple: my_tuple[1])[0]

    def closer_than(self, distance: Union[int, float], position: Union[Unit, Point2, Point3]) -> "Units":
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            distance_squared = distance ** 2
            return self.subgroup(
                unit
                for unit in self
                if self._bot_object._distance_squared_unit_to_unit(unit, position) < distance_squared
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        return self.subgroup(unit for unit, dist in zip(self, distances) if dist < distance)

    def further_than(self, distance: Union[int, float], position: Union[Unit, Point2, Point3]) -> "Units":
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            distance_squared = distance ** 2
            return self.subgroup(
                unit
                for unit in self
                if distance_squared < self._bot_object._distance_squared_unit_to_unit(unit, position)
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        return self.subgroup(unit for unit, dist in zip(self, distances) if distance < dist)

    def in_distance_between(
        self, position: Union[Unit, Point2, Tuple[float, float]], distance1: float, distance2: float
    ) -> "Units":
        """ Returns units that are further than distance1 and closer than distance2 to position """
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            distance1_squared = distance1 ** 2
            distance2_squared = distance2 ** 2
            return self.subgroup(
                unit
                for unit in self
                if distance1_squared
                < self._bot_object._distance_squared_unit_to_unit(unit, position)
                < distance2_squared
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        return self.subgroup(unit for unit, dist in zip(self, distances) if distance1 < dist < distance2)

    def closest_n_units(self, position: Union[Unit, Point2], n: int) -> "Units":
        """ Returns the n closest units in distance to position """
        assert self, "Units object is empty"
        return self.subgroup(self._list_sorted_by_distance_to(position)[:n])

    def furthest_n_units(self, position: Union[Unit, Point2, np.ndarray], n: int) -> "Units":
        """ Returns the n furthest units in distance to position """
        assert self, "Units object is empty"
        return self.subgroup(self._list_sorted_by_distance_to(position)[-n:])

    def in_distance_of_group(self, other_units: "Units", distance: float) -> "Units":
        """ Returns units that are closer than distance from any unit in the other units object """
        assert other_units, "Other units object is empty"
        # Return self because there are no enemies
        if not self:
            return self
        distance_squared = distance ** 2
        if len(self) == 1:
            if any(
                self._bot_object._distance_squared_unit_to_unit(self[0], target) < distance_squared
                for target in other_units
            ):
                return self
            else:
                return self.subgroup([])

        return self.subgroup(
            self_unit
            for self_unit in self
            if any(
                self._bot_object._distance_squared_unit_to_unit(self_unit, other_unit) < distance_squared
                for other_unit in other_units
            )
        )

    def in_closest_distance_to_group(self, other_units: "Units") -> Unit:
        """ Returns unit in shortest distance from any unit in self to any unit in group. """
        assert self, "Units object is empty"
        assert other_units, "Given units object is empty"
        return min(
            self,
            key=lambda self_unit: min(
                self._bot_object._distance_squared_unit_to_unit(self_unit, other_unit) for other_unit in other_units
            ),
        )

    def _list_sorted_closest_to_distance(self, position: Union[Unit, Point2], distance: float) -> List[Unit]:
        """ This function should be a bit faster than using units.sorted(key=lambda u: u.distance_to(position)) """
        if isinstance(position, Unit):
            return sorted(
                self,
                key=lambda unit: abs(self._bot_object._distance_squared_unit_to_unit(unit, position) - distance),
                reverse=True,
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        unit_dist_dict = {unit.tag: dist for unit, dist in zip(self, distances)}
        return sorted(self, key=lambda unit2: abs(unit_dist_dict[unit2.tag] - distance), reverse=True)

    def n_closest_to_distance(
        self, position: Union[Point2, np.ndarray], distance: Union[int, float], n: int
    ) -> "Units":
        """ Returns n units that are the closest to distance away.
        For example if the distance is set to 5 and you want 3 units, from units with distance [3, 4, 5, 6, 7]
        the units with distacnce [4, 5, 6] will be selected """
        return self.subgroup(self._list_sorted_closest_to_distance(position=position, distance=distance)[:n])

    def n_furthest_to_distance(
        self, position: Union[Point2, np.ndarray], distance: Union[int, float], n: int
    ) -> "Units":
        """ Inverse of the function above """
        return self.subgroup(self._list_sorted_closest_to_distance(position=position, distance=distance)[-n:])

    def subgroup(self, units):
        return Units(units, self._bot_object)

    def filter(self, pred: callable) -> "Units":
        assert callable(pred), "Function is not callable"
        return self.subgroup(filter(pred, self))

    def sorted(self, key: callable, reverse: bool = False) -> "Units":
        return self.subgroup(sorted(self, key=key, reverse=reverse))

    def _list_sorted_by_distance_to(self, position: Union[Unit, Point2], reverse: bool = False) -> List[Unit]:
        """ This function should be a bit faster than using units.sorted(key=lambda u: u.distance_to(position)) """
        if isinstance(position, Unit):
            return sorted(
                self, key=lambda unit: self._bot_object._distance_squared_unit_to_unit(unit, position), reverse=reverse
            )
        distances = self._bot_object._distance_units_to_pos(self, position)
        unit_dist_dict = {unit.tag: dist for unit, dist in zip(self, distances)}
        return sorted(self, key=lambda unit2: unit_dist_dict[unit2.tag], reverse=reverse)

    def sorted_by_distance_to(self, position: Union[Unit, Point2], reverse: bool = False) -> "Units":
        """ This function should be a bit faster than using units.sorted(key=lambda u: u.distance_to(position)) """
        return self.subgroup(self._list_sorted_by_distance_to(position, reverse=reverse))

    def tags_in(self, other: Union[Set[int], List[int], Dict[int, Any]]) -> "Units":
        """ Filters all units that have their tags in the 'other' set/list/dict """
        # example: self.units(QUEEN).tags_in(self.queen_tags_assigned_to_do_injects)
        return self.filter(lambda unit: unit.tag in other)

    def tags_not_in(self, other: Union[Set[int], List[int], Dict[int, Any]]) -> "Units":
        """ Filters all units that have their tags not in the 'other' set/list/dict """
        # example: self.units(QUEEN).tags_not_in(self.queen_tags_assigned_to_do_injects)
        return self.filter(lambda unit: unit.tag not in other)

    def of_type(self, other: Union[UnitTypeId, Set[UnitTypeId], List[UnitTypeId], Dict[UnitTypeId, Any]]) -> "Units":
        """ Filters all units that are of a specific type """
        # example: self.units.of_type([ZERGLING, ROACH, HYDRALISK, BROODLORD])
        if isinstance(other, UnitTypeId):
            other = {other}
        return self.filter(lambda unit: unit.type_id in other)

    def exclude_type(
        self, other: Union[UnitTypeId, Set[UnitTypeId], List[UnitTypeId], Dict[UnitTypeId, Any]]
    ) -> "Units":
        """ Filters all units that are not of a specific type """
        # example: self.enemy_units.exclude_type([OVERLORD])
        if isinstance(other, UnitTypeId):
            other = {other}
        if isinstance(other, list):
            other = set(other)
        return self.filter(lambda unit: unit.type_id not in other)

    def same_tech(self, other: Union[UnitTypeId, Set[UnitTypeId], List[UnitTypeId], Dict[UnitTypeId, Any]]) -> "Units":
        """ Usage:
        'self.townhalls.same_tech(UnitTypeId.COMMANDCENTER)' or 'self.townhalls.same_tech(UnitTypeId.ORBITALCOMMAND)'
        returns all CommandCenter, CommandCenterFlying, OrbitalCommand, OrbitalCommandFlying, PlanetaryFortress
        This also works with a set/list/dict parameter, e.g. 'self.structures.same_tech({UnitTypeId.COMMANDCENTER, UnitTypeId.SUPPLYDEPOT})'
        Untested: This should return the equivalents for Hatchery, WarpPrism, Observer, Overseer, SupplyDepot and others
        """
        if isinstance(other, UnitTypeId):
            other = {other}
        tech_alias_types = set(other)
        unit_data = self._bot_object._game_data.units
        for unitType in other:
            tech_alias = unit_data[unitType.value].tech_alias
            if tech_alias:
                for same in tech_alias:
                    tech_alias_types.add(same)
        return self.filter(
            lambda unit: unit.type_id in tech_alias_types
            or unit._type_data.tech_alias is not None
            and any(same in tech_alias_types for same in unit._type_data.tech_alias)
        )

    def same_unit(self, other: Union[UnitTypeId, Set[UnitTypeId], List[UnitTypeId], Dict[UnitTypeId, Any]]) -> "Units":
        """ Usage:
        'self.townhalls.same_tech(UnitTypeId.COMMANDCENTER)'
        returns CommandCenter and CommandCenterFlying,
        'self.townhalls.same_tech(UnitTypeId.ORBITALCOMMAND)'
        returns OrbitalCommand and OrbitalCommandFlying
        This also works with a set/list/dict parameter, e.g. 'self.structures.same_tech({UnitTypeId.COMMANDCENTER, UnitTypeId.SUPPLYDEPOT})'
        Untested: This should return the equivalents for WarpPrism, Observer, Overseer, SupplyDepot and other units that have different modes but still act as the same unit
        """
        if isinstance(other, UnitTypeId):
            other = {other}
        unit_alias_types = set(other)
        unit_data = self._bot_object._game_data.units
        for unitType in other:
            unit_alias = unit_data[unitType.value].unit_alias
            if unit_alias:
                unit_alias_types.add(unit_alias)
        return self.filter(
            lambda unit: unit.type_id in unit_alias_types
            or unit._type_data.unit_alias is not None
            and unit._type_data.unit_alias in unit_alias_types
        )

    @property
    def center(self) -> Point2:
        """ Returns the central point of all units in this list """
        assert self, f"Units object is empty"
        amount = self.amount
        pos = Point2(
            (
                sum(unit.position_tuple[0] for unit in self) / amount,
                sum(unit.position_tuple[1] for unit in self) / amount,
            )
        )
        return pos

    @property
    def selected(self) -> "Units":
        return self.filter(lambda unit: unit.is_selected)

    @property
    def tags(self) -> Set[int]:
        return {unit.tag for unit in self}

    @property
    def ready(self) -> "Units":
        return self.filter(lambda unit: unit.is_ready)

    @property
    def not_ready(self) -> "Units":
        return self.filter(lambda unit: not unit.is_ready)

    @property
    def idle(self) -> "Units":
        return self.filter(lambda unit: unit.is_idle)

    @property
    def owned(self) -> "Units":
        return self.filter(lambda unit: unit.is_mine)

    @property
    def enemy(self) -> "Units":
        return self.filter(lambda unit: unit.is_enemy)

    @property
    def flying(self) -> "Units":
        return self.filter(lambda unit: unit.is_flying)

    @property
    def not_flying(self) -> "Units":
        return self.filter(lambda unit: not unit.is_flying)

    @property
    def structure(self) -> "Units":
        return self.filter(lambda unit: unit.is_structure)

    @property
    def not_structure(self) -> "Units":
        return self.filter(lambda unit: not unit.is_structure)

    @property
    def gathering(self) -> "Units":
        return self.filter(lambda unit: unit.is_gathering)

    @property
    def returning(self) -> "Units":
        return self.filter(lambda unit: unit.is_returning)

    @property
    def collecting(self) -> "Units":
        return self.filter(lambda unit: unit.is_collecting)

    @property
    def visible(self) -> "Units":
        return self.filter(lambda unit: unit.is_visible)

    @property
    def mineral_field(self) -> "Units":
        return self.filter(lambda unit: unit.is_mineral_field)

    @property
    def vespene_geyser(self) -> "Units":
        return self.filter(lambda unit: unit.is_vespene_geyser)

    @property
    def prefer_idle(self) -> "Units":
        return self.sorted(lambda unit: unit.is_idle, reverse=True)


class UnitSelection(Units):
    def __init__(self, parent, selection=None):
        if isinstance(selection, (UnitTypeId)):
            super().__init__((unit for unit in parent if unit.type_id == selection), parent._bot_object)
        elif isinstance(selection, set):
            assert all(isinstance(t, UnitTypeId) for t in selection), f"Not all ids in selection are of type UnitTypeId"
            super().__init__((unit for unit in parent if unit.type_id in selection), parent._bot_object)
        elif selection is None:
            super().__init__((unit for unit in parent), parent._bot_object)
        else:
            assert isinstance(
                selection, (UnitTypeId, set)
            ), f"selection is not None or of type UnitTypeId or Set[UnitTypeId]"
