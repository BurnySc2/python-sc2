import sys

from __init__ import run_ladder_game

# Load bot
from bot import CompetitiveBot

import sc2
from sc2 import Difficulty, Race
from sc2.player import Bot, Computer

bot = Bot(Race.Zerg, CompetitiveBot())

# Start game
if __name__ == "__main__":
    if "--LadderServer" in sys.argv:
        # Ladder game started by LadderManager
        print("Starting ladder game...")
        result, opponentid = run_ladder_game(bot)
        print(result, " against opponent ", opponentid)
    else:
        # Local game
        print("Starting local game...")
        sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [bot, Computer(Race.Zerg, Difficulty.VeryHard)], realtime=True)
