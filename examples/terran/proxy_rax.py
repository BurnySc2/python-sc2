import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units
from sc2.position import Point2
from sc2.ids.unit_typeid import UnitTypeId


class ProxyRaxBot(sc2.BotAI):
    def __init__(self):
        self.attack_groups = set()

    async def on_step(self, iteration):

        # If we don't have a townhall anymore, send all units to attack
        ccs: Units = self.townhalls(UnitTypeId.COMMANDCENTER)
        if not ccs:
            target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(UnitTypeId.MARINE):
                self.do(unit.attack(target))
            return
        else:
            cc: Unit = ccs.first

        # Send marines in waves of 15, each time 15 are idle, send them to their death
        marines: Units = self.units(UnitTypeId.MARINE).idle
        if marines.amount > 15:
            target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
            for marine in marines:
                self.do(marine.attack(target))

        # Train more SCVs
        if self.can_afford(UnitTypeId.SCV) and self.supply_workers < 16 and cc.is_idle:
            self.do(cc.train(UnitTypeId.SCV), subtract_supply=True, subtract_cost=True)

        # Build more depots
        elif (
            self.supply_left < (2 if self.structures(UnitTypeId.BARRACKS).amount < 3 else 4) and self.supply_used >= 14
        ):
            if self.can_afford(UnitTypeId.SUPPLYDEPOT) and self.already_pending(UnitTypeId.SUPPLYDEPOT) < 2:
                await self.build(UnitTypeId.SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))

        # Build proxy barracks
        elif self.structures(UnitTypeId.BARRACKS).amount < 3 or (
            self.minerals > 400 and self.structures(UnitTypeId.BARRACKS).amount < 5
        ):
            if self.can_afford(UnitTypeId.BARRACKS):
                p = self.game_info.map_center.towards(self.enemy_start_locations[0], 25)
                await self.build(UnitTypeId.BARRACKS, near=p)

        # Train marines
        for rax in self.structures(UnitTypeId.BARRACKS).ready.idle:
            if self.can_afford(UnitTypeId.MARINE):
                self.do(rax.train(UnitTypeId.MARINE), subtract_supply=True, subtract_cost=True)

        # Send idle workers to gather minerals near command center
        for scv in self.workers.idle:
            self.do(scv.gather(self.mineral_field.closest_to(cc)))


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, ProxyRaxBot()), Computer(Race.Zerg, Difficulty.Hard)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
