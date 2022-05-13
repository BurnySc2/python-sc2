import asyncio
import random

from examples.terran.proxy_rax import ProxyRaxBot
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer


class SlowBot(ProxyRaxBot):

    async def on_step(self, iteration):
        await asyncio.sleep(random.random())
        await super().on_step(iteration)


def main():
    run_game(
        maps.get("Abyssal Reef LE"),
        [Bot(Race.Terran, SlowBot()), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=False,
    )


if __name__ == "__main__":
    main()
