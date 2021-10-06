import sc2
from examples.zerg.zerg_rush import ZergRushBot
from sc2 import Race
from sc2.player import Bot, Human


def main():
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [Human(Race.Terran), Bot(Race.Zerg, ZergRushBot())], realtime=True)


if __name__ == "__main__":
    main()
