import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import random
import logging
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

from sc2.dicts.unit_trained_from import UNIT_TRAINED_FROM

from typing import List, Set, Dict, Optional, Union

logger = logging.getLogger(__name__)


class TestBot(sc2.BotAI):
    def __init__(self):
        sc2.BotAI.__init__(self)
        # The time the bot has to complete all tests, here: the number of game seconds
        self.game_time_timeout_limit = 20 * 60  # 20 minutes ingame time

        # Check how many test action functions we have
        # At least 4 tests because we test properties and variables
        self.action_tests = [
            getattr(self, f"test_botai_actions{index}")
            for index in range(4000)
            if hasattr(getattr(self, f"test_botai_actions{index}", 0), "__call__")
        ]
        self.tests_done_by_name = set()

        # Keep track of the action index and when the last action was started
        self.current_action_index = 1
        self.iteration_last_action_started = 8
        # There will be 20 iterations of the bot doing nothing between tests
        self.iteration_wait_time_between_actions = 20

        self.scv_action_list = ["move", "patrol", "attack", "hold", "scan_move"]

        # Variables for test_botai_actions11

    async def on_start(self):
        self.client.game_step = 8
        # await self.client.quick_save()
        await self.distribute_workers()

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")
        # Test if chat message was sent correctly
        if iteration == 1:
            assert len(self.state.chat) >= 1, self.state.chat

        # Test actions
        if iteration == 7:
            for action_test in self.action_tests:
                await action_test()

        # Exit bot
        if iteration > 100:
            print("Tests completed after {} seconds".format(round(self.time, 1)))
            exit(0)

    async def clean_up_center(self):
        map_center = self.game_info.map_center
        # Remove everything close to map center
        my_units = self.units | self.structures
        if my_units:
            my_units = my_units.closer_than(20, map_center)
        if my_units:
            await self.client.debug_kill_unit(my_units)
        enemy_units = self.enemy_units | self.enemy_structures
        if enemy_units:
            enemy_units = enemy_units.closer_than(20, map_center)
        if enemy_units:
            await self.client.debug_kill_unit(enemy_units)
        await self._advance_steps(2)

    # Create all upgrade research structures and research each possible upgrade
    async def test_botai_actions1(self):
        map_center: Point2 = self._game_info.map_center

        from sc2.dicts.upgrade_researched_from import UPGRADE_RESEARCHED_FROM
        from sc2.dicts.unit_research_abilities import RESEARCH_INFO

        structure_types: List[UnitTypeId] = sorted(set(UPGRADE_RESEARCHED_FROM.values()), key=lambda data: data.name)
        upgrade_types: List[UpgradeId] = list(UPGRADE_RESEARCHED_FROM.keys())

        # TODO if *techlab in name -> spawn rax/ fact / starport next to it
        addon_structures: Dict[str, UnitTypeId] = {
            "BARRACKS": UnitTypeId.BARRACKS,
            "FACTORY": UnitTypeId.FACTORY,
            "STARPORT": UnitTypeId.STARPORT,
        }

        await self.client.debug_fast_build()

        structure_type: UnitTypeId
        for structure_type in structure_types:
            # TODO: techlabs
            if "TECHLAB" in structure_type.name:
                continue

            structure_upgrade_types: Dict[UpgradeId, Dict[str, AbilityId]] = RESEARCH_INFO[structure_type]
            data: Dict[str, AbilityId]
            for upgrade_id, data in structure_upgrade_types.items():

                # Collect data to spawn
                research_ability: AbilityId = data.get("ability", None)
                requires_power: bool = data.get("requires_power", False)
                required_building: UnitTypeId = data.get("required_building", None)

                # Prevent linux crash
                if (
                    research_ability.value not in self.game_data.abilities
                    or upgrade_id.value not in self.game_data.upgrades
                    or self.game_data.upgrades[upgrade_id.value].research_ability is None or self.game_data.upgrades[upgrade_id.value].research_ability.exact_id != research_ability
                ):
                    print(
                        f"Could not find upgrade {upgrade_id} or research ability {research_ability} in self.game_data - potential version mismatch (balance upgrade - windows vs linux SC2 client"
                    )
                    continue

                # Spawn structure and requirements
                spawn_structures: List[UnitTypeId] = []
                if requires_power:
                    spawn_structures.append(UnitTypeId.PYLON)
                spawn_structures.append(structure_type)
                if required_building:
                    spawn_structures.append(required_building)

                await self.client.debug_create_unit([[structure, 1, map_center, 1] for structure in spawn_structures])
                print(
                    f"Spawning {structure_type} to research upgrade {upgrade_id} via research ability {research_ability}"
                )
                await self._advance_steps(2)

                # Wait for the structure to spawn
                while not self.structures(structure_type):
                    # print(f"Waiting for structure {structure_type} to spawn, structures close to center so far: {self.structures.closer_than(20, map_center)}")
                    await self._advance_steps(2)

                # If cannot afford to research: cheat money
                while not self.can_afford(upgrade_id):
                    # print(f"Cheating money to be able to afford {upgrade_id}, cost: {self.calculate_cost(upgrade_id)}")
                    await self.client.debug_all_resources()
                    await self._advance_steps(2)

                # Research upgrade
                assert upgrade_id in upgrade_types, f"Given upgrade is not in the list of upgrade types"
                assert self.structures(structure_type), f"Structure {structure_type} has not been spawned in time"

                # Try to research the upgrade
                while 1:
                    upgrader_structures: Units = self.structures(structure_type)
                    # Upgrade has been researched, break
                    # Hi atira monkaBirthday
                    if upgrader_structures:
                        upgrader_structure: Unit = upgrader_structures.closest_to(map_center)
                        if upgrader_structure.is_idle:
                            # print(f"Making {upgrader_structure} research upgrade {upgrade_id}")
                            self.do(upgrader_structure.research(upgrade_id))
                        await self._advance_steps(2)
                        if upgrade_id in self.state.upgrades:
                            break

                await self.clean_up_center()
        logger.warning("Action test 1 successful.")


class EmptyBot(sc2.BotAI):
    async def on_start(self):
        if self.units:
            await self.client.debug_kill_unit(self.units)

    async def on_step(self, iteration: int):
        map_center = self.game_info.map_center
        enemies = self.enemy_units | self.enemy_structures
        if enemies:
            enemies = enemies.closer_than(20, map_center)
        if enemies:
            # If attacker is visible: move command to attacker but try to not attack
            for unit in self.units:
                self.do(unit.move(enemies.closest_to(unit).position))
        else:
            # If attacker is invisible: dont move
            for unit in self.units:
                self.do(unit.hold_position())


def main():
    sc2.run_game(sc2.maps.get("Empty128"), [Bot(Race.Terran, TestBot()), Bot(Race.Zerg, EmptyBot())], realtime=False)


if __name__ == "__main__":
    main()
