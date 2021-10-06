from zerg.zerg_rush import ZergRushBot

import sc2
from sc2 import Race
from sc2.player import Bot


def main():
    portconfig = sc2.portconfig.Portconfig()
    print(portconfig.as_json)

    player_config = [Bot(Race.Zerg, ZergRushBot()), Bot(Race.Zerg, None)]

    for g in sc2.main._host_game_iter(
        sc2.maps.get("Abyssal Reef LE"), player_config, realtime=False, portconfig=portconfig
    ):
        print(g)


if __name__ == "__main__":
    main()
