import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.player import Human


class BCRushBot(sc2.BotAI):
    def select_target(self):
        target = self.known_enemy_structures
        if target.exists:
            return target.random.position

        target = self.known_enemy_units
        if target.exists:
            return target.random.position

        if min([u.position.distance_to(self.enemy_start_locations[0]) for u in self.units]) < 5:
            return self.enemy_start_locations[0].position

        return self.mineral_field.random.position

    async def on_step(self, iteration):
        cc = self.townhalls(COMMANDCENTER) | self.townhalls(ORBITALCOMMAND)
        if not cc.exists:
            target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(BATTLECRUISER):
                self.do(unit.attack(target))
            return
        else:
            cc = cc.first

        if iteration % 50 == 0 and self.units(BATTLECRUISER).amount > 2:
            target = self.select_target()
            forces = self.units(BATTLECRUISER)
            if (iteration // 50) % 10 == 0:
                for unit in forces:
                    self.do(unit.attack(target))
            else:
                for unit in forces.idle:
                    self.do(unit.attack(target))

        if self.can_afford(SCV) and self.workers.amount < 22 and cc.is_idle:
            self.do(cc.train(SCV))

        if self.structures(FUSIONCORE).exists and self.can_afford(BATTLECRUISER):
            for sp in self.structures(STARPORT):
                if sp.has_add_on and sp.is_idle:
                    if not self.can_afford(BATTLECRUISER):
                        break
                    self.do(sp.train(BATTLECRUISER))

        elif self.supply_left < 3:
            if self.can_afford(SUPPLYDEPOT):
                await self.build(SUPPLYDEPOT, near=cc.position.towards(self.game_info.map_center, 8))

        if self.structures(SUPPLYDEPOT).exists:
            if not self.structures(BARRACKS).exists:
                if self.can_afford(BARRACKS):
                    await self.build(BARRACKS, near=cc.position.towards(self.game_info.map_center, 8))

            elif self.structures(BARRACKS).exists and self.gas_buildings.amount < 2:
                if self.can_afford(REFINERY):
                    vgs = self.vespene_geyser.closer_than(20.0, cc)
                    for vg in vgs:
                        if self.gas_buildings.filter(lambda unit: unit.distance_to(vg) < 1):
                            break

                        worker = self.select_build_worker(vg.position)
                        if worker is None:
                            break

                        self.do(worker.build(REFINERY, vg))
                        break

            if self.structures(BARRACKS).ready.exists:
                f = self.structures(FACTORY)
                if not f.exists:
                    if self.can_afford(FACTORY):
                        await self.build(FACTORY, near=cc.position.towards(self.game_info.map_center, 8))
                elif f.ready.exists and self.structures(STARPORT).amount < 2:
                    if self.can_afford(STARPORT):
                        await self.build(
                            STARPORT, near=cc.position.towards(self.game_info.map_center, 30).random_on_distance(8)
                        )

        for sp in self.structures(STARPORT).ready:
            if sp.add_on_tag == 0:
                self.do(sp.build(STARPORTTECHLAB))

        if self.structures(STARPORT).ready.exists:
            if self.can_afford(FUSIONCORE) and not self.structures(FUSIONCORE).exists:
                await self.build(FUSIONCORE, near=cc.position.towards(self.game_info.map_center, 8))

        for a in self.gas_buildings:
            if a.assigned_harvesters < a.ideal_harvesters:
                w = self.workers.closer_than(20, a)
                if w.exists:
                    self.do(w.random.gather(a))

        for scv in self.workers.idle:
            self.do(scv.gather(self.mineral_field.closest_to(cc)))


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [
            # Human(Race.Terran),
            Bot(Race.Terran, BCRushBot()),
            Computer(Race.Zerg, Difficulty.Hard),
        ],
        realtime=False,
    )


if __name__ == "__main__":
    main()
