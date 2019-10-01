import sc2
from sc2 import Race, Difficulty
from sc2 import maps, run_game
from sc2.player import Computer, Bot

from .protoss.cannon_rush import CannonRushBot


def main():
    sc2.run_game(
        sc2.maps.get("Abyssal Reef LE"),
        [Bot(Race.Protoss, CannonRushBot()), Computer(Race.Protoss, Difficulty.Medium)],
        realtime=True,
    )


if __name__ == "__main__":
    main()
