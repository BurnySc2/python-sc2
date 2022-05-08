from loguru import logger

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.buff_id import BuffId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.main import run_game
from sc2.player import Bot, Computer


# pylint: disable=W0231
class WarpGateBot(BotAI):

    def __init__(self):
        # Initialize inherited class
        self.proxy_built = False

    async def warp_new_units(self, proxy):
        for warpgate in self.structures(UnitTypeId.WARPGATE).ready:
            abilities = await self.get_available_abilities(warpgate)
            # all the units have the same cooldown anyway so let's just look at ZEALOT
            if AbilityId.WARPGATETRAIN_STALKER in abilities:
                pos = proxy.position.to2.random_on_distance(4)
                placement = await self.find_placement(AbilityId.WARPGATETRAIN_STALKER, pos, placement_step=1)
                if placement is None:
                    # return ActionResult.CantFindPlacementLocation
                    logger.info("can't place")
                    return
                warpgate.warp_in(UnitTypeId.STALKER, placement)

    # pylint: disable=R0912
    async def on_step(self, iteration):
        await self.distribute_workers()

        if not self.townhalls.ready:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                worker.attack(self.enemy_start_locations[0])
            return

        nexus = self.townhalls.ready.random

        # Build pylon when on low supply
        if self.supply_left < 2 and self.already_pending(UnitTypeId.PYLON) == 0:
            # Always check if you can afford something before you build it
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus)
            return

        if self.workers.amount < self.townhalls.amount * 22 and nexus.is_idle:
            if self.can_afford(UnitTypeId.PROBE):
                nexus.train(UnitTypeId.PROBE)

        elif self.structures(UnitTypeId.PYLON).amount < 5 and self.already_pending(UnitTypeId.PYLON) == 0:
            if self.can_afford(UnitTypeId.PYLON):
                await self.build(UnitTypeId.PYLON, near=nexus.position.towards(self.game_info.map_center, 5))

        proxy = None
        if self.structures(UnitTypeId.PYLON).ready:
            proxy = self.structures(UnitTypeId.PYLON).closest_to(self.enemy_start_locations[0])
            pylon = self.structures(UnitTypeId.PYLON).ready.random
            if self.structures(UnitTypeId.GATEWAY).ready:
                # If we have no cyber core, build one
                if not self.structures(UnitTypeId.CYBERNETICSCORE):
                    if (
                        self.can_afford(UnitTypeId.CYBERNETICSCORE)
                        and self.already_pending(UnitTypeId.CYBERNETICSCORE) == 0
                    ):
                        await self.build(UnitTypeId.CYBERNETICSCORE, near=pylon)
            # Build up to 4 gates
            if (
                self.can_afford(UnitTypeId.GATEWAY)
                and self.structures(UnitTypeId.WARPGATE).amount + self.structures(UnitTypeId.GATEWAY).amount < 4
            ):
                await self.build(UnitTypeId.GATEWAY, near=pylon)

        # Build gas
        for nexus in self.townhalls.ready:
            vgs = self.vespene_geyser.closer_than(15, nexus)
            for vg in vgs:
                if not self.can_afford(UnitTypeId.ASSIMILATOR):
                    break
                worker = self.select_build_worker(vg.position)
                if worker is None:
                    break
                if not self.gas_buildings or not self.gas_buildings.closer_than(1, vg):
                    worker.build_gas(vg)
                    worker.stop(queue=True)

        # Research warp gate if cybercore is completed
        if (
            self.structures(UnitTypeId.CYBERNETICSCORE).ready and self.can_afford(AbilityId.RESEARCH_WARPGATE)
            and self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 0
        ):
            ccore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            ccore.research(UpgradeId.WARPGATERESEARCH)

        # Morph to warp gate when research is complete
        for gateway in self.structures(UnitTypeId.GATEWAY).ready.idle:
            if self.already_pending_upgrade(UpgradeId.WARPGATERESEARCH) == 1:
                gateway(AbilityId.MORPH_WARPGATE)

        if self.proxy_built and proxy:
            await self.warp_new_units(proxy)

        # Make stalkers attack either closest enemy unit or enemy spawn location
        if self.units(UnitTypeId.STALKER).amount > 3:
            for stalker in self.units(UnitTypeId.STALKER).ready.idle:
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(stalker)
                    stalker.attack(target)
                else:
                    stalker.attack(self.enemy_start_locations[0])

        # Build proxy pylon
        if (
            self.structures(UnitTypeId.CYBERNETICSCORE).amount >= 1 and not self.proxy_built
            and self.can_afford(UnitTypeId.PYLON)
        ):
            p = self.game_info.map_center.towards(self.enemy_start_locations[0], 20)
            await self.build(UnitTypeId.PYLON, near=p)
            self.proxy_built = True

        # Chrono nexus if cybercore is not ready, else chrono cybercore
        if not self.structures(UnitTypeId.CYBERNETICSCORE).ready:
            if not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not nexus.is_idle:
                if nexus.energy >= 50:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus)
        else:
            ccore = self.structures(UnitTypeId.CYBERNETICSCORE).ready.first
            if not ccore.has_buff(BuffId.CHRONOBOOSTENERGYCOST) and not ccore.is_idle:
                if nexus.energy >= 50:
                    nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, ccore)


def main():
    run_game(
        maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, WarpGateBot()), Computer(Race.Protoss, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
