import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

import random

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


class TestBot(sc2.BotAI):
    def __init__(self):
        # Tests related
        self.game_time_timeout_limit = 2 * 60
        # Check how many test action functions we have
        self.tests_target = 4 + len(
            [True for index in range(1000) if hasattr(getattr(self, f"test_botai_actions{index}", 0), "__call__")]
        )
        self.tests_done_by_name = set()
        self.current_action_index = 1

        self.scv_action_list = ["move", "patrol", "attack", "hold", "scan_move"]

    async def on_start(self):
        await self.distribute_workers()

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")
        # Test if chat message was sent correctly
        if iteration == 1:
            assert len(self.state.chat) >= 1, self.state.chat

        # Tests at start
        if iteration == 3:
            # No need to use try except as the travis test script checks for "Traceback" in STDOUT
            await self.test_botai_properties()
            await self.test_botai_functions()
            await self.test_game_state_static_variables()
            await self.test_game_info_static_variables()

        # Test actions
        if iteration > 7:
            # Execute actions on even iterations, test if actions were successful on uneven iterations
            if iteration % 2 == 0:
                action_execute_function_name = f"test_botai_actions{self.current_action_index}"
                action_execute_function = getattr(self, action_execute_function_name, None)
                if action_execute_function is not None:
                    await action_execute_function()
            else:
                action_test_function_name = f"test_botai_actions{self.current_action_index}_successful"
                action_test_function = getattr(self, action_test_function_name, None)
                if action_test_function is not None:
                    success = await action_test_function()
                    if success:
                        self.tests_done_by_name.add(f"test_botai_actions{self.current_action_index}_successful")
                        self.current_action_index += 1

        # End when all tests successful
        if len(self.tests_done_by_name) >= self.tests_target:
            print(
                "{}/{} Tests completed after {} seconds: {}".format(
                    len(self.tests_done_by_name), self.tests_target, round(self.time, 1), self.tests_done_by_name
                )
            )
            exit(0)

        # End time reached, cancel testing and report error: took too long
        if self.time >= self.game_time_timeout_limit:
            print(
                "{}/{} Tests completed: {}\nCurrent action index is at {}".format(
                    len(self.tests_done_by_name), self.tests_target, self.tests_done_by_name, self.current_action_index
                )
            )
            print("Not all tests were successful. Timeout reached. Testing was aborted")
            exit(1000)

    # Test BotAI properties, starting conditions
    async def test_botai_properties(self):
        assert 1 <= self.player_id <= 2, self.player_id
        assert self.race == Race.Terran, self.race
        assert 0 <= self.time <= 180, self.time
        assert self.start_location == self.townhalls.random.position, (
            self.start_location,
            self.townhalls.random.position,
        )
        for loc in self.enemy_start_locations:
            assert isinstance(loc, Point2), loc
            assert loc.distance_to(self.start_location) > 20, (loc, self.start_location)
        assert self.main_base_ramp.top_center.distance_to(self.start_location) < 30, self.main_base_ramp.top_center
        assert self.can_afford(UnitTypeId.SCV)
        assert self.owned_expansions == {self.townhalls.first.position: self.townhalls.first}
        # Test if bot start location is in expansion locations
        assert self.townhalls.random.position in set(self.expansion_locations.keys())
        # Test if enemy start locations are in expansion locations
        for location in self.enemy_start_locations:
            assert location in set(self.expansion_locations.keys())

        self.tests_done_by_name.add("test_botai_properties")

    # Test BotAI functions
    async def test_botai_functions(self):
        for location in self.expansion_locations.keys():
            # Can't build on spawn locations, skip these
            if location in self.enemy_start_locations or location == self.start_location:
                continue
            assert await self.can_place(UnitTypeId.COMMANDCENTER, location)
            await self.find_placement(UnitTypeId.COMMANDCENTER, location)
        assert len(await self.get_available_abilities(self.workers)) == self.workers.amount
        # TODO: can_cast
        self.tests_done_by_name.add("test_botai_functions")

    # Test self.state variables
    async def test_game_state_static_variables(self):
        assert len(self.state.actions) == 0, self.state.actions
        assert len(self.state.action_errors) == 0, self.state.action_errors
        assert len(self.state.chat) == 0, self.state.chat
        assert self.state.game_loop > 0, self.state.game_loop
        assert self.state.score.collection_rate_minerals >= 0, self.state.score.collection_rate_minerals
        assert len(self.state.upgrades) == 0, self.state.upgrades
        self.tests_done_by_name.add("test_game_state_static_variables")

    # Test self._game_info variables
    async def test_game_info_static_variables(self):
        assert len(self._game_info.players) == 2, self._game_info.players
        assert len(self._game_info.map_ramps) >= 2, self._game_info.map_ramps
        assert len(self._game_info.player_races) == 2, self._game_info.player_races
        self.tests_done_by_name.add("test_game_info_static_variables")

    # TODO:
    # Test client.py debug functions

    # Test BotAI action: train SCV
    async def test_botai_actions1(self):
        if self.can_afford(UnitTypeId.SCV):
            self.do(self.townhalls.random.train(UnitTypeId.SCV))

    async def test_botai_actions1_successful(self):
        if self.already_pending(UnitTypeId.SCV) > 0:
            return True

    # Test BotAI action: move all SCVs to center of map
    async def test_botai_actions2(self):
        center = self._game_info.map_center
        scv: Unit
        for index, scv in enumerate(self.workers):
            if index > len(self.scv_action_list):
                self.do(scv.stop())
            action = self.scv_action_list[index % len(self.scv_action_list)]
            if action == "move":
                self.do(scv.move(center))
            elif action == "patrol":
                self.do(scv.patrol(center))
            elif action == "attack":
                self.do(scv.attack(center))
            elif action == "hold":
                self.do(scv.hold_position())
            elif action == "scan_move":
                self.do(scv.scan_move(center))

    async def test_botai_actions2_successful(self):
        def temp_filter(unit: Unit):
            return (
                unit.is_moving
                or unit.is_patrolling
                or unit.orders
                and unit.orders[0] == AbilityId.HOLDPOSITION_HOLD
                or unit.is_attacking
            )

        if self.units.filter(lambda x: temp_filter(x)).amount >= len(self.scv_action_list):
            return True

    # Test BotAI action: move some scvs to the center, some to minerals
    async def test_botai_actions3(self):
        center = self._game_info.map_center
        scvs = self.workers
        scvs1 = scvs[:6]
        scvs2 = scvs[6:]
        for scv in scvs1:
            self.do(scv.move(center))
        mf = self.mineral_field.closest_to(self.townhalls.random)
        for scv in scvs2:
            self.do(scv.gather(mf))

    async def test_botai_actions3_successful(self):
        if self.units.filter(lambda x: x.is_moving).amount >= 6 and self.units.gathering.amount >= 6:
            return True

    # Test BotAI action: move all SCVs to mine minerals near townhall
    async def test_botai_actions4(self):
        mf = self.mineral_field.closest_to(self.townhalls.random)
        for scv in self.workers:
            self.do(scv.gather(mf))

    async def test_botai_actions4_successful(self):
        if self.units.gathering.amount >= 12:
            return True

    # Test BotAI action: self.expand_now() which tests for get_next_expansion, select_build_worker, can_place, find_placement, build and can_afford
    async def test_botai_actions5(self):
        if self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(UnitTypeId.COMMANDCENTER):
            await self.get_next_expansion()
            await self.expand_now()

    async def test_botai_actions5_successful(self):
        if self.townhalls(UnitTypeId.COMMANDCENTER).amount >= 2:
            return True

    # Test if reaper grenade shows up in effects
    async def test_botai_actions6(self):
        center = self._game_info.map_center
        if self.units(UnitTypeId.REAPER).amount < 10:
            await self._client.debug_create_unit([[UnitTypeId.REAPER, 10, center, 1]])
        for reaper in self.units(UnitTypeId.REAPER):
            self.do(reaper(AbilityId.KD8CHARGE_KD8CHARGE, center))

    async def test_botai_actions6_successful(self):
        if len(self.state.effects) > 2:
            # print(f"Effects: {self.state.effects}")
            for effect in self.state.effects:
                # print(f"Effect: {effect}")
                pass
            # Cleanup
            await self._client.debug_kill_unit(self.units(UnitTypeId.REAPER))
            return True

    # Test ravager effects
    async def test_botai_actions7(self):
        center = self._game_info.map_center
        if self.units(UnitTypeId.RAVAGER).amount < 10:
            await self._client.debug_create_unit([[UnitTypeId.RAVAGER, 10, center, 1]])
        for reaper in self.units(UnitTypeId.RAVAGER):
            self.do(reaper(AbilityId.EFFECT_CORROSIVEBILE, center))

    async def test_botai_actions7_successful(self):
        success = False
        if len(self.state.effects) >= 1:
            # print(f"Effects: {self.state.effects}")
            for effect in self.state.effects:
                # print(f"Effect: {effect}")
                if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                    success = True
        if success:
            # Cleanup
            await self._client.debug_kill_unit(self.units(UnitTypeId.RAVAGER))
            return True


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, TestBot()), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
