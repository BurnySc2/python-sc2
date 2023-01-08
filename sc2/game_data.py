# pylint: disable=W0212
from __future__ import annotations

from bisect import bisect_left
from contextlib import suppress
from dataclasses import dataclass, field
from functools import cached_property
from typing import Any, ClassVar, Dict, List, Optional, Set

from google.protobuf.json_format import MessageToDict

from sc2.cache import CacheDict
from sc2.constants import ATTRIBUTES_LITERAL, TARGET_AIR, TARGET_GROUND, WEAPON_TYPE_LITERAL
from sc2.data import Attribute, Race, Target
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId

with suppress(ImportError):
    from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM

# Set of parts of names of abilities that have no cost
# E.g every ability that has 'Hold' in its name is free
FREE_ABILITIES = {"Lower", "Raise", "Land", "Lift", "Hold", "Harvest"}


@dataclass
class GameData:
    _abilities: List[Any] = field(default_factory=list)
    _units: List[Any] = field(default_factory=list)
    _upgrades: List[Any] = field(default_factory=list)
    _buffs: List[Any] = field(default_factory=list)
    _effects: List[Any] = field(default_factory=list)

    _ability_cost_cache: ClassVar[Dict[int, Cost]] = {}

    @classmethod
    def from_proto(cls, data: Any):
        data_as_dict = MessageToDict(data, including_default_value_fields=False, preserving_proto_field_name=True)
        underscore_prepended = {f"_{key}": value for key, value in data_as_dict.items()}
        return GameData(**underscore_prepended)

    @cached_property
    def ids(self) -> Set[Any]:
        return set(a.value for a in AbilityId if a.value != 0)

    @cached_property
    def abilities(self) -> Dict[int, AbilityData]:
        return {
            a['ability_id']: AbilityData(**a, _game_data=self)
            for a in self._abilities if a['ability_id'] in self.ids
        }

    @cached_property
    def units(self) -> Dict[int, UnitTypeData]:
        return {u['unit_id']: UnitTypeData(**u, _game_data=self) for u in self._units if u['available']}

    @cached_property
    def upgrades(self) -> Dict[int, UpgradeData]:
        return {u['upgrade_id']: UpgradeData(**u, _game_data=self) for u in self._upgrades}

    # TODO: Buffs and effects from GameData

    def calculate_ability_cost(self, ability: AbilityId) -> Cost:
        # Cache values if not calculated before
        if not self._ability_cost_cache:
            for unit in self.units.values():
                if unit.creation_ability is None:
                    continue

                if not AbilityData.id_exists(unit.creation_ability.id.value):
                    continue

                if unit.creation_ability.is_free_morph:
                    continue

                if unit.id == UnitTypeId.ZERGLING:
                    # HARD CODED: zerglings are generated in pairs
                    self._ability_cost_cache[unit.ability_id] = Cost(
                        unit.cost.minerals * 2,
                        unit.cost.vespene * 2,
                        unit.cost.time,
                    )
                    continue
                # Correction for morphing units, e.g. orbital would return 550/0 instead of actual 150/0
                morph_cost = unit.morph_cost
                if morph_cost:  # can be None
                    self._ability_cost_cache[unit.ability_id] = morph_cost
                    continue
                # Correction for zerg structures without morph: Extractor would return 75 instead of actual 25
                self._ability_cost_cache[unit.ability_id] = unit.cost_zerg_corrected

            for upgrade in self.upgrades.values():
                upgrade_ability_data = upgrade.research_ability
                if upgrade_ability_data:
                    self._ability_cost_cache[upgrade_ability_data.exact_id.value] = upgrade.cost

        return self._ability_cost_cache.get(ability.value, Cost(0, 0))


@dataclass
class AbilityData:
    ability_id: int = 0
    link_name: str = ''  #: For Stimpack this returns 'BarracksTechLabResearch'
    link_index: int = 0
    button_name: str = ""  #: For Stimpack this returns 'Stimpack'
    friendly_name: str = ""  #: For Stimpack this returns 'Research Stimpack'
    hotkey: str = ""
    remaps_to_ability_id: int = 0

    available: bool = False
    target: str = ""
    allow_minimap: bool = False
    allow_autocast: bool = False
    is_building: bool = False
    footprint_radius: float = 0.0
    is_instant_placement: bool = False
    cast_range: float = 0.0

    _game_data: GameData = None  # type: ignore

    ability_ids: ClassVar[List[int]] = [ability_id.value for ability_id in AbilityId][1:]  # sorted list
    _ability_type_data_remap_cache: ClassVar[CacheDict] = CacheDict()
    _ability_type_data_cache: ClassVar[CacheDict] = CacheDict()

    @classmethod
    def id_exists(cls, ability_id: int) -> bool:
        if ability_id == 0:
            return False
        i = bisect_left(cls.ability_ids, ability_id)  # quick binary search
        return i != len(cls.ability_ids) and cls.ability_ids[i] == ability_id

    def __repr__(self) -> str:
        return f"AbilityData(name={self.button_name})"

    @property
    def target_enum(self) -> Target:
        return Target[self.target]

    @property
    def id(self) -> AbilityId:
        """ Returns the generic remap ID. See sc2/dicts/generic_redirect_abilities.py """
        if self.remaps_to_ability_id:
            return self._ability_type_data_remap_cache.retrieve_and_set(
                self.remaps_to_ability_id, lambda: AbilityId(self.remaps_to_ability_id)
            )
        return self.exact_id

    @property
    def exact_id(self) -> AbilityId:
        """ Returns the exact ID of the ability """
        return self._ability_type_data_cache.retrieve_and_set(self.ability_id, lambda: AbilityId(self.ability_id))

    @property
    def is_free_morph(self) -> bool:
        return any(free in self.link_name for free in FREE_ABILITIES)

    @property
    def cost(self) -> Cost:
        return self._game_data.calculate_ability_cost(self.exact_id)


@dataclass
class DamageBonus:
    attribute: ATTRIBUTES_LITERAL
    bonus: float


@dataclass
class Weapon:
    type: WEAPON_TYPE_LITERAL = "Any"
    damage: float = 0.0
    damage_bonus: List[DamageBonus] = field(default_factory=list)
    attacks: int = 0
    range: float = 0.0
    speed: float = 0.0

    def __post_init__(self):
        self.damage_bonus = [DamageBonus(**bonus) for bonus in self.damage_bonus]  # type: ignore


@dataclass
class UnitTypeData:
    """ Same as https://github.com/Blizzard/s2client-proto/blob/63615821fad543d570d65f8d7ab67f71f33cf663/s2clientprotocol/data.proto#L72 """
    unit_id: int = 0
    name: str = ''
    available: bool = False
    cargo_size: int = 0  #: How much cargo this unit uses up in cargo_space
    mineral_cost: int = 0
    vespene_cost: int = 0
    food_required: float = 0
    food_provided: float = 0
    ability_id: int = 0
    race: Race = "NoRace"  # type: ignore
    build_time: float = 0.0
    has_vespene: bool = False
    has_minerals: bool = False
    sight_range: float = 0.0

    tech_alias: List[int] = field(default_factory=list)
    unit_alias: int = 0

    tech_requirement: int = 0
    require_attached: bool = False

    attributes: List[ATTRIBUTES_LITERAL] = field(default_factory=list)
    movement_speed: float = 0.0
    armor: float = 0.0
    weapons: List[dict] = field(default_factory=list)

    _game_data: GameData = None  # type: ignore
    _unit_type_data_cache: ClassVar[Dict[int, UnitTypeId]] = {}

    def __post_init__(self):
        self.race = Race[self.race]
        # The ability_id for lurkers is
        # LURKERASPECTMPFROMHYDRALISKBURROWED_LURKERMPFROMHYDRALISKBURROWED
        # instead of the correct MORPH_LURKER.
        if self.unit_id == UnitTypeId.LURKERMP.value:
            self.ability_id = AbilityId.MORPH_LURKER.value

    def __repr__(self) -> str:
        return f"UnitTypeData(name={self.name})"

    @property
    def id(self) -> UnitTypeId:
        if self.unit_id not in self._unit_type_data_cache:
            self._unit_type_data_cache[self.unit_id] = UnitTypeId(self.unit_id)
        return self._unit_type_data_cache[self.unit_id]

    @cached_property
    def ground_weapon(self) -> Optional[Weapon]:
        for weapon in self.weapons_list:
            if weapon.type in TARGET_GROUND:
                return weapon
        return None

    @cached_property
    def air_weapon(self) -> Optional[Weapon]:
        for weapon in self.weapons_list:
            if weapon.type in TARGET_AIR:
                return weapon
        return None

    @property
    def weapons_list(self) -> List[Weapon]:
        return [Weapon(**weapon) for weapon in self.weapons]

    @property
    def attributes_enum(self) -> List[Attribute]:
        return [Attribute[attribute] for attribute in self.attributes]

    @property
    def creation_ability(self) -> Optional[AbilityData]:
        if self.ability_id == 0:
            return None
        if self.ability_id not in self._game_data.abilities:
            return None
        return self._game_data.abilities[self.ability_id]

    @property
    def footprint_radius(self) -> Optional[float]:
        """ See unit.py footprint_radius """
        if self.creation_ability is None:
            return None
        return self.creation_ability.footprint_radius

    def has_attribute(self, attribute: ATTRIBUTES_LITERAL) -> bool:
        return attribute in self.attributes

    @property
    def tech_requirement_id(self) -> Optional[UnitTypeId]:
        """ Tech-building requirement of buildings - may work for units but unreliably """
        if self.tech_requirement == 0:
            return None
        if self.tech_requirement not in self._game_data.units:
            return None
        return UnitTypeId(self.tech_requirement)

    @property
    def tech_alias_ids(self) -> Optional[List[UnitTypeId]]:
        """Building tech equality, e.g. OrbitalCommand is the same as CommandCenter
        Building tech equality, e.g. Hive is the same as Lair and Hatchery
        For Hive, this returns [UnitTypeId.Hatchery, UnitTypeId.Lair]
        For SCV, this returns an empty list"""
        return [UnitTypeId(tech_alias) for tech_alias in self.tech_alias if tech_alias in self._game_data.units]

    @property
    def unit_alias_id(self) -> Optional[UnitTypeId]:
        """ Building type equality, e.g. FlyingOrbitalCommand is the same as OrbitalCommand """
        if self.unit_alias == 0:
            return None
        if self.unit_alias not in self._game_data.units:
            return None
        """ For flying OrbitalCommand, this returns UnitTypeId.OrbitalCommand """
        return UnitTypeId(self.unit_alias)

    @property
    def cost(self) -> Cost:
        return Cost(self.mineral_cost, self.vespene_cost, self.build_time)

    @property
    def cost_zerg_corrected(self) -> Cost:
        """ This returns 25 for extractor and 200 for spawning pool instead of 75 and 250 respectively """
        if self.race == Race.Zerg and "Structure" in self.attributes:
            return Cost(self.mineral_cost - 50, self.vespene_cost, self.build_time)
        return self.cost

    @property
    def morph_cost(self) -> Optional[Cost]:
        """ This returns 150 minerals for OrbitalCommand instead of 550 """
        # Morphing units
        supply_cost = self.food_required
        if supply_cost > 0 and self.id in UNIT_TRAINED_FROM and len(UNIT_TRAINED_FROM[self.id]) == 1:
            producer: UnitTypeId
            for producer in UNIT_TRAINED_FROM[self.id]:
                producer_unit_data = self._game_data.units[producer.value]
                if 0 < producer_unit_data.food_required <= supply_cost:
                    if producer == UnitTypeId.ZERGLING:
                        producer_cost = Cost(25, 0)
                    else:
                        producer_cost = self._game_data.calculate_ability_cost(
                            producer_unit_data.creation_ability.exact_id
                        )
                    return Cost(
                        self.mineral_cost - producer_cost.minerals,
                        self.vespene_cost - producer_cost.vespene,
                        self.build_time,
                    )
        # Fix for BARRACKSREACTOR which has tech alias [REACTOR] which has (0, 0) cost
        if not self.tech_alias_ids or self.tech_alias[0] in {UnitTypeId.TECHLAB.value, UnitTypeId.REACTOR.value}:
            return None
        # Morphing a HIVE would have HATCHERY and LAIR in the tech alias - now subtract HIVE cost from LAIR cost instead of from HATCHERY cost
        tech_alias_cost_minerals = max(
            self._game_data.units[tech_alias].cost.minerals for tech_alias in self.tech_alias
        )
        tech_alias_cost_vespene = max(self._game_data.units[tech_alias].cost.vespene for tech_alias in self.tech_alias)
        return Cost(
            self.mineral_cost - tech_alias_cost_minerals,
            self.vespene_cost - tech_alias_cost_vespene,
            self.build_time,
        )


@dataclass
class UpgradeData:
    upgrade_id: int = 0
    name: str = ""
    mineral_cost: int = 0
    vespene_cost: int = 0
    research_time: float = 0.0
    ability_id: int = 0

    _game_data: GameData = None  # type: ignore

    def __repr__(self):
        return f"UpgradeData({self.name} - research ability: {self.research_ability}, {self.cost})"

    @property
    def research_ability(self) -> Optional[AbilityData]:
        if self.ability_id == 0:
            return None
        if self.ability_id not in self._game_data.abilities:
            return None
        return self._game_data.abilities[self.ability_id]

    @property
    def cost(self) -> Cost:
        return Cost(self.mineral_cost, self.vespene_cost, self.research_time)


@dataclass
class Cost:
    """
    The cost of an action, a structure, a unit or a research upgrade.
    The time is given in frames (22.4 frames per game second).
    """
    minerals: int
    vespene: int
    time: Optional[float] = None

    def __repr__(self) -> str:
        return f"Cost({self.minerals}, {self.vespene})"

    def __eq__(self, other: Cost) -> bool:
        return self.minerals == other.minerals and self.vespene == other.vespene

    def __ne__(self, other: Cost) -> bool:
        return self.minerals != other.minerals or self.vespene != other.vespene

    def __bool__(self) -> bool:
        return self.minerals != 0 or self.vespene != 0

    def __add__(self, other: Cost) -> Cost:
        if not other:
            return self
        if not self:
            return other
        time = (self.time or 0) + (other.time or 0)
        return Cost(self.minerals + other.minerals, self.vespene + other.vespene, time=time)

    def __sub__(self, other: Cost) -> Cost:
        time = (self.time or 0) + (other.time or 0)
        return Cost(self.minerals - other.minerals, self.vespene - other.vespene, time=time)

    def __mul__(self, other: int) -> Cost:
        return Cost(self.minerals * other, self.vespene * other, time=self.time)

    def __rmul__(self, other: int) -> Cost:
        return Cost(self.minerals * other, self.vespene * other, time=self.time)
