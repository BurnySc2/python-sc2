"""
This testbot's purpose is to test the query behavior of the API.
These query functions are:
self.can_place (RequestQueryBuildingPlacement)
TODO: self.client.query_pathing (RequestQueryPathing)
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from typing import List, Union

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot
from sc2.position import Point2


class TestBot(BotAI):
    def __init__(self):
        # The time the bot has to complete all tests, here: the number of game seconds
        self.game_time_timeout_limit = 20 * 60  # 20 minutes ingame time

    async def on_start(self):
        self.client.game_step = 16

    async def on_step(self, iteration):
        if iteration <= 7:
            return

        await self.clear_map_center()
        await self.test_can_place_expect_true()
        await self.test_can_place_expect_false()

        # await self.client.leave()
        sys.exit(0)

    async def clear_map_center(self):
        """ Spawn observer in map center, remove all enemy units, remove all own units. """
        map_center = self.game_info.map_center

        # Spawn observer to be able to see enemy invisible units
        await self.client.debug_create_unit([[UnitTypeId.OBSERVER, 1, map_center, 1]])
        await self._advance_steps(10)

        # Remove everything close to map center
        enemy_units = self.enemy_units | self.enemy_structures
        if enemy_units:
            await self.client.debug_kill_unit(enemy_units)
            await self._advance_steps(10)

        neutral_units = self.resources
        if neutral_units:
            await self.client.debug_kill_unit(neutral_units)
            await self._advance_steps(10)

        my_units = self.units | self.structures
        if my_units:
            await self.client.debug_kill_unit(my_units)
            await self._advance_steps(10)

    async def spawn_unit(self, unit_type: Union[UnitTypeId, List[UnitTypeId]]):
        await self._advance_steps(10)
        if not isinstance(unit_type, List):
            unit_type = [unit_type]
        for i in unit_type:
            await self.client.debug_create_unit([[i, 1, self.game_info.map_center, 1]])

    async def spawn_unit_enemy(self, unit_type: Union[UnitTypeId, List[UnitTypeId]]):
        await self._advance_steps(10)
        if not isinstance(unit_type, List):
            unit_type = [unit_type]
        for i in unit_type:
            if i == UnitTypeId.CREEPTUMOR:
                await self.client.debug_create_unit([[i, 1, self.game_info.map_center + Point2((5, 5)), 2]])
            else:
                await self.client.debug_create_unit([[i, 1, self.game_info.map_center, 2]])

    async def run_can_place(self) -> bool:
        # await self._advance_steps(200)
        result = await self.can_place(AbilityId.TERRANBUILD_COMMANDCENTER, [self.game_info.map_center])
        return result[0]

    async def run_can_place_single(self) -> bool:
        # await self._advance_steps(200)
        result = await self.can_place(AbilityId.TERRANBUILD_COMMANDCENTER, [self.game_info.map_center])
        return result[0]

    async def test_can_place_expect_true(self):
        test_cases = [
            # Invisible undetected enemy units
            [UnitTypeId.OVERLORD, UnitTypeId.DARKTEMPLAR],
            [UnitTypeId.OVERLORD, UnitTypeId.ROACHBURROWED],
            [UnitTypeId.OVERLORD, UnitTypeId.ZERGLINGBURROWED],
            [UnitTypeId.BARRACKSFLYING, UnitTypeId.WIDOWMINEBURROWED],
            # Own units
            [UnitTypeId.ZEALOT, None],
            # Enemy units and structures, but without vision
            [None, UnitTypeId.ZEALOT],
            [None, UnitTypeId.SUPPLYDEPOT],
            [None, UnitTypeId.DARKTEMPLAR],
            [None, UnitTypeId.ROACHBURROWED],
        ]

        for i, (own_unit_type, enemy_unit_type) in enumerate(test_cases):
            if enemy_unit_type:
                await self.spawn_unit_enemy(enemy_unit_type)
            if own_unit_type:
                await self.spawn_unit(own_unit_type)

            # Wait for creep
            if enemy_unit_type == UnitTypeId.CREEPTUMOR:
                await self._advance_steps(1000)
            else:
                await self._advance_steps(10)

            result = await self.run_can_place()
            if result:
                logger.info(f"Test case successful: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}")
            else:
                logger.error(
                    f"Expected result to be True, but was False for test case: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}"
                )
            assert result, f"Expected result to be False, but was True for test case: {i}"
            result2 = await self.run_can_place_single()
            if result2:
                logger.info(f"Test case successful: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}")
            else:
                logger.error(
                    f"Expected result2 to be True, but was False for test case: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}"
                )
            assert result2, f"Expected result to be False, but was True for test case: {i}"
            await self.clear_map_center()

    async def test_can_place_expect_false(self):
        test_cases = [
            # Own structures
            [UnitTypeId.COMMANDCENTER, None],
            # Enemy structures
            [UnitTypeId.OVERLORD, UnitTypeId.SUPPLYDEPOT],
            [UnitTypeId.OVERLORD, UnitTypeId.SUPPLYDEPOTLOWERED],
            # Visible units
            [UnitTypeId.OVERLORD, UnitTypeId.ZEALOT],
            [UnitTypeId.OVERLORD, UnitTypeId.SIEGETANKSIEGED],
            # Visible creep
            [UnitTypeId.OVERLORD, UnitTypeId.CREEPTUMOR],
            [UnitTypeId.OBSERVER, UnitTypeId.CREEPTUMOR],
            # Invisible but detected units
            [UnitTypeId.OBSERVER, UnitTypeId.DARKTEMPLAR],
            [UnitTypeId.OBSERVER, UnitTypeId.ROACHBURROWED],
            [UnitTypeId.OBSERVER, UnitTypeId.WIDOWMINEBURROWED],
            # Special cases
            [UnitTypeId.SIEGETANKSIEGED, None],
            [UnitTypeId.OVERLORD, UnitTypeId.CHANGELING],
            [UnitTypeId.OBSERVER, UnitTypeId.CHANGELING],
            # True for linux client, False for windows client:
            # [UnitTypeId.OVERLORD, UnitTypeId.MINERALFIELD450],
            # [None, UnitTypeId.MINERALFIELD450],
        ]

        for i, (own_unit_type, enemy_unit_type) in enumerate(test_cases):
            if own_unit_type:
                await self.spawn_unit(own_unit_type)
            if enemy_unit_type:
                await self.spawn_unit_enemy(enemy_unit_type)

            # Wait for creep
            if enemy_unit_type == UnitTypeId.CREEPTUMOR:
                await self._advance_steps(1000)
            else:
                await self._advance_steps(10)

            result = await self.run_can_place()
            if result:
                logger.error(
                    f"Expected result to be False, but was True for test case: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}"
                )
            else:
                logger.info(f"Test case successful: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}")
            assert not result, f"Expected result to be False, but was True for test case: {i}"
            await self.clear_map_center()

        # TODO Losing vision of a blocking enemy unit, check if can_place still returns False
        #   for: creep, burrowed ling, burrowed roach, dark templar

        # TODO Check if a moving invisible unit is blocking (patroulling dark templar, patroulling burrowed roach)


class EmptyBot(BotAI):
    async def on_step(self, iteration: int):
        for unit in self.units:
            unit.hold_position()


def main():
    run_game(maps.get("Empty128"), [Bot(Race.Terran, TestBot()), Bot(Race.Zerg, EmptyBot())], realtime=False)


if __name__ == "__main__":
    main()
