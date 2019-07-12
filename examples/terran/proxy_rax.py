import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.helpers import ControlGroup


class ProxyRaxBot(sc2.BotAI):
    def __init__(self):
        self.attack_groups = set()

    async def on_step(self, iteration):
        cc = self.townhalls(COMMANDCENTER)
        if not cc.exists:
            target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(MARINE):
                self.do(unit.attack(target))
            return
        else:
            cc = cc.first

        if self.units(MARINE).idle.amount > 15 and iteration % 50 == 1:
            cg = ControlGroup(self.units(MARINE).idle)
            self.attack_groups.add(cg)

        if self.can_afford(SCV) and self.workers.amount < 16 and cc.is_idle:
            self.do(cc.train(SCV))

        elif self.supply_left < (2 if self.structures(BARRACKS).amount < 3 else 4):
            if self.can_afford(SUPPLYDEPOT) and self.already_pending(SUPPLYDEPOT) < 2:
                await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 5))

        elif self.structures(BARRACKS).amount < 3 or (self.minerals > 400 and self.structures(BARRACKS).amount < 5):
            if self.can_afford(BARRACKS):
                p = self.game_info.map_center.towards(self.enemy_start_locations[0], 25)
                await self.build(BARRACKS, near=p)

        for rax in self.structures(BARRACKS).ready.idle:
            if not self.can_afford(MARINE):
                break
            self.do(rax.train(MARINE))

        for scv in self.workers.idle:
            self.do(scv.gather(self.mineral_field.closest_to(cc)))

        for ac in list(self.attack_groups):
            alive_units = ac.select_units(self.units)
            if alive_units.exists and alive_units.idle.exists:
                target = self.enemy_structures.random_or(self.enemy_start_locations[0]).position
                for marine in ac.select_units(self.units):
                    self.do(marine.attack(target))
            else:
                self.attack_groups.remove(ac)


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Terran, ProxyRaxBot()), Computer(Race.Zerg, Difficulty.Hard)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
