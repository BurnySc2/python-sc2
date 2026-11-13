from __future__ import annotations

import itertools
import math
import time
import warnings
from abc import ABC
from collections import Counter
from collections.abc import Generator, Iterable
from contextlib import suppress
from typing import TYPE_CHECKING, Any, cast, final

import numpy as np
from loguru import logger

from s2clientprotocol import sc2api_pb2 as sc_pb
from sc2.cache import property_cache_once_per_frame
from sc2.constants import (
    ALL_GAS,
    CREATION_ABILITY_FIX,
    IS_PLACEHOLDER,
    TERRAN_STRUCTURES_REQUIRE_SCV,
    FakeEffectID,
    abilityid_to_unittypeid,
    geyser_ids,
    mineral_ids,
)
from sc2.data import ActionResult, Race, race_townhalls
from sc2.game_data import Cost, GameData
from sc2.game_state import Blip, EffectData, GameState
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.pixel_map import PixelMap
from sc2.position import Point2, _PointLike
from sc2.unit import Unit
from sc2.unit_command import UnitCommand
from sc2.units import Units

with warnings.catch_warnings():
    warnings.simplefilter("ignore")
    from scipy.spatial.distance import cdist, pdist

if TYPE_CHECKING:
    from sc2.client import Client
    from sc2.game_info import GameInfo
    from sc2.bot_ai import BotAI


class BotAIInternal(ABC):
    """Base class for bots."""

    def __init__(self: BotAI) -> None:
        self._initialize_variables()

    @final
    def _initialize_variables(self: BotAI) -> None:
        """Called from main.py internally"""
        self.cache: dict[str, Any] = {}
        # Specific opponent bot ID used in sc2ai ladder games http://sc2ai.net/ and on ai arena https://aiarena.net
        # The bot ID will stay the same each game so your bot can "adapt" to the opponent
        if not hasattr(self, "opponent_id"):
            # Prevent overwriting the opponent_id which is set here https://github.com/Hannessa/python-sc2-ladderbot/blob/master/__init__.py#L40
            # otherwise set it to None
            self.opponent_id: str | None = None
        # Select distance calculation method, see _distances_override_functions function
        if not hasattr(self, "distance_calculation_method"):
            self.distance_calculation_method: int = 2
        # Select if the Unit.command should return UnitCommand objects. Set this to True if your bot uses 'unit(ability, target)'
        if not hasattr(self, "unit_command_uses_self_do"):
            self.unit_command_uses_self_do: bool = False
        # This value will be set to True by main.py in self._prepare_start if game is played in realtime (if true, the bot will have limited time per step)
        self.realtime: bool = False
        self.base_build: int = -1
        self.all_units: Units = Units([], self)
        self.units: Units = Units([], self)
        self.workers: Units = Units([], self)
        self.larva: Units = Units([], self)
        self.structures: Units = Units([], self)
        self.townhalls: Units = Units([], self)
        self.gas_buildings: Units = Units([], self)
        self.all_own_units: Units = Units([], self)
        self.enemy_units: Units = Units([], self)
        self.enemy_structures: Units = Units([], self)
        self.all_enemy_units: Units = Units([], self)
        self.resources: Units = Units([], self)
        self.destructables: Units = Units([], self)
        self.watchtowers: Units = Units([], self)
        self.mineral_field: Units = Units([], self)
        self.vespene_geyser: Units = Units([], self)
        self.placeholders: Units = Units([], self)
        self.techlab_tags: set[int] = set()
        self.reactor_tags: set[int] = set()
        self.minerals: int = 50
        self.vespene: int = 0
        self.supply_army: float = 0
        self.supply_workers: float = 12  # Doesn't include workers in production
        self.supply_cap: float = 15
        self.supply_used: float = 12
        self.supply_left: float = 3
        self.idle_worker_count: int = 0
        self.army_count: int = 0
        self.warp_gate_count: int = 0
        self.actions: list[UnitCommand] = []
        self.blips: set[Blip] = set()

        # Will be set on AbstractPlayer init
        self.race: Race = None  # pyrefly: ignore
        self.enemy_race: Race | None = None
        self._generated_frame = -100
        self._units_created: Counter = Counter()
        self._unit_tags_seen_this_game: set[int] = set()
        self._units_previous_map: dict[int, Unit] = {}
        self._structures_previous_map: dict[int, Unit] = {}
        self._enemy_units_previous_map: dict[int, Unit] = {}
        self._enemy_structures_previous_map: dict[int, Unit] = {}
        self._all_units_previous_map: dict[int, Unit] = {}
        self._previous_upgrades: set[UpgradeId] = set()
        self._expansion_positions_list: list[Point2] = []
        self._resource_location_to_expansion_position_dict: dict[Point2, set[Point2]] = {}
        self._time_before_step: float = 0
        self._time_after_step: float = 0
        self._min_step_time: float = math.inf
        self._max_step_time: float = 0
        self._last_step_step_time: float = 0
        self._total_time_in_on_step: float = 0
        self._total_steps_iterations: int = 0
        # Internally used to keep track which units received an action in this frame, so that self.train() function does not give the same larva two orders - cleared every frame
        self.unit_tags_received_action: set[int] = set()

    @final
    @property
    def _game_info(self) -> GameInfo:
        """See game_info.py"""
        warnings.warn(
            "Using self._game_info is deprecated and may be removed soon. Please use self.game_info directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.game_info

    @final
    @property
    def _game_data(self) -> GameData:
        """See game_data.py"""
        warnings.warn(
            "Using self._game_data is deprecated and may be removed soon. Please use self.game_data directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.game_data

    @final
    @property
    def _client(self) -> Client:
        """See client.py"""
        warnings.warn(
            "Using self._client is deprecated and may be removed soon. Please use self.client directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.client

    @final
    @property_cache_once_per_frame
    def expansion_locations(self: BotAI) -> dict[Point2, Units]:
        """Same as the function above."""
        assert self._expansion_positions_list, (
            "self._find_expansion_locations() has not been run yet, so accessing the list of expansion locations is pointless."
        )
        warnings.warn(
            "You are using 'self.expansion_locations', please use 'self.expansion_locations_list' (fast) or 'self.expansion_locations_dict' (slow) instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return self.expansion_locations_dict

    def _cluster_center(self, group: list[Unit]) -> Point2:
        """
        Calculates the geometric center (centroid) of a given group of units.

        Parameters:
        group: A list of Unit objects representing the group of units for
                            which the center is to be calculated.

        Raises:
        ValueError: If the provided group is empty.

        Returns:
        Point2: The calculated centroid of the group as a Point2 object.
        """
        if not group:
            raise ValueError("Cannot calculate center of empty group")

        total_x: float = 0
        total_y: float = 0
        for unit in group:
            total_x += unit.position.x
            total_y += unit.position.y

        count = len(group)
        return Point2((total_x / count, total_y / count))

    def _find_expansion_location(
        self, resources: Units | list[Unit], amount: int, offsets: list[tuple[float, float]]
    ) -> Point2:
        """
        Finds the most suitable expansion location for resources.

        Parameters:
            resources: The list of resource entities or units near which the
                expansion location needs to be found.
            amount: The total number of resource entities or units to consider.
            offsets (list[tuple[float, float]): A list of coordinate pairs denoting position
                offsets to consider around the center of resources.

        Returns:
            The calculated optimal expansion Point2 if a suitable position is found;
                otherwise, None.
        """
        # Normal single expansion logic for regular bases
        # Calculate center, round and add 0.5 because expansion location will have (x.5, y.5)
        # coordinates because bases have size 5.
        center_x = int(sum(resource.position.x for resource in resources) / amount) + 0.5
        center_y = int(sum(resource.position.y for resource in resources) / amount) + 0.5
        possible_points = (Point2((offset[0] + center_x, offset[1] + center_y)) for offset in offsets)
        # Filter out points that are too near
        possible_points = [
            point
            for point in possible_points
            # Check if point can be built on
            if self.game_info.placement_grid[point.rounded] == 1
            # Check if all resources have enough space to point
            and all(
                point.distance_to(resource) >= (7 if resource._proto.unit_type in geyser_ids else 6)
                for resource in resources
            )
        ]
        # Choose best fitting point
        result: Point2 = min(
            possible_points, key=lambda point: sum(point.distance_to(resource_) for resource_ in resources)
        )
        return result

    def _has_opposite_side_geyser_layout(self, minerals: list[Unit], gas_geysers: list[Unit]) -> bool:
        """
        Determines whether the gas geysers have an opposite-side mineral line layout.

        The method evaluates if two gas geysers are located on opposite sides of a
        mineral line.
        If this returns True we consider this location has 2 valid expansion locations
        either side of the mineral line.

        Parameters:
            minerals:
                A list of mineral fields at this location.
            gas_geysers : list[Unit]
                A list of gas geysers at this location.

        Returns:
            bool
                True if the geysers fulfill the opposite-side layout condition with
                respect to the mineral line, otherwise False.
        """
        # Need exactly 2 geysers and enough minerals for a line
        if len(gas_geysers) != 2 or len(minerals) < 6:
            return False

        # Find the two minerals that are furthest apart
        max_distance: float = 0.0
        mineral_1: Unit = minerals[0]
        mineral_2: Unit = minerals[1]

        for i, m1 in enumerate(minerals):
            for m2 in minerals[i + 1 :]:
                distance = m1.distance_to(m2)
                if distance > max_distance:
                    max_distance = distance
                    mineral_1 = m1
                    mineral_2 = m2

        # ensure line is long enough
        if max_distance < 4:
            return False

        # Create line from the two furthest minerals
        x1, y1 = mineral_1.position.x, mineral_1.position.y
        x2, y2 = mineral_2.position.x, mineral_2.position.y

        geyser_1, geyser_2 = gas_geysers

        # Check if the mineral line is more vertical than horizontal
        if abs(x2 - x1) < 0.1:
            # Vertical line: use x-coordinate to determine sides
            line_x = (x1 + x2) / 2

            side_1 = geyser_1.position.x - line_x
            side_2 = geyser_2.position.x - line_x

            # Must be on opposite sides and far enough from the line
            return side_1 * side_2 < 0 and abs(side_1) > 3 and abs(side_2) > 3

        # Calculate line equation: y = mx + b
        slope = (y2 - y1) / (x2 - x1)
        intercept = y1 - slope * x1

        # Function to determine which side of the line a point is on
        def side_of_line(point: Point2) -> float:
            return point.y - slope * point.x - intercept

        side_1 = side_of_line(geyser_1.position)
        side_2 = side_of_line(geyser_2.position)

        # Check if geysers are on opposite sides
        opposite_sides = side_1 * side_2 < 0

        return opposite_sides

    @final
    def _find_expansion_locations(self) -> None:
        """Ran once at the start of the game to calculate expansion locations."""
        # Idea: create a group for every resource, then merge these groups if
        # any resource in a group is closer than a threshold to any resource of another group

        # Distance we group resources by
        resource_spread_threshold: float = 10.5
        # Create a group for every resource
        resource_groups: list[list[Unit]] = [
            [resource]
            for resource in self.resources
            if resource.name != "MineralField450"  # dont use low mineral count patches
        ]
        # Loop the merging process as long as we change something
        merged_group = True
        height_grid: PixelMap = self.game_info.terrain_height
        while merged_group:
            merged_group = False
            # Check every combination of two groups
            for group_a, group_b in itertools.combinations(resource_groups, 2):
                # Check if any pair of resource of these groups is closer than threshold together
                # And that they are on the same terrain level
                center_a = self._cluster_center(group_a)
                center_b = self._cluster_center(group_b)

                if center_a.distance_to(center_b) <= resource_spread_threshold and all(
                    abs(height_grid[res_a.position.rounded] - height_grid[res_b.position.rounded]) <= 10
                    for res_a in group_a
                    for res_b in group_b
                ):
                    # Remove the single groups and add the merged group
                    resource_groups.remove(group_a)
                    resource_groups.remove(group_b)
                    resource_groups.append(group_a + group_b)
                    merged_group = True
                    break

        # Distance offsets we apply to center of each resource group to find expansion position
        offset_range: int = 7
        offsets: list[tuple[float, float]] = [
            (x, y)
            for x, y in itertools.product(range(-offset_range, offset_range + 1), repeat=2)
            if 4 < math.hypot(x, y) <= 8
        ]
        # Dict we want to return
        centers = {}
        # For every resource group:
        for resources in resource_groups:
            # Possible expansion points
            amount = len(resources)
            # this check is needed for TorchesAIE where the gold mineral wall has a
            # unit type of `RichMineralField` so we can only filter out by amount of resources
            if amount > 12:
                continue

            minerals = [r for r in resources if r._proto.unit_type not in geyser_ids]
            gas_geysers = [r for r in resources if r._proto.unit_type in geyser_ids]

            # Check if we have exactly 2 gas geysers positioned above/below the mineral line
            # Needed for TorchesAIE where one gold base has 2 expansion locations
            if self._has_opposite_side_geyser_layout(minerals, gas_geysers):
                # Create expansion locations for each geyser + minerals
                for geyser in gas_geysers:
                    local_resources = minerals + [geyser]
                    result: Point2 = self._find_expansion_location(local_resources, len(local_resources), offsets)
                    centers[result] = local_resources
                    # Put all expansion locations in a list
                    self._expansion_positions_list.append(result)
                    # Maps all resource positions to the expansion position
                    for resource in local_resources:
                        if resource.position in self._resource_location_to_expansion_position_dict:
                            self._resource_location_to_expansion_position_dict[resource.position].add(result)
                        else:
                            self._resource_location_to_expansion_position_dict[resource.position] = {result}

                continue

            # Choose best fitting point
            result: Point2 = self._find_expansion_location(resources, amount, offsets)
            centers[result] = resources
            # Put all expansion locations in a list
            self._expansion_positions_list.append(result)
            # Maps all resource positions to the expansion position
            for resource in resources:
                self._resource_location_to_expansion_position_dict[resource.position] = {result}

    @final
    def _correct_zerg_supply(self) -> None:
        """The client incorrectly rounds zerg supply down instead of up (see
        https://github.com/Blizzard/s2client-proto/issues/123), so self.supply_used
        and friends return the wrong value when there are an odd number of zerglings
        and banelings. This function corrects the bad values."""
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

    @final
    @property_cache_once_per_frame
    def _abilities_count_and_build_progress(self) -> tuple[Counter[AbilityId], dict[AbilityId, float]]:
        """Cache for the already_pending function, includes protoss units warping in,
        all units in production and all structures, and all morphs"""
        abilities_amount: Counter[AbilityId] = Counter()
        max_build_progress: dict[AbilityId, float] = {}
        ability_by_id = cast(Dict[int, AbilityId], AbilityId._value2member_map_)        
        structure_type_ids = self.game_data.structure_type_ids
        is_terran = self.race == Race.Terran

        unit: Unit
        for unit in self.all_own_units:
            proto = unit._proto

            # Read the raw protobuf orders: this avoids constructing a
            # UnitOrder and a Point2 for every order.
            for order in proto.orders:
                abilities_amount[ability_by_id[order.ability_id]] += 1

            if proto.build_progress == 1:
                continue
            # An SCV constructing a Terran structure is already counted by its
            # build order; do not count the structure a second time.
            if is_terran and proto.unit_type in structure_type_ids:
                continue

            unit_type = unit.type_id
            creation_ability = CREATION_ABILITY_FIX.get(unit_type)
            if creation_ability is None:
                creation_ability_data = self.game_data.units[proto.unit_type].creation_ability
                if creation_ability_data is None:
                    continue
                creation_ability = creation_ability_data.exact_id
                abilities_amount[creation_ability] += 1
            elif unit_type == UnitTypeId.ARCHON:
                creation_ability = AbilityId.ARCHON_WARP_TARGET
                abilities_amount[creation_ability] += 2
            else:
                # Hotfix for rich geysirs, cocoons, interceptors, etc.
                abilities_amount[creation_ability] += 1

            max_build_progress[creation_ability] = max(
                max_build_progress.get(creation_ability, 0), proto.build_progress
            )

        return abilities_amount, max_build_progress

    @final
    @property_cache_once_per_frame
    def _worker_orders(self) -> Counter[AbilityId]:
        """This function is used internally, do not use! It is to store all worker abilities."""
        abilities_amount: Counter[AbilityId] = Counter()
        structures_in_production: set[Point2 | int] = set()
        for structure in self.structures:
            if structure.type_id in TERRAN_STRUCTURES_REQUIRE_SCV:
                structures_in_production.add(structure.position)
                structures_in_production.add(structure.tag)
        for worker in self.workers:
            for order in worker.orders:
                # Skip if the SCV is constructing (not isinstance(order.target, int))
                # or resuming construction (isinstance(order.target, int))
                if order.target in structures_in_production:
                    continue
                abilities_amount[order.ability.exact_id] += 1
        return abilities_amount

    @final
    def do(
        self: BotAI,
        action: UnitCommand,
        subtract_cost: bool = False,
        subtract_supply: bool = False,
        can_afford_check: bool = False,
        ignore_warning: bool = False,
    ) -> bool:
        """Adds a unit action to the 'self.actions' list which is then executed at the end of the frame.

        Training a unit::

            # Train an SCV from a random idle command center
            cc = self.townhalls.idle.random_or(None)
            # self.townhalls can be empty or there are no idle townhalls
            if cc and self.can_afford(UnitTypeId.SCV):
                cc.train(UnitTypeId.SCV)

        Building a building::

            # Building a barracks at the main ramp, requires 150 minerals and a depot
            worker = self.workers.random_or(None)
            barracks_placement_position = self.main_base_ramp.barracks_correct_placement
            if worker and self.can_afford(UnitTypeId.BARRACKS):
                worker.build(UnitTypeId.BARRACKS, barracks_placement_position)

        Moving a unit::

            # Move a random worker to the center of the map
            worker = self.workers.random_or(None)
            # worker can be None if all are dead
            if worker:
                worker.move(self.game_info.map_center)

        :param action:
        :param subtract_cost:
        :param subtract_supply:
        :param can_afford_check:
        """
        if not self.unit_command_uses_self_do and isinstance(action, bool):
            if not ignore_warning:
                warnings.warn(
                    "You have used self.do(). Please consider putting 'self.unit_command_uses_self_do = True' in your bot __init__() function or removing self.do().",
                    DeprecationWarning,
                    stacklevel=2,
                )
            return action

        assert isinstance(action, UnitCommand), (
            f"Given unit command is not a command, but instead of type {type(action)}"
        )
        if subtract_cost:
            cost: Cost = self.game_data.calculate_ability_cost(action.ability)
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
        self.actions.append(action)
        self.unit_tags_received_action.add(action.unit.tag)
        return True

    @final
    async def synchronous_do(self: BotAI, action: UnitCommand):
        """
        Not recommended. Use self.do instead to reduce lag.
        This function is only useful for realtime=True in the first frame of the game to instantly produce a worker
        and split workers on the mineral patches.
        """
        assert isinstance(action, UnitCommand), (
            f"Given unit command is not a command, but instead of type {type(action)}"
        )
        if not self.can_afford(action.ability):
            logger.warning(f"Cannot afford action {action}")
            return ActionResult.Error
        r: ActionResult = await self.client.actions(action)  # pyrefly: ignore
        if not r:  # success
            cost = self.game_data.calculate_ability_cost(action.ability)
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene
            self.unit_tags_received_action.add(action.unit.tag)
        else:
            logger.error(f"Error: {r} (action: {action})")
        return r

    @final
    async def _do_actions(self, actions: list[UnitCommand], prevent_double: bool = True):
        """Used internally by main.py after each step

        :param actions:
        :param prevent_double:"""
        if not actions:
            return None
        if prevent_double:
            actions = list(filter(self.prevent_double_actions, actions))
        result = await self.client.actions(actions)
        return result

    @final
    @staticmethod
    def prevent_double_actions(action: UnitCommand) -> bool:
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
            if action.ability not in {current_action.ability.id, current_action.ability.exact_id}:
                # Different action, return True
                return True
            with suppress(AttributeError):
                if current_action.target == action.target.tag:  # pyrefly: ignore
                    # Same action, remove action if same target unit
                    return False
            with suppress(AttributeError):
                if (
                    # pyrefly: ignore
                    action.target.x == current_action.target.x and action.target.y == current_action.target.y
                ):
                    # Same action, remove action if same target position
                    return False
            return True
        return True

    @final
    def _prepare_start(
        self,
        client: Client,
        player_id: int,
        game_info: GameInfo,
        game_data: GameData,
        realtime: bool = False,
        base_build: int = -1,
    ) -> None:
        """
        Ran until game start to set game and player data.

        :param client:
        :param player_id:
        :param game_info:
        :param game_data:
        :param realtime:
        """
        self.client: Client = client
        self.player_id: int = player_id
        self.game_info: GameInfo = game_info
        self.game_data: GameData = game_data
        self.realtime: bool = realtime
        self.base_build: int = base_build

        # Get the player's race. As observer, get Race.NoRace=0
        self.race: Race = Race(self.game_info.player_races.get(self.player_id, 0))
        # Get the enemy's race only if we are not observer (replay) and the game has 2 players
        if self.player_id > 0 and len(self.game_info.player_races) == 2:
            self.enemy_race: Race = Race(self.game_info.player_races[3 - self.player_id])

        self._distances_override_functions(self.distance_calculation_method)

    @final
    def _prepare_first_step(self) -> None:
        """First step extra preparations. Must not be called before _prepare_step."""
        if self.townhalls:
            self.game_info.player_start_location = self.townhalls.first.position
            # Calculate and cache expansion locations forever inside 'self._cache_expansion_locations', this is done to prevent a bug when this is run and cached later in the game
            self._find_expansion_locations()
        self.game_info.map_ramps, self.game_info.vision_blockers = self.game_info._find_ramps_and_vision_blockers()
        self._time_before_step: float = time.perf_counter()

    @final
    def _prepare_step(self: BotAI, state: GameState, proto_game_info: sc_pb.Response) -> None:
        """
        :param state:
        :param proto_game_info:
        """
        # Set attributes from new state before on_step."""
        self.state = state  # See game_state.py
        # update pathing grid, which unfortunately is in GameInfo instead of GameState
        self.game_info.pathing_grid = PixelMap(proto_game_info.game_info.start_raw.pathing_grid, in_bits=True)
        # Required for events, needs to be before self.units are initialized so the old units are stored
        self._units_previous_map: dict[int, Unit] = {unit.tag: unit for unit in self.units}
        self._structures_previous_map: dict[int, Unit] = {structure.tag: structure for structure in self.structures}
        self._enemy_units_previous_map: dict[int, Unit] = {unit.tag: unit for unit in self.enemy_units}
        self._enemy_structures_previous_map: dict[int, Unit] = {
            structure.tag: structure for structure in self.enemy_structures
        }
        self._all_units_previous_map: dict[int, Unit] = {unit.tag: unit for unit in self.all_units}

        self._prepare_units()
        self.minerals: int = state.common.minerals
        self.vespene: int = state.common.vespene
        self.supply_army: int = state.common.food_army
        self.supply_workers: int = state.common.food_workers  # Doesn't include workers in production
        self.supply_cap: int = state.common.food_cap
        self.supply_used: int = state.common.food_used
        self.supply_left: int = self.supply_cap - self.supply_used

        if self.race == Race.Zerg:
            # Workaround Zerg supply rounding bug
            self._correct_zerg_supply()
        elif self.race == Race.Protoss:
            self.warp_gate_count: int = state.common.warp_gate_count

        self.idle_worker_count: int = state.common.idle_worker_count
        self.army_count: int = state.common.army_count
        self._time_before_step: float = time.perf_counter()

        if self.enemy_race == Race.Random and self.all_enemy_units:
            self.enemy_race = Race(self.all_enemy_units.first.race)

    @final
    def _prepare_units(self: BotAI) -> None:
        # Set of enemy units detected by own sensor tower, as blips have less unit information than normal visible units
        self.blips: set[Blip] = set()
        self.all_units: Units = Units([], self)
        self.units: Units = Units([], self)
        self.workers: Units = Units([], self)
        self.larva: Units = Units([], self)
        self.structures: Units = Units([], self)
        self.townhalls: Units = Units([], self)
        self.gas_buildings: Units = Units([], self)
        self.all_own_units: Units = Units([], self)
        self.enemy_units: Units = Units([], self)
        self.enemy_structures: Units = Units([], self)
        self.all_enemy_units: Units = Units([], self)
        self.resources: Units = Units([], self)
        self.destructables: Units = Units([], self)
        self.watchtowers: Units = Units([], self)
        self.mineral_field: Units = Units([], self)
        self.vespene_geyser: Units = Units([], self)
        self.placeholders: Units = Units([], self)
        self.techlab_tags: set[int] = set()
        self.reactor_tags: set[int] = set()

        worker_types: set[UnitTypeId] = {UnitTypeId.DRONE, UnitTypeId.DRONEBURROWED, UnitTypeId.SCV, UnitTypeId.PROBE}
        structure_types: frozenset[int] = self.game_data.structure_types

        index: int = 0
        for unit in self.state.observation_raw.units:
            if unit.is_blip:
                self.blips.add(Blip(unit))
            else:
                unit_type: int = unit.unit_type
                # Convert these units to effects: reaper grenade, parasitic bomb dummy, forcefield
                if unit_type in FakeEffectID:
                    self.state.effects.add(EffectData(unit, fake=True))
                    continue
                unit_obj = Unit(unit, self, distance_calculation_index=index, base_build=self.base_build)
                index += 1
                self.all_units.append(unit_obj)
                if unit.display_type == IS_PLACEHOLDER:
                    self.placeholders.append(unit_obj)
                    continue
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
                    self.all_own_units.append(unit_obj)
                    unit_id: UnitTypeId = unit_obj.type_id
                    if unit_type in structure_types:
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
                        if unit_id in worker_types:
                            self.workers.append(unit_obj)
                        elif unit_id == UnitTypeId.LARVA:
                            self.larva.append(unit_obj)
                # Alliance.Enemy.value = 4
                elif alliance == 4:
                    self.all_enemy_units.append(unit_obj)
                    if unit_type in structure_types:
                        self.enemy_structures.append(unit_obj)
                    else:
                        self.enemy_units.append(unit_obj)

        # Force distance calculation and caching on all units using scipy pdist or cdist
        if self.distance_calculation_method == 1:
            _ = self._pdist
        elif self.distance_calculation_method in {2, 3}:
            _ = self._cdist

    @final
    async def _after_step(self) -> int:
        """Executed by main.py after each on_step function."""
        # Keep track of the bot on_step duration
        self._time_after_step: float = time.perf_counter()
        step_duration = self._time_after_step - self._time_before_step
        self._min_step_time = min(step_duration, self._min_step_time)
        self._max_step_time = max(step_duration, self._max_step_time)
        self._last_step_step_time = step_duration
        self._total_time_in_on_step += step_duration
        self._total_steps_iterations += 1
        # Commit and clear bot actions
        if self.actions:
            await self._do_actions(self.actions)
            self.actions.clear()
        # Clear set of unit tags that were given an order this frame
        self.unit_tags_received_action.clear()
        # Commit debug queries
        await self.client._send_debug()

        return self.state.game_loop

    @final
    async def _advance_steps(self: BotAI, steps: int) -> None:
        """Advances the game loop by amount of 'steps'. This function is meant to be used as a debugging and testing tool only.
        If you are using this, please be aware of the consequences, e.g. 'self.units' will be filled with completely new data."""
        await self._after_step()
        # Advance simulation by exactly "steps" frames
        await self.client.step(steps)
        state = await self.client.observation()
        gs = GameState(state.observation)
        proto_game_info = await self.client._execute(game_info=sc_pb.RequestGameInfo())
        self._prepare_step(gs, proto_game_info)
        await self.issue_events()

    @final
    async def issue_events(self: BotAI) -> None:
        """This function will be automatically run from main.py and triggers the following functions:
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

    @final
    async def _issue_unit_added_events(self: BotAI) -> None:
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

    @final
    async def _issue_upgrade_events(self: BotAI) -> None:
        difference = self.state.upgrades - self._previous_upgrades
        for upgrade_completed in difference:
            await self.on_upgrade_complete(upgrade_completed)
        self._previous_upgrades = self.state.upgrades

    @final
    async def _issue_building_events(self: BotAI) -> None:
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

    @final
    async def _issue_vision_events(self: BotAI) -> None:
        # Call events for enemy unit entered vision
        for enemy_unit in self.enemy_units:
            if enemy_unit.tag not in self._enemy_units_previous_map:
                await self.on_enemy_unit_entered_vision(enemy_unit)
        for enemy_structure in self.enemy_structures:
            if enemy_structure.tag not in self._enemy_structures_previous_map:
                await self.on_enemy_unit_entered_vision(enemy_structure)

        # Call events for enemy unit left vision
        enemy_units_left_vision: set[int] = set(self._enemy_units_previous_map) - self.enemy_units.tags
        for enemy_unit_tag in enemy_units_left_vision:
            await self.on_enemy_unit_left_vision(enemy_unit_tag)
        enemy_structures_left_vision: set[int] = set(self._enemy_structures_previous_map) - self.enemy_structures.tags
        for enemy_structure_tag in enemy_structures_left_vision:
            await self.on_enemy_unit_left_vision(enemy_structure_tag)

    @final
    async def _issue_unit_dead_events(self: BotAI) -> None:
        for unit_tag in self.state.dead_units & set(self._all_units_previous_map):
            await self.on_unit_destroyed(unit_tag)

    # DISTANCE CALCULATION

    @final
    @property
    def _units_count(self) -> int:
        return len(self.all_units)

    @final
    @property
    def _pdist(self) -> np.ndarray:
        """As property, so it will be recalculated each time it is called, or return from cache if it is called multiple times in teh same game_loop."""
        if self._generated_frame != self.state.game_loop:
            return self.calculate_distances()
        return self._cached_pdist

    @final
    @property
    def _cdist(self) -> np.ndarray:
        """As property, so it will be recalculated each time it is called, or return from cache if it is called multiple times in teh same game_loop."""
        if self._generated_frame != self.state.game_loop:
            return self.calculate_distances()
        return self._cached_cdist

    @final
    def _calculate_distances_method1(self) -> np.ndarray:
        self._generated_frame = self.state.game_loop
        # Converts tuple [(1, 2), (3, 4)] to flat list like [1, 2, 3, 4]
        flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
        # Converts to numpy array, then converts the flat array back to shape (n, 2): [[1, 2], [3, 4]]
        positions_array: np.ndarray = np.fromiter(
            flat_positions,
            dtype=float,
            count=2 * self._units_count,
        ).reshape((self._units_count, 2))
        assert len(positions_array) == self._units_count
        # See performance benchmarks
        self._cached_pdist = pdist(positions_array, "sqeuclidean")

        return self._cached_pdist

    @final
    def _calculate_distances_method2(self) -> np.ndarray:
        self._generated_frame = self.state.game_loop
        # Converts tuple [(1, 2), (3, 4)] to flat list like [1, 2, 3, 4]
        flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
        # Converts to numpy array, then converts the flat array back to shape (n, 2): [[1, 2], [3, 4]]
        positions_array: np.ndarray = np.fromiter(
            flat_positions,
            dtype=float,
            count=2 * self._units_count,
        ).reshape((self._units_count, 2))
        assert len(positions_array) == self._units_count
        # See performance benchmarks
        self._cached_cdist = cdist(positions_array, positions_array, "sqeuclidean")

        return self._cached_cdist

    @final
    def _calculate_distances_method3(self) -> np.ndarray:
        """Nearly same as above, but without asserts"""
        self._generated_frame = self.state.game_loop
        flat_positions = (coord for unit in self.all_units for coord in unit.position_tuple)
        positions_array: np.ndarray = np.fromiter(
            flat_positions,
            dtype=float,
            count=2 * self._units_count,
        ).reshape((-1, 2))
        # See performance benchmarks
        self._cached_cdist = cdist(positions_array, positions_array, "sqeuclidean")

        return self._cached_cdist

    # Helper functions

    @final
    def square_to_condensed(self, i, j) -> int:
        # Converts indices of a square matrix to condensed matrix
        # https://stackoverflow.com/a/36867493/10882657
        assert i != j, "No diagonal elements in condensed matrix! Diagonal elements are zero"
        if i < j:
            i, j = j, i
        return self._units_count * j - j * (j + 1) // 2 + i - 1 - j

    @final
    @staticmethod
    def convert_tuple_to_numpy_array(pos: tuple[float, float]) -> np.ndarray:
        """Converts a single position to a 2d numpy array with 1 row and 2 columns."""
        return np.fromiter(pos, dtype=float, count=2).reshape((1, 2))

    # Fast and simple calculation functions

    @final
    @staticmethod
    def distance_math_hypot(
        p1: _PointLike,
        p2: _PointLike,
    ) -> float:
        return math.hypot(p1[0] - p2[0], p1[1] - p2[1])

    @final
    @staticmethod
    def distance_math_hypot_squared(
        p1: _PointLike,
        p2: _PointLike,
    ) -> float:
        return pow(p1[0] - p2[0], 2) + pow(p1[1] - p2[1], 2)

    @final
    def _distance_squared_unit_to_unit_method0(self, unit1: Unit, unit2: Unit) -> float:
        return self.distance_math_hypot_squared(unit1.position_tuple, unit2.position_tuple)

    # Distance calculation using the pre-calculated matrix above

    @final
    def _distance_squared_unit_to_unit_method1(self, unit1: Unit, unit2: Unit) -> float:
        # If checked on units if they have the same tag, return distance 0 as these are not in the 1 dimensional pdist array - would result in an error otherwise
        if unit1.tag == unit2.tag:
            return 0
        # Calculate index, needs to be after pdist has been calculated and cached
        condensed_index = self.square_to_condensed(unit1.distance_calculation_index, unit2.distance_calculation_index)
        assert condensed_index < len(self._cached_pdist), (
            f"Condensed index is larger than amount of calculated distances: {condensed_index} < {len(self._cached_pdist)}, units that caused the assert error: {unit1} and {unit2}"
        )
        distance = self._pdist[condensed_index]
        return distance

    @final
    def _distance_squared_unit_to_unit_method2(self, unit1: Unit, unit2: Unit) -> float:
        # Calculate index, needs to be after cdist has been calculated and cached
        return self._cdist[unit1.distance_calculation_index, unit2.distance_calculation_index]

    # Distance calculation using the fastest distance calculation functions

    @final
    def _distance_pos_to_pos(
        self,
        pos1: tuple[float, float] | Point2,
        pos2: tuple[float, float] | Point2,
    ) -> float:
        return self.distance_math_hypot(pos1, pos2)

    @final
    def _distance_units_to_pos(
        self,
        units: Units,
        pos: tuple[float, float] | Point2,
    ) -> Generator[float, None, None]:
        """This function does not scale well, if len(units) > 100 it gets fairly slow"""
        return (self.distance_math_hypot(u.position_tuple, pos) for u in units)

    @final
    def _distance_unit_to_points(
        self,
        unit: Unit,
        points: Iterable[tuple[float, float]],
    ) -> Generator[float, None, None]:
        """This function does not scale well, if len(points) > 100 it gets fairly slow"""
        pos = unit.position_tuple
        return (self.distance_math_hypot(p, pos) for p in points)

    @final
    def _distances_override_functions(self, method: int = 0) -> None:
        """Overrides the internal distance calculation functions at game start in bot_ai.py self._prepare_start() function
        method 0: Use python's math.hypot
        The following methods calculate the distances between all units once:
        method 1: Use scipy's pdist condensed matrix (1d array)
        method 2: Use scipy's cidst square matrix (2d array)
        method 3: Use scipy's cidst square matrix (2d array) without asserts (careful: very weird error messages, but maybe slightly faster)"""
        assert 0 <= method <= 3, f"Selected method was: {method}"
        if method == 0:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method0
        elif method == 1:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method1
            self.calculate_distances = self._calculate_distances_method1
        elif method == 2:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method2
            self.calculate_distances = self._calculate_distances_method2
        elif method == 3:
            self._distance_squared_unit_to_unit = self._distance_squared_unit_to_unit_method2
            self.calculate_distances = self._calculate_distances_method3
