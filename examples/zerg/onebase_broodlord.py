import random

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class BroodlordBot(BotAI):

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    # pylint: disable=R0912
    async def on_step(self, iteration):
        larvae: Units = self.larva
        forces: Units = self.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.CORRUPTOR, UnitTypeId.BROODLORD})

        if self.units(UnitTypeId.BROODLORD).amount > 2 and iteration % 50 == 0:
            for unit in forces:
                unit.attack(self.select_target())

        if self.supply_left < 2:
            if larvae and self.can_afford(UnitTypeId.OVERLORD):
                larvae.random.train(UnitTypeId.OVERLORD)
                return

        if self.structures(UnitTypeId.GREATERSPIRE).ready:
            corruptors: Units = self.units(UnitTypeId.CORRUPTOR)
            # build half-and-half corruptors and broodlords
            if corruptors and corruptors.amount > self.units(UnitTypeId.BROODLORD).amount:
                if self.can_afford(UnitTypeId.BROODLORD):
                    corruptors.random.train(UnitTypeId.BROODLORD)
            elif larvae and self.can_afford(UnitTypeId.CORRUPTOR):
                larvae.random.train(UnitTypeId.CORRUPTOR)
                return

        # Send all units to attack if we dont have any more townhalls
        if not self.townhalls:
            all_attack_units: Units = self.units.of_type(
                {UnitTypeId.DRONE, UnitTypeId.QUEEN, UnitTypeId.ZERGLING, UnitTypeId.CORRUPTOR, UnitTypeId.BROODLORD}
            )
            for unit in all_attack_units:
                unit.attack(self.enemy_start_locations[0])
            return

        hq: Unit = self.townhalls.first

        # Make idle queens inject
        for queen in self.units(UnitTypeId.QUEEN).idle:
            if queen.energy >= 25:
                queen(AbilityId.EFFECT_INJECTLARVA, hq)

        # Build pool
        if self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
            if self.can_afford(UnitTypeId.SPAWNINGPOOL):
                await self.build(UnitTypeId.SPAWNINGPOOL, near=hq)

        # Upgrade to lair
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if not self.townhalls(UnitTypeId.LAIR) and not self.townhalls(UnitTypeId.HIVE) and hq.is_idle:
                if self.can_afford(UnitTypeId.LAIR):
                    hq.build(UnitTypeId.LAIR)

        # Build infestation pit
        if self.townhalls(UnitTypeId.LAIR).ready:
            if self.structures(UnitTypeId.INFESTATIONPIT).amount + self.already_pending(UnitTypeId.INFESTATIONPIT) == 0:
                if self.can_afford(UnitTypeId.INFESTATIONPIT):
                    await self.build(UnitTypeId.INFESTATIONPIT, near=hq)

            # Build spire
            if self.structures(UnitTypeId.SPIRE).amount + self.already_pending(UnitTypeId.SPIRE) == 0:
                if self.can_afford(UnitTypeId.SPIRE):
                    await self.build(UnitTypeId.SPIRE, near=hq)

        # Upgrade to hive
        if self.structures(UnitTypeId.INFESTATIONPIT).ready and not self.townhalls(UnitTypeId.HIVE) and hq.is_idle:
            if self.can_afford(UnitTypeId.HIVE):
                hq.build(UnitTypeId.HIVE)

        # Upgrade to greater spire
        if self.townhalls(UnitTypeId.HIVE).ready:
            spires: Units = self.structures(UnitTypeId.SPIRE).ready
            if spires:
                spire: Unit = spires.random
                if self.can_afford(UnitTypeId.GREATERSPIRE) and spire.is_idle:
                    spire.build(UnitTypeId.GREATERSPIRE)

        # Build extractor
        if self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) < 2:
            if self.can_afford(UnitTypeId.EXTRACTOR):
                drone: Unit = self.workers.random
                target: Unit = self.vespene_geyser.closest_to(drone.position)
                drone.build_gas(target)

        # Build up to 22 drones
        if self.supply_workers + self.already_pending(UnitTypeId.DRONE) < 22:
            if larvae and self.can_afford(UnitTypeId.DRONE):
                larva: Unit = larvae.random
                larva.train(UnitTypeId.DRONE)
                return

        # Saturate gas
        for extractor in self.gas_buildings:
            if extractor.assigned_harvesters < extractor.ideal_harvesters:
                workers: Units = self.workers.closer_than(20, extractor)
                if workers:
                    workers.random.gather(extractor)

        # Build queen
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if not self.units(UnitTypeId.QUEEN) and hq.is_idle:
                if self.can_afford(UnitTypeId.QUEEN):
                    hq.train(UnitTypeId.QUEEN)

        # Build zerglings if we have not enough gas to build corruptors and broodlords
        if self.units(UnitTypeId.ZERGLING).amount < 40 and self.minerals > 1000:
            if larvae and self.can_afford(UnitTypeId.ZERGLING):
                larvae.random.train(UnitTypeId.ZERGLING)


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Zerg, BroodlordBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
