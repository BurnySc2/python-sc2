import itertools
import logging
import math
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union  # mypy type checking

from .cache import property_cache_forever, property_cache_once_per_frame
from .data import ActionResult, Alert, Race, Result, Target, race_gas, race_townhalls, race_worker
from .game_data import AbilityData, GameData

# imports for mypy and pycharm autocomplete
from .game_state import GameState
from .ids.ability_id import AbilityId
from .ids.unit_typeid import UnitTypeId
from .ids.upgrade_id import UpgradeId
from .pixel_map import PixelMap
from .position import Point2, Point3
from .unit import Unit
from .units import Units

logger = logging.getLogger(__name__)


class BotAI:
    """Base class for bots."""

    EXPANSION_GAP_THRESHOLD = 15

    def __init__(self):
        # Specific opponent bot ID used in sc2ai ladder games http://sc2ai.net/
        # The bot ID will stay the same each game so your bot can "adapt" to the opponent
        self.opponent_id: int = None
        self.units: Units = None
        self.workers: Units = None
        self.townhalls: Units = None
        self.geysers: Units = None
        self.minerals: int = None
        self.vespene: int = None
        self.supply_army: Union[float, int] = None
        self.supply_workers: Union[float, int] = None  # Doesn't include workers in production
        self.supply_cap: Union[float, int] = None
        self.supply_used: Union[float, int] = None
        self.supply_left: Union[float, int] = None
        self.idle_worker_count: int = None
        self.army_count: int = None
        self.warp_gate_count: int = None
        self.larva_count: int = None
        self.cached_known_enemy_structures = None
        self.cached_known_enemy_units = None

    @property
    def time(self) -> Union[int, float]:
        """ Returns time in seconds, assumes the game is played on 'faster' """
        return self.state.game_loop / 22.4  # / (1/1.4) * (1/16)

    @property
    def time_formatted(self) -> str:
        """ Returns time as string in min:sec format """
        t = self.time
        return f"{int(t // 60):02}:{int(t % 60):02}"

    @property
    def game_info(self) -> "GameInfo":
        """ See game_info.py """
        return self._game_info

    def alert(self, alert_code: Alert) -> bool:
        """
        Check if alert is triggered in the current step.

        Example use:
        from sc2.data import Alert
        if self.alert(Alert.AddOnComplete):
            print("Addon Complete")

        Alert codes:

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
        
        """
        assert isinstance(alert_code, Alert), f"alert_code {alert_code} is no Alert"
        return alert_code.value in self.state.alerts

    @property
    def start_location(self) -> Point2:
        return self._game_info.player_start_location

    @property
    def enemy_start_locations(self) -> List[Point2]:
        """Possible start locations for enemies."""
        return self._game_info.start_locations

    @property_cache_once_per_frame
    def known_enemy_units(self) -> Units:
        """List of known enemy units, including structures."""
        return self.state.enemy_units

    @property_cache_once_per_frame
    def known_enemy_structures(self) -> Units:
        """List of known enemy units, structures only."""
        return self.state.enemy_units.structure

    @property
    def main_base_ramp(self) -> "Ramp":
        """ Returns the Ramp instance of the closest main-ramp to start location.
        Look in game_info.py for more information """
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
        # any resource in a group is closer than 6 to any resource of another group

        # Distance we group resources by
        RESOURCE_SPREAD_THRESHOLD = 8.5
        geysers = self.state.vespene_geyser
        # Create a group for every resource
        resource_groups = [[resource] for resource in self.state.resources]
        # Loop the merging process as long as we change something
        found_something = True
        while found_something:
            found_something = False
            # Check every combination of two groups
            for group_a, group_b in itertools.combinations(resource_groups, 2):
                # Check if any pair of resource of these groups is closer than threshold together
                if any(
                    resource_a.distance_to(resource_b) <= RESOURCE_SPREAD_THRESHOLD
                    for resource_a, resource_b in itertools.product(group_a, group_b)
                ):
                    # Remove the single groups and add the merged group
                    resource_groups.remove(group_a)
                    resource_groups.remove(group_b)
                    resource_groups.append(group_a + group_b)
                    found_something = True
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
        self, units: Union[List[Unit], Units], ignore_resource_requirements=False
    ) -> List[List[AbilityId]]:
        """ Returns available abilities of one or more units. Right know only checks cooldown, energy cost, and whether the ability has been researched.
        Example usage:
        units_abilities = await self.get_available_abilities(self.units)
        or
        units_abilities = await self.get_available_abilities([self.units.random]) """
        return await self._client.query_available_abilities(units, ignore_resource_requirements)

    async def expand_now(
        self, building: UnitTypeId = None, max_distance: Union[int, float] = 10, location: Optional[Point2] = None
    ):
        """ Not recommended as this function uses 'self.do' (reduces performance).
        Finds the next possible expansion via 'self.get_next_expansion()'. If the target expansion is blocked (e.g. an enemy unit), it will misplace the expansion. """

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
        ratio is bigger than `resource_ratio`, this function prefer filling geysers
        first, if it is lower, it will prefer sending workers to minerals first.
        This is only for workers that need to be moved anyways, it will NOT will
        geysers on its own.

        NOTE: This function is far from optimal, if you really want to have
        refined worker control, you should write your own distribution function.
        For example long distance mining control and moving workers if a base was killed
        are not being handled.

        WARNING: This is quite slow when there are lots of workers or multiple bases.
        """
        if not self.state.mineral_field or not self.workers or not self.townhalls.ready:
            return
        actions = []
        worker_pool = [worker for worker in self.workers.idle]
        bases = self.townhalls.ready
        geysers = self.geysers.ready

        # list of places that need more workers
        deficit_mining_places = []

        for mining_place in bases | geysers:
            difference = mining_place.surplus_harvesters
            # perfect amount of workers, skip mining place
            if not difference:
                continue
            if mining_place.is_vespene_geyser:
                # get all workers that target the gas extraction site
                # or are on their way back from it
                local_workers = self.workers.filter(
                    lambda unit: unit.order_target == mining_place.tag
                    or (unit.is_carrying_vespene and unit.order_target == bases.closest_to(mining_place).tag)
                )
            else:
                # get tags of minerals around expansion
                local_minerals_tags = {
                    mineral.tag for mineral in self.state.mineral_field if mineral.distance_to(mining_place) <= 8
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
                for mineral in self.state.mineral_field
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
                    actions.append(worker.gather(current_place))
                # if current place is a gas extraction site,
                # go to the mineral field that is near and has the most minerals left
                else:
                    local_minerals = [
                        mineral for mineral in self.state.mineral_field if mineral.distance_to(current_place) <= 8
                    ]
                    target_mineral = max(local_minerals, key=lambda mineral: mineral.mineral_contents)
                    actions.append(worker.gather(target_mineral))
            # more workers to distribute than free mining spots
            # send to closest if worker is doing nothing
            elif worker.is_idle and all_minerals_near_base:
                target_mineral = min(all_minerals_near_base, key=lambda mineral: mineral.distance_to(worker))
                actions.append(worker.gather(target_mineral))
            else:
                # there are no deficit mining places and worker is not idle
                # so dont move him
                pass

        await self.do_actions(actions)

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

    def can_feed(self, unit_type: UnitTypeId) -> bool:
        """ Checks if you have enough free supply to build the unit """
        required = self._game_data.units[unit_type.value]._proto.food_required
        return required == 0 or self.supply_left >= required

    def can_afford(
        self, item_id: Union[UnitTypeId, UpgradeId, AbilityId], check_supply_cost: bool = True
    ) -> "CanAffordWrapper":
        """Tests if the player has enough resources to build a unit or cast an ability."""
        enough_supply = True
        if isinstance(item_id, UnitTypeId):
            unit = self._game_data.units[item_id.value]
            cost = self._game_data.calculate_ability_cost(unit.creation_ability)
            if check_supply_cost:
                enough_supply = self.can_feed(item_id)
        elif isinstance(item_id, UpgradeId):
            cost = self._game_data.upgrades[item_id.value].cost
        else:
            cost = self._game_data.calculate_ability_cost(item_id)

        return CanAffordWrapper(cost.minerals <= self.minerals, cost.vespene <= self.vespene, enough_supply)

    async def can_cast(
        self,
        unit: Unit,
        ability_id: AbilityId,
        target: Optional[Union[Unit, Point2, Point3]] = None,
        only_check_energy_and_cooldown: bool = False,
        cached_abilities_of_unit: List[AbilityId] = None,
    ) -> bool:
        """Tests if a unit has an ability available and enough energy to cast it.
        See data_pb2.py (line 161) for the numbers 1-5 to make sense"""
        assert isinstance(unit, Unit), f"{unit} is no Unit object"
        assert isinstance(ability_id, AbilityId), f"{ability_id} is no AbilityId"
        assert isinstance(target, (type(None), Unit, Point2, Point3))
        # check if unit has enough energy to cast or if ability is on cooldown
        if cached_abilities_of_unit:
            abilities = cached_abilities_of_unit
        else:
            abilities = (await self.get_available_abilities([unit]))[0]

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
                and unit.distance_to(target) <= cast_range
            ):  # cant replace 1 with "Target.None.value" because ".None" doesnt seem to be a valid enum name
                return True
            # Check if able to use ability on a unit
            elif (
                ability_target in {Target.Unit.value, Target.PointOrUnit.value}
                and isinstance(target, Unit)
                and unit.distance_to(target) <= cast_range
            ):
                return True
            # Check if able to use ability on a position
            elif (
                ability_target in {Target.Point.value, Target.PointOrUnit.value}
                and isinstance(target, (Point2, Point3))
                and unit.distance_to(target) <= cast_range
            ):
                return True
        return False

    def select_build_worker(self, pos: Union[Unit, Point2, Point3], force: bool = False) -> Optional[Unit]:
        """Select a worker to build a building with."""
        workers = (
            self.workers.filter(lambda w: (w.is_gathering or w.is_idle) and w.distance_to(pos) < 20) or self.workers
        )
        if workers:
            for worker in workers.sorted_by_distance_to(pos).prefer_idle:
                if (
                    not worker.orders
                    or len(worker.orders) == 1
                    and worker.orders[0].ability.id in {AbilityId.MOVE, AbilityId.HARVEST_GATHER}
                ):
                    return worker

            return workers.random if force else None

    async def can_place(self, building: Union[AbilityData, AbilityId, UnitTypeId], position: Point2) -> bool:
        """Tests if a building can be placed in the given location."""
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
        """Finds a placement location for building."""

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

    def already_pending_upgrade(self, upgrade_type: UpgradeId) -> Union[int, float]:
        """ Check if an upgrade is being researched
        Return values:
        0: not started
        0 < x < 1: researching
        1: finished
        """
        assert isinstance(upgrade_type, UpgradeId), f"{upgrade_type} is no UpgradeId"
        if upgrade_type in self.state.upgrades:
            return 1
        level = None
        if "LEVEL" in upgrade_type.name:
            level = upgrade_type.name[-1]
        creationAbilityID = self._game_data.upgrades[upgrade_type.value].research_ability.id
        for structure in self.units.filter(lambda unit: unit.is_structure and unit.is_ready):
            for order in structure.orders:
                if order.ability.id is creationAbilityID:
                    if level and order.ability.button_name[-1] != level:
                        return 0
                    return order.progress
        return 0

    @property_cache_once_per_frame
    def _abilities_all_units(self) -> Counter:
        """ Cache for the already_pending function, includes protoss units warping in, and all units in production, and all structures, and all morphs """
        abilities_amount = Counter()
        for unit in self.units:  # type: Unit
            for order in unit.orders:
                abilities_amount[order.ability] += 1
            if not unit.is_ready:
                if self.race != Race.Terran or not unit.is_structure:
                    # If an SCV is constructing a building, already_pending would count this structure twice (once from the SCV order, and once from "not structure.is_ready")
                    abilities_amount[self._game_data.units[unit.type_id.value].creation_ability] += 1

        return abilities_amount

    @property_cache_once_per_frame
    def _abilities_workers_and_eggs(self) -> Counter:
        """ Cache for the already_pending function, includes all worker orders (including pending).
        Zerg units in production (except queens and morphing units) and structures in production,
        counts double for terran """
        abilities_amount = Counter()
        for worker in self.workers:  # type: Unit
            for order in worker.orders:
                abilities_amount[order.ability] += 1
        if self.race == Race.Zerg:
            for egg in self.units(UnitTypeId.EGG):  # type: Unit
                for order in egg.orders:
                    abilities_amount[order.ability] += 1
        if self.race != Race.Terran:
            # If an SCV is constructing a building, already_pending would count this structure twice
            # (once from the SCV order, and once from "not structure.is_ready")
            for unit in self.units.structure.not_ready:  # type: Unit
                abilities_amount[self._game_data.units[unit.type_id.value].creation_ability] += 1
        return abilities_amount

    def already_pending(self, unit_type: Union[UpgradeId, UnitTypeId], all_units: bool = True) -> int:
        """
        Returns a number of buildings or units already in progress, or if a
        worker is en route to build it. This also includes queued orders for
        workers and build queues of buildings.

        If all_units==True, then build queues of other units (such as Carriers
        (Interceptors) or Oracles (Stasis Ward)) are also included.
        """

        # TODO / FIXME: SCV building a structure might be counted as two units

        if isinstance(unit_type, UpgradeId):
            return self.already_pending_upgrade(unit_type)

        ability = self._game_data.units[unit_type.value].creation_ability

        if all_units:
            return self._abilities_all_units[ability]
        else:
            return self._abilities_workers_and_eggs[ability]

    async def build(
        self,
        building: UnitTypeId,
        near: Union[Point2, Point3],
        max_distance: int = 20,
        unit: Optional[Unit] = None,
        random_alternative: bool = True,
        placement_step: int = 2,
    ):
        """ Not recommended as this function uses 'self.do' (reduces performance).
        Also if the position is not placeable, this function tries to find a nearby position to place the structure. Then uses 'self.do' to give the worker the order to start the construction. """

        if isinstance(near, Unit):
            near = near.position.to2
        elif near is not None:
            near = near.to2
        else:
            return

        p = await self.find_placement(building, near, max_distance, random_alternative, placement_step)
        if p is None:
            return ActionResult.CantFindPlacementLocation

        unit = unit or self.select_build_worker(p)
        if unit is None or not self.can_afford(building):
            return ActionResult.Error
        return await self.do(unit.build(building, p))

    async def do(self, action):
        """ Not recommended. Use self.do_actions once per iteration instead to reduce lag:
        self.actions = []
        cc = self.units(COMMANDCENTER).random
        self.actions.append(cc.train(SCV))
        await self.do_action(self.actions) """
        if not self.can_afford(action):
            logger.warning(f"Cannot afford action {action}")
            return ActionResult.Error

        r = await self._client.actions(action)

        if not r:  # success
            cost = self._game_data.calculate_ability_cost(action.ability)
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene

        else:
            logger.error(f"Error: {r} (action: {action})")

        return r

    async def do_actions(self, actions: List["UnitCommand"], prevent_double=True):
        """ Unlike 'self.do()', this function does not instantly subtract minerals and vespene. """
        if not actions:
            return None
        if prevent_double:
            actions = list(filter(self.prevent_double_actions, actions))
        for action in actions:
            cost = self._game_data.calculate_ability_cost(action.ability)
            self.minerals -= cost.minerals
            self.vespene -= cost.vespene

        return await self._client.actions(actions)

    def prevent_double_actions(self, action):
        # always add actions if queued
        if action.queue:
            return True
        if action.unit.orders:
            # action: UnitCommand
            # current_action: UnitOrder
            current_action = action.unit.orders[0]
            if current_action.ability.id != action.ability:
                # different action, return true
                return True
            try:
                if current_action.target == action.target.tag:
                    # same action, remove action if same target unit
                    return False
            except AttributeError:
                pass
            try:
                if action.target.x == current_action.target.x and action.target.y == current_action.target.y:
                    # same action, remove action if same target position
                    return False
            except AttributeError:
                pass
            return True
        return True

    async def chat_send(self, message: str):
        """ Send a chat message. """
        assert isinstance(message, str), f"{message} is no string"
        await self._client.chat_send(message, False)

    # For the functions below, make sure you are inside the boundries of the map size.
    def get_terrain_height(self, pos: Union[Point2, Point3, Unit]) -> int:
        """ Returns terrain height at a position.
        Caution: terrain height is different from a unit's z-coordinate.
        """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.terrain_height[pos]

    def get_terrain_z_height(self, pos: Union[Point2, Point3, Unit]) -> int:
        """ Returns terrain z-height at a position. """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return -16 + 32 * self._game_info.terrain_height[pos] / 255

    def in_placement_grid(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if you can place something at a position.
        Remember, buildings usually use 2x2, 3x3 or 5x5 of these grid points.
        Caution: some x and y offset might be required, see ramp code:
        https://github.com/Dentosal/python-sc2/blob/master/sc2/game_info.py#L17-L18 """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.placement_grid[pos] == 1

    def in_pathing_grid(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if a unit can pass through a grid point. """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self._game_info.pathing_grid[pos] == 1

    def is_visible(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if you have vision on a grid point. """
        # more info: https://github.com/Blizzard/s2client-proto/blob/9906df71d6909511907d8419b33acc1a3bd51ec0/s2clientprotocol/spatial.proto#L19
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self.state.visibility[pos] == 2

    def has_creep(self, pos: Union[Point2, Point3, Unit]) -> bool:
        """ Returns True if there is creep on the grid point. """
        assert isinstance(pos, (Point2, Point3, Unit)), f"pos is not of type Point2, Point3 or Unit"
        pos = pos.position.to2.rounded
        return self.state.creep[pos] == 1

    def _prepare_start(self, client, player_id, game_info, game_data):
        """Ran until game start to set game and player data."""
        self._client: "Client" = client
        self._game_info: "GameInfo" = game_info
        self._game_data: GameData = game_data

        self.player_id: int = player_id
        self.race: Race = Race(self._game_info.player_races[self.player_id])

        if len(self._game_info.player_races) == 2:
            self.enemy_race: Race = Race(self._game_info.player_races[3 - self.player_id])

        self._units_previous_map: dict = dict()
        self._previous_upgrades: Set[UpgradeId] = set()
        self.units: Units = Units([])

    def _prepare_first_step(self):
        """First step extra preparations. Must not be called before _prepare_step."""
        if self.townhalls:
            self._game_info.player_start_location = self.townhalls.first.position
        self._game_info.map_ramps, self._game_info.vision_blockers = self._game_info._find_ramps_and_vision_blockers()

    def _prepare_step(self, state, proto_game_info):
        # Set attributes from new state before on_step."""
        self.state: GameState = state  # See game_state.py
        # update pathing grid
        self._game_info.pathing_grid: PixelMap = PixelMap(
            proto_game_info.game_info.start_raw.pathing_grid, in_bits=True, mirrored=False
        )
        # Required for events
        self._units_previous_map: Dict = {unit.tag: unit for unit in self.units}
        self.units: Units = state.own_units
        self.workers: Units = self.units(race_worker[self.race])
        self.townhalls: Units = self.units(race_townhalls[self.race])
        self.geysers: Units = self.units(race_gas[self.race])
        self.minerals: int = state.common.minerals
        self.vespene: int = state.common.vespene
        self.supply_army: int = state.common.food_army
        self.supply_workers: int = state.common.food_workers  # Doesn't include workers in production
        self.supply_cap: int = state.common.food_cap
        self.supply_used: int = state.common.food_used
        self.supply_left: int = self.supply_cap - self.supply_used

        if self.race == Race.Zerg:
            self.larva_count: int = state.common.larva_count
            # Workaround Zerg supply rounding bug
            self._correct_zerg_supply()
        elif self.race == Race.Protoss:
            self.warp_gate_count: int = state.common.warp_gate_count

        self.idle_worker_count: int = state.common.idle_worker_count
        self.army_count: int = state.common.army_count
        # reset cached values
        self.cached_known_enemy_structures = None
        self.cached_known_enemy_units = None

    async def issue_events(self):
        """ This function will be automatically run from main.py and triggers the following functions:
        - on_unit_created
        - on_unit_destroyed
        - on_building_construction_complete
        - on_upgrade_complete
        """
        await self._issue_unit_dead_events()
        await self._issue_unit_added_events()
        for unit in self.units.structure:
            await self._issue_building_complete_event(unit)
        if len(self._previous_upgrades) != len(self.state.upgrades):
            for upgrade_completed in self.state.upgrades - self._previous_upgrades:
                await self.on_upgrade_complete(upgrade_completed)
            self._previous_upgrades = self.state.upgrades

    async def _issue_unit_added_events(self):
        for unit in self.units:
            if unit.tag not in self._units_previous_map:
                if unit.is_structure:
                    await self.on_building_construction_started(unit)
                else:
                    await self.on_unit_created(unit)

    async def _issue_building_complete_event(self, unit):
        if unit.build_progress < 1:
            return
        if unit.tag not in self._units_previous_map:
            return
        unit_prev = self._units_previous_map[unit.tag]
        if unit_prev.build_progress < 1:
            await self.on_building_construction_complete(unit)

    async def _issue_unit_dead_events(self):
        for unit_tag in self.state.dead_units:
            await self.on_unit_destroyed(unit_tag)

    async def on_unit_destroyed(self, unit_tag):
        """ Override this in your bot class.
        Note that this function uses unit tags because the unit does not exist any more. """

    async def on_unit_created(self, unit: Unit):
        """ Override this in your bot class. """

    async def on_building_construction_started(self, unit: Unit):
        """ Override this in your bot class. """

    async def on_building_construction_complete(self, unit: Unit):
        """ Override this in your bot class. Note that this function is also
        triggered at the start of the game for the starting base building."""

    async def on_upgrade_complete(self, upgrade: UpgradeId):
        """ Override this in your bot class. """

    def on_start(self):
        """ Allows initializing the bot when the game data is available. """

    async def on_start_async(self):
        """ This function is run after "on_start". At this point, game_data, game_info and
        the first iteration of game_state (self.state) are available. """

    async def on_step(self, iteration: int):
        """Ran on every game step (looped in realtime mode)."""
        raise NotImplementedError

    def on_end(self, game_result: Result):
        """ Triggered at the end of a game. """


class CanAffordWrapper:
    def __init__(self, can_afford_minerals, can_afford_vespene, have_enough_supply):
        self.can_afford_minerals = can_afford_minerals
        self.can_afford_vespene = can_afford_vespene
        self.have_enough_supply = have_enough_supply

    def __bool__(self):
        return self.can_afford_minerals and self.can_afford_vespene and self.have_enough_supply

    @property
    def action_result(self):
        if not self.can_afford_vespene:
            return ActionResult.NotEnoughVespene
        elif not self.can_afford_minerals:
            return ActionResult.NotEnoughMinerals
        elif not self.have_enough_supply:
            return ActionResult.NotEnoughFood
        else:
            return None
