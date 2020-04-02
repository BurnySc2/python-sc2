import sys, os

sys.path.append(os.path.join(os.path.dirname(__file__), "../.."))

import sc2
from sc2.position import Point2, Point3
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer
from sc2.unit import Unit
from sc2.units import Units

import asyncio

"""
This bot is just to demonstrate that you can do worker split 
at game start without having to use 'synchronous_do()'.
This is especially important when your bot runs on realtime=True and 
you want your bot to be reliable against Human opponents.
"""


class WorkerSplitBot(sc2.BotAI):
    async def on_before_start(self):
        """ This function is run before the expansion locations and ramps are calculated. These calculations can take up to a second, depending on the CPU. """
        mf: Units = self.mineral_field
        for w in self.workers:
            w.gather(mf.closest_to(w))
        await self._do_actions(self.actions)
        self.actions.clear()
        await asyncio.sleep(3)

    async def on_start(self):
        """ This function is run after the expansion locations and ramps are calculated. """
        pass

    async def on_step(self, iteration):
        if iteration % 10 == 0:
            await asyncio.sleep(3)
        # In realtime=False, this should print "8*x" and "x" if
        # self.client.game_step is set to 8 (default value)
        # But if your bot takes too long, it will skip game loops.
        print(f"Bot's game loop is {self.state.game_loop} and iteration {iteration}")


def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Zerg, WorkerSplitBot()), Computer(Race.Terran, Difficulty.Medium)],
        realtime=True,
    )


if __name__ == "__main__":
    main()
