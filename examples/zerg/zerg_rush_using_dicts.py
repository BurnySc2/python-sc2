import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units


class ZergRushBot(sc2.BotAI):
    def __init__(self):
        pass

    async def on_start(self):
        self._client.game_step = 2

    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

        if not self.townhalls:
            for unit in self.units.exclude_type({UnitTypeId.EGG, UnitTypeId.LARVA}):
                self.do(unit.attack(self.enemy_start_locations[0]))
            return

        hatch: Unit = self.townhalls[0]

        target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position

        for zl in self.units(UnitTypeId.ZERGLING):
            self.do(zl.attack(target))

        # Inject hatchery if queen has more than 25 energy
        for queen in self.units(UnitTypeId.QUEEN):
            if queen.energy >= 25 and not hatch.has_buff(BuffId.QUEENSPAWNLARVATIMER):
                self.do(queen(AbilityId.EFFECT_INJECTLARVA, hatch))

        if self.vespene >= 88 or self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) > 0:
            gas_drones = self.workers.filter(lambda w: w.is_carrying_vespene and len(w.orders) < 2)
            drone: Unit
            for drone in gas_drones:
                minerals: Units = self.mineral_field.closer_than(10, hatch)
                mineral = minerals.closest_to(drone)
                self.do(drone.gather(mineral, queue=True))

        if self.vespene >= 100:
            sp = self.structures(UnitTypeId.SPAWNINGPOOL).ready
            if sp and self.minerals >= 100 and self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0:
                self.do(sp.first.research(UpgradeId.ZERGLINGMOVEMENTSPEED))

        if self.supply_left < 2 and self.already_pending(UnitTypeId.OVERLORD) < 1:
            self.train(UnitTypeId.OVERLORD, 1)

        if (
            self.gas_buildings.ready
            and self.vespene < 88
            and self.already_pending_upgrade(UpgradeId.ZERGLINGMOVEMENTSPEED) == 0
        ):
            extractor: Unit = self.gas_buildings.first
            if extractor.surplus_harvesters < 0:
                self.do(self.workers.random.gather(extractor))

        if self.minerals > 500:
            for d in range(4, 15):
                pos = hatch.position.towards(self.game_info.map_center, d)
                if await self.can_place(UnitTypeId.HATCHERY, pos):
                    self.do(self.workers.random.build(UnitTypeId.HATCHERY, pos), subtract_cost=True)
                    break

        if self.can_afford(UnitTypeId.DRONE) and self.supply_workers < 16:
            self.train(UnitTypeId.DRONE)

        if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.larva and self.can_afford(UnitTypeId.ZERGLING):
            amount_trained = self.train(UnitTypeId.ZERGLING, self.larva.amount)

        if self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) == 0 and self.can_afford(
            UnitTypeId.EXTRACTOR
        ):
            drone = self.workers.random
            target = self.vespene_geyser.closest_to(drone)
            self.do(drone.build(UnitTypeId.EXTRACTOR, target))

        elif self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
            if self.can_afford(UnitTypeId.SPAWNINGPOOL):
                for d in range(4, 15):
                    pos = hatch.position.towards(self.game_info.map_center, d)
                    if await self.can_place(UnitTypeId.SPAWNINGPOOL, pos):
                        drone = self.workers.closest_to(pos)
                        self.do(drone.build(UnitTypeId.SPAWNINGPOOL, pos))

        elif (
            self.units(UnitTypeId.QUEEN).amount + self.already_pending(UnitTypeId.QUEEN) == 0
            and self.structures(UnitTypeId.SPAWNINGPOOL).ready
        ):
            if self.can_afford(UnitTypeId.QUEEN):
                self.train(UnitTypeId.QUEEN)


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Zerg, ZergRushBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
