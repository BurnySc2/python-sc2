"""
This script let's you play as human against a simple zerg rush bot.
"""

from examples.zerg.zerg_rush import ZergRushBot
from sc2 import maps
from sc2.data import Race
from sc2.main import run_game
from sc2.player import Bot, Human


def main():
    run_game(maps.get("Abyssal Reef LE"), [Human(Race.Terran), Bot(Race.Zerg, ZergRushBot())], realtime=True)


if __name__ == "__main__":
    main()
