"""
This script shows how to let two custom bots play against each other.
"""
from typing import List

from loguru import logger

from examples.protoss.warpgate_push import WarpGateBot
from examples.zerg.zerg_rush import ZergRushBot
from sc2 import maps
from sc2.data import Race, Result
from sc2.main import GameMatch, run_game, run_multiple_games
from sc2.player import Bot


def main_old():
    result: List[Result] = run_game(
        maps.get("AcropolisLE"),
        [
            Bot(Race.Protoss, WarpGateBot()),
            Bot(Race.Zerg, ZergRushBot()),
        ],
        realtime=False,
        game_time_limit=2,
        save_replay_as="Example.SC2Replay",
    )
    logger.info(f"Result: {result}")


def main():
    result = run_multiple_games(
        [
            GameMatch(
                map_sc2=maps.get("AcropolisLE"),
                players=[
                    Bot(Race.Protoss, WarpGateBot()),
                    Bot(Race.Zerg, ZergRushBot()),
                ],
                realtime=False,
                game_time_limit=2,
            )
        ]
    )
    logger.info(f"Result: {result}")


if __name__ == "__main__":
    main_old()
    # TODO Why does "run_multiple_games" get stuck?
    # main()
