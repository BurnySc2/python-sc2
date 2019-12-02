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
        self.tests_target = 4
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

    # Create a lot of units and check if their damage calculation is correct based on Unit.calculate_damage_vs_target()
    async def test_botai_actions1001(self):
        upgrade_levels = [0, 1]
        attacker_units = [
            #
            # Protoss
            #
            UnitTypeId.PROBE,
            # UnitTypeId.ZEALOT,
            UnitTypeId.ADEPT,
            UnitTypeId.STALKER,
            UnitTypeId.HIGHTEMPLAR,
            UnitTypeId.DARKTEMPLAR,
            UnitTypeId.ARCHON,  # Doesnt work vs workers when attacklevel > 1
            UnitTypeId.IMMORTAL,
            UnitTypeId.COLOSSUS,
            UnitTypeId.PHOENIX,
            UnitTypeId.VOIDRAY,
            # UnitTypeId.CARRIER, # TODO
            UnitTypeId.MOTHERSHIP,
            UnitTypeId.TEMPEST,
            #
            # Terran
            #
            UnitTypeId.SCV,
            UnitTypeId.MARINE,
            UnitTypeId.MARAUDER,
            UnitTypeId.GHOST,
            UnitTypeId.HELLION,
            # UnitTypeId.HELLIONTANK, # Incorrect for light targets because hellbat does not seem to have another weapon vs light specifically in the API
            # UnitTypeId.CYCLONE, # Seems to lock on as soon as it spawns
            UnitTypeId.SIEGETANK,
            UnitTypeId.THOR,
            # UnitTypeId.THORAP, # TODO uncomment when new version for linux client is released
            UnitTypeId.BANSHEE,
            UnitTypeId.VIKINGFIGHTER,
            UnitTypeId.VIKINGASSAULT,
            # UnitTypeId.BATTLECRUISER, # Does not work because weapon_cooldown is not displayed in the API
            #
            # Zerg
            #
            UnitTypeId.DRONE,
            UnitTypeId.ZERGLING,
            # UnitTypeId.BANELING, # TODO
            UnitTypeId.QUEEN,
            # UnitTypeId.ROACH, # Has bugs that I don't know how to fix
            UnitTypeId.RAVAGER,
            # UnitTypeId.HYDRALISK, # TODO
            # UnitTypeId.LURKERMPBURROWED, # Somehow fails the test
            # UnitTypeId.MUTALISK, # Mutalisk is supposed to deal 9-3-1 damage, but it seems it deals 12 damage if there is no nearby 2nd target
            UnitTypeId.CORRUPTOR,
            # UnitTypeId.BROODLORD, # Was unreliable because the broodlings would also attack
            UnitTypeId.ULTRALISK,
            # Buildings
            UnitTypeId.MISSILETURRET,
            UnitTypeId.SPINECRAWLER,
            UnitTypeId.SPORECRAWLER,
            UnitTypeId.PLANETARYFORTRESS,
        ]
        defender_units = [
            # Ideally one of each type: ground and air unit with each armor tage
            # Ground, no tag
            UnitTypeId.RAVAGER,
            # Ground, light
            UnitTypeId.MULE,
            # Ground, armored
            UnitTypeId.MARAUDER,
            # Ground, biological
            UnitTypeId.ROACH,
            # Ground, psionic
            UnitTypeId.HIGHTEMPLAR,
            # Ground, mechanical
            UnitTypeId.STALKER,
            # Ground, massive
            # UnitTypeId.ULTRALISK, # Fails vs our zergling
            # Ground, structure
            # UnitTypeId.PYLON, # Pylon seems to regenerate 1 shield for no reason
            UnitTypeId.SUPPLYDEPOT,
            UnitTypeId.BUNKER,
            UnitTypeId.MISSILETURRET,
            # Air, light
            UnitTypeId.PHOENIX,
            # Air, armored
            UnitTypeId.VOIDRAY,
            # Air, biological
            UnitTypeId.CORRUPTOR,
            # Air, psionic
            UnitTypeId.VIPER,
            # Air, mechanical
            UnitTypeId.MEDIVAC,
            # Air, massive
            UnitTypeId.BATTLECRUISER,
            # Air, structure
            UnitTypeId.BARRACKSFLYING,
            # Ground and air
            UnitTypeId.COLOSSUS,
        ]
        await self._advance_steps(20)
        map_center = self.game_info.map_center

        # Show whole map
        await self.client.debug_show_map()

        def get_attacker_and_defender():
            my_units = self.units | self.structures
            enemy_units = self.enemy_units | self.enemy_structures
            if not my_units or not enemy_units:
                # print("my units:", my_units)
                # print("enemy units:",enemy_units)
                return None, None
            attacker: Unit = my_units.closest_to(map_center)
            defender: Unit = enemy_units.closest_to(map_center)
            return attacker, defender

        def do_some_unit_property_tests(attacker: Unit, defender: Unit):
            """ Some tests that are not covered by test_pickled_data.py """
            # TODO move unit unrelated tests elsewhere
            self.step_time
            self.units_created

            self.structure_type_build_progress(attacker.type_id)
            self.structure_type_build_progress(defender.type_id)
            self.tech_requirement_progress(attacker.type_id)
            self.tech_requirement_progress(defender.type_id)
            self.in_map_bounds(attacker.position)
            self.in_map_bounds(defender.position)
            self.get_terrain_z_height(attacker.position)
            self.get_terrain_z_height(defender.position)

            for unit in [attacker, defender]:
                unit.shield_percentage
                unit.shield_health_percentage
                unit.energy_percentage
                unit.age_in_frames
                unit.age
                unit.is_memory
                unit.is_snapshot
                unit.cloak
                unit.is_revealed
                unit.can_be_attacked
                unit.buff_duration_remain
                unit.buff_duration_max
                unit.order_target
                unit.is_transforming
                unit.has_techlab
                unit.has_reactor
                unit.add_on_position
                unit.health_percentage
                unit.bonus_damage
                unit.air_dps

            attacker.target_in_range(defender)
            defender.target_in_range(attacker)
            attacker.calculate_dps_vs_target(defender)
            defender.calculate_dps_vs_target(attacker)
            attacker.is_facing(defender)
            defender.is_facing(attacker)
            attacker == defender
            defender == attacker

        await self.clean_up_center()

        attacker: Unit
        defender: Unit
        for upgrade_level in upgrade_levels:
            if upgrade_level != 0:
                await self.client.debug_upgrade()
                # await self._advance_steps(5)
            for attacker_type in attacker_units:
                for defender_type in defender_units:
                    # DT, Thor, Tempest one-shots workers, so skip test
                    if attacker_type in {
                        UnitTypeId.DARKTEMPLAR,
                        UnitTypeId.TEMPEST,
                        UnitTypeId.THOR,
                        UnitTypeId.THORAP,
                        UnitTypeId.LIBERATORAG,
                        UnitTypeId.PLANETARYFORTRESS,
                        UnitTypeId.ARCHON,
                    } and defender_type in {UnitTypeId.PROBE, UnitTypeId.DRONE, UnitTypeId.SCV, UnitTypeId.MULE}:
                        continue

                    # Spawn units
                    await self.client.debug_create_unit(
                        [[attacker_type, 1, map_center, 1], [defender_type, 1, map_center, 2]]
                    )
                    await self._advance_steps(1)

                    # Wait for units to spawn
                    attacker, defender = get_attacker_and_defender()
                    while (
                        attacker is None
                        or defender is None
                        or attacker.type_id != attacker_type
                        or defender.type_id != defender_type
                    ):
                        await self._advance_steps(1)
                        attacker, defender = get_attacker_and_defender()
                        # TODO check if shield calculation is correct by setting shield of enemy unit
                    # print(f"Attacker: {attacker}, defender: {defender}")
                    do_some_unit_property_tests(attacker, defender)

                    # Units have spawned, calculate expected damage
                    expected_damage: float = attacker.calculate_damage_vs_target(defender)[0]
                    # If expected damage is zero, it means that the attacker cannot attack the defender: skip test
                    if expected_damage == 0:
                        await self.clean_up_center()
                        continue
                    # Thor antiground seems buggy sometimes and not reliable in tests, skip it
                    if attacker_type in {UnitTypeId.THOR, UnitTypeId.THORAP} and not defender.is_flying:
                        await self.clean_up_center()
                        continue

                    real_damage = 0
                    # Limit the while loop
                    max_steps = 100
                    while (
                        attacker.weapon_cooldown == 0 or attacker.weapon_cooldown > 3
                    ) and real_damage < expected_damage:
                        if attacker_type in {UnitTypeId.PROBE, UnitTypeId.SCV, UnitTypeId.DRONE}:
                            self.do(attacker.attack(defender))
                        await self._advance_steps(1)
                        # Unsure why I have to recalculate this here again but it prevents a bug
                        attacker, defender = get_attacker_and_defender()
                        expected_damage: float = max(expected_damage, attacker.calculate_damage_vs_target(defender)[0])
                        real_damage = math.ceil(
                            defender.health_max + defender.shield_max - defender.health - defender.shield
                        )
                        # print(
                        #     f"Attacker type: {attacker_type}, defender health: {defender.health} / {defender.health_max}, defender shield: {defender.shield} / {defender.shield_max}, expected damage: {expected_damage}, real damage so far: {real_damage}, attacker weapon cooldown: {attacker.weapon_cooldown}"
                        # )
                        max_steps -= 1
                        assert (
                            max_steps > 0
                        ), f"Step limit reached. Test timed out for attacker {attacker_type} and defender {defender_type}"
                    assert (
                        expected_damage == real_damage
                    ), f"Expected damage does not match real damage: Unit type {attacker_type} (attack upgrade: {attacker.attack_upgrade_level}) deals {real_damage} damage against {defender_type} (armor upgrade: {defender.armor_upgrade_level} and shield upgrade: {defender.shield_upgrade_level}) but calculated damage was {expected_damage}, attacker weapons: \n{attacker._weapons}"

                    await self.clean_up_center()

        # Hide map again
        await self.client.debug_show_map()
        await self._advance_steps(2)
        logger.warning("Action test 1001 successful.")


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
