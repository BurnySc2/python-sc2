from pathlib import Path

from sc2 import maps
from sc2.data import Race
from sc2.main import GameMatch, run_multiple_games
from sc2.player import BotProcess, Computer


def main():
    run_multiple_games(
        [
            GameMatch(
                maps.get("AcropolisLE"),
                [
                    # Enable up to 2 of the 4 following bots to test this file
                    # Assuming you launch external_bot.py from the root directory of 'python-sc2'
                    BotProcess(
                        Path.cwd(),
                        ["python", "examples/competitive/run.py"],
                        Race.Terran,
                        "CompetiveBot",
                        stdout="temp.txt",
                    ),
                    # Bot(Race.Zerg, ZergRushBot()),
                    # Bot(Race.Zerg, ZergRushBot()),
                    Computer(Race.Zerg),
                ],
                realtime=True,
            ),
        ]
    )


if __name__ == "__main__":
    main()
