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
        self.tests_target = 8
        self.tests_done_by_name = set()

    async def on_start_async(self):
        await self.distribute_workers()

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")
        # Test if chat message was sent correctly
        if iteration == 1:
            assert len(self.state.chat) >= 1, self.state.chat

        # Tests at start:
        if iteration == 5:
            # No need to use try except as the travis test script checks for "Traceback" in STDOUT
            await self.test_botai_properties()
            await self.test_botai_functions()
            await self.test_gamestate_static_variables()
            await self.test_game_info_static_variables()
            await self.test_unit()
            await self.test_units()

        # Test actions:
        if "test_botai_actions1_successful" not in self.tests_done_by_name:
            if iteration >= 6:
                # Test actions
                await self.test_botai_actions1()
                # Test if actions were successful
                await self.test_botai_actions1_successful()

        elif "test_botai_actions2_successful" not in self.tests_done_by_name:
            await self.test_botai_actions2()
            await self.test_botai_actions2_successful()

        elif "test_botai_actions3_successful" not in self.tests_done_by_name:
            await self.test_botai_actions3()
            await self.test_botai_actions3_successful()

        elif "test_botai_actions4_successful" not in self.tests_done_by_name:
            await self.test_botai_actions4()
            await self.test_botai_actions4_successful()

        # elif "test_botai_actions5_successful" not in self.tests_done_by_name:
        #    await self.test_botai_actions5()
        #    await self.test_botai_actions5_successful()

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
                "{}/{} Tests completed: {}".format(
                    len(self.tests_done_by_name), self.tests_target, self.tests_done_by_name
                )
            )
            print("Not all tests were successful. Timeout reached. Testing was aborted")
            exit(1000)

        """
        TODO BotAI tests:
        distribute workers, owned expansions, can cast, select build worker, can place, find placement, self build
        """

    # Test BotAI properties
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
        assert self.known_enemy_units.amount == 0, self.known_enemy_units
        assert self.known_enemy_structures.amount == 0, self.known_enemy_structures
        assert self.known_enemy_structures.amount <= self.known_enemy_units.amount
        assert self.main_base_ramp.top_center.distance_to(self.start_location) < 30, self.main_base_ramp.top_center
        assert self.can_afford(UnitTypeId.SCV)
        assert self.minerals >= 50, self.minerals
        assert self.vespene == 0, self.vespene
        assert self.supply_used == 12, self.supply_used
        assert self.supply_cap == 15, self.supply_cap
        assert self.supply_left == 3, self.supply_left
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

    # Test BotAI action: train SCV
    async def test_botai_actions1(self):
        if self.can_afford(UnitTypeId.SCV):
            await self.do(self.townhalls.random.train(UnitTypeId.SCV))

    # Test BotAI action: move all SCVs to center of map
    async def test_botai_actions2(self):
        combined_actions = []
        center = self._game_info.map_center
        for scv in self.workers:
            combined_actions.append(scv.move(center))
        await self.do_actions(combined_actions)

    # Test BotAI action: move some scvs to the center, some to minerals
    async def test_botai_actions3(self):
        combined_actions = []
        center = self._game_info.map_center
        scvs = self.workers
        scvs1 = scvs[:6]
        scvs2 = scvs[6:]
        for scv in scvs1:
            combined_actions.append(scv.move(center))
        mf = self.state.mineral_field.closest_to(self.townhalls.random)
        for scv in scvs2:
            combined_actions.append(scv.gather(mf))
        await self.do_actions(combined_actions)

    # Test BotAI action: move all SCVs to mine minerals near townhall
    async def test_botai_actions4(self):
        combined_actions = []
        mf = self.state.mineral_field.closest_to(self.townhalls.random)
        for scv in self.workers:
            combined_actions.append(scv.gather(mf))
        await self.do_actions(combined_actions)

    # Test BotAI action: self.expand_now()
    async def test_botai_actions5(self):
        if self.can_afford(UnitTypeId.COMMANDCENTER) and not self.already_pending(
            UnitTypeId.COMMANDCENTER, all_units=True
        ):
            await self.get_next_expansion()
            await self.expand_now()

    # Test BotAI action results
    async def test_botai_actions1_successful(self):
        if self.already_pending(UnitTypeId.SCV, all_units=True) > 0:
            self.tests_done_by_name.add("test_botai_actions1_successful")

    async def test_botai_actions2_successful(self):
        if self.units.filter(lambda x: x.is_moving).amount >= 12:
            self.tests_done_by_name.add("test_botai_actions2_successful")

    async def test_botai_actions3_successful(self):
        if self.units.filter(lambda x: x.is_moving).amount >= 6:
            if self.units.gathering.amount >= 6:
                self.tests_done_by_name.add("test_botai_actions3_successful")

    async def test_botai_actions4_successful(self):
        if self.units.gathering.amount >= 12:
            self.tests_done_by_name.add("test_botai_actions4_successful")

    async def test_botai_actions5_successful(self):
        if self.townhalls(UnitTypeId.COMMANDCENTER).amount >= 2:
            self.tests_done_by_name.add("test_botai_actions5_successful")

    # Test self.state variables
    async def test_gamestate_static_variables(self):
        assert len(self.state.actions) == 0, self.state.actions
        assert len(self.state.action_errors) == 0, self.state.action_errors
        assert len(self.state.chat) == 0, self.state.chat
        assert self.state.game_loop > 0, self.state.game_loop
        assert self.state.score.collection_rate_minerals >= 0, self.state.score.collection_rate_minerals
        assert len(self.state.destructables) > 0, self.state.destructables
        assert self.state.units.amount > 0, self.state.units
        assert len(self.state.blips) == 0, self.state.blips
        assert len(self.state.upgrades) == 0, self.state.upgrades
        self.tests_done_by_name.add("test_gamestate_static_variables")

    # Test self._game_info variables
    async def test_game_info_static_variables(self):
        assert len(self._game_info.players) == 2, self._game_info.players
        assert len(self._game_info.map_ramps) >= 2, self._game_info.map_ramps
        assert len(self._game_info.player_races) == 2, self._game_info.player_races
        self.tests_done_by_name.add("test_game_info_static_variables")

    # Test unit.py
    async def test_unit(self):
        scv1, scv2, scv3 = self.workers[:3]

        assert scv1.type_id == UnitTypeId.SCV
        assert scv1._type_data == self._game_data.units[UnitTypeId.SCV.value]
        assert scv1.alliance == Alliance.Self.value
        assert scv1.is_mine is True
        assert isinstance(scv1.position, Point2)
        assert isinstance(scv1.position3d, Point3)
        assert scv1.health == 45
        assert scv1.health_max == 45
        assert scv1.health_percentage == 45 / 45
        assert scv1.energy == 0
        assert scv1.energy_max == 0
        assert scv1.energy_percentage == 0
        assert not scv1.target_in_range(self.workers.tags_not_in({scv1.tag}).furthest_to(scv1.position))
        assert scv1.target_in_range(scv1)

    # Test units.py
    async def test_units(self):
        scv1, scv2, scv3 = self.workers[:3]
        scv_group = self.workers.tags_in({scv1.tag, scv2.tag, scv3.tag})
        empty_group = self.workers & []

        assert scv_group.amount == 3
        assert empty_group.amount == 0

        assert not scv_group.empty
        assert empty_group.empty

        assert scv_group.exists
        assert not empty_group.exists

        assert scv_group.find_by_tag(scv1.tag) == scv1
        assert scv_group.find_by_tag(1337) is None

        assert scv_group.random in [scv1, scv2, scv3]

        # Test distances and closest/furthest filters
        test_point = scv1.position.offset(Point2((0.01, 0.01)))
        assert abs(scv_group.closest_distance_to(test_point) - (0.01 ** 2 + 0.01 ** 2) ** 0.5) < 0.01

        assert scv_group.closest_to(test_point) == scv1
        assert scv_group.furthest_to(test_point) != scv1
        assert scv_group.furthest_to(test_point) in [scv2, scv3]

        assert scv_group.closer_than(0.02, test_point) == self.workers.tags_in({scv1.tag})
        assert scv_group.closer_than(30, test_point) == scv_group

        assert scv_group.further_than(0.02, test_point) == self.workers.tags_in({scv2.tag, scv3.tag})

        # Test chained filters
        assert (
            scv_group.closer_than(50, test_point).further_than(0.00001, test_point).of_type(UnitTypeId.SCV) == scv_group
        )

        assert scv_group.of_type({UnitTypeId.SCV}) == scv_group
        assert scv_group.of_type({UnitTypeId.MARINE}) == empty_group

        assert scv_group.tags == {u.tag for u in scv_group}

        assert scv_group.owned == scv_group

        assert scv_group.enemy == empty_group

    # TODO:
    # Test ramp building placement position
    # Test client.py debug functions


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, TestBot()), Computer(Race.Zerg, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
