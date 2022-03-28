from examples.protoss.cannon_rush import CannonRushBot
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import run_game
from sc2.player import Bot, Computer


def main():
    run_game(
        maps.get("Abyssal Reef LE"),
        [Bot(Race.Protoss, CannonRushBot()),
         Computer(Race.Protoss, Difficulty.Medium)],
        realtime=True,
    )


if __name__ == "__main__":
    main()
