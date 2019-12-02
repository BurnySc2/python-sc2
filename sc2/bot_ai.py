from __future__ import annotations
import itertools
import logging
import math
import random
import time
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING
from s2clientprotocol import sc2api_pb2 as sc_pb

from .cache import property_cache_forever, property_cache_once_per_frame, property_cache_once_per_frame_no_copy
from .constants import (
    FakeEffectID,
    abilityid_to_unittypeid,
    geyser_ids,
    mineral_ids,
    TERRAN_TECH_REQUIREMENT,
    PROTOSS_TECH_REQUIREMENT,
    ZERG_TECH_REQUIREMENT,
    ALL_GAS,
    EQUIVALENTS_FOR_TECH_PROGRESS,
    TERRAN_STRUCTURES_REQUIRE_SCV,
)
from .data import ActionResult, Alert, Race, Result, Target, race_gas, race_townhalls, race_worker
from .distances import DistanceCalculation
from .game_data import AbilityData, GameData

from .dicts.unit_trained_from import UNIT_TRAINED_FROM
from .dicts.unit_train_build_abilities import TRAIN_INFO
from .dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from .dicts.unit_research_abilities import RESEARCH_INFO

# Imports for mypy and pycharm autocomplete as well as sphinx autodocumentation
from .game_state import Blip, EffectData, GameState
from .ids.ability_id import AbilityId
from .ids.unit_typeid import UnitTypeId
from .ids.upgrade_id import UpgradeId
from .pixel_map import PixelMap
from .position import Point2, Point3
from .unit import Unit
from .units import Units
from .game_data import Cost
from .unit_command import UnitCommand

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from .game_info import GameInfo, Ramp
    from .client import Client


class BotAI(DistanceCalculation):
    """Base class for bots."""

    EXPANSION_GAP_THRESHOLD = 15

    def _initialize_variables(self):
        """ Called from main.py internally """
        DistanceCalculation.__init__(self)
        # Specific opponent bot ID used in sc2ai ladder games http://sc2ai.net/ and on ai arena https://ai-arena.net
        # The bot ID will stay the same each game so your bot can "adapt" to the opponent
        if not hasattr(self, "opponent_id"):
            # Prevent overwriting the opponent_id which is set here https://github.com/Hannessa/python-sc2-ladderbot/blob/master/__init__.py#L40
            # otherwise set it to None
            self.opponent_id: str = None
        # Select distance calculation method, see distances.py: _distances_override_functions function
        if not hasattr(self, "distance_calculation_method"):
            self.distance_calculation_method: int = 2
        # This value will be set to True by main.py in self._prepare_start if game is played in realtime (if true, the bot will have limited time per step)
        self.realtime: bool = False
        self.all_units: Units = Units([], self)
        self.units: Units = Units([], self)
        self.workers: Units = Units([], self)
        self.townhalls: Units = Units([], self)
        self.structures: Units = Units([], self)
        self.gas_buildings: Units = Units([], self)
        self.enemy_units: Units = Units([], self)
        self.enemy_structures: Units = Units([], self)
        self.resources: Units = Units([], self)
        self.destructables: Units = Units([], self)
        self.watchtowers: Units = Units([], self)
        self.mineral_field: Units = Units([], self)
        self.vespene_geyser: Units = Units([], self)
        self.larva: Units = Units([], self)
        self.techlab_tags: Set[int] = set()
        self.reactor_tags: Set[int] = set()
        self.minerals: int = None
        self.vespene: int = None
        self.supply_army: float = None
        self.supply_workers: float = None  # Doesn't include workers in production
        self.supply_cap: float = None
        self.supply_used: float = None
        self.supply_left: float = None
        self.idle_worker_count: int = None
        self.army_count: int = None
        self.warp_gate_count: int = None
        self.larva_count: int = None
        self.actions: List[UnitCommand] = []
        self.blips: Set[Blip] = set()
        self._units_created: Counter = Counter()
        self._unit_tags_seen_this_game: Set[int] = set()
        self._units_previous_map: Dict[int, Unit] = dict()
        self._structures_previous_map: Dict[int, Unit] = dict()
        self._enemy_units_previous_map: Dict[int, Unit] = dict()
        self._enemy_structures_previous_map: Dict[int, Unit] = dict()
        self._previous_upgrades: Set[UpgradeId] = set()
        self._time_before_step: float = None
        self._time_after_step: float = None
        self._min_step_time: float = math.inf
        self._max_step_time: float = 0
        self._last_step_step_time: float = 0
        self._total_time_in_on_step: float = 0
        self._total_steps_iterations: int = 0
        # Internally used to keep track which units received an action in this frame, so that self.train() function does not give the same larva two orders - cleared every frame
        self.unit_tags_received_action: Set[int] = set()

    @property
    def time(self) -> float:
        """ Returns time in seconds, assumes the game is played on 'faster' """
        return self.state.game_loop / 22.4  # / (1/1.4) * (1/16)

    @property
    def time_formatted(self) -> str:
        """ Returns time as string in min:sec format """
        t = self.time
        return f"{int(t // 60):02}:{int(t % 60):02}"

    @property
    def step_time(self) -> Tuple[float, float, float, float]:
        """ Returns a tuple of step duration in milliseconds.
        First value is the minimum step duration - the shortest the bot ever took
        Second value is the average step duration
        Third value is the maximum step duration - the longest the bot ever took (including on_start())
        Fourth value is the step duration the bot took last iteration
        If called in the first iteration, it returns (inf, 0, 0, 0) """
        avg_step_duration = (
            (self._total_time_in_on_step / self._total_steps_iterations) if self._total_steps_iterations else 0
        )
        return (
            self._min_step_time * 1000,
            avg_step_duration * 1000,
            self._max_step_time * 1000,
            self._last_step_step_time * 1000,
        )

    @property
    def game_info(self) -> GameInfo:
        """ See game_info.py """
        return self._game_info

    @property
    def game_data(self) -> GameData:
        """ See game_data.py """
        return self._game_data

    @property
    def client(self) -> Client:
        """ See client.py """
        return self._client

    def alert(self, alert_code: Alert) -> bool:
        """
        Check if alert is triggered in the current step.
        Possible alerts are listed here https://github.com/Blizzard/s2client-proto/blob/e38efed74c03bec90f74b330ea1adda9215e655f/s2clientprotocol/sc2api.proto#L679-L702

        Example use:

            from sc2.data import Alert
            if self.alert(Alert.AddOnComplete):
                print("Addon Complete")

        Alert codes::

            AlertError
            AddOnComplete
            BuildingComplete
            BuildingUnderAttack
            LarvaHatched
            MergeComplete
            MineralsExhausted
            MorphComplete
            MothershipComplete
            MULEExpired
            NuclearLaunchDetected
            NukeComplete
            NydusWormDetected
            ResearchComplete
            TrainError
            TrainUnitComplete
            TrainWorkerComplete
            TransformationComplete
            UnitUnderAttack
            UpgradeComplete
            VespeneExhausted
            WarpInComplete

        :param alert_code:
        """
        assert isinstance(alert_code, Alert), f"alert_code {alert_code} is no Alert"
        return alert_code.value in self.state.alerts

    @property
    def start_location(self) -> Point2:
        """
        Returns the spawn location of the bot, using the position of the first created townhall.
        This will be None if the bot is run on an arcade or custom map that does not feature townhalls at game start.
        """
        return self._game_info.player_start_location

    @property
    def enemy_start_locations(self) -> List[Point2]:
        """Possible start locations for enemies."""
        return self._game_info.start_locations

    @property
    def main_base_ramp(self) -> Ramp:
        """ Returns the Ramp instance of the closest main-ramp to start location.
        Look in game_info.py for more information about the Ramp class

        Example: See terran ramp wall bot
        """
        if hasattr(self, "cached_main_base_ramp"):
            return self.cached_main_base_ramp
        # The reason for len(ramp.upper) in {2, 5} is:
        # ParaSite map has 5 upper points, and most other maps have 2 upper points at the main ramp.
        # The map Acolyte has 4 upper points at the wrong ramp (which is closest to the start position).
        try:
            self.cached_main_base_ramp = min(
                (ramp for ramp in self.game_info.map_ramps if len(ramp.upper) in {2, 5}),
                key=lambda r: self.start_location.distance_to(r.top_center),
            )
        except ValueError:
            # Hardcoded hotfix for Honorgrounds LE map, as that map has a large main base ramp with inbase natural
            self.cached_main_base_ramp = min(
                (ramp for ramp in self.game_info.map_ramps if len(ramp.upper) in {4, 9}),
                key=lambda r: self.start_location.distance_to(r.top_center),
            )
        return self.cached_main_base_ramp

    @property_cache_forever
    def expansion_locations(self) -> Dict[Point2, Units]:
        """
        Returns dict with the correct expansion position Point2 object as key,
        resources (mineral field and vespene geyser) as value.
        """

        # Idea: create a group for every resource, then merge these groups if
        # any resource in a group is closer than a threshold to any resource of another group

        # Distance we group resources by
        resource_spread_threshold = 8.5
        geysers = self.vespene_geyser
        # Create a group for every resource
        resource_groups = [
            [resource]
            for resource in self.resources
            if resource.name != "MineralField450"  # dont use low mineral count patches
        ]
        # Loop the merging process as long as we change something
        merged_group = True
        while merged_group:
            merged_group = False
            # Check every combination of two groups
            for group_a, group_b in itertools.combinations(resource_groups, 2):
                # Check if any pair of resource of these groups is closer than threshold together
                if any(
                    resource_a.distance_to(resource_b) <= resource_spread_threshold
                    for resource_a, resource_b in itertools.product(group_a, group_b)
                ):
                    # Remove the single groups and add the merged group
                    resource_groups.remove(group_a)
                    resource_groups.remove(group_b)
                    resource_groups.append(group_a + group_b)
                    merged_group = True
                    break
        # Distance offsets we apply to center of each resource group to find expansion position
        offset_range = 7
        offsets = [
            (x, y)
            for x, y in itertools.product(range(-offset_range, offset_range + 1), repeat=2)
            if math.hypot(x, y) <= 8
        ]
        # Dict we want to return
        centers = {}
        # For every resource group:
        for resources in resource_groups:
            # Possible expansion points
            amount = len(resources)
            # Calculate center, round and add 0.5 because expansion location will have (x.5, y.5)
            # coordinates because bases have size 5.
            center_x = int(sum(resource.position.x for resource in resources) / amount) + 0.5
            center_y = int(sum(resource.position.y for resource in resources) / amount) + 0.5
            possible_points = (Point2((offset[0] + center_x, offset[1] + center_y)) for offset in offsets)
            # Filter out points that are too near
            possible_points = (
                point
                for point in possible_points
                # Check if point can be built on
                if self._game_info.placement_grid[point.rounded] == 1
                # Check if all resources have enough space to point
                and all(point.distance_to(resource) > (7 if resource in geysers else 6) for resource in resources)
            )
            # Choose best fitting point
            result = min(possible_points, key=lambda point: sum(point.distance_to(resource) for resource in resources))
            centers[result] = resources
        return centers

    @property
    def units_created(self) -> Counter:
        """ Returns a Counter for all your units and buildings you have created so far.

        This may be used for statistics (at the end of the game) or for strategic decision making.

        CAUTION: This does not properly work at the moment for morphing units and structures. Please use the 'on_unit_type_changed' event to add these morphing unit types manually to 'self._units_created'.
        Issues would arrise in e.g. siege tank morphing to sieged tank, and then morphing back (suddenly the counter counts 2 tanks have been created).

        Examples::

            # Give attack command to enemy base every time 10 marines have been trained
            async def on_unit_created(self, unit: Unit):
                if unit.type_id == UnitTypeId.MARINE:
                    if self.units_created[MARINE] % 10 == 0:
                        for marine in self.units(UnitTypeId.MARINE):
                            self.do(marine.attack(self.enemy_start_locations[0]))
        """
        return self._units_created

    def _correct_zerg_supply(self):
        """ The client incorrectly rounds zerg supply down instead of up (see
            https://github.com/Blizzard/s2client-proto/issues/123), so self.supply_used
            and friends return the wrong value when there are an odd number of zerglings
            and banelings. This function corrects the bad values. """
        # TODO: remove when Blizzard/sc2client-proto#123 gets fixed.
        half_supply_units = {
            UnitTypeId.ZERGLING,
            UnitTypeId.ZERGLINGBURROWED,
            UnitTypeId.BANELING,
            UnitTypeId.BANELINGBURROWED,
            UnitTypeId.BANELINGCOCOON,
        }
        correction = self.units(half_supply_units).amount % 2
        self.supply_used += correction
        self.supply_army += correction
        self.supply_left -= correction

    async def get_available_abilities(
        self, units: Union[List[Unit], Units], ignore_resource_requirements: bool = False
    ) -> List[List[AbilityId]]:
        """ Returns available abilities of one or more units. Right now only checks cooldown, energy cost, and whether the ability has been researched.

        Examples::

            units_abilities = await self.get_available_abilities(self.units)

        or::

            units_abilities = await self.get_available_abilities([self.units.random])

        :param units:
        :param ignore_resource_requirements: """
        return await self._client.query_available_abilities(units, ignore_resource_requirements)

    async def expand_now(
        self, building: UnitTypeId = None, max_distance: float = 10, location: Optional[Point2] = None
    ):
        """ Finds the next possible expansion via 'self.get_next_expansion()'. If the target expansion is blocked (e.g. an enemy unit), it will misplace the expansion.

        :param building:
        :param max_distance:
        :param location: """

        if not building:
            # self.race is never Race.Random
            start_townhall_type = {
                Race.Protoss: UnitTypeId.NEXUS,
                Race.Terran: UnitTypeId.COMMANDCENTER,
                Race.Zerg: UnitTypeId.HATCHERY,
            }
            building = start_townhall_type[self.race]

        assert isinstance(building, UnitTypeId), f"{building} is no UnitTypeId"

        if not location:
            location = await self.get_next_expansion()
        if not location:
            # All expansions are used up or mined out
            logger.warning(f"Trying to expand_now() but bot is out of locations to expand to")
            return
        await self.build(building, near=location, max_distance=max_distance, random_alternative=False, placement_step=1)

    async def get_next_expansion(self) -> Optional[Point2]:
        """Find next expansion location."""

        closest = None
        distance = math.inf
        for el in self.expansion_locations:

            def is_near_to_expansion(t):
                return t.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            if any(map(is_near_to_expansion, self.townhalls)):
                # already taken
                continue

            startp = self._game_info.player_start_location
            d = await self._client.query_pathing(startp, el)
            if d is None:
                continue

            if d < distance:
                distance = d
                closest = el

        return closest

    async def distribute_workers(self, resource_ratio: float = 2):
        """
        Distributes workers across all the bases taken.
        Keyword `resource_ratio` takes a float. If the current minerals to gas
        ratio is bigger than `resource_ratio`, this function prefer filling gas_buildings
        first, if it is lower, it will prefer sending workers to minerals first.

        NOTE: This function is far from optimal, if you really want to have
        refined worker control, you should write your own distribution function.
        For example long distance mining control and moving workers if a base was killed
        are not being handled.

        WARNING: This is quite slow when there are lots of workers or multiple bases.

        :param resource_ratio: """
        if not self.mineral_field or not self.workers or not self.townhalls.ready:
            return
        worker_pool = [worker for worker in self.workers.idle]
        bases = self.townhalls.ready
        gas_buildings = self.gas_buildings.ready

        # list of places that need more workers
        deficit_mining_places = []

        for mining_place in bases | gas_buildings:
            difference = mining_place.surplus_harvesters
            # perfect amount of workers, skip mining place
            if not difference:
                continue
            if mining_place.has_vespene:
                # get all workers that target the gas extraction site
                # or are on their way back from it
                local_workers = self.workers.filter(
                    lambda unit: unit.order_target == mining_place.tag
                    or (unit.is_carrying_vespene and unit.order_target == bases.closest_to(mining_place).tag)
                )
            else:
                # get tags of minerals around expansion
                local_minerals_tags = {
                    mineral.tag for mineral in self.mineral_field if mineral.distance_to(mining_place) <= 8
                }
                # get all target tags a worker can have
                # tags of the minerals he could mine at that base
                # get workers that work at that gather site
                local_workers = self.workers.filter(
                    lambda unit: unit.order_target in local_minerals_tags
                    or (unit.is_carrying_minerals and unit.order_target == mining_place.tag)
                )
            # too many workers
            if difference > 0:
                for worker in local_workers[:difference]:
                    worker_pool.append(worker)
            # too few workers
            # add mining place to deficit bases for every missing worker
            else:
                deficit_mining_places += [mining_place for _ in range(-difference)]

        # prepare all minerals near a base if we have too many workers
        # and need to send them to the closest patch
        if len(worker_pool) > len(deficit_mining_places):
            all_minerals_near_base = [
                mineral
                for mineral in self.mineral_field
                if any(mineral.distance_to(base) <= 8 for base in self.townhalls.ready)
            ]
        # distribute every worker in the pool
        for worker in worker_pool:
            # as long as have workers and mining places
            if deficit_mining_places:
                # choose only mineral fields first if current mineral to gas ratio is less than target ratio
                if self.vespene and self.minerals / self.vespene < resource_ratio:
                    possible_mining_places = [place for place in deficit_mining_places if not place.vespene_contents]
                # else prefer gas
                else:
                    possible_mining_places = [place for place in deficit_mining_places if place.vespene_contents]
                # if preferred type is not available any more, get all other places
                if not possible_mining_places:
                    possible_mining_places = deficit_mining_places
                # find closest mining place
                current_place = min(deficit_mining_places, key=lambda place: place.distance_to(worker))
                # remove it from the list
                deficit_mining_places.remove(current_place)
                # if current place is a gas extraction site, go there
                if current_place.vespene_contents:
                    self.do(worker.gather(current_place))
                # if current place is a gas extraction site,
                # go to the mineral field that is near and has the most minerals left
                else:
                    local_minerals = (
                        mineral for mineral in self.mineral_field if mineral.distance_to(current_place) <= 8
                    )
                    # local_minerals can be empty if townhall is misplaced
                    target_mineral = max(local_minerals, key=lambda mineral: mineral.mineral_contents, default=None)
                    if target_mineral:
                        self.do(worker.gather(target_mineral))
            # more workers to distribute than free mining spots
            # send to closest if worker is doing nothing
            elif worker.is_idle and all_minerals_near_base:
                target_mineral = min(all_minerals_near_base, key=lambda mineral: mineral.distance_to(worker))
                self.do(worker.gather(target_mineral))
            else:
                # there are no deficit mining places and worker is not idle
                # so dont move him
                pass

    @property
    def owned_expansions(self) -> Dict[Point2, Unit]:
        """List of expansions owned by the player."""
        owned = {}
        for el in self.expansion_locations:

            def is_near_to_expansion(t):
                return t.distance_to(el) < self.EXPANSION_GAP_THRESHOLD

            th = next((x for x in self.townhalls if is_near_to_expansion(x)), None)
            if th:
                owned[el] = th
        return owned

    def calculate_supply_cost(self, unit_type: UnitTypeId) -> float:
        """
        This function calculates the required supply to train or morph a unit.
        The total supply of a baneling is 0.5, but a zergling already uses up 0.5 supply, so the morph supply cost is 0.
        The total supply of a ravager is 3, but a roach already uses up 2 supply, so the morph supply cost is 1.
        The required supply to build zerglings is 1 because they pop in pairs, so this function returns 1 because the larva morph command requires 1 free supply.

        Example::

            roach_supply_cost = self.calculate_supply_cost(UnitTypeId.ROACH) # Is 2
            ravager_supply_cost = self.calculate_supply_cost(UnitTypeId.RAVAGER) # Is 1
            baneling_supply_cost = self.calculate_supply_cost(UnitTypeId.BANELING) # Is 0

        :param unit_type: """
        if unit_type in {UnitTypeId.ZERGLING}:
            return 1
        unit_supply_cost = self._game_data.units[unit_type.value]._proto.food_required
        if unit_supply_cost > 0 and unit_type in UNIT_TRAINED_FROM and len(UNIT_TRAINED_FROM[unit_type]) == 1:
            for producer in UNIT_TRAINED_FROM[unit_type]:  # type: UnitTypeId
                producer_unit_data = self.game_data.units[producer.value]
                if producer_unit_data._proto.food_required <= unit_supply_cost:
                    producer_supply_cost = producer_unit_data._proto.food_required
                    unit_supply_cost -= producer_supply_cost
        return unit_supply_cost

    def can_feed(self, unit_type: UnitTypeId) -> bool:
        """ Checks if you have enough free supply to build the unit

        Example::

            cc = self.townhalls.idle.random_or(None)
            # self.townhalls can be empty or there are no idle townhalls
            if cc and self.can_feed(UnitTypeId.SCV):
                self.do(cc.train(UnitTypeId.SCV))

        :param unit_type: """
        required = self.calculate_supply_cost(unit_type)
        # "required <= 0" in case self.supply_left is negative
        return required <= 0 or self.supply_left >= required

    def calculate_unit_value(self, unit_type: UnitTypeId) -> Cost:
        """
        Unlike the function below, this function returns the value of a unit given by the API (e.g. the resources lost value on kill).

        Examples::

            self.calculate_value(UnitTypeId.ORBITALCOMMAND) == Cost(550, 0)
            self.calculate_value(UnitTypeId.RAVAGER) == Cost(100, 100)
            self.calculate_value(UnitTypeId.ARCHON) == Cost(175, 275)

        :param unit_type:
        """
        unit_data = self.game_data.units[unit_type.value]
        return Cost(unit_data._proto.mineral_cost, unit_data._proto.vespene_cost)

    def calculate_cost(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId]) -> Cost:
        """
        Calculate the required build, train or morph cost of a unit. It is recommended to use the UnitTypeId instead of the ability to create the unit.
        The total cost to create a ravager is 100/100, but the actual morph cost from roach to ravager is only 25/75, so this function returns 25/75.

        It is adviced to use the UnitTypeId instead of the AbilityId. Instead of::

            self.calculate_cost(AbilityId.UPGRADETOORBITAL_ORBITALCOMMAND)

        use::

            self.calculate_cost(UnitTypeId.ORBITALCOMMAND)

        More examples::

            from sc2.game_data import Cost

            self.calculate_cost(UnitTypeId.BROODLORD) == Cost(150, 150)
            self.calculate_cost(UnitTypeId.RAVAGER) == Cost(25, 75)
            self.calculate_cost(UnitTypeId.BANELING) == Cost(25, 25)
            self.calculate_cost(UnitTypeId.ORBITALCOMMAND) == Cost(150, 0)
            self.calculate_cost(UnitTypeId.REACTOR) == Cost(50, 50)
            self.calculate_cost(UnitTypeId.TECHLAB) == Cost(50, 25)
            self.calculate_cost(UnitTypeId.QUEEN) == Cost(150, 0)
            self.calculate_cost(UnitTypeId.HATCHERY) == Cost(300, 0)
            self.calculate_cost(UnitTypeId.LAIR) == Cost(150, 100)
            self.calculate_cost(UnitTypeId.HIVE) == Cost(200, 150)

        :param item_id:
        """
        if isinstance(item_id, UnitTypeId):
            # Fix cost for reactor and techlab where the API returns 0 for both
            if item_id in {UnitTypeId.REACTOR, UnitTypeId.TECHLAB, UnitTypeId.ARCHON}:
                if item_id == UnitTypeId.REACTOR:
                    return Cost(50, 50)
                elif item_id == UnitTypeId.TECHLAB:
                    return Cost(50, 25)
                elif item_id == UnitTypeId.ARCHON:
                    return self.calculate_unit_value(UnitTypeId.ARCHON)
            unit_data = self._game_data.units[item_id.value]
            # Cost of structure morphs is automatically correctly calculated by 'calculate_ability_cost'
            cost = self._game_data.calculate_ability_cost(unit_data.creation_ability)
            # Fix non-structure morph cost: check if is morph, then subtract the original cost
            unit_supply_cost = unit_data._proto.food_required
            if unit_supply_cost > 0 and item_id in UNIT_TRAINED_FROM and len(UNIT_TRAINED_FROM[item_id]) == 1:
                for producer in UNIT_TRAINED_FROM[item_id]:  # type: UnitTypeId
                    producer_unit_data = self.game_data.units[producer.value]
                    if 0 < producer_unit_data._proto.food_required <= unit_supply_cost:
                        if producer == UnitTypeId.ZERGLING:
                            producer_cost = Cost(25, 0)
                        else:
                            producer_cost = self.game_data.calculate_ability_cost(producer_unit_data.creation_ability)
                        cost = cost - producer_cost

        elif isinstance(item_id, UpgradeId):
            cost = self._game_data.upgrades[item_id.value].cost
        else:
            # Is already AbilityId
            cost = self._game_data.calculate_ability_cost(item_id)
        return cost

    def can_afford(self, item_id: Union[UnitTypeId, UpgradeId, AbilityId], check_supply_cost: bool = True) -> bool:
        """ Tests if the player has enough resources to build a unit or structure.

        Example::

            cc = self.townhalls.idle.random_or(None)
            # self.townhalls can be empty or there are no idle townhalls
            if cc and self.can_afford(UnitTypeId.SCV):
                self.do(cc.train(UnitTypeId.SCV))

        Example::

            # Current state: we have 150 minerals and one command center and a barracks
            can_afford_morph = self.can_afford(UnitTypeId.ORBITALCOMMAND, check_supply_cost=False)
            # Will be 'True' although the API reports that an orbital is worth 550 minerals, but the morph cost is only 150 minerals

        :param item_id:
        :param check_supply_cost: """
        cost = self.calculate_cost(item_id)
        if cost.minerals > self.minerals or cost.vespene > self.vespene:
            return False
        if check_supply_cost and isinstance(item_id, UnitTypeId):
            supply_cost = self.calculate_supply_cost(item_id)
            if supply_cost and supply_cost > self.supply_left:
                return False
        return True

    async def can_cast(
        self,
        unit: Unit,
        ability_id: AbilityId,
        target: Optional[Union[Unit, Point2, Point3]] = None,
        only_check_energy_and_cooldown: bool = False,
        cached_abilities_of_unit: List[AbilityId] = None,
    ) -> bool:
        """ Tests if a unit has an ability available and enough energy to cast it.

        Example::

            stalkers = self.units(UnitTypeId.STALKER)
            stalkers_that_can_blink = stalkers.filter(lambda unit: unit.type_id == UnitTypeId.STALKER and (await self.can_cast(unit, AbilityId.EFFECT_BLINK_STALKER, only_check_energy_and_cooldown=True)))

        See data_pb2.py (line 161) for the numbers 1-5 to make sense

        :param unit:
        :param ability_id:
        :param target:
        :param only_check_energy_and_cooldown:
        :param cached_abilities_of_unit: """
        assert isinstance(unit, Unit), f"{unit} is no Unit object"
        assert isinstance(ability_id, AbilityId), f"{ability_id} is no AbilityId"
        assert isinstance(target, (type(None), Unit, Point2, Point3))
        # check if unit has enough energy to cast or if ability is on cooldown
        if cached_abilities_of_unit:
            abilities = cached_abilities_of_unit
        else:
            abilities = (await self.get_available_abilities([unit], ignore_resource_requirements=False))[0]

        if ability_id in abilities:
            if only_check_energy_and_cooldown:
                return True
            cast_range = self._game_data.abilities[ability_id.value]._proto.cast_range
            ability_target = self._game_data.abilities[ability_id.value]._proto.target
            # Check if target is in range (or is a self cast like stimpack)
            if (
                ability_target == 1
                or ability_target == Target.PointOrNone.value
                and isinstance(target, (Point2, Point3))
                and unit.distance_to(target) <= unit.radius + target.radius + cast_range
            ):  # cant replace 1 with "Target.None.value" because ".None" doesnt seem to be a valid enum name
                return True
            # Check if able to use ability on a unit
            elif (
                ability_target in {Target.Unit.value, Target.PointOrUnit.value}
                and isinstance(target, Unit)
                and unit.distance_to(target) <= unit.radius + target.radius + cast_range
            ):
                return True
            # Check if able to use ability on a position
            elif (
                ability_target in {Target.Point.value, Target.PointOrUnit.value}
                and isinstance(target, (Point2, Point3))
                and unit.distance_to(target) <= unit.radius + cast_range
            ):
                return True
        return False

    def select_build_worker(self, pos: Union[Unit, Point2, Point3], force: bool = False) -> Optional[Unit]:
        """Select a worker to build a building with.
        
        Example::

            barracks_placement_position = self.main_base_ramp.barracks_correct_placement
            worker = self.select_build_worker(barracks_placement_position)
            # Can return None
            if worker:
                self.do(worker.build(UnitTypeId.BARRACKS, barracks_placement_position))

        :param pos:
        :param force: """
        workers = (
            self.workers.filter(lambda w: (w.is_gathering or w.is_idle) and w.distance_to(pos) < 20) or self.workers
        )
        if workers:
            for worker in workers.sorted_by_distance_to(pos).prefer_idle:
                if (
                    worker not in self.unit_tags_received_action
                    and not worker.orders
                    or len(worker.orders) == 1
                    and worker.orders[0].ability.id in {AbilityId.MOVE, AbilityId.HARVEST_GATHER}
                ):
                    return worker

            return workers.random if force else None

    async def can_place(self, building: Union[AbilityData, AbilityId, UnitTypeId], position: Point2) -> bool:
        """ Tests if a building can be placed in the given location.

        Example::

            barracks_placement_position = self.main_base_ramp.barracks_correct_placement
            worker = self.select_build_worker(barracks_placement_position)
            # Can return None
            if worker and (await self.can_place(UnitTypeId.BARRACKS, barracks_placement_position):
                self.do(worker.build(UnitTypeId.BARRACKS, barracks_placement_position))

        :param building:
        :param position: """
        building_type = type(building)
        assert building_type in {AbilityData, AbilityId, UnitTypeId}
        if building_type == UnitTypeId:
            building = self._game_data.units[building.value].creation_ability
        elif building_type == AbilityId:
            building = self._game_data.abilities[building.value]

        r = await self._client.query_building_placement(building, [position])
        return r[0] == ActionResult.Success

    async def find_placement(
        self,
        building: UnitTypeId,
        near: Union[Unit, Point2, Point3],
        max_distance: int = 20,
        random_alternative: bool = True,
        placement_step: int = 2,
    ) -> Optional[Point2]:
        """ Finds a placement location for building.

        Example::

            if self.townahlls:
                cc = self.townhalls[0]
                depot_position = await self.find_placement(UnitTypeId.SUPPLYDEPOT, near=cc)

        :param building:
        :param near:
        :param max_distance:
        :param random_alternative:
        :param placement_step: """

        assert isinstance(building, (AbilityId, UnitTypeId))
        assert isinstance(near, Point2), f"{near} is no Point2 object"

        if isinstance(building, UnitTypeId):
            building = self._game_data.units[building.value].creation_ability
        else:  # AbilityId
            building = self._game_data.abilities[building.value]

        if await self.can_place(building, near):
            return near

        if max_distance == 0:
            return None

        for distance in range(placement_step, max_distance, placement_step):
            possible_positions = [
                Point2(p).offset(near).to2
                for p in (
                    [(dx, -distance) for dx in range(-distance, distance + 1, placement_step)]
                    + [(dx, distance) for dx in range(-distance, distance + 1, placement_step)]
                    + [(-distance, dy) for dy in range(-distance, distance + 1, placement_step)]
                    + [(distance, dy) for dy in range(-distance, distance + 1, placement_step)]
                )
            ]
            res = await self._client.query_building_placement(building, possible_positions)
            possible = [p for r, p in zip(res, possible_positions) if r == ActionResult.Success]
            if not possible:
                continue

            if random_alternative:
                return random.choice(possible)
            else:
                return min(possible, key=lambda p: p.distance_to_point2(near))
        return None

    # TODO: improve using cache per frame
    def already_pending_upgrade(self, upgrade_type: UpgradeId) -> float:
        """ Check if an upgrade is being researched

        Returns values are::

            0 # not started
            0 < x < 1 # researching
            1 # completed

        Example::

            stim_completion_percentage = self.already_pending_upgrade(UpgradeId.STIMPACK)

        :param upgrade_type:
        """
        assert isinstance(upgrade_type, UpgradeId), f"{upgrade_type} is no UpgradeId"
        if upgrade_type in self.state.upgrades:
            return 1
        creationAbilityID = self._game_data.upgrades[upgrade_type.value].research_ability.exact_id
        for structure in self.structures.filter(lambda unit: unit.is_ready):
            for order in structure.orders:
                if order.ability.exact_id == creationAbilityID:
                    return order.progress
        return 0

    @property_cache_once_per_frame_no_copy
    def _abilities_all_units(self) -> Tuple[Counter, Dict[UnitTypeId, float]]:
        """ Cache for the already_pending function, includes protoss units warping in,
        all units in production and all structures, and all morphs """
        abilities_amount = Counter()
        max_build_progress: Dict[UnitTypeId, float] = {}
        for unit in self.units + self.structures:  # type: Unit
            for order in unit.orders:
                abilities_amount[order.ability] += 1
            if not unit.is_ready:
                if self.race != Race.Terran or not unit.is_structure:
                    # If an SCV is constructing a building, already_pending would count this structure twice
                    # (once from the SCV order, and once from "not structure.is_ready")
                    creation_ability: AbilityData = self._game_data.units[unit.type_id.value].creation_ability
                    abilities_amount[creation_ability] += 1
                    max_build_progress[creation_ability] = max(
                        max_build_progress.get(creation_ability, 0), unit.build_progress
                    )

        return abilities_amount, max_build_progress

    def structure_type_build_progress(self, structure_type: Union[UnitTypeId, int]) -> float:
        """
        Returns the build progress of a structure type.

        Return range: 0 <= x <= 1 where
            0: no such structure exists
            0 < x < 1: at least one structure is under construction, returns the progress of the one with the highest progress
            1: we have at least one such structure complete

        Example::

            # Assuming you have one barracks building at 0.5 build progress:
            progress = self.structure_type_build_progress(UnitTypeId.BARRACKS)
            print(progress)
            # This prints out 0.5

            # If you want to save up money for mutalisks, you can now save up once the spire is nearly completed:
            spire_almost_completed: bool = self.structure_type_build_progress(UnitTypeId.SPIRE) > 0.75

            # Assume you have 2 command centers in production, one has 0.5 build_progress and the other 0.2, the following returns 0.5
            highest_progress_of_command_center: float = self.structure_type_build_progress(UnitTypeId.COMMANDCENTER)

        :param structure_type:
        """
        assert isinstance(
            structure_type, (int, UnitTypeId)
        ), f"Needs to be int or UnitTypeId, but was: {type(structure_type)}"
        if isinstance(structure_type, int):
            structure_type_value = structure_type
        else:
            structure_type_value = structure_type.value
        assert structure_type_value, f"structure_type can not be 0 or NOTAUNIT, but was: {structure_type_value}"
        requirement_structure_ready: bool = next((structure for structure in self.structures if structure._proto.unit_type == structure_type_value and structure.is_ready), False)
        if requirement_structure_ready:
            return 1
        ability = self._game_data.units[structure_type_value].creation_ability
        return self._abilities_all_units[1].get(ability, 0)

    def tech_requirement_progress(self, structure_type: UnitTypeId) -> float:
        """ Returns the tech requirement progress for a specific building

        Example::

            # Current state: supply depot is at 50% completion
            tech_requirement = self.tech_requirement_progress(UnitTypeId.BARRACKS)
            print(tech_requirement) # Prints 0.5 because supply depot is half way done

        Example::

            # Current state: your bot has one hive, no lair
            tech_requirement = self.tech_requirement_progress(UnitTypeId.HYDRALISKDEN)
            print(tech_requirement) # Prints 1 because a hive exists even though only a lair is required

        Example::

            # Current state: One factory is flying and one is half way done
            tech_requirement = self.tech_requirement_progress(UnitTypeId.STARPORT)
            print(tech_requirement) # Prints 1 because even though the type id of the flying factory is different, it still has build progress of 1 and thus tech requirement is completed

        :param structure_type: """
        race_dict = {
            Race.Protoss: PROTOSS_TECH_REQUIREMENT,
            Race.Terran: TERRAN_TECH_REQUIREMENT,
            Race.Zerg: ZERG_TECH_REQUIREMENT,
        }
        unit_info_id_value = race_dict[self.race][structure_type].value
        # The following commented out line is unreliable for ghost / thor as they return 0 which is incorrect
        # unit_info_id_value = self._game_data.units[structure_type.value]._proto.tech_requirement
        if not unit_info_id_value:  # Equivalent to "if unit_info_id_value == 0:"
            return 1
        progresses: List[int] = [self.structure_type_build_progress(unit_info_id_value)]
        for equiv_structure in EQUIVALENTS_FOR_TECH_PROGRESS.get(structure_type, []):
            progresses.append(self.structure_type_build_progress(equiv_structure))
        return max(progresses)

    def already_pending(self, unit_type: Union[UpgradeId, UnitTypeId]) -> float:
        """
        Returns a number of buildings or units already in progress, or if a
        worker is en route to build it. This also includes queued orders for
        workers and build queues of buildings.

        Example::

            amount_of_scv_in_production: int = self.already_pending(UnitTypeId.SCV)
            amount_of_CCs_in_queue_and_production: int = self.already_pending(UnitTypeId.COMMANDCENTER)
            amount_of_lairs_morphing: int = self.already_pending(UnitTypeId.LAIR)


        :param unit_type:
        """
        if isinstance(unit_type, UpgradeId):
            return self.already_pending_upgrade(unit_type)
        ability = self._game_data.units[unit_type.value].creation_ability
        return self._abilities_all_units[0][ability]

    @property_cache_once_per_frame_no_copy
    def _worker_orders(self) -> Counter:
        """ This function is used internally, do not use! It is to store all worker abilities. """
        abilities_amount = Counter()
        structures_in_production: Set[Union[Point2, int]] = set()
        for structure in self.structures:
            if structure.type_id in TERRAN_STRUCTURES_REQUIRE_SCV:
                structures_in_production.add(structure.position)
                structures_in_production.add(structure.tag)
        for worker in self.workers:
            for order in worker.orders:
                # Skip if the SCV is constructing (not isinstance(order.target, int))
                # or resuming construction (isinstance(order.target, int))
                is_int = isinstance(order.target, int)
                if (
                    is_int
                    and order.target in structures_in_production
                    or not is_int
                    and Point2.from_proto(order.target) in structures_in_production
                ):
                    continue
                abilities_amount[order.ability] += 1
        return abilities_amount

    def worker_en_route_to_build(self, unit_type: UnitTypeId) -> float:
        """ This function counts how many workers are on the way to start the construction a building.
        Warning: this function may change its name in the future!
        New function. Please report any bugs!

        :param unit_type: """
        ability = self._game_data.units[unit_type.value].creation_ability
        return self._worker_orders[ability]

    @property_cache_once_per_frame
    def structures_without_construction_SCVs(self) -> Units:
        """ Returns all structures that do not have an SCV constructing it.
        Warning: this function may move to become a Units filter.
        New function. Please report any bugs! """
        worker_targets: Set[Union[int, Point2]] = set()
        for worker in self.workers:
            # Ignore repairing workers
            if not worker.is_constructing_scv:
                continue
            for order in worker.orders:
                # When a construction is resumed, the worker.orders[0].target is the tag of the structure, else it is a Point2
                target = order.target
                if isinstance(target, int):
                    worker_targets.add(target)
                else:
                    worker_targets.add(Point2.from_proto(target))
        return self.structures.filter(
            lambda structure: structure.build_progress < 1
            and structure.position not in worker_targets
            and structure.tag not in worker_targets
            # Redundant check?
            and structure.type_id in TERRAN_STRUCTURES_REQUIRE_SCV
        )

    async def build(
        self,
        building: UnitTypeId,
        near: Union[Unit, Point2, Point3],
        max_distance: int = 20,
        build_worker: Optional[Unit] = None,
        random_alternative: bool = True,
        placement_step: int = 2,
    ) -> bool:
        """ Not recommended as this function checks many positions if it "can place" on them until it found a valid position.
        Also if the given position is not placeable, this function tries to find a nearby position to place the structure. Then uses 'self.do' to give the worker the order to start the construction.

        :param building:
        :param near:
        :param max_distance:
        :param unit:
        :param random_alternative:
        :param placement_step: """

        assert isinstance(near, (Unit, Point2, Point3))
        if isinstance(near, Unit):
            near = near.position
        near = near.to2

        if not self.can_afford(building):
            return False

        p = await self.find_placement(building, near, max_distance, random_alternative, placement_step)
        if p is None:
            return False

        builder = build_worker or self.select_build_worker(p)
        if builder is None:
            return False
        self.do(builder.build(building, p), subtract_cost=True)
        return True

    def train(
        self, unit_type: UnitTypeId, amount: int = 1, closest_to: Point2 = None, train_only_idle_buildings: bool = True
    ) -> int:
        """ Trains a specified number of units. Trains only one if amount is not specified.
        Warning: currently has issues with warp gate warp ins

        New function. Please report any bugs!

        Example Zerg::

            self.train(UnitTypeId.QUEEN, 5)
            # This should queue 5 queens in 5 different townhalls if you have enough townhalls, enough minerals and enough free supply left

        Example Terran::

            # Assuming you have 2 idle barracks with reactors, one barracks without addon and one with techlab
            # It should only queue 4 marines in the 2 idle barracks with reactors
            self.train(UnitTypeId.MARINE, 4)

        Example distance to::

            # If you want to train based on distance to a certain point, you can use "closest_to"
            self.train(UnitTypeId.MARINE, 4, closest_to = self.game_info.map_center)


        :param unit_type:
        :param amount:
        :param closest_to:
        :param train_only_idle_buildings: """
        # Tech requirement not met
        if self.tech_requirement_progress(unit_type) < 1:
            race_dict = {
                Race.Protoss: PROTOSS_TECH_REQUIREMENT,
                Race.Terran: TERRAN_TECH_REQUIREMENT,
                Race.Zerg: ZERG_TECH_REQUIREMENT,
            }
            unit_info_id = race_dict[self.race][unit_type]
            logger.warning(f"Trying to produce unit {unit_type} but tech requirement is not met: {unit_info_id}")
            return 0

        # Not affordable
        if not self.can_afford(unit_type):
            return 0

        trained_amount = 0
        # All train structure types: queen can made from hatchery, lair, hive
        train_structure_type: Set[UnitTypeId] = UNIT_TRAINED_FROM[unit_type]
        train_structures = self.structures if self.race != Race.Zerg else self.structures | self.larva
        requires_techlab = any(
            TRAIN_INFO[structure_type][unit_type].get("requires_techlab", False)
            for structure_type in train_structure_type
        )
        is_protoss = self.race == Race.Protoss
        is_terran = self.race == Race.Terran
        can_have_addons = any(
            u in train_structure_type for u in {UnitTypeId.BARRACKS, UnitTypeId.FACTORY, UnitTypeId.STARPORT}
        )
        # Sort structures closest to a point
        if closest_to is not None:
            train_structures = train_structures.sorted_by_distance_to(closest_to)
        elif can_have_addons:
            # This should sort the structures in ascending order: first structures with reactor, then naked, then with techlab
            train_structures = train_structures.sorted(
                key=lambda structure: -1 * (structure.add_on_tag in self.reactor_tags)
                + 1 * (structure.add_on_tag in self.techlab_tags)
            )

        structure: Unit
        for structure in train_structures:
            # Exit early if we can't afford
            if not self.can_afford(unit_type):
                return trained_amount
            if (
                # If structure hasn't received an action/order this frame
                structure.tag not in self.unit_tags_received_action
                # If structure can train this unit at all
                and structure.type_id in train_structure_type
                # Structure has to be completed to be able to train
                and structure.build_progress == 1
                # If structure is protoss, it needs to be powered to train
                and (not is_protoss or structure.is_powered)
                # Either parameter "train_only_idle_buildings" is False or structure is idle or structure has less than 2 orders and has reactor
                and (
                    not train_only_idle_buildings
                    or len(structure.orders) < 1 + int(structure.add_on_tag in self.reactor_tags)
                )
                # If structure type_id does not accept addons, it cant require a techlab
                # Else we have to check if building has techlab as addon
                and (not requires_techlab or structure.add_on_tag in self.techlab_tags)
            ):
                # Warp in at location
                # TODO: find fast warp in locations either random location or closest to the given parameter "closest_to"
                # TODO: find out which pylons have fast warp in by checking distance to nexus.ready and warp gates
                if structure.type_id == UnitTypeId.WARPGATE:
                    pylons = self.structures(UnitTypeId.PYLON)
                    location = pylons.random.position.random_on_distance(4)
                    successfully_trained = self.do(
                        structure.warp_in(unit_type, location), subtract_cost=True, subtract_supply=True
                    )
                else:
                    # Normal train a unit from larva or inside a structure
                    successfully_trained = self.do(structure.train(unit_type), subtract_cost=True, subtract_supply=True)
                    # Check if structure has reactor: queue same unit again
                    if (
                        # Only terran can have reactors
                        is_terran
                        # Check if we have enough cost or supply for this unit type
                        and self.can_afford(unit_type)
                        # Structure needs to be idle in the current frame
                        and not structure.orders
                        # We are at least 2 away from goal
                        and trained_amount + 1 < amount
                        # Unit type does not require techlab
                        and not requires_techlab
                        # Train structure has reactor
                        and structure.add_on_tag in self.reactor_tags
                    ):
                        trained_amount += 1
                        # With one command queue=False and one queue=True, you can queue 2 marines in a reactored barracks in one frame
                        successfully_trained = self.do(
                            structure.train(unit_type, queue=True), subtract_cost=True, subtract_supply=True
                        )

                if successfully_trained:
                    trained_amount += 1
                    if trained_amount == amount:
                        # Target unit train amount reached
                        return trained_amount
                else:
                    # Some error occured and we couldn't train the unit
                    return trained_amount
        return trained_amount

    def research(self, upgrade_type: UpgradeId) -> bool:
        """
        Researches an upgrade from a structure that can research it, if it is idle and powered (protoss).
        Returns True if the research was started.
        Return False if the requirement was not met, or the bot did not have enough resources to start the upgrade,
        or the building to research the upgrade was missing or not idle.

        New function. Please report any bugs!

        Example::

            # Try to research zergling movement speed if we can afford it
            # and if at least one pool is at build_progress == 1
            # and we are not researching it yet
            if self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0 and self.can_afford(UpgradeId.ZERGLINGMOVEMENTSPEED):
                spawning_pools_ready = self.structures(UnitTypeId.SPAWNINGPOOL).ready
                if spawning_pools_ready:
                    self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)

        :param upgrade_type:
        """
        assert (
            upgrade_type in UPGRADE_RESEARCHED_FROM
        ), f"Could not find upgrade {upgrade_type} in 'research from'-dictionary"

        # Not affordable
        if not self.can_afford(upgrade_type):
            return False

        research_structure_types: UnitTypeId = UPGRADE_RESEARCHED_FROM[upgrade_type]
        required_tech_building: Optional[UnitTypeId] = RESEARCH_INFO[research_structure_types][upgrade_type].get(
            "required_building", None
        )

        requirement_met = (
            required_tech_building is None or self.structure_type_build_progress(required_tech_building) == 1
        )
        # Requirement not met
        if not requirement_met:
            return False

        is_protoss = self.race == Race.Protoss

        equiv_structures = {
            UnitTypeId.GREATERSPIRE: {UnitTypeId.SPIRE, UnitTypeId.GREATERSPIRE},
            UnitTypeId.HIVE: {UnitTypeId.HATCHERY, UnitTypeId.LAIR, UnitTypeId.HIVE},
        }
        # Convert to a set, or equivalent structures are chosen
        # Overlord speed upgrade can be researched from hatchery, lair or hive
        research_structure_types: Set[UnitTypeId] = equiv_structures.get(
            research_structure_types, {research_structure_types}
        )

        structure: Unit
        for structure in self.structures:
            if (
                # If structure hasn't received an action/order this frame
                structure.tag not in self.unit_tags_received_action
                # Structure can research this upgrade
                and structure.type_id in research_structure_types
                # Structure is idle
                and structure.is_idle
                # Structure belongs to protoss and is powered (near pylon)
                and (not is_protoss or structure.is_powered)
            ):
                # Can_afford check was already done earlier in this function
                successful_action: bool = self.do(structure.research(upgrade_type), subtract_cost=True)
                return successful_action
        return False

    def do(
        self,
        action: UnitCommand,
        subtract_cost: bool = False,
        subtract_supply: bool = False,
        can_afford_check: bool = False,
    ) -> bool:
        """ Adds a unit action to the 'self.actions' list which is then executed at the end of the frame.

        Training a unit::

            # Train an SCV from a random idle command center
            cc = self.townhalls.idle.random_or(None)
            # self.townhalls can be empty or there are no idle townhalls
            if cc and self.can_afford(UnitTypeId.SCV):
                self.do(cc.train(UnitTypeId.SCV), subtract_cost=True, subtract_supply=True)

        Building a building::

            # Building a barracks at the main ramp, requires 150 minerals and a depot
            worker = self.workers.random_or(None)
            barracks_placement_position = self.main_base_ramp.barracks_correct_placement
            if worker and self.can_afford(UnitTypeId.BARRACKS):
                self.do(worker.build(UnitTypeId.BARRACKS, barracks_placement_position), subtract_cost=True)

        Moving a unit::

            # Move a random worker to the center of the map
            worker = self.workers.random_or(None)
            # worker can be None if all are dead
            if worker:
                self.do(worker.move(self.game_info.map_center))

        :param action:
        :param subtract_cost:
        :param subtract_supply:
        :param can_afford_check:
        """
        assert isinstance(
            action, UnitCommand
        ), f"Given unit command is not a command, but instead of type {type(action)}"
        if subtract_cost:
            cost: Cost = self._game_data.calculate_ability_cost(action.ability)
            if can_afford_check and not (self.minerals >= cost.minerals and self.vespene >= cost.vespene):
                # Dont do action if can't afford
                return False
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene
        if subtract_supply and action.ability in abilityid_to_unittypeid:
            unit_type = abilityid_to_unittypeid[action.ability]
            required_supply = self.calculate_supply_cost(unit_type)
            # Overlord has -8
            if required_supply > 0:
                self.supply_used += required_supply
                self.supply_left -= required_supply
            if (
                self.race == Race.Zerg
                and unit_type in UNIT_TRAINED_FROM
                and UNIT_TRAINED_FROM[unit_type] == {UnitTypeId.LARVA}
            ):
                self.larva_count -= 1
        self.actions.append(action)
        self.unit_tags_received_action.add(action.unit.tag)
        return True

    # TODO remove again, because you can just use 'self.do()' and execute '_do_actions' and 'self.actions.clear()' afterwards?
    async def synchronous_do(self, action: UnitCommand):
        """
        Not recommended. Use self.do instead to reduce lag.
        This function is only useful for realtime=True in the first frame of the game to instantly produce a worker
        and split workers on the mineral patches.
        """
        assert isinstance(
            action, UnitCommand
        ), f"Given unit command is not a command, but instead of type {type(action)}"
        if not self.can_afford(action.ability):
            logger.warning(f"Cannot afford action {action}")
            return ActionResult.Error
        r = await self._client.actions(action)
        if not r:  # success
            cost = self._game_data.calculate_ability_cost(action.ability)
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene
            self.unit_tags_received_action.add(action.unit.tag)
        else:
            logger.error(f"Error: {r} (action: {action})")
        return r

    async def _do_actions(self, actions: List[UnitCommand], prevent_double: bool = True):
        """ Used internally by main.py automatically, use self.do() instead!

        :param actions:
        :param prevent_double: """
        if not actions:
            return None
        if prevent_double:
            actions = list(filter(self.prevent_double_actions, actions))
        result = await self._client.actions(actions)
        return result

    def prevent_double_actions(self, action) -> bool:
        """
        :param action:
        """
        # Always add actions if queued
        if action.queue:
            return True
        if action.unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = action.unit.orders[0]
            if current_action.ability.id != action.ability:
                # Different action, return True
                return True
            try:
                if current_action.target == action.target.tag:
                    # Same action, remove action if same target unit
                    return False
            except AttributeError:
                pass
            try:
                if action.target.x == current_action.target.x and action.target.y == current_action.target.y:
                    # Same action, remove action if same target position
                    return False
            except AttributeError:
                pass
            return True
        return True

    async def chat_send(self, message: str):
        """ Send a chat message to the SC2 Client.

        Example::

            await self.chat_send("Hello, this is a message from my bot!")

        :param message: """
        assert isinstance(message, str), f"{message} is not a string"
        await self._client.chat_send(message, False)

    def in_map_bounds(self, pos: Union[Point2, tuple]) -> bool:
        """ Tests if a 2 dimensional point is within the map boundaries of the pixelmaps.
        :param pos: """
        return self._game_info.playable_area.x <= pos[0] < self._game_info.playable_area.x + self.game_info.playable_area.width and self._game_info.playable_area.y <= pos[1] < self._game_info.playable_area.y + self.game_info.playable_area.height

    # For the functions below, make sure you are inside the boundries of the map size.
    def get_terrain_height(self, pos: Union[Point2, Point3, Unit]) -> int:
        """ Returns terrain height at a position.
        Caution: terrain height is different from a unit's z-coordinate.

        :param pos: """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.terrain_height[pos]

    def get_terrain_z_height(self, pos: Union[Point2, Point3, Unit]) -> int:
        """ Returns terrain z-height at a position.

        :param pos: """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return -16 + 32 * self._game_info.terrain_height[pos] / 255

    def in_placement_grid(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if you can place something at a position.
        Remember, buildings usually use 2x2, 3x3 or 5x5 of these grid points.
        Caution: some x and y offset might be required, see ramp code in game_info.py

        :param pos: """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.placement_grid[pos] == 1

    def in_pathing_grid(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if a ground unit can pass through a grid point.

        :param pos: """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[pos] == 1

    def is_visible(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if you have vision on a grid point.

        :param pos: """
        # more info: https://github.com/Blizzard/s2client-proto/blob/9906df71d6909511907d8419b33acc1a3bd51ec0/s2clientprotocol/spatial.proto#L19
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self.state.visibility[pos] == 2

    def has_creep(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if there is creep on the grid point.

        :param pos: """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self.state.creep[pos] == 1

    def _prepare_start(self, client, player_id, game_info, game_data, realtime: bool = False):
        """
        Ran until game start to set game and player data.

        :param client:
        :param player_id:
        :param game_info:
        :param game_data:
        :param realtime:
        """
        self._client: Client = client
        self.player_id: int = player_id
        self._game_info: GameInfo = game_info
        self._game_data: GameData = game_data
        self.realtime: bool = realtime

        self.race: Race = Race(self._game_info.player_races[self.player_id])

        if len(self._game_info.player_races) == 2:
            self.enemy_race: Race = Race(self._game_info.player_races[3 - self.player_id])

        self._distances_override_functions(self.distance_calculation_method)

    def _prepare_first_step(self):
        """First step extra preparations. Must not be called before _prepare_step."""
        if self.townhalls:
            self._game_info.player_start_location = self.townhalls.first.position
            # Calculate and cache expansion locations forever inside 'self._cache_expansion_locations', this is done to prevent a bug when this is run and cached later in the game
            _ = self.expansion_locations
        self._game_info.map_ramps, self._game_info.vision_blockers = self._game_info._find_ramps_and_vision_blockers()
        self._time_before_step: float = time.perf_counter()

    def _prepare_step(self, state, proto_game_info):
        """
        :param state:
        :param proto_game_info:
        """
        # Set attributes from new state before on_step."""
        self.state: GameState = state  # See game_state.py
        # update pathing grid
        self._game_info.pathing_grid: PixelMap = PixelMap(
            proto_game_info.game_info.start_raw.pathing_grid, in_bits=True, mirrored=False
        )
        # Required for events, needs to be before self.units are initialized so the old units are stored
        self._units_previous_map: Dict = {unit.tag: unit for unit in self.units}
        self._structures_previous_map: Dict = {structure.tag: structure for structure in self.structures}
        self._enemy_units_previous_map: Dict = {unit.tag: unit for unit in self.enemy_units}
        self._enemy_structures_previous_map: Dict = {structure.tag: structure for structure in self.enemy_structures}

        self._prepare_units()
        self.minerals: int = state.common.minerals
        self.vespene: int = state.common.vespene
        self.supply_army: int = state.common.food_army
        self.supply_workers: int = state.common.food_workers  # Doesn't include workers in production
        self.supply_cap: int = state.common.food_cap
        self.supply_used: int = state.common.food_used
        self.supply_left: int = self.supply_cap - self.supply_used

        if self.race == Race.Zerg:
            # Larva count does not seem to be reliable at all
            self.larva_count: int = state.common.larva_count
            # Workaround Zerg supply rounding bug
            self._correct_zerg_supply()
        elif self.race == Race.Protoss:
            self.warp_gate_count: int = state.common.warp_gate_count

        self.idle_worker_count: int = state.common.idle_worker_count
        self.army_count: int = state.common.army_count
        self._time_before_step: float = time.perf_counter()

    def _prepare_units(self):
        # Set of enemy units detected by own sensor tower, as blips have less unit information than normal visible units
        self.blips: Set[Blip] = set()
        self.units: Units = Units([], self)
        self.structures: Units = Units([], self)
        self.enemy_units: Units = Units([], self)
        self.enemy_structures: Units = Units([], self)
        self.mineral_field: Units = Units([], self)
        self.vespene_geyser: Units = Units([], self)
        self.resources: Units = Units([], self)
        self.destructables: Units = Units([], self)
        self.watchtowers: Units = Units([], self)
        self.all_units: Units = Units([], self)
        self.workers: Units = Units([], self)
        self.townhalls: Units = Units([], self)
        self.gas_buildings: Units = Units([], self)
        self.larva: Units = Units([], self)
        self.techlab_tags: Set[int] = set()
        self.reactor_tags: Set[int] = set()

        for unit in self.state.observation_raw.units:
            if unit.is_blip:
                self.blips.add(Blip(unit))
            else:
                unit_type: int = unit.unit_type
                # Convert these units to effects: reaper grenade, parasitic bomb dummy, forcefield
                if unit_type in FakeEffectID:
                    self.state.effects.add(EffectData(unit, fake=True))
                    continue
                unit_obj = Unit(unit, self)
                self.all_units.append(unit_obj)
                alliance = unit.alliance
                # Alliance.Neutral.value = 3
                if alliance == 3:
                    # XELNAGATOWER = 149
                    if unit_type == 149:
                        self.watchtowers.append(unit_obj)
                    # mineral field enums
                    elif unit_type in mineral_ids:
                        self.mineral_field.append(unit_obj)
                        self.resources.append(unit_obj)
                    # geyser enums
                    elif unit_type in geyser_ids:
                        self.vespene_geyser.append(unit_obj)
                        self.resources.append(unit_obj)
                    # all destructable rocks
                    else:
                        self.destructables.append(unit_obj)
                # Alliance.Self.value = 1
                elif alliance == 1:
                    unit_id = unit_obj.type_id
                    if unit_obj.is_structure:
                        self.structures.append(unit_obj)
                        if unit_id in race_townhalls[self.race]:
                            self.townhalls.append(unit_obj)
                        elif unit_id in ALL_GAS or unit_obj.vespene_contents:
                            # TODO: remove "or unit_obj.vespene_contents" when a new linux client newer than version 4.10.0 is released
                            self.gas_buildings.append(unit_obj)
                        elif unit_id in {
                            UnitTypeId.TECHLAB,
                            UnitTypeId.BARRACKSTECHLAB,
                            UnitTypeId.FACTORYTECHLAB,
                            UnitTypeId.STARPORTTECHLAB,
                        }:
                            self.techlab_tags.add(unit_obj.tag)
                        elif unit_id in {
                            UnitTypeId.REACTOR,
                            UnitTypeId.BARRACKSREACTOR,
                            UnitTypeId.FACTORYREACTOR,
                            UnitTypeId.STARPORTREACTOR,
                        }:
                            self.reactor_tags.add(unit_obj.tag)
                    else:
                        self.units.append(unit_obj)
                        if unit_id == race_worker[self.race]:
                            self.workers.append(unit_obj)
                        elif unit_id == UnitTypeId.LARVA:
                            self.larva.append(unit_obj)
                # Alliance.Enemy.value = 4
                elif alliance == 4:
                    if unit_obj.is_structure:
                        self.enemy_structures.append(unit_obj)
                    else:
                        self.enemy_units.append(unit_obj)

        # Force distance calculation and caching on all units using scipy pdist or cdist
        if self.distance_calculation_method == 1:
            _ = self._unit_index_dict
            _ = self._pdist
        elif self.distance_calculation_method == 2:
            _ = self._unit_index_dict
            _ = self._cdist

    async def _after_step(self) -> int:
        """ Executed by main.py after each on_step function. """
        # Keep track of the bot on_step duration
        self._time_after_step: float = time.perf_counter()
        step_duration = self._time_after_step - self._time_before_step
        self._min_step_time = min(step_duration, self._min_step_time)
        self._max_step_time = max(step_duration, self._max_step_time)
        self._last_step_step_time = step_duration
        self._total_time_in_on_step += step_duration
        self._total_steps_iterations += 1
        # Commit and clear bot actions
        await self._do_actions(self.actions)
        self.actions.clear()
        # Clear set of unit tags that were given an order this frame by self.do()
        self.unit_tags_received_action.clear()
        # Commit debug queries
        await self._client._send_debug()

        return self.state.game_loop

    async def _advance_steps(self, steps: int):
        """ Advances the game loop by amount of 'steps'. This function is meant to be used as a debugging and testing tool only.
        If you are using this, please be aware of the consequences, e.g. 'self.units' will be filled with completely new data. """
        old_game_loop = self.state.game_loop
        await self._after_step()
        # Advance simulation by exactly "steps" frames
        await self.client.step(steps)
        state = await self.client.observation()
        gs = GameState(state.observation)
        proto_game_info = await self.client._execute(game_info=sc_pb.RequestGameInfo())
        self._prepare_step(gs, proto_game_info)
        # print(f"Advanced from game loop ({old_game_loop}) to ({self.state.game_loop})")
        # await self.issue_events()
        # await self.on_step(-1)

    async def issue_events(self):
        """ This function will be automatically run from main.py and triggers the following functions:
        - on_unit_created
        - on_unit_destroyed
        - on_building_construction_started
        - on_building_construction_complete
        - on_upgrade_complete
        """
        await self._issue_unit_dead_events()
        await self._issue_unit_added_events()
        await self._issue_building_events()
        await self._issue_upgrade_events()
        await self._issue_vision_events()

    async def _issue_unit_added_events(self):
        for unit in self.units:
            if unit.tag not in self._units_previous_map and unit.tag not in self._unit_tags_seen_this_game:
                self._unit_tags_seen_this_game.add(unit.tag)
                self._units_created[unit.type_id] += 1
                await self.on_unit_created(unit)
            elif unit.tag in self._units_previous_map:
                previous_frame_unit: Unit = self._units_previous_map[unit.tag]
                # Check if a unit took damage this frame and then trigger event
                if unit.health < previous_frame_unit.health or unit.shield < previous_frame_unit.shield:
                    damage_amount = previous_frame_unit.health - unit.health + previous_frame_unit.shield - unit.shield
                    await self.on_unit_took_damage(unit, damage_amount)
                # Check if a unit type has changed
                if previous_frame_unit.type_id != unit.type_id:
                    await self.on_unit_type_changed(unit, previous_frame_unit.type_id)

    async def _issue_upgrade_events(self):
        difference = self.state.upgrades - self._previous_upgrades
        for upgrade_completed in difference:
            await self.on_upgrade_complete(upgrade_completed)
        self._previous_upgrades = self.state.upgrades

    async def _issue_building_events(self):
        for structure in self.structures:
            if structure.tag not in self._structures_previous_map:
                if structure.build_progress < 1:
                    await self.on_building_construction_started(structure)
                else:
                    # Include starting townhall
                    self._units_created[structure.type_id] += 1
                    await self.on_building_construction_complete(structure)
            elif structure.tag in self._structures_previous_map:
                # Check if a structure took damage this frame and then trigger event
                previous_frame_structure: Unit = self._structures_previous_map[structure.tag]
                if (
                    structure.health < previous_frame_structure.health
                    or structure.shield < previous_frame_structure.shield
                ):
                    damage_amount = (
                        previous_frame_structure.health
                        - structure.health
                        + previous_frame_structure.shield
                        - structure.shield
                    )
                    await self.on_unit_took_damage(structure, damage_amount)
                # Check if a structure changed its type
                if previous_frame_structure.type_id != structure.type_id:
                    await self.on_unit_type_changed(structure, previous_frame_structure.type_id)
                # Check if structure completed
                if structure.build_progress == 1 and previous_frame_structure.build_progress < 1:
                    self._units_created[structure.type_id] += 1
                    await self.on_building_construction_complete(structure)

    async def _issue_vision_events(self):
        # Call events for enemy unit entered vision
        for enemy_unit in self.enemy_units:
            if enemy_unit.tag not in self._enemy_units_previous_map:
                await self.on_enemy_unit_entered_vision(enemy_unit)
        for enemy_structure in self.enemy_structures:
            if enemy_structure.tag not in self._enemy_structures_previous_map:
                await self.on_enemy_unit_entered_vision(enemy_structure)

        # Call events for enemy unit left vision
        if self.enemy_units:
            visible_enemy_units = self.enemy_units.tags
            for enemy_unit_tag in self._enemy_units_previous_map.keys():
                if enemy_unit_tag not in visible_enemy_units:
                    await self.on_enemy_unit_left_vision(enemy_unit_tag)
        if self.enemy_structures:
            visible_enemy_structures = self.enemy_structures.tags
            for enemy_structure_tag in self._enemy_units_previous_map.keys():
                if enemy_structure_tag not in visible_enemy_structures:
                    await self.on_enemy_unit_left_vision(enemy_structure_tag)

    async def _issue_unit_dead_events(self):
        for unit_tag in self.state.dead_units:
            await self.on_unit_destroyed(unit_tag)

    async def on_unit_destroyed(self, unit_tag: int):
        """
        Override this in your bot class.
        Note that this function uses unit tags and not the unit objects
        because the unit does not exist any more.

        :param unit_tag:
        """

    async def on_unit_created(self, unit: Unit):
        """ Override this in your bot class. This function is called when a unit is created.

        :param unit: """

    async def on_unit_type_changed(self, unit: Unit, previous_type: UnitTypeId):
        """ Override this in your bot class. This function is called when a unit type has changed. To get the current UnitTypeId of the unit, use 'unit.type_id'

        This may happen when a larva morphed to an egg, siege tank sieged, a zerg unit burrowed, a hatchery morphed to lair, a corruptor morphed to broodlordcocoon, etc..

        Examples::

            print(f"My unit changed type: {unit} from {previous_type} to {unit.type_id}")

        :param unit:
        :param previous_type:
        """

    async def on_building_construction_started(self, unit: Unit):
        """
        Override this in your bot class.
        This function is called when a building construction has started.

        :param unit:
        """

    async def on_building_construction_complete(self, unit: Unit):
        """
        Override this in your bot class. This function is called when a building
        construction is completed.

        :param unit:
        """

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        """
        Override this in your bot class. This function is called with the upgrade id of an upgrade that was not finished last step and is now.

        :param upgrade:
        """

    async def on_unit_took_damage(self, unit: Unit, amount_damage_taken: float):
        """
        Override this in your bot class. This function is called when your own unit (unit or structure) took damage. It will not be called if the unit died this frame.

        This may be called frequently for terran structures that are burning down, or zerg buildings that are off creep, or terran bio units that just used stimpack ability.
        TODO: If there is a demand for it, then I can add a similar event for when enemy units took damage

        Examples::

            print(f"My unit took damage: {unit} took {amount_damage_taken} damage")

        :param unit:
        """

    async def on_enemy_unit_entered_vision(self, unit: Unit):
        """
        Override this in your bot class. This function is called when an enemy unit (unit or structure) entered vision (which was not visible last frame).

        :param unit:
        """

    async def on_enemy_unit_left_vision(self, unit_tag: int):
        """
        Override this in your bot class. This function is called when an enemy unit (unit or structure) left vision (which was visible last frame).
        Same as the self.on_unit_destroyed event, this function is called with the unit's tag because the unit is no longer visible anymore. If you want to store a snapshot of the unit, use self._enemy_units_previous_map[unit_tag] for units or self._enemy_structures_previous_map[unit_tag] for structures.

        Examples::

            last_known_unit = self._enemy_units_previous_map.get(unit_tag, None) or self._enemy_structures_previous_map[unit_tag]
            print(f"Enemy unit left vision, last known location: {last_known_unit.position}")

        :param unit_tag:
        """

    async def on_before_start(self):
        """
        Override this in your bot class. This function is called before "on_start"
        and before "prepare_first_step" that calculates expansion locations.
        Not all data is available yet.
        This function is useful in realtime=True mode to split your workers or start producing the first worker.
        """

    async def on_start(self):
        """
        Override this in your bot class.
        At this point, game_data, game_info and the first iteration of game_state (self.state) are available.
        """

    async def on_step(self, iteration: int):
        """
        You need to implement this function!
        Override this in your bot class.
        This function is called on every game step (looped in realtime mode).

        :param iteration:
        """
        raise NotImplementedError

    async def on_end(self, game_result: Result):
        """ Override this in your bot class. This function is called at the end of a game. Unsure if this function will be called on the laddermanager client as the bot process may forcefully be terminated.

        :param game_result: """
