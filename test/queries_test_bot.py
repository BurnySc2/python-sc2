import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import random
import math

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.data import Alliance

from sc2.position import Pointlike, Point2, Point3
from sc2.units import Units
from sc2.unit import Unit

from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.upgrade_id import UpgradeId
from sc2.ids.effect_id import EffectId

from typing import List, Set, Dict, Optional, Union

from loguru import logger


"""
This testbot's purpose is to test the query behavior of the API.
These query functions are:
self.can_place (RequestQueryBuildingPlacement)
TODO: self.client.query_pathing (RequestQueryPathing)
"""


class TestBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
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
        exit(0)

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
        if not isinstance(unit_type, List):
            unit_type = [unit_type]
        for i in unit_type:
            await self.client.debug_create_unit([[i, 1, self.game_info.map_center, 1]])

    async def spawn_unit_enemy(self, unit_type: Union[UnitTypeId, List[UnitTypeId]]):
        if not isinstance(unit_type, List):
            unit_type = [unit_type]
        for i in unit_type:
            await self.client.debug_create_unit([[i, 1, self.game_info.map_center, 2]])

    async def run_can_place(self) -> bool:
        await self._advance_steps(20)
        result = await self.can_place(AbilityId.TERRANBUILD_COMMANDCENTER, [self.game_info.map_center])
        return result[0]

    async def test_can_place_expect_true(self):
        test_cases = [
            [UnitTypeId.OVERLORD, UnitTypeId.DARKTEMPLAR],
            [UnitTypeId.ZEALOT, None],
            [None, UnitTypeId.ZEALOT],
            [None, UnitTypeId.SUPPLYDEPOT],
            [None, UnitTypeId.DARKTEMPLAR],
            [None, UnitTypeId.ROACHBURROWED],
        ]

        for i, (own_unit_type, enemy_unit_type) in enumerate(test_cases):
            if own_unit_type:
                await self.spawn_unit(own_unit_type)
            if enemy_unit_type:
                await self.spawn_unit_enemy(enemy_unit_type)
            result = await self.run_can_place()
            if result:
                logger.info(f"Test case successful: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}")
            else:
                logger.error(
                    f"Expected result to be True, but was False for test case: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}"
                )
            assert result, f"Expected result to be False, but was True for test case: {i}"
            await self.clear_map_center()

    async def test_can_place_expect_false(self):
        test_cases = [
            [UnitTypeId.OVERLORD, UnitTypeId.ZEALOT],
            [UnitTypeId.OVERLORD, UnitTypeId.SUPPLYDEPOT],
            [UnitTypeId.OVERLORD, UnitTypeId.CREEPTUMOR],
            [UnitTypeId.OBSERVER, UnitTypeId.CREEPTUMOR],
            [UnitTypeId.OBSERVER, UnitTypeId.DARKTEMPLAR],
            [UnitTypeId.OVERLORD, UnitTypeId.ROACHBURROWED],
            [UnitTypeId.OBSERVER, UnitTypeId.ROACHBURROWED],
            [UnitTypeId.OVERLORD, UnitTypeId.MINERALFIELD450],
            [UnitTypeId.OVERLORD, UnitTypeId.CHANGELING],
            [UnitTypeId.OBSERVER, UnitTypeId.CHANGELING],
            [UnitTypeId.COMMANDCENTER, None],
            # True for linux client:
            # [None, UnitTypeId.MINERALFIELD450],
        ]

        for i, (own_unit_type, enemy_unit_type) in enumerate(test_cases):
            if own_unit_type:
                await self.spawn_unit(own_unit_type)
            if enemy_unit_type:
                await self.spawn_unit_enemy(enemy_unit_type)
            result = await self.run_can_place()
            if result:
                logger.error(
                    f"Expected result to be False, but was True for test case: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}"
                )
            else:
                logger.info(f"Test case successful: {i}, own unit: {own_unit_type}, enemy unit: {enemy_unit_type}")
            assert not result, f"Expected result to be False, but was True for test case: {i}"
            await self.clear_map_center()


class EmptyBot(sc2.BotAI):
    async def on_step(self, iteration: int):
        for unit in self.units:
            unit.hold_position()


def main():
    sc2.run_game(sc2.maps.get("Empty128"), [Bot(Race.Terran, TestBot()), Bot(Race.Zerg, EmptyBot())], realtime=False)


if __name__ == "__main__":
    main()
