import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

class WarpGateBot(sc2.BotAI):

    def __init__(self):
        self.warpgate_started = False
        self.proxy_built = False

    def select_target(self, state):
        return self.enemy_start_locations[0]

    async def warp_new_units(self, proxy):
        for warpgate in self.structures(WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if AbilityId.WARPGATETRAIN_ZEALOT in abilities:
                pos = proxy.position.to2.random_on_distance(4)
                placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
                if placement is None:
                    #return ActionResult.CantFindPlacementLocation
                    print("can't place")
                    return
                await self.do(warpgate.warp_in(STALKER, placement))


    async def on_step(self, iteration):
        await self.distribute_workers()

        if not self.townhalls.ready.exists:
            for worker in self.workers:
                await self.do(worker.attack(self.enemy_start_locations[0]))
            return
        else:
            nexus = self.townhalls.ready.random

        if self.supply_left < 2 and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus)
            return

        if self.workers.amount < self.townhalls.amount*22 and nexus.is_idle:
            if self.can_afford(PROBE):
                await self.do(nexus.train(PROBE))

        elif self.structures(PYLON).amount < 5 and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 5))


        if self.structures(PYLON).ready.exists:
            proxy = self.structures(PYLON).closest_to(self.enemy_start_locations[0])
            pylon = self.structures(PYLON).ready.random
            if self.structures(GATEWAY).ready.exists:
                if not self.structures(CYBERNETICSCORE).exists:
                    if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                        await self.build(CYBERNETICSCORE, near=pylon)
            if self.can_afford(GATEWAY) and self.structures(WARPGATE).amount < 4 and self.structures(GATEWAY).amount < 4:
                await self.build(GATEWAY, near=pylon)

        for nexus in self.townhalls.ready:
            vgs = self.state.vespene_geyser.closer_than(20.0, nexus)
            for vg in vgs:
                if not self.can_afford(ASSIMILATOR):
                    break

                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break

                if not self.gas_buildings.closer_than(1.0, vg).exists:
                    await self.do(worker.build(ASSIMILATOR, vg))

        if self.structures(CYBERNETICSCORE).ready.exists and self.can_afford(RESEARCH_WARPGATE) and not self.warpgate_started:
            ccore = self.structures(CYBERNETICSCORE).ready.first
            await self.do(ccore(RESEARCH_WARPGATE))
            self.warpgate_started = True

        for gateway in self.structures(GATEWAY).ready:
            abilities = await self.get_available_abilities(gateway)
            if AbilityId.MORPH_WARPGATE in abilities and self.can_afford(AbilityId.MORPH_WARPGATE):
                await self.do(gateway(MORPH_WARPGATE))

        if self.proxy_built:
            await self.warp_new_units(proxy)

        if self.units(STALKER).amount > 3:
            for vr in self.units(STALKER).ready.idle:
                await self.do(vr.attack(self.select_target(self.state)))

        if self.structures(CYBERNETICSCORE).amount >= 1 and not self.proxy_built and self.can_afford(PYLON):
            p = self.game_info.map_center.towards(self.enemy_start_locations[0], 20)
            await self.build(PYLON, near=p)
            self.proxy_built = True

        if not self.structures(CYBERNETICSCORE).ready.exists:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                abilities = await self.get_available_abilities(nexus)
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                    await self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
        else:
            ccore = self.structures(CYBERNETICSCORE).ready.first
            if not ccore.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
                abilities = await self.get_available_abilities(nexus)
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities:
                    await self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, ccore))


def main():
    sc2.run_game(sc2.maps.get("(2)CatalystLE"), [
        Bot(Race.Protoss, WarpGateBot()),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=False)

if __name__ == '__main__':
    main()
