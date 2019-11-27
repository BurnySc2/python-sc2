import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class WarpGateBot(sc2.BotAI):
    def __init__(self):
        # Initialize inherited class
        sc2.BotAI.__init__(self)
        self.proxy_built = False

    async def warp_new_units(self, proxy):
        for warpgate in self.structures(WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if AbilityId.WARPGATETRAIN_STALKER in abilities:
                pos = proxy.position.to2.random_on_distance(4)
                placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
                if placement is None:
                    # return ActionResult.CantFindPlacementLocation
                    print("can't place")
                    return
                self.do(warpgate.warp_in(STALKER, placement), subtract_cost=True, subtract_supply=True)

    async def on_step(self, iteration):
        await self.distribute_workers()

        if not self.townhalls.ready:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))
            return
        else:
            nexus = self.townhalls.ready.random

        # Build pylon when on low supply
        if self.supply_left < 2 and self.already_pending(PYLON) == 0:
            # Always check if you can afford something before you build it
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus)
            return

        if self.workers.amount < self.townhalls.amount * 22 and nexus.is_idle:
            if self.can_afford(PROBE):
                self.do(nexus.train(PROBE), subtract_cost=True, subtract_supply=True)

        elif self.structures(PYLON).amount < 5 and self.already_pending(PYLON) == 0:
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus.position.towards(self.game_info.map_center, 5))

        if self.structures(PYLON).ready:
            proxy = self.structures(PYLON).closest_to(self.enemy_start_locations[0])
            pylon = self.structures(PYLON).ready.random
            if self.structures(GATEWAY).ready:
                # If we have no cyber core, build one
                if not self.structures(CYBERNETICSCORE):
                    if self.can_afford(CYBERNETICSCORE) and self.already_pending(CYBERNETICSCORE) == 0:
                        await self.build(CYBERNETICSCORE, near=pylon)
            # Build up to 4 gates
            if self.can_afford(GATEWAY) and self.structures(WARPGATE).amount + self.structures(GATEWAY).amount < 4:
                await self.build(GATEWAY, near=pylon)

        # Build gas
        for nexus in self.townhalls.ready:
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                if not self.can_afford(ASSIMILATOR):
                    break
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break
                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    self.do(worker.build(ASSIMILATOR, vg), subtract_cost=True)
                    self.do(worker.stop(queue=True))

        # Research warp gate if cybercore is completed
        if (
            self.structures(CYBERNETICSCORE).ready
            and self.can_afford(AbilityId.RESEARCH_WARPGATE)
            and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
        ):
            ccore = self.structures(CYBERNETICSCORE).ready.first
            self.do(ccore(RESEARCH_WARPGATE), subtract_cost=True)

        # Morph to warp gate when research is complete
        for gateway in self.structures(GATEWAY).ready.idle:
            if self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1:
                self.do(gateway(MORPH_WARPGATE))

        if self.proxy_built:
            await self.warp_new_units(proxy)

        # Make stalkers attack either closest enemy unit or enemy spawn location
        if self.units(STALKER).amount > 3:
            for stalker in self.units(STALKER).ready.idle:
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(stalker)
                    self.do(stalker.attack(target))
                else:
                    self.do(stalker.attack(self.enemy_start_locations[0]))

        # Build proxy pylon
        if self.structures(CYBERNETICSCORE).amount >= 1 and not self.proxy_built and self.can_afford(PYLON):
            p = self.game_info.map_center.towards(self.enemy_start_locations[0], 20)
            await self.build(PYLON, near=p)
            self.proxy_built = True

        # Chrono nexus if cybercore is not ready, else chrono cybercore
        if not self.structures(CYBERNETICSCORE).ready:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not nexus.is_idle:
                if nexus.energy >= 50:
                    self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
        else:
            ccore = self.structures(CYBERNETICSCORE).ready.first
            if not ccore.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not ccore.is_idle:
                if nexus.energy >= 50:
                    self.do(nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, ccore))


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, WarpGateBot()), Computer(Race.Protoss, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
