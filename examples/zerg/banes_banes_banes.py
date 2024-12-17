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


class BanesBanesBanes(BotAI):
    """
    A dumb bot that a-moves banes.
    Use to check if bane morphs are working correctly
    """

    def select_target(self) -> Point2:
        if self.enemy_structures:
            return random.choice(self.enemy_structures).position
        return self.enemy_start_locations[0]

    async def on_step(self, iteration):
        larvae: Units = self.larva
        lings: Units = self.units(UnitTypeId.ZERGLING)
        # Send all idle banes to enemy
        if banes := [u for u in self.units if u.type_id == UnitTypeId.BANELING and u.is_idle]:
            for unit in banes:
                unit.attack(self.select_target())

        # If supply is low, train overlords
        if (
            self.supply_left < 2
            and larvae
            and self.can_afford(UnitTypeId.OVERLORD)
            and not self.already_pending(UnitTypeId.OVERLORD)
        ):
            larvae.random.train(UnitTypeId.OVERLORD)
            return

        # If bane nest is ready, train banes
        if lings and self.can_afford(UnitTypeId.BANELING) and self.structures(UnitTypeId.BANELINGNEST).ready:
            # TODO: Get lings.random.train(UnitTypeId.BANELING) to work
            #   Broken on recent patches
            # lings.random.train(UnitTypeId.BANELING)

            # This way is working
            lings.random(AbilityId.MORPHTOBANELING_BANELING)
            return

        # If all our townhalls are dead, send all our units to attack
        if not self.townhalls:
            for unit in self.units.of_type({UnitTypeId.DRONE, UnitTypeId.QUEEN, UnitTypeId.ZERGLING}):
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
                await self.build(
                    UnitTypeId.SPAWNINGPOOL,
                    near=hq.position.towards(self.game_info.map_center, 5),
                )

        # Upgrade to lair if spawning pool is complete
        # if self.structures(UnitTypeId.SPAWNINGPOOL).ready:
        #     if hq.is_idle and not self.townhalls(UnitTypeId.LAIR):
        #         if self.can_afford(UnitTypeId.LAIR):
        #             hq.build(UnitTypeId.LAIR)

        # If lair is ready and we have no hydra den on the way: build hydra den
        if self.structures(UnitTypeId.SPAWNINGPOOL).ready and self.can_afford(UnitTypeId.BANELINGNEST):
            if self.structures(UnitTypeId.BANELINGNEST).amount + self.already_pending(UnitTypeId.BANELINGNEST) == 0:
                await self.build(
                    UnitTypeId.BANELINGNEST,
                    near=hq.position.towards(self.game_info.map_center, 5),
                )

        # If we dont have both extractors: build them
        if (
            self.structures(UnitTypeId.SPAWNINGPOOL)
            and self.gas_buildings.amount + self.already_pending(UnitTypeId.EXTRACTOR) < 2
            and self.can_afford(UnitTypeId.EXTRACTOR)
        ):
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

        # Train zerglings
        if larvae and self.can_afford(UnitTypeId.ZERGLING):
            larvae.random.train(UnitTypeId.ZERGLING)


def main():
    run_game(
        maps.get("GoldenAura513AIE"),
        [Bot(Race.Zerg, BanesBanesBanes()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=False,
        save_replay_as="ZvT.SC2Replay",
    )


if __name__ == "__main__":
    main()
