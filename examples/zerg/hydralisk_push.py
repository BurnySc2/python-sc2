import random

from sc2 import maps
from sc2.bot_ai import BotAI
from sc2.data import Difficulty, Race
from sc2.ids.ability_id import AbilityId
from sc2.ids.unit_typeid import UnitTypeId
from sc2.ids.upgrade_id import UpgradeId
from sc2.main import run_game
from sc2.player import Bot, Computer
from sc2.position import Point2
from sc2.unit import Unit
from sc2.units import Units


class Hydralisk(BotAI):

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    # pylint: disable=R0912
    async def on_step(self, iteration):
        larvae: Units = self.larva
        forces: Units = self.units.of_type({UnitTypeId.ZERGLING, UnitTypeId.HYDRALISK})

        # Send all idle lings + hydras to attack-move if we have at least 10 hydras, every 400th frame
        if self.units(UnitTypeId.HYDRALISK).amount >= 10 and iteration % 50 == 0:
            for unit in forces.idle:
                unit.attack(self.select_target())

        # If supply is low, train overlords
        if self.supply_left < 2 and larvae and self.can_afford(UnitTypeId.OVERLORD):
            larvae.random.train(UnitTypeId.OVERLORD)
            return

        # If hydra den is ready and idle, research upgrades
        hydra_dens = self.structures(UnitTypeId.HYDRALISKDEN)
        if hydra_dens:
            for hydra_den in hydra_dens.ready.idle:
                if self.already_pending_upgrade(UpgradeId.EVOLVEGROOVEDSPINES
                                                ) == 0 and self.can_afford(UpgradeId.EVOLVEGROOVEDSPINES):
                    hydra_den.research(UpgradeId.EVOLVEGROOVEDSPINES)
                elif self.already_pending_upgrade(UpgradeId.EVOLVEMUSCULARAUGMENTS
                                                  ) == 0 and self.can_afford(UpgradeId.EVOLVEMUSCULARAUGMENTS):
                    hydra_den.research(UpgradeId.EVOLVEMUSCULARAUGMENTS)

        # If hydra den is ready, train hydra
        if larvae and self.can_afford(UnitTypeId.HYDRALISK) and self.structures(UnitTypeId.HYDRALISKDEN).ready:
            larvae.random.train(UnitTypeId.HYDRALISK)
            return

        # If all our townhalls are dead, send all our units to attack
        if not self.townhalls:
            for unit in self.units.of_type(
                {UnitTypeId.DRONE, UnitTypeId.QUEEN, UnitTypeId.ZERGLING, UnitTypeId.HYDRALISK}
            ):
                unit.attack(self.enemy_start_locations[0])
            return

        hq: Unit = self.townhalls.first

        # Send idle queens with >=25 energy to inject
        for queen in self.units(UnitTypeId.QUEEN).idle:
            # The following checks if the inject ability is in the queen abilitys - basically it checks if we have enough energy and if the ability is off-cooldown
            # abilities = await self.get_available_abilities(queen)
            # if AbilityId.EFFECT_INJECTLARVA in abilities:
            if queen.energy >= 25:
                queen(AbilityId.EFFECT_INJECTLARVA, hq)

        # Build spawning pool
        if self.structures(UnitTypeId.SPAWNINGPOOL).amount + self.already_pending(UnitTypeId.SPAWNINGPOOL) == 0:
            if self.can_afford(UnitTypeId.SPAWNINGPOOL):
                await self.build(UnitTypeId.SPAWNINGPOOL, near=hq.position.towards(self.game_info.map_center, 5))

        # Upgrade to lair if spawning pool is complete
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if hq.is_idle and not self.townhalls(UnitTypeId.LAIR):
                if self.can_afford(UnitTypeId.LAIR):
                    hq.build(UnitTypeId.LAIR)

        # If lair is ready and we have no hydra den on the way: build hydra den
        if self.townhalls(UnitTypeId.LAIR).ready:
            if self.structures(UnitTypeId.HYDRALISKDEN).amount + self.already_pending(UnitTypeId.HYDRALISKDEN) == 0:
                if self.can_afford(UnitTypeId.HYDRALISKDEN):
                    await self.build(UnitTypeId.HYDRALISKDEN, near=hq.position.towards(self.game_info.map_center, 5))

        # If we dont have both extractors: build them
        if (
            self.structures(UnitTypeId.SPAWNINGPOOL)
            and self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) < 2
        ):
            if self.can_afford(UnitTypeId.EXTRACTOR):
                # May crash if we dont have any drones
                for vg in self.vespene_geyser.closer_than(10, hq):
                    drone: Unit = self.workers.random
                    drone.build_gas(vg)
                    break

        # If we have less than 22 drones, build drones
        if self.supply_workers + self.already_pending(UnitTypeId.DRONE) < 22:
            if larvae and self.can_afford(UnitTypeId.DRONE):
                larva: Unit = larvae.random
                larva.train(UnitTypeId.DRONE)
                return

        # Saturate gas
        for a in self.gas_buildings:
            if a.assigned_harvesters < a.ideal_harvesters:
                w: Units = self.workers.closer_than(10, a)
                if w:
                    w.random.gather(a)

        # Build queen once the pool is done
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
            if not self.units(UnitTypeId.QUEEN) and hq.is_idle:
                if self.can_afford(UnitTypeId.QUEEN):
                    hq.train(UnitTypeId.QUEEN)

        # Train zerglings if we have much more minerals than vespene (not enough gas for hydras)
        if self.units(UnitTypeId.ZERGLING).amount < 20 and self.minerals > 1000:
            if larvae and self.can_afford(UnitTypeId.ZERGLING):
                larvae.random.train(UnitTypeId.ZERGLING)


def main():
    run_game(
        maps.get("(2)CatalystLE"),
        [Bot(Race.Zerg, Hydralisk()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
