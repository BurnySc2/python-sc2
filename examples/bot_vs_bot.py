import sc2
from sc2 import Race
from sc2.player import Bot

from zerg.zerg_rush import ZergRushBot


def main():
    sc2.run_game(
        sc2.maps.get("AcropolisLE"),
        [Bot(Race.Zerg, ZergRushBot()), Bot(Race.Zerg, ZergRushBot())],
        realtime=False,
        save_replay_as="Example.SC2Replay",
    )


if __name__ == "__main__":
    main()
