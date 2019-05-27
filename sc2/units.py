import random
import warnings
from itertools import chain
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple, Union

from .ids.unit_typeid import UnitTypeId
from .position import Point2, Point3
from .unit import Unit, UnitGameData

warnings.simplefilter("once")


class Units(list):
    """A collection of Unit objects. Makes it easy to select units by selectors."""

    # TODO: You dont need to provide game_data any more.
    # Add keyword argument 'game_data=None' to provide downwards
    # compatibility for bots that use '__init__' or 'from_proto' functions.
    @classmethod
    def from_proto(cls, units, game_data=None):  # game_data=None
        if game_data:
            warnings.warn(
                "Keyword argument 'game_data' in Units classmethod 'from_proto' is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
            warnings.warn(
                "You can safely remove it from your Units objects created by the classmethod.",
                DeprecationWarning,
                stacklevel=2,
            )
        return cls((Unit(u) for u in units))

    def __init__(self, units, game_data=None):
        if game_data:
            warnings.warn(
                "Keyword argument 'game_data' in Units function '__init__' is deprecated.",
                DeprecationWarning,
                stacklevel=2,
            )
            warnings.warn(
                "You can safely remove it from your Units objects initializations.", DeprecationWarning, stacklevel=2
            )
        super().__init__(units)

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
            )
        )

    def __and__(self, other: "Units") -> "Units":
        return Units(other_unit for other_unit in other if other_unit.tag in (self_unit.tag for self_unit in self))

    def __sub__(self, other: "Units") -> "Units":
        return Units(self_unit for self_unit in self if self_unit.tag not in (other_unit.tag for other_unit in other))

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

    # NOTE former argument 'require_all' is not needed any more
    def take(self, n: int, require_all=None) -> "Units":
        if require_all:
            warnings.warn("Argument 'require_all' in function 'take' is deprecated", DeprecationWarning, stacklevel=2)
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

    # NOTE former argument 'require_all' is not needed any more
    def random_group_of(self, n: int, require_all=None) -> "Units":
        """ Returns self if n >= self.amount. """
        if require_all:
            warnings.warn(
                "Argument 'require_all' in function 'random_group_of' is deprecated", DeprecationWarning, stacklevel=2
            )
        if n < 1:
            return Units([])
        elif n >= self.amount:
            return self
        else:
            return self.subgroup(random.sample(self, n))

    def in_attack_range_of(self, unit: Unit, bonus_distance: Union[int, float] = 0) -> "Units":
        """ Filters units that are in attack range of the unit in parameter """
        return self.filter(lambda x: unit.target_in_range(x, bonus_distance=bonus_distance))

    def closest_distance_to(self, position: Union[Unit, Point2, Point3]) -> Union[int, float]:
        """ Returns the distance between the closest unit from this group to the target unit """
        assert self, "Units object is empty"
        position = position.position
        return position.distance_to_closest(u.position for u in self)

    def furthest_distance_to(self, position: Union[Unit, Point2, Point3]) -> Union[int, float]:
        """ Returns the distance between the furthest unit from this group to the target unit """
        assert self, "Units object is empty"
        position = position.position
        return position.distance_to_furthest(u.position for u in self)

    def closest_to(self, position: Union[Unit, Point2, Point3]) -> Unit:
        assert self, "Units object is empty"
        position = position.position
        return position.closest(self)

    def furthest_to(self, position: Union[Unit, Point2, Point3]) -> Unit:
        assert self, "Units object is empty"
        if isinstance(position, Unit):
            position = position.position
        return position.furthest(self)

    def closer_than(self, distance: Union[int, float], position: Union[Unit, Point2, Point3]) -> "Units":
        position = position.position
        return self.filter(lambda unit: unit.distance_to(position.to2) < distance)

    def further_than(self, distance: Union[int, float], position: Union[Unit, Point2, Point3]) -> "Units":
        position = position.position
        return self.filter(lambda unit: unit.distance_to(position.to2) > distance)

    def subgroup(self, units):
        return Units(units)

    def filter(self, pred: callable) -> "Units":
        return self.subgroup(filter(pred, self))

    def sorted(self, keyfn: callable, reverse: bool = False) -> "Units":
        return self.subgroup(sorted(self, key=keyfn, reverse=reverse))

    def sorted_by_distance_to(self, position: Union[Unit, Point2], reverse: bool = False) -> "Units":
        """ This function should be a bit faster than using units.sorted(keyfn=lambda u: u.distance_to(position)) """
        position = position.position
        return self.sorted(keyfn=lambda unit: unit.distance_to(position), reverse=reverse)

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
        # example: self.known_enemy_units.exclude_type([OVERLORD])
        if isinstance(other, UnitTypeId):
            other = {other}
        if isinstance(other, list):
            other = set(other)
        return self.filter(lambda unit: unit.type_id not in other)

    def same_tech(self, other: Union[UnitTypeId, Set[UnitTypeId], List[UnitTypeId], Dict[UnitTypeId, Any]]) -> "Units":
        """ Usage:
        'self.units.same_tech(UnitTypeId.COMMANDCENTER)' or 'self.units.same_tech(UnitTypeId.ORBITALCOMMAND)'
        returns all CommandCenter, CommandCenterFlying, OrbitalCommand, OrbitalCommandFlying, PlanetaryFortress
        This also works with a set/list/dict parameter, e.g. 'self.units.same_tech({UnitTypeId.COMMANDCENTER, UnitTypeId.SUPPLYDEPOT})'
        Untested: This should return the equivalents for Hatchery, WarpPrism, Observer, Overseer, SupplyDepot and others
        """
        if isinstance(other, UnitTypeId):
            other = {other}
        tech_alias_types = set(other)
        unit_data = UnitGameData._game_data.units
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
        'self.units.same_tech(UnitTypeId.COMMANDCENTER)'
        returns CommandCenter and CommandCenterFlying,
        'self.units.same_tech(UnitTypeId.ORBITALCOMMAND)'
        returns OrbitalCommand and OrbitalCommandFlying
        This also works with a set/list/dict parameter, e.g. 'self.units.same_tech({UnitTypeId.COMMANDCENTER, UnitTypeId.SUPPLYDEPOT})'
        Untested: This should return the equivalents for WarpPrism, Observer, Overseer, SupplyDepot and other units that have different modes but still act as the same unit
        """
        if isinstance(other, UnitTypeId):
            other = {other}
        unit_alias_types = set(other)
        unit_data = UnitGameData._game_data.units
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
        pos = Point2((sum(unit.position.x for unit in self) / amount, sum(unit.position.y for unit in self) / amount))
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
    def noqueue(self) -> "Units":
        warnings.warn("noqueue will be removed soon, please use idle instead", DeprecationWarning, stacklevel=2)
        return self.idle

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

    def prefer_close_to(self, p: Union[Unit, Point2, Point3]) -> "Units":
        warnings.warn(
            "prefer_close_to will be removed soon, please use sorted_by_distance_to instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.sorted_by_distance_to(p)


class UnitSelection(Units):
    def __init__(self, parent, selection=None):
        if isinstance(selection, (UnitTypeId)):
            super().__init__(unit for unit in parent if unit.type_id == selection)
        elif isinstance(selection, set):
            assert all(isinstance(t, UnitTypeId) for t in selection), f"Not all ids in selection are of type UnitTypeId"
            super().__init__(unit for unit in parent if unit.type_id in selection)
        elif selection is None:
            super().__init__(unit for unit in parent)
        else:
            assert isinstance(
                selection, (UnitTypeId, set)
            ), f"selection is not None or of type UnitTypeId or Set[UnitTypeId]"
