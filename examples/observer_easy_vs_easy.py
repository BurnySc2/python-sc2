import sc2
from examples.protoss.cannon_rush import CannonRushBot
from sc2 import Difficulty, Race
from sc2.player import Bot, Computer


def main():
    sc2.run_game(
        sc2.maps.get("Abyssal Reef LE"),
        [Bot(Race.Protoss, CannonRushBot()),
         Computer(Race.Protoss, Difficulty.Medium)],
        realtime=True,
    )


if __name__ == "__main__":
    main()
