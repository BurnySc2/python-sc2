"""
This bot tests if on 'realtime=True' any nexus has more than 1 probe in the queue.
"""
import os
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
import asyncio

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race, Result
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.unit import Unit

on_end_was_called: bool = False


class RealTimeTestBot(BotAI):
    async def on_before_start(self):
        mf = self.mineral_field
        for w in self.workers:
            w.gather(mf.closest_to(w))

        # for nexus in self.townhalls:
        #     nexus.train(UnitTypeId.PROBE)

        await self._do_actions(self.actions)
        self.actions.clear()
        await asyncio.sleep(1)

    async def on_start(self):
        """ This function is run after the expansion locations and ramps are calculated. """
        self.client.game_step = 1

    async def on_step(self, iteration):
        # assert (
        #     self.supply_left <= 15
        # ), f"Bot created 2 nexus in one step. Supply: {self.supply_used} / {self.supply_cap}"

        # Simulate that the bot takes too long in one iteration, sometimes
        if iteration % 20 != 0:
            await asyncio.sleep(0.1)

        # Queue probes
        for nexus in self.townhalls:
            nexus_orders_amount = len(nexus.orders)
            assert nexus_orders_amount <= 1, f"{nexus_orders_amount}"
            # print(f"{self.time_formatted} {self.state.game_loop} {nexus} orders: {nexus_orders_amount}")
            if nexus.is_idle and self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)
                print(
                    f"{self.time_formatted} {self.state.game_loop} Training probe {self.supply_used} / {self.supply_cap}"
                )
            # Chrono
            if nexus.energy >= 50:
                nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)

        # Spawn nexus at expansion location that is not used
        made_nexus = False
        if self.supply_left == 0:
            for expansion_location in self.expansion_locations_list:
                if self.townhalls.closer_than(10, expansion_location):
                    continue
                if self.enemy_structures.closer_than(10, expansion_location):
                    continue
                await self.client.debug_create_unit([[UnitTypeId.NEXUS, 1, expansion_location, 1]])
                print(
                    f"{self.time_formatted} {self.state.game_loop} Spawning a nexus {self.supply_used} / {self.supply_cap}"
                )
                made_nexus = True
                break

        # Spawn new pylon in map center if no more expansions are available
        if self.supply_left == 0 and not made_nexus:
            await self.client.debug_create_unit([[UnitTypeId.PYLON, 1, self.game_info.map_center, 1]])

        # Don't get disturbed during this test
        if self.enemy_units:
            await self.client.debug_kill_unit(self.enemy_units)

        if self.supply_used >= 199 or self.time > 7 * 60:
            print("Test successful, bot reached 199 supply without queueing two probes at once")
            await self.client.leave()

    async def on_building_construction_complete(self, unit: Unit):
        # Set worker rally point
        if unit.is_structure:
            unit(AbilityId.RALLY_WORKERS, self.mineral_field.closest_to(unit))

    async def on_end(self, game_result: Result):
        global on_end_was_called
        on_end_was_called = True
        print(f"on_end() was called with result: {game_result}")


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Protoss, RealTimeTestBot()),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=True,
        disable_fog=True,
    )
    assert on_end_was_called, f"{on_end_was_called}"


if __name__ == "__main__":
    main()
