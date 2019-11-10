from __future__ import annotations
from bisect import bisect_left
from functools import lru_cache
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

from .constants import ZERGLING
from .data import Attribute, Race
from .ids.ability_id import AbilityId
from .ids.unit_typeid import UnitTypeId
from .unit_command import UnitCommand

# Set of parts of names of abilities that have no cost
# E.g every ability that has 'Hold' in its name is free
# TODO move to constants, add more?
FREE_ABILITIES = {"Lower", "Raise", "Land", "Lift", "Hold", "Harvest"}


class GameData:
    def __init__(self, data):
        """
        :param data:
        """
        ids = set(a.value for a in AbilityId if a.value != 0)
        self.abilities = {a.ability_id: AbilityData(self, a) for a in data.abilities if a.ability_id in ids}
        self.units = {u.unit_id: UnitTypeData(self, u) for u in data.units if u.available}
        self.upgrades = {u.upgrade_id: UpgradeData(self, u) for u in data.upgrades}
        # Cached UnitTypeIds so that conversion does not take long. This needs to be moved elsewhere if a new GameData object is created multiple times per game
        self.unit_types: Dict[int, UnitTypeId] = {}

    @lru_cache(maxsize=256)
    def calculate_ability_cost(self, ability) -> Cost:
        if isinstance(ability, AbilityId):
            ability = self.abilities[ability.value]
        elif isinstance(ability, UnitCommand):
            ability = self.abilities[ability.ability.value]

        assert isinstance(ability, AbilityData), f"C: {ability}"

        for unit in self.units.values():
            if unit.creation_ability is None:
                continue

            if not AbilityData.id_exists(unit.creation_ability.id.value):
                continue

            if unit.creation_ability.is_free_morph:
                continue

            if unit.creation_ability == ability:
                if unit.id == ZERGLING:
                    # HARD CODED: zerglings are generated in pairs
                    return Cost(unit.cost.minerals * 2, unit.cost.vespene * 2, unit.cost.time)
                # Correction for morphing units, e.g. orbital would return 550/0 instead of actual 150/0
                morph_cost = unit.morph_cost
                if morph_cost:  # can be None
                    return morph_cost
                # Correction for zerg structures without morph: Extractor would return 75 instead of actual 25
                return unit.cost_zerg_corrected

        for upgrade in self.upgrades.values():
            if upgrade.research_ability == ability:
                return upgrade.cost

        return Cost(0, 0)


class AbilityData:

    ability_ids: List[int] = [ability_id.value for ability_id in AbilityId][1:]  # sorted list

    @classmethod
    def id_exists(cls, ability_id):
        assert isinstance(ability_id, int), f"Wrong type: {ability_id} is not int"
        if ability_id == 0:
            return False
        i = bisect_left(cls.ability_ids, ability_id)  # quick binary search
        return i != len(cls.ability_ids) and cls.ability_ids[i] == ability_id

    def __init__(self, game_data, proto):
        self._game_data = game_data
        self._proto = proto

        # What happens if we comment this out? Should this not be commented out? What is its purpose?
        assert self.id != 0

    def __repr__(self) -> str:
        return f"AbilityData(name={self._proto.button_name})"

    @property
    def id(self) -> AbilityId:
        if self._proto.remaps_to_ability_id:
            return AbilityId(self._proto.remaps_to_ability_id)
        return AbilityId(self._proto.ability_id)

    @property
    def link_name(self) -> str:
        """ For Stimpack this returns 'BarracksTechLabResearch' """
        return self._proto.link_name

    @property
    def button_name(self) -> str:
        """ For Stimpack this returns 'Stimpack' """
        return self._proto.button_name

    @property
    def friendly_name(self) -> str:
        """ For Stimpack this returns 'Research Stimpack' """
        return self._proto.friendly_name

    @property
    def is_free_morph(self) -> bool:
        if any(free in self._proto.link_name for free in FREE_ABILITIES):
            return True
        return False

    @property
    def cost(self) -> Cost:
        return self._game_data.calculate_ability_cost(self.id)


class UnitTypeData:
    def __init__(self, game_data: GameData, proto):
        """
        :param game_data:
        :param proto:
        """
        # The ability_id for lurkers is
        # LURKERASPECTMPFROMHYDRALISKBURROWED_LURKERMPFROMHYDRALISKBURROWED
        # instead of the correct MORPH_LURKER.
        if proto.unit_id == UnitTypeId.LURKERMP.value:
            proto.ability_id = AbilityId.MORPH_LURKER.value

        self._game_data = game_data
        self._proto = proto

    def __repr__(self) -> str:
        return f"UnitTypeData(name={self.name})"

    @property
    def id(self) -> UnitTypeId:
        return UnitTypeId(self._proto.unit_id)

    @property
    def name(self) -> str:
        return self._proto.name

    @property
    def creation_ability(self) -> Optional[AbilityData]:
        if self._proto.ability_id == 0:
            return None
        if self._proto.ability_id not in self._game_data.abilities:
            return None
        return self._game_data.abilities[self._proto.ability_id]

    @property
    def attributes(self) -> List[Attribute]:
        return self._proto.attributes

    def has_attribute(self, attr) -> bool:
        assert isinstance(attr, Attribute)
        return attr in self.attributes

    @property
    def has_minerals(self) -> bool:
        return self._proto.has_minerals

    @property
    def has_vespene(self) -> bool:
        return self._proto.has_vespene

    @property
    def cargo_size(self) -> int:
        """ How much cargo this unit uses up in cargo_space """
        return self._proto.cargo_size

    @property
    def tech_requirement(self) -> Optional[UnitTypeId]:
        """ Tech-building requirement of buildings - may work for units but unreliably """
        if self._proto.tech_requirement == 0:
            return None
        if self._proto.tech_requirement not in self._game_data.units:
            return None
        return UnitTypeId(self._proto.tech_requirement)

    @property
    def tech_alias(self) -> Optional[List[UnitTypeId]]:
        """ Building tech equality, e.g. OrbitalCommand is the same as CommandCenter
        Building tech equality, e.g. Hive is the same as Lair and Hatchery
        For Hive, this returns [UnitTypeId.Hatchery, UnitTypeId.Lair]
        For SCV, this returns None """
        return_list = [
            UnitTypeId(tech_alias) for tech_alias in self._proto.tech_alias if tech_alias in self._game_data.units
        ]
        return return_list if return_list else None

    @property
    def unit_alias(self) -> Optional[UnitTypeId]:
        """ Building type equality, e.g. FlyingOrbitalCommand is the same as OrbitalCommand """
        if self._proto.unit_alias == 0:
            return None
        if self._proto.unit_alias not in self._game_data.units:
            return None
        """ For flying OrbitalCommand, this returns UnitTypeId.OrbitalCommand """
        return UnitTypeId(self._proto.unit_alias)

    @property
    def race(self) -> Race:
        return Race(self._proto.race)

    @property
    def cost(self) -> Cost:
        return Cost(self._proto.mineral_cost, self._proto.vespene_cost, self._proto.build_time)

    @property
    def cost_zerg_corrected(self) -> Cost:
        """ This returns 25 for extractor and 200 for spawning pool instead of 75 and 250 respectively """
        if self.race == Race.Zerg and Attribute.Structure.value in self.attributes:
            # a = self._game_data.units(UnitTypeId.ZERGLING)
            # print(a)
            # print(vars(a))
            return Cost(self._proto.mineral_cost - 50, self._proto.vespene_cost, self._proto.build_time)
        else:
            return self.cost

    @property
    def morph_cost(self) -> Optional[Cost]:
        """ This returns 150 minerals for OrbitalCommand instead of 550 """
        # Fix for BARRACKSREACTOR which has tech alias [REACTOR] which has (0, 0) cost
        if self.tech_alias is None or self.tech_alias[0] in {UnitTypeId.TECHLAB, UnitTypeId.REACTOR}:
            return None
        # Morphing a HIVE would have HATCHERY and LAIR in the tech alias - now subtract HIVE cost from LAIR cost instead of from HATCHERY cost
        tech_alias_cost_minerals = max(
            self._game_data.units[tech_alias.value].cost.minerals for tech_alias in self.tech_alias
        )
        tech_alias_cost_vespene = max(
            self._game_data.units[tech_alias.value].cost.vespene for tech_alias in self.tech_alias
        )
        return Cost(
            self._proto.mineral_cost - tech_alias_cost_minerals,
            self._proto.vespene_cost - tech_alias_cost_vespene,
            self._proto.build_time,
        )


class UpgradeData:
    def __init__(self, game_data: GameData, proto):
        """
        :param game_data:
        :param proto:
        """
        self._game_data = game_data
        self._proto = proto

    def __repr__(self):
        return f"UpgradeData({self.name} - research ability: {self.research_ability}, {self.cost})"

    @property
    def name(self) -> str:
        return self._proto.name

    @property
    def research_ability(self) -> Optional[AbilityData]:
        if self._proto.ability_id == 0:
            return None
        if self._proto.ability_id not in self._game_data.abilities:
            return None
        return self._game_data.abilities[self._proto.ability_id]

    @property
    def cost(self) -> Cost:
        return Cost(self._proto.mineral_cost, self._proto.vespene_cost, self._proto.research_time)


class Cost:
    def __init__(self, minerals: int, vespene: int, time: float = None):
        """
        :param minerals:
        :param vespene:
        :param time:
        """
        self.minerals = minerals
        self.vespene = vespene
        self.time = time

    def __repr__(self) -> str:
        return f"Cost({self.minerals}, {self.vespene})"

    def __eq__(self, other: Cost) -> bool:
        return self.minerals == other.minerals and self.vespene == other.vespene

    def __ne__(self, other: Cost) -> bool:
        return self.minerals != other.minerals or self.vespene != other.vespene

    def __bool__(self) -> bool:
        return self.minerals != 0 or self.vespene != 0

    def __add__(self, other) -> Cost:
        if not other:
            return self
        if not self:
            return other
        if self.time is None:
            time = other.time
        elif other.time is None:
            time = self.time
        else:
            time = self.time + other.time
        return self.__class__(self.minerals + other.minerals, self.vespene + other.vespene, time=time)

    def __sub__(self, other) -> Cost:
        assert isinstance(other, Cost)
        if self.time is None:
            time = other.time
        elif other.time is None:
            time = self.time
        else:
            time = self.time - other.time
        return self.__class__(self.minerals - other.minerals, self.vespene - other.vespene, time=time)

    def __mul__(self, other: int) -> Cost:
        return self.__class__(self.minerals * other, self.vespene * other, time=self.time)

    def __rmul__(self, other: int) -> Cost:
        return self.__class__(self.minerals * other, self.vespene * other, time=self.time)
