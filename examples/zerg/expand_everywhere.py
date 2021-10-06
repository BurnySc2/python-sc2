import os
import sys
from contextlib import suppress

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.main import run_game

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import random
from typing import Set

from sc2.ids.unit_typeid import UnitTypeId
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit


class ExpandEverywhere(BotAI):
    async def on_start(self):
        self.client.game_step = 50
        await self.client.debug_show_map()

    async def on_step(self, iteration):
        # Build overlords if about to be supply blocked
        if (
            self.supply_left < 2 and self.supply_cap < 200 and self.already_pending(UnitTypeId.OVERLORD) < 2
            and self.can_afford(UnitTypeId.OVERLORD)
        ):
            self.train(UnitTypeId.OVERLORD)

        # While we have less than 16 drones, make more drones
        if (
            self.can_afford(UnitTypeId.DRONE)
            and self.supply_workers - self.worker_en_route_to_build(UnitTypeId.HATCHERY) <
            (self.townhalls.amount + self.placeholders(UnitTypeId.HATCHERY).amount) * 16
        ):
            self.train(UnitTypeId.DRONE)

        # Send workers across bases
        await self.distribute_workers()

        # Expand if we have 300 minerals, try to expand if there is one more expansion location available
        with suppress(AssertionError):
            if self.can_afford(UnitTypeId.HATCHERY):
                planned_hatch_locations: Set[Point2] = {placeholder.position for placeholder in self.placeholders}
                my_structure_locations: Set[Point2] = {structure.position for structure in self.structures}
                enemy_structure_locations: Set[Point2] = {structure.position for structure in self.enemy_structures}
                blocked_locations: Set[Point2] = (
                    my_structure_locations | planned_hatch_locations | enemy_structure_locations
                )
                shuffled_expansions = self.expansion_locations_list.copy()
                random.shuffle(shuffled_expansions)
                for exp_pos in shuffled_expansions:
                    if exp_pos in blocked_locations:
                        continue
                    for drone in self.workers.collecting:
                        drone: Unit
                        drone.build(UnitTypeId.HATCHERY, exp_pos)
                        assert False, f"Break out of 2 for loops"

        # Kill all enemy units in vision / sight
        if self.enemy_units:
            await self.client.debug_kill_unit(self.enemy_units)

    async def on_building_construction_complete(self, unit: Unit):
        """ Set rally point of new hatcheries. """
        if unit.type_id == UnitTypeId.HATCHERY and self.mineral_field:
            mf = self.mineral_field.closest_to(unit)
            unit.smart(mf)


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Zerg, ExpandEverywhere()),
         Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
