import sc2
from sc2 import Race
from sc2.player import Human, Bot

from .zerg.zerg_rush import ZergRushBot

# from .protoss.cannon_rush import CannonRushBot


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [Human(Race.Terran), Bot(Race.Zerg, ZergRushBot())], realtime=True)


if __name__ == "__main__":
    main()
