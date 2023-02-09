import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))

from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.effect_id import EffectId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class TestBot(BotAI):

    def __init__(self):
        BotAI.__init__(self)
        # The time the bot has to complete all tests, here: the number of game seconds
        self.game_time_timeout_limit = 20 * 60  # 20 minutes ingame time

        # Check how many test action functions we have
        # At least 4 tests because we test properties and variables
        self.action_tests = [
            getattr(self, f"test_botai_actions{index}") for index in range(4000)
            if hasattr(getattr(self, f"test_botai_actions{index}", 0), "__call__")
        ]
        self.tests_done_by_name = set()

        # Keep track of the action index and when the last action was started
        self.current_action_index = 1
        self.iteration_last_action_started = 8
        # There will be 20 iterations of the bot doing nothing between tests
        self.iteration_wait_time_between_actions = 20

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

        # Tests at start
        if iteration == 3:
            # No need to use try except as the travis test script checks for "Traceback" in STDOUT
            await self.test_botai_properties()
            await self.test_botai_functions()
            await self.test_game_state_static_variables()
            await self.test_game_info_static_variables()

        # Test actions
        if iteration == 7:
            for action_test in self.action_tests:
                await action_test()

        # Exit bot
        if iteration > 100:
            logger.info("Tests completed after {} seconds".format(round(self.time, 1)))
            exit(0)

    async def clean_up_center(self):
        map_center = self.game_info.map_center
        # Remove everything close to map center
        my_units = self.all_own_units
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
        assert self.townhalls.random.position in self.expansion_locations_list
        # Test if enemy start locations are in expansion locations
        for location in self.enemy_start_locations:
            assert location in self.expansion_locations_list

        self.tests_done_by_name.add("test_botai_properties")

    # Test BotAI functions
    async def test_botai_functions(self):
        for location in self.expansion_locations_list:
            # Can't build on spawn locations, skip these
            if location in self.enemy_start_locations or location == self.start_location:
                continue
            assert (await self.can_place(UnitTypeId.COMMANDCENTER, [location]))[0]
            assert (await self.can_place(AbilityId.TERRANBUILD_COMMANDCENTER, [location]))[0]
            # TODO Remove the following two lines if can_place function gets fully converted to only accept list of positions
            assert await self.can_place(UnitTypeId.COMMANDCENTER, [location])
            assert await self.can_place(AbilityId.TERRANBUILD_COMMANDCENTER, [location])
            assert await self.can_place_single(UnitTypeId.COMMANDCENTER, location)
            assert await self.can_place_single(AbilityId.TERRANBUILD_COMMANDCENTER, location)
            await self.find_placement(UnitTypeId.COMMANDCENTER, location)
        assert len(await self.get_available_abilities(self.workers)) == self.workers.amount
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
        assert len(self.game_info.players) == 2, self.game_info.players
        assert len(self.game_info.map_ramps) >= 2, self.game_info.map_ramps
        assert len(self.game_info.player_races) == 2, self.game_info.player_races
        self.tests_done_by_name.add("test_game_info_static_variables")

    async def test_botai_actions1(self):
        # Test BotAI action: train SCV
        while self.already_pending(UnitTypeId.SCV) < 1:
            if self.can_afford(UnitTypeId.SCV):
                self.townhalls.random.train(UnitTypeId.SCV)
            await self._advance_steps(2)

        await self._advance_steps(2)
        logger.warning("Action test 01 successful.")

    # Test BotAI action: move all SCVs to center of map
    async def test_botai_actions2(self):
        center = self.game_info.map_center

        def temp_filter(unit: Unit):
            return (
                unit.is_moving or unit.is_patrolling or unit.orders and unit.orders[0] == AbilityId.HOLDPOSITION_HOLD
                or unit.is_attacking
            )

        scv_action_list = ["move", "patrol", "attack", "hold", "scan_move"]
        while self.units.filter(lambda unit: temp_filter(unit)).amount < len(scv_action_list):
            scv: Unit
            for index, scv in enumerate(self.workers):
                if index > len(scv_action_list):
                    scv.stop()
                action = scv_action_list[index % len(scv_action_list)]
                if action == "move":
                    scv.move(center)
                elif action == "patrol":
                    scv.patrol(center)
                elif action == "attack":
                    scv.attack(center)
                elif action == "hold":
                    scv.hold_position()

            await self._advance_steps(2)

        await self._advance_steps(2)
        logger.warning("Action test 02 successful.")

    async def test_botai_actions3(self):
        # Test BotAI action: move some scvs to the center, some to minerals
        center = self.game_info.map_center

        while self.units.filter(lambda x: x.is_moving).amount < 6 and self.units.gathering.amount >= 6:
            scvs = self.workers
            scvs1 = scvs[:6]
            scvs2 = scvs[6:]
            for scv in scvs1:
                scv.move(center)
            mf = self.mineral_field.closest_to(self.townhalls.random)
            for scv in scvs2:
                scv.gather(mf)

            await self._advance_steps(2)
        await self._advance_steps(2)
        logger.warning("Action test 03 successful.")

    async def test_botai_actions4(self):
        # Test BotAI action: move all SCVs to mine minerals near townhall
        while self.units.gathering.amount < 12:
            mf = self.mineral_field.closest_to(self.townhalls.random)
            for scv in self.workers:
                scv.gather(mf)

            await self._advance_steps(2)
        await self._advance_steps(2)
        logger.warning("Action test 04 successful.")

    async def test_botai_actions5(self):
        # Test BotAI action: self.expand_now() which tests for get_next_expansion, select_build_worker, can_place, find_placement, build and can_afford
        # Wait till worker has started construction of CC
        while 1:
            if self.can_afford(UnitTypeId.COMMANDCENTER):
                await self.get_next_expansion()
                await self.expand_now()

            await self._advance_steps(10)

            assert self.structures_without_construction_SCVs(UnitTypeId.COMMANDCENTER).amount == 0

            if self.townhalls(UnitTypeId.COMMANDCENTER).amount >= 2:
                assert self.townhalls(UnitTypeId.COMMANDCENTER).not_ready.amount == 1
                assert self.already_pending(UnitTypeId.COMMANDCENTER) == 1
                # The CC construction has started, 'worker_en_route_to_build' should show 0
                assert self.worker_en_route_to_build(UnitTypeId.COMMANDCENTER) == 0
                break
            elif self.already_pending(UnitTypeId.COMMANDCENTER) == 1:
                assert self.worker_en_route_to_build(UnitTypeId.COMMANDCENTER) == 1

        await self._advance_steps(2)
        logger.warning("Action test 05 successful.")

    async def test_botai_actions6(self):
        # Test if reaper grenade shows up in effects
        center = self.game_info.map_center

        while 1:
            if self.units(UnitTypeId.REAPER).amount < 10:
                await self.client.debug_create_unit([[UnitTypeId.REAPER, 10, center, 1]])

            for reaper in self.units(UnitTypeId.REAPER):
                reaper(AbilityId.KD8CHARGE_KD8CHARGE, center)

            # logger.info(f"Effects: {self.state.effects}")
            for effect in self.state.effects:
                # logger.info(f"Effect: {effect}")
                pass
            # Cleanup
            await self._advance_steps(2)
            # Check if condition is met
            if len(self.state.effects) != 0:
                break

        await self.client.debug_kill_unit(self.units(UnitTypeId.REAPER))
        # Wait for effectts to time out
        await self._advance_steps(100)
        logger.warning("Action test 06 successful.")

    async def test_botai_actions7(self):
        # Test ravager effects
        center = self.game_info.map_center
        while 1:
            if self.units(UnitTypeId.RAVAGER).amount < 10:
                await self.client.debug_create_unit([[UnitTypeId.RAVAGER, 10, center, 1]])
            for ravager in self.units(UnitTypeId.RAVAGER):
                ravager(AbilityId.EFFECT_CORROSIVEBILE, center)

            # logger.info(f"Effects: {self.state.effects}")
            for effect in self.state.effects:
                # logger.info(f"Effect: {effect}")
                if effect.id == EffectId.RAVAGERCORROSIVEBILECP:
                    success = True
            await self._advance_steps(2)
            # Check if condition is met
            if len(self.state.effects) != 0:
                break
        # Cleanup
        await self.client.debug_kill_unit(self.units(UnitTypeId.RAVAGER))
        # Wait for effectts to time out
        await self._advance_steps(100)
        logger.warning("Action test 07 successful.")

    async def test_botai_actions8(self):
        # Test if train function works on hatchery, lair, hive
        center = self.game_info.map_center
        if not self.structures(UnitTypeId.HIVE):
            await self.client.debug_create_unit([[UnitTypeId.HIVE, 1, center, 1]])
        if not self.structures(UnitTypeId.LAIR):
            await self.client.debug_create_unit([[UnitTypeId.LAIR, 1, center, 1]])
        if not self.structures(UnitTypeId.HATCHERY):
            await self.client.debug_create_unit([[UnitTypeId.HATCHERY, 1, center, 1]])
        if not self.structures(UnitTypeId.SPAWNINGPOOL):
            await self.client.debug_create_unit([[UnitTypeId.SPAWNINGPOOL, 1, center, 1]])

        while 1:
            townhalls = self.structures.of_type({UnitTypeId.HIVE, UnitTypeId.LAIR, UnitTypeId.HATCHERY})
            if townhalls.amount == 3 and self.minerals >= 450 and not self.already_pending(UnitTypeId.QUEEN):
                self.train(UnitTypeId.QUEEN, amount=3)
                # Equivalent to:
                # for townhall in townhalls:
                #     townhall.train(UnitTypeId.QUEEN)
            await self._advance_steps(20)
            # Check if condition is met
            if self.already_pending(UnitTypeId.QUEEN) == 3:
                break

        # Cleanup
        townhalls = self.structures.of_type({UnitTypeId.HIVE, UnitTypeId.LAIR, UnitTypeId.HATCHERY})
        queens = self.units(UnitTypeId.QUEEN)
        pool = self.structures(UnitTypeId.SPAWNINGPOOL)
        await self.client.debug_kill_unit(townhalls | queens | pool)
        await self._advance_steps(2)
        logger.warning("Action test 08 successful.")

    async def test_botai_actions9(self):
        # Morph an archon from 2 high templars
        center = self.game_info.map_center
        await self.client.debug_create_unit(
            [
                [UnitTypeId.HIGHTEMPLAR, 1, center, 1],
                [UnitTypeId.DARKTEMPLAR, 1, center + Point2((5, 0)), 1],
            ]
        )
        await self._advance_steps(4)
        assert self.already_pending(UnitTypeId.ARCHON) == 0

        while 1:
            for templar in self.units.of_type({UnitTypeId.HIGHTEMPLAR, UnitTypeId.DARKTEMPLAR}):
                templar(AbilityId.MORPH_ARCHON)

            await self._advance_steps(4)

            templars = self.units.of_type({UnitTypeId.HIGHTEMPLAR, UnitTypeId.DARKTEMPLAR})
            archons = self.units(UnitTypeId.ARCHON)
            if templars.amount > 0:
                # High templars are on their way to morph ot morph has started
                assert self.already_pending(UnitTypeId.ARCHON) == 1
            else:
                # Morph started
                assert self.already_pending(UnitTypeId.ARCHON) == archons.not_ready.amount

            # Check if condition is met
            if archons.ready.amount == 1:
                assert templars.amount == 0
                assert self.already_pending(UnitTypeId.ARCHON) == 0
                break

        # Cleanup
        if archons:
            await self.client.debug_kill_unit(archons)
        if templars:
            await self.client.debug_kill_unit(templars)
        await self._advance_steps(2)
        logger.warning("Action test 09 successful.")

    async def test_botai_actions10(self):
        # Morph 400 banelings from 400 lings in the same frame
        center = self.game_info.map_center

        target_amount = 400
        while 1:
            bane_nests = self.structures(UnitTypeId.BANELINGNEST)
            lings = self.units(UnitTypeId.ZERGLING)
            banes = self.units(UnitTypeId.BANELING)
            bane_cocoons = self.units(UnitTypeId.BANELINGCOCOON)

            # Cheat money, need 10k/10k to morph 400 lings to 400 banes
            if not banes and not bane_cocoons:
                if self.minerals < 10_000:
                    await self.client.debug_all_resources()
                elif self.vespene < 10_000:
                    await self.client.debug_all_resources()

            # Spawn units
            if not bane_nests:
                await self.client.debug_create_unit([[UnitTypeId.BANELINGNEST, 1, center, 1]])
            current_amount = banes.amount + bane_cocoons.amount + lings.amount
            if current_amount < target_amount:
                await self.client.debug_create_unit([[UnitTypeId.ZERGLING, target_amount - current_amount, center, 1]])

            if lings.amount >= target_amount and self.minerals >= 10_000 and self.vespene >= 10_000:
                for ling in lings:
                    ling.train(UnitTypeId.BANELING)
            await self._advance_steps(20)

            # Check if condition is met
            bane_nests = self.structures(UnitTypeId.BANELINGNEST)
            lings = self.units(UnitTypeId.ZERGLING)
            banes = self.units(UnitTypeId.BANELING)
            bane_cocoons = self.units(UnitTypeId.BANELINGCOCOON)
            if banes.amount >= target_amount:
                break

        # Cleanup
        await self.client.debug_kill_unit(lings | banes | bane_nests | bane_cocoons)
        await self._advance_steps(2)
        logger.warning("Action test 10 successful.")

    async def test_botai_actions11(self):
        # Trigger anti armor missile of raven against enemy unit and check if buff was received
        await self.clean_up_center()
        await self.clean_up_center()

        map_center = self.game_info.map_center

        while not self.units(UnitTypeId.RAVEN):
            await self.client.debug_create_unit([[UnitTypeId.RAVEN, 1, map_center, 1]])
            await self._advance_steps(2)

        while not self.enemy_units(UnitTypeId.INFESTOR):
            await self.client.debug_create_unit([[UnitTypeId.INFESTOR, 1, map_center, 2]])
            await self._advance_steps(2)

        raven = self.units(UnitTypeId.RAVEN)[0]
        # Set raven energy to max
        await self.client.debug_set_unit_value(raven, 1, 200)
        await self._advance_steps(4)

        enemy = self.enemy_units(UnitTypeId.INFESTOR)[0]
        while 1:
            raven = self.units(UnitTypeId.RAVEN)[0]
            raven(AbilityId.EFFECT_ANTIARMORMISSILE, enemy)
            await self._advance_steps(2)
            enemy = self.enemy_units(UnitTypeId.INFESTOR)[0]
            if enemy.buffs:
                # logger.info(enemy.buffs, enemy.buff_duration_remain, enemy.buff_duration_max)
                break

        logger.warning("Action test 11 successful.")
        await self.clean_up_center()

    async def test_botai_actions12(self):
        # Test if structures_without_construction_SCVs works after killing the scv
        # Wait till can afford depot
        while not self.can_afford(UnitTypeId.SUPPLYDEPOT):
            await self.client.debug_all_resources()
            await self._advance_steps(2)

        while 1:
            # Once depot is under construction: debug kill scv -> advance simulation: should now match the test case
            if self.structures(UnitTypeId.SUPPLYDEPOT).not_ready.amount == 1:
                construction_scvs: Units = self.workers.filter(lambda worker: worker.is_constructing_scv)
                if construction_scvs:
                    await self.client.debug_kill_unit(construction_scvs)
                    await self._advance_steps(8)
                    await self._advance_steps(8)

                    # Test case
                    assert not self.workers.filter(lambda worker: worker.is_constructing_scv)
                    assert self.structures_without_construction_SCVs.amount >= 1
                    break

            if not self.already_pending(UnitTypeId.SUPPLYDEPOT):
                # Pick scv
                scv: Unit = self.workers.random
                # Pick location to build depot on
                placement_position: Point2 = await self.find_placement(
                    UnitTypeId.SUPPLYDEPOT, near=self.townhalls.random.position
                )
                if placement_position:
                    scv.build(UnitTypeId.SUPPLYDEPOT, placement_position)
            await self._advance_steps(2)

        logger.warning("Action test 12 successful.")
        await self.clean_up_center()

    # TODO:
    # self.can_cast function
    # Test client.py debug functions
    # Test if events work (upgrade complete, unit complete, building complete, building started)
    # Test if functions with various combinations works (e.g. already_pending)
    # Test self.train function on: larva, hatchery + lair (queens), 2 barracks (2 marines), 2 nexus (probes) (best: every building)
    # Test unit range and (base attack damage) and other unit stats (e.g. acceleration, deceleration, movement speed (on, off creep), turn speed
    # Test if dicts are correct for unit_trained_from.py -> train all units once


class EmptyBot(BotAI):

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
                unit.move(enemies.closest_to(unit).position)
        else:
            # If attacker is invisible: dont move
            for unit in self.units:
                unit.hold_position()


def main():
    run_game(maps.get("Acropolis"), [Bot(Race.Terran, TestBot()), Bot(Race.Zerg, EmptyBot())], realtime=False)


if __name__ == "__main__":
    main()
