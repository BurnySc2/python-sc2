from __future__ import annotations
import itertools
import logging
import math
import random
from collections import Counter
from typing import Any, Dict, List, Optional, Set, Tuple, Union, TYPE_CHECKING

from sc2.cache import property_cache_forever, property_cache_once_per_frame
from sc2.constants import (
    FakeEffectID,
    abilityid_to_unittypeid,
    geyser_ids,
    mineral_ids,
    TERRAN_TECH_REQUIREMENT,
    PROTOSS_TECH_REQUIREMENT,
    ZERG_TECH_REQUIREMENT,
)
from sc2.data import ActionResult, Alert, Race, Result, Target, race_gas, race_townhalls, race_worker
from sc2.distances import DistanceCalculation
from sc2.game_data import AbilityData, GameData

from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM
from sc2.dicts.unit_train_build_abilities import TRAIN_INFO
from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
from sc2.dicts.unit_research_abilities import RESEARCH_INFO

# Imports for mypy and pycharm autocomplete as well as sphinx autodocumentation
from sc2.game_state import Blip, EffectData, GameState
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.pixel_map import PixelMap
from sc2.position import Point2, Point3
from sc2.unit import Unit
from sc2.units import Units
from sc2.game_data import Cost

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from sc2.game_info import GameInfo, Ramp
    from sc2.client import Client
    from sc2.unit_command import UnitCommand


class ObserverAI(DistanceCalculation):
    """Base class for bots."""

    EXPANSION_GAP_THRESHOLD = 15

    def _initialize_variables(self):
        DistanceCalculation.__init__(self)
        # Specific opponent bot ID used in sc2ai ladder games http://sc2ai.net/
        # The bot ID will stay the same each game so your bot can "adapt" to the opponent
        self.opponent_id: int = None
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
        self.supply_army: Union[float, int] = None
        # Doesn't include workers in production
        self.supply_workers: Union[float, int] = None
        self.supply_cap: Union[float, int] = None
        self.supply_used: Union[float, int] = None
        self.supply_left: Union[float, int] = None
        self.idle_worker_count: int = None
        self.army_count: int = None
        self.warp_gate_count: int = None
        self.larva_count: int = None
        self.actions: List[UnitCommand] = []
        self.blips: Set[Blip] = set()
        self._unit_tags_seen_this_game: Set[int] = set()
        self._units_previous_map: Dict[int, Unit] = dict()
        self._structures_previous_map: Dict[int, Unit] = dict()
        self._previous_upgrades: Set[UpgradeId] = set()
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
        assert isinstance(
            alert_code, Alert), f"alert_code {alert_code} is no Alert"
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

    @property_cache_once_per_frame
    def _abilities_all_units(self) -> Counter:
        """ Cache for the already_pending function, includes protoss units warping in,
        all units in production and all structures, and all morphs """
        abilities_amount = Counter()
        for unit in self.units + self.structures:  # type: Unit
            for order in unit.orders:
                abilities_amount[order.ability] += 1
            if not unit.is_ready:
                if self.race != Race.Terran or not unit.is_structure:
                    # If an SCV is constructing a building, already_pending would count this structure twice
                    # (once from the SCV order, and once from "not structure.is_ready")
                    abilities_amount[self._game_data.units[unit.type_id.value].creation_ability] += 1

        return abilities_amount

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

    def _prepare_first_step(self):
        """First step extra preparations. Must not be called before _prepare_step."""
        if self.townhalls:
            self._game_info.player_start_location = self.townhalls.first.position
        self._game_info.map_ramps, self._game_info.vision_blockers = self._game_info._find_ramps_and_vision_blockers()

    def _prepare_step(self, state, proto_game_info):
        """
        :param state:
        :param proto_game_info:
        """
        # Set attributes from new state before on_step."""
        self.state: GameState = state  # See game_state.py
        # Required for events, needs to be before self.units are initialized so the old units are stored
        self._units_previous_map: Dict = {
            unit.tag: unit for unit in self.units}
        self._structures_previous_map: Dict = {
            structure.tag: structure for structure in self.structures}

        self._prepare_units()

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
                unit_obj = Unit(unit, self)
                self.units.append(unit_obj)

    async def _after_step(self) -> int:
        """ Executed by main.py after each on_step function. """
        self.unit_tags_received_action.clear()
        # Commit debug queries
        await self._client._send_debug()
        return self.state.game_loop

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

    async def _issue_unit_added_events(self):
        for unit in self.units:
            if unit.tag not in self._units_previous_map and unit.tag not in self._unit_tags_seen_this_game:
                self._unit_tags_seen_this_game.add(unit.tag)
                await self.on_unit_created(unit)

    async def _issue_upgrade_events(self):
        difference = self.state.upgrades - self._previous_upgrades
        for upgrade_completed in difference:
            await self.on_upgrade_complete(upgrade_completed)
        self._previous_upgrades = self.state.upgrades

    async def _issue_building_events(self):
        for structure in self.structures:
            # Check build_progress < 1 to exclude starting townhall
            if structure.tag not in self._structures_previous_map and structure.build_progress < 1:
                await self.on_building_construction_started(structure)
                continue
            # From here on, only check completed structure, so we ignore structures with build_progress < 1
            if structure.build_progress < 1:
                continue
            # Using get function in case somehow the previous structure map (from last frame) does not contain this structure
            structure_prev = self._structures_previous_map.get(
                structure.tag, None)
            if structure_prev and structure_prev.build_progress < 1:
                await self.on_building_construction_complete(structure)

    async def _issue_unit_dead_events(self):
        for unit_tag in self.state.dead_units:
            await self.on_unit_destroyed(unit_tag)

    async def on_unit_destroyed(self, unit_tag):
        """
        Override this in your bot class.
        Note that this function uses unit tags and not the unit objects
        because the unit does not exist any more.

        :param unit_tag:
        """

    async def on_unit_created(self, unit: Unit):
        """ Override this in your bot class. This function is called when a unit is created.

        :param unit: """

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

    async def on_start(self):
        """
        Override this in your bot class. This function is called after "on_start". 
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
        """ Override this in your bot class. This function is called at the end of a game.

        :param game_result: """
