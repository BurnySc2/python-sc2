import os

import sc2
from sc2 import Race
from sc2.player import Bot, BotProcess
from sc2.main import GameMatch, run_multiple_games

from zerg.zerg_rush import ZergRushBot


def main():
	run_multiple_games(
		GameMatch(
			sc2.maps.get("AcropolisLE"),
			[BotProcess(
				os.path.join(os.getcwd(), "competitive"),
				"python run.py",
				Race.Terran,
				"CompetiveBot",
			), 
			Bot(Race.Zerg, ZergRushBot())]
		)
	)


if __name__ == "__main__":
    main()
