from importlib import reload

from examples.zerg import zerg_rush
from sc2 import maps
from sc2.data import Difficulty, Race
from sc2.main import _host_game_iter
from sc2.player import Bot, Computer


def main():
    player_config = [Bot(Race.Zerg, zerg_rush.ZergRushBot()), Computer(Race.Terran, Difficulty.Medium)]

    gen = _host_game_iter(maps.get("Abyssal Reef LE"), player_config, realtime=False)

    _r = next(gen)
    while True:
        input("Press enter to reload ")

        reload(zerg_rush)
        player_config[0].ai = zerg_rush.ZergRushBot()
        gen.send(player_config)


if __name__ == "__main__":
    main()
