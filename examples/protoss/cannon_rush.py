import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer


class CannonRushBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(probe)(pylon)(cannon)(cannon)(gg)")

        if not self.townhalls:
            # Attack with all workers if we don't have any nexuses left, attack-move on enemy spawn (doesn't work on 4 player map) so that probes auto attack on the way
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))
            return
        else:
            nexus = self.townhalls.random

        # Make probes until we have 16 total
        if self.supply_workers < 16 and nexus.is_idle:
            if self.can_afford(PROBE):
                self.do(nexus.train(PROBE), subtract_cost=True, subtract_supply=True)

        # If we have no pylon, build one near starting nexus
        elif not self.structures(PYLON) and self.already_pending(PYLON) == 0:
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus)

        # If we have no forge, build one near the pylon that is closest to our starting nexus
        elif not self.structures(FORGE):
            pylon_ready = self.structures(PYLON).ready
            if pylon_ready:
                if self.can_afford(FORGE):
                    await self.build(FORGE, near=pylon_ready.closest_to(nexus))

        # If we have less than 2 pylons, build one at the enemy base
        elif self.structures(PYLON).amount < 2:
            if self.can_afford(PYLON):
                pos = self.enemy_start_locations[0].towards(self.game_info.map_center, random.randrange(8, 15))
                await self.build(PYLON, near=pos)

        # If we have no cannons but at least 2 completed pylons, automatically find a placement location and build them near enemy start location
        elif not self.structures(PHOTONCANNON):
            if self.structures(PYLON).ready.amount >= 2 and self.can_afford(PHOTONCANNON):
                pylon = self.structures(PYLON).closer_than(20, self.enemy_start_locations[0]).random
                await self.build(PHOTONCANNON, near=pylon)

        # Decide if we should make pylon or cannons, then build them at random location near enemy spawn
        elif self.can_afford(PYLON) and self.can_afford(PHOTONCANNON):
            # Ensure "fair" decision
            for _ in range(20):
                pos = self.enemy_start_locations[0].random_on_distance(random.randrange(5, 12))
                building = PHOTONCANNON if self.state.psionic_matrix.covers(pos) else PYLON
                await self.build(building, near=pos)


def main():
    sc2.run_game(
        sc2.maps.get("(2)CatalystLE"),
        [Bot(Race.Protoss, CannonRushBot(), name="CheeseCannon"), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
