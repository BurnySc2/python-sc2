import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.ids.buff_id import BuffId
from sc2.player import Bot, Computer


class ThreebaseVoidrayBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(glhf)")

        if not self.townhalls.ready:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))
            return
        else:
            nexus = self.townhalls.ready.random

        # If this random nexus is not idle and has not chrono buff, chrono it with one of the nexuses we have
        if not nexus.is_idle and not nexus.has_buff(BuffId.CHRONOBOOSTENERGYCOST):
            nexuses = self.structures(NEXUS)
            abilities = await self.get_available_abilities(nexuses)
            for loop_nexus, abilities_nexus in zip(nexuses, abilities):
                if AbilityId.EFFECT_CHRONOBOOSTENERGYCOST in abilities_nexus:
                    self.do(loop_nexus(AbilityId.EFFECT_CHRONOBOOSTENERGYCOST, nexus))
                    break

        # If we have at least 5 void rays, attack closes enemy unit/building, or if none is visible: attack move towards enemy spawn
        if self.units(VOIDRAY).amount > 5:
            for vr in self.units(VOIDRAY):
                # Activate charge ability if the void ray just attacked
                if vr.weapon_cooldown > 0:
                    self.do(vr(AbilityId.EFFECT_VOIDRAYPRISMATICALIGNMENT))
                # Choose target and attack, filter out invisible targets
                targets = (self.enemy_units | self.enemy_structures).filter(lambda unit: unit.can_be_attacked)
                if targets:
                    target = targets.closest_to(vr)
                    self.do(vr.attack(target))
                else:
                    self.do(vr.attack(self.enemy_start_locations[0]))

        # Distribute workers in gas and across bases
        await self.distribute_workers()

        # If we are low on supply, build pylon
        if (
            self.supply_left < 2
            and self.already_pending(PYLON) == 0
            or self.supply_used > 15
            and self.supply_left < 4
            and self.already_pending(PYLON) < 2
        ):
            # Always check if you can afford something before you build it
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus)

        # Train probe on nexuses that are undersaturated (avoiding distribute workers functions)
        # if nexus.assigned_harvesters < nexus.ideal_harvesters and nexus.is_idle:
        if self.supply_workers + self.already_pending(PROBE) < self.townhalls.amount * 22 and nexus.is_idle:
            if self.can_afford(PROBE):
                self.do(nexus.train(PROBE), subtract_cost=True, subtract_supply=True)

        # If we have less than 3 nexuses and none pending yet, expand
        if self.townhalls.ready.amount + self.already_pending(NEXUS) < 3:
            if self.can_afford(NEXUS):
                await self.expand_now()

        # Once we have a pylon completed
        if self.structures(PYLON).ready:
            pylon = self.structures(PYLON).ready.random
            if self.structures(GATEWAY).ready:
                # If we have gateway completed, build cyber core
                if not self.structures(CYBERNETICSCORE):
                    if self.can_afford(CYBERNETICSCORE) and self.already_pending(CYBERNETICSCORE) == 0:
                        await self.build(CYBERNETICSCORE, near=pylon)
            else:
                # If we have no gateway, build gateway
                if self.can_afford(GATEWAY) and self.already_pending(GATEWAY) == 0:
                    await self.build(GATEWAY, near=pylon)

        # Build gas near completed nexuses once we have a cybercore (does not need to be completed
        if self.structures(CYBERNETICSCORE):
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

        # If we have less than 3  but at least 3 nexuses, build stargate
        if self.structures(PYLON).ready and self.structures(CYBERNETICSCORE).ready:
            pylon = self.structures(PYLON).ready.random
            if (
                self.townhalls.ready.amount + self.already_pending(NEXUS) >= 3
                and self.structures(STARGATE).ready.amount + self.already_pending(STARGATE) < 3
            ):
                if self.can_afford(STARGATE):
                    await self.build(STARGATE, near=pylon)

        # Save up for expansions, loop over idle completed stargates and queue void ray if we can afford
        if self.townhalls.amount >= 3:
            for sg in self.structures(STARGATE).ready.idle:
                if self.can_afford(VOIDRAY):
                    self.do(sg.train(VOIDRAY), subtract_cost=True, subtract_supply=True)


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, ThreebaseVoidrayBot()), Computer(Race.Protoss, Difficulty.Easy)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
