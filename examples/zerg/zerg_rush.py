import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import numpy as np
from sc2.position import Point2, Point3

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units


class ZergRushBot(sc2.BotAI):
    async def on_start(self):
        self._client.game_step = 2

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

        # If townhall no longer exists: attack move with all units to enemy start location
        if not self.townhalls:
            for unit in self.units.exclude_type({UnitTypeId.EGG, UnitTypeId.LARVA}):
                self.do(unit.attack(self.enemy_start_locations[0]))
            return

        hatch: Unit = self.townhalls[0]

        # Pick a target location
        target = self.enemy_structures.not_flying.random_or(self.enemy_start_locations[0]).position

        # Give all zerglings an attack command
        for zl in self.units(UnitTypeId.ZERGLING):
            self.do(zl.attack(target))

        # Inject hatchery if queen has more than 25 energy
        for queen in self.units(UnitTypeId.QUEEN):
            if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                self.do(queen(AbilityId.EFFECT_INJECTLARVA, hatch))

        # Pull workers out of gas if we have almost enough gas mined, this will stop mining when we reached 100 gas mined
        if self.vespene >= 88 or self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0:
            gas_drones = self.workers.filter(lambda w: w.is_carrying_vespene and len(w.orders) < 2)
            drone: Unit
            for drone in gas_drones:
                minerals: Units = self.mineral_field.closer_than(10, hatch)
                if minerals:
                    mineral = minerals.closest_to(drone)
                    self.do(drone.gather(mineral, queue=True))

        # If we have 100 vespene, this will try to research zergling speed once the spawning pool is at 100% completion
        if self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0 and self.can_afford(
            UpgradeId.ZERGLINGMOVEMENTSPEED
        ):
            spawning_pools_ready = self.structures(UnitTypeId.SPAWNINGPOOL).ready
            if spawning_pools_ready:
                self.research(UpgradeId.ZERGLINGMOVEMENTSPEED)

        # If we have less than 2 supply left and no overlord is in the queue: train an overlord
        if self.supply_left < 2 and self.already_pending(UnitTypeId.OVERLORD) < 1:
            self.train(UnitTypeId.OVERLORD, 1)

        # While we have less than 88 vespene mined: send drones into extractor one frame at a time
        if (
            self.gas_buildings.ready
            and self.vespene < 88
            and self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0
        ):
            extractor: Unit = self.gas_buildings.first
            if extractor.surplus_harvesters < 0:
                self.do(self.workers.random.gather(extractor))

        # If we have lost of minerals, make a macro hatchery
        if self.minerals > 500:
            for d in range(4, 15):
                pos = hatch.position.towards(self.game_info.map_center, d)
                if await self.can_place(UnitTypeId.HATCHERY, pos):
                    self.do(self.workers.random.build(UnitTypeId.HATCHERY, pos), subtract_cost=True)
                    break

        # While we have less than 16 drones, make more drones
        if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < 16:
            self.train(UnitTypeId.DRONE)

        # If our spawningpool is completed, start making zerglings
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.larva and self.can_afford(UnitTypeId.ZERGLING):
            amount_trained = self.train(UnitTypeId.ZERGLING, self.larva.amount)

        # If we have no extractor, build extractor
        if self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0 and self.can_afford(
            UnitTypeId.EXTRACTOR
        ):
            drone = self.workers.random
            target = self.vespene_geyser.closest_to(drone)
            self.do(drone.build(UnitTypeId.EXTRACTOR, target))

        # If we have no spawning pool, try to build spawning pool
        elif self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
            if self.can_afford(UnitTypeId.SPAWNINGPOOL):
                for d in range(4, 15):
                    pos = hatch.position.towards(self.game_info.map_center, d)
                    if await self.can_place(UnitTypeId.SPAWNINGPOOL, pos):
                        drone = self.workers.closest_to(pos)
                        self.do(drone.build(UnitTypeId.SPAWNINGPOOL, pos))

        # If we have no queen, try to build a queen if we have a spawning pool compelted
        elif (
            self.units(UnitTypeId.QUEEN).amount + self.already_pending(UnitTypeId.QUEEN) == 0
            and self.structures(UnitTypeId.SPAWNINGPOOL).ready
        ):
            if self.can_afford(UnitTypeId.QUEEN):
                self.train(UnitTypeId.QUEEN)

        # Draw creep pixelmap for debugging
        # self.draw_creep_pixelmap()

    def draw_creep_pixelmap(self):
        for (y, x), value in np.ndenumerate(self.state.creep.data_numpy):
            p = Point2((x, y))
            h2 = self.get_terrain_z_height(p)
            pos = Point3((p.x, p.y, h2))
            # Red if there is no creep
            color = Point3((255, 0, 0))
            if value == 1:
                # Green if there is creep
                color = Point3((0, 255, 0))
            self._client.debug_box2_out(pos, half_vertex_length=0.25, color=color)


def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Zerg, ZergRushBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
