from importlib import reload

from zerg import zerg_rush

import sc2
from sc2 import Difficulty, Race
from sc2.player import Bot, Computer


def main():
    player_config = [Bot(Race.Zerg, zerg_rush.ZergRushBot()), Computer(Race.Terran, Difficulty.Medium)]

    gen = sc2.main._host_game_iter(sc2.maps.get("Abyssal Reef LE"), player_config, realtime=False)

    r = next(gen)
    while True:
        input("Press enter to reload ")

        reload(zerg_rush)
        player_config[0].ai = zerg_rush.ZergRushBot()
        gen.send(player_config)


if __name__ == "__main__":
    main()
