# pyre-ignore-all-errors[6, 11, 16]
"""
This class is very experimental and probably not up to date and needs to be refurbished.
If it works, you can watch replays with it.
"""

from __future__ import annotations

from sc2.bot_ai_internal import BotAIInternal
from sc2.data import Alert, Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.upgrade_id import UpgradeId
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class ObserverAI(BotAIInternal):
    """Base class for bots."""

    @property
    def time(self) -> float:
        """Returns time in seconds, assumes the game is played on 'faster'"""
        return self.state.game_loop / 22.4  # / (1/1.4) * (1/16)

    @property
    def time_formatted(self) -> str:
        """Returns time as string in min:sec format"""
        t = self.time
        return f"{int(t // 60):02}:{int(t % 60):02}"

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
        return self.game_info.player_start_location

    @property
    def enemy_start_locations(self) -> list[Point2]:
        """Possible start locations for enemies."""
        return self.game_info.start_locations

    async def get_available_abilities(
        self, units: list[Unit] | Units, ignore_resource_requirements: bool = False
    ) -> list[list[AbilityId]]:
        """Returns available abilities of one or more units. Right now only checks cooldown, energy cost, and whether the ability has been researched.

        Examples::

            units_abilities = await self.get_available_abilities(self.units)

        or::

            units_abilities = await self.get_available_abilities([self.units.random])

        :param units:
        :param ignore_resource_requirements:"""
        return await self.client.query_available_abilities(units, ignore_resource_requirements)

    async def on_unit_destroyed(self, unit_tag: int) -> None:
        """
        Override this in your bot class.
        This will event will be called when a unit (or structure, friendly or enemy) dies.
        For enemy units, this only works if the enemy unit was in vision on death.

        :param unit_tag:
        """

    async def on_unit_created(self, unit: Unit) -> None:
        """Override this in your bot class. This function is called when a unit is created.

        :param unit:"""

    async def on_building_construction_started(self, unit: Unit) -> None:
        """
        Override this in your bot class.
        This function is called when a building construction has started.

        :param unit:
        """

    async def on_building_construction_complete(self, unit: Unit) -> None:
        """
        Override this in your bot class. This function is called when a building
        construction is completed.

        :param unit:
        """

    async def on_upgrade_complete(self, upgrade: UpgradeId) -> None:
        """
        Override this in your bot class. This function is called with the upgrade id of an upgrade that was not finished last step and is now.

        :param upgrade:
        """

    async def on_start(self) -> None:
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

    async def on_end(self, game_result: Result) -> None:
        """Override this in your bot class. This function is called at the end of a game.

        :param game_result:"""
