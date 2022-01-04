from sc2 import maps
from sc2.data import Race
from sc2.main import run_game
from zerg.zerg_rush import ZergRushBot

from sc2.player import Bot


def main():
    run_game(
        maps.get("AcropolisLE"),
        [Bot(Race.Zerg, ZergRushBot()), Bot(Race.Zerg, ZergRushBot())],
        realtime=False,
        save_replay_as="Example.SC2Replay",
    )


if __name__ == "__main__":
    main()
