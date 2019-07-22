import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.player import Human


class CyclonePush(sc2.BotAI):
    def select_target(self):
        target = self.known_enemy_structures
        if target.exists:
            return target.random.position

        target = self.known_enemy_units
        if target.exists:
            return target.random.position

        if min([u.position.distance_to(self.enemy_start_locations[0]) for u in self.units]) < 5:
            return self.enemy_start_locations[0].position

        return self.state.mineral_field.random.position

    async def on_step(self, iteration):
        cc = self.townhalls(COMMANDCENTER)
        if not cc.exists:
            target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position
            for unit in self.workers | self.units(CYCLONE):
                self.do(unit.attack(target))
            return
        else:
            cc = cc.first

        if iteration % 50 == 0 and self.units(CYCLONE).amount > 2:
            target = self.select_target()
            forces = self.units(CYCLONE)
            if (iteration // 50) % 10 == 0:
                for unit in forces:
                    self.do(unit.attack(target))
            else:
                for unit in forces.idle:
                    self.do(unit.attack(target))

        if self.can_afford(SCV) and self.workers.amount < 22 and cc.is_idle:
            self.do(cc.train(SCV))

        elif self.supply_left < 3:
            if self.can_afford(SUPPLYDEPOT) and self.already_pending(SUPPLYDEPOT) < 2:
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
                if self.structures(FACTORY).amount < 3 and not self.already_pending(FACTORY):
                    if self.can_afford(FACTORY):
                        p = cc.position.towards_with_random_angle(self.game_info.map_center, 16)
                        await self.build(FACTORY, near=p)

        for factory in self.structures(FACTORY).ready.idle:
            # Reactor allows us to build two at a time
            if self.can_afford(CYCLONE):
                self.do(factory.train(CYCLONE))

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
            Bot(Race.Terran, CyclonePush()),
            Computer(Race.Zerg, Difficulty.Easy),
        ],
        realtime=False,
        sc2_version="4.7",
    )


if __name__ == "__main__":
    main()
