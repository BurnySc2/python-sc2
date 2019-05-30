import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

class CannonRushBot(sc2.BotAI):
    async def on_step(self, iteration):
        if iteration == 0:
            await self.chat_send("(probe)(pylon)(cannon)(cannon)(gg)")

        if not self.townhalls.exists:
            for worker in self.workers:
                self.do(worker.attack(self.enemy_start_locations[0]))
            return
        else:
            nexus = self.townhalls.first

        if self.workers.amount < 16 and nexus.is_idle:
            if self.can_afford(PROBE):
                self.do(nexus.train(PROBE))

        elif not self.structures(PYLON).exists and not self.already_pending(PYLON):
            if self.can_afford(PYLON):
                await self.build(PYLON, near=nexus)

        elif not self.structures(FORGE).exists:
            pylon = self.structures(PYLON).ready
            if pylon.exists:
                if self.can_afford(FORGE):
                    await self.build(FORGE, near=pylon.closest_to(nexus))

        elif self.structures(PYLON).amount < 2:
            if self.can_afford(PYLON):
                pos = self.enemy_start_locations[0].towards(self.game_info.map_center, random.randrange(8, 15))
                await self.build(PYLON, near=pos)

        elif not self.structures(PHOTONCANNON).exists:
            if self.structures(PYLON).ready.amount >= 2 and self.can_afford(PHOTONCANNON):
                pylon = self.structures(PYLON).closer_than(20, self.enemy_start_locations[0]).random
                await self.build(PHOTONCANNON, near=pylon)

        else:
            if self.can_afford(PYLON) and self.can_afford(PHOTONCANNON): # ensure "fair" decision
                for _ in range(20):
                    pos = self.enemy_start_locations[0].random_on_distance(random.randrange(5, 12))
                    building = PHOTONCANNON if self.state.psionic_matrix.covers(pos) else PYLON
                    r = await self.build(building, near=pos)
                    if not r: # success
                        break

def main():
    sc2.run_game(sc2.maps.get("(2)CatalystLE"), [
        Bot(Race.Protoss, CannonRushBot(), name="CheeseCannon"),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
