import random
import asyncio

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from proxy_rax import ProxyRaxBot


class SlowBot(ProxyRaxBot):
    async def on_step(self, iteration):
        await asyncio.sleep(random.random())
        await super().on_step(iteration)


def main():
    sc2.run_game(
        sc2.maps.get("Abyssal Reef LE"),
        [Bot(Race.Terran, SlowBot()), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
        step_time_limit=0.2,
    )


if __name__ == "__main__":
    main()
